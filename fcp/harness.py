"""Harness generation: wire designs and monitors together for each analysis.

The same builder emits a *formal* harness (with assume/assert/cover) and a
*simulation* harness with an identical hierarchy and no formal statements, so
counterexamples found by the solvers can be replayed in an independent
simulator (Icarus Verilog) with the same instance paths.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from .ir import Bundle, RtlVariant, Signal, rtl_param_values
from .lang import seq_len_port
from .monitor import Monitor


# The wire of a harness that says its free signals carry values a run can
# produce (HarnessBuilder.canonical_outcome).  A formal run assumes it.  The
# solver model of a harness is read without its assumptions, so every
# unrolling of one asserts the wire (SmtModel.unroll).
ENV_OK = 'fcp_env_ok'


def vw(w: int) -> str:
    return f'[{w - 1}:0] ' if w > 1 else ''


class HarnessBuilder:
    def __init__(self, b: Bundle, name: str = 'fcp_harness'):
        self.b = b
        self.name = name
        self.inputs: list[tuple[str, int]] = [('clk', 1)]
        self.wires: list[tuple[str, int]] = []
        self.regs: list[str] = []
        self.body: list[str] = []
        self.assumes: list[str] = []
        self.asserts: list[str] = []
        self.covers: list[str] = []
        self.monitors: dict[str, Monitor] = {}
        self.rigid_regs: list[tuple[str, int, int, int]] = []
        self._names = {'clk'}
        r = b.iface.reset
        self.rst = f'!{r.name}' if r.active_low else r.name
        self._ndelay = 0

    def free(self, name: str, width: int):
        if name not in self._names:
            self.inputs.append((name, width))
            self._names.add(name)

    def wire(self, name: str, width: int):
        if name not in self._names:
            self.wires.append((name, width))
            self._names.add(name)

    def interface_free(self, outputs_too: bool, suffix_out: str = ''):
        for s in self.b.iface.signals:
            if s.name == self.b.iface.clock:
                continue
            if s.dir == 'in' or outputs_too:
                self.free(s.name + (suffix_out if s.dir == 'out' else ''), s.width)

    def dut(self, inst: str, v: RtlVariant, module: Optional[str] = None, out_suffix: str = '',
            in_rename: Optional[dict] = None):
        """Instantiate an RTL variant; its outputs drive wires <signal><out_suffix>."""
        iface = self.b.iface
        params = rtl_param_values(self.b, v)
        ptxt = ', '.join(f'.{k}({val})' for k, val in params.items())
        conns = []
        for s in iface.signals:
            port = v.port_map.get(s.name, s.name)
            if s.name == iface.clock:
                conns.append(f'.{port}(clk)')
            elif s.dir == 'in':
                conns.append(f'.{port}({(in_rename or {}).get(s.name, s.name)})')
            else:
                w = s.name + out_suffix
                self.wire(w, s.width)
                conns.append(f'.{port}({w})')
        mod = module or v.top
        self.body.append(f'  {mod} {"#(" + ptxt + ") " if ptxt else ""}{inst} (' + ', '.join(conns) + ');')

    def monitor(self, inst: str, mon: Monitor, rename: Optional[dict] = None):
        """Instantiate a monitor; its outputs become wires <inst>_<port>."""
        rename = rename or {}
        self.monitors[inst] = mon
        conns = ['.clk(clk)']
        for name, w in mon.ports_in:
            conns.append(f'.{name}({rename.get(name, name)})')
        for port, w, lo, hi in mon.rigid_ports:
            r = f'{inst}_{port}'
            self.regs.append(f'  reg signed [{w - 1}:0] {r};  // rigid variable: arbitrary but constant')
            self.body.append(f'  always @(posedge clk) {r} <= {r};')
            self.rigid_regs.append((r, w, lo, hi))
            conns.append(f'.{port}({r})')
        for port, w in mon.nondet_ports:
            n = f'{inst}_{port}'
            self.free(n, w)
            conns.append(f'.{port}({n})')
        for o in mon.outputs:
            n = f'{inst}_{o}'
            self.wire(n, 1)
            conns.append(f'.{o}({n})')
        self.body.append(f'  {mon.module} {inst} (' + ', '.join(conns) + ');')

    def delayed(self, expr: str, n: int) -> str:
        """Harness register chain: expr as it was n cycles ago (0 before that)."""
        self._ndelay += 1
        cur = f'({expr})'
        for i in range(n):
            r = f'fcp_dl{self._ndelay}_{i}'
            self.regs.append(f'  reg {r} = 1\'b0;')
            self.body.append(f'  always @(posedge clk) {r} <= {cur};')
            cur = r
        return cur

    def no_later_reset(self):
        self.assumes.append(f'fcp_init || !({self.rst})')

    def std_env(self, rst_expr: Optional[str] = None):
        """Standard environment: reset in cycle 0, optional later resets, rigid domains."""
        env = self.b.env
        r = self.b.iface.reset
        rst = rst_expr or (f'!{r.name}' if r.active_low else r.name)
        if env.get('initial_reset', True):
            self.assumes.append(f'fcp_init ? ({rst}) : 1\'b1')
        if not env.get('reset_anytime', True):
            self.assumes.append(f'fcp_init || !({rst})')
        for reg, w, lo, hi in self.rigid_regs:
            self.assumes.append(f'({reg} >= {lo}) && ({reg} <= {hi})')
        self.canonical()
        self.canonical_calls()
        self.canonical_outcome()

    def canonical_outcome(self):
        """The outcome signal of a function says how a call ended: 0 it
        returned, one code per exception the request names, then "another
        exception or no answer" and "returned something else" (software.Fn).
        A signal wide enough for these can have codes left over, which no
        call produces.  Left free, such a code is an ending on which two
        readings can differ, and one that keeps rules that contradict each
        other satisfiable.  So every free copy of the signal, and of the one
        that carries the ending of the code before a change, stays within
        the codes that name an ending."""
        f = (getattr(self.b, 'raw_design', None) or {}).get('function') or {}
        oc = f.get('outcome') or {}
        if not oc.get('signal') or ENV_OK in self._names:
            return
        top = 2 + len(oc.get('raises') or [])
        sigs = [oc['signal']] + [x for x in [(f.get('baseline') or {}).get('outcome')] if x]
        conds = [f"({n} <= {w}'d{top})" for n, w in sorted(self.inputs)
                 if any(n == s or n.startswith(s + '__') for s in sigs) and (1 << w) - 1 > top]
        if conds:
            self.wire(ENV_OK, 1)
            self.body.append(f'  assign {ENV_OK} = ' + ' && '.join(conds) + ';')
            self.assumes.append(ENV_OK)

    def canonical_calls(self):
        """An object with several methods (function.methods): every call is a
        call of one of them (op), and the arguments that method does not take
        are 0, as the adapter drives them."""
        f = (getattr(self.b, 'raw_design', None) or {}).get('function') or {}
        if not f.get('methods'):
            return
        names = {n for n, _ in self.inputs}
        op = f['op']['signal']
        if op not in names:
            return
        w = self.b.iface.sig(op).width
        seqs = getattr(self.b.iface, 'seqs', {}) or {}
        self.assumes.append(' || '.join(f"({op} == {w}'d{int(m['op'])})" for m in f['methods']))
        argsigs = list(dict.fromkeys(a.get('signal', a['name']) for m in f['methods'] for a in m.get('args') or []))
        for m in f['methods']:
            used = {a.get('signal', a['name']) for a in m.get('args') or []}
            for sg in argsigs:
                for p in ([sg, seq_len_port(sg)] if sg in seqs else [sg]) if sg not in used else []:
                    if p in names:
                        self.assumes.append(f"({op} != {w}'d{int(m['op'])}) || ({p} == {self.b.iface.sig(p).width}'d0)")

    def canonical(self):
        """Every free sequence signal (and every renamed copy of one) in
        canonical form: its length at most n and every slot beyond the length
        zero, so that two equal values are equal ports.  Monitors ignore what
        a port carries beyond the length; without this, a spec-only witness
        could differ only there."""
        names = {n for n, _ in self.inputs}
        for seq, (w, n) in (getattr(self.b.iface, 'seqs', {}) or {}).items():
            ln = seq_len_port(seq)
            for data in sorted(x for x in names if x.startswith(seq)):
                suf = data[len(seq):]
                if ln + suf not in names or (suf and not suf.startswith('__')) or data == ln + suf:
                    continue
                lw = self.b.iface.sig(ln).width
                if (1 << lw) - 1 > n:
                    self.assumes.append(f"{ln}{suf} <= {lw}'d{n}")
                for k in range(n):
                    self.assumes.append(f"({ln}{suf} > {lw}'d{k}) || ({data}[{k * w + w - 1}:{k * w}] == {w}'d0)")
        # the fields of a list of records: one length
        for members in (getattr(self.b.iface, 'groups', {}) or {}).values():
            first = seq_len_port(members[0])
            for x in sorted(x for x in names if x.startswith(first)):
                suf = x[len(first):]
                if suf and not suf.startswith('__'):
                    continue
                for m in members[1:]:
                    if seq_len_port(m) + suf in names:
                        self.assumes.append(f'{first}{suf} == {seq_len_port(m)}{suf}')

    def text(self, formal: bool = True) -> str:
        ports = ', '.join(f'input {vw(w)}{n}' for n, w in self.inputs)
        out = [f'// Generated by FCP. {"Formal" if formal else "Simulation"} harness.',
               f'module {self.name} ({ports});']
        for n, w in self.wires:
            out.append(f'  (* keep *) wire {vw(w)}{n};')
        out += self.regs
        out.append('  reg fcp_init = 1\'b1;')
        out.append('  always @(posedge clk) fcp_init <= 1\'b0;')
        out.append('  reg [7:0] fcp_cnt = 8\'d0;  // trace length so far')
        out.append('  always @(posedge clk) if (fcp_cnt != 8\'d255) fcp_cnt <= fcp_cnt + 8\'d1;')
        out += self.body
        if formal:
            out.append('  always @* begin')
            for a in self.assumes:
                out.append(f'    assume({a});')
            for a in self.asserts:
                out.append(f'    assert({a});')
            for c in self.covers:
                out.append(f'    cover({c});')
            out.append('  end')
        out.append('endmodule')
        return '\n'.join(out) + '\n'


# ----------------------------------------------------------------------------
# Simulation replay of a solver trace
# ----------------------------------------------------------------------------

def replay_tb(hb: HarnessBuilder, witness: dict, probe: list[str]) -> str:
    """Testbench that drives the simulation harness with a witness' inputs and
    initial register values and prints the probed signals at every step."""
    steps = witness['steps']
    init = steps[0] if steps else {}
    sig_meta = {'.'.join(p.lstrip('\\') for p in s['path']): s for s in witness['signals']}
    lines = ['`timescale 1ns/1ps', 'module fcp_tb;', '  reg clk = 1\'b0;']
    for n, w in hb.inputs:
        if n != 'clk':
            lines.append(f'  reg {vw(w)}{n};')
    lines.append(f'  {hb.name} h (' + ', '.join(f'.{n}({n})' for n, _ in hb.inputs) + ');')
    lines.append('  initial begin')
    for path, meta in sig_meta.items():
        if meta.get('init_only') and init.get(path) is not None:
            hp = '.'.join(_vlog_path_part(p) for p in path.split('.'))
            lines.append(f"    h.{hp} = {meta['width']}'d{init[path]};")
    in_names = [n for n, _ in hb.inputs if n != 'clk']
    for k, st in enumerate(steps):
        for n in in_names:
            v = st.get(n)
            if v is not None:
                lines.append(f'    {n} = {v};')
        lines.append('    #1;')
        fmt = ' '.join(f'{p}=%0d' for p in probe)
        args = ', '.join(f'h.{p}' for p in probe)
        lines.append(f'    $display("STEP {k} {fmt}", {args});')
        lines.append('    #4 clk = 1\'b1; #5 clk = 1\'b0;')
    lines.append('    $finish;')
    lines.append('  end')
    lines.append('endmodule')
    return '\n'.join(lines) + '\n'


def _vlog_path_part(p: str) -> str:
    import re
    # memories mapped to registers appear as "mem[3]": address the array word
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*\[\d+\]', p):
        return p
    if all(c.isalnum() or c == '_' for c in p) and not p[0].isdigit():
        return p
    return '\\' + p + ' '
