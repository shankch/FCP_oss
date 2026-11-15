"""An object with several methods: each cycle calls one of them, chosen by
the `op` input; arguments of the other methods are 0, and results of the
other methods are 0 (frame).  Built from scratch: a cart with add, remove
and total."""
import os
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402

DESIGN = '''
fcp: '0.1'
design: cart
docs:
- {id: SPEC, path: spec.md}
interface:
  clock: clk
  reset: {name: rst_n, active_low: true, synchronous: true}
  signals:
  - {name: clk, dir: in, width: 1}
  - {name: rst_n, dir: in, width: 1}
  - {name: op, dir: in, width: 2, desc: '1 add, 2 remove, 3 total'}
  - {name: sku, dir: in, width: 3}
  - {name: qty, dir: in, width: 3}
  - {name: outcome, dir: out, width: 3}
  - {name: total, dir: out, width: 6}
environment: {initial_reset: true, reset_anytime: true, bmc_depth: 6, cover_depth: 6}
frame:
- {id: F-ZERO, req: R-1, expr: 'op != 3 || outcome != 0 -> total == 0'}
function:
  class: Cart
  module: cart
  op: {signal: op}
  methods:
  - name: add
    op: 1
    args: [{name: sku, signal: sku, type: int}, {name: qty, signal: qty, type: int}]
  - name: remove
    op: 2
    args: [{name: sku, signal: sku, type: int}]
  - name: total
    op: 3
    returns: {signal: total, type: int}
  outcome: {signal: outcome, raises: [ValueError, KeyError]}
  scope:
    sequences: 300
    length: [1, 6]
    sku: {values: [0, 1, 2]}
    qty: {values: [0, 1, 2, 7]}
'''
SPEC = 'A cart: add(sku, qty) adds qty units of sku; remove(sku) removes one unit of sku; total() is the number of units.\n'
REQS = '''
fcp: '0.1'
design: cart
origin: {kind: human, id: gold, role: decomposer}
requirements:
- {id: R-1, doc: SPEC, lines: [1], quote: 'total() is the number of units.', text: t, kind: guarantee}
- {id: R-2, doc: SPEC, lines: [1], quote: 'remove(sku) removes one unit of sku', text: t, kind: guarantee}
'''
GOLD = '''
fcp: '0.1'
set: gold
origin: {kind: human, role: formalizer, id: gold}
ghosts:
- {name: all, range: [0, 63], init: 0, next: 'op == 1 && outcome == 0 ? all + qty : (op == 2 && outcome == 0 ? all - 1 : all)'}
properties:
- {id: G-RET, req: R-1, pattern: implies, args: {trigger: 'op == 1 || op == 3', cond: 'outcome == 0'}}
- {id: G-TOT, req: R-1, pattern: implies, args: {trigger: 'op == 3 && outcome == 0', cond: 'total == all'}}
'''
GOOD = '''
class Cart:
    def __init__(self):
        self.units = {}

    def add(self, sku, qty):
        self.units[sku] = self.units.get(sku, 0) + qty

    def remove(self, sku):
        if self.units.get(sku, 0) == 0:
            raise KeyError(sku)
        self.units[sku] -= 1

    def total(self):
        return sum(self.units.values())
'''


@pytest.fixture(scope='module')
def corpus(tmp_path_factory):
    d = tmp_path_factory.mktemp('cart')
    (d / 'formal').mkdir()
    (d / 'design.yaml').write_text(DESIGN)
    (d / 'requirements.yaml').write_text(REQS)
    (d / 'spec.md').write_text(SPEC)
    (d / 'formal' / 'gold.yaml').write_text(GOLD)
    return d


def test_methods_shape(corpus):
    S = Session(str(corpus), sets=['gold'])
    fn = SW.function(S)
    assert [a for a, _, _ in fn.args] == ['op', 'sku', 'qty'] and fn.rets == ['total']
    assert SW.call_text(fn, (1, 2, 5)) == 'add(2, 5)'
    assert SW.call_text(fn, (3, 0, 0)) == 'total()'
    calls = SW.calls_for(S, fn, small=True)
    real = [c for c in calls if c is not None]
    assert {c[0] for c in real} == {1, 2, 3}
    assert all(c[2] == 0 for c in real if c[0] != 1) and all(c[1] == 0 for c in real if c[0] == 3)


def test_methods_run_and_verify(corpus, tmp_path):
    S = Session(str(corpus), sets=['gold'])
    fn = SW.function(S)
    calls = SW.calls_for(S, fn, small=True)
    good = tmp_path / 'cart.py'
    good.write_text(textwrap.dedent(GOOD))
    res = SW.run(fn, str(good), calls)
    assert res['load_error'] is None
    out = SW.verify(S, 'gold', fn, str(good), calls, res, SW.trace(fn, calls, res))
    assert {k: x['status'] for k, x in out.items() if x['status'] == 'FAIL'} == {}
    bad = tmp_path / 'bad.py'                      # remove takes away every unit of the sku
    bad.write_text(textwrap.dedent(GOOD.replace('self.units[sku] -= 1', 'self.units[sku] = 0')))
    res = SW.run(fn, str(bad), calls)
    out = SW.verify(S, 'gold', fn, str(bad), calls, res, SW.trace(fn, calls, res))
    assert out['G-TOT']['status'] == 'FAIL'
    shown = out['G-TOT']['calls_shown']
    assert any(x['call'].startswith('remove(') for x in shown) and shown[-1]['call'] == 'total()'


def test_methods_spec_only(corpus):
    """Before any code: no conflict, and one open choice, the exception for
    removing a sku that is not in the cart (the reading does not say)."""
    S = Session(str(corpus), sets=['gold'])
    fn = SW.function(S)
    assert SW.conflicts(S, 'gold', fn, limit=1)['conflicts'] == []
    ch = SW.object_choices(S, 'gold', fn, fn.rets + [fn.outcome])
    opened = ch.get('open', ch)
    assert set(opened) == {'outcome'} and opened['outcome']['call'].split('; ')[-1].startswith('remove(')


def test_outcome_width(corpus, tmp_path):
    import shutil
    d = tmp_path / 'narrow'
    shutil.copytree(corpus, d)
    (d / 'design.yaml').write_text(DESIGN.replace('{name: outcome, dir: out, width: 2}', '{name: outcome, dir: out, width: 2}'))
    text = (corpus / 'design.yaml').read_text()
    assert 'width: 3}\n  - {name: total' in text
    (d / 'design.yaml').write_text(text.replace('{name: outcome, dir: out, width: 3}', '{name: outcome, dir: out, width: 2}'))
    with pytest.raises(SW.SoftwareError):
        SW.function(Session(str(d), sets=['gold']))


def test_scenarios_that_never_happen(corpus, tmp_path):
    """A scenario whose cover is impossible, and one the reading's rules
    forbid, are both named (they used to pass as 'consistent')."""
    import shutil
    d = tmp_path / 'scen'
    shutil.copytree(corpus, d)
    gold = (corpus / 'formal' / 'gold.yaml').read_text() + '''scenarios:
- {id: G-IMP, req: R-1, cover: 'total == 1 && total == 2'}
- {id: G-FORB, req: R-1, cover: 'op == 1 && outcome == 1'}
- {id: G-OK, req: R-1, cover: 'op == 3 && total == 3'}
'''
    (d / 'formal' / 'gold.yaml').write_text(gold)
    S = Session(str(d), sets=['gold'])
    c = S.consistency('gold', pairs=False)
    assert c['impossible_scenarios'] == ['G-IMP'] and c['forbidden_scenarios'] == ['G-FORB']
