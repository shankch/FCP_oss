"""The Lean reference semantics against the compiled monitors (fcp.leanref).

    python experiments/lean_oracle.py [proofs] [agree] [cold] [monitor] [lean]     (default: all)

proofs   the theorems of lean/ (the registers of the monitor compute the
         reference; the propositions of the paper), with the axioms each
         rests on.
agree    every reading of the corpus and two written for this comparison:
         the monitor is simulated on random traces, the Lean oracle evaluates
         the same traces, every output is compared at every cycle.
monitor  the same comparison after one change to the monitor (an operator,
         a constant, a negation, a reset), a sample per reading: is the
         change noticed?
lean     the same comparison after one change to a definition in lean/
         (rebuilt in a copy): is the change noticed?
cold     traces that do not start with a reset (outside the standard
         environment): the monitor is undefined there, never different.

Writes experiments/results/lean_oracle.json.
"""
from __future__ import annotations

import collections
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from fcp import leanref as L  # noqa: E402
from fcp.ir import load_bundle  # noqa: E402

# One change each to a definition of the reference: (what, file, the text, the text instead).
CHANGES = [
    ('quiet also asks the cycle after the span', 'FCP/Semantics.lean',
     '(List.range (b - a)).all fun i => !rst (a + i)', '(List.range (b - a + 1)).all fun i => !rst (a + i)'),
    ('a look-back of d is met one cycle early', 'FCP/Semantics.lean',
     'decide (d ≤ t) && quiet rst (t - d) t', 'decide (d ≤ t) && quiet rst (t - d + 1) t'),
    ('a look-back of d needs d + 1 cycles', 'FCP/Semantics.lean',
     'decide (d ≤ t) && quiet rst (t - d) t', 'decide (d < t) && quiet rst (t - d) t'),
    ('once keeps a cycle that was a reset', 'FCP/Semantics.lean',
     'a s && quiet rst s t', 'a s && quiet rst (s + 1) t'),
    ('hist keeps a cycle that was a reset', 'FCP/Semantics.lean',
     'a s || !quiet rst s t', 'a s || !quiet rst (s + 1) t'),
    ('since asks its first operand one cycle early', 'FCP/Semantics.lean',
     '(List.range (t - s)).all fun i => a (s + 1 + i)', '(List.range (t - s + 1)).all fun i => a (s + i)'),
    ('% truncates', 'FCP/Semantics.lean', '| .mod => .int (a % b)', '| .mod => .int (Int.tmod a b)'),
    ('>> truncates', 'FCP/Semantics.lean',
     '| .shr => .int (a / (2 : Int) ^ b.toNat)', '| .shr => .int (Int.tdiv a ((2 : Int) ^ b.toNat))'),
    ('<< of a vector keeps every bit', 'FCP/Semantics.lean',
     '| .shlw w => .int ((a * (2 : Int) ^ b.toNat) % (2 : Int) ^ w)',
     '| .shlw _ => .int (a * (2 : Int) ^ b.toNat)'),
    ('isspace is the space alone', 'FCP/Semantics.lean',
     '| .isspace => .ofBool (inRange 9 13 a || a == 32)', '| .isspace => .ofBool (a == 32)'),
    ('upper moves every letter', 'FCP/Semantics.lean',
     '| .upper => .int (if inRange 97 122 a then a - 32 else a)',
     '| .upper => .int (if inRange 65 122 a then a - 32 else a)'),
    ('a trigger counts before it is defined', 'FCP/Items.lean',
     '(always || segGe env.rst e.lookback t) && holds env e t', 'holds env e t'),
    ('next keeps a trigger in a reset cycle', 'FCP/Items.lean',
     'decide (1 ≤ t) && !env.rst (t - 1) && armed env alw tr (t - 1)', 'decide (1 ≤ t) && armed env alw tr (t - 1)'),
    ('within opens one cycle late', 'FCP/Items.lean',
     '!(decide (lo ≤ i) && holds env c (t - hi + i))', '!(decide (lo < i) && holds env c (t - hi + i))'),
    ('hold_until: a release in the checked cycle ends it', 'FCP/Items.lean',
     '(List.range (t - s - 1)).all fun i => !holds env r (s + 1 + i)',
     '(List.range (t - s)).all fun i => !holds env r (s + 1 + i)'),
    ('bounded_wait allows one cycle more', 'FCP/Items.lean',
     '!(armed env alw c t && waited env alw c n t)', '!(armed env alw c t && waited env alw c (n + 1) t)'),
    ('after_reset also asks the cycles of a long reset', 'FCP/Items.lean',
     '!(decide (1 ≤ t) && env.rst (t - 1)) || holds env c t', '!(decide (1 ≤ t) && env.rst (t - 1) && !env.rst t) || holds env c t'),
    ('a verdict counts in a reset cycle', 'FCP/Items.lean',
     'env.rst t || !segGe env.rst d t || raw', '!segGe env.rst d t || raw'),
    ('a trigger counts in a reset cycle', 'FCP/Items.lean',
     '!env.rst t && segGe env.rst d t && trig', 'segGe env.rst d t && trig'),
    ('checked in reset too: a verdict counts before its look-back', 'FCP/Items.lean',
     'if alw then decide (t < d) || raw else', 'if alw then raw else'),
    ('checked in reset too: a trigger counts before its look-back', 'FCP/Items.lean',
     'if alw then decide (d ≤ t) && trig else', 'if alw then trig else'),
    ('a reset does not set the ghosts', 'FCP/Items.lean', 'if base.rst t then g.init', 'if false then g.init'),
    ('the range of a ghost is asked in reset too', 'FCP/Items.lean',
     'env.rst t || inRange g.lo g.hi (eval env [] g.next t).toInt', 'inRange g.lo g.hi (eval env [] g.next t).toInt'),
]
# The readings a changed definition is compared on.
PROBE = [('arbiter', 'gold'), ('fifo', 'gold'), ('hub', 'gold'), ('agent_desk', 'gold'), ('code_pay', 'gold'),
         ('code_card', 'gold')]


def readings() -> list[tuple]:
    out = []
    for c in sorted(os.listdir(os.path.join(ROOT, 'corpus'))):
        b = load_bundle(os.path.join(ROOT, 'corpus', c))
        out += [(f'{c}/{s}', b.iface, b.fsets[s]) for s in sorted(b.fsets)]
    return out + [(f'written/{n}', i, f) for n, (i, f) in L.synthetic().items()]


def agree(rs: list[tuple]) -> dict:
    rows, tot = {}, collections.Counter()
    for name, iface, fset in rs:
        t = time.time()
        r = L.check(iface, fset)
        r['seconds'] = round(time.time() - t, 1)
        rows[name] = r
        tot.update({k: r[k] for k in ('items', 'streams', 'varied', 'cycles', 'compared', 'differ', 'undefined',
                                      'past_range')})
        tot['skipped'] += len(r['skipped'])
        print(name, {k: r[k] for k in ('items', 'streams', 'compared', 'differ', 'undefined', 'past_range', 'seconds')},
              flush=True)
    return {'readings': rows, 'total': dict(tot, readings=len(rows))}


def monitor(rs: list[tuple], sample: int = 40) -> dict:
    rows, tot, read = {}, collections.Counter(), collections.Counter()
    for name, iface, fset in rs:
        t = time.time()
        r = L.sensitivity(iface, fset, sample=sample, traces=24 if name.startswith('code_mask') else 60)
        r['seconds'] = round(time.time() - t, 1)
        rows[name] = r
        tot.update({k: r[k] for k in ('changes', 'tried', 'noticed', 'rejected', 'initial')})
        read.update(u['read'] for u in r['unnoticed'])
        print(name, {k: r[k] for k in ('changes', 'tried', 'noticed', 'rejected', 'initial', 'seconds')},
              dict(collections.Counter(u['read'] for u in r['unnoticed'])), flush=True)
    return {'readings': rows, 'total': dict(tot, readings=len(rows), unnoticed=dict(read))}


def lean(rs: list[tuple]) -> dict:
    probe = [r for r in rs if r[0] in {f'{c}/{s}' for c, s in PROBE} or r[0].startswith('written/')]
    rows = []
    with tempfile.TemporaryDirectory(prefix='fcp_lean_') as d:
        for what, rel, old, new in CHANGES:
            copy = os.path.join(d, 'lean')
            shutil.rmtree(copy, ignore_errors=True)
            shutil.copytree(L.LEAN_DIR, copy, symlinks=True)
            path = os.path.join(copy, rel)
            with open(path, encoding='utf-8') as f:
                src = f.read()
            assert src.count(old) == 1, (what, src.count(old))
            with open(path, 'w', encoding='utf-8') as f:
                f.write(src.replace(old, new))
            t = time.time()
            env = dict(os.environ, PATH=L.LEAN_BIN + os.pathsep + os.environ.get('PATH', ''))
            b = subprocess.run(['lake', 'build', 'fcp-oracle'], cwd=copy, env=env, capture_output=True, text=True)
            row = {'what': what, 'file': rel, 'built': b.returncode == 0, 'differ': 0, 'on': []}
            # the theorems of FCP/Monitor.lean relate these definitions to the registers: do they still check?
            lib = subprocess.run(['lake', 'build', 'FCP'], cwd=copy, env=env, capture_output=True, text=True)
            row['proofs_break'] = lib.returncode != 0
            row['broken'] = sorted(set(re.findall(r'error: (FCP/\w+\.lean):', lib.stdout + lib.stderr)))
            if row['built']:
                binary = os.path.join(copy, '.lake', 'build', 'bin', 'fcp-oracle')
                for name, iface, fset in probe:
                    n = L.check(iface, fset, binary=binary)['differ']
                    row['differ'] += n
                    row['on'] += [name] if n else []
            else:
                row['error'] = (b.stdout + b.stderr)[-600:]
            row['seconds'] = round(time.time() - t, 1)
            rows.append(row)
            print(what, '|', 'built' if row['built'] else 'NOT BUILT', row['differ'], row['on'],
                  'proofs break' if row['proofs_break'] else 'proofs hold', row['seconds'], flush=True)
    return {'changes': rows, 'probe': [r[0] for r in probe],
            'total': {'changes': len(rows), 'noticed': sum(r['differ'] > 0 for r in rows),
                      'proofs_break': sum(r['proofs_break'] for r in rows)}}


def cold(rs: list[tuple]) -> dict:
    """Traces that do not start with a reset: the registers of the monitor
    have no value yet, so some of its outputs are undefined; where they are
    defined they are the reference's."""
    import random
    rows, tot = {}, collections.Counter()
    for name, iface, fset in [r for r in rs if r[0] in {f'{c}/{s}' for c, s in PROBE} or r[0].startswith('written/')]:
        rng = random.Random(1)
        x = L.Export(iface, fset)
        vs = L.valuations(x, rng, 3)
        ts = [L.random_trace(x, rng, 40, first=False) for _ in range(20)]
        r = L.compare(x, L.simulate(x, ts, vs), L.oracle(x, ts, vs), vs)
        rows[name] = {'streams': r['streams'], 'compared': r['compared'], 'undefined': r['undefined'],
                      'differ_defined': r['differ'] - r['undefined'], 'past_range': r['past_range']}
        tot.update(rows[name])
        print(name, rows[name], flush=True)
    return {'readings': rows, 'total': dict(tot, readings=len(rows))}


def proofs(rs: list[tuple]) -> dict:
    """What the Lean library proves: every listed theorem, with the axioms it
    rests on (a gap in a proof would show as `sorryAx`)."""
    names = [n for group in L.THEOREMS.values() for n in group]
    found = L.axioms(names)
    files = [os.path.join(L.LEAN_DIR, 'FCP', f) for f in ('Monitor.lean', 'Contracts.lean', 'Causal.lean')]
    count = sum(line.startswith('theorem ') for f in files for line in open(f))
    allowed = {'propext', 'Classical.choice', 'Quot.sound'}
    return {'theorems': found,
            'total': {'listed': len(names), 'proved': sum(n in found and set(found[n]) <= allowed for n in names),
                      'theorems_in_all': count,
                      'axioms': sorted({a for ax in found.values() for a in ax})}}


def main():
    parts = sys.argv[1:] or ['proofs', 'agree', 'cold', 'monitor', 'lean']
    path = os.path.join(HERE, 'results', 'lean_oracle.json')
    out = json.load(open(path)) if os.path.exists(path) else {}
    L.build()
    rs = readings()
    for p in parts:
        t = time.time()
        out[p] = {'agree': agree, 'monitor': monitor, 'lean': lean, 'cold': cold, 'proofs': proofs}[p](rs)
        out[p]['seconds'] = round(time.time() - t)
        print(p, json.dumps(out[p]['total']), out[p]['seconds'], 's', flush=True)
        with open(path, 'w') as f:
            json.dump(out, f, indent=1, default=list)


if __name__ == '__main__':
    main()
