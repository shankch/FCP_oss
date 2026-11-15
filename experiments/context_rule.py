"""Does comparing readings in context raise assurance yield without false assurance?

  strict    the FCP rule (ASSURED): proved, clean, and the two independent readings
            of the requirement are equivalent
  context   strict, or: proved and clean, the two readings are equivalent on every
            behaviour that meets all *other* requirements under both readings
            (Session.compare(context=True)), and every other requirement of both
            readings is proved on this RTL variant.  The variant's behaviours then lie
            inside that context, so the peer's reading of the requirement holds as well.
  minimal   as context, but only the requirements of a minimal sufficient context
            (Session.minimal_context: drop context requirements while the readings stay
            equivalent) must be proved on the variant.  The argument is the same.

Yield and false assurance are counted exactly as in decision_rules.py.  The script
also checks the argument empirically: whenever `context` accepts a requirement that
`strict` does not, the peer's reading must be proved on the variant too.
Needs experiments/results/<design>.json and <design>_evidence.json from run_study.py.
"""
from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from run_study import DESIGNS, OUT, ground_truth, verdicts  # noqa: E402
from fcp.analyses import Session  # noqa: E402

CLEAN = {'ASSURED', 'PROVED-DISPUTED'}
RULES = ('strict', 'context', 'minimal')
PLAIN_AGREE = {'EQUIVALENT', 'ONLY-A', 'ONLY-B'}


def context_relations(d: str, ev: dict, s: str, p: str) -> dict:
    cmp_ = ev['compare'].get(f'{s}|{p}') or ev['compare'].get(f'{p}|{s}') or {}
    disputed = {r for r, c in cmp_.items() if r != '<assumptions>' and c['relation'] not in PLAIN_AGREE}
    if not disputed:
        return {}
    S = Session(os.path.join(ROOT, 'corpus', d))
    out = {}
    for r, c in S.compare(s, p, context=True, only=disputed).items():
        out[r] = {'relation': c['relation'],
                  'minimal': S.minimal_context(s, p, r) if c['relation'] == 'EQUIVALENT' else None}
    return out


def evaluate(d: str) -> dict:
    with open(os.path.join(OUT, f'{d}.json')) as f:
        R = json.load(f)
    with open(os.path.join(OUT, f'{d}_evidence.json')) as f:
        ev = json.load(f)
    agents = [a for a in R['agent_sets'] if 'ill_formed' not in R['sets'][a]]
    gt = ground_truth(ev, R['variants'])
    rel = {}
    out = {}
    for s in agents:
        peers = [a for a in agents if a != s]
        if not peers:
            continue
        p = peers[0]
        key = '|'.join(sorted((s, p)))
        if key not in rel:
            t = time.time()
            rel[key] = context_relations(d, ev, s, p)
            print(f'  {d} {key}: in context {rel[key]}  ({time.time() - t:.0f}s)', flush=True)
        row = {'ref_formalized': 0, 'violations': 0, 'theorem_violations': [], 'gained': [],
               **{k: {'ref_accepted': 0, 'false_assurance': 0} for k in RULES}}
        for v in R['variants']:
            vs = verdicts(ev, s, v, [p])['reqs']
            vp = verdicts(ev, p, v, [s])['reqs']
            for rid, x in vs.items():
                c = rel[key].get(rid) or {}
                eq = x['level'] in CLEAN and c.get('relation') == 'EQUIVALENT'
                ctx_ok = (eq and all(vs[r]['naive'] for r in vs if r != rid)
                          and all(vp[r]['naive'] for r in vp if r != rid))
                min_ok = eq and c.get('minimal') is not None and all(
                    all(z[r]['naive'] for z in (vs, vp) if r in z) for r in c['minimal'])
                acc = {'strict': x['fcp'], 'context': x['fcp'] or ctx_ok, 'minimal': x['fcp'] or min_ok}
                if min_ok and not x['fcp']:
                    row['gained'].append({'variant': v, 'req': rid, 'plain': x['level'], 'full_context': ctx_ok})
                    if rid in vp and not vp[rid]['naive']:
                        row['theorem_violations'].append({'variant': v, 'req': rid})
                if v == 'ref':
                    row['ref_formalized'] += 1
                    for k in acc:
                        row[k]['ref_accepted'] += acc[k]
                if gt[v].get(rid):
                    row['violations'] += 1
                    for k in acc:
                        row[k]['false_assurance'] += acc[k]
        out[s] = row
    out['_relations'] = rel
    return out


if __name__ == '__main__':
    res = {d: evaluate(d) for d in (sys.argv[1:] or DESIGNS)}
    tot = {k: {'ref_accepted': 0, 'false_assurance': 0} for k in RULES}
    nref = nviol = 0
    thm = []
    for d, sets in res.items():
        for s, r in sets.items():
            if s.startswith('_'):
                continue
            nref += r['ref_formalized']
            nviol += r['violations']
            thm += r['theorem_violations']
            for k in tot:
                for m in tot[k]:
                    tot[k][m] += r[k][m]
            print(f"{d:8s} {s:8s} " + '  '.join(
                f"{k}: ref {r[k]['ref_accepted']}/{r['ref_formalized']} FA {r[k]['false_assurance']}/{r['violations']}"
                for k in tot))
    res['totals'] = {'ref_formalized': nref, 'violations': nviol, 'theorem_violations': thm, **tot}
    with open(os.path.join(OUT, 'context_rule.json'), 'w') as f:
        json.dump(res, f, indent=1)
    for k in tot:
        print(f"TOTAL {k:8s} accepted on ref {tot[k]['ref_accepted']}/{nref}  "
              f"false assurance {tot[k]['false_assurance']}/{nviol}")
    print('peer reading unproved where context accepted (must be 0):', len(thm))
