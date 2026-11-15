"""Compile the scaffold kernels to RTL and check each translation by co-simulation.

  rtl/ref.v     scaffold/desk.py   (the guarded scaffold)
  rtl/naive.v   scaffold/naive.py  (pass-through ReAct loop)
  bugs/G*.v     scaffold/desk.py with the textual patches of bugs/bugs.yaml
"""
from __future__ import annotations

import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from fcp import kernel as K  # noqa: E402

# Proposal streams that reach deep states: few endings, arguments that repeat.
DRIVE = dict(runs=200, turns=30, seed=11,
             weights={'p_act': {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 0.15, 7: 0.3},
                      'p_amt': {0: 1, 40: 3, 120: 3, 150: 2, 151: 1, 200: 1},
                      'total': {40: 2, 120: 3, 150: 2, 200: 2, 300: 1}},
             sticky={'p_ord': 0.8, 'p_amt': 0.7},
             bias={'human': 0.03, 'p_more': 0.3, 'id_ok': 0.6, 'elig': 0.7, 'accepted': 0.7})


def kernels() -> dict:
    """variant -> (kernel source file, patches)"""
    out = {'ref': ('scaffold/desk.py', []), 'naive': ('scaffold/naive.py', [])}
    with open(os.path.join(HERE, 'bugs', 'bugs.yaml')) as f:
        for b in yaml.safe_load(f)['bugs']:
            out[b['id']] = ('scaffold/desk.py', [tuple(p) for p in b['patch']])
    return out


def build(check: bool = True) -> dict:
    res = {}
    for v, (src, patches) in kernels().items():
        mod = K.load(os.path.join(HERE, src), patches, name=v)
        dst = f'rtl/{v}.v' if v in ('ref', 'naive') else f'bugs/{v}.v'
        note = src + (f' + {len(patches)} patch(es) from bugs/bugs.yaml ({v})' if patches else '')
        with open(os.path.join(HERE, dst), 'w') as f:
            f.write(K.verilog(mod, 'scaffold', origin=note))
        res[v] = K.cosim(mod, **DRIVE) if check else None
        if check:
            r = res[v]
            print(f'{v:6s} -> {dst:12s} cosim: ' + (f"agree on {r['turns']} turns, refunds run {r['nonzero']['refund']}"
                                                    if r['agree'] else f'DISAGREE {r}'))
    return res


if __name__ == '__main__':
    build()
