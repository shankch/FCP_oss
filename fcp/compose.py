"""Compositional (assume-guarantee) reasoning across block boundaries.

A sub-block with its own FCP contract (assumptions A_c, guarantees G_c) is
replaced inside the parent RTL by a generated *contract stub* with the same
module name and ports:

  obligation   the stub wraps the real sub-block and ASSERTS A_c on the
               boundary signals: does the parent honour the child's contract?
               A failure is an integration defect even when every end-to-end
               property of the parent holds (a latent bug).
  abstraction  the stub has free outputs constrained by ASSUMING the
               deterministic forms of G_c: parent properties are then proved
               against the contract instead of the implementation.

Sound use of the abstraction requires the obligation proofs as well (the
standard non-circular assume-guarantee rule for safety properties).
"""
from __future__ import annotations

import os
import re

from .harness import vw
from .ir import Bundle, RtlVariant, load_bundle
from .monitor import build_monitor


def stub_text(child: Bundle, mon, mode: str, only_assumption: str | None = None) -> str:
    iface = child.iface
    mod = child.rtl['ref'].top
    ports = []
    for s in iface.signals:
        d = 'input' if s.dir == 'in' else 'output'
        ports.append(f'{d} wire {vw(s.width)}{s.name}')
    lines = [f'// FCP contract stub for {mod} ({mode}). Generated.', f'module {mod} (' + ', '.join(ports) + ');']
    if mode == 'obligation':
        conn = ', '.join(f'.{s.name}({s.name})' for s in iface.signals)
        lines.append(f'  {mod}__impl impl ({conn});')
    else:
        for s in iface.outputs:
            lines.append(f'  (* anyseq *) reg {vw(s.width)}{s.name}__free;')
            lines.append(f'  assign {s.name} = {s.name}__free;')
    conns = [f'.clk({iface.clock})']
    for name, w in mon.ports_in:
        conns.append(f'.{name}({name})')
    for port, w, lo, hi in mon.rigid_ports:
        lines.append(f'  reg signed [{w - 1}:0] c_{port};')
        lines.append(f'  always @(posedge {iface.clock}) c_{port} <= c_{port};')
        conns.append(f'.{port}(c_{port})')
    for port, w in mon.nondet_ports:
        lines.append(f'  (* anyseq *) reg {vw(w)}c_{port};')
        conns.append(f'.{port}(c_{port})')
    for o in mon.outputs:
        lines.append(f'  wire c_{o};')
        conns.append(f'.{o}(c_{o})')
    lines.append(f'  {mon.module} cmon (' + ', '.join(conns) + ');')
    lines.append('  always @* begin')
    for port, w, lo, hi in mon.rigid_ports:
        lines.append(f'    assume((c_{port} >= {lo}) && (c_{port} <= {hi}));')
    for it in mon.items.values():
        if it.role == 'assumption' and (only_assumption in (None, it.id)):
            lines.append(f'    assert(c_{it.out["aok"]});   // child assumption {it.id}')
        if mode == 'abstraction' and it.role == 'property' and 'okd' in it.out:
            lines.append(f'    assume(c_{it.out["okd"]});   // child guarantee {it.id}')
    lines.append('  end')
    lines.append('endmodule')
    return '\n'.join(lines) + '\n'


def renamed_impl(child: Bundle, dest_dir: str) -> list[str]:
    """Copy the child's RTL with its top module renamed to <top>__impl."""
    top = child.rtl['ref'].top
    out = []
    os.makedirs(dest_dir, exist_ok=True)
    for f in child.rtl['ref'].files:
        with open(child.path(f)) as fh:
            txt = fh.read()
        txt = re.sub(rf'\bmodule\s+{re.escape(top)}\b', f'module {top}__impl', txt)
        p = os.path.join(dest_dir, os.path.basename(f).replace('.v', '__impl.v'))
        with open(p, 'w') as fh:
            fh.write(txt)
        out.append(p)
    return out


def contract_variants(S, parent_variant: str, child_root: str, child_set: str, child_file_in_parent: str,
                      workdir: str):
    """Build parent RTL variants with the child replaced by its contract stub.

    Returns (obligation_variants: {assumption_id: RtlVariant}, abstraction_variant, child_monitor)."""
    child = load_bundle(child_root, sets=[child_set])
    mon = build_monitor(child.iface, child.fsets[child_set], f'fcp_cmon_{child.design}_{child_set}')
    pv = S.variant(parent_variant)
    os.makedirs(workdir, exist_ok=True)
    mon_path = os.path.join(workdir, f'{mon.module}.v')
    with open(mon_path, 'w') as f:
        f.write(mon.text)
    keep = [S.b.path(f) for f in pv.files if os.path.basename(f) != os.path.basename(child_file_in_parent)]
    impl = renamed_impl(child, workdir)
    obls = {}
    for it in mon.items.values():
        if it.role != 'assumption':
            continue
        p = os.path.join(workdir, f'stub_obl_{it.id}.v')
        with open(p, 'w') as f:
            f.write(stub_text(child, mon, 'obligation', it.id))
        obls[it.id] = RtlVariant(f'{parent_variant}+obl:{it.id}', pv.top, keep + impl + [p, mon_path],
                                 pv.params, pv.port_map)
    p = os.path.join(workdir, 'stub_abs.v')
    with open(p, 'w') as f:
        f.write(stub_text(child, mon, 'abstraction', only_assumption='__none__'))
    absv = RtlVariant(f'{parent_variant}+abs', pv.top, keep + [p, mon_path], pv.params, pv.port_map)
    return obls, absv, mon


def check(S, s: str, parent_variant: str, child_root: str, child_set: str, child_file: str, workdir: str) -> dict:
    """Obligation proofs for every child assumption, and parent properties proved
    against the child's contract (abstraction)."""
    obls, absv, mon = contract_variants(S, parent_variant, child_root, child_set, child_file, workdir)
    tasks = []
    for aid, v in obls.items():
        hb = S.rtl_hb(s, v)
        tasks.append(S.task(f'obl:{aid}', 'prove', hb, [s], v, engine='pdr'))
    for it in S.props(s):
        hb = S.rtl_hb(s, absv)
        hb.asserts.append(f"mon_{it.out['ok']}")
        tasks.append(S.task(f'abs:{it.id}', 'prove', hb, [s], absv, engine='pdr'))
    R = S.run(tasks)
    out = {'obligations': {}, 'abstraction': {}}
    for aid in obls:
        r = R[f'obl:{aid}']
        out['obligations'][aid] = {'status': r.status, 'seconds': r.seconds, 'trace': r.trace,
                                   'english': mon.items[aid].english}
    for it in S.props(s):
        r = R[f'abs:{it.id}']
        out['abstraction'][it.id] = {'status': r.status, 'seconds': r.seconds}
    return out
