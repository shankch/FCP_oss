"""Tests for the agent-as-chip pieces: kernel translation, contract lifting,
runtime verification and the arming of latched triggers."""
import os
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fcp import agent as AG, kernel as K, rv  # noqa: E402
from fcp.analyses import Session  # noqa: E402

DESK = os.path.join(ROOT, 'corpus', 'agent_desk')


def _kernel(tmp_path, decide, update='    pass\n'):
    src = textwrap.dedent('''
        PRE = {'a': 2}
        POST = {'res': 1}
        OUT = {'x': 2}
        REGS = {'s': (2, 0)}
        ''') + 'def decide(i, r, o):\n' + decide + 'def update(i, r, o, n):\n' + update
    p = tmp_path / 'k.py'
    p.write_text(src)
    return K.load(str(p))


def test_translator_rejects_subtraction(tmp_path):
    m = _kernel(tmp_path, '    o.x = i.a - 1\n')
    with pytest.raises(K.KernelError, match='subtraction'):
        K.verilog(m)


def test_decide_cannot_read_tool_results(tmp_path):
    m = _kernel(tmp_path, '    o.x = i.res\n')
    with pytest.raises(K.KernelError, match='exists only after the action runs'):
        K.verilog(m)


def test_and_or_need_boolean_operands(tmp_path):
    m = _kernel(tmp_path, '    o.x = i.a and r.s\n')
    with pytest.raises(K.KernelError, match='boolean'):
        K.verilog(m)


@pytest.mark.parametrize('name', ['desk', 'naive'])
def test_scaffold_python_and_verilog_agree(name):
    m = K.load(os.path.join(DESK, 'scaffold', f'{name}.py'))
    r = K.cosim(m, runs=20, turns=20, seed=7, weights={'p_act': {1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 0.2, 7: 0.3}},
                sticky={'p_ord': 0.8, 'p_amt': 0.7}, bias={'human': 0.03, 'accepted': 0.7})
    assert r['agree'], r


def test_lift_keeps_the_past():
    out = AG.lift('refund -> prev(refund) && once(confirm)', {'refund': 'p_act == 5', 'confirm': 'p_act == 4'}, {})
    assert out.startswith('p_act == 5 ->')
    assert 'prev(refund)' in out and 'once(confirm)' in out


@pytest.fixture(scope='module')
def desk():
    S = Session(DESK, sets=['gold', 'agent_a'])
    AG.contract_set(S, 'gold', dest_dir=os.path.join(DESK, 'contracts'))
    return S


def _trace(turns):
    base = {k: 0 for k in ('p_act', 'p_ord', 'p_amt', 'p_more', 'human', 'id_ok', 'elig', 'total', 'accepted',
                           'say', 'verify', 'lookup', 'confirm', 'refund', 'handoff', 'close', 'ord', 'amt',
                           'more', 'done')}
    return [dict(base, **t) for t in turns]


def test_runtime_check_reports_turn(desk):
    # verify ok, lookup an eligible $64 order, refund without a confirmation
    tr = _trace([{'rst_n': 0},
                 {'rst_n': 1, 'p_act': 2, 'verify': 1, 'id_ok': 1},
                 {'rst_n': 1, 'p_act': 3, 'lookup': 1, 'elig': 1, 'total': 64},
                 {'rst_n': 1, 'p_act': 5, 'p_amt': 64, 'refund': 1, 'amt': 64}])
    res = rv.check(desk, 'gold+c', tr)
    assert res['G-CONF'] == 3 and res['C-G-CONF'] == 3
    assert res['G-ELIG'] is None and res['G-TOT'] is None


def test_latched_trigger_ignores_reset_cycle(desk):
    # garbage in the reset cycle (verify && !id_ok) must not count as a first
    # failed verification for agent_a's "hand off after the second failure"
    tr = _trace([{'rst_n': 0, 'verify': 1},
                 {'rst_n': 1, 'p_act': 2, 'verify': 1},
                 {'rst_n': 1, 'p_act': 1, 'say': 1}])
    assert rv.check(desk, 'agent_a', tr)['PA-ID-2'] is None
