"""The Lean reference semantics (lean/, fcp.leanref) against the compiled
monitors, and the three monitor defects the comparison found."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fcp import leanref as L  # noqa: E402
from fcp.ir import load_bundle  # noqa: E402
from fcp.lang import lookback, parse  # noqa: E402
from fcp.monitor import MonitorGen  # noqa: E402

lean = pytest.mark.skipif(not L.available(), reason='no Lean toolchain (.tools/lean) or no Icarus')


@pytest.fixture(scope='module')
def oracle():
    return L.build()


def _reading(case, name='gold'):
    b = load_bundle(os.path.join(ROOT, 'corpus', case))
    return b.iface, b.fsets[name]


# -- the monitor defects (no Lean needed) --------------------------------------
def test_a_ghost_bound_to_a_negative_value_gets_a_legal_name():
    iface, fset = L.synthetic()['ops']
    text = MonitorGen(iface, fset, 'm').build().text
    assert 'g_acc_km1' in text and 'g_acc_k0' in text and 'g_acc_k1' in text and 'g_acc_k-1' not in text


def test_the_look_back_of_prev_counts_a_depth_given_by_a_parameter():
    iface, fset = L.synthetic()['ops']
    syms = MonitorGen(iface, fset, 'm').syms
    assert iface.params['D'] == 2
    assert [lookback(parse(e), syms) for e in ('prev(a)', 'prev(a, 3)', 'prev(a, D)', 'prev(prev(a, D), D + 1)')] \
        == [1, 3, 2, 5]
    mon = MonitorGen(iface, fset, 'm').build()
    assert mon.items['P-PREVD'].depth == 2 and '_seg < 2' in mon.text


def test_a_ghost_takes_the_rigid_names_of_the_ghosts_it_reads():
    """g2 reads g1 and g1 reads k: an item over g2 is an item over k (one
    instance of both ghosts per value, a verdict for one value and one for all)."""
    iface, fset = L.synthetic()['chain']
    gen = MonitorGen(iface, fset, 'm')
    mon = gen.build()
    assert gen.ghost_deps('g2', 'rigid') == {'k'} and gen.ghost_deps('g2', 'signal') == {'a', 'en'}
    for iid in ('P-1', 'P-3', 'A-1'):
        assert mon.items[iid].rigids == ['k'], iid
    assert mon.items['P-1'].out['okd'] != mon.items['P-1'].out['ok']
    assert all(f'g_g2_k{v}' in mon.text for v in range(4))


# -- the comparison ------------------------------------------------------------
@lean
@pytest.mark.parametrize('case', ['arbiter', 'hub', 'agent_desk', 'code_pay'])
def test_a_corpus_monitor_computes_the_reference(oracle, case):
    r = L.check(*_reading(case), traces=10)
    assert r['differ'] == 0 and not r['unmatched'] and not r['mismatches'], r['mismatches'][:3]
    assert r['compared'] > 0.9 * r['cycles'] and r['varied'] > 0.5 * r['streams']


@lean
def test_the_written_readings_use_every_operator_and_agree(oracle):
    iface, fset = L.synthetic()['ops']
    x = L.Export(iface, fset)
    assert not x.skipped
    heads = set(L.re.findall(r'\((\w+)', x.text))
    assert {'allbits', 'anybit', 'bor', 'bxor', 'shlw', 'shr', 'slice', 'isspace', 'upper', 'lower', 'since',
            'once', 'hist', 'within', 'hold_until', 'bounded_wait', 'after_reset'} <= heads, sorted(heads)
    for name, (iface, fset) in L.synthetic().items():
        r = L.check(iface, fset)
        assert r['differ'] == 0 and not r['unmatched'] and not r['skipped'], (name, r['mismatches'][:3])
        assert r['compared'] > 0.8 * r['cycles']


@lean
def test_a_trace_that_does_not_start_with_a_reset_is_undefined_not_different(oracle):
    import random
    iface, fset = _reading('arbiter')
    rng = random.Random(1)
    x = L.Export(iface, fset)
    vs = L.valuations(x, rng, 2)
    ts = [L.random_trace(x, rng, 30, first=False) for _ in range(8)]
    r = L.compare(x, L.simulate(x, ts, vs), L.oracle(x, ts, vs), vs)
    assert r['undefined'] > 0 and r['differ'] == r['undefined']


@lean
def test_a_changed_monitor_is_noticed(oracle):
    """One operator, constant, negation or reset of the monitor changed: the
    comparison with the reference notices (the few it does not are read only
    by logic the random traces do not reach, or change nothing)."""
    r = L.sensitivity(*_reading('arbiter'), sample=30)
    assert r['tried'] == 30 and r['rejected'] == 0 and r['noticed'] >= 25, r
    assert all(u['read'] in ('verdict', 'scenario', 'range') for u in r['unnoticed'])


@lean
def test_the_theorems_are_proved_with_no_gap(oracle):
    names = [n for group in L.THEOREMS.values() for n in group]
    found = L.axioms(names)
    assert sorted(found) == sorted(names)
    allowed = {'propext', 'Classical.choice', 'Quot.sound'}
    assert all(set(ax) <= allowed for ax in found.values()), found
