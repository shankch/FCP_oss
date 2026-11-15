#!/usr/bin/env python3
"""Replay of the calls that the reviews of the HumanEvalComm pilot show.

A review that asks which of two readings is meant shows a call on which the
readings differ, and one that asks whether the shared answers are meant shows
a call on which a reading and the variant reading differ.  A shown call is
the engine's claim about the two readings, and the reader of a review takes
it as a fact.  This script checks the claim after the fact and by other
means: it takes every such call of every stored review back from its printed
line, runs the monitors of the two readings on it (fcp.rv: no solver, no
search), and records whether one reading accepts the call and the other
rejects it, read as the comparison reads a witness.  It changes no review.

A printed line names the ending of a call in words, and the replay reads the
words as the code they name.  So a call that a search found on an outcome
code that names no ending is not confirmed here: the fault that the replay
found in the review of HumanEval/46 (1a), see tests/test_limits.py.

The reading back of a line and the judgment of a call are the engine's own
(fcp.software.read_line and separates).  Since the pilot a review runs them
itself before it shows a call (the step `the replay of the calls of ...` of
fcp.review.check, tests/test_replay.py).  The reviews stored here were
written before that step, and this script is what measured them.

  comm_replay.py [--gb N] [--seconds N] [--cases N] [--force] [KEY...]
        every request with a review (or those named), each in a process of
        its own inside N GB (default 3) and N seconds (default 300); a
        request whose review is unchanged since its last replay is skipped.
        A reading with free values is run for every combination of them,
        up to N combinations (default 4096); beyond that the relation is
        recorded as an error
  comm_replay.py one KEY [N]  the replay of one request, in this process
  comm_replay.py totals       the totals of the stored results

Results: experiments/comm/replay.json, one entry per request.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)


def _pilot():
    spec = importlib.util.spec_from_file_location('comm_demo', os.path.join(HERE, 'comm_demo.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _pilot()                                # the pilot's own list of requests, work directories and status
STORE = os.path.join(C.REPO, 'replay.json')
CASES = 4096                                # combinations of a reading's free values that one replay runs at most


# ---------------------------------------------------------------- one request

def shown(rv: dict) -> list:
    """The relations of a review that come with a call: (kind, requirement,
    printed lines, the pairs of readings the relation is between)."""
    todo = [('readings', r, x['witness'], [tuple(rv['sets'])])
            for r, x in rv['readings'].items() if x.get('witness')]
    todo += [('depends', r, x['witness'], [(p, 'variant') for p in x.get('peers', [])])
             for r, x in rv['depends'].items() if x.get('witness')]
    return todo


def replay(key: str) -> list:
    """One record per relation of the request's review that comes with a call.
    Its result is `confirmed` with the pair of readings and the direction;
    `not confirmed` (the line shows the returned value) or `not confirmed,
    ending in words` (the line names an ending, and the values that go with
    it are not shown); `prints back differently` where the line does not
    parse to the call it prints; or `error` with the exception."""
    from fcp import software as SW
    from fcp.analyses import Session
    out = os.path.join(C.WORK, key, 'out')
    with open(os.path.join(out, 'review.json')) as f:
        rv = json.load(f)
    sets = list(rv['sets']) + (['variant'] if os.path.exists(os.path.join(out, 'bundle', 'formal', 'variant.yaml'))
                               else [])
    S = Session(os.path.join(out, 'bundle'), sets=sets, jobs=1)
    fn = SW.function(S)
    rels = []
    for kind, req, lines, pairs in shown(rv):
        try:
            if not SW.printable(fn):
                raise ValueError('not a plain function: its printed calls are not read back here')
            got = [SW.read_line(fn, l) for l in lines]
            w = {'calls': [g[0] for g in got], 'outs': [g[1] for g in got]}
            back = [SW.line(fn, c, o) for c, o in zip(w['calls'], w['outs'])]
            if back != list(lines):
                res = {'result': 'prints back differently', 'back': back}
            else:
                both = [(a, b) for p, q in pairs for a, b in ((p, q), (q, p))]
                ok = [(a, b, 'in context') for a, b in both if SW.separates(S, fn, w, a, b, req, True, cases=CASES)]
                if not ok and kind == 'readings':       # a review shows a plain witness where context has none
                    ok = [(a, b, 'plain') for a, b in both if SW.separates(S, fn, w, a, b, req, False, cases=CASES)]
                if ok:
                    res = {'result': 'confirmed', 'accepts': ok[0][0], 'rejects': ok[0][1], 'mode': ok[0][2]}
                else:
                    res = {'result': 'not confirmed' if all(g[2] for g in got) else 'not confirmed, ending in words'}
        except Exception as e:                          # one relation that cannot be replayed is recorded as such
            res = {'result': 'error', 'error': f'{type(e).__name__}: {str(e)[:200]}'}
        rels.append({'kind': kind, 'req': req, 'calls': list(lines), **res})
    return rels


# ---------------------------------------------------------------- every request, one process each

def load() -> dict:
    if os.path.exists(STORE):
        with open(STORE) as f:
            return json.load(f)['requests']
    return {}


def totals(store: dict) -> dict:
    tot = {'requests': len(store), 'requests by status': {}, 'relations': 0, 'by result': {}}
    for d in store.values():
        word = d['status'] if d['status'] in ('ok', 'no call') else 'not replayed'
        tot['requests by status'][word] = tot['requests by status'].get(word, 0) + 1
        for r in d['relations']:
            tot['relations'] += 1
            k = f"{r['kind']}: {r['result']}"
            tot['by result'][k] = tot['by result'].get(k, 0) + 1
    tot['requests by status'] = dict(sorted(tot['requests by status'].items()))
    tot['by result'] = dict(sorted(tot['by result'].items()))
    return tot


def save(store: dict):
    doc = {'what': 'every call shown under a `readings` or `depends` relation of a stored review, replayed on '
                   'the monitors of the two readings (experiments/comm_replay.py)',
           'totals': totals(store), 'requests': dict(sorted(store.items()))}
    with open(STORE + '.tmp', 'w') as f:
        json.dump(doc, f, indent=1)
        f.write('\n')
    os.replace(STORE + '.tmp', STORE)


def scoped(key: str, gb: float, secs: int, cases: int = CASES) -> dict:
    """The replay of one request in a process of its own, inside a memory cap
    and a time limit: a witness of long strings can need gigabytes."""
    systemd = ['systemd-run', '--user', '--scope', '-q']
    capped = bool(shutil.which('systemd-run')) and not subprocess.run(systemd + ['--', 'true'],
                                                                      capture_output=True).returncode
    unit = f'fcp-replay-{key}-{os.getpid()}'
    cmd = [sys.executable, '-I', '-u', os.path.abspath(__file__), 'one', key, str(cases)]
    if capped:
        cmd = systemd + ['--unit', unit, '-p', f'MemoryMax={int(gb * 1024)}M', '-p', 'MemorySwapMax=0',
                         '-p', f'RuntimeMaxSec={secs + 30}', '--'] + cmd
    t = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        text, _ = proc.communicate(timeout=secs)
        status = 'ok' if proc.returncode == 0 else f'stopped: exit code {proc.returncode}'
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        text, _ = proc.communicate()
        status = f'stopped after {secs} s'
    if capped:
        ctl = lambda *a: subprocess.run(('systemctl', '--user') + a + (unit + '.scope',),
                                        capture_output=True, text=True).stdout.strip()
        for _ in range(10 if status != 'ok' else 1):    # killed: systemd learns why a moment later
            if ctl('show', '-p', 'Result', '--value') == 'oom-kill':
                status = f'stopped: more than {gb:g} GB of memory'
                break
            time.sleep(0.2)
        ctl('kill', '--signal=KILL')
        ctl('stop')
        ctl('reset-failed')
    rels = None
    for l in text.splitlines():
        if l.startswith('RESULT '):
            rels = json.loads(l[7:])
    if status == 'ok' and rels is None:
        status = 'stopped: no result'
    res = {'status': status, 'seconds': round(time.time() - t, 1), 'relations': rels if status == 'ok' else []}
    if status != 'ok':
        res['tail'] = text[-400:]
    return res


def drive(keys: list, gb: float, secs: int, force: bool, cases: int = CASES):
    ps = [p for p in C.prompts() if C.status(p).get('check') == 'ok'
          and os.path.exists(os.path.join(C.work(p), 'out', 'review.json'))]
    live = {p['key'] for p in ps}
    store = {k: v for k, v in load().items() if k in live}      # a request without a review now has no entry
    for p in ps:
        if keys and p['key'] not in keys:
            continue
        with open(os.path.join(C.work(p), 'out', 'review.json'), 'rb') as f:
            raw = f.read()
        sha = hashlib.sha256(raw).hexdigest()[:16]
        n = len(shown(json.loads(raw)))
        old = store.get(p['key'])
        if old and old['review'] == sha and old['status'] in ('ok', 'no call') and not force:
            continue
        res = {'task': p['task'], 'variant': p['variant'], 'review': sha, 'with_call': n}
        res.update(scoped(p['key'], gb, secs, cases) if n else {'status': 'no call', 'seconds': 0, 'relations': []})
        if n and cases != CASES:
            res['cases'] = cases                # replayed with a bound other than the default
        store[p['key']] = res
        save(store)
        bad = [r for r in res['relations'] if r['result'] != 'confirmed']
        print(time.strftime('%H:%M:%S'), p['task'], p['variant'], p['key'], res['status'] + ',',
              n, 'with a call,', res['seconds'], 's',
              ''.join(f"\n    {r['kind']} {r['req']}: {r['result']} {r.get('error', '')} {str(r['calls'])[:160]}"
                      for r in bad), flush=True)
    save(store)
    print('TOTAL', json.dumps(totals(store)), flush=True)


def main():
    global CASES
    args = sys.argv[1:]
    os.environ['PATH'] = os.path.join(ROOT, '.tools', 'oss-cad-suite', 'bin') + os.pathsep + os.environ['PATH']
    if args[:1] == ['one']:
        if len(args) > 2:
            CASES = int(args[2])
        print('RESULT ' + json.dumps(replay(args[1])), flush=True)
        return
    if args[:1] == ['totals']:
        print(json.dumps(totals(load()), indent=1))
        return
    gb, secs, force, keys, cases = 3.0, 300, False, [], CASES
    while args:
        a = args.pop(0)
        if a == '--gb':
            gb = float(args.pop(0))
        elif a == '--seconds':
            secs = int(args.pop(0))
        elif a == '--cases':
            cases = int(args.pop(0))
        elif a == '--force':
            force = True
        else:
            keys.append(a)
    drive(keys, gb, secs, force, cases)


if __name__ == '__main__':
    main()
