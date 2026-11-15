"""The model alone on the ten code tasks: does it tell its reader about the planted conflict?

    python experiments/alone_demo.py run [--reps N] [--jobs K]    the replies (no tools, no files)
    python experiments/alone_demo.py judge [--jobs K]             each reply against the planted conflict
    python experiments/alone_demo.py summary

Each task's prompt (corpus/code_*/spec.md; the change request has the old
code and its tests pasted below it) is given to the model with no tools,
--reps times (3) under each of three instructions:

  b0  the prompt as it is, which is what the code writers of the studies got;
  b1  HumanEvalComm's instruction, "either generate Python3 code ... or ask clarifying questions";
  b2  HumanEvalComm's instruction to ask clarifying questions or to answer NO_QUESTIONS.

The summaries the 30 code writers of the studies gave with their code (three
models on ten tasks; each was asked for "every decision you made where the
request was unclear") are judged with them, as `coder_<model>`.

The judge is the same model without tools.  It is given the request, the
reply and the planted conflict of spec_defects.yaml, and grades whether the
reply tells its reader about the conflict: 2 it says that the rules cannot
all be met or asks which of them wins, 1 it touches the rules without
saying so (it picks one, or asks about one), 0 it does not mention them.
Replies and grades are kept in experiments/alone/<task>.json, the counts in
experiments/results/alone.json.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import comm_demo as C  # noqa: E402

TASKS = ('checkout', 'mask', 'limit', 'change', 'pay', 'save', 'invoice', 'card', 'order', 'loyal')
MODELS = ('haiku', 'sonnet', 'opus')
ALONE = ('b0', 'b1', 'b2')
KEEP = os.path.join(HERE, 'alone')
RESULT = os.path.join(HERE, 'results', 'alone.json')
JUDGE = ('A request for a piece of software contains rules that cannot all be met. The conflict is '
         'described below, with an input on which the rules clash. The request was given to an expert, '
         'whose answer is given below. Your task is to say whether the answer tells its reader about '
         'this conflict, on a scale from 0 to 2, where 0 indicates that the answer does not mention the '
         'conflict, 1 indicates that the answer touches the rules involved (for instance it follows one '
         'of them, or asks about one of them) without saying that they cannot all be met, and 2 '
         'indicates that the answer says that these rules cannot all be met, or asks which of them '
         'wins. Please respond with a single integer 0, 1, or 2. No explanation needed, just a single '
         'integer. \n\n ### Answer: {answer} \n ### Request: {request} \n ### Conflict: {conflict}')


def corpus(task: str, *rel) -> str:
    return os.path.join(ROOT, 'corpus', f'code_{task}', *rel)


def read(path: str) -> str:
    with open(path) as f:
        return f.read()


def request(task: str) -> str:
    text = read(corpus(task, 'spec.md'))
    if task == 'change':                               # the request is about code: paste it, as the files it names
        for name, src in (('checkout.py', 'old.py'), ('test_checkout.py', 'test_old.py')):
            text += f'\n`{name}`:\n\n```python\n{read(corpus(task, "impl", src))}```\n'
    return text


def conflict(task: str) -> str:
    import yaml
    d = yaml.safe_load(read(corpus(task, 'spec_defects.yaml')))
    planted = [x for x in d['defects'] if x['kind'] == 'conflict']
    assert len(planted) == 1, task
    return ' '.join(planted[0]['note'].split())


def kept(task: str) -> dict:
    path = os.path.join(KEEP, f'{task}.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {'task': task, 'conflict': conflict(task), 'replies': {}}


def keep(d: dict):
    os.makedirs(KEEP, exist_ok=True)
    path = os.path.join(KEEP, f'{d["task"]}.json')
    with open(path + '.tmp', 'w') as f:
        json.dump(d, f, indent=1)
    os.replace(path + '.tmp', path)


def run_one(task: str, reps: int):
    d, text = kept(task), request(task)
    todo = {'b0': text, 'b1': C.B1 + text, 'b2': C.B2.format(problem=text)}
    for k, prompt in todo.items():
        got = [r for r in d['replies'].get(k, []) if not r.get('error')]
        tries = 0
        while len(got) < reps and tries < reps + 3:      # a call that stalls is cut at five minutes and asked again
            tries += 1
            r = C.ask(prompt, timeout=300)
            if not r.get('error'):
                got.append(r)
        d['replies'][k] = got
        keep(d)
    for m in MODELS:                                    # what the code writers of the study said with their code
        path = corpus(task, 'agents', f'coder_{m}', 'summary.md')
        if os.path.exists(path) and f'coder_{m}' not in d['replies']:
            d['replies'][f'coder_{m}'] = [{'reply': read(path).replace(ROOT, '<fcp>')}]
    keep(d)
    print(time.strftime('%H:%M:%S'), 'run', task, {k: len(v) for k, v in d['replies'].items()}, flush=True)


def judge_one(task: str):
    d, text = kept(task), request(task)
    for k, rs in d['replies'].items():
        for r in rs:
            if r.get('grade') is not None or not r.get('reply'):
                continue
            a = C.ask(JUDGE.format(answer=r['reply'], request=text, conflict=d['conflict']))
            r['grade'], r['judge'] = C.grade(a['reply'], '012'), {'reply': a['reply'], 'cost_usd': a.get('cost_usd')}
    keep(d)
    print(time.strftime('%H:%M:%S'), 'judge', task, {k: [r.get('grade') for r in rs] for k, rs in d['replies'].items()},
          flush=True)


def summary():
    rows, cost = {}, 0.0
    for t in TASKS:
        d = kept(t)
        rows[t] = {k: [r.get('grade') for r in rs] for k, rs in d['replies'].items()}
        rows[t]['asks'] = {'b1': [C.asks_b1(r['reply']) for r in d['replies'].get('b1', [])],
                           'b2': [C.asks_b2(r['reply']) for r in d['replies'].get('b2', [])]}
        cost += sum((r.get('cost_usd') or 0) + ((r.get('judge') or {}).get('cost_usd') or 0)
                    for rs in d['replies'].values() for r in rs)
    conds = ALONE + tuple(f'coder_{m}' for m in MODELS)
    tot = {k: {'replies': sum(len(rows[t].get(k, [])) for t in TASKS),
               'names': sum(g == 2 for t in TASKS for g in rows[t].get(k, [])),
               'touches': sum(g == 1 for t in TASKS for g in rows[t].get(k, [])),
               'silent': sum(g == 0 for t in TASKS for g in rows[t].get(k, [])),
               'tasks_named_every_time': sum(bool(rows[t].get(k)) and all(g == 2 for g in rows[t][k]) for t in TASKS),
               'tasks_never_named': sum(bool(rows[t].get(k)) and not any(g == 2 for g in rows[t][k]) for t in TASKS)}
           for k in conds}
    out = {'model': C.MODEL, 'tasks': rows, 'totals': tot, 'cost_usd': round(cost, 2)}
    with open(RESULT, 'w') as f:
        json.dump(out, f, indent=1)
    for t in TASKS:
        print(f'{t:9}', ' '.join(f'{k}={"".join("-" if g is None else str(g) for g in rows[t].get(k, []))}' for k in conds))
    for k, v in tot.items():
        print(f'{k:13}', v)
    print('cost', out['cost_usd'])


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else 'summary'
    opt = {k: int(args[args.index(k) + 1]) for k in ('--reps', '--jobs') if k in args}
    if cmd == 'run':
        with ThreadPoolExecutor(max_workers=opt.get('--jobs', 3)) as ex:
            list(ex.map(lambda t: run_one(t, opt.get('--reps', 3)), TASKS))
    elif cmd == 'judge':
        with ThreadPoolExecutor(max_workers=opt.get('--jobs', 3)) as ex:
            list(ex.map(judge_one, TASKS))
    elif cmd == 'summary':
        summary()
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
