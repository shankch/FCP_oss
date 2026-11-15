"""Agents as chips: the model is a cut point and the scaffold is the RTL.

The design declares a `cutpoint`: the inputs that carry the model's proposed
tool call, and, for each output, the value it takes when the scaffold runs
the proposal unchanged (`passes`).  The ordinary analyses already treat the
proposal as a free input, so a proof holds for every possible model output,
including one produced under prompt injection.  This module adds

  contract(S, s)       every property of a reading restated over the proposal:
                       what the model itself would have to do for the
                       requirement to hold through a pass-through scaffold
  trust(S, s, vs)      per requirement and scaffold variant:
                         enforced   proved with the proposal free
                         delegated  fails, but is proved when the model keeps
                                    that requirement's contract: only a model
                                    that breaks the rule can break it
                         broken     fails even then: the scaffold breaks the
                                    requirement by itself
  conversation(...)    a trace rendered turn by turn (proposal, what ran)
"""
from __future__ import annotations

import dataclasses
import os
from typing import Optional

import yaml

from .ir import load_fset
from .lang import Node, parse, unparse

TEMPORAL = {'prev', 'rose', 'fell', 'stable', 'changed', 'once', 'hist', 'since'}
# pattern arguments that are evaluated in the turn whose proposal they constrain;
# a `next`/`within` trigger lies in the past of its condition and stays as it ran
LIFT = {'implies': ('trigger', 'cond'), 'invariant': ('cond',), 'next': ('cond',), 'after_reset': ('cond',),
        'within': ('cond',), 'bounded_wait': ('cond',), 'hold_until': ('hold', 'release')}


def cutpoint(S) -> dict:
    cp = S.b.raw_design.get('cutpoint')
    if not cp:
        raise KeyError(f'{S.b.design}: design.yaml declares no cutpoint')
    return cp


def _subst(n: Node, m: dict, defs: dict) -> Node:
    if n.op == 'ref':
        if n.val in m:
            return m[n.val]
        if n.val in defs:
            return _subst(defs[n.val], m, defs)
        return n
    if n.op == 'call' and n.val in TEMPORAL:
        return n        # the past is what ran, not what is proposed
    if not n.args:
        return n
    return dataclasses.replace(n, args=tuple(_subst(a, m, defs) for a in n.args))


def lift(src: str, passes: dict, defs: dict) -> str:
    m = {k: parse(f'({v})') for k, v in passes.items()}
    d = {k: parse(f'({v})') for k, v in defs.items()}
    return unparse(_subst(parse(src), m, d))


def contract(S, s: str) -> tuple[list[dict], list[str]]:
    """The contract items of reading s (assumptions on the cut point), and the
    ids of properties that could not be restated."""
    cp = cutpoint(S)
    fs = S.b.fsets[s]
    defs = {k: str(v) for k, v in (fs.get('defs') or {}).items()}
    items, skipped = [], []
    for it in fs.get('properties') or []:
        if it['id'] in S.b.frame_ids:
            continue
        c = {'id': f'C-{it["id"]}', 'req': it['req'], 'note': f'{it["id"]} restated over the proposal'}
        if 'expr' in it:
            c['expr'] = lift(str(it['expr']), cp['passes'], defs)
        elif it.get('pattern') in LIFT:
            args = dict(it.get('args') or {})
            for k in LIFT[it['pattern']]:
                if k in args:
                    args[k] = lift(str(args[k]), cp['passes'], defs)
            c['pattern'], c['args'] = it['pattern'], args
        else:
            skipped.append(it['id'])
            continue
        if it.get('mode'):
            c['mode'] = it['mode']
        items.append(c)
    return items, skipped


def contract_set(S, s: str, dest_dir: Optional[str] = None) -> str:
    """Write reading s plus its contract as a formalization set and attach it to
    the session's bundle under the name '<s>+c'.  Returns that name."""
    items, _ = contract(S, s)
    fs = S.b.fsets[s]
    out = {'fcp': '0.1', 'set': f'{s}+c', 'origin': {'kind': 'tool', 'role': 'contract', 'id': f'fcp.agent.contract({s})'}}
    for k in ('defs', 'ghosts', 'rigids'):
        if fs.get(k):
            out[k] = fs[k]
    if fs.get('assumptions'):
        out['assumptions'] = list(fs['assumptions'])
    # contract items are compiled as properties so that they share the reading's
    # rigid registers; trust() assumes their per-value form (see there)
    out['properties'] = [it for it in fs.get('properties') or [] if it['id'] not in S.b.frame_ids] + items
    for k in ('dont_cares', 'unformalized'):
        if fs.get(k):
            out[k] = fs[k]
    dest_dir = dest_dir or S.b.path('contracts')
    os.makedirs(dest_dir, exist_ok=True)
    p = os.path.join(dest_dir, f'{s}.yaml')
    with open(p, 'w') as f:
        yaml.safe_dump(out, f, sort_keys=False, width=200)
    return load_fset(S.b, p, f'{s}+c')


def trust(S, s: str, variants: list[str]) -> dict:
    """Classify every requirement of reading s on every scaffold variant."""
    cname = f'{s}+c' if f'{s}+c' in S.b.fsets else contract_set(S, s)
    env = S.assumptions(cname)
    contract_items, by_req = {}, {}
    for it in S.props(cname):
        (contract_items if it.id.startswith('C-') else by_req).setdefault(it.req, []).append(it)
    tasks, keys = [], {}
    for v in variants:
        rv = S.variant(v)
        for req, props in by_req.items():
            for it in props:
                for mode in ('free', 'contract'):
                    if mode == 'contract' and (it.id in S.b.frame_ids or req not in contract_items):
                        continue
                    hb = S.rtl_hb(cname, rv, with_assumptions=False)
                    for a in env:
                        hb.assumes.append(f"mon_{a.out['aok']}")
                    # the contract is assumed at the rigid values of the property being
                    # checked: C(b) => R(b) for every b implies (all a. C(a)) => (all b. R(b)),
                    # so a proof is sound; only a 'broken' verdict may be pessimistic when
                    # R(b) would need C at other values
                    for c in (contract_items[req] if mode == 'contract' else []):
                        hb.assumes.append(f"mon_{c.out['ok']}")
                    hb.asserts.append(f"mon_{it.out['ok']}")
                    k = f'trust:{mode}:{v}:{it.id}'
                    keys[(mode, v, it.id)] = k
                    tasks.append(S.task(k, 'prove', hb, [cname], rv, engine='pdr'))
    R = S.run(tasks)
    out = {}
    for v in variants:
        row = {}
        for req, props in by_req.items():
            free = {it.id: R[keys[('free', v, it.id)]] for it in props}
            if all(r.status == 'PASS' for r in free.values()):
                row[req] = {'class': 'enforced'}
                continue
            fail = next(p for p, r in free.items() if r.status != 'PASS')
            rec = {'free_fail': fail, 'free_trace': free[fail].trace}
            if any(it.id in S.b.frame_ids for it in props) or req not in contract_items:
                rec['class'] = 'broken'
            else:
                con = {it.id: R[keys[('contract', v, it.id)]] for it in props}
                bad = [p for p, r in con.items() if r.status != 'PASS']
                rec['class'] = 'broken' if bad else 'delegated'
                if bad:
                    rec['contract_fail'] = bad[0]
                    rec['contract_trace'] = con[bad[0]].trace
            if any(r.status not in ('PASS', 'FAIL') for r in free.values()):
                rec['class'] = 'unknown'
            row[req] = rec
        out[v] = row
    return out


def conversation(S, trace: list, proposals: bool = True, upto: Optional[int] = None,
                 outputs: bool = True) -> list[str]:
    """One line per turn: what the model proposed (if proposals), what ran (if
    outputs) and the results that mean something for it (cutpoint.show).
    upto: last cycle to render.  outputs=False renders a stimulus: the
    proposal and the environment's inputs only."""
    cp = S.b.raw_design.get('cutpoint') or {}
    dec, show = cp.get('decode', {}), cp.get('show', {})
    acts = cp.get('actions') or [x.name for x in S.b.iface.outputs if x.width == 1]
    ins = cp.get('inputs', [])
    code = next((n for n in ins if n in dec), None)
    rst = S.b.iface.reset

    def call(name, st, sigs):
        args = [f'{n}={st.get(n)}' for n in sigs if name in show.get(n, []) and st.get(n) is not None]
        return f'{name}({", ".join(args)})' if args else name

    lines = []
    for k, st in enumerate(trace):
        if upto is not None and k > upto:
            break
        if str(st.get(rst.name)) == ('0' if rst.active_low else '1'):
            continue
        ran = next((a for a in acts if st.get(a)), None)
        outs = [x.name for x in S.b.iface.outputs if x.name not in acts]
        res = [x.name for x in S.b.iface.inputs if x.name not in ins and x.name != rst.name]
        what = call(ran, st, outs) if ran else 'nothing'
        extra = [f'{n}={st.get(n)}' for n in res if ran in show.get(n, []) and st.get(n) is not None]
        extra += [f'{n}=1' for n in res if n not in show and st.get(n)]
        line = f'turn {k}: '
        if not outputs:
            v = st.get(code) or 0 if code else 0
            pname = dec[code][v] if code and v < len(dec[code]) else str(v)
            env = [f'{n}=1' for n in res if n not in show and st.get(n)]
            lines.append(line + (f'model proposes {call(pname, st, [n for n in ins if n != code])}' if proposals else '')
                         + (f' [{", ".join(env)}]' if env else ''))
            continue
        if proposals and code is not None and (st.get(code) or 0):
            v = st.get(code)
            pname = dec[code][v] if v < len(dec[code]) else str(v)
            line += f'model proposes {call(pname, st, [n for n in ins if n != code])}, '
            line += f'{what} runs' if ran else 'nothing runs'
        else:
            line += what
        lines.append(line + (f' [{", ".join(extra)}]' if extra else ''))
    return lines
