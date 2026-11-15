"""Code written by AI models, checked with FCP: run on a code corpus
(corpus/code_checkout by default; `code_demo.py code_mask` for the string task).

  1. The prompt alone, before any code exists: for every reading, conflicts at
     the prompt's own boundaries (pairs of calls no implementation can
     answer), the outputs it leaves open with the simplest call that shows
     each, and the readings compared in context, every disagreement shown as
     the simplest calls that separate them.
  2. Every implementation (three AI models, the reference, eight planted bugs)
     run on the scope and checked against every reading; every failure is
     replayed in a fresh process.
  3. Where the AI implementations disagree with each other, and what every
     implementation does at each question (the answer key).
  4. The naive baseline: the tests each model wrote for its own code, run
     against every implementation.
  5. Mutants of every AI implementation and of the reference: behaviour no
     requirement notices.
  6. False assurance: requirements an implementation breaks under the gold
     reading that the naive flow or FCP would certify.

Writes results/<corpus>.json and results/<corpus>_evidence.json.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORPUS = sys.argv[1] if len(sys.argv) > 1 else 'code_checkout'
B = os.path.join(ROOT, 'corpus', CORPUS)
OUT = os.environ.get('FCP_OUT') or os.path.join(HERE, 'results')
sys.path.insert(0, ROOT)
sys.path.insert(0, B)

import build as BUILD  # noqa: E402
from fcp import pipeline, rv, software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402

SETS = ['gold', 'agent_a', 'agent_b']
PEERS = ['agent_a', 'agent_b']
MODELS = ['haiku', 'sonnet', 'opus']
ANALYSES = ('lint', 'tautology', 'consistency', 'determinacy')
PLAIN_AGREE = {'EQUIVALENT', 'ONLY-A', 'ONLY-B'}
T0 = time.time()


def note(what: str):
    """Progress on stderr (the report itself is printed at the end)."""
    print(f'[{time.time() - T0:8.0f}s] {what}', file=sys.stderr, flush=True)


def implementations(fn) -> dict:
    if '.' in fn.module:                    # a package: the directory that holds it
        out = {m: os.path.join(B, 'agents', f'coder_{m}') for m in MODELS}
        out['ref'] = os.path.join(B, 'impl', 'ref')
    else:
        out = {m: os.path.join(B, 'agents', f'coder_{m}', f'{fn.module}.py') for m in MODELS}
        out['ref'] = os.path.join(B, 'impl', 'ref.py')
    out.update(BUILD.materialize())
    return out


def checked_reqs(S) -> list[str]:
    return [r.id for r in S.b.requirements.values() if r.kind in ('guarantee', 'scenario') and r.doc != 'FRAME']


# ----------------------------------------------------------------------------
# 1. the prompt alone
# ----------------------------------------------------------------------------

def prompt_level(S, fn, ev: dict) -> dict:
    out = {}
    for s in SETS:
        rec = ev['sets'][s]
        det = rec.get('determinacy', {})
        opened = [k for k, x in det.items() if not x.get('determined', True)]
        if fn.stateful:
            # determinacy assumes only properties with an assumable form; for an
            # object, every output is asked about after the request sequences
            opened = fn.rets + [fn.outcome]
        cons = rec.get('consistency', {})
        out[s] = {'trigger_situations': {'consistent': cons.get('consistent'),
                                         'conflicts': [x['reqs'] for x in cons.get('conflicts', [])]},
                  'scenarios_never': {'impossible': cons.get('impossible_scenarios', []),
                                      'forbidden': cons.get('forbidden_scenarios', [])},
                  'boundary': SW.conflicts(S, s, fn),
                  'determined': {k: x.get('determined') for k, x in det.items()},
                  'open': SW.choices(S, s, fn, opened),
                  'tautologies': [k for k, v in rec.get('tautology', {}).items() if v.get('tautology')]}
    return out


def trace_calls(S, fn, tr: list) -> tuple[list, list]:
    """The calls of a spec-only witness trace (its last sequence of calls
    between resets; resets after it only pad the trace) and the outputs the
    witness gives them."""
    rst, low = S.b.iface.reset.name, S.b.iface.reset.active_low
    segs = [([], [])]
    for st in tr:
        if int(st.get(rst) or 0) == (0 if low else 1):
            if segs[-1][0]:
                segs.append(([], []))
            continue
        get = lambda p: int(st.get(p) or 0)  # noqa: E731
        segs[-1][0].append(tuple(fn.decode(sig, get) for _, sig, _ in fn.args))
        segs[-1][1].append({x: fn.decode(x, get) for x in fn.rets + [fn.outcome]})
    calls, outs = next((sg for sg in reversed(segs) if sg[0]), ([], []))
    return calls, outs


def object_readings(S, fn) -> dict:
    """readings() for an object: the chip engine's comparison of contracts,
    plain and in context (a rigid range too large to expand is assumed at
    pinned values); every witness is a sequence of calls.  PDR timed out on
    these readings (ghost clocks of 17 bits and a rigid customer), so the
    comparison is bounded: no disagreement in the first bmc_depth - lookahead
    cycles of a run (one is reported `lookahead` cycles after it happens)."""
    S.cmp_engine = 'bmc'
    out = {}
    for i, a in enumerate(SETS):
        for b in SETS[i + 1:]:
            plain = S.compare(a, b)
            rec = {r: {'plain': x['relation'], 'bounded': x.get('depth')} for r, x in plain.items()
                   if r != '<assumptions>'}
            for r, x in rec.items():
                if x['plain'] == 'UNKNOWN':        # the proof engine left it open: scope evidence
                    x['plain_scope_check'] = SW.object_separation(S, fn, a, b, r, False)
            disputed = {r for r, x in rec.items() if x['plain'] not in PLAIN_AGREE}
            if disputed:
                for r, x in S.compare(a, b, context=True, only=disputed).items():
                    if r not in rec:
                        continue
                    rec[r]['context'] = x['relation']
                    for w in ('a_not_b', 'b_not_a'):
                        if x.get(f'witness_{w}'):
                            calls, outs = trace_calls(S, fn, x[f'witness_{w}'])
                            rec[r][w] = {'calls': [list(c) for c in calls],
                                         'lines': [SW.line(fn, c, o) for c, o in zip(calls, outs)], 'sequence': True}
                    if x['relation'] == 'UNKNOWN':
                        sc = SW.object_separation(S, fn, a, b, r, True)
                        rec[r]['context_scope_check'] = {'calls': sc['calls'], 'separated': any(
                            k in sc for k in ('a_not_b', 'b_not_a'))}
                        for w in ('a_not_b', 'b_not_a'):
                            if sc.get(w) and not rec[r].get(w):
                                rec[r][w] = sc[w]
            out[f'{a}|{b}'] = rec
    return out


def readings(S, fn) -> dict:
    """Every pair of readings compared per requirement, plain and in context
    (fcp.software.compare: decided on k calls), every disagreement in context
    shown as the simplest calls that separate the readings, and every
    agreement in context spot-checked on the bit-level monitor model."""
    if fn.stateful:
        return object_readings(S, fn)
    out = {}
    for i, a in enumerate(SETS):
        for b in SETS[i + 1:]:
            spec = SW._Spec(S, [a, b], fn, 2)
            plain = SW.compare(S, a, b, fn, spec=spec)
            rec = {r: {'plain': x['relation'], 'k': x['k'], 'exact': x['exact']} for r, x in plain.items()}
            for r, x in plain.items():
                if x.get('scope_check'):
                    rec[r]['plain_scope_check'] = x['scope_check']
            disputed = {r for r, x in plain.items() if x['relation'] not in PLAIN_AGREE}
            for r, x in SW.compare(S, a, b, fn, context=True, only=disputed, spec=spec).items():
                rec[r]['context'] = x['relation']
                if x.get('scope_check'):
                    rec[r]['context_scope_check'] = x['scope_check']
                for w, acc, rej in (('a_not_b', a, b), ('b_not_a', b, a)):
                    if x.get(f'witness_{w}'):
                        rec[r][w] = SW.separating(S, spec, fn, acc, rej, r) or x[f'witness_{w}']
                if x['relation'] == 'EQUIVALENT':
                    rec[r]['spot_check'] = {'calls': 400, 'separated': SW.spot_check(S, spec, fn, a, b, r) +
                                            SW.spot_check(S, spec, fn, b, a, r)}
            out[f'{a}|{b}'] = rec
    return out


# ----------------------------------------------------------------------------
# 2. every implementation against every reading
# ----------------------------------------------------------------------------

def code_level(S, fn, imps: dict) -> dict:
    # the scope first, in this thread: drawing it may use z3, which is not thread-safe
    scopes = {}
    for name in imps:
        scopes[name] = SW.calls_for(S, fn, [imps[name]])
        note(f'scope of {name}: {len(scopes[name])} calls')

    def one(name):
        src = imps[name]
        calls = scopes[name]
        res = SW.run(fn, src, calls)
        cols = SW.trace(fn, calls, res)
        return name, {'calls': len(calls), 'outcomes': SW.outcome_summary(fn, res),
                      'verify': {s: SW.verify(S, s, fn, src, calls, res, cols) for s in SETS}}
    with ThreadPoolExecutor(max_workers=6) as ex:
        return dict(ex.map(one, imps))


def failing(code: dict, v: str, s: str) -> dict:
    """Requirement -> failing items of reading s on implementation v."""
    out: dict[str, list] = {}
    for iid, x in code[v]['verify'][s].items():
        if x['status'] in ('FAIL', 'NOT-COVERED') and x['req'] and not iid.startswith('F-'):
            out.setdefault(x['req'], []).append(iid)
    return out


# ----------------------------------------------------------------------------
# 3. where the implementations disagree, and the answer key
# ----------------------------------------------------------------------------

def accepted(S, fn, src: str, calls: list[tuple]) -> tuple[list[str], dict]:
    """One implementation on a few calls (for an object, one sequence on a new
    object): its answers, and per reading the properties those answers break."""
    lead = [None] if fn.stateful else []
    res = SW.run(fn, src, lead + list(calls))
    cols = SW.trace(fn, lead + list(calls), res)
    tr = [SW.cycle(cols, k) for k in range(len(lead) + len(calls) + 1)]
    broken = {}
    for s in SETS:
        r = rv.check(S, s, tr)
        broken[s] = sorted(i for i, k in r.items() if k is not None and not i.startswith('F-'))
    return [SW.result_text(fn, res, i + len(lead), calls[i]) for i in range(len(calls))], broken


def answer_key(S, fn, imps: dict, prompt: dict, reads: dict, splits: list) -> list[dict]:
    qs = []
    g = prompt['gold']
    if g['boundary']['conflicts']:
        c = g['boundary']['conflicts'][0]
        qs.append({'kind': 'conflict', 'about': c['reqs'], 'calls': [tuple(x) for x in c['calls']]})
    for sig, x in g['open']['open'].items():
        cs = [tuple(c) for c in x['args']] if x.get('sequence') else [tuple(x['args'])]
        qs.append({'kind': 'open', 'about': [sig], 'calls': cs, 'allowed': x['values']})
    for key, rows in reads.items():
        for r, x in rows.items():
            for w in ('a_not_b', 'b_not_a'):
                if x.get(w) and x[w].get('calls'):
                    qs.append({'kind': 'readings', 'about': [r, key], 'calls': [tuple(c) for c in x[w]['calls']]})
    for sp in splits:
        cs = [tuple(c) for c in sp['args']] if sp.get('sequence') else [tuple(sp['args'])]
        qs.append({'kind': 'code split', 'about': sp['groups'], 'calls': cs, 'count': sp['count']})
    for q in qs:
        q['answers'] = {}
        for v in MODELS + ['ref']:
            ans, broken = accepted(S, fn, imps[v], q['calls'])
            q['answers'][v] = {'answers': ans, 'broken': broken}
        q['calls'] = [SW.call_text(fn, c) for c in q['calls']]
    return qs


# ----------------------------------------------------------------------------
# 4. the naive baseline, 5. mutants
# ----------------------------------------------------------------------------

def naive(fn, imps: dict) -> dict:
    jobs = [(m, v) for m in MODELS for v in imps]

    def one(mv):
        m, v = mv
        return mv, SW.run_tests(os.path.join(B, 'agents', f'coder_{m}', f'test_{fn.module.split(".")[0]}.py'), imps[v],
                                fn.module, support=os.path.join(B, 'support'))
    with ThreadPoolExecutor(max_workers=12) as ex:
        res = dict(ex.map(one, jobs))
    return {m: {v: res[(m, v)] for v in imps} for m in MODELS}


def mutation_level(S, fn, imps: dict) -> dict:
    out = {}
    for v in MODELS + ['ref']:
        calls = SW.calls_for(S, fn, [imps[v]], small=True)
        out[v] = SW.mutation(S, SETS, fn, imps[v], calls, limit=60, jobs=24)
        note(f'mutants of {v}')
    return out


# ----------------------------------------------------------------------------
# 6. false assurance
# ----------------------------------------------------------------------------

def assurance(S, code: dict, reads: dict, prompt: dict, tests: dict, imps: dict) -> dict:
    """Per AI implementation and requirement: is it violated (a gold item
    fails), and would the naive flow (the model's own tests pass) or FCP
    certify it?  FCP certifies a requirement only if it passes under both
    agent readings within the scope, the two agent readings agree on it, it
    is in no conflict of either agent reading, and the decomposer did not
    flag its text as ambiguous (that stays a question, whatever the readers
    chose).  Gold is never a peer."""
    rel = reads.get('agent_a|agent_b', {})
    ambiguous = {r.id for r in S.b.requirements.values() if getattr(r, 'ambiguity', None)}

    def agree(r):
        x = rel.get(r, {})
        return x.get('context', x.get('plain')) in PLAIN_AGREE

    conflicted = set()
    for s in PEERS:
        for c in prompt[s]['boundary']['conflicts']:
            conflicted |= set(c['reqs'])
        for c in prompt[s]['trigger_situations']['conflicts']:
            conflicted |= set(c)
    out = {}
    for v in MODELS:
        rows = {}
        gfail = failing(code, v, 'gold')
        for r in checked_reqs(S):
            peer_items = {s: [x for x in code[v]['verify'][s].values() if x['req'] == r] for s in PEERS}
            peer_ok = all(items and all(x['status'] in ('PASS', 'COVERED') for x in items)
                          for items in peer_items.values())
            fcp = peer_ok and agree(r) and r not in conflicted and r not in ambiguous
            why = [w for w, bad in (('fails under an agent reading', not peer_ok),
                                    ('agent readings disagree', not agree(r)),
                                    ('in a conflict', r in conflicted),
                                    ('its text is flagged ambiguous', r in ambiguous)) if bad]
            rows[r] = {'violated': r in gfail, 'naive': tests[v][v]['ok'], 'fcp': fcp, 'fcp_why_not': why}
        out[v] = rows
    viol = [(v, r) for v, rows in out.items() for r, x in rows.items() if x['violated']]
    return {'rows': out, 'violations': len(viol),
            'naive_false': sum(out[v][r]['naive'] for v, r in viol),
            'fcp_false': sum(out[v][r]['fcp'] for v, r in viol),
            'fcp_certified': sum(x['fcp'] for rows in out.values() for x in rows.values()),
            'cells': sum(len(rows) for rows in out.values())}


def detection(S, fn, code: dict, tests: dict, bugs: list[dict], imps: dict) -> dict:
    """Planted bugs: does FCP (gold) see the change, and does each model's
    test suite fail a test that passes on the reference?  FCP sees a bug if,
    on the reference's own calls, some gold property fails on a different
    number of calls (or first fails elsewhere) than on the reference, so a
    bug inside a requirement that the prompt's own conflict already breaks
    is still seen."""
    calls = SW.calls_for(S, fn, [imps['ref']])
    gm = S.mon('gold')

    def verdicts(src):
        res = SW.run(fn, src, calls)
        chk = SW.check(S, 'gold', SW.trace(fn, calls, res))
        return {i: (x['first'], x['count']) for i, x in chk.items() if gm.items[i].role in ('property', 'scenario')}
    ref_v = verdicts(imps['ref'])
    out = {}
    for b in bugs:
        v = b['id']
        bv = verdicts(imps[v])
        new = sorted({gm.items[i].req for i in bv if bv[i] != ref_v[i] and gm.items[i].req and not i.startswith('F-')})
        suites = {m: sorted(set(tests[m][v]['failing']) - set(tests[m]['ref']['failing'])) for m in MODELS}
        out[v] = {'desc': b['desc'], 'planted': b.get('violates', []), 'fcp_gold': new,
                  'fcp_by_reading': {s: sorted(failing(code, v, s)) for s in SETS},
                  'tests': {m: len(x) for m, x in suites.items()}}
    return out


# ----------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------

def report(res: dict):
    print('== 1. The prompt, before any code')
    for s, x in res['prompt'].items():
        b = x['boundary']
        print(f'[{s}] trigger situations consistent: {x["trigger_situations"]["consistent"]}; '
              f'boundary conflicts: {len(b["conflicts"])} ({b["checked"]} pairs, {b["seconds"]}s); '
              f'tautologies: {x["tautologies"] or "none"}')
        for c in b['conflicts']:
            print(f'    {" + ".join(c["reqs"])}:  ' + ' | '.join(c['stimulus']))
        for sig, o in x['open']['open'].items():
            print(f'    open: {sig} on {o["call"]}: {o["values"][0]} or {o["values"][1]}')
        sn = x.get('scenarios_never') or {}
        for k, why in (('impossible', 'its cover is impossible'), ('forbidden', 'the reading forbids it')):
            for sc in sn.get(k, []):
                print(f'    scenario {sc} can never happen: {why}')
    for key, rows in res['readings'].items():
        a, b = key.split('|')
        shown = {r: x for r, x in rows.items() if x['plain'] not in PLAIN_AGREE or 'context' in x}
        print(f'  {a} vs {b}: ' + ('equivalent on every requirement' if not shown else ''))
        for r, x in shown.items():
            print(f'    {r:10s} {x["plain"]:13s} in context {x.get("context", "-")}')
            for w, lab in (('a_not_b', f'{a} accepts, {b} rejects'), ('b_not_a', f'{b} accepts, {a} rejects')):
                if x.get(w):
                    print(f'        {lab}: ' + ' | '.join(x[w]['lines']))
    print('== 2. Every implementation against every reading (failing requirements)')
    for v, x in res['code'].items():
        fails = {s: sorted(failing(res['code'], v, s)) for s in SETS}
        print(f'  {v:6s} {x["calls"]} calls  ' + '  '.join(f'{s}: {",".join(f) or "-"}' for s, f in fails.items()))
        for iid, y in x['verify']['gold'].items():
            if y['status'] == 'FAIL':
                print(f'      {iid}: ' + ' | '.join(f'{c["call"]} -> {c["got"]}' for c in y['calls_shown']) +
                      f'  ({y["count"]} failing calls, replay {y["replay"]})')
    print('== 3. Where the AI implementations disagree')
    for sp in res['splits']:
        print(f'  {sp["count"]:6d} calls split {sp["groups"]}: {sp["call"]} -> {sp["answers"]}')
    print('   answer key')
    for q in res['answer_key']:
        print(f'  [{q["kind"]}] {q["about"]}: {" | ".join(q["calls"])}')
        for v, a in q['answers'].items():
            print(f'      {v:6s} {" | ".join(a["answers"])}   broken: {a["broken"]}')
    print('== 4. The tests each model wrote, against every implementation (tests failing / run)')
    for m, row in res['naive'].items():
        print(f'  {m:6s} ' + ' '.join(f'{v}:{x["failed"]}/{x["failed"] + x["passed"]}' for v, x in row.items()))
    print('   planted bugs: requirements FCP flags (gold), and tests of each model that fail beyond the reference')
    for v, x in res['detection'].items():
        print(f'  {v}: {x["desc"]}; planted {x["planted"]}; FCP {x["fcp_gold"] or "-"}; tests {x["tests"]}')
    print('== 5. Mutants: observable, killed per reading, survivors')
    for v, x in res['mutation'].items():
        print(f'  {v:6s} {x["observable"]}/{x["mutants"]} observable; killed ' +
              ' '.join(f'{s}:{k}' for s, k in x['killed'].items()))
        for s in ('gold',):
            for r in x['survivors'][s][:6]:
                e = r['example']
                print(f'      survives {s}: {r["desc"]}: {e["call"]} -> {e["mutant"]} instead of {e["original"]}')
    a = res['assurance']
    print('== 6. False assurance on the AI implementations (requirement violated under gold, but certified)')
    print(f'  violations {a["violations"]}; naive (own tests pass) certifies {a["naive_false"]}; '
          f'FCP certifies {a["fcp_false"]}; FCP certified {a["fcp_certified"]}/{a["cells"]} cells')


if __name__ == '__main__':
    import faulthandler
    faulthandler.dump_traceback_later(3600, repeat=True)     # where a long stage spends its time, hourly
    t0 = time.time()
    ev = pipeline.run(B, SETS, [], analyses=ANALYSES, log=lambda *a: None)
    os.makedirs(OUT, exist_ok=True)
    pipeline.save(ev, os.path.join(OUT, f'{CORPUS}_evidence.json'))
    note('analyses of the readings')
    S = Session(B, sets=SETS)
    fn = SW.function(S)
    imps = implementations(fn)
    res = {'prompt': prompt_level(S, fn, ev)}
    note('the prompt alone')
    res['readings'] = readings(S, fn)
    note('readings compared')
    res['code'] = code_level(S, fn, imps)
    note('every implementation against every reading')
    ai = [imps[m] for m in MODELS]
    calls = SW.calls_for(S, fn, ai)
    runs = {m: SW.run(fn, imps[m], calls) for m in MODELS}
    res['splits'] = SW.disagreements(fn, calls, runs)
    note('disagreements')
    res['answer_key'] = answer_key(S, fn, imps, res['prompt'], res['readings'], res['splits'])
    note('answer key')
    res['naive'] = naive(fn, imps)
    note("the models' own tests")
    res['detection'] = detection(S, fn, res['code'], res['naive'], BUILD.bugs(), imps)
    note('planted bugs')
    res['mutation'] = mutation_level(S, fn, imps)
    note('mutants')
    res['assurance'] = assurance(S, res['code'], res['readings'], res['prompt'], res['naive'], imps)
    note('false assurance')
    res['seconds'] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, f'{CORPUS}.json'), 'w') as f:
        json.dump(res, f, indent=1, default=str)
    report(res)
    print(f'total {res["seconds"]}s')
