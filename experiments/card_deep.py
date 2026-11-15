"""The gift-card verdicts the induction left PROVED-BOUNDED: are they true
beyond the bound?

    python experiments/card_deep.py

experiments/prove_demo.py code_card proves 182 of the 186 passing verdicts
for sequences of every length and leaves four as bounded proofs (no
sequence of up to 10 calls breaks them, and no invariant was found).  All
four are on planted variants whose balance drifts (C3: a spend may take
the balance below zero; C6: a refused spend empties the card; C7: the
bonus is returned but never put on the card), under the literal reading,
whose model of the balance is a ghost with a declared range.  This script
replays one long sequence per variant, built by hand, on the code and on
the compiled monitors: the drift takes the model out of its range, and the
bounded verdicts fail there.  The same sequences on the reference fail
nothing but the known conflict (the bonus cut at the cap).
Writes experiments/results/prove_code_card_deep.json.
"""
from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402

LOAD, SPEND, BALANCE = 1, 2, 3

# one sequence per variant: (op, amount) per call
SEQUENCES = {
    'C3': [(SPEND, 50000)] * 21,                                           # 21 spends on an empty card
    'C6': [(LOAD, 49499), (SPEND, 50000)] * 20 + [(LOAD, 49499)],          # 20 loads lost to a refused spend
    'C7': [(LOAD, 10000), (SPEND, 10000)] * 2077 + [(LOAD, 10000)],        # 2,077 bonuses never credited
}


def first_failures(S, s: str, fn, src: str, seq: list) -> dict:
    """Per requirement of reading s, the first call of seq at which one of
    its items fails on the compiled monitors (calls count from 1)."""
    run = [None] + seq                                   # None: a new object
    chk = SW.check(S, s, SW.trace(fn, run, SW.run(fn, src, run)))
    items = S.mon(s).items
    out: dict[str, int] = {}
    for iid, v in chk.items():
        it = items.get(iid)
        if it is None or it.role != 'property' or iid in S.b.frame_ids or v.get('first') is None:
            continue
        call = v['first'] - 1                            # cycle 1 is the constructor
        out[it.req] = min(out.get(it.req, call), call)
    return dict(sorted(out.items()))


def main():
    B = os.path.join(ROOT, 'corpus', 'code_card')
    with open(os.path.join(HERE, 'results', 'prove_code_card.json')) as f:
        study = json.load(f)
    bounded = [(name, s, r) for name, rec in study['implementations'].items() for s, row in rec.items()
               for r, c in row.get('requirements', {}).items() if c['proof'] == 'PROVED-BOUNDED']
    S = Session(B, sets=sorted({s for _, s, _ in bounded}))
    fn = SW.function(S)
    ref = os.path.join(B, 'impl', 'ref.py')
    out = {'bounded': len(bounded), 'fail_beyond_the_bound': 0, 'verdicts': []}
    t0 = time.time()
    for name, s, r in bounded:
        seq = SEQUENCES[name]
        fails = first_failures(S, s, fn, os.path.join(B, 'bugs', f'{name}.py'), seq)
        row = {'implementation': name, 'reading': s, 'requirement': r, 'calls': len(seq),
               'fails_at_call': fails.get(r), 'reference_fails': first_failures(S, s, fn, ref, seq)}
        out['fail_beyond_the_bound'] += row['fails_at_call'] is not None
        out['verdicts'].append(row)
        print(row, flush=True)
    out['seconds'] = round(time.time() - t0)
    with open(os.path.join(HERE, 'results', 'prove_code_card_deep.json'), 'w') as f:
        json.dump(out, f, indent=1)
    print({k: out[k] for k in ('bounded', 'fail_beyond_the_bound', 'seconds')})


if __name__ == '__main__':
    main()
