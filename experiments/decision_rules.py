"""Compare acceptance rules for a requirement on one RTL variant, using the study evidence.

  naive         every property of the set for the requirement is proved
  all_readings  the set's reading and its independent peer's reading are both proved
                and clean (non-vacuous, receptive environment, conflict-free), even if
                the two readings differ: accept when no surviving reading rejects this RTL
  strict        the FCP rule: proved, clean, and the two readings are equivalent (ASSURED)

For each rule it reports the requirements accepted without human input on the reference
RTL (yield) and the violated requirements accepted on buggy variants (false assurance).
Needs experiments/results/<design>_evidence.json from run_study.py.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from run_study import DESIGNS, OUT, ground_truth, verdicts  # noqa: E402

RULES = ('naive', 'all_readings', 'strict')
CLEAN = {'ASSURED', 'PROVED-DISPUTED'}


def accept(x: dict, peer: dict | None) -> dict:
    both = x['level'] in CLEAN and peer is not None and peer['level'] in CLEAN
    return {'naive': x['naive'], 'all_readings': x['fcp'] or both, 'strict': x['fcp']}


def evaluate(d: str) -> dict:
    with open(os.path.join(OUT, f'{d}.json')) as f:
        R = json.load(f)
    with open(os.path.join(OUT, f'{d}_evidence.json')) as f:
        ev = json.load(f)
    agents = [a for a in R['agent_sets'] if 'ill_formed' not in R['sets'][a]]
    gt = ground_truth(ev, R['variants'])
    out = {}
    for s in agents:
        peers = [a for a in agents if a != s]
        if not peers:
            continue
        row = {'ref_formalized': 0, 'violations': 0, 'cases': [],
               **{k: {'ref_accepted': 0, 'false_assurance': 0} for k in RULES}}
        for v in R['variants']:
            vs = verdicts(ev, s, v, peers)['reqs']
            vp = verdicts(ev, peers[0], v, [s])['reqs']
            for rid, x in vs.items():
                acc = accept(x, vp.get(rid))
                if v == 'ref':
                    row['ref_formalized'] += 1
                    for k in RULES:
                        row[k]['ref_accepted'] += acc[k]
                if gt[v].get(rid):
                    row['violations'] += 1
                    for k in RULES:
                        row[k]['false_assurance'] += acc[k]
                    if acc['all_readings'] and not acc['strict']:
                        row['cases'].append({'variant': v, 'req': rid})
        out[s] = row
    return out


if __name__ == '__main__':
    res = {d: evaluate(d) for d in (sys.argv[1:] or DESIGNS)}
    tot = {k: {'ref_accepted': 0, 'false_assurance': 0} for k in RULES}
    nref = nviol = 0
    for d, sets in res.items():
        for s, r in sets.items():
            nref += r['ref_formalized']
            nviol += r['violations']
            for k in RULES:
                for m in ('ref_accepted', 'false_assurance'):
                    tot[k][m] += r[k][m]
            print(f"{d:8s} {s:8s} " + '  '.join(
                f"{k}: ref {r[k]['ref_accepted']}/{r['ref_formalized']} FA {r[k]['false_assurance']}/{r['violations']}"
                for k in RULES))
    res['totals'] = {'ref_formalized': nref, 'violations': nviol, **tot}
    with open(os.path.join(OUT, 'decision_rules.json'), 'w') as f:
        json.dump(res, f, indent=1)
    for k in RULES:
        print(f"TOTAL {k:12s} accepted on ref {tot[k]['ref_accepted']}/{nref}  "
              f"false assurance {tot[k]['false_assurance']}/{nviol}")
