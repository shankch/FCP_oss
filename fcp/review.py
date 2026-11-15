"""fcp review: the whole protocol on one AI answer, from the request alone.

    fcp review --request request.md --code answer.py [--tests test_answer.py] --out review/
    fcp review --request request.md --code answer_dir/ --entry shop.cart --out review/   (a package)
    fcp review --request request.md --signature stub.py --out review/                    (before any code)

A person who asked an AI assistant for code gets back a short list of
questions about the request, and a verdict per requirement on the code,
instead of having to read every line:

1. adapter: an agent turns the code's signature (never its body) into an
   interface: design.yaml and frame.md, checked by `fcp lint`;
2. decomposer: an agent splits the request into atomic requirements, each
   with a verbatim quote (`fcp anchor` rejects any quote it cannot find);
3. readings: two formalizer agents, isolated from the code and from each
   other, write FCP-PL readings (`fcp lint`, `fcp explain`);
4. the request alone: conflicts, open choices, and the two readings compared
   in context, each with a concrete call;
5. the code: run on the scope against both readings, every failure replayed;
   a pure function on integers and booleans (or a change to one, or code
   that calls a service) is also translated to z3 terms and checked over
   every call or run the interface can carry (fcp.prove), so a requirement
   can be proved, or broken by calls outside the scope;
6. report: a requirement is certified only if the code passes it under both
   readings, the readings agree on it, and it is in no conflict; everything
   else is a question with a call, an expected answer and the code's answer.

With --signature instead of --code the review stops after step 4: the
questions the request raises before any code is written (the signature is a
file with the def line of the function asked for, bodies ignored).

Agents run headless through the Claude Code CLI (`claude -p`), each in its own
workspace; every prompt and output is recorded under out/agents.
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from typing import Optional

from . import agents as AG

CLAUDE = shutil.which('claude') or os.path.expanduser('~/.local/bin/claude')
EXAMPLES = ['code_checkout', 'code_mask', 'code_limit', 'code_change', 'code_pay', 'code_invoice']

ADAPTER = """You are an FCP adapter agent.

Workspace: {ws}
It contains spec.md (a request someone gave an AI coding assistant),
signature.txt (the signature of the code the assistant wrote, without its
body), docs/IR_spec.md (the FCP IR), and examples/, the design.yaml and
frame.md of checked designs: a function on integers (code_checkout), a
function on strings (code_mask), an object (code_limit), a change to
existing code (code_change), code acting through a service it receives
(code_pay) and a function of records, dicts and lists of dicts
(code_invoice). An object with several methods is described in
docs/IR_spec.md (`methods`).

Task: write {ws}/design.yaml and {ws}/frame.md, which say how calls of this
code become the cycles of a trace, as in the examples:
- one input signal per argument and one output signal per returned value,
  each wide enough for every value the request allows and the values just
  outside it (a string or list is a signal with a `length`); an `outcome`
  signal coded as in the examples, with the exceptions the request names;
- the `function` section (name, args, returns, outcome; `class` for a
  method of an object, `methods` for several; `record` and `records` for
  dicts; `interface` for a service the code receives; a `scope` with the
  values the request talks about);
- docs: SPEC (spec.md) and FRAME (frame.md); frame rules for outputs that are
  zero unless the call returned, as in the examples;
- frame.md explains the encoding to someone who will formalize the request.
Describe the interface only: do not restate or interpret the request's rules.
Signals are unsigned, so negative integers are not part of the trace (frame.md
says so), and `raises` is `[]` when the request names no exception. Each
frame rule cites a requirement that states it: add it to
{ws}/requirements.yaml (id R-FR-<n>, doc: FRAME, a verbatim quote of frame.md,
kind: definition, and the `lines` of the quote, which
`{fcp} anchor {ws} {ws}/draft.yaml --out {ws}/requirements.yaml` computes
from a draft without them).

Validate with `{fcp} lint {ws}` until it reports no errors. Work only inside
{ws}. Reply with a one-paragraph summary."""

DECOMPOSER = """You are an FCP specification agent.

Workspace: {ws}
It contains spec.md (a request someone gave an AI coding assistant),
design.yaml and frame.md (how calls of the code become a trace) and
docs/IR_spec.md (section 2 describes requirements.yaml).

Task: decompose spec.md into atomic requirements.
1. Write {ws}/requirements_draft.yaml:
     fcp: "0.1"
     design: {design}
     origin: {{kind: agent, role: decomposer, id: decomposer}}
     requirements:
       - id: R-<AREA>-<n>
         doc: SPEC            # or FRAME, for each frame rule of frame.md
         quote: <verbatim sentence or clause>
         text: <atomic, self-contained restatement>
         kind: guarantee | assumption | dont_care | scenario | definition | non_functional
         ambiguity: [{{phrase: ..., readings: [..., ...]}}]   # optional
   Do not write line numbers.
2. Run `{fcp} anchor {ws} {ws}/requirements_draft.yaml --out {ws}/requirements.yaml`.
   It rejects any quote that is not verbatim; fix rejected quotes and re-run.

One requirement per independently checkable obligation. Examples in the
request are scenarios. Flag every ambiguity and every pair of statements that
seem to contradict each other (record a contradiction as an ambiguity on both
requirements). Do not read any file outside {ws}. Reply with a short summary."""


def entry_path(code: str, entry: Optional[str] = None) -> str:
    """The file that holds the entry point: code itself, or in a package
    (a directory) the module entry names (shop.cart -> shop/cart.py)."""
    if not os.path.isdir(code):
        return code
    if not entry:
        raise ValueError(f'{code} is a package: name the module the entry point is in (--entry)')
    base = os.path.join(code, *entry.split('.'))
    return base + '.py' if os.path.exists(base + '.py') else os.path.join(base, '__init__.py')


def signature(code: str, entry: Optional[str] = None) -> str:
    """The entry point of the code as a reader of the request needs it: every
    top-level function's def line and every class with its method def lines,
    without bodies or docstrings.  For a package, those of the entry module."""
    with open(entry_path(code, entry)) as f:
        tree = ast.parse(f.read())
    out = [f'# a package; the entry point is in module {entry}'] if os.path.isdir(code) else []
    for n in tree.body:                      # public names only: a private helper's name tells how the code works
        if isinstance(n, ast.FunctionDef) and not n.name.startswith('_'):
            out.append(_def_line(n))
        elif isinstance(n, ast.ClassDef) and not n.name.startswith('_'):
            out.append(f'class {n.name}:')
            for m in n.body:
                if isinstance(m, ast.FunctionDef) and (not m.name.startswith('_') or m.name == '__init__'):
                    out.append('    ' + _def_line(m))
    return '\n'.join(out) + '\n'


def _def_line(n: ast.FunctionDef) -> str:
    args = ast.unparse(n.args)
    ret = f' -> {ast.unparse(n.returns)}' if n.returns is not None else ''
    return f'def {n.name}({args}){ret}: ...'


class Reply(str):
    """An agent's final reply, with what the run cost (meta)."""
    meta: dict = {}


def agent_command(prompt: str, model: str) -> list[str]:
    """The command of one agent, to be run in its workspace.  The agent has
    four tools (Read, Write, Edit, Bash), no web and no MCP server.  No
    permission reaches beyond the working directory: Claude Code refuses the
    file tools, and the commands that read or edit files, on any path outside
    it, and refuses interpreters, scripts and every other program but the
    fcp launcher, which in turn works on the agent's workspace only, inside a
    memory and a time limit (FCP_AGENT_WS, fcp.cli.agent_refusal, limited).
    Permissions alone still let a shell list the machine's processes and the
    names in a directory elsewhere, and read a file through xargs; those
    commands are denied by name here, and the agent runs in a sandbox where
    there is nothing else to list or read (sandbox())."""
    return [CLAUDE, '-p', prompt, '--model', model, '--output-format', 'json',
            '--permission-mode', 'acceptEdits', '--strict-mcp-config', '--tools', 'Read,Write,Edit,Bash',
            '--allowedTools', f'Bash({AG.FCP}:*)', 'Bash(ls:*)', 'Bash(cat:*)',
            '--disallowedTools', *(f'Bash({c}:*)' for c in DENIED)]


DENIED = ('ps', 'pgrep', 'pidof', 'top', 'pstree', 'tree', 'du', 'xargs')
SYSTEM_DIRS = ('usr', 'bin', 'sbin', 'lib', 'lib32', 'lib64', 'libx32', 'etc', 'sys')
CLAUDE_KEEP = ()                           # the directories of ~/.claude an agent's Claude Code still finds filled
CLAUDE_FIXED = ('settings.json',)          # the files of ~/.claude it can read and cannot change


def programs() -> list[str]:
    """What an agent runs, to be found in its sandbox: Claude Code, and the fcp
    launcher with its package, its interpreter and its tools."""
    pkg = os.path.dirname(os.path.abspath(__file__))
    need = [os.path.realpath(CLAUDE), pkg, os.path.dirname(AG.FCP),
            os.path.join(os.path.dirname(pkg), '.tools', 'oss-cad-suite'),
            sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix]
    need += [d for d in os.environ.get('FCP_AGENT_BIND', '').split(os.pathsep) if d]
    seen = []
    for d in need:
        if os.path.exists(d) and d not in seen and not d.startswith(('/usr/', '/etc/')) and d != '/usr':
            seen.append(d)
    return seen


def bwrap() -> Optional[str]:
    """The system's bubblewrap.  The PATH is asked last: a tool suite put in
    front of it may bring a bubblewrap of its own that does not start here."""
    for b in ('/usr/bin/bwrap', '/bin/bwrap', '/usr/local/bin/bwrap'):
        if os.access(b, os.X_OK):
            return b
    return shutil.which('bwrap')


def sandbox(ws: str) -> Optional[tuple[list[str], list[int]]]:
    """The bubblewrap prefix that confines one agent to its workspace, and the
    file descriptors it reads; None where there is no bubblewrap (or with
    FCP_AGENT_SANDBOX=0), and then the agent is held by its permissions alone.

    Inside, the file system is put together from a list, so what is not on the
    list does not exist there: the system directories, read-only; what the
    agent runs (programs()), read-only; a private /tmp; the workspace,
    read-write; and of the user's own files only what Claude Code needs to log
    in: ~/.claude with its directories empty (the user's plugins, skills and
    past sessions are not there), the user's settings read-only, the prompt
    history empty and the session records going to <out>/sessions/<workspace>,
    and a throwaway copy of ~/.claude.json.  No home directory, no checkout of
    a repository, no other workspace.  The agent is alone in its process
    table, so it sees no other command line.  The network stays: the agent is
    a model behind an API.

    ~/.claude itself is the real directory, writable: Claude Code renews its
    login by renaming a new file into it under a lock it keeps there, and a
    copy would leave the user's other sessions with a login that has been
    replaced.  So the login is the one thing of the user's that an agent's
    process can reach, and what keeps the model from it is the first layer
    (agent_command): no tool reads or writes outside the workspace."""
    exe = bwrap()
    if not exe or os.environ.get('FCP_AGENT_SANDBOX') == '0':
        return None
    home, real = os.path.expanduser('~'), os.path.realpath(ws)
    a = [exe, '--unshare-pid', '--unshare-ipc', '--unshare-uts', '--die-with-parent', '--new-session',
         '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp']
    for d in SYSTEM_DIRS:
        if os.path.islink('/' + d):
            a += ['--symlink', os.readlink('/' + d), '/' + d]
        elif os.path.isdir('/' + d):
            a += ['--ro-bind', '/' + d, '/' + d]
    resolv = os.path.dirname(os.path.realpath('/etc/resolv.conf'))      # often a link into /run
    if not resolv.startswith(('/etc', '/usr')):
        a += ['--ro-bind', resolv, resolv]
    a += ['--tmpfs', home]
    for d in programs():
        a += ['--ro-bind', d, d]
    conf, fds = os.path.join(home, '.claude'), []
    if os.path.isdir(conf):
        a += ['--bind', conf, conf]
        for e in os.scandir(conf):
            if e.is_dir(follow_symlinks=False) and e.name != 'projects':
                a += ['--ro-bind', e.path, e.path] if e.name in CLAUDE_KEEP else ['--tmpfs', e.path]
            elif e.name in CLAUDE_FIXED and e.is_file(follow_symlinks=False):
                a += ['--ro-bind', e.path, e.path]
        if os.path.isfile(os.path.join(conf, 'history.jsonl')):      # a bind, never a copy: the directory is the real one
            a += ['--dev-bind', '/dev/null', os.path.join(conf, 'history.jsonl')]
        sessions = os.path.join(os.path.dirname(real), 'sessions', os.path.basename(real))
        os.makedirs(sessions, exist_ok=True)
        a += ['--bind', sessions, os.path.join(conf, 'projects')]
    if os.path.isfile(conf + '.json'):
        fds.append(os.open(conf + '.json', os.O_RDONLY))
        a += ['--perms', '0600', '--file', str(fds[0]), conf + '.json']
    return a + ['--bind', real, os.path.abspath(ws), '--chdir', os.path.abspath(ws)], fds


_FAULT: dict = {}
_FAULT_LOCK = threading.Lock()


def sandbox_fault() -> Optional[str]:
    """Why no sandbox starts on this machine; None when one does.  Found by
    starting, once, the sandbox of an empty workspace around a program that
    does nothing."""
    if os.environ.get('FCP_AGENT_SANDBOX') == '0':
        return 'switched off (FCP_AGENT_SANDBOX=0)'
    with _FAULT_LOCK:
        if 'why' not in _FAULT:
            why = None
            with tempfile.TemporaryDirectory() as tmp:
                ws = os.path.join(tmp, 'ws')
                os.makedirs(ws)
                box = sandbox(ws)
                if not box:
                    why = 'no bubblewrap (bwrap) on this machine'
                else:
                    try:
                        p = subprocess.run(box[0] + ['/bin/sh', '-c', ':'], capture_output=True, text=True,
                                           timeout=120, stdin=subprocess.DEVNULL, pass_fds=box[1])
                        if p.returncode:
                            why = ((p.stderr or p.stdout).strip() or f'exit code {p.returncode}')[:300]
                    except (OSError, subprocess.SubprocessError) as e:
                        why = f'{type(e).__name__}: {e}'[:300]
                    finally:
                        for fd in box[1]:
                            os.close(fd)
            _FAULT['why'] = why
        return _FAULT['why']


def run_agent(prompt: str, ws: str, model: str, timeout: int = 3600) -> str:
    """One headless Claude Code run in workspace ws; its final reply.  The run
    is sandboxed where a sandbox starts on this machine (sandbox_fault());
    where none does, the agent is held by its permissions alone, unless
    FCP_AGENT_SANDBOX=1 asks for a sandbox or no run at all.  The reply's meta
    says what the run cost, whether it was sandboxed, and if not, why."""
    ws = os.path.abspath(ws)
    why = sandbox_fault()
    if why and os.environ.get('FCP_AGENT_SANDBOX') == '1':
        raise RuntimeError(f'the agent was to run in a sandbox, and none starts: {why}')
    cmd, box = agent_command(prompt, model), None if why else sandbox(ws)
    env = dict(os.environ, FCP_AGENT_WS=ws)
    t = time.time()
    try:
        if box:
            try:
                p = subprocess.run(box[0] + [os.path.realpath(CLAUDE)] + cmd[1:], cwd=ws, capture_output=True,
                                   text=True, timeout=timeout, stdin=subprocess.DEVNULL, pass_fds=box[1],
                                   env=dict(env, DISABLE_AUTOUPDATER='1'))
            finally:
                for fd in box[1]:
                    os.close(fd)
        else:
            p = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=timeout,
                               stdin=subprocess.DEVNULL, env=env)
    except subprocess.TimeoutExpired:
        r = Reply(f'(no reply: the agent was stopped after {timeout} s)')
        r.meta = {'seconds': round(time.time() - t), 'timeout': True, 'sandbox': bool(box)}
        return r
    try:
        d = json.loads(p.stdout)
        r = Reply(d.get('result', '') or '')
        r.meta = {'seconds': round(time.time() - t), 'cost_usd': d.get('total_cost_usd'),
                  'turns': d.get('num_turns'), 'error': bool(d.get('is_error'))}
    except (json.JSONDecodeError, AttributeError):
        r = Reply((p.stdout + p.stderr)[-4000:])
        r.meta = {'seconds': round(time.time() - t), 'error': True}
    r.meta['sandbox'] = bool(box)
    if why:
        r.meta['sandbox_error'] = why
    return r


def _copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)


def build_bundle(request: str, code: str, out: str, model: str = 'opus', log=print,
                 entry: Optional[str] = None) -> str:
    """Steps 1 and 2: the adapter and the requirements, in out/bundle."""
    bundle = os.path.join(out, 'bundle')
    os.makedirs(bundle, exist_ok=True)
    design = 'review'
    # 1. adapter, from the signature only
    ws = os.path.join(out, 'ws_adapter')
    if os.path.exists(ws):
        shutil.rmtree(ws)
    os.makedirs(os.path.join(ws, 'examples'))
    _copy(request, os.path.join(ws, 'spec.md'))
    with open(os.path.join(ws, 'signature.txt'), 'w') as f:
        f.write(signature(code, entry))
    _copy(os.path.join(AG.ROOT, 'docs', 'IR_spec.md'), os.path.join(ws, 'docs', 'IR_spec.md'))
    for ex in EXAMPLES:
        for fname in ('design.yaml', 'frame.md'):
            _copy(os.path.join(AG.ROOT, 'corpus', ex, fname), os.path.join(ws, 'examples', ex, fname))
    with open(os.path.join(ws, 'requirements.yaml'), 'w') as f:
        f.write(f"fcp: '0.1'\ndesign: {design}\norigin: {{kind: agent, id: adapter, role: decomposer}}\nrequirements: []\n")
    log('  adapter agent ...')
    t = time.time()
    prompt = ADAPTER.format(ws=ws, fcp=AG.FCP)
    if entry:
        prompt += f'\nThe code is a package: set `module: {entry}` in the function section.'
    summary = run_agent(prompt, ws, model)
    if entry:                                  # the package's entry module, whatever the agent wrote
        _set_module(os.path.join(ws, 'design.yaml'), entry)
    AG.record(out, 'adapter', 'adapter', model, prompt,
              {'design.yaml': os.path.join(ws, 'design.yaml'), 'frame.md': os.path.join(ws, 'frame.md')}, summary)
    log(f'    {round(time.time() - t)}s')
    for fname in ('spec.md', 'design.yaml', 'frame.md'):
        _copy(os.path.join(ws, fname), os.path.join(bundle, fname))
    # 2. decomposer
    ws2 = os.path.join(out, 'ws_decomposer')
    if os.path.exists(ws2):
        shutil.rmtree(ws2)
    for fname in ('spec.md', 'design.yaml', 'frame.md'):
        _copy(os.path.join(bundle, fname), os.path.join(ws2, fname))
    _copy(os.path.join(AG.ROOT, 'docs', 'IR_spec.md'), os.path.join(ws2, 'docs', 'IR_spec.md'))
    log('  decomposer agent ...')
    t = time.time()
    prompt = DECOMPOSER.format(ws=ws2, design=design, fcp=AG.FCP)
    summary = run_agent(prompt, ws2, model)
    AG.record(out, 'decomposer', 'decomposer', model, prompt,
              {'requirements.yaml': os.path.join(ws2, 'requirements.yaml')}, summary)
    log(f'    {round(time.time() - t)}s')
    _copy(os.path.join(ws2, 'requirements.yaml'), os.path.join(bundle, 'requirements.yaml'))
    os.makedirs(os.path.join(bundle, 'formal'), exist_ok=True)
    return bundle


def formalize(bundle: str, out: str, model: str = 'opus', log=print) -> list[str]:
    """Step 3: two isolated formalizer agents, at the same time."""
    from concurrent.futures import ThreadPoolExecutor

    def one(s, prefix):
        ws = os.path.join(out, f'ws_{s}')
        AG.workspace(bundle, 'formalizer', ws, s)
        prompt = AG.prompt('formalizer', ws, 'review', s, prefix=prefix)
        prompt = prompt.replace('the FCP IR and the FCP-PL property language).',
                                'the FCP IR and the FCP-PL property language).\nframe.md defines how calls of '
                                'the code become cycles of the trace; read it\nbefore formalizing.', 1)
        t = time.time()
        summary = run_agent(prompt, ws, model)
        src = os.path.join(ws, 'formal', f'{s}.yaml')
        AG.record(out, 'formalizer', s, model, prompt, {f'formal/{s}.yaml': src}, summary)
        log(f'  formalizer {s}: {round(time.time() - t)}s')
        if os.path.exists(src):
            _copy(src, os.path.join(bundle, 'formal', f'{s}.yaml'))
            return s
        return None
    log('  two formalizer agents ...')
    with ThreadPoolExecutor(max_workers=2) as ex:
        done = list(ex.map(lambda x: one(*x), (('agent_a', 'RA'), ('agent_b', 'RB'))))
    return [s for s in done if s]


def agreed_answers(bundle: str, sets: list[str]) -> list[dict]:
    """Flagged phrases on which every reading recorded the same reading
    (`decisions`), each with the first other reading the decomposer listed:
    nothing in the readings shows what that answer decides.  A phrase that a
    reading did not record is left out."""
    import yaml
    with open(os.path.join(bundle, 'requirements.yaml')) as f:
        reqs = {r['id']: r for r in yaml.safe_load(f)['requirements']}
    chosen: dict[tuple, set] = {}
    for st in sets:
        with open(os.path.join(bundle, 'formal', f'{st}.yaml')) as f:
            fs = yaml.safe_load(f) or {}
        for dc in fs.get('decisions') or []:
            chosen.setdefault((dc['req'], dc['phrase']), set()).add((st, int(dc['reading'])))
    out = []
    for (rid, phrase), picks in chosen.items():
        if {st for st, _ in picks} != set(sets) or len({k for _, k in picks}) != 1:
            continue                           # undecided by one, or the readers differ: compared anyway
        k = next(iter(picks))[1]
        amb = next((a for a in reqs.get(rid, {}).get('ambiguity') or [] if a.get('phrase') == phrase), None)
        others = [(j, x) for j, x in enumerate((amb or {}).get('readings') or [], 1) if j != k]
        if others:
            out.append({'req': rid, 'phrase': phrase, 'taken': k, 'variant': others[0][0], 'text': others[0][1]})
    return out


VARIANT = """
Both other readers of this request read the phrases below the same way. Read
each of them instead as given here, even where another reading seems more
natural, and say so in the note of every item it affects:
{lines}
"""


def variant(bundle: str, out: str, sets: list[str], model: str = 'opus', log=print) -> Optional[str]:
    """Step 3b: one more isolated formalizer, with every flagged phrase that
    the readers answered alike read the other way.  The requirements on which
    it differs from them depend on those answers."""
    answers = agreed_answers(bundle, sets)
    if not answers:
        return None
    ws = os.path.join(out, 'ws_variant')
    AG.workspace(bundle, 'formalizer', ws, 'variant')
    prompt = AG.prompt('formalizer', ws, 'review', 'variant', prefix='RV')
    prompt = prompt.replace('the FCP IR and the FCP-PL property language).',
                            'the FCP IR and the FCP-PL property language).\nframe.md defines how calls of '
                            'the code become cycles of the trace; read it\nbefore formalizing.', 1)
    lines = '\n'.join(f'- {a["req"]}, "{a["phrase"]}": {a["text"]}' for a in answers)
    prompt = prompt.replace('\nRules:', VARIANT.format(lines=lines) + '\nRules:', 1)
    log(f'  variant formalizer: {len(answers)} answers the readers shared ...')
    t = time.time()
    summary = run_agent(prompt, ws, model)
    src = os.path.join(ws, 'formal', 'variant.yaml')
    AG.record(out, 'formalizer', 'variant', model, prompt, {'formal/variant.yaml': src}, summary)
    log(f'    {round(time.time() - t)}s')
    if not os.path.exists(src):
        return None
    _copy(src, os.path.join(bundle, 'formal', 'variant.yaml'))
    with open(os.path.join(bundle, 'formal', 'variant_answers.json'), 'w') as f:
        json.dump(answers, f, indent=1)
    return 'variant'


def _set_module(path: str, entry: str):
    import yaml
    if not os.path.exists(path):
        return
    with open(path) as f:
        d = yaml.safe_load(f)
    if isinstance(d, dict) and isinstance(d.get('function'), dict) and d['function'].get('module') != entry:
        d['function']['module'] = entry
        with open(path, 'w') as f:
            yaml.safe_dump(d, f, sort_keys=False)


JOBS = 8                                   # engine tasks of a review that run at a time
STEP_SECONDS = 900                         # a step of a watched check that runs longer is stopped ...
CHECK_SECONDS = 3600                       # ... and after this long, what is left of the check is not run


def scenarios(cons: dict) -> dict:
    """What a review takes from the scenario search of one reading (the
    result of Session.consistency).  'impossible': the formal example cannot
    happen by itself.  'forbidden': it can, and the reading's rules exclude
    it.  'blocked': the rules exclude it, and the search that tells those two
    apart did not end.  'undecided': the search did not end; the requirement
    is then not settled, and the report names the search."""
    def ids(ks):
        return [k[9:-1] for k in ks if k.startswith('scenario(')]
    told = set(cons.get('impossible_scenarios', [])) | set(cons.get('forbidden_scenarios', [])) | \
        {i for c in cons.get('conflicts', []) for i in ids(c['situations'])}
    return {'impossible': list(cons.get('impossible_scenarios', [])),
            'forbidden': list(cons.get('forbidden_scenarios', [])),
            'blocked': [i for i in ids(cons.get('blocked', [])) if i not in told],
            'undecided': ids(cons.get('undecided', []))}


def why_failed(e: BaseException) -> str:
    """One line on why a step raised."""
    from .smt import TranslationFailed
    text = ' '.join(str(e).split())
    if isinstance(e, TranslationFailed):
        return text
    return (type(e).__name__ + (f': {text}' if text else ''))[:300]


class Steps:
    """The steps of one check, and what each returned.  A step runs once.
    One that raises is recorded as failed with the reason, and the check goes
    on with the next step: `run` then gives the step's empty result.  With a
    path, the record is a file, written before and after every step: a check
    started again on that file runs only the steps the file does not hold,
    which is how `supervised` goes on after it stopped a step.  In the file,
    'running' names the step that runs and when it began; 'stop' says that
    no further step is to run, and why; a step recorded with 'again' is run
    once more, one engine task at a time.  A failed step on which the
    verdicts rest can name, under 'reqs', the only requirements that rest on
    it (see run)."""

    def __init__(self, path: Optional[str] = None, log=print, S=None):
        self.path, self.log, self.S = path, log, S
        self.d: dict = {}
        if path and os.path.exists(path):
            with open(path) as f:
                self.d = json.load(f)
        self.d.setdefault('steps', {})

    def save(self):
        if self.path:
            _write_json(self.path, self.d)

    def failed(self, name: str) -> bool:
        return 'failed' in self.d['steps'].get(name, {})

    def run(self, name: str, f, empty, rests: str = 'all', reading: Optional[str] = None, needs: Optional[str] = None,
            reqs: Optional[list] = None):
        """The result of step `name`: what it returned when it ran, f() now,
        or `empty` when it failed.  rests: what rests on the step, 'all' the
        requirements, the 'scenarios' of `reading`, or 'none' of the
        verdicts.  needs: a step without which this one is not run.  reqs:
        for a step with rests 'all' whose `empty` holds what the step gives
        for some requirements whatever it does, the other requirements: the
        only ones that rest on the step when it fails.  The failed record
        keeps rests 'all' and names them under 'reqs', so that a reader of
        the file or of the review that does not know 'reqs' takes every
        requirement to rest on the step.  None: every requirement does."""
        rec = self.d['steps'].get(name)
        if rec is None or 'again' in rec:
            if self.d.get('stop'):
                rec = {'failed': 'not run: ' + self.d['stop']}
            elif needs and self.failed(needs):
                rec = {'failed': f'not run: {needs} did not end'}
            else:
                rec = self._run(name, f, alone=rec is not None)
            self.d['steps'][name] = rec
            self.d.pop('running', None)
        if 'rests' not in rec:                 # also of a step that `supervised` stopped
            rec.update(rests=rests, reading=reading)
            if reqs is not None and 'failed' in rec:       # the only requirements that rest on it
                rec['reqs'] = list(reqs)
            self.save()
        return empty if 'failed' in rec else rec['result']

    def _run(self, name: str, f, alone: bool) -> dict:
        from . import software as SW
        self.log(f'  {name}' + (', one task at a time' if alone else ''))
        n, t = len(SW.BUDGET_HIT), time.time()
        self.d['running'] = {'step': name, 'since': t, 'again': alone}
        self.save()
        keep = (self.S.runner.jobs, SW.BIT_JOBS)
        if alone:
            self.S.runner.jobs, SW.BIT_JOBS = 1, 1
        try:
            rec = {'result': f()}
            if self.path:                      # the shapes a later process reads back from the file
                rec = json.loads(json.dumps(rec, default=str))
        except Exception as e:
            rec = {'failed': why_failed(e)}
            self.log(f'  {name}: failed ({rec["failed"]})')
            traceback.print_exc()
        finally:
            self.S.runner.jobs, SW.BIT_JOBS = keep
        rec.update(cut=SW.BUDGET_HIT[n:], seconds=round(time.time() - t, 1))
        return rec

    def summary(self) -> tuple[list[dict], list[dict]]:
        """(every step with its seconds, the steps that failed: each with the
        reason, what rests on it and, where the step names them, the only
        requirements that do)."""
        recs = self.d['steps']
        return ([{'step': n, 'seconds': r.get('seconds'), **({'failed': r['failed']} if 'failed' in r else {})}
                 for n, r in recs.items()],
                [{'step': n, 'why': r['failed'], 'rests': r.get('rests', 'all'), 'reading': r.get('reading'),
                  **({'reqs': r['reqs']} if 'reqs' in r else {})}
                 for n, r in recs.items() if 'failed' in r])


def _write_json(path: str, d: dict):
    with open(path + '.tmp', 'w') as f:
        json.dump(d, f, default=str)
    os.replace(path + '.tmp', path)


def check(bundle: str, code: Optional[str], sets: list[str], log=print, scope_budget: float = 120,
          conflict_budget: float = 300, compare_budget: float = 300, jobs: int = JOBS,
          state: Optional[str] = None) -> dict:
    """Steps 4 and 5 on a bundle with readings: the request alone, then the
    code (step 4 only when code is None).  Each search has a time budget
    (seconds), so that a review answers in minutes; the report names every
    search the budget cut short.  jobs: the engine tasks that run at a time
    (one task of a large reading takes 1 GB).  Every search is a step with a
    name (Steps).  A step that raises is listed under 'failed' with the
    reason and the check goes on: the verdicts then certify nothing that
    rests on it, and the report says that the review is partial.  Where the
    comparison of the two readings in context fails and the one without
    context ended, a requirement that the latter closed in both directions
    keeps its agreement, and the failed step names the others, which alone
    rest on it (SW.carried_over; not for a bounded comparison).  state: a
    file that keeps what every step returned (see Steps and `supervised`)."""
    from . import effects as FX
    from . import software as SW
    from .analyses import Session
    SW.SCOPE_BUDGET, SW.CONFLICT_BUDGET, SW.COMPARE_BUDGET = scope_budget, conflict_budget, compare_budget
    SW.BUDGET_HIT.clear()
    has_variant = os.path.exists(os.path.join(bundle, 'formal', 'variant.yaml'))
    S = Session(bundle, sets=sets + (['variant'] if has_variant else []), jobs=jobs)
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    st = Steps(state, log, S)
    out = {'sets': sets, 'prompt': {}, 'readings': {}, 'code': {}, 'given': given(S, sets)}
    cut: list[str] = []                        # the searches that did not end, or that leave a rule out
    for s in sets:
        sc = out.setdefault('scenarios', {})[s] = st.run(
            f'the scenarios of {s}', lambda: scenarios(S.consistency(s, pairs=False, scenarios_only=True)),
            {'impossible': [], 'forbidden': [], 'blocked': [], 'undecided': []}, rests='scenarios', reading=s)
        if sc['undecided'] or sc['blocked']:
            cut.append(f'the scenarios of {s}: ' + ', '.join(sc['undecided'] + sc['blocked']))
        none = {'conflicts': [], 'candidates': 0, 'checked': 0}
        if ifc:
            out['prompt'][s] = {'conflicts': st.run(f'the conflicts of {s}', lambda: FX.conflicts(S, s, fn, ifc), none),
                                'open': {'open': {}, 'checked': 0}}
        else:
            out['prompt'][s] = {'conflicts': st.run(f'the conflicts of {s}', lambda: SW.conflicts(S, s, fn), none),
                                'open': st.run(f'the open choices of {s}',
                                               lambda: SW.choices(S, s, fn, fn.rets + [fn.outcome]),
                                               {'open': {}, 'checked': 0})}
        op = out['prompt'][s]['open']
        if op.get('left_out'):                 # rules over a large rigid range: not in these two searches
            cut.append(f'the conflicts and open choices of {s}: these searches leave out '
                       + ', '.join(op['left_out']) + ' (rules stated for every value of a variable)'
                       + (f'; {op["rejected"]} calls with two answers that break them are not reported'
                          if op.get('rejected') else ''))
        elif op.get('rejected'):               # an object: such rules are assumed at the values the calls name
            cut.append(f'the open choices of {s}: {op["rejected"]} call sequences with two answers that break '
                       'a rule stated for every value of a variable are not reported')

    def compared(a: str, b: str, context: bool, plain: Optional[dict] = None):
        if fn.stateful or ifc:
            S.cmp_engine = 'bmc'
            return S.compare(a, b, context=True) if context else S.compare(a, b)
        # undecided directions are kept short; a direction that `plain` (the same comparison without
        # context) closed is closed in context and is not asked again
        return SW.compare(S, a, b, fn, context=context, bit_timeout=300, plain=plain)

    def shown(name: str, a: str, b: str, recs: dict) -> dict:
        """The records of a comparison whose calls a question shows, each call
        run again from its printed line (SW.replayed).  A step of its own: on
        a long call the replay takes minutes and gigabytes, and what it costs
        must not take the comparison with it.  Where the step does not end,
        no call of the comparison is shown."""
        if fn.stateful or ifc or not SW.printable(fn) or not SW.shows(recs):
            return recs
        got = st.run(f'the replay of the calls of {name}', lambda: SW.replayed(S, a, b, fn, recs, context=True),
                     None, rests='none')
        if got is None:
            got = SW.unshown(recs, 'the replay did not end')
        for r, x in got.items():
            for d in ((x.get('dropped') or {}).values() if isinstance(x, dict) else ()):
                out.setdefault('dropped', []).append({'step': name, 'req': r, 'lines': d['lines'], 'why': d['why']})
        return got

    if len(sets) == 2:
        a, b = sets
        first = f'the comparison of {a} and {b}'
        plain = st.run(first, lambda: compared(a, b, False), {}, rests='none')
        # What the comparison in context gives whatever it does: the record of a requirement that the first
        # comparison closed in both directions, and of one that only one reading states (SW.carried_over).
        # When the step fails these records are its result, and the other requirements of the first comparison
        # are the only ones that rest on it.  Nothing is known where the first comparison failed, or for the
        # bounded comparison, which in context can answer NO-CONTEXT on a requirement that is equal without.
        known = None if fn.stateful or ifc or st.failed(first) else SW.carried_over(plain)
        rest = None if known is None else sorted(r for r in plain if r != '<assumptions>' and r not in known)
        ctx = st.run(first + ', in context', lambda: compared(a, b, True, plain), known or {}, reqs=rest)
        ctx = shown(first + ', in context', a, b, ctx)
        out['readings'] = {r: {'plain': plain.get(r, {}).get('relation'), 'context': ctx.get(r, {}).get('relation'),
                               'witness': next((ctx[r][w]['lines'] for w in ('witness_a_not_b', 'witness_b_not_a')
                                                if isinstance(ctx.get(r, {}).get(w), dict)), None),
                               **({'carried': ctx[r]['carried']} if ctx.get(r, {}).get('carried') else {})}
                           for r in (plain or ctx) if r != '<assumptions>'}
    if has_variant:                            # what the answers the readers shared decide
        with open(os.path.join(bundle, 'formal', 'variant_answers.json')) as f:
            out['variant_answers'] = json.load(f)
        dep: dict[str, dict] = {}
        kept: dict[str, str] = {}              # per requirement, the direction of the call that is kept
        for peer in sets:
            # without context first: a direction closed there holds on every run, which is what lets a
            # requirement go without the shared answers (`waiting`), and it is not asked again in context.
            # Nothing rests on this step: where it fails, no direction is closed and the requirements wait
            alone = st.run(f'the comparison of {peer} and variant', lambda: compared(peer, 'variant', False), {},
                           rests='none')
            ctx = st.run(f'the comparison of {peer} and variant, in context',
                         lambda: compared(peer, 'variant', True, alone), {})
            ctx = shown(f'the comparison of {peer} and variant, in context', peer, 'variant', ctx)
            for r, x in ctx.items():
                # an agreement that a replay refuted is no agreement: the requirement is undecided
                rel = 'UNKNOWN' if x.get('refuted') and x['relation'] == 'EQUIVALENT' else x['relation']
                if r != '<assumptions>' and rel not in ('EQUIVALENT', 'ONLY-A', 'ONLY-B'):
                    k, w = next(((k, x[k]['lines']) for k in SW.WITNESSES
                                 if isinstance(x.get(k), dict) and x[k].get('lines')), (None, None))
                    d = dep.setdefault(r, {'relation': rel, 'peers': [], 'witness': None, 'by': {}})
                    d['peers'].append(peer)
                    # per reader: the relation; the directions without a disagreement in context and, of the
                    # comparison without context, by themselves (see `waiting`); those handed over from the
                    # second to the first; and what the searches covered where that is less than every run
                    bound = _bound(x, alone.get(r))
                    d['by'][peer] = {'relation': rel, 'closed': list(SW.closed(x)),
                                     'closed_alone': list(SW.closed(alone.get(r))),
                                     **({'carried': x['carried']} if x.get('carried') else {}),
                                     **({'bound': bound} if bound else {})}
                    # one call per requirement: the first reader's, and a run that a reader accepts and the
                    # variant rejects (what makes a requirement wait once there is code) before any other
                    if w is not None and (d['witness'] is None or
                                          (k == 'witness_a_not_b' and kept.get(r) != 'witness_a_not_b')):
                        d['witness'], kept[r] = w, k
                    if d['relation'] == 'UNKNOWN':     # where the first reader's comparison did not end, the second's
                        d['relation'] = rel
        out['depends'] = dep
    if code is None:                           # before any code: the questions the request raises
        out['code'] = None
    else:
        held: dict = {}                        # the scope and the code's answers on it, drawn once in a process

        def scope() -> dict:
            if not held:
                if ifc:
                    runs = FX.scope(S, fn, ifc)
                    held.update(runs=runs, res=FX.run(fn, ifc, code, runs))
                else:
                    calls = SW.calls_for(S, fn, [code])
                    res = SW.run(fn, code, calls)
                    held.update(calls=calls, res=res, cols=SW.trace(fn, calls, res))
            return held

        def on_scope() -> dict:
            h = scope()
            if ifc:
                ver = {s: FX.verify(S, s, fn, ifc, code, h['runs'], h['res']) for s in sets}
                for v in ver.values():         # the same shape as for functions
                    for x in v.values():
                        if x.get('conversation'):
                            x['calls_shown'] = [{'call': x['call'], 'got': ' ; '.join(x['conversation'])}]
                return {'calls': len(h['runs']), 'verify': ver}
            return {'calls': len(h['calls']), 'outcomes': SW.outcome_summary(fn, h['res'])['counts'],
                    'verify': {s: SW.verify(S, s, fn, code, h['calls'], h['res'], h['cols']) for s in sets}}

        def beyond(s: str) -> dict:
            from . import prove as P
            h = scope()
            if ifc:
                return P.prove_effects(S, s, fn, ifc, code, h['runs'], h['res'])
            return P.prove(S, s, fn, code, h['calls'], h['res'])

        out['code'] = st.run('the code on the scope', on_scope, {'calls': 0, 'verify': {s: {} for s in sets}})
        if ifc or not (fn.stateful or fn.structured or fn.methods):       # integers, booleans, strings, lists
            out['proofs'] = {}
            for s in sets:
                p = st.run(f'the proofs beyond the scope under {s}', lambda: beyond(s), None, rests='none',
                           needs='the code on the scope')
                if p is not None:
                    out['proofs'][s] = p
    out['steps'], out['failed'] = st.summary()
    out['limits'] = list(dict.fromkeys(cut + [x for r in st.d['steps'].values() for x in r.get('cut') or []]))
    out['certified'], out['queue'] = verdicts(S, out)
    return out


# ---------------------------------------------------------------- a check that is watched
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.sysconf('SC_PAGE_SIZE')
CLOSING = 300                              # seconds for the verdicts of a check whose time is up
WORKER = 'import sys; sys.path.insert(0, sys.argv[1]); from fcp.review import worker; sys.exit(worker(sys.argv[2]))'


def _read_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _session(sid: int) -> list[tuple[int, int]]:
    """(pid, resident bytes) of every live process of session sid, from /proc."""
    found = []
    try:
        names = os.listdir('/proc')
    except OSError:
        return found
    for name in names:
        if name.isdigit():
            try:
                with open(f'/proc/{name}/stat') as f:
                    x = f.read().rsplit(')', 1)[1].split()
                if int(x[3]) == sid and x[0] != 'Z':
                    found.append((int(name), int(x[21]) * PAGE))
            except (OSError, IndexError, ValueError):
                pass
    return found


def _stop_session(sid: int, leader: bool = True):
    """Kill every process of session sid: the checking process, the workers
    of its pools and the tools they started.  A process group is not enough:
    sby starts each tool in a group of its own.  leader: the process that
    began the session has not been waited for, so its group still has its
    number."""
    if leader:
        try:
            os.killpg(sid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    for _ in range(100):
        pids = [p for p, _ in _session(sid)]
        if not pids:
            return
        for p in pids:
            try:
                os.kill(p, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        time.sleep(0.05)


def memory_budget(gb: Optional[float] = None) -> Optional[int]:
    """The bytes that the processes of a watched check may hold together: gb
    when given, else FCP_MEMORY_GB (0: no limit).  Otherwise the least of
    8 GB, half of the machine's memory, and 85% of the memory limit of the
    control group this process runs in (a systemd scope with MemoryMax, a
    container): the step that runs is then stopped before the kernel stops
    the whole review."""
    if gb is None and os.environ.get('FCP_MEMORY_GB'):
        gb = float(os.environ['FCP_MEMORY_GB'])
    if gb is not None:
        return int(gb * 2 ** 30) or None
    most = [8 * 2 ** 30]
    try:
        with open('/proc/meminfo') as f:
            most.append(next(int(x.split()[1]) for x in f if x.startswith('MemTotal:')) * 1024 // 2)
    except (OSError, StopIteration, ValueError, IndexError):
        pass
    try:
        with open('/proc/self/cgroup') as f:
            path = next(x.strip()[3:] for x in f if x.startswith('0::'))
        while True:
            p = os.path.join('/sys/fs/cgroup', path.lstrip('/'), 'memory.max')
            if os.path.exists(p):
                with open(p) as f:
                    v = f.read().strip()
                if v != 'max':
                    most.append(int(int(v) * 0.85))
            if path in ('/', ''):
                break
            path = os.path.dirname(path)
    except (OSError, StopIteration, ValueError):
        pass
    return min(most)


def _watch(proc, state: str, budget: Optional[int], step_seconds: float, end: float, peaks: dict) -> Optional[str]:
    """Wait for the checking process.  None when it ended by itself.
    Otherwise it was stopped, and why: 'memory' (its processes held more
    than the budget), 'step' (the step that runs took longer than
    step_seconds; the time before the first step and after the last counts
    as one) or 'check' (the time of the whole check is up).  peaks: step ->
    the most its processes held, in bytes."""
    since, seen, name = time.time(), None, None
    while proc.poll() is None:
        time.sleep(0.25)
        now = time.time()
        try:
            x = os.stat(state)
            m = (x.st_mtime_ns, x.st_ino, x.st_size)
        except OSError:
            m = seen
        if m != seen:                          # a step began or ended: its clock starts again
            seen, run = m, _read_json(state).get('running') or {}
            since, name = run.get('since', now), run.get('step')
        held = sum(r for _, r in _session(proc.pid))
        peaks[name] = max(peaks.get(name, 0), held)
        why = 'memory' if budget and held > budget else 'step' if now - since > step_seconds else \
            'check' if now > end else None
        if why:
            _stop_session(proc.pid)
            proc.wait()
            return why
    _stop_session(proc.pid, leader=False)      # whatever it left behind
    return None


def supervised(bundle: str, code: Optional[str], sets: list[str], log=print, scope_budget: float = 120,
               conflict_budget: float = 300, compare_budget: float = 300, jobs: int = JOBS,
               memory: Optional[float] = None, step_seconds: float = STEP_SECONDS,
               check_seconds: float = CHECK_SECONDS, state: Optional[str] = None,
               worker: Optional[list] = None) -> dict:
    """`check` in a process of its own, watched, so that a review ends with a
    report whatever a step does.  A step that runs longer than step_seconds
    is stopped, and so is a step during which the checking process and all
    it started hold more than the memory budget (memory, in GB: see
    memory_budget): every process of the check is killed, the step is
    recorded as failed with the reason, and a new process goes on with the
    next step.  A step stopped for its memory is first run once more, one
    engine task at a time.  After check_seconds the step that runs is
    stopped and the steps that are left are not run.  Returns what `check`
    returns, each step with the most memory it held ('peak_gb'); when the
    check gave no verdicts at all (it did not start, or it ended outside its
    steps), what `unchecked` returns.  state: the file of the steps (kept;
    without it a temporary one).  worker: the command that runs the check on
    a state file (for tests)."""
    tmp = None if state else tempfile.mkdtemp(prefix='fcp_check_')
    state = state or os.path.join(tmp, 'state.json')
    budget, peaks, proc, t0 = memory_budget(memory), {}, None, time.time()
    limit = f'the check reached its time limit of {check_seconds:g} s'
    _write_json(state, {'steps': {}, 'args': {
        'bundle': bundle, 'code': code, 'sets': sets, 'scope_budget': scope_budget,
        'conflict_budget': conflict_budget, 'compare_budget': compare_budget, 'jobs': jobs,
        'watcher': os.getpid()}})
    cmd = worker or [sys.executable] + (['-I'] if sys.flags.isolated else []) + ['-u', '-c', WORKER, ROOT]
    open(state + '.err', 'w').close()          # what the checking processes print as errors
    try:
        for _ in range(1000):                  # every round ends the check or settles one step
            d = _read_json(state)
            if 'out' in d or 'error' in d:
                break
            if time.time() - t0 > check_seconds and not d.get('stop'):
                d['stop'] = limit
                _write_json(state, d)
            with open(state + '.err', 'a') as err:
                proc = subprocess.Popen(cmd + [state], stdout=subprocess.PIPE, stderr=err, text=True,
                                        errors='replace', start_new_session=True)
            reader = threading.Thread(target=lambda p=proc: [log(x.rstrip('\n')) for x in p.stdout], daemon=True)
            reader.start()
            why = _watch(proc, state, budget, step_seconds,
                         time.time() + CLOSING if d.get('stop') else t0 + check_seconds, peaks)
            reader.join(5)
            d = _read_json(state)
            if why is None and ('out' in d or 'error' in d):
                break
            run, rc = d.pop('running', None), proc.returncode
            reason = {'memory': f'passed the memory limit of {(budget or 0) / 2 ** 30:.1f} GB',
                      'step': f'did not end in {step_seconds:g} s', 'check': f'was stopped: {limit}',
                      None: 'ended with ' + (f'signal {-rc}' if rc < 0 else f'exit code {rc}')}[why]
            if why == 'check':
                d['stop'] = limit
            if run is None:                    # before the first step or after the last
                d['error'] = f'outside its steps, the checking process {reason}'
            elif why == 'memory' and not run.get('again'):
                d['steps'][run['step']] = {'again': reason}
                log(f'  {run["step"]}: {reason}; once more, one task at a time')
            else:
                reason = (reason if why else f'the checking process {reason}') + \
                    (', also with one task at a time' if why == 'memory' else '')
                d['steps'][run['step']] = {'failed': reason, 'seconds': round(time.time() - run['since'], 1)}
                log(f'  {run["step"]}: failed ({reason})')
            _write_json(state, d)
        d = _read_json(state)
        if 'out' in d:
            res = d['out']
        else:
            res = unchecked(bundle, sets, d.get('error') or 'it did not end', code is not None, Steps(state, log))
        for s in res.get('steps') or []:
            if peaks.get(s['step']):
                s['peak_gb'] = round(peaks[s['step']] / 2 ** 30, 2)
        return res
    finally:
        if proc is not None and proc.poll() is None:       # interrupted: nothing of the check is left running
            _stop_session(proc.pid)
            proc.wait()
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def _ends_with(watcher: Optional[int]):
    """The checking process, which leads a session of its own, ends when the
    process that watches it is gone (a review killed from outside, which
    stops nothing itself): a thread looks every second, then kills every
    other process of the check, and this one."""
    if not watcher or os.getsid(0) != os.getpid():
        return

    def gone():
        me = os.getpid()
        for _ in range(100):
            others = [p for p, _ in _session(me) if p != me]
            if not others:
                break
            for p in others:
                try:
                    os.kill(p, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
            time.sleep(0.05)
        try:
            os.killpg(me, signal.SIGKILL)      # its own group, where no /proc lists the session; and itself
        finally:
            os._exit(1)

    def look():
        while os.getppid() == watcher:
            time.sleep(1)
        gone()

    if os.getppid() != watcher:                # gone before this process was up
        gone()
    threading.Thread(target=look, daemon=True).start()


def worker(state: str) -> int:
    """The process `supervised` starts: the check that the state file
    describes, from the first step the file does not hold."""
    a = _read_json(state)['args']
    _ends_with(a.get('watcher'))
    try:
        new, rc = {'out': check(a['bundle'], a['code'], a['sets'], lambda *x: print(*x, flush=True),
                                a['scope_budget'], a['conflict_budget'], a['compare_budget'], a['jobs'], state)}, 0
    except Exception as e:
        traceback.print_exc()
        new, rc = {'error': why_failed(e)}, 3
    d = _read_json(state)
    d.update(new)
    _write_json(state, d)
    return rc


def given(S, sets: list[str]) -> dict:
    """What the readings take from the request as it stands.  'contract':
    the conditions on the caller, outside which no call is reviewed (the
    assumptions, and the don't-cares that cite a requirement of kind
    assumption).  'free': the outputs a reading leaves free on purpose (the
    other don't-cares); where a call shows two answers, an open question
    asks about it.  Each with the definitions it names."""
    kinds = {r.id: r.kind for r in S.b.requirements.values()}
    out = {'contract': [], 'free': []}
    for s in sets:
        defs = S.b.fsets[s].get('defs') or {}
        for it in S.mon(s).items.values():
            if it.role not in ('assumption', 'dontcare'):
                continue
            raw = {k: str(v) for k, v in it.args.raw.items()}
            names = [n for n in dict.fromkeys(re.findall(r'[A-Za-z_]\w*', ' '.join(raw.values()))) if n in defs]
            if it.role == 'dontcare':
                says = f'`{it.note}` is free when `{raw["cond"]}`'
            elif it.pattern == 'invariant':
                says = f'every call meets `{raw["cond"]}`'
            else:
                says = f'`{it.formula}`'
            rec = {'reading': s, 'id': it.id, 'req': it.req, 'says': says,
                   'where': {n: str(defs[n]) for n in names}}
            out['contract' if it.role == 'assumption' or kinds.get(it.req) == 'assumption' else 'free'].append(rec)
    return out


def open_question(found: dict) -> str:
    """The question of one call the request leaves open.  found: output ->
    its open choice on that call (software.choices)."""
    parts = []
    for sig, o in found.items():
        if o.get('ending'):
            p = 'lets this call end in two ways, ' + ' or '.join(f'"{x}"' for x in o['shown'])
        else:
            p = ('allows ' if len(found) == 1 else f'allows `{sig}` to be ') + ' or '.join(o['shown'])
        if o.get('declared'):
            p += f' (the reading leaves this free on purpose: {", ".join(o["declared"])})'
        parts.append(p)
    return 'the request ' + ' and '.join(parts) + \
        (': is any answer acceptable, or which is meant?' if any(o.get('declared') for o in found.values())
         else ': which is meant?')


JUDGED = ('guarantee', 'scenario')         # the kinds of requirement a review certifies or settles


def _bound(*recs) -> Optional[str]:
    """What the searches of comparison records covered, where that is less
    than every run: a bounded check (objects, effects) runs `depth` cycles
    and reports a disagreement `lookahead` cycles after it happens, so it
    looks at the first `depth - lookahead` cycles; a comparison whose
    horizon is not exact looks at runs of `k` calls.  None where every
    record is of every run."""
    for x in recs:
        if isinstance(x, dict) and x.get('engine') == 'bmc':
            d, la = x.get('depth'), x.get('lookahead')
            if isinstance(d, int) and isinstance(la, int):
                return f'the first {d - la} cycles of a bounded check of {d}'
            return f'a bounded check of {d} cycles'
    for x in recs:
        if isinstance(x, dict) and x.get('exact') is False:
            return f'runs of {x.get("k")} call{"" if x.get("k") == 1 else "s"}'
    return None


def waiting(out: dict) -> tuple[list[str], list[str]]:
    """The requirements on which the third reader differs from a reader
    (out['depends']), in two lists: those that wait for the answers the
    readers shared, and those that do not.  Before any code every one of
    them waits: read the other way the request means something else on it,
    so its meaning is not settled.  With code, a requirement does not wait
    where the other reading accepts every run that each reader it differs
    from accepts on it: the direction 'witness_a_not_b' of the comparison of
    that reader with the variant is closed without context ('closed_alone')
    and in context ('closed').  Closed without context, it holds on every
    run, whatever the run does on the other requirements, so code that was
    shown to meet the requirement under the readers meets it under the other
    answer too.  Closed in context only, it holds among the runs that meet
    every other rule of both readings, and code that meets the readers'
    rules may break two rules of the variant in one run: such a requirement
    waits.  So does one with a call in that direction, a search that did not
    end, no context to compare in (NO-CONTEXT closes nothing), or a
    comparison without context that failed.  Every requirement waits where
    nothing was shown about the code (its run on the scope did not end) or
    the comparison in context of a reader with the variant did not end
    (that reader closed nothing), and in a review written before the two
    closures were kept per reader (no 'by', or no 'closed_alone').  The
    comparison is of rules: an example that the variant states is never run
    against the code.  `verdicts` asks about a requirement that does not
    wait all the same when the review does not certify it (`released`)."""
    dep = out.get('depends') or {}
    lost = {f.get('step') for f in out.get('failed') or []}
    if out.get('code') is None or 'the code on the scope' in lost or \
            any(f'the comparison of {s} and variant, in context' in lost for s in out.get('sets') or []):
        return sorted(dep), []

    def closed(p) -> bool:
        return isinstance(p, dict) and all('witness_a_not_b' in (p.get(k) or ()) for k in ('closed_alone', 'closed'))
    held = sorted(r for r, x in dep.items() if not isinstance(x.get('by'), dict) or not x['by'] or
                  not all(closed(p) for p in x['by'].values()))
    return held, sorted(set(dep) - set(held))


def released(out: dict, certified=None) -> list[str]:
    """The requirements that the review certifies without the shared answers:
    those that do not wait (`waiting`) and are certified.  The rule protects
    a certificate; a requirement that the review does not certify (the code
    breaks it, the readers disagree on it, the review is partial) stays in
    the question about the shared answers, as before any code."""
    got = set((out.get('certified') or []) if certified is None else certified)
    return [r for r in waiting(out)[1] if r in got]


def held_back(failed: list[dict]) -> tuple[bool, list[str]]:
    """What the failed steps of a check keep from being certified or
    settled: (every requirement, the requirements that are named).  A failed
    step with rests 'all' holds back every requirement, unless it names,
    under 'reqs', the only ones that rest on it (Steps.run): a list, and
    anything else names none.  A review written before a step could name
    any has no 'reqs' and reads as it did."""
    alls = [f for f in failed if f.get('rests', 'all') == 'all']
    return (any(not isinstance(f.get('reqs'), list) for f in alls),
            sorted({r for f in alls if isinstance(f.get('reqs'), list) for r in f['reqs']}))


def verdicts(S, out: dict) -> tuple[list[str], list[dict]]:
    """A requirement is certified only if the code passes it under both
    readings, the two readings agree on it (in context) and it is in no
    conflict of either reading.  Everything else is a question.  Before any
    code (out['code'] is None) the first list holds the requirements the
    request settles: the readings agree, no conflict, nothing flagged, and
    no reading cites it where it leaves an output free on purpose.  A
    requirement that a reading states no rule for is never certified or
    settled: nothing was checked against it under that reading, and the
    readings were not compared on it, so it is a question.  A requirement
    of another kind (a definition, an assumption, a don't-care, a
    non-functional one) is never certified or settled, since the readings
    take it in or it says nothing about calls; but a rule a reader states for
    it that the code breaks is a question, and so is every ambiguity flagged
    on it: the requirements that are judged are read through it.  A
    requirement that the third reader reads another way waits for the
    answers the readers shared, under the rule of `waiting`.  A step
    of the check that failed (out['failed']) certifies nothing that rests on
    it, and raises no question: a comparison that did not run shows no
    disagreement, and no agreement either.  Where the failed step names
    requirements ('reqs': the comparison of the two readings in context,
    when the one without context ended), only those rest on it."""
    sets = out['sets']
    failed = out.get('failed') or []
    partial, resting = held_back(failed)       # a search every requirement rests on, or only those it names
    conflicted = {r: c for s in sets for c in out['prompt'][s]['conflicts']['conflicts'] for r in c['reqs']}
    certified, queue = [], []
    byid = {r.id: r for r in S.b.requirements.values()}
    # the judged requirements first, then those of the other kinds, each in the order of the request
    reqs = [r.id for k in (True, False) for r in S.b.requirements.values()
            if (r.kind in JUDGED) == k and r.doc != 'FRAME']
    frame = {r.id for r in S.b.requirements.values() if r.doc == 'FRAME'}
    # one question per conflict: conflicts are grouped by the requirements in
    # every one of their minimal sets (the same clash at other values is one question)
    groups: dict[tuple, list] = {}
    for st in sets:
        for c in out['prompt'][st]['conflicts']['conflicts']:
            mon = S.mon(st)
            per = [{mon.items[i].req for i in mu if mon.items[i].req} - frame for mu in c.get('muses') or [c['core']]]
            common = tuple(sorted(set.intersection(*per))) if per else tuple(c['reqs'])
            groups.setdefault(common, []).append(c)
    for common, cs in groups.items():
        c = min(cs, key=lambda x: (len(x['stimulus']), x['stimulus']))
        others = sorted({r for x in cs for r in x['reqs']} - set(common) - frame)
        places = len({json.dumps(x['stimulus'], sort_keys=True, default=str) for x in cs})
        more = ([f'also with {", ".join(others)}'] if others else []) + \
            ([f'at {places} places'] if places > 1 else [])      # both readings at one call: one place
        queue.append({'kind': 'conflict', 'reqs': list(common), 'calls': c['stimulus'], 'variants': len(cs),
                      'question': 'no implementation can meet these requirements on these calls: which one gives way?' +
                      (f' ({", ".join(more)})' if more else '')})
    opened: dict[str, dict] = {}               # one question per call: every output the request leaves open on it
    stated = set()                             # (output, requirements cited): a freedom the readings declare, asked once
    for st in sets:
        mon = S.mon(st)
        for sig, o in out['prompt'][st]['open']['open'].items():
            cited = sorted({mon.items[d].req for d in o.get('declared') or [] if d in mon.items and mon.items[d].req})
            q = opened.get(o['call'])
            if (q and sig in q['outputs']) or (cited and (sig, tuple(cited)) in stated):
                continue                       # the other reading leaves the same open: on this call, or by the same freedom
            if q is None:
                q = opened[o['call']] = {'kind': 'open', 'reading': st, 'calls': [o['call']], 'outputs': {}}
                queue.append(q)
            stated.add((sig, tuple(cited)))
            q['outputs'][sig] = {'reading': st, 'shown': o['shown'], 'ending': bool(o.get('ending')),
                                 'declared': o.get('declared') or [], 'reqs': cited}
    freed: set[str] = set()                    # requirements a reading cites where it leaves an output free on purpose
    for q in opened.values():
        q['signal'] = ', '.join(q['outputs'])
        q['reqs'] = sorted({r for x in q['outputs'].values() for r in x['reqs']})
        q['question'] = open_question(q['outputs'])
        freed.update(q['reqs'])
    never = {}
    for st, sc in (out.get('scenarios') or {}).items():
        mon = S.mon(st)
        for k, why in (('impossible', 'its formal example is impossible in itself (a formalization error)'),
                       ('forbidden', 'the reading\'s own rules forbid it'),
                       ('blocked', 'its formal example is impossible in itself, or the reading\'s own rules '
                                   'forbid it (the search that tells the two apart did not end)')):
            for i in sc.get(k, []):
                r = mon.items[i].req if i in mon.items else None
                never.setdefault(r, True)
                queue.append({'kind': 'scenario', 'reqs': [r] if r else [], 'reading': st, 'calls': [],
                              'question': f'the behaviour {i} describes can never happen under {st}: {why}. '
                                          'Is the example, or the rule, what is meant?'})
        for i in sc.get('undecided', []):      # the search did not end: no question, and nothing settled
            never.setdefault(mon.items[i].req if i in mon.items else None, True)
    for f in failed:                           # the scenario search of a reading failed: none of them is settled
        if f.get('rests') == 'scenarios' and f.get('reading') in sets:
            for it in S.mon(f['reading']).items.values():
                if it.role == 'scenario':
                    never.setdefault(it.req, True)
    depends = out.get('depends') or {}
    held = waiting(out)[0]                     # the requirements that wait for the shared answers
    at = len(queue)                            # the place of their question, drawn once the certificates are

    def differs(x: dict) -> bool:
        """A requirement differs where a call, or a comparison that ended with a difference, says so.
        UNKNOWN without a call says nothing, and neither does a comparison that had nothing to compare on."""
        rels = [p.get('relation') for p in (x.get('by') or {}).values()] or [x.get('relation')]
        return bool(x.get('witness')) or any(rel not in ('UNKNOWN', 'NO-CONTEXT') for rel in rels)

    def shared(held: list) -> Optional[dict]:
        """The one question about the answers the readers shared (listed once, in the report)."""
        if not held:
            return None
        unshown = [r for r in held if not differs(depends[r])]
        differ = [r for r in held if r not in unshown]
        if not unshown:
            what = 'read the other way, these requirements mean something else'
        elif differ:
            what = (f'read the other way, {", ".join(differ)} mean{"s" if len(differ) == 1 else ""} something '
                    f'else; whether {", ".join(unshown)} {"does" if len(unshown) == 1 else "do"} was not shown '
                    'either way')
        else:
            what = 'whether these requirements mean something else when read the other way was not shown either way'
        q = {'kind': 'depends' if differ else 'undecided', 'reqs': held,
             'calls': next((x['witness'] for r, x in depends.items() if r in held and x.get('witness')), []),
             'question': f'both readers gave the same answer to every ambiguity listed under "Shared answers"; {what}: '
                         'are those answers meant?'}
        if unshown and differ:
            q['undecided'] = unshown
        return q
    asked: dict[tuple, dict] = {}
    agreeing = (None, 'EQUIVALENT', 'ONLY-A', 'ONLY-B')     # ONLY-x: one reading alone constrains it
    for r, x in out['readings'].items():
        if x['context'] not in agreeing:
            if x['witness']:
                q = 'the two readings of this requirement disagree on these calls: which is meant?'
            elif x['context'] == 'UNKNOWN':      # nothing was shown either way: not called a disagreement
                q = ('the two readings of this requirement were not shown to agree, and no call that '
                     'separates them was found: do they mean the same?')
            elif x['context'] == 'NO-CONTEXT':   # (a bounded comparison) the other rules of the two leave no behavior
                q = ('the two readings of this requirement were not shown to agree: no behavior meets the other '
                     'requirements under both readings at once, so there was nothing to compare them on. '
                     'Do they mean the same?')
            else:
                q = ('the two readings of this requirement disagree (no separating call was found '
                     'within the budget): which is meant?')
            decided = x['witness'] or x['context'] not in ('UNKNOWN', 'NO-CONTEXT')
            queue.append({'kind': 'readings' if decided else 'undecided', 'reqs': [r], 'relation': x['context'],
                          'calls': x['witness'] or [], 'question': q})
    proofs = out.get('proofs') or {}
    coded = out.get('code') is not None
    formal = {s: {it.req for it in S.mon(s).items.values()} for s in sets}
    for r in reqs:
        items = {s: [v for v in out['code']['verify'][s].values() if v['req'] == r] if coded else [] for s in sets}
        fails = [(s, v) for s in sets for v in items[s] if v['status'] in ('FAIL', 'NOT-COVERED')]
        for s, v in fails[:1]:
            queue.append({'kind': 'code', 'reqs': [r], 'reading': s,
                          'calls': [f'{c["call"]} -> {c["got"]}' for c in v.get('calls_shown', [])],
                          'question': 'the code breaks this requirement here (replayed): a bug, or a reading to change?'})
        ok = not coded or all(items[s] and all(v['status'] in ('PASS', 'COVERED') for v in items[s]) for s in sets)
        beyond = [(s, proofs[s]['requirements'][r]) for s in sets
                  if proofs.get(s, {}).get('status') == 'ok' and
                  proofs[s]['requirements'].get(r, {}).get('status') == 'FAILS']
        if beyond and not fails:               # the scope missed it: calls outside it break the requirement
            s, p = beyond[0]
            shown = [f'{p["call"]}: ' + ' ; '.join(p['conversation'])] if 'call' in p else \
                [', '.join(f'{fn_call(S, c)}' for c in p['calls'])]
            queue.append({'kind': 'code', 'reqs': [r], 'reading': s,
                          'calls': shown,
                          'question': 'the code passes this requirement on the scope, but these calls outside '
                                      'it break it' + (' (replayed)' if p.get('confirmed') else '') +
                                      ': a bug, or a reading to change?'})
            ok = False
        agree = out['readings'].get(r, {}).get('context') in agreeing
        amb = byid[r].ambiguity if r in byid else []
        for a in amb:                          # flagged by the decomposer: a question, whatever the readers chose
            _flagged(asked, queue, r, a)
        if byid[r].kind not in JUDGED:         # asked about, never certified; no rule for it is no fault
            continue
        lacking = [s for s in sets if r not in formal[s]]
        if lacking:                            # a reader wrote no rule for it: under that reading nothing checks it
            queue.append(_unformalized(S, r, lacking, sets))
        if ok and agree and r not in conflicted and not amb and r not in never and r not in held \
                and r not in freed and not partial and not lacking and r not in resting:
            certified.append(r)
    # a requirement that does not wait leaves the question about the shared answers only with its certificate
    q = shared(sorted(set(depends) - set(released(out, certified))))
    if q:
        queue.insert(at, q)
    return certified, queue


def _flagged(asked: dict, queue: list, r: str, a: dict):
    """The question of one ambiguity flagged on requirement r; the same phrase
    and readings on another requirement are one question."""
    key = (a.get('phrase'), tuple(a.get('readings') or []))
    if key in asked:
        asked[key]['reqs'].append(r)
        return
    asked[key] = {'kind': 'ambiguity', 'reqs': [r], 'calls': [],
                  'question': f'"{a.get("phrase")}" can mean: ' + ' / '.join(a.get('readings') or []) +
                  '. Which is meant?'}
    queue.append(asked[key])


def _unformalized(S, r: str, lacking: list[str], sets: list[str]) -> dict:
    """The question of a requirement for which the readings in `lacking` hold
    no formal item: under them nothing was checked against it, and the
    readings were not compared on it.  It quotes the reason each reader
    recorded for leaving it out."""
    why = {s: next((' '.join(str(u.get('reason') or '').split()) for u in S.b.fsets[s].get('unformalized') or []
                    if u.get('req') == r), '') for s in lacking}
    said = '; '.join(f'{s}: "{w[:200]}"' for s, w in why.items() if w)
    if len(lacking) == len(sets):
        text = 'no reading states this requirement as a rule{}, so nothing here was checked against it'
    else:
        text = ' and '.join(lacking) + (' does' if len(lacking) == 1 else ' do') + \
            ' not state this requirement as a rule{}, so the readings were not compared on it'
    return {'kind': 'unformalized', 'reqs': [r], 'readings': lacking, 'calls': [],
            'question': text.format(f' ({said})' if said else '') + ': should it constrain the answer?'}


def unchecked(bundle: str, sets: list[str], why: str, coded: bool = False, steps: Optional[Steps] = None) -> dict:
    """The review of a request whose check gave no verdicts (it did not
    start, or it ended outside its steps): nothing is settled, the report
    says why, and the questions are the ambiguities flagged when the request
    was split into requirements, which need no check."""
    from .ir import load_bundle
    asked: dict[tuple, dict] = {}
    queue: list[dict] = []
    try:
        reqs = list(load_bundle(bundle, sets).requirements.values())
    except Exception:                          # the bundle does not load: `why` says so, and there is no question
        reqs = []
    for k in (True, False):                    # in the order of `verdicts`
        for r in reqs:
            if (r.kind in JUDGED) == k and r.doc != 'FRAME':
                for a in r.ambiguity:
                    _flagged(asked, queue, r.id, a)
    done, failed = steps.summary() if steps else ([], [])
    return {'sets': sets, 'prompt': {}, 'readings': {}, 'given': {}, 'unchecked': why, 'steps': done, 'failed': failed,
            'code': {'calls': 0, 'verify': {s: {} for s in sets}} if coded else None, 'certified': [], 'queue': queue,
            'limits': []}


def fn_call(S, c) -> str:
    from . import software as SW
    return SW.call_text(SW.function(S), tuple(c))


def proved(out: dict) -> list[str]:
    """Certified requirements proved for every call under every reading."""
    proofs = out.get('proofs') or {}
    sets = out['sets']
    return [r for r in out['certified']
            if all(proofs.get(s, {}).get('status') == 'ok' and
                   proofs[s]['requirements'].get(r, {}).get('status') == 'PROVED' for s in sets)]


def _resting(reqs: list[str]) -> str:
    """The line of a report under a failed step that names the requirements
    that rest on it (the comparison of the two readings in context, when
    the one without context ended: see check)."""
    carry = ('the comparison without context found no run that one reading accepts and the other rejects, '
             'and in context there is none either.')
    if not reqs:
        return 'No requirement rests on it: on every requirement that both readings state, ' + carry
    one = len(reqs) == 1
    return (f'Only {", ".join(reqs)} rest{"s" if one else ""} on it: whether the two readings agree on '
            f'{"it" if one else "them"} in context was not shown. On every other requirement that both readings '
            'state, ' + carry)


def report(S, out: dict) -> str:
    lines = ['# FCP review', '']
    reqs = {r.id: r for r in S.b.requirements.values()} if S else {}
    coded = out.get('code') is not None
    if coded:
        lines.append(f'Certified: {len(out["certified"])} requirements. Questions: {len(out["queue"])}.')
    else:
        lines += ['Before any code: the request alone.', '',
                  f'Settled: {len(out["certified"])} requirements. Questions: {len(out["queue"])}.']
    lines.append('')
    if out.get('unchecked') or out.get('failed'):
        lines.append('## This review is partial')
        if out.get('unchecked'):
            lines.append(f'The check gave no verdicts: {out["unchecked"]}. Nothing is '
                         f'{"certified" if coded else "settled"}; the questions below are the ambiguities '
                         'flagged when the request was split into requirements, which need no check.')
        if out.get('failed'):
            lines.append(f'{len(out["failed"])} of the {len(out.get("steps") or out["failed"])} steps of the check '
                         'did not end. What the other steps found stands; no requirement is '
                         f'{"certified" if coded else "settled"} that rests on one of these:')
            for x in out['failed']:
                lines.append(f'- {x["step"]}: {x["why"]}')
                if isinstance(x.get('reqs'), list) and not out.get('unchecked'):
                    lines.append('  - ' + _resting(x['reqs']))
        if out.get('trace'):
            lines += ['', f'What the checking process printed about it is in {out["trace"]}.']
        lines.append('')
    if out['certified'] and not coded:
        lines.append('## Settled (the two readings agree on them; no conflict; nothing flagged)')
        lines += [f'- {r}: {reqs[r].text}' for r in out['certified']]
        lines.append('')
    elif out['certified']:
        pr = set(proved(out))
        lines.append('## Certified (the code meets them under both readings, which agree; no conflict)')
        if pr:
            lines.append(f'{len(pr)} of them are proved for every call the interface can carry, '
                         'not only on the scope (marked "proved").')
        lines += [f'- {r}: {reqs[r].text}' + (' (proved)' if r in pr else '') for r in out['certified']]
        lines.append('')
    lines.append('## Questions')
    for i, q in enumerate(out['queue'], 1):
        about = ', '.join(([q['signal']] if q.get('signal') else []) + (q.get('reqs') or []))
        lines.append(f'{i}. **{q["kind"]}** ({about}): {q["question"]}')
        for c in q.get('calls') or []:
            lines.append(f'   - `{c}`')
    if out.get('variant_answers'):
        free = released(out)                   # with code: certified, and the other reading only accepts more
        held = sorted(set(out.get('depends') or {}) - set(free))
        if not free:
            lead = 'the requirements on which its reading differs depend on these answers:'
        elif held:
            lead = (f'of the requirements on which its reading differs, {", ".join(held)} '
                    f'depend{"s" if len(held) == 1 else ""} on these answers:')
        else:
            lead = 'no requirement on which its reading differs waits for these answers:'
        lines += ['', '## Shared answers',
                  'Both readers took the same reading of these flagged phrases. A third reader took the other '
                  f'reading of all of them; {lead}']
        lines += [f'- {a["req"]}, "{a["phrase"]}": both took "{_reading(S, a["req"], a["phrase"], a["taken"])}"'
                  for a in out['variant_answers']]
        if free:
            one = len(free) == 1
            bounds = sorted({p['bound'] for r in free for p in out['depends'][r]['by'].values() if p.get('bound')})
            # of a run that both readers accept: a reader with no entry reads the requirement as the
            # other reading does in context, and the entries that are there are closed on every run
            lines += ['', f'On {", ".join(free)} the other reading accepts every run that both readers accept, '
                      'whatever the run does on the other requirements'
                      + (f' (searched within {" and ".join(bounds)})' if bounds else '') + ': what is certified of '
                      f'{"this requirement" if one else "these requirements"} stands under either answer, and '
                      f'{"it does" if one else "they do"} not wait for these answers.']
    gv = out.get('given') or {}
    if gv.get('contract') or gv.get('free'):
        def one(x):
            where = ''.join(f'; `{n}` is `{d}`' for n, d in x['where'].items())
            return f'- {x["reading"]}, {x["id"]}' + (f' ({x["req"]})' if x.get('req') else '') + f': {x["says"]}{where}'
        lines += ['', '## Taken as given']
        if gv.get('contract'):
            lines.append('The readings take these conditions on the caller from the request. '
                         'A reading says nothing about a call outside its conditions, '
                         'and no open choice is reported there:')
            lines += [one(x) for x in gv['contract']]
        if gv.get('free'):
            lines.append('The readings leave these outputs free on purpose. '
                         'Where a call shows two answers, a question above asks about it:')
            lines += [one(x) for x in gv['free']]
    outside = [r for r in reqs.values() if r.kind == 'non_functional' and r.doc != 'FRAME']
    if outside:
        lines += ['', '## Outside this review',
                  'A review judges what calls return and do. The request also asks for these, which were marked '
                  'non-functional when it was split into requirements. They are not '
                  f'{"certified" if coded else "settled"}, and nothing is said about them except where the '
                  'report above names one:']
        lines += [f'- {r.id}: {r.text}' for r in outside]
    if out.get('dropped'):
        lines += ['', '## Calls not shown',
                  'A call is shown under a question only after it was run again, from the line as printed, on the '
                  'compiled monitors of the two readings. These searches found a call that did not pass. It is not '
                  'shown, and the direction it was found for stays undecided: no certificate rests on that direction '
                  '(the calls are in review.json, under "dropped"):']
        lines += [f'- {x["req"]} ({x["step"]}): {x["why"]}' for x in out['dropped']]
    if out.get('limits'):
        lines += ['', '## Limits of this review',
                  'These searches were cut short, by their time budget or by a rule they cannot use. '
                  'What they found stands; what lies beyond was not searched:']
        lines += [f'- {x}' for x in out['limits']]
    return '\n'.join(lines) + '\n'


def rereport(out: str) -> dict:
    """The verdicts and the report again, from a finished review's review.json
    (after a change to how verdicts are drawn); nothing is re-run.  A review
    whose check gave no verdicts is left as it is: there is nothing to draw
    them from."""
    from .analyses import Session
    with open(os.path.join(out, 'review.json')) as f:
        res = json.load(f)
    if res.get('unchecked'):
        return res
    S = Session(os.path.join(out, 'bundle'), sets=res['sets'])
    res.setdefault('given', given(S, res['sets']))
    res['certified'], res['queue'] = verdicts(S, res)
    with open(os.path.join(out, 'review.json'), 'w') as f:
        json.dump(res, f, indent=1, default=str)
    with open(os.path.join(out, 'review.md'), 'w') as f:
        f.write(report(S, res))
    return res


def _reading(S, rid: str, phrase: str, k: int) -> str:
    r = next((x for x in S.b.requirements.values() if x.id == rid), None)
    a = next((x for x in (r.ambiguity if r else []) if x.get('phrase') == phrase), {})
    rs = a.get('readings') or []
    return rs[k - 1] if 0 < k <= len(rs) else f'reading {k}'


def review(request: str, code: Optional[str], out: str, model: str = 'opus', log=print, resume: bool = False,
           scope_budget: float = 120, conflict_budget: float = 300, entry: Optional[str] = None,
           signature: Optional[str] = None, variants: bool = True, compare_budget: float = 300,
           jobs: int = JOBS, memory: Optional[float] = None, step_seconds: float = STEP_SECONDS,
           check_seconds: float = CHECK_SECONDS) -> dict:
    """The whole protocol on one answer.  resume: reuse the bundle and the
    readings a previous review left in out (no agent runs again).  With
    code None and signature (a file with the def line of the function asked
    for), the request alone: the review stops before the code.  variants:
    one more reader for the answers the two readers shared (step 3b).  The
    check is watched (`supervised`: memory in GB, step_seconds,
    check_seconds), so the review is written also when a step of it fails,
    and then says which."""
    os.makedirs(out, exist_ok=True)
    if code is None and not signature:
        raise ValueError('without code, name a file with the signature asked for (--signature)')
    log('fcp review: the request, the readings, the code' if code else 'fcp review: the request alone')
    bundle = os.path.join(out, 'bundle')
    sets = ['agent_a', 'agent_b']
    if resume and all(os.path.exists(os.path.join(bundle, 'formal', f'{x}.yaml')) for x in sets):
        log('  resuming: the bundle and both readings are already there')
    else:
        bundle = build_bundle(request, code or signature, out, model, log, entry)
        sets = formalize(bundle, out, model, log)
    if variants and not (resume and os.path.exists(os.path.join(bundle, 'formal', 'variant.yaml'))):
        variant(bundle, out, sets, model, log)
    return checked(bundle, code, sets, out, log, scope_budget=scope_budget, conflict_budget=conflict_budget,
                   compare_budget=compare_budget, jobs=jobs, memory=memory, step_seconds=step_seconds,
                   check_seconds=check_seconds)


def checked(bundle: str, code: Optional[str], sets: list[str], out: str, log=print, **limits) -> dict:
    """The watched check of a bundle with readings (`supervised`, which
    takes the limits), and its review written into directory out:
    review.json, review.md and, when a step failed or the check gave no
    verdicts, check_errors.txt with what the checking process printed."""
    os.makedirs(out, exist_ok=True)
    state = os.path.join(out, 'check_state.json')
    res = supervised(bundle, code, sets, log, state=state, **limits)
    os.remove(state)                           # review.json holds the steps
    trace = os.path.join(out, 'check_errors.txt')
    if os.path.exists(trace):                  # of an earlier check
        os.remove(trace)
    if os.path.getsize(state + '.err') and (res.get('failed') or res.get('unchecked')):
        os.replace(state + '.err', trace)      # the trace of what failed
        res['trace'] = os.path.basename(trace)
    else:
        os.remove(state + '.err')
    from .analyses import Session
    try:
        S = Session(bundle, sets=sets)
    except Exception:
        if not res.get('unchecked'):
            raise
        S = None                               # the bundle does not load, which the report then says
    with open(os.path.join(out, 'review.json'), 'w') as f:
        json.dump(res, f, indent=1, default=str)
    text = report(S, res)
    with open(os.path.join(out, 'review.md'), 'w') as f:
        f.write(text)
    return res
