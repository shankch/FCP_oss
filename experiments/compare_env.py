"""My reading against each agent's reading, on the runs the agent's own
assumptions admit.

    python experiments/compare_env.py <effects corpus>

The study compares readings with every input free.  A reading without
assumptions (gold) then constrains runs that no trace has (arguments that
change within a run, an answer the script never gives), and looks stronger
than a reading that assumes them away.  Here both sides are compared under
the agent's assumptions only, so what remains is a difference in what the
readings ask of the code.  Writes results/<corpus>_env.json.
"""
from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import effects_demo as ED  # noqa: E402
from fcp import effects as FX, software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402

if __name__ == '__main__':
    t0 = time.time()
    S = Session(ED.B, sets=ED.SETS)
    S.cmp_engine = 'bmc'
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    out = {}
    for b in ED.PEERS:
        plain = S.compare('gold', b, env=b)
        ctx = S.compare('gold', b, env=b, context=True)
        rec = {}
        for r in sorted(plain):
            if r == '<assumptions>' or r in {it.req for it in S.frame_items('gold')}:
                continue
            x = ctx.get(r, {})
            rec[r] = {'plain': plain[r]['relation'], 'context': x.get('relation')}
            for w in ('a_not_b', 'b_not_a'):
                if x.get(f'witness_{w}'):
                    rec[r][w] = {'lines': ED.conversation_lines(S, fn, ifc, x[f'witness_{w}'])}
        out[f'gold|{b}'] = rec
        print(f'gold|{b} under the assumptions of {b}:')
        for r, x in rec.items():
            print(f"    {r:<10} {x['plain']:<13} in context {x['context']}")
            for w in ('a_not_b', 'b_not_a'):
                if w in x:
                    print(f"        {w}: " + ' ; '.join(x[w]['lines']))
    path = os.path.join(HERE, 'results', f'{ED.CORPUS}_env.json')
    with open(path, 'w') as f:
        json.dump({'readings': out, 'seconds': round(time.time() - t0, 1)}, f, indent=1)
    print(f'written {path}')
