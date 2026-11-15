"""Runtime verification: check one recorded trace against a reading.

A proof covers every behaviour of an RTL variant; a recorded trace (a run of
an agent, a simulation dump) is one behaviour.  Checking it needs no solver:
the compiled monitor of the reading is simulated on the trace (Icarus), and
for every item the first cycle at which its deterministic form fails is
reported.  Rigid variables are replayed over their whole range, so a
property fails if it fails for any value.  A contract item on a cut point
(fcp.agent) reports the first turn at which the component, the model, broke
its contract.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
from typing import Optional

from .agents import IVERILOG
from .harness import vw
from .kernel import VVP


MAX_CASES = 4096            # combinations of rigid values that a replay runs through, unless a caller gives its own


class NotReplayed(ValueError):
    """A trace that `check` did not run to its end: the reading has more rigid
    cases than max_cases, or the simulation passed its time."""


def check(S, s: str, trace: list[dict], max_cases: int = MAX_CASES, valuations: bool = False,
          timeout: Optional[float] = None) -> dict:
    """trace: one dict per cycle with a value for every monitor input (cycle 0
    is reset).  Returns {item id: first failing cycle, or None}; with
    valuations=True, {item id: (cycle, {rigid: value}) or None}.  timeout:
    seconds for the compile and the simulation together.  NotReplayed (a
    ValueError) where the rigid cases exceed max_cases or the time is passed."""
    mon = S.mon(s)
    probes = []
    for it in mon.items.values():
        if it.role == 'property':
            # with rigid ports driven over their whole range, ok is exact as well
            probes.append((it.id, it.out['ok'] if mon.rigid_ports else (it.out.get('okd') or it.out['ok'])))
        elif it.role == 'assumption':
            probes.append((it.id, it.out['aok']))
    rig = mon.rigid_ports
    cases = 1
    for _, _, lo, hi in rig:
        cases *= hi - lo + 1
    if cases > max_cases:
        raise NotReplayed(f'{s}: {cases} rigid cases exceed max_cases={max_cases}')
    tb = ['`timescale 1ns/1ps', 'module fcp_rv;', "  reg clk = 1'b0;"]
    conns = ['.clk(clk)']
    for n, w in mon.ports_in:
        tb.append(f'  reg {vw(w)}{n};')
        conns.append(f'.{n}({n})')
    for port, w, lo, hi in rig:
        # every rigid value is replayed: the property must hold for all of them
        tb.append(f'  reg signed [{w - 1}:0] rg_{port};')
        tb.append(f'  integer i_{port};')
        conns.append(f'.{port}(rg_{port})')
    for port, w in mon.nondet_ports:
        conns.append(f".{port}({w}'d0)")
    for o in mon.outputs:
        tb.append(f'  wire {o};')
        conns.append(f'.{o}({o})')
    tb.append(f'  {mon.module} m (' + ', '.join(conns) + ');')
    fmt = ' '.join('%0d' for _ in probes)
    tb.append('  task replay;')
    tb.append('    begin')
    for k, st in enumerate(trace):
        tb.append('      ' + ' '.join(f"{n} = {w}'h{int(st.get(n, 0)):x};" for n, w in mon.ports_in) + ' #1;')
        tb.append(f'      $display("C {k}{" %0d" * len(rig)} {fmt}"{"".join(f", rg_{p}" for p, _, _, _ in rig)}, '
                  f'{", ".join(w for _, w in probes)});')
        tb.append("      #4 clk = 1'b1; #5 clk = 1'b0;")
    tb += ['    end', '  endtask', '  initial begin']
    ind = '    '
    for port, w, lo, hi in rig:
        tb.append(f'{ind}for (i_{port} = {lo}; i_{port} <= {hi}; i_{port} = i_{port} + 1) begin')
        ind += '  '
        tb.append(f'{ind}rg_{port} = i_{port};')
    tb.append(f'{ind}replay;')
    for _ in rig:
        ind = ind[:-2]
        tb.append(f'{ind}end')
    tb += ['    $finish;', '  end', 'endmodule']
    with tempfile.TemporaryDirectory(prefix='fcp_rv_') as d:
        with open(os.path.join(d, 'mon.v'), 'w') as f:
            f.write(mon.text)
        with open(os.path.join(d, 'tb.v'), 'w') as f:
            f.write('\n'.join(tb) + '\n')
        t0 = time.time()
        try:
            subprocess.run([IVERILOG, '-g2005', '-o', os.path.join(d, 'sim'), os.path.join(d, 'mon.v'),
                            os.path.join(d, 'tb.v')], check=True, capture_output=True, text=True, timeout=timeout)
            res = subprocess.run([VVP, os.path.join(d, 'sim')], check=True, capture_output=True, text=True,
                                 timeout=None if timeout is None else max(0.05, timeout - (time.time() - t0)))
        except subprocess.TimeoutExpired:
            raise NotReplayed(f'{s}: the replay did not end in {timeout:.3g} s') from None
    first = {i: None for i, _ in probes}
    names = [p[3:] for p, _, _, _ in rig]
    for line in res.stdout.splitlines():
        if not line.startswith('C '):
            continue
        p = line.split()
        k = int(p[1])
        val = dict(zip(names, map(int, p[2:2 + len(rig)])))
        for (i, _), v in zip(probes, p[2 + len(rig):]):
            if v != '1' and (first[i] is None or k < first[i][0]):
                first[i] = (k, val)
    return first if valuations else {i: (x[0] if x else None) for i, x in first.items()}
