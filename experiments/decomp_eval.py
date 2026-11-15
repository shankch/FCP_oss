"""Evaluate the decomposer agents against the gold requirement lists.

Matching is by verbatim-quote overlap (the quotes are tool-verified), so no
judgement is involved: a gold requirement is recalled if some agent
requirement's quote covers at least 60% of its tokens.  A ground-truth spec
defect counts as flagged if the agent attached an ambiguity/contradiction
note to a requirement matching one of the defect's gold requirements.
"""
from __future__ import annotations

import json
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def toks(s: str) -> set[str]:
    return set(re.findall(r'[a-z0-9_]+', s.lower()))


def coverage(g: str, a: str) -> float:
    tg = toks(g)
    return len(tg & toks(a)) / len(tg) if tg else 0.0


def evaluate(design: str) -> dict:
    base = os.path.join(ROOT, 'corpus', design)
    gold = yaml.safe_load(open(os.path.join(base, 'requirements.yaml')))['requirements']
    p = os.path.join(base, 'agents', 'decomposer', 'requirements.yaml')
    if not os.path.exists(p):
        return {}
    agent = yaml.safe_load(open(p))['requirements']
    defects = yaml.safe_load(open(os.path.join(base, 'spec_defects.yaml')))['defects']
    match = {}
    for g in gold:
        best = max(agent, key=lambda a: coverage(g['quote'], a['quote']))
        cov = coverage(g['quote'], best['quote'])
        cands = [a for a in agent if coverage(g['quote'], a['quote']) >= 0.6 or
                 coverage(a['quote'], g['quote']) >= 0.8]
        match[g['id']] = {'recalled': cov >= 0.6 or bool(cands), 'cov': round(cov, 2),
                          'agents': [a['id'] for a in cands] or [best['id']],
                          'kind_gold': g['kind'], 'kinds_agent': sorted({a['kind'] for a in cands})}
    recalled = sum(1 for m in match.values() if m['recalled'])
    kind_ok = sum(1 for m in match.values() if m['recalled'] and m['kind_gold'] in m['kinds_agent'])
    amb_by_id = {a['id']: bool(a.get('ambiguity')) for a in agent}
    flagged = {}
    for d in defects:
        ids = set()
        for gid in d['reqs']:
            if gid in match:
                ids |= set(match[gid]['agents'])
        flagged[d['id']] = any(amb_by_id.get(i) for i in ids)
    return {'design': design, 'gold': len(gold), 'agent': len(agent), 'recalled': recalled,
            'recall': round(recalled / len(gold), 3), 'kind_agreement': kind_ok,
            'with_ambiguity': sum(amb_by_id.values()), 'defects': flagged,
            'defects_planted': [d['id'] for d in defects if d.get('planted')],
            'unmatched_gold': [g for g, m in match.items() if not m['recalled']]}


if __name__ == '__main__':
    out = {d: evaluate(d) for d in (sys.argv[1:] or ['fifo', 'arbiter', 'bridge', 'hub'])}
    os.makedirs(os.path.join(ROOT, 'experiments', 'results'), exist_ok=True)
    with open(os.path.join(ROOT, 'experiments', 'results', 'decomposition.json'), 'w') as f:
        json.dump(out, f, indent=1)
    for d, r in out.items():
        if r:
            print(f"{d:8s} gold={r['gold']:2d} agent={r['agent']:2d} recall={r['recall']} kind-agree={r['kind_agreement']}/{r['recalled']} "
                  f"amb={r['with_ambiguity']} defects flagged={r['defects']} unmatched={r['unmatched_gold']}")
