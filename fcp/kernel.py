"""Guard kernels: agent control code that runs in Python and compiles to RTL.

An agent turn is: the LLM proposes an action (a cut point: any value at all),
the kernel decides what executes, the tool runs, and the kernel updates its
state from the tool's result.  A kernel module defines

  PRE    {name: width}             inputs known before the action runs: the
                                   LLM's proposal and customer events
  POST   {name: width}             results of the executed action
  OUT    {name: width}             what executes this turn
  REGS   {name: (width, reset)}    kernel state
  decide(i, r, o)                  sets o from i (PRE fields only) and r
  update(i, r, o, n)               sets n (next state) from i, r and o

The two functions are written in a small Python subset: unsigned integer
fields, locals, if/elif/else, assignments, `+ * & | ^ << >>`, comparisons,
`and or not`, conditional expressions, and `~` only as an operand of `&`.
There is no subtraction, so every value is a non-negative integer and plain
Python arithmetic agrees with 32-bit Verilog arithmetic.

`verilog()` translates a kernel to one synthesizable module, `Runtime` runs the
same functions in the agent loop, and `cosim()` checks on random turns that
the two agree.  The code the agent executes is therefore the code that is
verified, up to this translator.
"""
from __future__ import annotations

import ast
import os
import random
import subprocess
import tempfile
from types import ModuleType

from .agents import IVERILOG

VVP = os.path.join(os.path.dirname(IVERILOG), 'vvp')
_PREFIXES = ('w_', 'r_', 'n_', 'd_', 'u_')


class KernelError(Exception):
    pass


def _mask(w: int) -> int:
    return (1 << w) - 1


def load(path: str, patches: list | None = None, name: str | None = None) -> ModuleType:
    """Import a kernel module from a file, optionally after textual patches
    [(old, new), ...] (mutants are built this way)."""
    with open(path) as f:
        src = f.read()
    for old, new in patches or []:
        if src.count(old) != 1:
            raise KernelError(f'patch target must occur exactly once in {path}: {old!r}')
        src = src.replace(old, new)
    mod = ModuleType(name or os.path.splitext(os.path.basename(path))[0])
    mod.__file__ = path
    mod.__source__ = src
    exec(compile(src, path, 'exec'), mod.__dict__)
    for k in ('PRE', 'POST', 'OUT', 'REGS', 'decide', 'update'):
        if not hasattr(mod, k):
            raise KernelError(f'kernel {path} defines no {k}')
    names = list(mod.PRE) + list(mod.POST) + list(mod.OUT)
    if len(set(names)) != len(names):
        raise KernelError('PRE, POST and OUT field names must be distinct')
    for n in names + list(mod.REGS):
        if n.startswith(_PREFIXES) or n in ('clk', 'rst_n'):
            raise KernelError(f'reserved field name {n}')
    return mod


# ----------------------------------------------------------------------------
# Translation to Verilog
# ----------------------------------------------------------------------------

_BIN = {ast.Add: '+', ast.Mult: '*', ast.BitAnd: '&', ast.BitOr: '|', ast.BitXor: '^',
        ast.LShift: '<<', ast.RShift: '>>'}
_CMP = {ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=', ast.Gt: '>', ast.GtE: '>='}


class _Fn:
    """One kernel function, translated to the body of an always @* block."""

    def __init__(self, mod: ModuleType, fdef: ast.FunctionDef, kind: str):
        self.mod, self.kind = mod, kind
        want = ['i', 'r', 'o'] if kind == 'decide' else ['i', 'r', 'o', 'n']
        if [a.arg for a in fdef.args.args] != want:
            raise KernelError(f'{kind}() must take ({", ".join(want)})')
        self.prefix = 'd_' if kind == 'decide' else 'u_'
        self.locals: dict[str, bool] = {}
        assigns = [(t.id, s.value) for s in ast.walk(fdef) if isinstance(s, ast.Assign)
                   for t in s.targets if isinstance(t, ast.Name)]
        for name, _ in assigns:
            self.locals[name] = True
        changed = True
        while changed:                  # a local is boolean iff every value assigned to it is
            changed = False
            for name, val in assigns:
                if self.locals[name] and not self.boolean(val):
                    self.locals[name] = False
                    changed = True
        self.lines: list[str] = []
        for s in fdef.body:
            self.stmt(s, '    ')

    def err(self, node, msg):
        raise KernelError(f'{self.kind}() line {getattr(node, "lineno", "?")}: {msg}')

    def width(self, obj: str, name: str) -> int | None:
        m = self.mod
        if obj == 'i':
            w = m.PRE.get(name, m.POST.get(name))
        elif obj == 'r':
            w = m.REGS[name][0] if name in m.REGS else None
        elif obj == 'o':
            w = m.OUT.get(name)
        else:
            w = None
        return w

    def boolean(self, e) -> bool:
        if isinstance(e, (ast.Compare, ast.BoolOp)):
            return True
        if isinstance(e, ast.UnaryOp) and isinstance(e.op, ast.Not):
            return True
        if isinstance(e, ast.Constant):
            return isinstance(e.value, bool) or e.value in (0, 1)
        if isinstance(e, ast.Name):
            if e.id in self.locals:
                return self.locals[e.id]
            return self.mod.__dict__.get(e.id) in (0, 1)
        if isinstance(e, ast.Attribute) and isinstance(e.value, ast.Name):
            return self.width(e.value.id, e.attr) == 1
        if isinstance(e, ast.IfExp):
            return self.boolean(e.body) and self.boolean(e.orelse)
        return False

    def field(self, node: ast.Attribute) -> str:
        if not isinstance(node.value, ast.Name):
            self.err(node, 'only fields of i, r and o can be read')
        obj, name = node.value.id, node.attr
        m = self.mod
        if obj == 'i':
            if name in m.PRE:
                return f'w_{name}'
            if name in m.POST:
                if self.kind == 'decide':
                    self.err(node, f'decide() reads the tool result i.{name}, which exists only after the action runs')
                return f'w_{name}'
        elif obj == 'r' and name in m.REGS:
            return f'w_r_{name}'
        elif obj == 'o' and self.kind == 'update' and name in m.OUT:
            return f'w_{name}'
        self.err(node, f'{obj}.{name} cannot be read in {self.kind}()')

    def ex(self, e) -> str:
        if isinstance(e, ast.Constant):
            if isinstance(e.value, bool):
                return "1'b1" if e.value else "1'b0"
            if isinstance(e.value, int) and e.value >= 0:
                return f"32'd{e.value}"
            self.err(e, f'unsupported constant {e.value!r}')
        if isinstance(e, ast.Name):
            if e.id in self.locals:
                return self.prefix + e.id
            v = self.mod.__dict__.get(e.id)
            if isinstance(v, bool):
                return "1'b1" if v else "1'b0"
            if isinstance(v, int) and v >= 0:
                return f"32'd{v}"
            self.err(e, f'unknown name {e.id} (not a local or a non-negative module constant)')
        if isinstance(e, ast.Attribute):
            return self.field(e)
        if isinstance(e, ast.BinOp):
            op = _BIN.get(type(e.op))
            if op is None:
                self.err(e, f'operator {type(e.op).__name__} is not allowed (no subtraction: values stay non-negative)')
            sides = []
            for x in (e.left, e.right):
                if isinstance(x, ast.UnaryOp) and isinstance(x.op, ast.Invert):
                    if op != '&':
                        self.err(e, '~ is only allowed as an operand of &')
                    sides.append(f'(~{self.ex(x.operand)})')
                else:
                    sides.append(self.ex(x))
            return f'({sides[0]} {op} {sides[1]})'
        if isinstance(e, ast.UnaryOp):
            if isinstance(e.op, ast.Not):
                return f'(!{self.ex(e.operand)})'
            self.err(e, f'unary {type(e.op).__name__} is not allowed')
        if isinstance(e, ast.BoolOp):
            for v in e.values:
                if not self.boolean(v):
                    self.err(v, 'operands of and/or must be boolean (a comparison, a 1-bit field or a boolean local)')
            op = ' && ' if isinstance(e.op, ast.And) else ' || '
            return '(' + op.join(self.ex(v) for v in e.values) + ')'
        if isinstance(e, ast.Compare):
            if len(e.ops) != 1:
                self.err(e, 'chained comparisons are not allowed')
            op = _CMP.get(type(e.ops[0]))
            if op is None:
                self.err(e, f'comparison {type(e.ops[0]).__name__} is not allowed')
            return f'({self.ex(e.left)} {op} {self.ex(e.comparators[0])})'
        if isinstance(e, ast.IfExp):
            return f'({self.ex(e.test)} ? {self.ex(e.body)} : {self.ex(e.orelse)})'
        self.err(e, f'unsupported expression {type(e).__name__}')

    def stmt(self, s, ind: str):
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str):
            return
        if isinstance(s, ast.Pass):
            return
        if isinstance(s, ast.Assign):
            if len(s.targets) != 1:
                self.err(s, 'one target per assignment')
            t, rhs = s.targets[0], self.ex(s.value)
            if isinstance(t, ast.Name):
                self.lines.append(f'{ind}{self.prefix}{t.id} = {rhs};')
                return
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name):
                obj, name = t.value.id, t.attr
                if self.kind == 'decide' and obj == 'o' and name in self.mod.OUT:
                    self.lines.append(f'{ind}{name} = {rhs};')
                    return
                if self.kind == 'update' and obj == 'n' and name in self.mod.REGS:
                    self.lines.append(f'{ind}n_{name} = {rhs};')
                    return
            self.err(s, f'{self.kind}() may only assign locals and ' + ('o.<output>' if self.kind == 'decide' else 'n.<register>'))
        if isinstance(s, ast.If):
            self.lines.append(f'{ind}if ({self.ex(s.test)}) begin')
            for x in s.body:
                self.stmt(x, ind + '  ')
            if s.orelse:
                self.lines.append(f'{ind}end else begin')
                for x in s.orelse:
                    self.stmt(x, ind + '  ')
            self.lines.append(f'{ind}end')
            return
        self.err(s, f'unsupported statement {type(s).__name__}')


def _vw(w: int) -> str:
    return f'[{w - 1}:0] ' if w > 1 else ''


def verilog(mod: ModuleType, top: str = 'scaffold', origin: str = '') -> str:
    """Translate a kernel module to a Verilog-2005 module with ports clk, rst_n
    (synchronous, active low), PRE and POST inputs and OUT outputs."""
    tree = ast.parse(mod.__source__)
    fns = {f.name: f for f in tree.body if isinstance(f, ast.FunctionDef)}
    d = _Fn(mod, fns['decide'], 'decide')
    u = _Fn(mod, fns['update'], 'update')
    ins = {**mod.PRE, **mod.POST}
    ports = ['input wire clk', 'input wire rst_n']
    ports += [f'input wire {_vw(w)}{n}' for n, w in ins.items()]
    ports += [f'output reg {_vw(w)}{n}' for n, w in mod.OUT.items()]
    L = [f'// Generated by fcp.kernel from {origin or mod.__file__}. Do not edit: change the kernel instead.',
         f'module {top} (', '  ' + ',\n  '.join(ports), ');']
    for n, (w, _) in mod.REGS.items():
        L.append(f'  reg {_vw(w)}r_{n};')
        L.append(f'  reg {_vw(w)}n_{n};')
    for n in list(ins) + list(mod.OUT):
        L.append(f'  wire [31:0] w_{n} = {n};')
    for n in mod.REGS:
        L.append(f'  wire [31:0] w_r_{n} = r_{n};')
    for f in (d, u):
        for n in f.locals:
            L.append(f'  reg [31:0] {f.prefix}{n};')
    L.append('  // decide(): what executes this turn')
    L.append('  always @* begin')
    L += [f'    {n} = {w}\'d0;' for n, w in mod.OUT.items()]
    L += [f'    d_{n} = 32\'d0;' for n in d.locals]
    L += d.lines
    L.append('  end')
    L.append('  // update(): the state after the tool ran')
    L.append('  always @* begin')
    L += [f'    n_{n} = r_{n};' for n in mod.REGS]
    L += [f'    u_{n} = 32\'d0;' for n in u.locals]
    L += u.lines
    L.append('  end')
    L.append('  always @(posedge clk) begin')
    L.append('    if (!rst_n) begin')
    L += [f"      r_{n} <= {w}'d{v & _mask(w)};" for n, (w, v) in mod.REGS.items()]
    L.append('    end else begin')
    L += [f'      r_{n} <= n_{n};' for n in mod.REGS]
    L.append('    end')
    L.append('  end')
    L.append('endmodule')
    return '\n'.join(L) + '\n'


# ----------------------------------------------------------------------------
# Python runtime: the same functions, executed in the agent loop
# ----------------------------------------------------------------------------

class _Ro:
    """Read-only field namespace."""

    def __init__(self, vals: dict, name: str):
        object.__setattr__(self, '_v', vals)
        object.__setattr__(self, '_n', name)

    def __getattr__(self, k):
        try:
            return self._v[k]
        except KeyError:
            raise KernelError(f'{self._n}.{k} is not readable here') from None

    def __setattr__(self, k, v):
        raise KernelError(f'{self._n} is read-only')


class _Wo:
    """Write-only field namespace; writes are truncated to the field width,
    exactly as a Verilog assignment truncates."""

    def __init__(self, widths: dict, init: dict, name: str):
        object.__setattr__(self, '_w', widths)
        object.__setattr__(self, '_v', dict(init))
        object.__setattr__(self, '_n', name)

    def __getattr__(self, k):
        raise KernelError(f'{self._n} is write-only: {self._n}.{k} cannot be read')

    def __setattr__(self, k, v):
        if k not in self._w:
            raise KernelError(f'{self._n}.{k} is not a field')
        self._v[k] = int(v) & _mask(self._w[k])


class Runtime:
    """Executes a kernel turn by turn: decide() before the tool runs, update()
    after it has returned its result."""

    def __init__(self, mod: ModuleType):
        self.mod = mod
        self.reset()

    def reset(self):
        self.r = {k: v & _mask(w) for k, (w, v) in self.mod.REGS.items()}

    def _inputs(self, vals: dict, fields: dict) -> dict:
        miss = set(fields) - set(vals)
        if miss:
            raise KernelError(f'missing inputs {sorted(miss)}')
        return {k: int(vals[k]) & _mask(w) for k, w in fields.items()}

    def decide(self, pre: dict) -> dict:
        i = _Ro(self._inputs(pre, self.mod.PRE), 'i')
        o = _Wo(self.mod.OUT, {k: 0 for k in self.mod.OUT}, 'o')
        self.mod.decide(i, _Ro(dict(self.r), 'r'), o)
        return dict(o._v)

    def update(self, pre: dict, post: dict, out: dict):
        i = _Ro({**self._inputs(pre, self.mod.PRE), **self._inputs(post, self.mod.POST)}, 'i')
        n = _Wo({k: w for k, (w, _) in self.mod.REGS.items()}, self.r, 'n')
        self.mod.update(i, _Ro(dict(self.r), 'r'), _Ro(dict(out), 'o'), n)
        self.r = dict(n._v)

    def turn(self, pre: dict, post: dict) -> dict:
        out = self.decide(pre)
        self.update(pre, post, out)
        return out


# ----------------------------------------------------------------------------
# Co-simulation: Python runtime vs. the generated Verilog
# ----------------------------------------------------------------------------

def _rand_value(rng: random.Random, w: int, special: list[int]) -> int:
    x = rng.random()
    if x < 0.3 and special:
        return rng.choice(special) & _mask(w)
    if x < 0.45:
        return rng.choice([0, 1, _mask(w)])
    return rng.randrange(1 << w)


def cosim(mod: ModuleType, top: str = 'scaffold', runs: int = 40, turns: int = 30, seed: int = 1,
          special: dict | None = None, bias: dict | None = None, weights: dict | None = None,
          sticky: dict | None = None) -> dict:
    """Drive the Python runtime and an Icarus simulation of verilog(mod) with
    the same random turns; report the first disagreement, if any.

    special: {field: [interesting values]}; bias: {field: probability of 1}
    for 1-bit fields (e.g. keep a rare button rare so runs get deep);
    weights: {field: {value: weight}} for a field drawn from a fixed menu;
    sticky: {field: probability of repeating the previous turn's value}."""
    rng = random.Random(seed)
    special, bias, weights, sticky = special or {}, bias or {}, weights or {}, sticky or {}
    ins = {**mod.PRE, **mod.POST}
    seqs = []
    for _ in range(runs):
        seq = []
        for _ in range(turns):
            t = {}
            for n, w in ins.items():
                if seq and rng.random() < sticky.get(n, 0):
                    t[n] = seq[-1][n]
                elif n in weights:
                    vals = list(weights[n])
                    t[n] = rng.choices(vals, [weights[n][v] for v in vals])[0] & _mask(w)
                elif w == 1 and n in bias:
                    t[n] = int(rng.random() < bias[n])
                else:
                    t[n] = _rand_value(rng, w, special.get(n, []))
            seq.append(t)
        seqs.append(seq)
    py = []
    for seq in seqs:
        rt = Runtime(mod)
        py.append([rt.turn({k: t[k] for k in mod.PRE}, {k: t[k] for k in mod.POST}) for t in seq])
    outs = list(mod.OUT)
    tb = ['`timescale 1ns/1ps', 'module fcp_cosim;', "  reg clk = 1'b0;", "  reg rst_n = 1'b0;"]
    tb += [f'  reg {_vw(w)}{n};' for n, w in ins.items()]
    tb += [f'  wire {_vw(w)}{n};' for n, w in mod.OUT.items()]
    tb.append(f'  {top} dut (.clk(clk), .rst_n(rst_n), ' +
              ', '.join(f'.{n}({n})' for n in list(ins) + outs) + ');')
    tb.append('  initial begin')
    fmt = ' '.join('%0d' for _ in outs)
    for r, seq in enumerate(seqs):
        tb.append("    rst_n = 1'b0; #1; #4 clk = 1'b1; #5 clk = 1'b0; rst_n = 1'b1;")
        for k, t in enumerate(seq):
            tb.append('    ' + ' '.join(f'{n} = {v};' for n, v in t.items()) + ' #1;')
            tb.append(f'    $display("T {r} {k} {fmt}", {", ".join(outs)});')
            tb.append("    #4 clk = 1'b1; #5 clk = 1'b0;")
    tb += ['    $finish;', '  end', 'endmodule']
    with tempfile.TemporaryDirectory(prefix='fcp_cosim_') as d:
        with open(os.path.join(d, 'k.v'), 'w') as f:
            f.write(verilog(mod, top))
        with open(os.path.join(d, 'tb.v'), 'w') as f:
            f.write('\n'.join(tb) + '\n')
        subprocess.run([IVERILOG, '-g2005', '-o', os.path.join(d, 'sim'), os.path.join(d, 'k.v'),
                        os.path.join(d, 'tb.v')], check=True, capture_output=True, text=True)
        res = subprocess.run([VVP, os.path.join(d, 'sim')], check=True, capture_output=True, text=True)
    sim = {}
    for line in res.stdout.splitlines():
        if line.startswith('T '):
            p = line.split()
            sim[(int(p[1]), int(p[2]))] = dict(zip(outs, map(int, p[3:])))
    fired = {n: 0 for n in outs}
    for r, seq in enumerate(seqs):
        for k in range(len(seq)):
            v = sim.get((r, k))
            if v != py[r][k]:
                return {'agree': False, 'run': r, 'turn': k, 'inputs': seqs[r][: k + 1],
                        'python': py[r][k], 'verilog': v}
            for n in outs:
                fired[n] += bool(v[n])
    return {'agree': True, 'turns': runs * turns, 'nonzero': fired}
