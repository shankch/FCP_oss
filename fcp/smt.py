"""Direct SMT reasoning (z3) over the yosys SMT2 model of a flattened harness.

Used for analyses that need more than reachability:

  receptiveness   is there a reachable state in which *no* (non-reset) input
                  satisfies the environment assumptions?  Such an assumption
                  prunes behaviours of the design itself and can mask bugs.
                  Exists-forall query solved by counterexample-guided
                  refinement (CEGAR) over input vectors.
  triage          on the exact inputs of a counterexample, does *any*
                  specification-conforming output trace exist?  If yes, the
                  RTL is at fault and MaxSAT finds the closest conforming
                  behaviour (a minimal diff that localises the bug); if no,
                  the requirements themselves conflict on that stimulus and an
                  unsat core names them.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional

import z3

from .engine import run_yosys
from .harness import ENV_OK


def _bv(v: int, w: int) -> str:
    return f'#b{v & ((1 << w) - 1):0{w}b}'


class TranslationFailed(RuntimeError):
    """yosys did not turn a model into SMT2: it ran out of time, or it failed."""


_FAILED: dict[str, str] = {}                  # a model that did not translate is not tried again in this process


class SmtModel:
    """A flattened design exported by ``write_smt2 -wires``.  A model that
    does not translate raises TranslationFailed, at once when it is asked for
    again: every search over a reading would otherwise wait for the same
    translation to run out of time."""

    def __init__(self, gen: dict[str, str], srcs: list[str], top: str):
        self.top = top
        key = hashlib.sha256(repr((sorted(gen.items()), list(srcs), top)).encode()).hexdigest()
        if key in _FAILED:
            raise TranslationFailed(_FAILED[key])
        with tempfile.TemporaryDirectory(prefix='fcp_smt_') as d:
            names = []
            for k, v in gen.items():
                with open(os.path.join(d, k), 'w') as f:
                    f.write(v)
                names.append(k)
            for s in srcs:
                shutil.copy(s, d)
                names.append(os.path.basename(s))
            script = '; '.join([
                'read -formal ' + ' '.join(names), f'prep -top {top}', 'flatten', 'memory_map',
                'async2sync', 'chformal -remove', 'formalff -setundef -clk2ff -ff2anyinit',
                'setundef -undriven -anyseq', 'opt_clean', 'dffunmap', 'write_smt2 -wires model.smt2'])
            try:
                run_yosys(script, d)
            except subprocess.TimeoutExpired as e:
                _FAILED[key] = f'the translation of the monitors for the solver (yosys) did not end in {e.timeout:g} s'
                raise TranslationFailed(_FAILED[key]) from None
            except RuntimeError as e:
                last = [x for x in str(e).split('\n') if x.strip()][-1:]
                _FAILED[key] = 'the translation of the monitors for the solver (yosys) failed' + \
                    (f': {last[0].strip()[:200]}' if last else '')
                raise TranslationFailed(_FAILED[key]) from e
            with open(os.path.join(d, 'model.smt2')) as f:
                self.text = f.read()
        self.state_vars: dict[str, str] = {}      # function name -> sort
        self.inputs: dict[str, int] = {}          # input wire name -> width
        self.free_funcs: set[str] = set()         # per-step free functions (inputs, anyseq)
        self.wires: dict[str, int] = {}
        by_name: dict[str, str] = {}
        input_names = []
        for line in self.text.split('\n'):
            m = re.match(r'\(declare-fun \|(' + re.escape(top) + r'#\d+)\| \(\|' + re.escape(top) +
                         r'_s\|\) (.+?)\)(?: ; \\?(\S+))?$', line)
            if m:
                self.state_vars[m.group(1)] = m.group(2)
                if m.group(3):
                    by_name[m.group(3)] = m.group(1)
                continue
            # input annotations are not adjacent to their declarations in
            # flattened models: associate them by signal name
            m = re.match(r'; yosys-smt2-input (\S+) (\d+)', line)
            if m:
                self.inputs[m.group(1)] = int(m.group(2))
                input_names.append(m.group(1))
                continue
            m = re.match(r'; yosys-smt2-anyseq (\S+) ', line)
            if m:
                self.free_funcs.add(m.group(1))
                continue
            m = re.match(r'; yosys-smt2-wire (\S+) (\d+)', line)
            if m:
                self.wires[m.group(1)] = int(m.group(2))
        for n in input_names:
            # an input may be one state variable or a concatenation of several
            # (when its bits are used separately): take every variable its
            # accessor refers to
            found = set()
            if n in by_name:
                found.add(by_name[n])
            m = re.search(r'^\(define-fun \|' + re.escape(top) + r'_n ' + re.escape(n) + r'\| .*$',
                          self.text, re.M)
            if m:
                found |= set(re.findall(r'\|(' + re.escape(top) + r'#\d+)\|', m.group(0)))
            if not found:
                raise RuntimeError(f'cannot locate the SMT state variable of input {n}')
            self.free_funcs |= found
        self.has_h = f'(define-fun |{top}_h|' in self.text
        # the harness' own condition on its free signals: asserted at every step of every unrolling
        self.env_ok = self.has(ENV_OK)

    # -- term helpers --------------------------------------------------------
    def sig(self, name: str, st: str) -> str:
        return f'(|{self.top}_n {name}| {st})'

    def has(self, name: str) -> bool:
        """Signals optimized away by yosys (e.g. an unused rigid) have no accessor."""
        return f'(define-fun |{self.top}_n {name}| ' in self.text

    def is_true(self, name: str, st: str) -> str:
        w = self.wires.get(name, 1)
        t = self.sig(name, st)
        return t if w == 1 else f'(distinct {t} {_bv(0, w)})'

    def equals(self, name: str, st: str, v: int) -> str:
        w = self.wires.get(name, self.inputs.get(name, 1))
        t = self.sig(name, st)
        if w == 1:
            return t if v else f'(not {t})'
        return f'(= {t} {_bv(v, w)})'

    def unroll(self, k: int, prefix: str = 's') -> list[str]:
        out = [f'(declare-fun {prefix}{i} () |{self.top}_s|)' for i in range(k + 1)]
        out.append(f'(assert (|{self.top}_is| {prefix}0))')
        out.append(f'(assert (|{self.top}_i| {prefix}0))')
        for i in range(k + 1):
            if self.has_h:
                out.append(f'(assert (|{self.top}_h| {prefix}{i}))')
            if self.env_ok:
                out.append(f'(assert {self.is_true(ENV_OK, f"{prefix}{i}")})')
            if i:
                out.append(f'(assert (not (|{self.top}_is| {prefix}{i})))')
                out.append(f'(assert (|{self.top}_t| {prefix}{i - 1} {prefix}{i}))')
        return out

    def regs_equal(self, a: str, b: str) -> list[str]:
        return [f'(assert (= (|{f}| {a}) (|{f}| {b})))' for f in self.state_vars if f not in self.free_funcs]

    def solver(self, lines: list[str], opt: bool = False):
        s = z3.Optimize() if opt else z3.Solver()
        s.from_string(self.text + '\n' + '\n'.join(lines))
        return s


def _model_values(model, prefix: str) -> dict[str, int]:
    out = {}
    for d in model.decls():
        n = d.name()
        if n.startswith(prefix):
            v = model[d]
            out[n[len(prefix):]] = (1 if z3.is_true(v) else 0) if z3.is_bool(v) else v.as_long()
    return out


# ----------------------------------------------------------------------------
# Receptiveness of environment assumptions
# ----------------------------------------------------------------------------

def receptiveness(model: SmtModel, aok: list[str], rst_name: str, rst_active_low: bool,
                  rigid: list[tuple[str, int, int, int]], depth: int, max_iter: int = 60) -> dict:
    """Search, for k = 0..depth, for a state reachable under the assumptions in
    which no non-reset input satisfies them.  Returns the first blocking trace."""
    if not aok:
        return {'receptive': True, 'depth': depth, 'note': 'no assumptions'}
    rst_on = (lambda st: model.equals(rst_name, st, 0 if rst_active_low else 1))
    rst_off = (lambda st: model.equals(rst_name, st, 1 if rst_active_low else 0))
    all_ok = (lambda st: '(and ' + ' '.join(model.is_true(a, st) for a in aok) + ')')
    sigs_to_read = sorted(model.inputs)
    stats = {'iterations': 0}
    for k in range(1, depth + 1):
        cands: list[dict[str, int]] = []
        for _ in range(max_iter):
            stats['iterations'] += 1
            L = model.unroll(k)
            L.append(f'(assert {rst_on("s0")})')
            for reg, w, lo, hi in rigid:
                if not model.has(reg):
                    continue
                t = model.sig(reg, 's0')
                L.append(f'(assert (and (bvsge {t} {_bv(lo, w)}) (bvsle {t} {_bv(hi, w)})))')
            for i in range(k):
                L.append(f'(assert {all_ok(f"s{i}")})')
            for j, c in enumerate(cands):
                x = f'x{j}'
                L.append(f'(declare-fun {x} () |{model.top}_s|)')
                if model.has_h:
                    L.append(f'(assert (|{model.top}_h| {x}))')
                L.append(f'(assert (not (|{model.top}_is| {x})))')
                L += model.regs_equal(f's{k}', x)
                for n, v in c.items():
                    L.append(f'(assert {model.equals(n, x, v)})')
                L.append(f'(assert (not {all_ok(x)}))')
            # read back the register state and the trace
            for f in model.state_vars:
                if f not in model.free_funcs:
                    srt = model.state_vars[f]
                    L.append(f'(declare-fun r_{f.replace("#", "_")} () {srt})')
                    L.append(f'(assert (= r_{f.replace("#", "_")} (|{f}| s{k})))')
            for i in range(k + 1):
                for n in sigs_to_read:
                    w = model.inputs[n]
                    srt = 'Bool' if w == 1 else f'(_ BitVec {w})'
                    L.append(f'(declare-fun t_{i}_{n} () {srt})')
                    L.append(f'(assert (= t_{i}_{n} {model.sig(n, f"s{i}")}))')
            s1 = model.solver(L)
            if s1.check() != z3.sat:
                break               # no candidate blocking state at this depth
            m1 = s1.model()
            regs = {}
            for f in model.state_vars:
                if f not in model.free_funcs:
                    v = m1.eval(z3.Const(f'r_{f.replace("#", "_")}', _sort(model.state_vars[f])), model_completion=True)
                    regs[f] = (1 if z3.is_true(v) else 0) if z3.is_bool(v) else v.as_long()
            # is that state really blocking?
            L2 = [f'(declare-fun y () |{model.top}_s|)', f'(assert (not (|{model.top}_is| y)))']
            if model.has_h:
                L2.append(f'(assert (|{model.top}_h| y))')
            for f, v in regs.items():
                srt = model.state_vars[f]
                lit = ('true' if v else 'false') if srt == 'Bool' else _bv(v, int(re.search(r'(\d+)\)$', srt).group(1)))
                L2.append(f'(assert (= (|{f}| y) {lit}))')
            L2.append(f'(assert {rst_off("y")})')
            L2.append(f'(assert {all_ok("y")})')
            for n in sigs_to_read:
                w = model.inputs[n]
                srt = 'Bool' if w == 1 else f'(_ BitVec {w})'
                L2.append(f'(declare-fun i_{n} () {srt})')
                L2.append(f'(assert (= i_{n} {model.sig(n, "y")}))')
            s2 = model.solver(L2)
            if s2.check() == z3.sat:
                cands.append(_model_values(s2.model(), 'i_'))
                continue
            trace = []
            vals = {}
            for d in m1.decls():
                n = d.name()
                if n.startswith('t_'):
                    _, i, sig = n.split('_', 2)
                    v = m1[d]
                    vals.setdefault(int(i), {})[sig] = (1 if z3.is_true(v) else 0) if z3.is_bool(v) else v.as_long()
            trace = [vals.get(i, {}) for i in range(k + 1)]
            return {'receptive': False, 'blocking_step': k, 'trace': trace, 'iterations': stats['iterations']}
    return {'receptive': True, 'depth': depth, 'iterations': stats['iterations']}


def _sort(s: str):
    if s == 'Bool':
        return z3.BoolSort()
    m = re.match(r'\(_ BitVec (\d+)\)', s)
    return z3.BitVecSort(int(m.group(1)))


# ----------------------------------------------------------------------------
# Counterexample triage
# ----------------------------------------------------------------------------

def triage(model: SmtModel, trace: list[dict], inputs: list[tuple[str, int]], outputs: list[tuple[str, int]],
           aok: list[str], okd: dict[str, str], rigid: list[tuple[str, int, int, int]],
           nondet: list[str], closest: bool = True) -> dict:
    """On the counterexample's inputs, look for a spec-conforming output trace.

    model is a *spec-only* harness (interface signals free).  okd maps
    property id -> deterministic ok wire."""
    k = len(trace) - 1
    base = model.unroll(k)
    for reg, w, lo, hi in rigid:
        if not model.has(reg):
            continue
        t = model.sig(reg, 's0')
        base.append(f'(assert (and (bvsge {t} {_bv(lo, w)}) (bvsle {t} {_bv(hi, w)})))')
    for i, st in enumerate(trace):
        for n, w in inputs:
            if st.get(n) is not None:
                base.append(f'(assert {model.equals(n, f"s{i}", st[n])})')
    env = [f'(assert {model.is_true(a, f"s{i}")})' for a in aok for i in range(k + 1)]
    # assume-guarantee semantics: a guarantee must hold at t only while every
    # assumption has held at all cycles <= t
    for i in range(k + 1):
        cur = '(and ' + ' '.join(model.is_true(a, f's{i}') for a in aok) + ')' if aok else 'true'
        prev_h = f'ahist_{i - 1}' if i else 'true'
        base.append(f'(declare-fun ahist_{i} () Bool)')
        base.append(f'(assert (= ahist_{i} (and {prev_h} {cur})))')
    sels = []
    for pid, wire in okd.items():
        sel = f'sel_{re.sub(r"[^A-Za-z0-9_]", "_", pid)}'
        sels.append((pid, sel))
        base.append(f'(declare-fun {sel} () Bool)')
        base.append(f'(assert (=> {sel} (and ' + ' '.join(f'(=> ahist_{i} {model.is_true(wire, f"s{i}")})'
                                                            for i in range(k + 1)) + ')))')
    readback = []
    for i in range(k + 1):
        for n, w in outputs:
            srt = 'Bool' if w == 1 else f'(_ BitVec {w})'
            readback.append(f'(declare-fun o_{i}_{n} () {srt})')
            readback.append(f'(assert (= o_{i}_{n} {model.sig(n, f"s{i}")}))')
    sel_terms = [z3.Bool(sel) for _, sel in sels]

    # 1. spec-feasible on these inputs (with assumptions)?  closest conforming outputs
    opt = model.solver(base + env + readback + [f'(assert {sel})' for _, sel in sels], opt=True)
    soft = 0
    for i, st in enumerate(trace if closest else []):
        for n, w in outputs:
            if st.get(n) is None:
                continue
            o = z3.Bool(f'o_{i}_{n}') if w == 1 else z3.BitVec(f'o_{i}_{n}', w)
            opt.add_soft(o == (z3.BoolVal(bool(st[n])) if w == 1 else z3.BitVecVal(st[n], w)), 1)
            soft += 1
    if opt.check() == z3.sat:
        m = opt.model()
        vals = {}
        for d in m.decls():
            n = d.name()
            if n.startswith('o_'):
                _, i, sig = n.split('_', 2)
                v = m[d]
                vals.setdefault(int(i), {})[sig] = (1 if z3.is_true(v) else 0) if z3.is_bool(v) else v.as_long()
        diff = []
        for i, st in enumerate(trace):
            for n, w in outputs:
                if st.get(n) is not None and vals.get(i, {}).get(n) is not None and vals[i][n] != st[n]:
                    diff.append({'step': i, 'signal': n, 'rtl': st[n], 'spec': vals[i][n]})
        return {'class': 'RTL-DEVIATION', 'conforming_outputs': [vals.get(i, {}) for i in range(k + 1)],
                'diff': diff, 'first_divergence': min((d['step'] for d in diff), default=None)}

    # 2. feasible under assume-guarantee semantics (the stimulus may violate
    #    the assumptions for every conforming behaviour)?
    s = model.solver(base + [f'(assert {sel})' for _, sel in sels])
    if s.check() == z3.sat:
        return {'class': 'ENV-DEPENDENT',
                'note': 'every conforming behaviour makes this stimulus violate an environment assumption'}

    # 3. every output sequence violates a guarantee while all assumptions still
    #    hold: an open-loop environment playing these inputs defeats any
    #    implementation, so the requirements are unrealizable (minimal core)
    s = model.solver(base)
    r = s.check(*sel_terms)
    if r != z3.unsat:
        return {'class': 'UNKNOWN'}
    core = [str(c) for c in s.unsat_core()]
    names = {sel: pid for pid, sel in sels}
    keep = list(core)
    i = 0
    while i < len(keep):
        trial = keep[:i] + keep[i + 1:]
        if s.check(*[z3.Bool(t) for t in trial]) == z3.unsat:
            keep = trial
        else:
            i += 1
    return {'class': 'SPEC-CONFLICT', 'core': sorted(names[c] for c in keep)}


# ----------------------------------------------------------------------------
# Forcing stimuli: environments that defeat every implementation
# ----------------------------------------------------------------------------

def _decl(name: str, w: int) -> str:
    return f'(declare-fun {name} () {"Bool" if w == 1 else f"(_ BitVec {w})"})'


def _lit(v: int, w: int) -> str:
    return ('true' if v else 'false') if w == 1 else _bv(v, w)


def forcing(model: SmtModel, inputs: list[tuple[str, int]], outputs: list[tuple[str, int]],
            aok: list[str], okd: dict[str, str], rst_name: str, rst_active_low: bool,
            depth: int, max_iter: int = 80) -> dict:
    """Search for a stimulus on which no output sequence meets the guarantees.

    Exists-forall by counterexample-guided inductive synthesis.  A pool holds
    output sequences.  Query 1 asks for inputs (reset in cycle 0 only) on
    which every pooled sequence violates some guarantee while all assumptions
    have held.  Query 2 asks whether any output sequence conforms on those
    inputs.  If none does, the inputs force a violation: an environment that
    plays them defeats every implementation, even one that knows the inputs in
    advance.  Otherwise the conforming sequence joins the pool.  When query 1
    becomes unsatisfiable, no stimulus of that length forces a violation of a
    clairvoyant implementation (a causal one may still be defeated, so a miss
    is bounded evidence, not a proof of realizability)."""
    if not okd:
        return {'forced': False, 'depth': depth, 'iterations': 0}
    rst_on = 0 if rst_active_low else 1
    iters = 0

    def ahist(prefix: str, k: int, L: list[str]) -> list[str]:
        names = []
        for i in range(k + 1):
            cur = '(and ' + ' '.join(model.is_true(a, f'{prefix}{i}') for a in aok) + ')' if aok else 'true'
            prev_h = f'{prefix}ah{i - 1}' if i else 'true'
            L.append(f'(declare-fun {prefix}ah{i} () Bool)')
            L.append(f'(assert (= {prefix}ah{i} (and {prev_h} {cur})))')
            names.append(f'{prefix}ah{i}')
        return names

    for k in range(1, depth + 1):
        pool: list[list[dict]] = []
        while True:
            iters += 1
            if iters > max_iter:
                return {'forced': False, 'undecided': True, 'depth': k, 'iterations': iters}
            # query 1: inputs that defeat every pooled output sequence
            L = []
            for i in range(k + 1):
                for n, w in inputs:
                    L.append(_decl(f'x_{i}_{n}', w))
                L.append(f'(assert (= x_{i}_{rst_name} {_lit(rst_on if i == 0 else 1 - rst_on, 1)}))')
            if model.env_ok:                # a stimulus is one that the harness' own condition admits
                L += model.unroll(k, prefix='e_s')
                for i in range(k + 1):
                    for n, w in inputs:
                        L.append(f'(assert (= x_{i}_{n} {model.sig(n, f"e_s{i}")}))')
            for j, O in enumerate(pool):
                p = f'c{j}_s'
                L += model.unroll(k, prefix=p)
                for i in range(k + 1):
                    for n, w in inputs:
                        L.append(f'(assert (= x_{i}_{n} {model.sig(n, f"{p}{i}")}))')
                    for n, w in outputs:
                        L.append(f'(assert {model.equals(n, f"{p}{i}", O[i][n])})')
                ah = ahist(p, k, L)
                viol = [f'(and {ah[i]} (not {model.is_true(wire, f"{p}{i}")}))'
                        for i in range(k + 1) for wire in okd.values()]
                L.append('(assert (or ' + ' '.join(viol) + '))')
            s1 = model.solver(L)
            if s1.check() != z3.sat:
                break                       # every stimulus of length k is met by a pooled sequence
            m1 = s1.model()
            stim = []
            for i in range(k + 1):
                st = {}
                for n, w in inputs:
                    v = m1.eval(z3.Bool(f'x_{i}_{n}') if w == 1 else z3.BitVec(f'x_{i}_{n}', w),
                                model_completion=True)
                    st[n] = (1 if z3.is_true(v) else 0) if w == 1 else v.as_long()
                stim.append(st)
            # query 2: does any output sequence conform on these inputs?
            L2 = model.unroll(k)
            for i, st in enumerate(stim):
                for n, w in inputs:
                    L2.append(f'(assert {model.equals(n, f"s{i}", st[n])})')
            ah = ahist('s', k, L2)
            for i in range(k + 1):
                for wire in okd.values():
                    L2.append(f'(assert (=> {ah[i]} {model.is_true(wire, f"s{i}")}))')
            for i in range(k + 1):
                for n, w in outputs:
                    L2.append(_decl(f'o_{i}_{n}', w))
                    L2.append(f'(assert (= o_{i}_{n} {model.sig(n, f"s{i}")}))')
            s2 = model.solver(L2)
            if s2.check() != z3.sat:
                return {'forced': True, 'depth': k, 'stimulus': stim, 'iterations': iters}
            m2 = s2.model()
            O = []
            for i in range(k + 1):
                row = {}
                for n, w in outputs:
                    v = m2.eval(z3.Bool(f'o_{i}_{n}') if w == 1 else z3.BitVec(f'o_{i}_{n}', w),
                                model_completion=True)
                    row[n] = (1 if z3.is_true(v) else 0) if w == 1 else v.as_long()
                O.append(row)
            pool.append(O)
    return {'forced': False, 'depth': depth, 'iterations': iters}
