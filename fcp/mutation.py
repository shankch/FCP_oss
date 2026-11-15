"""Mutation-based assurance coverage.

A proof is only as good as the properties proved.  We measure how much of the
design's *observable* behaviour the proved properties pin down:

  1. sample N netlist mutations (yosys `mutate`: bit inversions, stuck-at,
     conditional inversions), each tied to RTL source lines;
  2. observability: a miter between the original and the mutant under the
     environment assumptions (outputs compared outside reset, modulo declared
     don't-cares).  Proved equal => equivalent mutant, excluded;
  3. kill: every property is checked on each observable mutant.

  assurance coverage = killed / observable.

An observable mutant that no property kills is concrete evidence of a gap: a
behaviour change that no formalized requirement constrains (a missing
requirement, a too-weak formalization, or intentionally free behaviour).
The kill matrix also links requirements to the RTL lines they constrain.
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import re

from .engine import run_yosys
from .ir import Bundle, RtlVariant, rtl_param_values, sha256_file


def _prep_script(b: Bundle, v: RtlVariant) -> str:
    files = ' '.join(os.path.abspath(b.path(f)) for f in v.files)
    params = rtl_param_values(b, v)
    chp = ' '.join(f'-set {k} {val}' for k, val in params.items())
    return '; '.join([f'read -formal {files}'] + ([f'chparam {chp} {v.top}'] if chp else []) +
                     [f'prep -top {v.top}', 'flatten', 'memory_map', 'opt_clean'])


def gen_mutants(b: Bundle, v: RtlVariant, n: int, seed: int, workdir: str) -> list[dict]:
    os.makedirs(workdir, exist_ok=True)
    h = hashlib.sha256(json.dumps([[sha256_file(b.path(f)) for f in v.files], rtl_param_values(b, v),
                                   n, seed, v.top]).encode()).hexdigest()[:16]
    d = os.path.join(workdir, f'mutants_{h}')
    idx = os.path.join(d, 'mutants.json')
    if os.path.exists(idx):
        with open(idx) as f:
            return json.load(f)
    os.makedirs(d, exist_ok=True)
    prep = _prep_script(b, v)
    run_yosys(prep + f'; mutate -list {n} -seed {seed} -o mutations.txt', d)
    with open(os.path.join(d, 'mutations.txt')) as f:
        cmds = [l.strip() for l in f if l.startswith('mutate ')]

    def make(i_cmd):
        i, cmd = i_cmd
        mod = f'{v.top}__m{i}'
        out = os.path.join(d, f'm{i}.v')
        run_yosys(prep + f'; {cmd}; rename {v.top} {mod}; write_verilog -noattr {out}', d)
        lines = sorted({int(x) for x in re.findall(r'-src \S+?:(\d+)\.', cmd)})
        files = sorted({x for x in re.findall(r'-src (\S+?):\d+\.', cmd)})
        mode = re.search(r'-mode (\S+)', cmd).group(1)
        wire = re.search(r'-wire (\S+)', cmd)
        return {'id': f'M{i}', 'module': mod, 'file': out, 'cmd': cmd, 'mode': mode,
                'src_lines': lines, 'src_files': files, 'wire': wire.group(1) if wire else None}

    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        muts = list(ex.map(make, enumerate(cmds)))
    with open(idx, 'w') as f:
        json.dump(muts, f, indent=1)
    return muts
