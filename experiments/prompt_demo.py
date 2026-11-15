"""A prompt checked as a chip: run the unchanged FCP pipeline on corpus/prompt_email.

  1. For every response, build one replay chip per labeler (fcp.text.build).
  2. Run the spec-only analyses on every reading of the prompt (consistency with
     minimal conflicting sets, tautology, pairwise comparison with
     distinguishing responses) and verification, vacuity and triage of every
     reading on every response chip.
  3. Print the results in prompt terms and write results/prompt_email.json.

Needs responses/<r>.md and responses/<r>.labels.yaml (two labelers' labels).
"""
from __future__ import annotations

import json
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from fcp import pipeline  # noqa: E402
from fcp.text import build, merge, render_trace, rule_labels, RULE_LABELS  # noqa: E402

B = os.path.join(ROOT, 'corpus', 'prompt_email')
OUT = os.path.join(HERE, 'results')
ANALYSES = ('lint', 'tautology', 'consistency', 'verify', 'vacuity', 'triage', 'compare')


def chips(responses: list[str]) -> dict:
    """Build replay chips and register them as RTL variants; return label disputes."""
    with open(os.path.join(B, 'design.yaml')) as f:
        d = yaml.safe_load(f)
    disputes = {}
    for r in responses:
        lp = os.path.join(B, 'responses', f'{r}.labels.yaml')
        for rel in build(B, lp):
            v = os.path.basename(rel)[:-2]
            who = 'the adjudicator' if v.endswith('_lh') else f'labeler {v[-1].upper()}'
            d['rtl'][v] = {'top': 'response', 'files': [rel], 'origin': 'fcp-text-adapter',
                           'desc': f'response {r}, labels by rules + {who}'}
        with open(lp) as f:
            L = yaml.safe_load(f)
        units = [u['text'] for u in L['units']]
        rules = rule_labels(units)
        a = [set(x) | (set(u.get('a') or []) - RULE_LABELS) for x, u in zip(rules, L['units'])]
        b = [set(x) | (set(u.get('b') or []) - RULE_LABELS) for x, u in zip(rules, L['units'])]
        disputes[r] = [dict(x, text=units[x['unit']]) for x in merge(a, b)]
    with open(os.path.join(B, 'design.yaml'), 'w') as f:
        yaml.safe_dump(d, f, sort_keys=False, width=200, default_flow_style=None)
    return disputes


def frame_reqs(ev: dict) -> set:
    return {r for r, x in ev['requirements'].items() if x['doc'] == 'FRAME'}


def report(ev: dict, sets: list[str], responses: list[str], disputes: dict) -> dict:
    fr = frame_reqs(ev)
    units = {}
    for r in responses:
        with open(os.path.join(B, 'responses', f'{r}.labels.yaml')) as f:
            units[r] = [u['text'] for u in yaml.safe_load(f)['units']]
    res = {'consistency': {}, 'compare': {}, 'verdicts': {}, 'label_disputes': disputes}
    print('== Prompt-level analyses (no response needed)')
    for s in sets:
        c = ev['sets'][s].get('consistency', {})
        confl = [{'reqs': [q for q in x['reqs'] if q not in fr], 'frame': [q for q in x['reqs'] if q in fr]}
                 for x in c.get('conflicts', [])]
        taut = [k for k, v in ev['sets'][s].get('tautology', {}).items() if v.get('tautology')]
        res['consistency'][s] = {'consistent': c.get('consistent'), 'conflicts': confl, 'tautologies': taut}
        print(f'[{s}] satisfiable: {c.get("consistent")}  tautologies: {taut or "none"}')
        for x in confl:
            print(f'    conflict: {", ".join(x["reqs"])}   (+ frame {", ".join(x["frame"])})')
    for key, cmp_ in ev['compare'].items():
        rows = {}
        for req, c in cmp_.items():
            if req in fr or req == '<assumptions>':
                continue
            rows[req] = {'relation': c['relation']}
            for w in ('witness_a_not_b', 'witness_b_not_a'):
                if c.get(w):
                    rows[req][w] = render_trace(c[w])
        res['compare'][key] = rows
        a, b = key.split('|')
        print(f'== Readings compared: {a} vs {b}')
        for req, x in rows.items():
            print(f'  {req:10s} {x["relation"]}')
            for w, lab in (('witness_a_not_b', f'accepted by {a}, rejected by {b}'),
                           ('witness_b_not_a', f'accepted by {b}, rejected by {a}')):
                if w in x:
                    print(f'      {lab}: ' + ' | '.join(x[w]))
    print('== Responses verified (per reading, per labeler)')
    for s in sets:
        if s not in ev['assessment']:
            continue
        for v, A in ev['assessment'][s].items():
            fails = {rid: x for rid, x in A['requirements'].items()
                     if x['status'] == 'FAILED' and rid not in fr}
            frame_fail = [rid for rid, x in A['requirements'].items() if x['status'] == 'FAILED' and rid in fr]
            res['verdicts'].setdefault(s, {})[v] = {'failed': sorted(fails), 'frame_failed': frame_fail,
                                                     'levels': {rid: x['level'] for rid, x in A['requirements'].items()}}
            print(f'[{s} / {v}] fails: {", ".join(sorted(fails)) or "none"}' +
                  (f'  FRAME VIOLATED: {frame_fail}' if frame_fail else ''))
            r = v.rsplit('_', 1)[0]
            ver = ev['sets'][s]['rtl'][v].get('verify', {})
            for rid in sorted(fails):
                for pid in fails[rid]['properties']:
                    tr = ver.get(pid, {}).get('trace')
                    if tr and r in units:
                        n = len([st for st in tr if str(st.get('rst_n')) != '0']) - 1
                        if 0 <= n < len(units[r]):
                            print(f'      {pid} violated at unit {n}: "{units[r][n][:80]}"')
                        else:
                            print(f'      {pid} violated at the end of the response')
    print('== Label disputes (labeler A vs B)')
    for r, ds in disputes.items():
        for x in ds:
            print(f'  {r} unit {x["unit"]} {x["label"]}: A={int(x["a"])} B={int(x["b"])}  "{x["text"][:70]}"')
    return res


if __name__ == '__main__':
    responses = sys.argv[1:] or sorted(f[:-3] for f in os.listdir(os.path.join(B, 'responses'))
                                       if f.endswith('.md'))
    disputes = chips(responses)
    sets = sorted(f[:-5] for f in os.listdir(os.path.join(B, 'formal')) if f.endswith('.yaml'))
    with open(os.path.join(B, 'design.yaml')) as f:
        variants = list(yaml.safe_load(f)['rtl'])
    ev = pipeline.run(B, sets, variants, analyses=ANALYSES, log=lambda *a: None)
    os.makedirs(OUT, exist_ok=True)
    pipeline.save(ev, os.path.join(OUT, 'prompt_email_evidence.json'))
    res = report(ev, sets, responses, disputes)
    res['runtime'] = ev['runtime'].get('total')
    with open(os.path.join(OUT, 'prompt_email.json'), 'w') as f:
        json.dump(res, f, indent=1)
    print(f'total {ev["runtime"]["total"]}s')
