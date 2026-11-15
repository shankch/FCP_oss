"""An agent checked as a chip: run FCP on corpus/agent_desk.

  1. Compile the scaffold kernels to RTL (corpus/agent_desk/build.py) and check
     every translation by co-simulation against the Python kernel.
  2. Prompt-level analyses of every reading, before any scaffold or model run:
     consistency, forcing stimuli (conflicts the customer can force on any
     agent), tautology, and the readings compared in context with the
     simplest distinguishing conversation (fewest tool calls).
  3. Every reading on every scaffold with the model's proposal free (verify,
     vacuity, triage), and the trust classification of every requirement:
     enforced, delegated to the model, or broken by the scaffold.
  4. Real model runs (runs/<model>_<scenario>): the model's proposals checked
     against every reading's contract, and what ran checked against every
     reading.
  5. The counterexamples on the pass-through scaffold, replayed through the
     Python kernels that the agent runs: what each scaffold executes.

Writes results/agent_desk.json and results/agent_desk_evidence.json.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
B = os.path.join(ROOT, 'corpus', 'agent_desk')
OUT = os.path.join(HERE, 'results')
sys.path.insert(0, ROOT)
sys.path.insert(0, B)

import build as BUILD  # noqa: E402
import runtime as RT  # noqa: E402
from fcp import agent as AG, kernel as K, pipeline, rv  # noqa: E402
from fcp.analyses import Session  # noqa: E402

SETS = ['gold', 'agent_a', 'agent_b']
ACTIONS = ['say', 'verify', 'lookup', 'confirm', 'refund', 'handoff', 'close']
ANALYSES = ('lint', 'tautology', 'consistency', 'verify', 'vacuity', 'triage', 'compare')
PLAIN_AGREE = {'EQUIVALENT', 'ONLY-A', 'ONLY-B'}


def frame_reqs(S) -> set:
    return {r.id for r in S.b.requirements.values() if r.doc == 'FRAME'}


def prompt_level(S, ev: dict) -> dict:
    out = {}
    for s in SETS:
        c = ev['sets'][s].get('consistency', {})
        f = S.forcing(s)
        out[s] = {'consistent': c.get('consistent'),
                  'conflicts': [{'reqs': x['reqs'], 'core': x['mus']} for x in c.get('conflicts', [])],
                  'forcing': [{'reqs': x['reqs'], 'core': x['core'], 'stimulus': x['stimulus'],
                               'conversation': AG.conversation(S, x['stimulus'], outputs=False)} for x in f['conflicts']],
                  'forcing_seconds': f['seconds'],
                  'tautologies': [k for k, v in ev['sets'][s].get('tautology', {}).items() if v.get('tautology')]}
    return out


def contextual(S, ev: dict) -> dict:
    out = {}
    fr = frame_reqs(S)
    for key, rows in ev['compare'].items():
        a, b = key.split('|')
        disputed = {r for r, x in rows.items() if r != '<assumptions>' and r not in fr
                    and x['relation'] not in PLAIN_AGREE}
        rec = {r: {'plain': x['relation']} for r, x in rows.items() if r != '<assumptions>' and r not in fr}
        if disputed:
            for r, x in S.compare(a, b, context=True, only=disputed, economy=ACTIONS).items():
                rec[r]['context'] = x['relation']
                for w, rej in (('witness_a_not_b', b), ('witness_b_not_a', a)):
                    if x.get(w):
                        # cut the witness at the turn where the rejecting reading fails
                        res = rv.check(S, rej, x[w])
                        k = min((c for i, c in res.items() if c is not None and S.mon(rej).items[i].req == r),
                                default=None)
                        # the model's proposal is shown only if a reading of r mentions it
                        cut = set(AG.cutpoint(S)['inputs'])
                        uses = any(cut & set(it.signals) for st_ in (a, b) for it in S.props(st_) if it.req == r)
                        rec[r][w] = AG.conversation(S, x[w], proposals=uses, upto=k)
        out[key] = rec
    return out


def runs(S) -> dict:
    out = {}
    for d in sorted(glob.glob(os.path.join(B, 'runs', '*', ''))):
        name = os.path.basename(d.rstrip('/'))
        tr = RT.trace(d)
        recs = RT.turns(d)
        row = {'turns': len(recs), 'blocked': [r['turn'] for r in recs if r['ran'] == 'nothing' and r['proposed'] != 'none'],
               'overridden': [r['turn'] for r in recs if r['ran'] not in ('nothing', r['proposed'])],
               'proposed': [r['proposed'] + ('' if r['ran'] == r['proposed'] else f'->{r["ran"]}') for r in recs],
               'readings': {}}
        for s in SETS:
            res = rv.check(S, f'{s}+c', tr)
            row['readings'][s] = {
                'model_broke': {i[2:]: k for i, k in res.items() if i.startswith('C-') and k is not None},
                'ran_violates': {i: k for i, k in res.items() if not i.startswith('C-') and k is not None}}
        out[name] = row
    return out


def replay_attacks(S, ev: dict) -> dict:
    """Counterexamples of gold on the pass-through scaffold are attacks: input
    sequences (model proposals, customer, tools) that break a rule.  Replay
    their inputs through the Python kernels and check what ran."""
    pre = ['p_act', 'p_ord', 'p_amt', 'p_more', 'human']
    post = ['id_ok', 'elig', 'total', 'accepted']
    mods = {v: K.load(os.path.join(B, f)) for v, f in RT.KERNELS.items()}
    out = {}
    for pid, r in ev['sets']['gold']['rtl']['naive']['verify'].items():
        if r['status'] != 'FAILED' or not r.get('trace'):
            continue
        rec = {}
        for v, mod in mods.items():
            rt = K.Runtime(mod)
            tr = [{'rst_n': 0}]
            for st in r['trace']:
                if str(st.get('rst_n')) == '0':
                    continue
                p = {k: int(st.get(k) or 0) for k in pre}
                q = {k: int(st.get(k) or 0) for k in post}
                tr.append({'rst_n': 1, **p, **q, **rt.turn(p, q)})
            res = rv.check(S, 'gold', tr)
            rec[v] = {'violated': sorted(i for i, k in res.items() if k is not None and not i.startswith('F-')),
                      'conversation': AG.conversation(S, tr)}
            if v == 'naive':   # the Python kernel must reproduce the solver's trace of the RTL
                rec['naive_matches_rtl'] = all(
                    all(int(a.get(o) or 0) == int(b.get(o) or 0) for o in ACTIONS + ['ord', 'amt', 'more', 'done'])
                    for a, b in zip([x for x in r['trace'] if str(x.get('rst_n')) != '0'], tr[1:]))
        out[pid] = rec
    return out


def report(res: dict):
    print('== 1. Scaffolds compiled from Python and co-simulated')
    for v, c in res['cosim'].items():
        print(f'  {v:6s} agree on {c["turns"]} random turns' if c['agree'] else f'  {v}: DISAGREE')
    print('== 2. The prompt, before any scaffold or model')
    for s, x in res['prompt'].items():
        print(f'[{s}] consistent: {x["consistent"]}; forcing conflicts: {len(x["forcing"])}')
        for c in x['forcing']:
            print(f'    {" + ".join(c["reqs"])}:  ' + ' | '.join(c['conversation']))
    for key, rows in res['context'].items():
        a, b = key.split('|')
        print(f'  {a} vs {b}:')
        for r, x in rows.items():
            if x['plain'] in PLAIN_AGREE and 'context' not in x:
                continue
            print(f'    {r:9s} {x["plain"]:13s} in context {x.get("context", "-")}')
            for w, lab in (('witness_a_not_b', f'{a} accepts, {b} rejects'), ('witness_b_not_a', f'{b} accepts, {a} rejects')):
                if x.get(w):
                    print(f'        {lab}: ' + ' | '.join(x[w]))
    print('== 3. Trust: E enforced (any model), D delegated (only if the model obeys), B broken (even then)')
    for s, T in res['trust'].items():
        reqs = [r for r in next(iter(T.values())) if not r.startswith('R-FR')]
        print(f'[{s}]        ' + ' '.join(f'{r[2:]:>7s}' for r in reqs) + '   frame')
        for v, row in T.items():
            fr = 'ok' if all(row[r]['class'] == 'enforced' for r in row if r.startswith('R-FR')) else 'BROKEN'
            print(f'  {v:6s}    ' + ' '.join(f'{row[r]["class"][0].upper():>7s}' for r in reqs) + f'   {fr}')
    print('== 4. Real models through the guarded scaffold')
    for name, x in res['runs'].items():
        broke = {s: sorted(y['model_broke']) for s, y in x['readings'].items()}
        ran = {s: sorted(y['ran_violates']) for s, y in x['readings'].items() if y['ran_violates']}
        print(f'  {name:15s} {" ".join(x["proposed"])}')
        print(f'      model broke contract: {broke}' + (f'   ran violates: {ran}' if ran else ''))
    print('== 5. Attacks found on the pass-through scaffold, replayed through the Python kernels')
    for pid, x in res['attacks'].items():
        print(f'  {pid:7s} naive violates {x["naive"]["violated"]}, ref violates {x["ref"]["violated"] or "nothing"}'
              f'  (python = rtl trace: {x["naive_matches_rtl"]})')
        print(f'      attack: ' + ' | '.join(x['naive']['conversation']))


if __name__ == '__main__':
    t0 = time.time()
    res = {'cosim': BUILD.build()}
    S0 = Session(B)
    variants = ['ref', 'naive'] + sorted(S0.bugs())
    ev = pipeline.run(B, SETS, variants, analyses=ANALYSES, log=lambda *a: None)
    os.makedirs(OUT, exist_ok=True)
    pipeline.save(ev, os.path.join(OUT, 'agent_desk_evidence.json'))
    S = Session(B, sets=SETS)
    res['prompt'] = prompt_level(S, ev)
    res['context'] = contextual(S, ev)
    res['trust'] = {s: AG.trust(S, s, variants) for s in SETS}
    for T in res['trust'].values():
        for row in T.values():
            for x in row.values():
                for k in ('free_trace', 'contract_trace'):
                    if x.get(k):
                        x[k.replace('trace', 'conversation')] = AG.conversation(S, x.pop(k))
    res['verify'] = {s: {v: {p: r['status'] for p, r in ev['sets'][s]['rtl'][v]['verify'].items()} for v in variants}
                     for s in SETS}
    res['runs'] = runs(S)
    res['attacks'] = replay_attacks(S, ev)
    res['seconds'] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, 'agent_desk.json'), 'w') as f:
        json.dump(res, f, indent=1, default=str)
    report(res)
    print(f'total {res["seconds"]}s')
