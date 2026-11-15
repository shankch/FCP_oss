"""Code with effects checked with FCP: python effects_demo.py [corpus] (default code_pay).

The same six steps as code_demo.py, for a function that acts through an
interface it receives (fcp.effects): the prompt alone (conflicts on scripts
of answers, readings compared by bounded model checking), every
implementation run against every script of the scope, where the AI
implementations disagree, the models' own tests, planted bugs and mutants,
and false assurance, and proofs beyond the scope.  Writes results/<corpus>.json.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORPUS = sys.argv[1] if len(sys.argv) > 1 else 'code_pay'
sys.argv = [sys.argv[0], CORPUS]
sys.path.insert(0, HERE)

import code_demo as CD  # noqa: E402
from fcp import effects as FX, pipeline, software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402

B, OUT, SETS, PEERS, MODELS = CD.B, CD.OUT, CD.SETS, CD.PEERS, CD.MODELS


def conversation_lines(S, fn, ifc, tr: list) -> list[str]:
    """A spec-only witness trace as calls on api and the return."""
    rst, low = S.b.iface.reset.name, S.b.iface.reset.active_low
    segs = [[]]
    for st in tr:
        if int(st.get(rst) or 0) == (0 if low else 1):
            if segs[-1]:
                segs.append([])
            continue
        segs[-1].append(st)
    seg = next((x for x in reversed(segs) if x), [])
    by_op = {m['op']: m for m in ifc.methods}
    out = []
    for st in seg:
        if int(st.get(ifc.phase) or 0):
            code = int(st.get(fn.outcome) or 0)
            out.append('returns ' + (str(bool(int(st.get(fn.rets[0]) or 0))) if code == 0 else fn.outcome_name(code)))
            break
        m = by_op.get(int(st.get(ifc.op) or 0))
        if m is None:
            out.append('(no call)')
            continue
        args = ', '.join(str(int(st.get(a) or 0)) for a in FX.arg_sigs(m))
        k = int(st.get(ifc.answer) or 0)
        got = (f' -> "{ifc.answers[k]}"' if k < len(ifc.answers) else f' -> answer {k}') if m.get('answers') else ''
        hn = int(st.get(ifc.handle) or 0) if ifc.handle else 0
        out.append(f'{FX.method_name(ifc, m, hn)}({args}){got}')
    head = ', '.join(f'{a}={int(seg[0].get(sig) or 0)}' for a, sig, _ in fn.args) if seg else ''
    return [f'[{head}]'] + out


def prompt_level(S, fn, ifc, ev: dict) -> dict:
    out = {}
    for s in SETS:
        rec = ev['sets'][s]
        cons = rec.get('consistency', {})
        out[s] = {'trigger_situations': {'consistent': cons.get('consistent'),
                                         'conflicts': [x['reqs'] for x in cons.get('conflicts', [])]},
                  'boundary': FX.conflicts(S, s, fn, ifc),
                  'open': {'open': {}, 'checked': 0, 'note': 'not searched for interfaces'},
                  'tautologies': [k for k, v in rec.get('tautology', {}).items() if v.get('tautology')]}
    return out


def readings(S, fn, ifc) -> dict:
    """Readings compared by the chip engine to bmc_depth cycles (bounded)."""
    S.cmp_engine = 'bmc'
    out = {}
    for i, a in enumerate(SETS):
        for b in SETS[i + 1:]:
            plain = S.compare(a, b)
            rec = {r: {'plain': x['relation'], 'bounded': x.get('depth')} for r, x in plain.items()
                   if r != '<assumptions>'}
            disputed = {r for r, x in rec.items() if x['plain'] not in CD.PLAIN_AGREE}
            if disputed:
                for r, x in S.compare(a, b, context=True, only=disputed).items():
                    if r not in rec:
                        continue
                    rec[r]['context'] = x['relation']
                    for w in ('a_not_b', 'b_not_a'):
                        if x.get(f'witness_{w}'):
                            rec[r][w] = {'lines': conversation_lines(S, fn, ifc, x[f'witness_{w}'])}
            out[f'{a}|{b}'] = rec
    return out


def code_level(S, fn, ifc, imps: dict, runs: list) -> dict:
    out = {}
    for name, src in imps.items():
        res = FX.run(fn, ifc, src, runs)
        out[name] = {'runs': len(runs), 'calls': sum(len(r['events']) for r in res),
                     'verify': {s: FX.verify(S, s, fn, ifc, src, runs, res) for s in SETS}, '_res': res}
    return out


def splits(fn, ifc, runs: list, results: dict) -> list[dict]:
    """Where the AI implementations end a run differently: grouped by how the
    implementations split, the shortest script of each group."""
    names = list(results)
    groups: dict[tuple, dict] = {}
    for i in range(len(runs)):
        outs = {n: json.dumps([results[n][i]['events'], results[n][i]['code'], results[n][i]['ret']]) for n in names}
        if len(set(outs.values())) == 1:
            continue
        part: dict[str, list[str]] = {}
        for n in names:
            part.setdefault(outs[n], []).append(n)
        key = tuple(sorted(tuple(g) for g in part.values()))
        g = groups.setdefault(key, {'count': 0, 'best': i})
        g['count'] += 1
        if (len(runs[i][1]), runs[i]) < (len(runs[g['best']][1]), runs[g['best']]):
            g['best'] = i
    out = []
    for key, g in sorted(groups.items(), key=lambda kv: -kv[1]['count']):
        i = g['best']
        out.append({'groups': [list(x) for x in key], 'count': g['count'], 'call': FX.call_text(fn, ifc, runs, i),
                    'answers': {n: ' ; '.join(FX.conversation(fn, ifc, runs, results[n], i)) for n in names}})
    return out


def detection(S, fn, ifc, bugs: list[dict], imps: dict, runs: list, tests: dict) -> dict:
    gm = S.mon('gold')

    def verdicts(src):
        res = FX.run(fn, ifc, src, runs)
        cols, _ = FX.trace(fn, ifc, runs, res)
        chk = SW.check(S, 'gold', cols)
        return {i: (x['first'], x['count']) for i, x in chk.items() if gm.items[i].role in ('property', 'scenario')}
    ref_v = verdicts(imps['ref'])
    out = {}
    for b in bugs:
        bv = verdicts(imps[b['id']])
        new = sorted({gm.items[i].req for i in bv if bv[i] != ref_v[i] and gm.items[i].req and not i.startswith('F-')})
        suites = {m: sorted(set(tests[m][b['id']]['failing']) - set(tests[m]['ref']['failing'])) for m in MODELS}
        out[b['id']] = {'desc': b['desc'], 'planted': b.get('violates', []), 'fcp_gold': new,
                        'tests': {m: len(x) for m, x in suites.items()}}
    return out


def mutation_level(S, fn, ifc, imps: dict, runs: list, limit: int = 60) -> dict:
    out = {}
    for v in MODELS + ['ref']:
        with open(imps[v]) as f:
            text = f.read()
        base = FX.run(fn, ifc, imps[v], runs)
        bcols, _ = FX.trace(fn, ifc, runs, base)
        bchk = {s: SW.check(S, s, bcols) for s in SETS}
        recs = []
        for mu in SW.mutants(text, limit):
            with tempfile.TemporaryDirectory(prefix='fcp_mutfx_') as d:
                p = os.path.join(d, os.path.basename(imps[v]))
                with open(p, 'w') as f:
                    f.write(mu['code'])
                r = FX.run(fn, ifc, p, runs)
            diff = next((i for i in range(len(runs)) if (r[i]['events'], r[i]['code'], r[i]['ret']) !=
                         (base[i]['events'], base[i]['code'], base[i]['ret'])), None)
            rec = {k: mu[k] for k in ('id', 'line', 'desc')}
            rec['observable'] = diff is not None
            if diff is not None:
                cols, _ = FX.trace(fn, ifc, runs, r)
                rec['killed_by'] = {}
                for s in SETS:
                    c = SW.check(S, s, cols)
                    rec['killed_by'][s] = sorted(i for i, x in c.items() if S.mon(s).items[i].role == 'property' and
                                                 (x['first'], x['count']) != (bchk[s][i]['first'], bchk[s][i]['count']))
                rec['example'] = {'call': FX.call_text(fn, ifc, runs, diff),
                                  'original': ' ; '.join(FX.conversation(fn, ifc, runs, base, diff)),
                                  'mutant': ' ; '.join(FX.conversation(fn, ifc, runs, r, diff))}
            recs.append(rec)
        obs = [x for x in recs if x['observable']]
        out[v] = {'mutants': len(recs), 'observable': len(obs),
                  'killed': {s: sum(1 for x in obs if x['killed_by'][s]) for s in SETS},
                  'survivors': {s: [x for x in obs if not x['killed_by'][s]] for s in SETS}}
    return out


def report(res: dict):
    print('== 1. The prompt, before any code')
    for s, x in res['prompt'].items():
        b = x['boundary']
        print(f'[{s}] trigger situations consistent: {x["trigger_situations"]["consistent"]}; '
              f'conflicts on scripts: {len(b["conflicts"])} ({b["checked"]} checked, {b["seconds"]}s)')
        for c in b['conflicts']:
            print(f'    {" + ".join(c["reqs"])}:  {c["stimulus"][0]}')
    for key, rows in res['readings'].items():
        shown = {r: x for r, x in rows.items() if x['plain'] not in CD.PLAIN_AGREE or 'context' in x}
        print(f'  {key}: ' + ('equivalent on every requirement (bounded)' if not shown else ''))
        for r, x in shown.items():
            print(f'    {r:10s} {x["plain"]:13s} in context {x.get("context", "-")}')
            for w in ('a_not_b', 'b_not_a'):
                if x.get(w):
                    print(f'        {w}: ' + ' ; '.join(x[w]['lines']))
    print('== 2. Every implementation against every reading (failing requirements)')
    for v, x in res['code'].items():
        fails = {s: sorted(CD.failing(res['code'], v, s)) for s in SETS}
        print(f'  {v:6s} {x["runs"]} runs  ' + '  '.join(f'{s}: {",".join(f) or "-"}' for s, f in fails.items()))
        for iid, y in x['verify']['gold'].items():
            if y['status'] == 'FAIL':
                print(f'      {iid}: {y["call"]}: {" ; ".join(y["conversation"])}  (replay {y["replay"]})')
    print('== 3. Where the AI implementations disagree')
    for sp in res['splits']:
        print(f'  {sp["count"]:6d} runs split {sp["groups"]}: {sp["call"]}')
        for n, a in sp['answers'].items():
            print(f'      {n:6s} {a}')
    print('== 4. The tests each model wrote, against every implementation (tests failing / run)')
    for m, row in res['naive'].items():
        print(f'  {m:6s} ' + ' '.join(f'{v}:{x["failed"]}/{x["failed"] + x["passed"]}' for v, x in row.items()))
    for v, x in res['detection'].items():
        print(f'  {v}: {x["desc"]}; planted {x["planted"]}; FCP {x["fcp_gold"] or "-"}; tests {x["tests"]}')
    print('== 5. Mutants: observable, killed per reading')
    for v, x in res['mutation'].items():
        print(f'  {v:6s} {x["observable"]}/{x["mutants"]} observable; killed ' +
              ' '.join(f'{s}:{k}' for s, k in x['killed'].items()))
        for r in x['survivors']['gold'][:6]:
            e = r['example']
            print(f'      survives gold: {r["desc"]}: {e["call"]}: {e["mutant"]} instead of {e["original"]}')
    a = res['assurance']
    print('== 6. False assurance on the AI implementations (requirement violated under gold, but certified)')
    print(f'  violations {a["violations"]}; naive (own tests pass) certifies {a["naive_false"]}; '
          f'FCP certifies {a["fcp_false"]}; FCP certified {a["fcp_certified"]}/{a["cells"]} cells')
    print('== 7. Proofs beyond the scope (every run: every argument, every script of answers)')
    for v, row in res.get('proofs', {}).items():
        print(f'  {v:6s} ' + '  '.join(f'{s}: ' + (', '.join(f'{r}={x["status"]}' for r, x in p['requirements'].items()
                                                            if x['status'] != 'PROVED') or 'all PROVED')
                                       if p['status'] == 'ok' else f'{s}: {p["status"]}' for s, p in row.items()))


if __name__ == '__main__':
    t0 = time.time()
    ev = pipeline.run(B, SETS, [], analyses=('lint', 'tautology', 'consistency'), log=lambda *a: None)
    S = Session(B, sets=SETS)
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    imps = CD.implementations(fn)
    res = {'prompt': prompt_level(S, fn, ifc, ev)}
    res['readings'] = readings(S, fn, ifc)
    runs = FX.scope(S, fn, ifc)
    res['code'] = code_level(S, fn, ifc, imps, runs)
    res['splits'] = splits(fn, ifc, runs, {m: res['code'][m]['_res'] for m in MODELS})
    for v in res['code']:
        res['code'][v].pop('_res')
    res['naive'] = CD.naive(fn, imps)
    res['detection'] = detection(S, fn, ifc, CD.BUILD.bugs(), imps, runs, res['naive'])
    res['mutation'] = mutation_level(S, fn, ifc, imps, FX.scope(S, fn, ifc, small=True))
    res['assurance'] = CD.assurance(S, res['code'], res['readings'], res['prompt'], res['naive'], imps)
    res['seconds'] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    from fcp import prove as P
    res['proofs'] = {v: {s: P.prove_effects(S, s, fn, ifc, imps[v], runs, FX.run(fn, ifc, imps[v], runs))
                         for s in SETS} for v in MODELS + ['ref']}
    with open(os.path.join(OUT, f'{CORPUS}.json'), 'w') as f:
        json.dump(res, f, indent=1, default=str)
    report(res)
    print(f'total {res["seconds"]}s')
