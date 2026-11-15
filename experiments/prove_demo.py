"""Proofs beyond the scope on the checkout study (fcp.prove).

    python experiments/prove_demo.py [corpus]          (default code_checkout)

For every implementation of the study (the three models, the reference and
the planted variants) and every reading, each requirement is checked over
every call the interface can carry, and the verdict is set beside the one
the scope gives (run again here): PASS on the scope and PROVED, FAIL on the
scope and FAILS in the proof (z3's calls replayed on the code and confirmed
on the monitors), or a failure the scope missed.  Code with effects
(an interface) is proved over every run: every argument and every script
of answers (fcp.prove.prove_effects).  An object is proved over every
sequence of calls of any length, by induction with an invariant found by
Houdini; where no invariant is found, over every sequence up to the
scope's longest, a bounded proof (fcp.prove.prove_object; an object that
holds dictionaries or lists: fcp.keyedproof).
Writes experiments/results/prove_<corpus>.json.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from fcp import effects as FX, prove as P, software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402

SETS = ['gold', 'agent_a', 'agent_b', 'variant']


def implementations(B: str, fname: str, module: str = '') -> dict:
    out = {}
    for m in ('haiku', 'sonnet', 'opus'):
        hit = [p for n in dict.fromkeys([module.split('.')[-1], fname]) if n
               for p in glob.glob(os.path.join(B, 'agents', f'coder_{m}', f'{n}.py'))]
        if hit:
            out[m] = hit[0]
    out['ref'] = os.path.join(B, 'impl', 'ref.py')
    for p in sorted(glob.glob(os.path.join(B, 'bugs', 'C*.py')), key=lambda p: int(os.path.basename(p)[1:-3])):
        out[os.path.basename(p)[:-3]] = p
    return out


def scope_verdicts(ver: dict) -> dict:
    """Per requirement: FAIL if any item of it failed on the scope, else PASS."""
    out: dict[str, str] = {}
    for iid, v in ver.items():
        if v.get('role') != 'property' or not v.get('req'):
            continue
        out[v['req']] = 'FAIL' if v['status'] == 'FAIL' or out.get(v['req']) == 'FAIL' else 'PASS'
    return out


def main():
    corpus = sys.argv[1] if len(sys.argv) > 1 else 'code_checkout'
    B = os.path.join(ROOT, 'corpus', corpus)
    sets = [s for s in SETS if os.path.exists(os.path.join(B, 'formal', f'{s}.yaml'))]
    S = Session(B, sets=sets)
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    frame_reqs = {S.mon(s).items[i].req for s in sets for i in S.b.frame_ids if i in S.mon(s).items}
    t0 = time.time()
    calls = FX.scope(S, fn, ifc) if ifc else SW.calls_for(S, fn)
    out = {'calls' if not ifc else 'runs': len(calls), 'implementations': {}, 'summary': {}}
    tally = {'proved': 0, 'proved_bounded': 0, 'fails_both': 0, 'missed_by_scope': 0, 'scope_only': 0,
             'unknown': 0, 'pairs': 0, 'untranslatable': [], 'seconds': []}
    for name, src in implementations(B, fn.name, fn.module or '').items():
        res = FX.run(fn, ifc, src, calls) if ifc else SW.run(fn, src, calls)
        cols = None if ifc else SW.trace(fn, calls, res)
        rec = {}
        for s in sets:
            sc = scope_verdicts(FX.verify(S, s, fn, ifc, src, calls, res) if ifc else
                                SW.verify(S, s, fn, src, calls, res, cols))
            t = time.time()
            pr = P.prove_effects(S, s, fn, ifc, src, calls, res) if ifc else \
                P.prove_object(S, s, fn, src, calls, res) if fn.stateful else P.prove(S, s, fn, src, calls, res)
            dt = round(time.time() - t, 1)
            row = {'status': pr['status'], 'seconds': dt}
            if pr['status'] != 'ok':
                row['why'] = pr['why'] if isinstance(pr['why'], str) else json.dumps(pr['why'])
                tally['untranslatable'].append(f'{name}/{s}: {row["why"]}')
                rec[s] = row
                print(name, s, pr['status'], row['why'], flush=True)
                continue
            tally['pairs'] += 1
            tally['seconds'].append(dt)
            row['requirements'] = {}
            if 'induction' in pr:
                row['induction'] = pr['induction']
            if 'sweep' in pr:                        # strings and lists: the agreements proved before the goals
                row['sweep'] = pr['sweep']
            for r, x in pr['requirements'].items():
                if r in frame_reqs:
                    continue
                cell = {'proof': x['status'], 'scope': sc.get(r)}
                if x['status'] == 'FAILS':
                    cell.update(confirmed=x['confirmed'], items=x['items'])
                    cell.update({k: x[k] for k in ('calls', 'call', 'conversation', 'rigids') if k in x})
                if 'invariant' in x:
                    cell['invariant'] = x['invariant']
                if x['status'] == 'PROVED-BOUNDED':
                    cell['k'] = x.get('k')
                if any('nodes' in d or 'cases' in d for d in x.get('sweep') or []):   # settled with the path's facts assumed
                    cell['sweep'] = x['sweep']
                    tally['with_path_facts'] = tally.get('with_path_facts', 0) + 1
                proved = x['status'] in ('PROVED', 'PROVED-BOUNDED')
                if proved and cell['scope'] == 'PASS':
                    tally['proved'] += 1
                    tally['proved_bounded'] += x['status'] == 'PROVED-BOUNDED'
                elif x['status'] == 'FAILS' and cell['scope'] == 'FAIL':
                    tally['fails_both'] += 1
                elif x['status'] == 'FAILS':
                    tally['missed_by_scope'] += 1
                elif proved:
                    tally['scope_only'] += 1         # the scope failed what the proof proved: a contradiction
                else:
                    tally['unknown'] += 1
                row['requirements'][r] = cell
            rec[s] = row
            print(name, s, dt, 's', {r: f"{c['scope']}/{c['proof']}" for r, c in row['requirements'].items()},
                  flush=True)
        out['implementations'][name] = rec
    tally['seconds'] = [min(tally['seconds'] or [0]), max(tally['seconds'] or [0])]
    out['summary'] = tally
    out['seconds'] = round(time.time() - t0)
    print(json.dumps(tally, indent=1))
    with open(os.path.join(HERE, 'results', f'prove_{corpus}.json'), 'w') as f:
        json.dump(out, f, indent=1)


if __name__ == '__main__':
    main()
