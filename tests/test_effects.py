"""Code with effects: a function that acts through an interface it receives
(corpus/code_pay, a payment retry)."""
import os
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_pay')
sys.path.insert(0, ROOT)

from fcp import effects as FX  # noqa: E402
from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402


@pytest.fixture(scope='module')
def S():
    return Session(B, sets=['gold'])


@pytest.fixture(scope='module')
def fn(S):
    return SW.function(S)


@pytest.fixture(scope='module')
def ifc(S, fn):
    return FX.interface(S, fn)


def test_stub_records_and_answers(tmp_path, fn, ifc):
    """Every call is recorded with its arguments; only answering calls take a
    script entry; a run that goes on is stopped after max_calls calls."""
    src = tmp_path / 'impl.py'
    src.write_text(textwrap.dedent('''
        def charge_order(api, order_id, amount):
            if amount == 5:
                while True:
                    api.sleep(1)
            out = []
            for _ in range(3):
                out.append(api.charge(order_id, amount))
                api.sleep(2)
            return out == ["error", "ok", "declined"]
    '''))
    res = FX.run(fn, ifc, str(src), [((7, 100), (2, 0, 1)), ((7, 5), ())])
    assert [e[0] for e in res[0]['events']] == [1, 2, 1, 2, 1, 2]
    assert [e[2] for e in res[0]['events'] if e[0] == 1] == [2, 0, 1]
    assert res[0]['events'][0][1] == [7, 100] and res[0]['ret'] is True and res[0]['code'] == 0
    assert len(res[1]['events']) == ifc.max_calls and res[1]['code'] == fn.other_exc
    cols, where = FX.trace(fn, ifc, [((7, 100), (2, 0, 1)), ((7, 5), ())], res)
    assert cols['phase'][:8] == [0, 0, 0, 0, 0, 0, 0, 1] and where[7] == (0, -1)


def test_reference_and_planted_bugs(S, fn, ifc):
    import importlib.util
    spec = importlib.util.spec_from_file_location('pay_build', os.path.join(B, 'build.py'))
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    srcs = build.materialize()
    srcs['ref'] = os.path.join(B, 'impl', 'ref.py')
    runs = FX.scope(S, fn, ifc, small=True)
    want = {'ref': {'R-KEEP-1'}, 'C1': {'R-DECL-1'}, 'C2': {'R-RETRY-1'}, 'C3': {'R-WAIT-1'},
            'C5': {'R-CALL-1'}, 'C6': {'R-ERR-1'}, 'C8': {'R-RET-1'}, 'C9': {'R-KEEP-1'}}
    for v, reqs in want.items():
        res = FX.run(fn, ifc, srcs[v], runs)
        out = FX.verify(S, 'gold', fn, ifc, srcs[v], runs, res)
        failing = {x['req'] for x in out.values() if x['status'] == 'FAIL'}
        assert reqs <= failing, (v, failing)
        if v in ('ref', 'C9'):
            assert failing == {'R-KEEP-1'}, v             # the prompt's own conflict, nothing else
        assert all(x['replay'] == 'confirmed' for x in out.values() if x['status'] == 'FAIL')


def test_conflict_before_code(S, fn, ifc):
    c = FX.conflicts(S, 'gold', fn, ifc, limit=1)
    assert c['conflicts'], c
    x = c['conflicts'][0]
    assert {'R-RETRY-1', 'R-KEEP-1'} <= set(x['reqs'])
    assert x['script'] == [2, 2, 2]                       # three errors
