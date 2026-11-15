"""Compile an FCP formalization set into a synthesizable Verilog monitor.

A monitor observes the design interface and produces, per property P:

  ok_P   1 iff P is not violated at this cycle (assert form; may use
         universally-quantified nondeterminism such as a tracked item)
  okd_P  deterministic form of the same property, safe in *assumption*
         position (nondeterminism is replaced by an explicit model and rigid
         variables are expanded into a conjunction over their range)
  tr_P   the property's trigger fired (used for vacuity / witness covers)

per assumption A: aok_A, and per scenario C: cov_C.  The monitor contains no
assert/assume/cover statements; harnesses decide how each output is used.
That separation is what lets a single compiled semantics serve proofs,
spec-only analyses and simulation replay.
"""
from __future__ import annotations

import itertools
import math
import re
from dataclasses import dataclass, field
from typing import Optional

from .lang import (BOOL, BITS, NUM, SEQ, Builder, FcpError, FcpTypeError, Node, Scope,
                   Sym, Ty, Val, calls, const_eval, depends_on, lookback, parse, seq_len_port, unparse, vconst)

TEMPORAL_FUNCS = {'prev', 'rose', 'fell', 'stable', 'changed', 'once', 'hist', 'since'}
MAX_EXPANSION = 64


def vname(s: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]', '_', s)


prev_depth = lookback


def cases(n: int) -> str:
    """A count for a message: itself, or its order of magnitude."""
    return str(n) if n < 10 ** 12 else f'about 10^{len(str(n)) - 1}'


# ----------------------------------------------------------------------------
# Pattern library
# ----------------------------------------------------------------------------

@dataclass
class PArgs:
    """Arguments of a pattern instance: parsed expressions and integers."""
    exprs: dict[str, Node]
    ints: dict[str, int]
    raw: dict[str, object]


class Pattern:
    name = ''
    params: list[tuple[str, str]] = []      # (name, 'bool' | 'expr' | 'int'); trailing '?' = optional
    nondet = False
    mode = 'operational'
    doc = ''

    def compile(self, g: 'MonitorGen', a: PArgs, sc: Scope) -> tuple[Val, Val]:
        raise NotImplementedError

    def compile_det(self, g: 'MonitorGen', a: PArgs, sc: Scope) -> tuple[Val, Val]:
        return self.compile(g, a, sc)

    def render(self, a: PArgs) -> str:
        raise NotImplementedError

    def formula(self, a: PArgs) -> str:
        raise NotImplementedError


def E(a: PArgs, k: str) -> str:
    return unparse(a.exprs[k])


class Invariant(Pattern):
    name = 'invariant'
    params = [('cond', 'bool')]
    doc = 'cond holds at every operational cycle.'

    def compile(self, g, a, sc):
        return g.b.boolean(a.exprs['cond'], sc, 'invariant condition'), g.b.const(1, BOOL)

    def render(self, a):
        return f'At every cycle outside reset, `{E(a, "cond")}` holds.'

    def formula(self, a):
        return f'G( {E(a, "cond")} )'


class Implies(Pattern):
    name = 'implies'
    params = [('trigger', 'bool'), ('cond', 'bool')]
    doc = 'whenever trigger holds, cond holds in the same cycle.'

    def compile(self, g, a, sc):
        t = g.b.boolean(a.exprs['trigger'], sc, 'trigger')
        c = g.b.boolean(a.exprs['cond'], sc, 'condition')
        return g.b.wire(BOOL, f'!{t.v} || {c.v}'), t

    def render(self, a):
        return f'Whenever `{E(a, "trigger")}` holds, `{E(a, "cond")}` holds in the same cycle.'

    def formula(self, a):
        return f'G( {E(a, "trigger")} -> {E(a, "cond")} )'


class Next(Pattern):
    name = 'next'
    params = [('trigger', 'bool'), ('cond', 'bool')]
    doc = 'whenever trigger holds, cond holds in the next cycle (unless reset intervenes).'

    def compile(self, g, a, sc):
        t = g.arm(g.b.boolean(a.exprs['trigger'], sc, 'trigger'))
        c = g.b.boolean(a.exprs['cond'], sc, 'condition')
        r = g.b.reg(BOOL, g.b.fresh('_nx'), init=0)
        g.b.seq.append(f'    {r} <= {g.b.rst} ? 1\'b0 : {t.v};')
        return g.b.wire(BOOL, f'!{r} || {c.v}'), t

    def render(self, a):
        return f'Whenever `{E(a, "trigger")}` holds, `{E(a, "cond")}` holds in the following cycle.'

    def formula(self, a):
        return f'G( {E(a, "trigger")} -> X {E(a, "cond")} )'


class Within(Pattern):
    name = 'within'
    params = [('trigger', 'bool'), ('cond', 'bool'), ('min', 'int'), ('max', 'int')]
    doc = 'whenever trigger holds at cycle t, cond holds at some cycle in [t+min, t+max].'

    def compile(self, g, a, sc):
        lo, hi = a.ints['min'], a.ints['max']
        if not 0 <= lo <= hi:
            raise FcpError(f'within: need 0 <= min <= max, got min={lo} max={hi}')
        t = g.arm(g.b.boolean(a.exprs['trigger'], sc, 'trigger'))
        c = g.b.boolean(a.exprs['cond'], sc, 'condition')
        ob = [t.v]
        for j in range(1, hi + 1):
            r = g.b.reg(BOOL, g.b.fresh('_ob'), init=0, comment=f'obligation of age {j}')
            prev_age = j - 1
            sat = c.v if prev_age >= lo else "1'b0"
            g.b.seq.append(f'    {r} <= {g.b.rst} ? 1\'b0 : ({ob[prev_age]} && !{sat});')
            ob.append(r)
        return g.b.wire(BOOL, f'!({ob[hi]} && !{c.v})'), t

    def render(self, a):
        lo, hi = a.ints['min'], a.ints['max']
        win = f'within {hi} cycle(s)' if lo == 0 else f'between {lo} and {hi} cycles later'
        if lo == hi:
            win = f'exactly {lo} cycle(s) later' if lo else 'in the same cycle'
            return f'Whenever `{E(a, "trigger")}` holds, `{E(a, "cond")}` holds {win}.'
        return f'Whenever `{E(a, "trigger")}` holds, `{E(a, "cond")}` holds at some cycle {win} (counting the trigger cycle as 0).'

    def formula(self, a):
        return f'G( {E(a, "trigger")} -> F[{a.ints["min"]},{a.ints["max"]}] {E(a, "cond")} )'


class HoldUntil(Pattern):
    name = 'hold_until'
    params = [('trigger', 'bool'), ('hold', 'bool'), ('release', 'bool')]
    doc = ('whenever trigger holds at t, hold holds at every cycle after t up to and including the '
           'first later cycle where release holds (weak: release need not ever occur).')

    def compile(self, g, a, sc):
        t = g.arm(g.b.boolean(a.exprs['trigger'], sc, 'trigger'))
        h = g.b.boolean(a.exprs['hold'], sc, 'hold condition')
        r = g.b.boolean(a.exprs['release'], sc, 'release condition')
        act = g.b.reg(BOOL, g.b.fresh('_hu'), init=0, comment='hold obligation active')
        g.b.seq.append(f'    {act} <= {g.b.rst} ? 1\'b0 : ({t.v} || ({act} && !{r.v}));')
        return g.b.wire(BOOL, f'!{act} || {h.v}'), t

    def render(self, a):
        return (f'Once `{E(a, "trigger")}` holds, `{E(a, "hold")}` must hold in every following cycle '
                f'up to and including the first cycle in which `{E(a, "release")}` holds.')

    def formula(self, a):
        return f'G( {E(a, "trigger")} -> X( {E(a, "hold")} W ({E(a, "hold")} && {E(a, "release")}) ) )'


class BoundedWait(Pattern):
    name = 'bounded_wait'
    params = [('cond', 'bool'), ('max', 'int')]
    doc = 'cond never holds for more than max consecutive cycles.'

    def compile(self, g, a, sc):
        n = a.ints['max']
        if n < 1:
            raise FcpError('bounded_wait: max must be >= 1')
        c = g.arm(g.b.boolean(a.exprs['cond'], sc, 'waiting condition'))
        ty = NUM(0, n)
        cnt = g.b.reg(ty, g.b.fresh('_bw'), init=0, comment='consecutive cycles of cond so far')
        at_max = g.b.wire(BOOL, f'{g.b.as_num(Val(cnt, ty), ty.nbits)} == {vconst(n, ty)}')
        nxt = f"{c.v} ? ({at_max.v} ? {cnt} : {cnt} + {vconst(1, ty)}) : {vconst(0, ty)}"
        g.b.seq.append(f'    {cnt} <= {g.b.rst} ? {vconst(0, ty)} : ({nxt});')
        return g.b.wire(BOOL, f'!({c.v} && {at_max.v})'), c

    def render(self, a):
        return f'`{E(a, "cond")}` never holds for more than {a.ints["max"]} consecutive cycles.'

    def formula(self, a):
        return f'G( !( {E(a, "cond")} for {a.ints["max"] + 1} consecutive cycles ) )'


class AfterReset(Pattern):
    name = 'after_reset'
    params = [('cond', 'bool')]
    mode = 'always'
    doc = 'in every cycle that follows a reset cycle, cond holds (reset values).'

    def compile(self, g, a, sc):
        c = g.b.boolean(a.exprs['cond'], sc, 'reset condition')
        r = g.b.reg(BOOL, g.b.fresh('_ar'), init=0)
        g.b.seq.append(f'    {r} <= {g.b.rst};')
        return g.b.wire(BOOL, f'!{r} || {c.v}'), g.b.wire(BOOL, r)

    def render(self, a):
        return f'In every cycle immediately following a cycle with reset asserted, `{E(a, "cond")}` holds.'

    def formula(self, a):
        return f'G( Y(reset) -> {E(a, "cond")} )'


class InOrder(Pattern):
    """FIFO-style data transport: every accepted item is delivered exactly
    once, unmodified, in acceptance order; nothing is delivered that was not
    accepted; at most `capacity` items are in flight.

    Assert form: one nondeterministically chosen item is tracked (Wolper's
    data-independence argument), which keeps proofs small.  Deterministic
    form: an explicit queue model of `capacity` entries."""
    name = 'inorder'
    params = [('in_fire', 'bool'), ('in_data', 'expr'), ('out_fire', 'bool'), ('out_data', 'expr'),
              ('capacity', 'int'), ('latency', 'int?'), ('peek', 'bool?')]
    nondet = True
    doc = 'in-order, loss-free, duplicate-free, corruption-free transport with bounded capacity.'

    def _common(self, g, a, sc):
        fi = g.arm(g.b.boolean(a.exprs['in_fire'], sc, 'in_fire'))
        fo = g.arm(g.b.boolean(a.exprs['out_fire'], sc, 'out_fire'))
        di = g.b.compile(a.exprs['in_data'], sc)
        do = g.b.compile(a.exprs['out_data'], sc)
        if di.ty.kind == 'num' or do.ty.kind == 'num' or di.ty.nbits != do.ty.nbits:
            raise FcpTypeError(f'inorder: in_data ({di.ty}) and out_data ({do.ty}) must be bit-vectors of equal width')
        cap = a.ints['capacity']
        if cap < 1:
            raise FcpError('inorder: capacity must be >= 1')
        lat = a.ints.get('latency', 0)
        if lat not in (0, 1):
            raise FcpError('inorder: latency must be 0 (data valid with out_fire) or 1 (data valid the cycle after)')
        pk = g.b.boolean(a.exprs['peek'], sc, 'peek') if 'peek' in a.exprs else None
        if pk is not None and lat != 0:
            raise FcpError('inorder: peek requires latency 0')
        self._pk = pk
        return fi, fo, di, do, cap, lat

    def compile(self, g, a, sc):
        b = g.b
        fi, fo, di, do, cap, lat = self._common(g, a, sc)
        oty = NUM(0, cap)
        W = oty.nbits
        occ = b.reg(oty, b.fresh('_io_occ'), comment='items accepted and not yet delivered')
        trk = b.reg(BOOL, b.fresh('_io_trk'), comment='an item is being tracked')
        tdat = b.reg(di.ty, b.fresh('_io_dat'), comment='data of the tracked item')
        ahead = b.reg(oty, b.fresh('_io_ahd'), comment='items ahead of the tracked item')
        choose = g.nondet_port(f'choose', 1)
        occv, ahv = Val(occ, oty), Val(ahead, oty)
        empty = b.wire(BOOL, f'{b.as_num(occv, W)} == {vconst(0, oty)}')
        fullc = b.wire(BOOL, f'{b.as_num(occv, W)} == {vconst(cap, oty)}')
        ah0 = b.wire(BOOL, f'{b.as_num(ahv, W)} == {vconst(0, oty)}')
        spurious = b.wire(BOOL, f'{fo.v} && {empty.v}', comment='delivery with nothing in flight')
        overflow = b.wire(BOOL, f'{fi.v} && !{fo.v} && {fullc.v}', comment='acceptance beyond capacity')
        deliver = b.wire(BOOL, f'{trk} && {fo.v} && {ah0.v}', comment='tracked item delivered now')
        if lat == 0:
            mism = b.wire(BOOL, f'{deliver.v} && ({do.v} != {tdat})')
        else:
            chk = b.reg(BOOL, b.fresh('_io_chk'))
            b.seq.append(f'    {chk} <= {b.rst} ? 1\'b0 : {deliver.v};')
            mism = b.wire(BOOL, f'{chk} && ({do.v} != {tdat})')
        start = b.wire(BOOL, f'!{trk} && {fi.v} && {choose}')
        one = vconst(1, oty)
        b.seq.append(f'    {occ} <= {b.rst} ? {vconst(0, oty)} : ({overflow.v} || {spurious.v}) ? {occ} : '
                     f'{occ} + ({fi.v} ? {one} : {vconst(0, oty)}) - ({fo.v} ? {one} : {vconst(0, oty)});')
        b.seq.append(f'    {trk} <= {b.rst} ? 1\'b0 : {deliver.v} ? 1\'b0 : {start.v} ? 1\'b1 : {trk};')
        b.seq.append(f'    if ({start.v}) {tdat} <= {di.v};')
        b.seq.append(f'    {ahead} <= {start.v} ? ({fo.v} && !{empty.v} ? {occ} - {one} : {occ}) : '
                     f'({trk} && {fo.v} && !{ah0.v}) ? {ahead} - {one} : {ahead};')
        bad = [spurious.v, overflow.v, mism.v]
        if self._pk is not None:
            bad.append(b.wire(BOOL, f'{self._pk.v} && {trk} && {ah0.v} && ({do.v} != {tdat})',
                              comment='head visible while peek').v)
        ok = b.wire(BOOL, '!(' + ' || '.join(bad) + ')')
        return ok, deliver

    def compile_det(self, g, a, sc):
        b = g.b
        fi, fo, di, do, cap, lat = self._common(g, a, sc)
        oty = NUM(0, cap)
        W = oty.nbits
        n = b.reg(oty, b.fresh('_iq_n'), comment='queue model occupancy')
        q = [b.reg(di.ty, b.fresh('_iq_q'), comment=f'queue model entry {i}') for i in range(cap)]
        nv = Val(n, oty)
        empty = b.wire(BOOL, f'{b.as_num(nv, W)} == {vconst(0, oty)}')
        fullc = b.wire(BOOL, f'{b.as_num(nv, W)} == {vconst(cap, oty)}')
        deq = b.wire(BOOL, f'{fo.v} && !{empty.v}')
        spurious = b.wire(BOOL, f'{fo.v} && {empty.v}')
        overflow = b.wire(BOOL, f'{fi.v} && !{fo.v} && {fullc.v}')
        if lat == 0:
            mism = b.wire(BOOL, f'{deq.v} && ({do.v} != {q[0]})')
        else:
            chk = b.reg(BOOL, b.fresh('_iq_chk'))
            exp = b.reg(di.ty, b.fresh('_iq_exp'))
            b.seq.append(f'    {chk} <= {b.rst} ? 1\'b0 : {deq.v};')
            b.seq.append(f'    {exp} <= {q[0]};')
            mism = b.wire(BOOL, f'{chk} && ({do.v} != {exp})')
        one, zero = vconst(1, oty), vconst(0, oty)
        wpos = b.wire(oty, f'{b.as_num(nv, W)} - ({deq.v} ? {one} : {zero})', comment='write position')
        for i in range(cap):
            base = (q[i + 1] if i + 1 < cap else q[i])
            shifted = f'({deq.v} ? {base} : {q[i]})'
            b.seq.append(f'    {q[i]} <= ({fi.v} && !{overflow.v} && {b.as_num(wpos, W)} == {vconst(i, oty)}) ? '
                         f'{di.v} : {shifted};')
        b.seq.append(f'    {n} <= {b.rst} ? {zero} : ({overflow.v} || {spurious.v}) ? {n} : '
                     f'{n} + ({fi.v} ? {one} : {zero}) - ({deq.v} ? {one} : {zero});')
        bad = [spurious.v, overflow.v, mism.v]
        if self._pk is not None:
            bad.append(b.wire(BOOL, f'{self._pk.v} && !{empty.v} && ({do.v} != {q[0]})').v)
        ok = b.wire(BOOL, '!(' + ' || '.join(bad) + ')')
        return ok, deq

    def render(self, a):
        lat = a.ints.get('latency', 0)
        when = 'in the same cycle as' if lat == 0 else 'in the cycle after'
        return (f'Every item accepted (`{E(a, "in_fire")}`, data `{E(a, "in_data")}`) is delivered exactly once, '
                f'unmodified and in acceptance order: on each delivery (`{E(a, "out_fire")}`) the value of '
                f'`{E(a, "out_data")}` {when} the delivery equals the oldest undelivered item. Nothing is delivered '
                f'when no item is in flight, and at most {a.ints["capacity"]} items are ever in flight.' +
                (f' Moreover, whenever `{E(a, "peek")}` holds and an item is in flight, `{E(a, "out_data")}` shows '
                 f'the oldest undelivered item.' if 'peek' in a.exprs else ''))

    def formula(self, a):
        return (f'inorder(in: {E(a, "in_fire")} / {E(a, "in_data")}, out: {E(a, "out_fire")} / {E(a, "out_data")}, '
                f'capacity {a.ints["capacity"]}, latency {a.ints.get("latency", 0)}' +
                (f', peek {E(a, "peek")}' if 'peek' in a.exprs else '') + ')')


PATTERNS: dict[str, Pattern] = {p.name: p for p in
                                [Invariant(), Implies(), Next(), Within(), HoldUntil(), BoundedWait(),
                                 AfterReset(), InOrder()]}


# ----------------------------------------------------------------------------
# Monitor generation
# ----------------------------------------------------------------------------

@dataclass
class Item:
    """A property, assumption or scenario after elaboration."""
    id: str
    role: str                        # property | assumption | scenario
    pattern: str
    args: PArgs
    mode: str
    depth: int
    rigids: list[str]
    tdepth: int = 0                  # history depth of the trigger expression(s)
    req: Optional[str] = None
    source: dict = field(default_factory=dict)
    english: str = ''
    formula: str = ''
    signals: list[str] = field(default_factory=list)
    out: dict = field(default_factory=dict)    # role -> Verilog output port name
    det_available: bool = True
    note: str = ''


@dataclass
class Monitor:
    module: str
    text: str
    ports_in: list[tuple[str, int]]          # interface inputs to the monitor
    rigid_ports: list[tuple[str, int, int, int]]   # (port, width, lo, hi)
    nondet_ports: list[tuple[str, int]]
    outputs: list[str]
    items: dict[str, Item]
    ghosts: dict[str, dict]


class MonitorGen:
    def __init__(self, iface, fset: dict, module: str):
        self.iface = iface
        self.fset = fset
        self.module = module
        self.b = Builder('rst_active')
        self.params = dict(iface.params)
        self.syms: dict[str, Sym] = {}
        self.ghost_cache: dict[tuple[str, str], Val] = {}
        self.ghost_wf: dict[tuple[str, str], str] = {}
        self.ghost_decl: dict[str, dict] = {}
        self.nondet: list[tuple[str, int]] = []
        self.cur_item: Optional[str] = None
        self.cur_arm = 0                 # trigger look-back of the item being compiled (see arm)
        self.outputs: list[str] = []
        self.assigns: list[str] = []
        self.items: dict[str, Item] = {}
        self.b.ghost_hook = self.ghost_val
        self._declare()

    # -- symbols ---------------------------------------------------------------
    def _declare(self):
        for k, v in self.params.items():
            self.syms[k] = Sym(k, 'param', NUM(v, v), value=v)
        seqs = getattr(self.iface, 'seqs', {}) or {}
        hidden = {seq_len_port(n) for n in seqs}          # reached through len()
        for s in self.iface.signals:
            if s.name in hidden:
                continue
            ty = SEQ(BITS(seqs[s.name][0]), seqs[s.name][1]) if s.name in seqs else BITS(s.width)
            self.syms[s.name] = Sym(s.name, 'signal', ty)
        self.syms['rst_active'] = Sym('rst_active', 'signal', BOOL)
        for g in self.fset.get('ghosts', []) or []:
            name = g['name']
            if 'range' in g:
                lo, hi = (const_eval(x, self.params) for x in g['range'])
                ty = NUM(lo, hi)
            else:
                ty = BITS(const_eval(g['width'], self.params))
            self._check_new(name)
            self.syms[name] = Sym(name, 'ghost', ty)
            self.ghost_decl[name] = dict(g, ty=ty, init_v=const_eval(g.get('init', 0), self.params),
                                         next_n=parse(g['next']))
        for r in self.fset.get('rigids', []) or []:
            name = r['name']
            lo, hi = (const_eval(x, self.params) for x in r['range'])
            self._check_new(name)
            self.syms[name] = Sym(name, 'rigid', NUM(lo, hi), value=None)
        for name, body in (self.fset.get('defs', {}) or {}).items():
            self._check_new(name)
            self.syms[name] = Sym(name, 'def', BOOL, node=parse(body))
        for name, g in self.ghost_decl.items():
            used = calls(g['next_n'])
            for d in depends_on(g['next_n'], Scope(self.syms), {'def'}):
                used |= calls(self.syms[d].node)
            if used & TEMPORAL_FUNCS:
                raise FcpError(f'ghost {name}: next-state expression may not use temporal operators '
                               f'({", ".join(sorted(used & TEMPORAL_FUNCS))}); ghosts are already state')

    def _check_new(self, name):
        if name in self.syms:
            raise FcpError(f'name {name!r} declared twice (signal/param/ghost/rigid/def names must be unique)')
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name):
            raise FcpError(f'invalid identifier {name!r}')

    def scope(self) -> Scope:
        return Scope(self.syms)

    def nondet_port(self, what: str, width: int) -> str:
        p = f'nd_{vname(self.cur_item)}_{what}'
        self.nondet.append((p, width))
        return p

    # -- ghosts ----------------------------------------------------------------
    def ghost_deps(self, name: str, kind: str) -> set:
        """Names of one kind (rigid, signal) the state of a ghost depends on:
        through its update, the definitions it uses and the ghosts it reads."""
        sc, seen, todo, out = Scope(self.syms), set(), [name], set()
        while todo:
            g = todo.pop()
            if g not in seen:
                seen.add(g)
                nx = self.ghost_decl[g]['next_n']
                out |= depends_on(nx, sc, {kind})
                todo += sorted(depends_on(nx, sc, {'ghost'}))
        return out

    def ghost_val(self, name: str, sc: Scope) -> Val:
        g = self.ghost_decl[name]
        deps = self.ghost_deps(name, 'rigid')
        relevant = {k: v for k, v in sc.bind.items() if k in deps}
        key = (name, ','.join(f'{k}={v}' for k, v in sorted(relevant.items())))
        if key in self.ghost_cache:
            return self.ghost_cache[key]
        ty = g['ty']
        suffix = ('_' + '_'.join(f'{k}{v}'.replace('-', 'm')         # k = -1: g_x_km1, a legal name
                                 for k, v in sorted(relevant.items()))) if relevant else ''
        r = self.b.reg(ty, f'g_{name}{suffix}', comment=f'ghost {name}')
        val = Val(r, ty)
        self.ghost_cache[key] = val
        nx = self.b.compile(g['next_n'], sc.with_binding(relevant) if relevant else Scope(self.syms))
        if nx.ty.kind == 'num' or ty.kind == 'num':
            w = max(nx.ty.nbits if nx.ty.kind == 'num' else nx.ty.nbits + 1, ty.nbits)
            nxv = self.b.as_num(nx, w)
            inr = self.b.wire(BOOL, f'({nxv} >= {self.b.as_num(self.b.const(ty.lo), w)}) && '
                                    f'({nxv} <= {self.b.as_num(self.b.const(ty.hi), w)})',
                              comment=f'ghost {name} update stays in its declared range')
            assign = f'{nxv}'
        else:
            if nx.ty.nbits > ty.nbits:
                raise FcpTypeError(f'ghost {name}: next value is wider ({nx.ty}) than the ghost ({ty})')
            inr = self.b.const(1, BOOL)
            assign = self.b.as_bits(nx, ty.nbits)
        init = vconst(g['init_v'], ty)
        if ty.kind == 'num':
            wide = self.b.wire(NUM(min(ty.lo, nx.ty.lo), max(ty.hi, nx.ty.hi)) if nx.ty.kind == 'num' else ty,
                               assign) if assign != r else Val(r, ty)
            sl = f'{wide.v}[{ty.nbits - 1}:0]' if wide.ty.nbits > ty.nbits else wide.v
            self.b.seq.append(f'    {r} <= rst_active ? {init} : {sl};')
        else:
            self.b.seq.append(f'    {r} <= rst_active ? {init} : {assign};')
        self.ghost_wf[key] = self.b.wire(BOOL, f'rst_active || {inr.v}').v
        return val

    def ghost_wf_for(self, n_list: list[Node], sc: Scope) -> list[str]:
        names = set()
        for n in n_list:
            names |= depends_on(n, sc, {'ghost'})
        # ghosts referenced by other ghosts' next-state functions
        frontier = list(names)
        while frontier:
            g = frontier.pop()
            for h in depends_on(self.ghost_decl[g]['next_n'], sc, {'ghost'}):
                if h not in names:
                    names.add(h)
                    frontier.append(h)
        out = []
        for (gname, key), wf in self.ghost_wf.items():
            if gname in names:
                out.append(wf)
        return out

    # -- items ---------------------------------------------------------------
    def _args(self, spec: dict, pat: Pattern) -> PArgs:
        args = spec.get('args', {}) or {}
        exprs, ints, raw = {}, {}, {}
        known = set()
        for pname, kind in pat.params:
            optional = kind.endswith('?')
            kind = kind.rstrip('?')
            known.add(pname)
            if pname not in args:
                if optional:
                    continue
                raise FcpError(f'{spec["id"]}: pattern {pat.name} requires argument {pname!r}')
            raw[pname] = args[pname]
            if kind == 'int':
                ints[pname] = const_eval(args[pname], self.params)
            else:
                exprs[pname] = parse(str(args[pname]))
        extra = set(args) - known
        if extra:
            raise FcpError(f'{spec["id"]}: unknown argument(s) {sorted(extra)} for pattern {pat.name}')
        return PArgs(exprs, ints, raw)

    def elaborate(self, spec: dict, role: str) -> Item:
        iid = spec['id']
        if 'expr' in spec:
            pat = PATTERNS['invariant']
            pargs = PArgs({'cond': parse(str(spec['expr']))}, {}, {'cond': spec['expr']})
        elif role == 'scenario':
            pat = PATTERNS['invariant']
            pargs = PArgs({'cond': parse(str(spec['cover']))}, {}, {'cond': spec['cover']})
        elif role == 'dontcare':
            pat = PATTERNS['invariant']
            pargs = PArgs({'cond': parse(str(spec['when']))}, {}, {'cond': spec['when']})
            if spec['signal'] not in {s.name for s in self.iface.outputs}:
                raise FcpError(f'{iid}: dont_care names {spec["signal"]!r}, which is not an interface output')
        else:
            pname = spec.get('pattern')
            if pname not in PATTERNS:
                raise FcpError(f'{iid}: unknown pattern {pname!r} (available: {", ".join(PATTERNS)})')
            pat = PATTERNS[pname]
            pargs = self._args(spec, pat)
        mode = spec.get('mode', pat.mode)
        if mode not in ('operational', 'always'):
            raise FcpError(f'{iid}: mode must be operational or always')
        sc = self.scope()
        depth = max([prev_depth(n, self.syms) for n in pargs.exprs.values()], default=0)
        rig = set()
        sigs = set()
        for n in pargs.exprs.values():
            rig |= depends_on(n, sc, {'rigid'})
            sigs |= depends_on(n, sc, {'signal'})
            for gname in depends_on(n, sc, {'ghost'}):
                rig |= self.ghost_deps(gname, 'rigid')
                sigs |= self.ghost_deps(gname, 'signal')
        tkeys = {'implies': ['trigger'], 'next': ['trigger'], 'within': ['trigger'], 'hold_until': ['trigger'],
                 'bounded_wait': ['cond'], 'inorder': ['in_fire', 'out_fire']}.get(pat.name, [])
        tdepth = max([prev_depth(pargs.exprs[k], self.syms) for k in tkeys if k in pargs.exprs], default=0)
        it = Item(id=iid, role=role, pattern=pat.name, args=pargs, mode=mode, depth=depth,
                  rigids=sorted(rig), tdepth=tdepth, req=spec.get('req'), source=spec.get('source', {}) or {},
                  signals=sorted(sigs - {'rst_active'}))
        if role == 'dontcare':
            it.note = spec['signal']
        if role == 'dontcare':
            it.english = f'`{spec["signal"]}` is intentionally unconstrained whenever `{unparse(pargs.exprs["cond"])}` holds.'
            it.formula = f'dont_care({spec["signal"]}) when {unparse(pargs.exprs["cond"])}'
            it.signals = [spec['signal']]
        elif role != 'scenario':
            it.english = pat.render(pargs)
            it.formula = pat.formula(pargs)
            if mode == 'always' and pat.mode != 'always':
                it.english = it.english.replace('At every cycle outside reset', 'At every cycle, including reset cycles,') \
                    if pat.name == 'invariant' else it.english + ' (Checked in every cycle, including reset cycles.)'
        else:
            it.english = f'It is possible to reach a cycle (outside reset) in which `{unparse(pargs.exprs["cond"])}` holds.'
            it.formula = f'EF( {unparse(pargs.exprs["cond"])} )'
        return it

    def arm(self, v: Val) -> Val:
        """A trigger that looks back n cycles is undefined in the first n
        cycles after a reset (IR_spec 4.2), so it cannot start an obligation
        there.  Patterns that latch their trigger into state (next, within,
        hold_until, bounded_wait, inorder) pass it through here; without this, a
        prev() in the trigger could arm an obligation from a reset cycle that the
        verdict gating (_gate) no longer masks."""
        d = self.cur_arm
        return v if not d else self.b.wire(BOOL, f'(_seg >= {d}) && {v.v}')

    def _gate(self, raw: Val, it: Item) -> str:
        """Apply reset / history-validity gating to a raw per-cycle verdict."""
        terms = []
        if it.mode == 'operational':
            terms.append('rst_active')
            if it.depth:
                terms.append(f'(_seg < {it.depth})')
        elif it.depth:
            terms.append(f'(_cyc < {it.depth})')
        return ' || '.join(terms + [raw.v]) if terms else raw.v

    def _gate_trig(self, trig: Val, it: Item) -> str:
        d = it.tdepth if it.role == 'property' else it.depth
        if it.mode == 'operational':
            g = f'!rst_active'
            if d:
                g += f' && (_seg >= {d})'
            return f'{g} && {trig.v}'
        return trig.v if not d else f'(_cyc >= {d}) && {trig.v}'

    def _out(self, port: str, expr: str):
        self.outputs.append(port)
        self.assigns.append(f'  assign {port} = {expr};')

    def _rigid_cases(self, it: Item) -> int:
        """How many bindings the rigid variables of an item have.  Counted, not
        listed: thirty-two rigids of sixteen bits have about 10^154 of them."""
        return math.prod(self.syms[r].ty.hi - self.syms[r].ty.lo + 1 for r in it.rigids)

    def _rigid_bindings(self, it: Item):
        """The bindings themselves: for an item with at most MAX_EXPANSION cases."""
        ranges = []
        for r in it.rigids:
            t = self.syms[r].ty
            ranges.append([(r, v) for v in range(t.lo, t.hi + 1)])
        return list(itertools.product(*ranges)) if ranges else [()]

    def add(self, spec: dict, role: str) -> Item:
        it = self.elaborate(spec, role)
        if it.id in self.items:
            raise FcpError(f'duplicate id {it.id}')
        self.cur_item = it.id
        self.cur_arm = it.tdepth if it.mode == 'operational' else 0
        pat = PATTERNS[it.pattern]
        sc = self.scope()
        vid = vname(it.id)
        exprs = list(it.args.exprs.values())
        if role == 'scenario':
            c = self.b.boolean(it.args.exprs['cond'], sc, 'scenario')
            self._out(f'cov_{vid}', self._gate_trig(c, it))
            it.out['cov'] = f'cov_{vid}'
        elif role == 'dontcare':
            c = self.b.boolean(it.args.exprs['cond'], sc, 'dont-care condition')
            self._out(f'dc_{vid}', f'rst_active || ({c.v})')
            it.out['dc'] = f'dc_{vid}'
        elif role == 'assumption':
            if pat.nondet:
                raise FcpError(f'{it.id}: pattern {pat.name} is nondeterministic and cannot be an assumption')
            parts = []
            if self._rigid_cases(it) > MAX_EXPANSION:
                raise FcpError(f'{it.id}: assumption over rigid variables expands to '
                               f'{cases(self._rigid_cases(it))} cases')
            for combo in self._rigid_bindings(it):
                s2 = sc.with_binding(dict(combo)) if combo else sc
                ok, _ = pat.compile_det(self, it.args, s2)
                parts.append(self._gate(ok, it))
            wf = self.ghost_wf_for(exprs, sc)
            self._out(f'aok_{vid}', ' && '.join(f'({p})' for p in parts + wf))
            it.out['aok'] = f'aok_{vid}'
        else:
            ok, trig = pat.compile(self, it.args, sc)
            wf = self.ghost_wf_for(exprs, sc)
            okx = self._gate(ok, it)
            self._out(f'ok_{vid}', ' && '.join([f'({okx})'] + wf))
            self._out(f'tr_{vid}', self._gate_trig(trig, it))
            it.out['ok'] = f'ok_{vid}'
            it.out['tr'] = f'tr_{vid}'
            # deterministic form for assumption position
            if not pat.nondet and not it.rigids:
                it.out['okd'] = it.out['ok']
            elif self._rigid_cases(it) > MAX_EXPANSION:
                it.det_available = False
                it.note = f'deterministic form unavailable ({cases(self._rigid_cases(it))} rigid cases)'
            else:
                parts = []
                for combo in self._rigid_bindings(it):
                    s2 = sc.with_binding(dict(combo)) if combo else sc
                    okd, _ = pat.compile_det(self, it.args, s2)
                    parts.append(self._gate(okd, it))
                wf2 = self.ghost_wf_for(exprs, sc)
                self._out(f'okd_{vid}', ' && '.join([f'({p})' for p in parts] + wf2))
                it.out['okd'] = f'okd_{vid}'
        self.items[it.id] = it
        self.cur_item = None
        self.cur_arm = 0
        return it

    # -- assembly ------------------------------------------------------------
    def build(self) -> Monitor:
        fs = self.fset
        for a in fs.get('assumptions', []) or []:
            self.add(a, 'assumption')
        for p in fs.get('properties', []) or []:
            self.add(p, 'property')
        for c in fs.get('scenarios', []) or []:
            self.add(c, 'scenario')
        for d in fs.get('dont_cares', []) or []:
            self.add(d, 'dontcare')
        return self.emit()

    def emit(self) -> Monitor:
        iface = self.iface
        rst = iface.reset
        maxd = max([it.depth for it in self.items.values()] + [1])
        cw = max(2, (maxd + 1).bit_length() + 1)
        ports = ['input clk']
        ports_in = []
        for s in iface.signals:
            if s.name == iface.clock:
                continue
            ports.append(f'input {vdecl_bits(s.width)}{s.name}')
            ports_in.append((s.name, s.width))
        rigid_ports = []
        for name, sym in self.syms.items():
            if sym.kind == 'rigid':
                w = sym.ty.nbits
                ports.append(f'input signed [{w - 1}:0] rg_{name}')
                rigid_ports.append((f'rg_{name}', w, sym.ty.lo, sym.ty.hi))
        for p, w in self.nondet:
            ports.append(f'input {vdecl_bits(w)}{p}')
        for o in self.outputs:
            ports.append(f'output {o}')
        lines = [f'// Generated by FCP from formalization set "{self.fset.get("set", "?")}". Do not edit.',
                 f'module {self.module} (', '  ' + ',\n  '.join(ports), ');']
        pol = '!' if rst.active_low else ''
        lines.append(f'  wire rst_active = {pol}{rst.name};')
        lines.append(f'  reg [{cw - 1}:0] _cyc = 0;  // cycles since start of trace (saturating)')
        lines.append(f'  reg [{cw - 1}:0] _seg = 0;  // cycles since end of last reset (saturating)')
        lines += self.b.decls
        lines.append('  always @(posedge clk) begin')
        lines.append(f'    if (_cyc != {cw}\'d{maxd + 1}) _cyc <= _cyc + 1\'b1;')
        lines.append(f'    _seg <= rst_active ? {cw}\'d0 : (_seg == {cw}\'d{maxd + 1}) ? _seg : _seg + 1\'b1;')
        lines += self.b.seq
        lines.append('  end')
        lines += self.assigns
        lines.append('endmodule')
        return Monitor(self.module, '\n'.join(lines) + '\n', ports_in, rigid_ports, list(self.nondet),
                       list(self.outputs), self.items, self.ghost_decl)


def vdecl_bits(w: int) -> str:
    return f'[{w - 1}:0] ' if w > 1 else ''


def build_monitor(iface, fset: dict, module: str) -> Monitor:
    try:
        return MonitorGen(iface, fset, module).build()
    except RecursionError:
        raise FcpError('the formulas nest too deeply to compile: a definition that names itself, directly '
                       'or through others, or a chain of thousands of definitions') from None
