"""Records: a function of a list of dicts that returns a dict, built from
scratch.  The fields of a list of records are sequence signals of one
interface group (one length); the runner builds the dicts and takes the
returned one apart."""
import os
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402
from fcp.lang import FcpError  # noqa: E402

DESIGN = '''
fcp: '0.1'
design: order_total
docs:
- {id: SPEC, path: spec.md}
interface:
  clock: clk
  reset: {name: rst_n, active_low: true, synchronous: true}
  signals:
  - {name: clk, dir: in, width: 1}
  - {name: rst_n, dir: in, width: 1}
  - {name: price, dir: in, width: 8, length: 4, group: items}
  - {name: qty, dir: in, width: 3, length: 4, group: items}
  - {name: gift, dir: in, width: 1, length: 4, group: items}
  - {name: member, dir: in, width: 1}
  - {name: outcome, dir: out, width: 2}
  - {name: subtotal, dir: out, width: 13}
  - {name: total, dir: out, width: 13}
  - {name: wraps, dir: out, width: 3}
environment: {initial_reset: true, reset_anytime: false, bmc_depth: 2, cover_depth: 2}
frame:
- {id: F-ZERO, req: R-1, expr: 'outcome != 0 -> subtotal == 0 && total == 0 && wraps == 0'}
function:
  name: order_total
  args:
  - name: items
    type: records
    fields:
    - {key: price, signal: price}
    - {key: qty, signal: qty}
    - {key: gift, signal: gift, type: bool}
  - {name: member, signal: member, type: bool}
  returns:
    type: record
    fields:
    - {key: subtotal, signal: subtotal}
    - {key: total, signal: total}
    - {key: wraps, signal: wraps}
  outcome: {signal: outcome, raises: [ValueError]}
'''
SPEC = '''Return the order's subtotal (price times quantity, summed over the items),
its total (members save $1.00 on a subtotal of $10.00 or more), and the number of gift items.
'''
REQS = '''
fcp: '0.1'
design: order_total
origin: {kind: human, id: gold, role: decomposer}
requirements:
- {id: R-1, doc: SPEC, lines: [1], quote: "Return the order's subtotal (price times quantity, summed over the items),", text: t, kind: guarantee}
- {id: R-2, doc: SPEC, lines: [2], quote: 'its total (members save $1.00 on a subtotal of $10.00 or more)', text: t, kind: guarantee}
- {id: R-3, doc: SPEC, lines: [2], quote: 'and the number of gift items.', text: t, kind: guarantee}
'''
GOLD = '''
fcp: '0.1'
set: gold
origin: {kind: human, role: formalizer, id: gold}
properties:
- {id: G-RET, req: R-1, pattern: invariant, args: {cond: 'outcome == 0'}}
- {id: G-SUB, req: R-1, pattern: implies, args: {trigger: 'outcome == 0', cond: 'subtotal == sum(i < len(price): price[i] * qty[i])'}}
- {id: G-TOT, req: R-2, pattern: implies, args: {trigger: 'outcome == 0', cond: 'total == (member && subtotal >= 1000 ? subtotal - 100 : subtotal)'}}
- {id: G-WRAP, req: R-3, pattern: implies, args: {trigger: 'outcome == 0', cond: 'wraps == count(i < len(gift): gift[i] == 1)'}}
'''
GOOD = '''
def order_total(items, member):
    sub = sum(it['price'] * it['qty'] for it in items)
    total = sub - 100 if member and sub >= 1000 else sub
    return {'subtotal': sub, 'total': total, 'wraps': sum(1 for it in items if it['gift'])}
'''
BUGS = {
    'noqty': (GOOD.replace("it['price'] * it['qty']", "it['price']"), {'G-SUB'}),
    'strict': (GOOD.replace('sub >= 1000', 'sub > 1000'), {'G-TOT'}),
    'extra': (GOOD.replace("'wraps': ", "'currency': 'USD', 'wraps': "), {'G-RET'}),
}


@pytest.fixture(scope='module')
def corpus(tmp_path_factory):
    d = tmp_path_factory.mktemp('records')
    (d / 'formal').mkdir()
    (d / 'design.yaml').write_text(DESIGN)
    (d / 'requirements.yaml').write_text(REQS)
    (d / 'spec.md').write_text(SPEC)
    (d / 'formal' / 'gold.yaml').write_text(GOLD)
    return d


@pytest.fixture(scope='module')
def S(corpus):
    return Session(str(corpus), sets=['gold'])


def test_shape_and_rendering(S):
    fn = SW.function(S)
    assert [a for a, _, _ in fn.args] == ['items.price', 'items.qty', 'items.gift', 'member']
    assert fn.group('qty') == ['price', 'qty', 'gift'] and fn.structured
    c = ((500, 250), (1, 4), (0, 1), 1)
    assert SW.call_text(fn, c) == ('order_total([{"price": 500, "qty": 1, "gift": False}, '
                                   '{"price": 250, "qty": 4, "gift": True}], True)')
    assert SW.ret_text(fn, [1500, 1400, 1]) == '{"subtotal": 1500, "total": 1400, "wraps": 1}'


def test_calls_keep_one_length(S):
    fn = SW.function(S)
    calls = SW.calls_for(S, fn, small=True)
    assert all(len(c[0]) == len(c[1]) == len(c[2]) for c in calls)
    assert {len(c[0]) for c in calls} == {0, 1, 2, 3, 4}
    assert any(c[3] and sum(p * q for p, q in zip(c[0], c[1])) == 1000 for c in calls), \
        'the scope reaches the discount boundary'


def test_reference_and_bugs(S, tmp_path):
    fn = SW.function(S)
    calls = SW.calls_for(S, fn, small=True)
    good = tmp_path / 'good.py'
    good.write_text(textwrap.dedent(GOOD))
    res = SW.run(fn, str(good), calls)
    assert res['load_error'] is None and set(res['code']) == {0}
    out = SW.verify(S, 'gold', fn, str(good), calls, res, SW.trace(fn, calls, res))
    assert {k: x['status'] for k, x in out.items() if x['status'] != 'PASS'} == {}
    for name, (src, expect) in BUGS.items():
        p = tmp_path / f'{name}.py'
        p.write_text(textwrap.dedent(src))
        res = SW.run(fn, str(p), calls)
        out = SW.verify(S, 'gold', fn, str(p), calls, res, SW.trace(fn, calls, res))
        failing = {k for k, x in out.items() if x['status'] == 'FAIL'}
        assert failing == expect, name
        assert all(x.get('replay', 'confirmed') == 'confirmed' for x in out.values()), name


def test_record_class(corpus, tmp_path):
    """Records built as objects of a class of the implementation (a dataclass)."""
    import shutil
    d = tmp_path / 'cls'
    shutil.copytree(corpus, d)
    text = DESIGN.replace('    type: records\n', '    type: records\n    class: Item\n')
    (d / 'design.yaml').write_text(text)
    S = Session(str(d), sets=['gold'])
    fn = SW.function(S)
    src = tmp_path / 'item.py'
    src.write_text(textwrap.dedent('''
        from dataclasses import dataclass

        @dataclass
        class Item:
            price: int
            qty: int
            gift: bool

        def order_total(items, member):
            sub = sum(it.price * it.qty for it in items)
            total = sub - 100 if member and sub >= 1000 else sub
            return {'subtotal': sub, 'total': total, 'wraps': sum(1 for it in items if it.gift)}
    '''))
    calls = SW.calls_for(S, fn, small=True)[:300]
    res = SW.run(fn, str(src), calls)
    assert set(res['code']) == {0}
    assert SW.call_text(fn, calls[0]).startswith('order_total([') or SW.call_text(fn, calls[0]) == 'order_total([], False)'


def test_group_errors(corpus, tmp_path):
    import shutil
    d = tmp_path / 'bad'
    shutil.copytree(corpus, d)
    (d / 'design.yaml').write_text(DESIGN.replace('length: 4, group: items}\n  - {name: gift',
                                                  'length: 3, group: items}\n  - {name: gift'))
    with pytest.raises(FcpError):
        Session(str(d), sets=['gold'])
    (d / 'design.yaml').write_text(DESIGN.replace('    - {key: gift, signal: gift, type: bool}\n', ''))
    S = Session(str(d), sets=['gold'])
    with pytest.raises(SW.SoftwareError):
        SW.function(S)                 # the group has a signal the records do not name


def test_invoice_conflict_before_code():
    """corpus/code_invoice: rounding each line and rounding the order cannot
    both hold; the conflict is found before any code, on one call for a
    member, and two items are enough.

    Which call shows the conflict is not fixed: the candidates come from
    the solver's models, which depend on what the process solved before
    (items of 3 and 7 cents in the study, 1 x 7 and 1 x 3 in a new process,
    three items after the other tests), and the shrink is greedy."""
    S = Session(os.path.join(ROOT, 'corpus', 'code_invoice'), sets=['gold'])
    fn = SW.function(S)
    c = SW.conflicts(S, 'gold', fn, limit=1)
    assert c['conflicts'], c
    x = c['conflicts'][0]
    assert {'R-MEM-1', 'R-DISC-1', 'R-SUM-1', 'R-TOT-1'} <= set(x['reqs'])
    (items, member), = [(cl[0], cl[3]) for cl in x['calls']]
    assert member and len(items) >= 2           # a single line never conflicts
    spec = SW._Spec(S, 'gold', fn, 2)

    def call(*rows):                             # (price, qty, sale) per item, for a member
        cols = list(zip(*rows))
        return tuple(fn.value_of(sig, list(col)) for sig, col in zip(('price', 'qty', 'sale'), cols)) + (1,)
    assert spec.core([call((3, 1, 0), (7, 1, 0))]) is not None     # total 10 by rule 5, 9 by rules 4 and 6
    assert spec.core([call((3, 1, 0))]) is None and spec.core([call((7, 1, 0))]) is None
    # the shrink itself draws nothing: from one conflicting call it always ends on the same one
    alpha = {sig: SW.alphabet(S, fn, a, sig, (), ['gold']) for a, sig, _ in fn.args if sig in fn.seqs}
    ints = SW.scope(S, fn, (), 1, small=True)
    start = call((1, 10, 1), (1, 9, 0), (7, 3, 0), (0, 10, 0))
    assert spec.core([start]) is not None
    assert SW.shrink(spec, fn, [start], alpha, ints) == [call((1, 7, 0), (1, 3, 0))]


def test_drawn_points_stay_with_their_session():
    """The calls drawn for a session are kept on it.  A table of the module
    keyed by id(S) could hand a later session the points of a dead one."""
    S = Session(os.path.join(ROOT, 'corpus', 'code_invoice'), sets=['gold'])
    fn = SW.function(S)
    pts = SW.request_points(S, fn, ['gold'], (), 1, 2)
    assert pts and [k for k in S._points if k[0] == 'request']
    assert SW.request_points(S, fn, ['gold'], (), 1, 2) == pts
    assert not Session(os.path.join(ROOT, 'corpus', 'code_invoice'), sets=['gold'])._points
    assert not hasattr(SW, '_POINTS')
