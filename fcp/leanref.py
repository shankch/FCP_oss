"""The reference semantics in Lean, as an oracle for the monitors.

FCP-PL has two definitions.  The one every verdict comes from is operational:
fcp.monitor compiles a reading to a Verilog monitor (registers for the
temporal operators and the patterns, a counter since the last reset).  The
other is declarative and lives in lean/ (FCP/Semantics.lean, FCP/Items.lean):
the value of an expression at a cycle and the verdict of an item at a cycle,
as closed forms over the past of the trace, with exact integers and no
registers.  This module sets the two side by side:

* a reading is exported to the Lean oracle in elaborated form (names
  resolved, definitions inlined, parameters replaced by their values, the
  widths the three width-dependent operators need);
* the compiled monitor is simulated (Icarus) on random traces, one monitor
  instance per value given to the rigid names;
* the oracle (lean/Main.lean, built by lake) evaluates the same traces;
* every output is compared at every cycle.

Where they are compared.  A ghost whose update leaves its declared range
wraps in the monitor and does not in Lean; both report it in the cycle that
computes the update (the ghost's well-formedness conjunct), and nothing is
compared after it.  An output the simulator reports as x is counted apart:
the monitor has no value there.  The pattern inorder (a nondeterministic
monitor) is not part of the Lean formalization and is skipped.
"""
from __future__ import annotations

import itertools
import os
import random
import re
import subprocess
import tempfile
from typing import Optional

from .agents import IVERILOG
from .kernel import VVP
from .ir import Interface, Reset, Signal
from .lang import CHARS, FcpError, Node, clog2, const_eval, unparse
from .monitor import MAX_EXPANSION, MonitorGen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEAN_DIR = os.path.join(ROOT, 'lean')
LEAN_BIN = os.path.join(ROOT, '.tools', 'lean', 'bin')
ORACLE = os.path.join(LEAN_DIR, '.lake', 'build', 'bin', 'fcp-oracle')

BIN = {'&&': 'and', '||': 'or', '->': 'imp', '<->': 'iff', '==': 'eq', '!=': 'ne', '<': 'lt', '<=': 'le',
       '>': 'gt', '>=': 'ge', '+': 'add', '-': 'sub', '*': 'mul', '%': 'mod', '>>': 'shr',
       '&': 'band', '|': 'bor', '^': 'bxor', 'in': 'mem'}
UNARY_CALLS = {'rose', 'fell', 'stable', 'changed', 'once', 'hist', 'len', 'lower', 'upper',
               'onehot', 'onehot0', 'countones'} | set(CHARS)


class Unsupported(Exception):
    """An expression the exporter does not carry over (the item is skipped)."""


def available() -> bool:
    return os.path.exists(os.path.join(LEAN_BIN, 'lake')) and os.path.exists(IVERILOG)


def build() -> str:
    """Build the oracle (lake) and return its path."""
    env = dict(os.environ, PATH=LEAN_BIN + os.pathsep + os.environ.get('PATH', ''))
    subprocess.run([os.path.join(LEAN_BIN, 'lake'), 'build'], cwd=LEAN_DIR, env=env, check=True,
                   capture_output=True, text=True)
    return ORACLE


#: What lean/ proves.  The monitor theorems (FCP/Monitor.lean) say that the
#: registers the compiler emits compute the closed forms of the reference;
#: the contract theorems (FCP/Contracts.lean) are the propositions of the paper;
#: the causality theorems (FCP/Causal.lean) say that a verdict of FCP-PL reads
#: the trace up to its cycle, which is what the propositions ask of a verdict.
THEOREMS = {
    'monitor': ['FCP.segGe_sat', 'FCP.eval_once', 'FCP.eval_hist', 'FCP.eval_since', 'FCP.eval_prev',
                'FCP.nextOpen_eq', 'FCP.withinDue_eq', 'FCP.holdOpen_eq', 'FCP.waited_eq',
                'FCP.afterReset_eq', 'FCP.Pattern.raw_eq_rawReg', 'FCP.gate_eq', 'FCP.gateTrig_eq',
                'FCP.Item.ok_eq_okReg', 'FCP.Item.cov_eq_covReg', 'FCP.ghostRuns_eq'],
    'contracts': ['FCP.Contracts.conflict_sound', 'FCP.Contracts.conflict_violates',
                  'FCP.Contracts.conflict_pinned', 'FCP.Contracts.enforced_meaning',
                  'FCP.Contracts.delegated_meaning', 'FCP.Contracts.horizon',
                  'FCP.Contracts.proved_sound', 'FCP.Contracts.proved_bounded_sound',
                  'FCP.Contracts.invariant_sound'],
    'causal': ['FCP.eval_causal', 'FCP.Item.ok_causal', 'FCP.ghostRun_causal', 'FCP.Item.okAll_causal',
               'FCP.Item.causal'],
}


def axioms(names: list) -> dict:
    """The axioms each theorem rests on, as Lean reports them.  A theorem with
    a gap in its proof rests on `sorryAx`; a name that is not a theorem of the
    library is missing from the result."""
    env = dict(os.environ, PATH=LEAN_BIN + os.pathsep + os.environ.get('PATH', ''))
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'axioms.lean')
        with open(path, 'w') as f:
            f.write('import FCP\n' + ''.join(f'#print axioms {n}\n' for n in names))
        out = subprocess.run([os.path.join(LEAN_BIN, 'lake'), 'env', 'lean', path], cwd=LEAN_DIR, env=env,
                             capture_output=True, text=True).stdout
    found = {}
    for m in re.finditer(r"'([^']+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)", out):
        found[m.group(1)] = sorted(x.strip() for x in (m.group(2) or '').replace('\n', ' ').split(',') if x.strip())
    return found


class Export:
    """A reading compiled to its monitor and written for the oracle."""

    def __init__(self, iface, fset: dict, module: str = 'fcp_mon_ref'):
        self.iface = iface
        self.gen = MonitorGen(iface, fset, module)
        self.info: dict[int, list] = {}        # node -> (type, constant) at every compilation of it
        inner = self.gen.b.compile

        def compile(n, scope):
            v = inner(n, scope)
            self.info.setdefault(id(n), []).append((v.ty, v.const))
            return v

        self.gen.b.compile = compile
        self.mon = self.gen.build()
        self.skipped: dict[str, str] = {}      # item id -> why it is not compared
        self.ids: dict[str, str] = {}          # name in the export -> item id
        self.notes: list[str] = []
        self.text = self._reading()

    # -- expressions -----------------------------------------------------------
    def _const(self, n: Node) -> int:
        seen = {c for _, c in self.info.get(id(n), [])}
        if len(seen) == 1 and None not in seen:
            return seen.pop()
        if n.op == 'num':
            return n.val
        try:
            return const_eval(unparse(n), self.gen.params)
        except FcpError:
            raise Unsupported(f'{unparse(n)} is not a constant')

    def _width(self, n: Node) -> int:
        seen = {(ty.kind in ('bits', 'bool'), ty.nbits) for ty, _ in self.info.get(id(n), [])}
        if len(seen) != 1 or not next(iter(seen))[0]:
            raise Unsupported(f'no single width for {unparse(n)}')
        return next(iter(seen))[1]

    def expr(self, n: Node, bound: tuple = ()) -> str:
        e = lambda x: self.expr(x, bound)                         # noqa: E731
        op = n.op
        if op == 'num':
            return str(n.val)
        if op == 'str':
            return '(lst ' + ' '.join(str(ord(c)) for c in n.val) + ')'
        if op == 'list':
            return '(lst ' + ' '.join(str(self._const(a)) for a in n.args) + ')'
        if op == 'ref':
            if n.val in bound:
                return f'(bvar {bound.index(n.val)})'
            s = self.gen.syms.get(n.val)
            if s is None:
                raise Unsupported(f'unknown name {n.val}')
            if s.kind == 'param':
                return str(s.value)
            if s.kind == 'def':
                return self.expr(s.node, bound)
            return f'({ {"ghost": "ghost", "rigid": "rigid"}.get(s.kind, "sig") } {n.val})'
        if op == 'un':
            a = e(n.args[0])
            if n.val == '!':
                return f'(not {a})'
            if n.val == '-':
                return f'(neg {a})'
            return f'(bnot {self._width(n.args[0])} {a})'
        if op == 'bin':
            a, b = e(n.args[0]), e(n.args[1])
            if n.val == '<<':
                seen = self.info.get(id(n.args[0]), [])
                kinds = {'const' if c is not None else ty.kind for ty, c in seen}
                if kinds == {'bits'}:                             # a bit-vector keeps its width
                    return f'(shlw {self._width(n.args[0])} {a} {b})'
                if not kinds or 'bits' in kinds:
                    raise Unsupported(f'no single type for {unparse(n.args[0])}')
                return f'(shl {a} {b})'
            return f'({BIN[n.val]} {a} {b})'
        if op == 'ite':
            return f'(ite {e(n.args[0])} {e(n.args[1])} {e(n.args[2])})'
        if op == 'idx':
            return f'(idx {e(n.args[0])} {e(n.args[1])})'
        if op == 'slice':
            return f'(slice {self._const(n.args[1])} {self._const(n.args[2])} {e(n.args[0])})'
        if op == 'quant':
            var, bnd, body = n.args
            return f'(q-{n.val} {e(bnd)} {self.expr(body, (var.val,) + bound)})'
        f, args = n.val, n.args
        if f == 'prev':
            return f'(prev {self._const(args[1]) if len(args) == 2 else 1} {e(args[0])})'
        if f == 'since':
            return f'(since {e(args[0])} {e(args[1])})'
        if f in ('min', 'max'):
            return f'({f} {e(args[0])} {e(args[1])})'
        if f == 'zext':
            return e(args[0])                                     # the value is kept; the type is wider
        if f == 'any':
            return f'(anybit {e(args[0])})'
        if f == 'all':
            return f'(allbits {self._width(args[0])} {e(args[0])})'
        if f in UNARY_CALLS:
            return f'({f} {e(args[0])})'
        raise Unsupported(f'function {f}')

    # -- the reading -----------------------------------------------------------
    def _pattern(self, it) -> str:
        x = {k: self.expr(n) for k, n in it.args.exprs.items()}
        i = it.args.ints
        if it.pattern == 'invariant':
            return f'(invariant {x["cond"]})'
        if it.pattern in ('implies', 'next'):
            return f'({it.pattern} {x["trigger"]} {x["cond"]})'
        if it.pattern == 'within':
            return f'(within {x["trigger"]} {x["cond"]} {i["min"]} {i["max"]})'
        if it.pattern == 'hold_until':
            return f'(hold_until {x["trigger"]} {x["hold"]} {x["release"]})'
        if it.pattern == 'bounded_wait':
            return f'(bounded_wait {x["cond"]} {i["max"]})'
        if it.pattern == 'after_reset':
            return f'(after_reset {x["cond"]})'
        raise Unsupported(f'pattern {it.pattern}')

    def _reading(self) -> str:
        g = self.gen
        live = sorted({name for name, _ in g.ghost_cache})        # the ghosts the monitor carries
        ghosts = []
        for name in live:
            d = g.ghost_decl[name]
            ghosts.append(f'({name} {d["ty"].lo} {d["ty"].hi} {d["init_v"]} {self.expr(d["next_n"])})')
        rigids = [f'({name} {s.ty.lo} {s.ty.hi})' for name, s in g.syms.items() if s.kind == 'rigid']
        items = []
        for it in self.mon.items.values():
            try:
                pat = self._pattern(it)
            except Unsupported as ex:
                self.skipped[it.id] = str(ex)
                continue
            name = f'i{len(self.ids)}'
            self.ids[name] = it.id
            items.append(f'({name} {it.role} {it.mode} {pat})')
        return '(reading\n (ghosts\n  ' + '\n  '.join(ghosts) + ')\n (rigids ' + ' '.join(rigids) + \
            ')\n (items\n  ' + '\n  '.join(items) + '))\n'


# -- traces --------------------------------------------------------------------

def random_trace(x: Export, rng: random.Random, T: int, first: bool = True) -> list[dict]:
    """One value of every monitor input at every cycle.  Cycle 0 is a reset,
    later resets are rare; a port holds small values, any value or its
    extremes, and may keep its value for a while, so that equalities,
    counters and the edges of ranges all occur."""
    iface, seqs = x.iface, x.iface.seqs or {}
    rst = iface.reset
    hidden = {f'{n}__len' for n in seqs}
    active, out = [], []
    for t in range(T):
        active.append((t == 0 and first) or (t > 0 and rng.random() < (0.35 if active[-1] and t > 1 else 0.04)))
    plan = {}
    for name, w in x.mon.ports_in:
        if name == rst.name or name in hidden:
            continue
        top = (1 << w) - 1
        plan[name] = (rng.choice(['small', 'any', 'edge']), rng.choice([0.0, 0.0, 0.6, 0.85]),
                      rng.choice([0.15, 0.5, 0.85]), top)
    last: dict = {}
    for t in range(T):
        st = {rst.name: int(active[t]) ^ int(rst.active_low)}
        for name, (mode, hold, p, top) in plan.items():
            if name in last and rng.random() < hold:
                st[name] = last[name]
                if name in seqs:
                    st[f'{name}__len'] = last[f'{name}__len']
                continue
            if name in seqs:
                w, n = seqs[name]
                lw = max(1, n.bit_length())
                ln = rng.randint(0, n) if rng.random() < 0.9 else rng.randint(0, (1 << lw) - 1)
                pool = [32, 45, 48, 57, 65, 90, 97, 122] if w == 8 else [0, 1, 2, (1 << w) - 1]
                slots = [rng.choice(pool) & ((1 << w) - 1) if rng.random() < 0.8 else rng.randint(0, (1 << w) - 1)
                         for _ in range(n)]
                if rng.random() < 0.7:                            # most of the time, nothing beyond the length
                    slots = [c if k < ln else 0 for k, c in enumerate(slots)]
                st[name] = sum(c << (k * w) for k, c in enumerate(slots))
                st[f'{name}__len'] = ln
            elif top == 1:
                st[name] = int(rng.random() < p)
            elif mode == 'small':
                st[name] = rng.randint(0, min(3, top))
            elif mode == 'edge':
                st[name] = rng.choice([0, 1, top, top - 1, rng.randint(0, top)])
            else:
                st[name] = rng.randint(0, top)
        last = st
        out.append(st)
    return out


def trace_text(x: Export, trace: list[dict]) -> str:
    """The trace as the oracle reads it: the reset, every signal, and every
    sequence in canonical form (the length clamped, nothing beyond it)."""
    iface, seqs = x.iface, x.iface.seqs or {}
    rst = iface.reset
    hidden = {f'{n}__len' for n in seqs}
    active = [int(bool(st[rst.name]) != rst.active_low) for st in trace]
    rows = [f'(len {len(trace)})', '(rst ' + ' '.join(map(str, active)) + ')',
            '(sig rst_active ' + ' '.join(map(str, active)) + ')']
    for name, _ in x.mon.ports_in:
        if name in hidden:
            continue
        if name in seqs:
            w, n = seqs[name]
            vals = []
            for st in trace:
                ln = min(st[f'{name}__len'], n)
                vals.append('(' + ' '.join(str((st[name] >> (k * w)) & ((1 << w) - 1)) for k in range(ln)) + ')')
            rows.append(f'(seq {name} ' + ' '.join(vals) + ')')
        else:
            rows.append(f'(sig {name} ' + ' '.join(str(st[name]) for st in trace) + ')')
    return '(trace ' + '\n '.join(rows) + ')\n'


def valuations(x: Export, rng: random.Random, n: int) -> list[dict]:
    rig = [(p[3:], lo, hi) for p, _, lo, hi in x.mon.rigid_ports]
    if not rig:
        return [{}]
    out = [{r: lo for r, lo, _ in rig}, {r: hi for r, _, hi in rig}]
    for _ in range(4 * n):
        out.append({r: rng.randint(lo, hi) for r, lo, hi in rig})
    seen, uniq = set(), []
    for v in out:
        k = tuple(sorted(v.items()))
        if k not in seen:
            seen.add(k)
            uniq.append(v)
    return uniq[:max(1, n)]


# -- the two sides ---------------------------------------------------------------

def simulate(x: Export, traces: list[list[dict]], vals: list[dict], text: str = '') -> list[list[dict]]:
    """The monitor's outputs: per trace, per valuation, {output port: one
    character per cycle (0, 1 or x)}.  Each valuation has its own monitor
    instance and each trace its own run, so every run starts from the
    monitor's initial state.  text: another body for the same module (a
    mutant of the monitor)."""
    mon, T = x.mon, len(traces[0])
    W = sum(w for _, w in mon.ports_in)
    tb = ['`timescale 1ns/1ps', 'module fcp_ref_tb;', "  reg clk = 1'b0;", f'  reg [{W - 1}:0] stim [0:{T - 1}];',
          f'  reg [{W - 1}:0] cur;', '  reg [8*512-1:0] file;', '  integer k;']
    at = W
    for n, w in mon.ports_in:
        at -= w
        tb.append(f'  wire {f"[{w - 1}:0] " if w > 1 else ""}{n} = cur[{at + w - 1}:{at}];')
    outs = []
    for j, val in enumerate(vals):
        conns = ['.clk(clk)'] + [f'.{n}({n})' for n, _ in mon.ports_in]
        for port, w, _, _ in mon.rigid_ports:
            v = val[port[3:]] & ((1 << w) - 1)
            tb.append(f"  wire signed [{w - 1}:0] v{j}_{port} = {w}'b{v:0{w}b};")
            conns.append(f'.{port}(v{j}_{port})')
        conns += [f".{port}({w}'d0)" for port, w in mon.nondet_ports]
        for o in mon.outputs:
            tb.append(f'  wire v{j}_{o};')
            conns.append(f'.{o}(v{j}_{o})')
            outs.append(f'v{j}_{o}')
        tb.append(f'  {mon.module} m{j} (' + ', '.join(conns) + ');')
    tb += ['  initial begin', '    if (!$value$plusargs("stim=%s", file)) $finish;', '    $readmemh(file, stim);',
           f'    for (k = 0; k < {T}; k = k + 1) begin', '      cur = stim[k]; #1;',
           '      $display("C %b", {' + ', '.join(outs) + '});', "      #4 clk = 1'b1; #5 clk = 1'b0;",
           '    end', '    $finish;', '  end', 'endmodule']
    res = []
    with tempfile.TemporaryDirectory(prefix='fcp_ref_') as d:
        for name, body in (('mon.v', text or mon.text), ('tb.v', '\n'.join(tb) + '\n')):
            with open(os.path.join(d, name), 'w') as f:
                f.write(body)
        subprocess.run([IVERILOG, '-g2005', '-o', os.path.join(d, 'sim'), os.path.join(d, 'mon.v'),
                        os.path.join(d, 'tb.v')], check=True, capture_output=True, text=True)
        for trace in traces:
            words = []
            for st in trace:
                word = 0
                for n, w in mon.ports_in:
                    word = (word << w) | (int(st.get(n, 0)) & ((1 << w) - 1))
                words.append(f'{word:x}')
            with open(os.path.join(d, 'stim.hex'), 'w') as f:
                f.write('\n'.join(words) + '\n')
            run = subprocess.run([VVP, os.path.join(d, 'sim'), f'+stim={os.path.join(d, "stim.hex")}'],
                                 check=True, capture_output=True, text=True)
            rows = [ln[2:].strip() for ln in run.stdout.splitlines() if ln.startswith('C ')]
            if len(rows) != T:
                raise RuntimeError(f'simulation printed {len(rows)} cycles of {T}: {run.stdout[-400:]}')
            per = []
            for j in range(len(vals)):
                base = j * len(mon.outputs)
                per.append({o: ''.join(r[base + i] for r in rows) for i, o in enumerate(mon.outputs)})
            res.append(per)
    return res


def oracle(x: Export, traces: list[list[dict]], vals: list[dict], binary: str = '') -> list[list[dict]]:
    """The reference verdicts: per trace, per valuation, {(item id, stream):
    one character per cycle}; the item id is '-' for the stream wf (every
    ghost stays in its range)."""
    text = x.text + '(vals ' + ' '.join('(' + ' '.join(f'({r} {v})' for r, v in val.items()) + ')'
                                        for val in vals) + ')\n' + ''.join(trace_text(x, t) for t in traces)
    with tempfile.TemporaryDirectory(prefix='fcp_ref_') as d:
        path = os.path.join(d, 'reading.sexpr')
        with open(path, 'w') as f:
            f.write(text)
        run = subprocess.run([binary or ORACLE, path], capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(f'fcp-oracle: {run.stderr.strip()[:400]}')
    res: list[list[dict]] = []
    for line in run.stdout.splitlines():
        p = line.split()
        if p[0] == 'trace':
            res.append([])
        elif p[0] == 'val':
            res[-1].append({})
        else:
            res[-1][-1][(x.ids.get(p[0], p[0]), p[1])] = p[2]
    return res


def compare(x: Export, sim: list[list[dict]], ref: list[list[dict]], vals: list[dict]) -> dict:
    """Every output at every cycle up to the first cycle at which a ghost
    leaves its range (in that cycle the monitor's verdicts also carry the
    range checks of its other ghost instances, so a verdict Lean passes is
    not compared there)."""
    out = {'streams': 0, 'varied': 0, 'cycles': 0, 'compared': 0, 'differ': 0, 'undefined': 0, 'past_range': 0,
           'mismatches': [], 'unmatched': []}
    for k, (srow, rrow) in enumerate(zip(sim, ref)):
        for j, (s, r) in enumerate(zip(srow, rrow)):
            T = len(r[('-', 'wf')])
            bad = min([v.index('0') for (_, what), v in r.items() if what in ('wf', 'wfx') and '0' in v] + [T])
            for (iid, what), bits in r.items():
                if what in ('wf', 'wfx'):
                    continue
                port = x.mon.items[iid].out.get(what)
                if port is None or (what == 'okd' and port == x.mon.items[iid].out.get('ok')):
                    out['unmatched'].append((iid, what))
                    continue
                out['streams'] += 1
                out['cycles'] += T
                out['varied'] += len(set(bits[:bad])) == 2      # the stream takes both values
                for t in range(T):
                    m = s[port][t]
                    if t > bad or (t == bad and what in ('ok', 'okd', 'aok') and bits[t] == '1'):
                        out['past_range'] += 1
                    elif m not in '01':
                        out['undefined'] += 1
                        out['differ'] += 1
                        if len(out['mismatches']) < 40:
                            out['mismatches'].append(dict(trace=k, val=vals[j], item=iid, stream=what, cycle=t,
                                                          lean=bits[t], monitor=m))
                    else:
                        out['compared'] += 1
                        if m != bits[t]:
                            out['differ'] += 1
                            if len(out['mismatches']) < 40:
                                out['mismatches'].append(dict(trace=k, val=vals[j], item=iid, stream=what, cycle=t,
                                                              lean=bits[t], monitor=m))
            for it in x.mon.items.values():                    # an output of the monitor Lean has no stream for
                for what, port in it.out.items():
                    if it.id not in x.skipped and (it.id, what) not in r and \
                            not (what == 'okd' and port == it.out.get('ok')):
                        out['unmatched'].append((it.id, what))
    out['unmatched'] = sorted(set(out['unmatched']))
    return out


def check(iface, fset: dict, traces: int = 20, cycles: int = 40, vals: int = 3, seed: int = 0,
          binary: str = '') -> dict:
    """Compare the monitor of a reading with the reference semantics on
    random traces.  Returns the counts and the disagreements (none expected).
    binary: another build of the oracle (a changed definition)."""
    rng = random.Random(seed)
    x = Export(iface, fset)
    vs = valuations(x, rng, vals)
    ts = [random_trace(x, rng, cycles) for _ in range(traces)]
    out = compare(x, simulate(x, ts, vs), oracle(x, ts, vs, binary), vs)
    out.update(items=len(x.ids), skipped=x.skipped, valuations=len(vs), traces=traces)
    return out


# -- sensitivity: would a wrong monitor be noticed? ----------------------------
_RULES = [
    ('&& to ||', re.compile(r'&&'), lambda m: '||'),
    ('|| to &&', re.compile(r'\|\|'), lambda m: '&&'),
    ('== to !=', re.compile(r'=='), lambda m: '!='),
    ('!= to ==', re.compile(r'!='), lambda m: '=='),
    ('< to <=', re.compile(r'(?<![<>=!])<(?![<=])'), lambda m: '<='),
    ('<= to <', re.compile(r'(?<![<>=!])<=(?!=)'), lambda m: '<'),
    ('> to >=', re.compile(r'(?<![<>=!])>(?![>=])'), lambda m: '>='),
    ('>= to >', re.compile(r'(?<![<>=!])>=(?!=)'), lambda m: '>'),
    ('+ to -', re.compile(r' \+ '), lambda m: ' - '),
    ('- to +', re.compile(r' - '), lambda m: ' + '),
    ('! dropped', re.compile(r'!(?!=)'), lambda m: ''),
    ('constant changed', re.compile(r"(\d+)'b([01]+)"),
     lambda m: f"{m.group(1)}'b{m.group(2)[:-1]}{'1' if m.group(2)[-1] == '0' else '0'}"),
    ('count changed', re.compile(r'(_seg|_cyc) (<|>=) (\d+)'),
     lambda m: f'{m.group(1)} {m.group(2)} {int(m.group(3)) + 1}'),
    ('reset dropped', re.compile(r'rst_active \? '), lambda m: "1'b0 ? "),
]


def mutants(text: str) -> list[tuple[int, str, str]]:
    """Single changes of the body of a monitor: one operator, one constant,
    one negation or one reset, at one place.  (line, what, the changed line):
    a large monitor has tens of thousands, so the text is built only for
    the ones tried."""
    lines, out = text.split('\n'), []
    for i, ln in enumerate(lines):
        code, sep, comment = ln.partition('  //')
        m = re.match(r'(  (?:wire|reg|assign) [^=]*? = |    \w+ <= )(.*)$', code)
        if not m:
            continue
        head, rhs = m.group(1), m.group(2)
        for what, rx, sub in _RULES:
            for hit in rx.finditer(rhs):
                new = rhs[:hit.start()] + sub(hit) + rhs[hit.end():]
                out.append((i + 1, what, head + new + sep + comment))
    return out


def _unread(text: str, outputs: set) -> dict:
    """Where a line of a monitor is read.  dead: by none of the compared
    outputs.  initial: the declaration of a register every reset sets (its
    initial value is gone after cycle 0, a reset).  scenario: only by the
    outputs of scenarios.  range: only through the check that a ghost stays
    in its range."""
    lines = text.split('\n')
    deps, line_of, resets, checks = {}, {}, set(), set()
    for i, ln in enumerate(lines):
        code, _, comment = ln.partition('  //')
        m = re.match(r'  (?:wire|reg|assign) (?:signed )?(?:\[[^\]]*\] )?(\w+)(?: = (.*))?;$', code) or \
            re.match(r'    (\w+) <= (.*);$', code)
        if m:
            deps.setdefault(m.group(1), set()).update(re.findall(r'[A-Za-z_]\w*', m.group(2) or ''))
            line_of.setdefault(m.group(1), set()).add(i + 1)
            if code.startswith('    ') and (m.group(2) or '').startswith('rst_active ? '):
                resets.add(m.group(1))
            if 'stays in its declared range' in comment:
                checks.add(m.group(1))

    def cone(roots, cut=()):
        seen, todo = set(), [r for r in roots if r in deps]
        while todo:
            n = todo.pop()
            if n not in seen:
                seen.add(n)
                todo += [d for d in deps[n] if d in deps and d not in cut]
        return seen

    live = cone(outputs)
    rest = cone({o for o in outputs if not o.startswith('cov_')})
    direct = cone(outputs, cut=checks)
    at = lambda names: {i for n in names for i in line_of[n]}
    return {'dead': at(set(deps) - live),
            'initial': {i for i in at(resets) if lines[i - 1].startswith('  reg ')},
            'scenario': at(live - rest), 'range': at(live - direct) | at(checks)}


def sensitivity(iface, fset: dict, sample: int = 40, traces: int = 60, cycles: int = 40, vals: int = 3,
                seed: int = 0) -> dict:
    """Change the monitor at one place and compare again: a change is noticed
    when some output differs from the reference at a compared cycle.  A
    sample of the changes; the ones not noticed are returned to be read
    (a change can leave the outputs as they were)."""
    rng = random.Random(seed)
    x = Export(iface, fset)
    vs = valuations(x, rng, vals)
    ts = [random_trace(x, rng, cycles) for _ in range(traces)]
    ref = oracle(x, ts, vs)
    where = _unread(x.mon.text, {p for i, it in x.mon.items.items() if i not in x.skipped
                                 for p in it.out.values()})
    every = [m for m in mutants(x.mon.text) if m[0] not in where['dead']]   # a line no output reads is not the monitor
    tried = rng.sample(every, min(sample, len(every)))
    out = {'changes': len(every), 'tried': len(tried), 'noticed': 0, 'rejected': 0, 'initial': 0, 'by': {},
           'unnoticed': []}
    base = x.mon.text.split('\n')
    for line, what, new in tried:
        text = '\n'.join(base[:line - 1] + [new] + base[line:])
        tally = out['by'].setdefault(what, [0, 0])
        tally[1] += 1
        try:
            hit = False
            for lo, hi in ((0, 2), (2, 12), (12, len(ts))):      # most changes show in the first traces
                if lo < hi and compare(x, simulate(x, ts[lo:hi], vs, text), ref[lo:hi], vs)['differ']:
                    hit = True
                    break
        except subprocess.CalledProcessError:              # not Verilog any more
            out['rejected'] += 1
            tally[1] -= 1
            continue
        if hit:
            out['noticed'] += 1
            tally[0] += 1
        elif line in where['initial']:     # the initial value of a register the reset in cycle 0 sets
            out['initial'] += 1
            tally[1] -= 1
        else:
            out['unnoticed'].append({'line': line, 'what': what, 'was': base[line - 1].strip(),
                                     'now': new.strip(),
                                     'read': next((k for k in ('scenario', 'range') if line in where[k]), 'verdict')})
    return out


# -- readings for what the corpus does not use ---------------------------------
def interface(signals: list[tuple], params: Optional[dict] = None, reset: tuple = ('rst', False)) -> Interface:
    """A small interface: (name, direction, width) or, for a sequence,
    (name, direction, slot width, longest length)."""
    sigs, seqs = [Signal('clk', 'in', 1), Signal(reset[0], 'in', 1)], {}
    for name, d, w, *n in signals:
        if n:
            sigs += [Signal(name, d, n[0] * w), Signal(name + '__len', d, max(1, clog2(n[0] + 1)))]
            seqs[name] = (w, n[0])
        else:
            sigs.append(Signal(name, d, w))
    return Interface('clk', Reset(*reset), dict(params or {}), sigs, seqs)


def _props(*rows: tuple) -> list[dict]:
    return [{'id': i, 'expr': e} if isinstance(e, str) else {'id': i, **e} for i, e in rows]


def synthetic() -> dict[str, tuple]:
    """Two readings written for this comparison.  ops: every operator, each
    pattern with the arguments the corpus does not give it (a window that
    opens late, items checked in reset), an active-high reset, a rigid name
    with negative values, ghosts that depend on it, a ghost that leaves its
    range.  chain: a ghost that depends on a rigid name through another."""
    ops = {
        'fcp': '0.1', 'set': 'ops',
        'defs': {'d': 'a - b', 'word': 'all(i < len(s): isalpha(s[i]))'},
        'ghosts': [{'name': 'cnt', 'range': [0, 5], 'init': 0, 'next': 'en ? (cnt == 5 ? 0 : cnt + 1) : cnt'},
                   {'name': 'acc', 'range': [-8, 8], 'init': 0, 'next': 'max(-8, min(8, acc + d + k))'},
                   {'name': 'over', 'range': [0, 2], 'init': 1,
                    'next': 'a == 0 && b[3] ? over + 1 : a == 1 ? 0 : over'},
                   {'name': 'lim', 'range': [0, 3], 'init': 3,          # its next value in a reset cycle is not asked
                    'next': 'rst_active ? 9 : en && lim > 0 ? lim - 1 : lim'}],
        'rigids': [{'name': 'k', 'range': [-1, 1]}],
        'properties': _props(
            ('P-ALL', 'all(a) -> any(b[1:0])'), ('P-ANY', 'any(a ^ b) == (a != b)'), ('P-OR', '(a | b) == q[3:0]'),
            ('P-XOR', '(a ^ b) != 5 || en'), ('P-AND', '(a & ~b) != 3'), ('P-SLICE', 'c[7:4] != a[2:1]'),
            ('P-SHLW', '(a << 1) != b'), ('P-SHLN', '(d << 2) != q - 20'), ('P-SHLC', '(1 << a[1:0]) != b'),
            ('P-SHRB', '(c >> 2) != q'), ('P-SHRN', '(d >> 1) != q[2:0] - 4'), ('P-MOD', 'd % N != q[1:0]'),
            ('P-NEG', '-d != q[3:0] - 8'), ('P-MINMAX', 'min(a, b) + max(d, 2) != q[4:0]'),
            ('P-ONES', 'countones(c) != a[2:0]'), ('P-HOT', 'onehot(a) -> !onehot0(b)'),
            ('P-ALPHA', 'isalpha(c) -> q[0]'), ('P-ALNUM', 'isalnum(c) -> q[1]'), ('P-LOWER', 'islower(c) -> q[2]'),
            ('P-UPPER', 'isupper(c) -> q[3]'), ('P-SPACE', 'isspace(c) -> q[4]'), ('P-DIGIT', 'isdigit(c) -> q[5]'),
            ('P-TOLOW', 'lower(c) == c || q[0]'), ('P-TOUP', 'upper(c) == c || q[1]'),
            ('P-WORD', 'word -> len(s) < 3'),
            ('P-CASE', 'count(i < len(s): lower(s[i]) == upper(s[i])) != a[1:0]'),
            ('P-SUM', 'sum(i < len(s): s[i] > "m" ? i : 0) != q[2:0]'), ('P-MEM', 'c in s -> q[0]'),
            ('P-IDX', 'len(s) > 1 -> s[1] != c'), ('P-EDGE', 'rose(en) -> !fell(q[0])'),
            ('P-STABLE', 'stable(a) -> changed(b)'), ('P-ONCE', 'once(a == 0) -> hist(b != 0) || q[0]'),
            ('P-SINCE', 'since(en, q[0]) -> q[1]'), ('P-PREV', 'prev(a, 3) != b'), ('P-PREVD', 'prev(a, D) != b'),
            ('P-IFF', '(a < b) == (prev(a) < prev(b)) || q[5]'), ('P-CNT', 'cnt != q[2:0]'),
            ('P-ACC', 'acc + k != d'), ('P-OVER', 'over != 1 || en'), ('P-LIM', 'lim != q[1:0]'),
            ('P-WITHIN', {'pattern': 'within',
                          'args': {'trigger': 'en && a == 0', 'cond': 'q[0]', 'min': 1, 'max': 3}}),
            ('P-WITHIN2', {'pattern': 'within', 'args': {'trigger': 'rose(en)', 'cond': 'q[1]', 'min': 2, 'max': 2}}),
            ('P-NEXT', {'pattern': 'next', 'args': {'trigger': 'a == k + 1', 'cond': 'q[0] || prev(en)'}}),
            ('P-HOLD', {'pattern': 'hold_until',
                        'args': {'trigger': 'rose(en)', 'hold': 'q[0]', 'release': 'a == 0'}}),
            ('P-WAIT', {'pattern': 'bounded_wait', 'args': {'cond': 'en && !q[0]', 'max': 'N'}}),
            ('P-RESET', {'pattern': 'after_reset', 'args': {'cond': 'q[1:0] == 0'}}),
            ('P-ALWAYS', {'expr': 'rst_active -> q[0]', 'mode': 'always'}),
            ('P-ALWAYS2', {'pattern': 'implies', 'args': {'trigger': 'en', 'cond': 'q[2] || prev(q[2])'},
                           'mode': 'always'}),
            ('P-ALWAYS3', {'expr': 'once(en) -> hist(a != 0) || since(q[3], b == 0)', 'mode': 'always'}),
            ('P-ALWAYS4', {'pattern': 'hold_until', 'args': {'trigger': 'en', 'hold': 'q[4]', 'release': 'a == 1'},
                           'mode': 'always'}),
            ('P-ALWAYS5', {'pattern': 'next', 'args': {'trigger': 'rose(en)', 'cond': 'q[5]'}, 'mode': 'always'}),
            ('P-ALWAYS6', {'pattern': 'bounded_wait', 'args': {'cond': 'a == 2', 'max': 2}, 'mode': 'always'}),
            ('P-ALWAYS7', {'pattern': 'within', 'args': {'trigger': 'a == 3', 'cond': 'q[0]', 'min': 0, 'max': 2},
                           'mode': 'always'})),
        'assumptions': _props(('A-K', 'a != k + 2 || en'),
                              ('A-HOLD', {'pattern': 'hold_until',
                                          'args': {'trigger': 'en', 'hold': 'b != 0', 'release': 'q[5]'}})),
        'scenarios': [{'id': 'S-1', 'cover': 'word && len(s) == 4'}, {'id': 'S-2', 'cover': 'cnt == 5 && fell(en)'}],
        'dont_cares': [{'id': 'X-1', 'signal': 'q', 'when': 'c == 0'}],
    }
    chain = {
        'fcp': '0.1', 'set': 'chain',
        'ghosts': [{'name': 'g1', 'range': [0, 7], 'init': 0, 'next': 'a == k ? (g1 == 7 ? 0 : g1 + 1) : g1'},
                   {'name': 'g2', 'range': [0, 7], 'init': 0, 'next': 'en ? g1 : g2'}],
        'rigids': [{'name': 'k', 'range': [0, 3]}],
        'properties': _props(('P-1', 'g2 != q'), ('P-2', 'g1 != q'),
                             ('P-3', {'pattern': 'next', 'args': {'trigger': 'g2 == 2', 'cond': 'q[0]'}})),
        'assumptions': _props(('A-1', 'g2 != a + 1'), ('A-2', 'g1 != a + 1')),
    }
    return {'ops': (interface([('a', 'in', 4), ('b', 'in', 4), ('c', 'in', 8), ('en', 'in', 1), ('s', 'in', 8, 4),
                               ('q', 'out', 6)], {'N': 3, 'D': 2}), ops),
            'chain': (interface([('a', 'in', 3), ('en', 'in', 1), ('q', 'out', 3)]), chain)}
