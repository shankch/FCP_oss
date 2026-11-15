"""Requests we did not write: FCP on HumanEvalComm, before any code is written.

    python experiments/comm_fetch.py                         # the benchmark, at a pinned commit
    python experiments/comm_demo.py prepare                  # screen, sample, one work directory per prompt
    python experiments/comm_demo.py agents   [--tasks N] [--jobs K]
    python experiments/comm_demo.py check    [--tasks N] [--jobs K]   # each prompt inside a memory cap of its own
    python experiments/comm_demo.py again WHY KEY...         # these prompts are checked again; the earlier check is kept
    python experiments/comm_demo.py baseline [--tasks N] [--jobs K]
    python experiments/comm_demo.py judge    [--tasks N] [--jobs K]
    python experiments/comm_demo.py audit    [--tasks N]     # every tool call of the agents, with its outcome
    python experiments/comm_demo.py collect  [--tasks N]     # the reviews, copied to experiments/comm/
    python experiments/comm_demo.py summary  [--tasks N]

HumanEvalComm (Wu and Fard, ACM TOSEM 2025) takes the 164 HumanEval problem
descriptions and rewrites each so that it is ambiguous (1a), inconsistent
(1c: the examples contradict the description) or incomplete (1p).  A model
given such a description should ask before it writes code.  Here every
description goes through `fcp review` with a signature and no code: the
questions the request raises before anything is written.  The original
descriptions are the controls.

Screen (on the benchmark's own test cases, which no agent sees): a problem
is kept when its values fit the types FCP's function adapter has, that is
every argument and result is a boolean, an integer in 0..100000, an ASCII
string of at most 32 characters or a list of at most 16 such integers, every
test compares with ==, and the original and the three single-defect variants
each parse as one Python function.  From the problems kept, 20 are drawn
with a fixed seed.

Compared with the same model alone, without tools, under the benchmark's two
instructions: write code or ask (B1), and ask if anything is unclear or
answer NO_QUESTIONS (B2); and on the request as `fcp review` gets it, with
no invitation to ask (B0).  The benchmark's own judging prompt rates whether
the questions asked recover what the rewrite changed; for B0, which answers
with code, a judge of the same form rates whether the answer's prose names
what the rewrite changed.

The review's questions are counted at three levels.  Hard: a conflict, a
scenario the requirements contradict, a call the request leaves open, two
readings that differ on a call: a result of the engine about the request,
shown on a call (a scenario question names an example and shows no call).
Depends: an answer both readers shared whose other reading changes a call.
Ambiguity: a phrase the decomposer flagged, with no call behind it.
A question about the two readings, or about a shared answer, that shows no
call reports a comparison that did not end.  It states nothing about the
request: it is counted apart (undecided) and is in neither judged subset.

Every agent runs confined (fcp.review.run_agent): four tools, permissions
that end at its workspace, a launcher that works on that workspace only, and
a sandbox whose file system holds the workspace and nothing else of this
machine but the programs it runs.  `audit` reads every tool call in the
agents' transcripts together with its outcome.

Work happens outside the repository, in ~/.cache/fcp/comm-work/<key>/ (or
$FCP_COMM_WORK), so that an agent's session loads nothing of this project,
one directory per prompt under a key that does not name the problem or the
variant, so that an agent reading one prompt cannot find its siblings by
name.  `collect` copies the finished reviews into experiments/comm/.
"""
from __future__ import annotations

import ast
import collections
import hashlib
import json
import os
import re
import random
import shutil
import signal
import subprocess
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, '.tools', 'humanevalcomm-dl', 'HumanEvalComm_v2.jsonl')
WORK = os.environ.get('FCP_COMM_WORK') or os.path.expanduser('~/.cache/fcp/comm-work')
REPO = os.path.join(HERE, 'comm')
TASKS = os.path.join(REPO, 'tasks.json')
RESULT = os.path.join(HERE, 'results', 'comm.json')

SEED, SAMPLE = 20261112, 20
INT_MAX, STR_MAX, LIST_MAX = 100000, 32, 16
VARIANTS = {'original': 'prompt', '1a': 'prompt1a', '1c': 'prompt1c', '1p': 'prompt1p'}
FORMAL = ('conflict', 'open', 'scenario', 'readings', 'depends')     # questions with a result of the engine behind them
HARD = ('conflict', 'open', 'scenario', 'readings')                  # ... that state a fact about the request
LEVELS = {'hard': HARD, 'depends': ('depends',), 'ambiguity': ('ambiguity',), 'undecided': ('undecided',)}
SETS = {'fcp': None, 'fcp_formal': FORMAL, 'fcp_hard': HARD}         # the questions given to the judge
MODEL = 'opus'


# ---------------------------------------------------------------- the benchmark, screened and sampled

def load() -> dict:
    rows = {}
    with open(DATA, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                rows[r['name']] = r
    return rows


def number(name: str) -> int:
    return int(name.split('/')[1])


def misfit(v):
    """Why a test value does not fit the function adapter's types (None: it fits)."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return None if 0 <= v <= INT_MAX else 'a negative or large integer'
    if isinstance(v, float):
        return 'a float'
    if isinstance(v, str):
        return None if len(v) <= STR_MAX and v.isascii() else 'a long or non-ASCII string'
    if isinstance(v, list):
        if len(v) > LIST_MAX:
            return 'a long list'
        why = [misfit(x) if isinstance(x, int) and not isinstance(x, bool) else
               'a float' if isinstance(x, float) else 'another type' for x in v]
        return next((w for w in why if w), None)
    return 'another type'


def one_function(src: str):
    """The single function a prompt defines (None if it is not one Python function)."""
    try:
        fns = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef)]
    except SyntaxError:
        return None
    return fns[0] if len(fns) == 1 else None


def screen(rows: dict) -> tuple[list[str], dict]:
    keep, why = [], collections.Counter()
    for name, r in rows.items():
        if any(not r.get(k) for k in VARIANTS.values()):
            why['a variant is missing'] += 1
            continue
        if any(one_function(r[k]) is None for k in VARIANTS.values()):
            why['a prompt is not one Python function'] += 1
            continue
        try:
            cases = r['test_case'] if isinstance(r['test_case'], list) else ast.literal_eval(r['test_case'])
            vals = []
            for c in cases:
                if c['relation'] != '==':
                    raise KeyError('relation')
                vals += list(ast.literal_eval('(' + c['input'] + ',)')) + [ast.literal_eval(c['output'])]
        except KeyError:
            why['a test does not compare with =='] += 1
            continue
        except (ValueError, SyntaxError, TypeError):
            why['the tests are not literal values'] += 1
            continue
        bad = next((w for w in map(misfit, vals) if w), None) if vals else 'no tests'
        if bad:
            why[bad] += 1
            continue
        keep.append(name)
    return sorted(keep, key=number), dict(why)


def key(name: str, variant: str) -> str:
    return hashlib.sha256(f'fcp-comm:{name}:{variant}'.encode()).hexdigest()[:12]


def work(p: dict) -> str:
    return os.path.join(WORK, p['key'])


def prompts(n_tasks=None) -> list[dict]:
    with open(TASKS) as f:
        t = json.load(f)
    names = t['sample'][:n_tasks] if n_tasks else t['sample']
    return [{'task': n, 'variant': v, 'key': key(n, v)} for n in names for v in VARIANTS]


def prepare():
    from fcp import review as R
    rows = load()
    keep, why = screen(rows)
    sample = random.Random(SEED).sample(keep, SAMPLE)
    os.makedirs(REPO, exist_ok=True)
    with open(TASKS, 'w') as f:
        json.dump({'benchmark': 'HumanEvalComm_v2.jsonl (jie-jw-wu/human-eval-comm at 794a91f)',
                   'problems': len(rows), 'kept': len(keep), 'excluded': why, 'kept_names': keep,
                   'seed': SEED, 'sample': sample}, f, indent=1)
    for name in sample:
        for v, field in VARIANTS.items():
            d = os.path.join(WORK, key(name, v))
            os.makedirs(d, exist_ok=True)
            src = rows[name][field].strip('\n')
            with open(os.path.join(d, 'request.md'), 'w') as f:
                f.write(f'Complete this function:\n\n```python\n{src}\n```\n')
            with open(os.path.join(d, 'stub.py'), 'w') as f:
                f.write(R._def_line(one_function(src)) + '\n')
            with open(os.path.join(d, 'problem.txt'), 'w') as f:
                f.write(src + '\n')
    print(f'{len(rows)} problems, {len(keep)} kept; excluded: {why}')
    print('sample:', ' '.join(str(number(n)) for n in sample))


# ---------------------------------------------------------------- per prompt: status, agents, the request alone

def status(p: dict) -> dict:
    path = os.path.join(work(p), 'status.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def set_status(p: dict, **kw):
    st = status(p)
    st.update(kw)
    path = os.path.join(work(p), 'status.json')
    with open(path + '.tmp', 'w') as f:
        json.dump(st, f, indent=1)
    os.replace(path + '.tmp', path)


def log_to(p: dict):
    path = os.path.join(work(p), 'log.txt')

    def log(msg):
        with open(path, 'a') as f:
            f.write(f'{time.strftime("%H:%M:%S")} {msg}\n')
    return log


LIMIT = re.compile(r'limit reached|usage limit|rate limit|hit your limit|\b429\b|overloaded|credit balance|quota',
                   re.I)
STOP = threading.Event()                    # set when an agent's reply is an error about usage: no further prompt starts


def limited(out: str):
    """The reply of an agent of this review that is an error about usage limits (None: there is none)."""
    for a in AGENTS:
        try:
            with open(os.path.join(out, 'agents', a, 'run.json')) as f:
                run = json.load(f).get('run') or {}
            with open(os.path.join(out, 'agents', a, 'summary.md')) as f:
                text = f.read()
        except OSError:
            continue
        if run.get('error') and LIMIT.search(text):
            return f'{a}: {text.strip()[:200]}'
    return None


def agents_one(p: dict):
    """Adapter, decomposer, two readers and, where they shared answers, a third."""
    from fcp import agents as AG, review as R
    st = status(p)
    if st.get('agents') == 'ok' or STOP.is_set():
        return
    d, t, log = work(p), time.time(), log_to(p)
    out = os.path.join(d, 'out')
    if os.path.exists(out):                                 # an attempt that did not finish: kept, out of the way
        n = 0
        while os.path.exists(f'{out}_try{n}'):
            n += 1
        os.rename(out, f'{out}_try{n}')
    stage = 'adapter or decomposer'
    try:
        bundle = R.build_bundle(os.path.join(d, 'request.md'), os.path.join(d, 'stub.py'), out, MODEL, log)
        stage = 'readers'
        sets = R.formalize(bundle, out, MODEL, log)
        if len(sets) < 2:
            raise RuntimeError(f'readings written: {sets}')
        stage = 'third reader'
        R.variant(bundle, out, sets, MODEL, log)
        res = 'ok'
        lint = subprocess.run([AG.FCP, 'lint', bundle], capture_output=True, text=True, timeout=900)
        set_status(p, lint='clean' if lint.returncode == 0 else lint.stdout[-1500:])
    except Exception as e:                                  # recorded: a failure is a result
        res = f'{stage}: {type(e).__name__}: {e}'[:600]
    why = limited(out)                                      # also after 'ok': a third reader that did not run
    if why:                                                 # not a result: the account's limit, the run stops here
        STOP.set()
        set_status(p, agents=f'limit: {why}')
        print(time.strftime('%H:%M:%S'), 'agents', p['key'], 'STOPPED on a usage limit:', why, flush=True)
        return
    set_status(p, agents=res, agents_seconds=round(time.time() - t), attempts=st.get('attempts', 0) + 1)
    print(time.strftime('%H:%M:%S'), 'agents', p['key'], res, round(time.time() - t), 's', flush=True)


def check_status(res: dict) -> str:
    """'ok' for a review of every step of the check; 'partial: ...' with the
    steps that did not end; 'unchecked: ...' where the check gave no
    verdicts.  Only 'ok' counts as a review in the tables."""
    if res.get('unchecked'):
        return f"unchecked: {res['unchecked']}"[:600]
    if res.get('failed'):
        return ('partial: ' + '; '.join(f"{x['step']}: {x['why']}" for x in res['failed']))[:600]
    return 'ok'


def check_one(p: dict, scope_budget: float, conflict_budget: float, compare_budget: float):
    """The request alone: scenarios, conflicts, open choices, the readings
    compared, in the watched check of the engine (fcp.review.checked), which
    writes a review whatever its steps do.  Its memory limit is the engine's
    own (85% of the scope this process runs in); its time limit leaves the
    engine six minutes of CHECK_MINUTES to close and to write the review."""
    from fcp import review as R
    st = status(p)
    if st.get('agents') != 'ok' or 'check' in st:
        return
    out, t = os.path.join(work(p), 'out'), time.time()
    bundle, sets = os.path.join(out, 'bundle'), ['agent_a', 'agent_b']
    try:
        res = R.checked(bundle, None, sets, out, log_to(p), scope_budget=scope_budget,
                        conflict_budget=conflict_budget, compare_budget=compare_budget, jobs=CHECK_JOBS,
                        step_seconds=CHECK_STEP_MINUTES * 60, check_seconds=max(60, CHECK_MINUTES * 60 - 360))
        r = check_status(res)
    except Exception as e:
        r = f'{type(e).__name__}: {e}'[:600]
    set_status(p, check=r, check_seconds=round(time.time() - t))
    print(time.strftime('%H:%M:%S'), 'check', p['key'], r, round(time.time() - t), 's', flush=True)


def again(p: dict, why: str):
    """The next `check` takes this prompt once more (after a fix to the
    engine).  The earlier result stays in status.json under 'earlier', with
    the reason, and the earlier review as out/check<n>_review.json and .md."""
    st = status(p)
    if 'check' not in st:
        return
    out, n = os.path.join(work(p), 'out'), 1 + len(st.get('earlier', []))
    for f in ('review.json', 'review.md'):
        if os.path.exists(os.path.join(out, f)):
            os.replace(os.path.join(out, f), os.path.join(out, f'check{n}_{f}'))
    st.setdefault('earlier', []).append({'check': st.pop('check'), 'seconds': st.pop('check_seconds', None),
                                         'why': why})
    path = os.path.join(work(p), 'status.json')
    with open(path + '.tmp', 'w') as f:
        json.dump(st, f, indent=1)
    os.replace(path + '.tmp', path)
    print('again', p['key'], st['earlier'][-1], flush=True)


CHECK_GB = float(os.environ.get('FCP_CHECK_GB', 8))                 # memory for the check of one prompt
CHECK_MINUTES = float(os.environ.get('FCP_CHECK_MINUTES', 45))      # ... and time
CHECK_JOBS = int(os.environ.get('FCP_CHECK_JOBS', 4))               # its engine tasks at a time, inside that memory
CHECK_STEP_MINUTES = float(os.environ.get('FCP_CHECK_STEP_MINUTES', 15))    # one step of the check, as in fcp review


def check_all(ps: list[dict], scope_budget: int, conflict_budget: int, compare_budget: int, jobs: int = 1):
    """The check of each prompt in a process of its own, inside a memory cap and
    a time limit of its own (FCP_CHECK_GB, FCP_CHECK_MINUTES), jobs at a time.
    A reading too large for the searches then stops the check of its own
    prompt, which is recorded as stopped, and the other prompts are checked."""
    systemd = ['systemd-run', '--user', '--scope', '-q']
    scoped = bool(shutil.which('systemd-run')) and not subprocess.run(systemd + ['--', 'true'],
                                                                      capture_output=True).returncode
    if not scoped:
        print('no systemd scope starts here: the checks run without a memory cap', flush=True)

    def one(p: dict):
        st = status(p)
        if st.get('agents') != 'ok' or 'check' in st:
            return
        unit = f'fcp-check-{p["key"]}-{os.getpid()}'
        cmd = [sys.executable, '-I', '-u', os.path.abspath(__file__), 'check-one', p['key'],
               '--scope', str(scope_budget), '--conflict', str(conflict_budget), '--compare', str(compare_budget)]
        if scoped:
            cmd = systemd + ['--unit', unit, '-p', f'MemoryMax={int(CHECK_GB * 1024)}M', '-p', 'MemorySwapMax=0',
                             '-p', f'RuntimeMaxSec={int(CHECK_MINUTES * 60) + 60}', '--'] + cmd   # if this process dies
        t, proc, rc = time.time(), subprocess.Popen(cmd, start_new_session=True), 0
        try:
            rc = proc.wait(timeout=CHECK_MINUTES * 60)
            why = f'stopped: exit code {rc}'
        except subprocess.TimeoutExpired:
            why = f'stopped after {CHECK_MINUTES:g} minutes'
            try:
                os.killpg(proc.pid, signal.SIGKILL)         # the check, the workers of its pool, their solvers
            except ProcessLookupError:
                pass
            proc.wait()
        if scoped:
            ctl = lambda *a: subprocess.run(('systemctl', '--user') + a + (unit + '.scope',),
                                            capture_output=True, text=True).stdout.strip()
            for _ in range(25 if rc < 0 else 1):            # killed: systemd learns why a moment later
                if ctl('show', '-p', 'Result', '--value') == 'oom-kill':
                    why = f'stopped: more than {CHECK_GB:g} GB of memory'
                    break
                time.sleep(0.2)
            ctl('kill', '--signal=KILL')                    # whatever is left of it
            ctl('stop')
            ctl('reset-failed')
        if 'check' not in status(p):
            set_status(p, check=why, check_seconds=round(time.time() - t))
            print(time.strftime('%H:%M:%S'), 'check', p['key'], why, round(time.time() - t), 's', flush=True)
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        list(ex.map(one, ps))


# ---------------------------------------------------------------- the same model alone, and the judge
# The three prompts below are the benchmark's own (generate_response.py at the pinned commit:
# PROMPT_START_3_v2, OK_PROMPT_CLARIFY_Q and PROMPT_EVALUATE_QUESTION_QUALITY), character for character.

B1 = ('You are an expert software developer who writes high quality code. With below information, '
      'please either generate Python3 code (Respond directly with code only with markdown), or ask '
      'clarifying questions: \n')
B2 = ('Given the programming problem, ask clarifying questions if the requirements in the given problem '
      'description are incomplete, inconsistent or ambiguous for solving the problem correctly and '
      "passing the tests. \n If no need to ask clarifying questions, return strictly 'NO_QUESTIONS' "
      'only. Otherwise, return the clarifying questions. \n\n ### Problem: \n {problem}')
JUDGE = ('The original description of a coding problem is modified such that the modified version is '
         'either  inconsistent, incomplete, ambiguous, or a combination of any of them. The modified '
         'problem is provided to an expert, where he will either answer with a question asking for '
         'clarifications or a direct code answer. You are provided the original and modified problem '
         'descriptions together with the expert answer. Your task is to evaluate the quality of expert '
         'questions on a scale from 1 to 2, where 1 indicates that fair questions were asked but they '
         'cannot help recover the modified requirements, and 2 indicates good questions that recover the '
         'modified requirements. Please respond with a signle integer 1, or 2 based on the grading schema '
         'that I outlined. No explanation needed, just a single integer. \n\n ### Questions: '
         '{clarifying_questions} \n ### Modified Problem Description: {problem} \n ### Original Description: '
         '{missing_information}')
NAMES = ('The original description of a coding problem is modified such that the modified version is '
         'either inconsistent, incomplete, ambiguous, or a combination of any of them. The modified '
         'problem is provided to an expert, whose answer is given below. Your task is to say whether the '
         'answer tells its reader about the modification in words, on a scale from 0 to 2, where 0 '
         'indicates that the answer says nothing about a problem in the description, 1 indicates that '
         'the answer remarks on the description but its remarks cannot help recover the modified '
         'requirements, and 2 indicates that the answer names what is missing, inconsistent or ambiguous '
         'so that its reader can recover the modified requirements. Please respond with a single integer '
         '0, 1, or 2. No explanation needed, just a single integer. \n\n ### Answer: {answer} \n '
         '### Modified Problem Description: {problem} \n ### Original Description: {original}')
SYSTEM = 'You are a helpful assistant.'


def ask(prompt: str, timeout: int = 900) -> dict:
    """The model alone: no tools, a one-line system prompt, an empty directory."""
    from fcp import review as R
    d = os.path.join(WORK, 'empty')
    os.makedirs(d, exist_ok=True)
    cmd = [R.CLAUDE, '-p', prompt, '--model', MODEL, '--output-format', 'json', '--tools', '',
           '--strict-mcp-config', '--system-prompt', SYSTEM, '--no-session-persistence']
    t = time.time()
    try:
        r = subprocess.run(cmd, cwd=d, capture_output=True, text=True, timeout=timeout)
        j = json.loads(r.stdout)
        return {'reply': j.get('result') or '', 'seconds': round(time.time() - t, 1),
                'cost_usd': j.get('total_cost_usd'), 'models': sorted(j.get('modelUsage') or {}),
                'error': bool(j.get('is_error'))}
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return {'reply': '', 'seconds': round(time.time() - t, 1), 'error': True, 'why': type(e).__name__}


def problem(p: dict, variant: str = None) -> str:
    q = dict(p, key=key(p['task'], variant)) if variant else p
    with open(os.path.join(work(q), 'problem.txt')) as f:
        return f.read()


def baseline_one(p: dict):
    """The model alone on one description: b1 and b2 under the benchmark's two
    instructions, b0 on the request as fcp review gets it (no invitation to ask)."""
    path = os.path.join(work(p), 'baseline.json')
    out = {}
    if os.path.exists(path):
        with open(path) as f:
            out = json.load(f)
    text = problem(p)
    with open(os.path.join(work(p), 'request.md')) as f:
        request = f.read()
    todo = {'b1': B1 + text, 'b2': B2.format(problem=text), 'b0': request}
    new = [k for k in todo if k not in out or out[k].get('error')]
    if not new:
        return
    for k in new:
        out[k] = ask(todo[k])
    with open(path + '.tmp', 'w') as f:
        json.dump(out, f, indent=1)
    os.replace(path + '.tmp', path)
    print(time.strftime('%H:%M:%S'), 'baseline', p['key'], asks_b1(out['b1']['reply']), asks_b2(out['b2']['reply']),
          wrote_code(out['b0']['reply']), flush=True)


def wrote_code(reply: str) -> bool:
    return any(line.lstrip().startswith('def ') for line in reply.splitlines())


def asks_b1(reply: str) -> bool:
    """B1 answered with questions, not code (code: a def in the reply)."""
    return bool(reply.strip()) and not wrote_code(reply)


def asks_b2(reply: str) -> bool:
    return bool(reply.strip()) and 'NO_QUESTIONS' not in reply


def kind_of(q: dict) -> str:
    """The kind a question is counted under.  A question about the two
    readings, or about a shared answer, that shows no call reports a
    comparison that did not end, not a fact about the request: undecided."""
    return 'undecided' if q['kind'] in ('readings', 'depends') and not q.get('calls') else q['kind']


def fcp_questions(p: dict, kinds=None) -> tuple[int, str]:
    """The review's questions as its reader gets them, each with the text of
    the requirements it names and its calls (kinds: only questions of these kinds)."""
    import yaml
    out = os.path.join(work(p), 'out')
    with open(os.path.join(out, 'review.json')) as f:
        res = json.load(f)
    with open(os.path.join(out, 'bundle', 'requirements.yaml')) as f:
        reqs = {r['id']: r for r in yaml.safe_load(f)['requirements']}
    lines, n = [], 0
    for q in res['queue']:
        if kinds and kind_of(q) not in kinds:
            continue
        n += 1
        lines.append(f'{n}. {q["question"]}')
        lines += [f'   - {r}: {reqs[r]["text"]}' for r in q.get('reqs') or [] if r in reqs]
        lines += [f'   - on: {c}' for c in q.get('calls') or []]
        if q['kind'] == 'depends':
            lines += [f'   - "{a["phrase"]}" ({a["req"]}) could also mean: {a["text"]}'
                      for a in res.get('variant_answers') or []]
    return n, '\n'.join(lines)


def grade(reply: str, scale: str = '12'):
    return next((int(c) for c in reply if c in scale), None)


def judge_one(p: dict):
    """The benchmark's judging prompt on each set of questions asked about a rewritten description."""
    if p['variant'] == 'original':
        return
    path = os.path.join(work(p), 'judge.json')
    done = {}
    if os.path.exists(path):
        with open(path) as f:
            done = json.load(f)
    items = {}
    if os.path.exists(os.path.join(work(p), 'baseline.json')):
        with open(os.path.join(work(p), 'baseline.json')) as f:
            b = json.load(f)
        if asks_b1(b['b1']['reply']):
            items['b1'] = b['b1']['reply']
        if asks_b2(b['b2']['reply']):
            items['b2'] = b['b2']['reply']
        if (b.get('b0') or {}).get('reply'):
            items['b0'] = b['b0']['reply']
    if status(p).get('check') == 'ok':
        for name, kinds in SETS.items():
            n, text = fcp_questions(p, kinds)
            if n:
                items[name] = text
    for name in SETS:                                   # a set the review does not ask (any more) has no grade
        if name not in items:
            done.pop(name, None)
    orig, mod = problem(p, 'original'), problem(p)
    for name, text in items.items():
        if done.get(name, {}).get('questions') == text and done[name].get('grade') is not None:
            continue
        if name == 'b0':                                # an answer with code: does its prose name the rewrite?
            a = ask(NAMES.format(answer=text, problem=mod, original=orig))
            g = grade(a['reply'], '012')
        else:
            a = ask(JUDGE.format(clarifying_questions=text, problem=mod, missing_information=orig))
            g = grade(a['reply'])
        done[name] = {'questions': text, 'reply': a['reply'], 'grade': g,
                      'cost_usd': a.get('cost_usd'), 'seconds': a['seconds']}
    with open(path + '.tmp', 'w') as f:
        json.dump(done, f, indent=1)
    os.replace(path + '.tmp', path)
    print(time.strftime('%H:%M:%S'), 'judge', p['key'], {k: v['grade'] for k, v in done.items()}, flush=True)


# ---------------------------------------------------------------- the reviews kept, and the numbers

AGENTS = ('adapter', 'decomposer', 'agent_a', 'agent_b', 'variant')
KEPT = ('request.md', 'status.json', 'baseline.json', 'judge.json', 'out/review.json', 'out/review.md',
        'out/check1_review.json', 'out/check1_review.md',
        'out/bundle/design.yaml', 'out/bundle/frame.md', 'out/bundle/requirements.yaml',
        'out/bundle/formal/agent_a.yaml', 'out/bundle/formal/agent_b.yaml', 'out/bundle/formal/variant.yaml',
        'out/bundle/formal/variant_answers.json') + tuple(
            f'out/agents/{a}/{f}' for a in AGENTS for f in ('prompt.md', 'summary.md', 'run.json'))


def collect(ps: list[dict]):
    """Copies what each review rests on into experiments/comm/<problem>/<variant>/."""
    n = 0
    for p in ps:
        dst = os.path.join(REPO, str(number(p['task'])), p['variant'])
        out = os.path.join(work(p), 'out')
        earlier = sorted(f'out/{f}' for f in (os.listdir(out) if os.path.isdir(out) else [])
                         if re.fullmatch(r'check\d+_review\.(json|md)', f))    # the review of every earlier check
        for rel in dict.fromkeys(KEPT + tuple(earlier)):
            src = os.path.join(work(p), rel)
            if os.path.exists(src):
                to = os.path.join(dst, rel.replace('out/', '', 1))
                os.makedirs(os.path.dirname(to), exist_ok=True)
                if rel.endswith(('prompt.md', 'summary.md', 'status.json', 'review.json', 'review.md')):
                    with open(src) as f:                    # the work directory's path says nothing: shorten it
                        text = f.read().replace(work(p), '<work>').replace(ROOT, '<fcp>')
                    with open(to, 'w') as f:
                        f.write(text)
                else:
                    shutil.copy(src, to)
                n += 1
    print(n, 'files copied to', os.path.relpath(REPO, ROOT))


def levels(kinds) -> dict:
    return {name: sum(kinds.get(k, 0) for k in ks) for name, ks in LEVELS.items()}


def row(p: dict) -> dict:
    import yaml
    st, out = status(p), os.path.join(work(p), 'out')
    r = {'task': p['task'], 'variant': p['variant'], 'agents': st.get('agents'), 'lint': st.get('lint'),
         'check': st.get('check'), 'attempts': st.get('attempts'),
         'seconds': {'agents': st.get('agents_seconds'), 'check': st.get('check_seconds')}, 'runs': {}}
    if st.get('earlier'):                                   # the checks of this prompt before a fix to the engine
        r['earlier'] = st['earlier']
    for a in AGENTS:
        path = os.path.join(out, 'agents', a, 'run.json')
        if os.path.exists(path):
            with open(path) as f:
                r['runs'][a] = json.load(f).get('run') or {}
    r['cost_usd'] = round(sum(x.get('cost_usd') or 0 for x in r['runs'].values()), 2)
    r['sandboxed'] = bool(r['runs']) and all(x.get('sandbox') for x in r['runs'].values())
    if st.get('check') == 'ok':
        with open(os.path.join(out, 'review.json')) as f:
            res = json.load(f)
        with open(os.path.join(out, 'bundle', 'requirements.yaml')) as f:
            reqs = yaml.safe_load(f)['requirements']
        kinds = collections.Counter(kind_of(q) for q in res['queue'])
        r['questions'] = dict(kinds)
        r['formal'] = sum(kinds[k] for k in FORMAL)
        r['levels'] = levels(kinds)
        r['settled'] = len(res['certified'])
        r['requirements'] = sum(x.get('kind') in ('guarantee', 'scenario') and x.get('doc') != 'FRAME' for x in reqs)
        r['flagged_phrases'] = sum(len(x.get('ambiguity') or []) for x in reqs)
        r['limits'] = len(res.get('limits') or [])
        r['third_reader'] = len(res.get('variant_answers') or [])
        r['unformalized'] = {}
        for s in res['sets']:
            with open(os.path.join(out, 'bundle', 'formal', f'{s}.yaml')) as f:
                fs = yaml.safe_load(f) or {}
            r['unformalized'][s] = sorted(u['req'] for u in fs.get('unformalized') or [] if not u.get('covered_by'))
    path = os.path.join(work(p), 'baseline.json')
    if os.path.exists(path):
        with open(path) as f:
            b = json.load(f)
        r['b1_asks'], r['b2_asks'] = asks_b1(b['b1']['reply']), asks_b2(b['b2']['reply'])
        if 'b0' in b:
            r['b0_code'] = wrote_code(b['b0']['reply'])
        r['baseline_cost_usd'] = round(sum(x.get('cost_usd') or 0 for x in b.values()), 3)
    path = os.path.join(work(p), 'judge.json')
    if os.path.exists(path):
        with open(path) as f:
            r['judge'] = {k: v['grade'] for k, v in json.load(f).items()}
    path = os.path.join(work(p), 'out_dry', 'review.json')
    if os.path.exists(path):                                # this prompt's first review, before the agents were confined
        with open(path) as f:
            kinds = collections.Counter(kind_of(q) for q in json.load(f)['queue'])
        r['dry'] = {'questions': dict(kinds), 'levels': levels(kinds)}
        path = os.path.join(work(p), 'judge_dry.json')
        if os.path.exists(path):
            with open(path) as f:
                r['dry']['judge'] = {k: v['grade'] for k, v in json.load(f).items()}
    return r


ALONE = ('b1', 'b2', 'b0')


def spread(xs: list) -> dict:
    return {'mean': round(statistics.mean(xs), 2), 'median': statistics.median(xs), 'max': max(xs)} if xs else {}


def cross(rs: list, missed_by: tuple, caught_by: tuple) -> dict:
    """For each of missed_by: the prompts where the judge did not rate it good,
    and on how many of those it rated each of caught_by good."""
    res = {}
    for a in missed_by:
        miss = [r for r in rs if r['judge'].get(a) != 2]
        res[a] = {'missed': len(miss), **{b: sum(r['judge'].get(b) == 2 for r in miss) for b in caught_by}}
    return res


def summary(ps: list[dict]):
    rows = [row(p) for p in ps]
    agg = {}
    for v in VARIANTS:
        rs = [r for r in rows if r['variant'] == v]
        ok = [r for r in rs if r['check'] == 'ok']
        a = {'prompts': len(rs), 'reviewed': len(ok),
             'fcp_asks': sum(bool(r['questions']) for r in ok),
             'fcp_asks_with_a_call': sum(r['formal'] > 0 for r in ok),
             'fcp_questions': sum(sum(r['questions'].values()) for r in ok),
             'fcp_questions_with_a_call': sum(r['formal'] for r in ok),
             'fcp_asks_hard': sum(r['levels']['hard'] > 0 for r in ok),
             'fcp_questions_hard': sum(r['levels']['hard'] for r in ok),
             'per_prompt': {**{k: spread([r['levels'][k] for r in ok]) for k in LEVELS},
                            'all': spread([sum(r['questions'].values()) for r in ok])},
             'kinds': dict(sum((collections.Counter(r['questions']) for r in ok), collections.Counter())),
             'b1_asks': sum(bool(r.get('b1_asks')) for r in rs), 'b2_asks': sum(bool(r.get('b2_asks')) for r in rs),
             'b0_code': sum(bool(r.get('b0_code')) for r in rs)}
        if v != 'original':
            who = tuple(SETS) + ALONE
            a['good'] = {k: sum((r.get('judge') or {}).get(k) == 2 for r in rs) for k in who}
            a['fair'] = {k: sum((r.get('judge') or {}).get(k) == 1 for r in rs) for k in who}
            both = [r for r in ok if r.get('judge')]
            a['alone_missed'] = cross(both, ALONE, tuple(SETS))
            a['fcp_missed'] = cross(both, tuple(SETS), ALONE)
        agg[v] = a
    both = [r for r in rows if r['variant'] != 'original' and r['check'] == 'ok' and r.get('judge')]
    rewrites = {'reviewed_and_judged': len(both),
                'good': {k: sum(r['judge'].get(k) == 2 for r in both) for k in tuple(SETS) + ALONE},
                'alone_missed': cross(both, ALONE, tuple(SETS)), 'fcp_missed': cross(both, tuple(SETS), ALONE)}
    every = [r for r in rows if r['variant'] != 'original' and r.get('judge')]
    rewrites['all'] = {'judged': len(every), 'not_reviewed': sum(r['check'] != 'ok' for r in every),
                       'good': {k: sum(r['judge'].get(k) == 2 for r in every) for k in tuple(SETS) + ALONE},
                       'alone_missed': cross(every, ALONE, tuple(SETS)),     # no review: no question, not good
                       'fcp_missed': cross(every, tuple(SETS), ALONE)}
    done = [r for r in rows if r['agents']]
    out = {'benchmark': 'HumanEvalComm (Wu and Fard, ACM TOSEM 2025), HumanEvalComm_v2.jsonl at commit 794a91f',
           'model': MODEL, 'tasks': sorted({r['task'] for r in rows}, key=number), 'by_variant': agg,
           'rewrites': rewrites,
           'agents': {'failed': [f'{r["task"]} {r["variant"]}: {r["agents"]}' for r in done if r['agents'] != 'ok'],
                      'lint_errors': [f'{r["task"]} {r["variant"]}' for r in done if r['lint'] not in (None, 'clean')],
                      'check_errors': [f'{r["task"]} {r["variant"]}: {r["check"]}' for r in done
                                       if r['check'] not in (None, 'ok')],
                      'unsandboxed': [f'{r["task"]} {r["variant"]}' for r in done if r['runs'] and not r['sandboxed']],
                      'seconds': sum(r['seconds']['agents'] or 0 for r in done),
                      'cost_usd': round(sum(r['cost_usd'] for r in done), 2)},
           'check_seconds': sum(r['seconds']['check'] or 0 for r in done), 'prompts': rows}
    with open(RESULT, 'w') as f:
        json.dump(out, f, indent=1)
    for v, a in agg.items():
        print(v, {k: x for k, x in a.items() if k != 'kinds'}, a['kinds'])
    print('rewrites', rewrites)
    for r in rows:
        if 'dry' in r and 'levels' in r:
            print('twice', number(r['task']), r['variant'], 'then', r['dry']['levels'], r['dry'].get('judge'),
                  'now', r['levels'], r.get('judge'))
    print({k: x for k, x in out['agents'].items()}, 'check seconds', out['check_seconds'])


# ---------------------------------------------------------------- what the agents touched

PATH_RE = re.compile(r'(?<![\w.~-])(~?/[\w.+@-]+(?:/[\w.+@-]+)*)')
ELSEWHERE = re.compile(r'\$\{?(?:HOME|PWD|OLDPWD|USER|TMPDIR|XDG_\w+|CLAUDE\w*)\b|~')
EXPECTED = (os.path.join(ROOT, 'bin', 'fcp'), os.path.join(ROOT, '.venv', 'bin'), '/dev/null', '/usr/bin', '/bin')
REFUSED = re.compile(r"Permission to use .{0,4000}has been denied|For security, Claude Code may only|"
                     r"requires? (?:explicit )?approval|needs approval|redirection .{0,400}was blocked|"
                     r"haven't granted it yet|can't be checked before it runs|cannot be auto-allowed|"
                     r"Contains brace with quote character|Arithmetic expansion references|"
                     r"Parser skipped input|changes assignment semantics|can hide arguments from path validation|"
                     r"is runtime-determined|"
                     r"is outside the workspace|is not available to an agent", re.S)
LAUNCHER = ('is outside the workspace', 'is not available to an agent')


def calls_of(path: str) -> list[dict]:
    """The tool calls of one transcript, each with its outcome: `ran`,
    `refused` (by Claude Code's permissions or by the launcher), `error` (it
    ran and failed, a lint error for one), or `no result`."""
    calls, by_id = [], {}
    with open(path) as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            c = (d.get('message') or {}).get('content') if isinstance(d, dict) else None
            for x in c if isinstance(c, list) else []:
                if not isinstance(x, dict):
                    continue
                if x.get('type') == 'tool_use':
                    by_id[x.get('id')] = call = {'tool': x.get('name', '?'), 'input': x.get('input') or {},
                                                 'outcome': 'no result', 'result': ''}
                    calls.append(call)
                elif x.get('type') == 'tool_result' and x.get('tool_use_id') in by_id:
                    t = x.get('content')
                    text = t if isinstance(t, str) else \
                        ' '.join(y.get('text', '') for y in t or [] if isinstance(y, dict))
                    call = by_id[x['tool_use_id']]
                    call['result'] = text
                    call['outcome'] = 'ran' if not x.get('is_error') else \
                        'refused' if REFUSED.search(text) else 'error'
                    if call['tool'] == 'Bash' and any(s in text for s in LAUNCHER):
                        call['outcome'] = 'refused'     # the launcher said no, whatever a pipe made of its exit code
    return calls


def names(call: dict) -> str:
    """What a call says about where it works: a command, or the path of a file tool."""
    i = call['input']
    if call['tool'] == 'Bash':
        return str(i.get('command', ''))
    if call['tool'] in ('Read', 'Write', 'Edit'):
        return str(i.get('file_path', ''))
    return json.dumps(i)


def slug(ws: str) -> str:
    """The name Claude Code gives a session's own directories: its scratch
    directory /tmp/claude-<uid>/<slug>/ (in the sandbox, a /tmp of its own)
    and ~/.claude/projects/<slug>/ (in the sandbox, <out>/sessions)."""
    return re.sub(r'[^A-Za-z0-9]', '-', ws)


def programs(command: str) -> list[str]:
    """The programs a shell command starts, roughly: the first word of each of its parts."""
    found = []
    for part in re.split(r'&&|\|\||[;|\n]', command):
        words = part.split()
        while words and (re.fullmatch(r'[A-Za-z_]\w*=.*', words[0]) or words[0] in ('time', '{', '(', 'then', 'do')):
            words = words[1:]
        if words and words[0] == 'timeout':
            words = words[2:]
        if words and re.fullmatch(r'[\w./-]+', words[0]):
            fcp = words[0].endswith('/fcp') and len(words) > 1
            found.append('fcp --help' if fcp and ('--help' in words or '-h' in words) else
                         'fcp ' + words[1] if fcp else os.path.basename(words[0]))
    return found


def audit(ps: list[dict]):
    """Every tool call in the transcripts of the agents of these reviews, with
    its outcome.  A call is listed when it names a path that is neither inside
    the agent's own workspace, nor one of its session's own directories, nor
    the fcp launcher; a parent directory; the home; or a tool other than the
    four an agent has.  Listed and refused: the confinement held.  Listed and
    not refused: to be read by hand, since a reading must rest on the request
    alone.  Also listed: the agents whose run was not sandboxed, and those
    that left no transcript."""
    tools, outside, launcher, unboxed, silent = {}, [], [], [], []
    ran, own = collections.Counter(), collections.Counter()
    roots = tuple('/' + d for d in os.listdir('/'))
    sessions = reviews = 0
    for p in ps:
        d = work(p)
        for o in sorted(x for x in os.listdir(d) if x == 'out' or x.startswith('out_try')):
            out, who = os.path.join(d, o), {'task': p['task'], 'variant': p['variant'], 'attempt': o}
            reviews += 1
            for a in AGENTS:
                run = os.path.join(out, 'agents', a, 'run.json')
                if not os.path.exists(run):
                    continue
                with open(run) as f:
                    if not (json.load(f).get('run') or {}).get('sandbox'):
                        unboxed.append({**who, 'agent': a})
                ws, found = os.path.join(d, 'out', 'ws_' + a), 0     # where it ran: an attempt is renamed later
                mine = (ws, f'/tmp/claude-{os.getuid()}/{slug(ws)}',
                        os.path.join(os.path.expanduser('~'), '.claude', 'projects', slug(ws)))
                for top, _, files in os.walk(os.path.join(out, 'sessions', 'ws_' + a)):
                    for name in sorted(files):
                        if not name.endswith('.jsonl'):
                            continue
                        found += 1
                        for call in calls_of(os.path.join(top, name)):
                            t = tools.setdefault(call['tool'], collections.Counter())
                            t[call['outcome']] += 1
                            text = names(call)
                            if call['tool'] == 'Bash' and call['outcome'] == 'ran':
                                ran.update(programs(text))
                            paths = [q for q in PATH_RE.findall(text)
                                     if q.startswith('~') or q == '/' or q.startswith(roots)]
                            if any(q.startswith(m + '/') or q == m for q in paths for m in mine[1:]):
                                own[call['outcome']] += 1   # its session's scratch or memory directory
                            bad = [q for q in paths if not (q.startswith(EXPECTED) or
                                                            any(q == m or q.startswith(m + '/') for m in mine))]
                            if bad or '..' in text.replace('...', '') or ELSEWHERE.search(text) \
                                    or call['tool'] not in ('Read', 'Write', 'Edit', 'Bash'):
                                outside.append({**who, 'agent': a, 'tool': call['tool'], 'outcome': call['outcome'],
                                                'paths': sorted(set(bad)), 'call': text[:400],
                                                'result': call['result'][:300]})
                            if any(s in call['result'] for s in LAUNCHER) and call['outcome'] == 'refused':
                                launcher.append({**who, 'agent': a, 'call': text[:400], 'result': call['result'][:300]})
                sessions += found
                if not found:
                    silent.append({**who, 'agent': a})
    got = collections.Counter(o['outcome'] for o in outside)
    res = {'reviews': reviews, 'sessions': sessions, 'tool_calls': {k: dict(v) for k, v in sorted(tools.items())},
           'programs_run': dict(ran.most_common()), 'own_session_directories': dict(own),
           'outside': {'calls': len(outside), **got, 'list': outside},
           'launcher_refusals': launcher, 'not_sandboxed': unboxed, 'no_transcript': silent}
    with open(os.path.join(REPO, 'audit.json'), 'w') as f:
        json.dump(res, f, indent=1)
    print(reviews, 'reviews,', sessions, 'transcripts', res['tool_calls'])
    for o in outside:
        print(' ', number(o['task']), o['variant'], o['agent'], o['tool'], o['outcome'].upper(), o['paths'],
              o['call'][:160].replace('\n', ' '))
    print('programs run by Bash:', dict(ran.most_common()))
    print('calls naming the session\'s own scratch or memory directory:', dict(own))
    print(len(outside), 'calls name something outside the workspace:', dict(got))
    print(len(launcher), 'refusals by the launcher;', len(unboxed), 'agents not sandboxed;', len(silent),
          'agents without a transcript')


# ---------------------------------------------------------------- command line

def main():
    args = sys.argv[1:]
    cmd = args[0] if args else 'summary'
    opt = {k: int(args[args.index(k) + 1]) for k in ('--tasks', '--jobs', '--scope', '--conflict', '--compare')
           if k in args}
    if cmd == 'prepare':
        return prepare()
    os.environ['PATH'] = os.path.join(ROOT, '.tools', 'oss-cad-suite', 'bin') + os.pathsep + os.environ['PATH']
    ps = prompts(opt.get('--tasks'))
    if cmd == 'check':                                  # bit-level searches: each prompt in a scope of its own
        check_all(ps, opt.get('--scope', 120), opt.get('--conflict', 300), opt.get('--compare', 300),
                  opt.get('--jobs', 1))
    elif cmd == 'check-one':                            # ... in the process that `check` starts for it
        for p in ps:
            if p['key'] == args[1]:
                check_one(p, opt.get('--scope', 120), opt.get('--conflict', 300), opt.get('--compare', 300))
    elif cmd in ('agents', 'baseline', 'judge'):
        if cmd == 'agents':                             # this study's agents run in the sandbox, or not at all
            from fcp import review as R
            os.environ['FCP_AGENT_SANDBOX'] = '1'
            if R.sandbox_fault():
                sys.exit(f'no sandbox starts on this machine: {R.sandbox_fault()}')
        one = {'agents': agents_one, 'baseline': baseline_one, 'judge': judge_one}[cmd]
        with ThreadPoolExecutor(max_workers=opt.get('--jobs', 3)) as ex:
            list(ex.map(one, ps))
    elif cmd == 'again':                                # again WHY KEY...
        for p in ps:
            if p['key'] in args[2:]:
                again(p, args[1])
    elif cmd == 'collect':
        collect(ps)
    elif cmd == 'audit':
        audit(ps)
    elif cmd == 'summary':
        summary(ps)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
