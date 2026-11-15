#!/usr/bin/env python3
"""The requests of the HumanEvalComm pilot that got no review, checked again.

In the pilot a step of the check that failed ended the check, and 8 of the
80 requests got no review (docs/FCP_code.md, section 13.5).  The engine has
changed since: a failed step is recorded, the check goes on, and the review
is written without what rested on the step (fcp.review.checked).  This
script checks those requests once more, from the bundles stored in
experiments/comm and inside the limits of the pilot (per check 8 GB and 45
minutes, per step 15 minutes, four engine tasks, the same search budgets),
and records what each gets now: a review of every step, a partial review,
or none.  No agent runs.  The results of the pilot stay as they are; what
is measured here is written beside them:

  experiments/comm/<problem>/<variant>/again/   review.json, review.md, status.json
  experiments/results/comm_again.json           one entry per request, and the counts

  comm_again.py [--jobs N] [--force] [KEY...]   the requests without a review (or those named), N at a
                                                time (default 1); a request that has a result is skipped
  comm_again.py one KEY DIR                     the check of the bundle in DIR, in this process
  comm_again.py summary                         the counts of the stored results
"""
from __future__ import annotations

import collections
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)


def _pilot():
    spec = importlib.util.spec_from_file_location('comm_demo', os.path.join(HERE, 'comm_demo.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _pilot()                                # the pilot's list of requests, its limits, and how it counts a question
WORK = os.environ.get('FCP_COMM_AGAIN') or os.path.expanduser('~/.cache/fcp/comm-again')
RESULT = os.path.join(HERE, 'results', 'comm_again.json')
SETS = ['agent_a', 'agent_b']
BUDGETS = {'scope_budget': 120, 'conflict_budget': 300, 'compare_budget': 300}     # those of the pilot's `check`
SYSTEMD = ['systemd-run', '--user', '--scope', '-q']
KEPT = ('review.json', 'review.md', 'check_errors.txt')


def stored(p: dict) -> str:
    return os.path.join(C.REPO, str(C.number(p['task'])), p['variant'])


def read(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def write(path: str, doc: dict):
    with open(path + '.tmp', 'w') as f:
        json.dump(doc, f, indent=1)
        f.write('\n')
    os.replace(path + '.tmp', path)


def todo() -> list[dict]:
    """The requests whose stored status says that the check of the pilot did not end."""
    ps = []
    for p in C.prompts():
        st = read(os.path.join(stored(p), 'status.json'))
        if st.get('agents') == 'ok' and st.get('check') != 'ok':
            ps.append(dict(p, pilot=st.get('check')))
    return ps


def engine() -> str:
    """The commit the engine is at, and whether fcp/ differs from it."""
    git = lambda *a: subprocess.run(('git', '-C', ROOT) + a, capture_output=True, text=True).stdout.strip()
    return git('rev-parse', '--short', 'HEAD') + (' with uncommitted changes in fcp/'
                                                  if git('status', '--porcelain', '--', 'fcp') else '')


# ---------------------------------------------------------------- one request

def one(key: str, d: str):
    """The check of the request in d/bundle, as the pilot's `check` runs it
    now.  The review is written to d, and how the check ended to
    d/status.json."""
    from fcp import review as R

    def log(msg):
        with open(os.path.join(d, 'log.txt'), 'a') as f:
            f.write(f'{time.strftime("%H:%M:%S")} {msg}\n')
    t = time.time()
    try:
        res = R.checked(os.path.join(d, 'bundle'), None, SETS, d, log, jobs=C.CHECK_JOBS,
                        step_seconds=C.CHECK_STEP_MINUTES * 60, check_seconds=max(60, C.CHECK_MINUTES * 60 - 360),
                        **BUDGETS)
        r = C.check_status(res)
    except Exception as e:
        r = f'{type(e).__name__}: {e}'[:600]
    write(os.path.join(d, 'status.json'), {'check': r, 'check_seconds': round(time.time() - t)})
    print(time.strftime('%H:%M:%S'), 'check', key, r[:300], round(time.time() - t), 's', flush=True)


def run(p: dict, scoped: bool) -> tuple[dict, str]:
    """The check of one request in a process of its own, in a new directory
    with a copy of the stored bundle, inside the memory cap and the time
    limit of the pilot: (how it ended, the directory)."""
    d = os.path.join(WORK, f'{p["key"]}-{time.strftime("%Y%m%d-%H%M%S")}')
    os.makedirs(d)                                          # new: nothing of an earlier check is read
    shutil.copytree(os.path.join(stored(p), 'bundle'), os.path.join(d, 'bundle'))
    shutil.copy(os.path.join(stored(p), 'request.md'), os.path.join(d, 'bundle', 'spec.md'))
    unit = f'fcp-again-{p["key"]}-{os.getpid()}'
    cmd = [sys.executable, '-I', '-u', os.path.abspath(__file__), 'one', p['key'], d]
    if scoped:
        cmd = SYSTEMD + ['--unit', unit, '-p', f'MemoryMax={int(C.CHECK_GB * 1024)}M', '-p', 'MemorySwapMax=0',
                         '-p', f'RuntimeMaxSec={int(C.CHECK_MINUTES * 60) + 60}', '--'] + cmd
    t, rc = time.time(), 0
    with open(os.path.join(d, 'check.out'), 'w') as f:
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = proc.wait(timeout=C.CHECK_MINUTES * 60)
            why = f'stopped: exit code {rc}'
        except subprocess.TimeoutExpired:
            why = f'stopped after {C.CHECK_MINUTES:g} minutes'
            try:
                os.killpg(proc.pid, signal.SIGKILL)         # the check and every tool it started
            except ProcessLookupError:
                pass
            proc.wait()
    if scoped:
        ctl = lambda *a: subprocess.run(('systemctl', '--user') + a + (unit + '.scope',),
                                        capture_output=True, text=True).stdout.strip()
        for _ in range(25 if rc < 0 else 1):                # killed: systemd learns why a moment later
            if ctl('show', '-p', 'Result', '--value') == 'oom-kill':
                why = f'stopped: more than {C.CHECK_GB:g} GB of memory'
                break
            time.sleep(0.2)
        ctl('kill', '--signal=KILL')                        # whatever is left of it
        ctl('stop')
        ctl('reset-failed')
    path = os.path.join(d, 'status.json')
    st = read(path) if os.path.exists(path) else {'check': why, 'check_seconds': round(time.time() - t)}
    return st, d


def keep(p: dict, st: dict, d: str):
    """What the check wrote, copied beside the stored request."""
    dst = os.path.join(stored(p), 'again')
    os.makedirs(dst, exist_ok=True)
    for name in KEPT:
        to = os.path.join(dst, name)
        if os.path.exists(os.path.join(d, name)):
            with open(os.path.join(d, name)) as f:          # the work directory's path says nothing: shorten it
                text = f.read().replace(d, '<work>').replace(ROOT, '<fcp>')
            with open(to, 'w') as f:
                f.write(text)
        elif os.path.exists(to):                            # of an earlier run of this script
            os.remove(to)
    st = {k: (v.replace(d, '<work>').replace(ROOT, '<fcp>') if isinstance(v, str) else v) for k, v in st.items()}
    write(os.path.join(dst, 'status.json'), st)


# ---------------------------------------------------------------- the eight, and the counts

def result(check: str) -> str:
    """full: a review of every step; partial: a review that names the steps
    that did not end; unchecked: a report without verdicts; stopped: the
    checking process ended and wrote nothing."""
    return 'full' if check == 'ok' else check.split(':')[0] if check.startswith(('partial:', 'unchecked:')) \
        else 'stopped'


def entry(p: dict) -> dict:
    dst = os.path.join(stored(p), 'again')
    st = read(os.path.join(dst, 'status.json'))
    e = {'task': p['task'], 'variant': p['variant'], 'key': p['key'], 'pilot': p['pilot'],
         'result': result(st['check']), 'check': st['check'], 'seconds': st.get('check_seconds'),
         'engine': st.get('engine')}
    if os.path.exists(os.path.join(dst, 'review.json')):
        res = read(os.path.join(dst, 'review.json'))
        kinds = collections.Counter(C.kind_of(q) for q in res.get('queue') or [])
        e.update(steps=len(res.get('steps') or []),
                 peak_gb=max((s.get('peak_gb') or 0 for s in res.get('steps') or []), default=0),
                 failed=[{'step': x.get('step'), 'why': x.get('why'), 'rests': x.get('rests')}
                         for x in res.get('failed') or []],
                 settled=len(res.get('certified') or []), questions=dict(sorted(kinds.items())),
                 levels=C.levels(kinds), limits=len(res.get('limits') or []),
                 not_shown=len(res.get('dropped') or []))
    return e


def summary() -> dict:
    es = [entry(p) for p in todo() if os.path.exists(os.path.join(stored(p), 'again', 'status.json'))]
    counts = {'requests': len(es)}
    for word in ('full', 'partial', 'unchecked', 'stopped'):
        counts[word] = sum(e['result'] == word for e in es)
    doc = {'what': 'the requests of the HumanEvalComm pilot that got no review, checked again from their stored '
                   'bundles (experiments/comm_again.py); the counts of the pilot are in comm.json and do not '
                   'include these',
           'limits': {'gb': C.CHECK_GB, 'minutes': C.CHECK_MINUTES, 'step_minutes': C.CHECK_STEP_MINUTES,
                      'jobs': C.CHECK_JOBS, **BUDGETS},
           'counts': counts, 'requests': es}
    write(RESULT, doc)
    return doc


def drive(keys: list, jobs: int, force: bool):
    scoped = bool(shutil.which('systemd-run')) and not subprocess.run(SYSTEMD + ['--', 'true'],
                                                                      capture_output=True).returncode
    if not scoped:
        print('no systemd scope starts here: the checks run without a memory cap', flush=True)
    rev = engine()

    def go(p: dict):
        if os.path.exists(os.path.join(stored(p), 'again', 'status.json')) and not force:
            return
        try:
            st, d = run(p, scoped)
            keep(p, dict(st, engine=rev), d)
            print(time.strftime('%H:%M:%S'), p['task'], p['variant'], p['key'], st['check'][:300],
                  st.get('check_seconds'), 's', flush=True)
        except Exception as e:                              # this request has no result; the others go on
            print(time.strftime('%H:%M:%S'), p['task'], p['variant'], p['key'], 'NOT RUN',
                  f'{type(e).__name__}: {e}'[:300], flush=True)
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        list(ex.map(go, [p for p in todo() if not keys or p['key'] in keys]))
    print('TOTAL', json.dumps(summary()['counts']), flush=True)


def main():
    args = sys.argv[1:]
    os.environ['PATH'] = os.path.join(ROOT, '.tools', 'oss-cad-suite', 'bin') + os.pathsep + os.environ['PATH']
    if args[:1] == ['one']:
        return one(args[1], args[2])
    if args[:1] == ['summary']:
        print(json.dumps(summary()['counts'], indent=1))
        return
    jobs, force, keys = 1, False, []
    while args:
        a = args.pop(0)
        if a == '--jobs':
            jobs = int(args.pop(0))
        elif a == '--force':
            force = True
        else:
            keys.append(a)
    drive(keys, jobs, force)


if __name__ == '__main__':
    main()
