"""Forcing-stimulus search (Session.forcing) on every formalization set of the
corpus, compared with the conflicts the consistency analysis reported.

For each set: the conflicts (minimal cores) found by forcing, the cores found
by consistency (from the study evidence where it exists, else recomputed),
and the cores only one of the two analyses found.  Writes
results/forcing_check.json.
"""
from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from fcp.analyses import Session  # noqa: E402

BUNDLES = ['fifo', 'arbiter', 'bridge', 'hub', 'prompt_email', 'agent_desk']
OUT = os.path.join(HERE, 'results')


def published(d: str) -> dict:
    for name in (f'{d}_evidence.json',):
        p = os.path.join(OUT, name)
        if os.path.exists(p):
            with open(p) as f:
                ev = json.load(f)
            return {s: x.get('consistency') for s, x in ev['sets'].items() if x.get('consistency')}
    return {}


def main(bundles):
    res = {}
    for d in bundles:
        root = os.path.join(ROOT, 'corpus', d)
        S = Session(root)
        pub = published(d)
        for s in sorted(S.b.fsets):
            try:
                S.mon(s)
            except Exception as e:  # ill-formed agent sets are skipped, as in the study
                res[f'{d}/{s}'] = {'error': str(e)[:200]}
                continue
            t = time.time()
            f = S.forcing(s, depth=max(S.lookahead(s) + 2, 4), max_iter=60)
            cons = pub.get(s)
            src = 'published'
            if cons is None:
                cons = S.consistency(s)
                src = 'recomputed'
            fc = {tuple(c['core']) for c in f['conflicts']}
            cc = {tuple(c['mus']) for c in cons.get('conflicts', [])}
            res[f'{d}/{s}'] = {'forcing': [c['core'] for c in f['conflicts']], 'forcing_reqs': [c['reqs'] for c in f['conflicts']],
                               'consistency': [c['mus'] for c in cons.get('conflicts', [])], 'consistency_source': src,
                               'only_forcing': sorted(map(list, fc - cc)), 'only_consistency': sorted(map(list, cc - fc)),
                               'undecided': [r for r in f['searches'] if r['undecided']], 'seconds': round(time.time() - t, 1)}
            r = res[f'{d}/{s}']
            print(f"{d}/{s}: forcing {len(fc)} consistency {len(cc)} ({src}) only-forcing {r['only_forcing']} "
                  f"only-consistency {r['only_consistency']} undecided {len(r['undecided'])} {r['seconds']}s", flush=True)
    path = os.path.join(OUT, 'forcing_check.json')
    old = {}
    if os.path.exists(path):        # results of bundles not re-run are kept
        with open(path) as f:
            old = {k: v for k, v in json.load(f).items() if k.split('/')[0] not in bundles}
    with open(path, 'w') as f:
        json.dump({**old, **res}, f, indent=1)


if __name__ == '__main__':
    main(sys.argv[1:] or BUNDLES)
