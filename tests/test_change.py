"""Changes to existing code: the code before the change runs on the same
calls (corpus/code_change)."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_change')
sys.path.insert(0, ROOT)

from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402


@pytest.fixture(scope='module')
def S():
    return Session(B, sets=['gold'])


@pytest.fixture(scope='module')
def fn(S):
    return SW.function(S)


def test_old_answers_in_the_trace(fn):
    calls = [(5000, 0, False, True), (4999, 10, True, False), (100, 51, False, True)]
    base = SW.baseline_values(fn, calls)
    assert base == {'old_price': [5000, 3999, 0], 'old_ship': [0, 499, 0], 'old_outcome': [0, 0, 1]}
    res = SW.run(fn, os.path.join(B, 'impl', 'ref.py'), calls)
    cols = SW.trace(fn, calls, res)
    assert cols['old_price'] == [0, 5000, 3999, 0] and cols['price'] == [0, 4250, 3999, 0]


def test_conflict_before_code(S, fn):
    c = SW.conflicts(S, 'gold', fn, limit=1)
    assert c['conflicts'] and set(c['conflicts'][0]['reqs']) == {'R-SAME-1', 'R-SHIP-1'}
    assert c['conflicts'][0]['stimulus'] == ['checkout(5000, 0, False, False)']


def test_regression_is_caught(S, fn, tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location('change_build', os.path.join(B, 'build.py'))
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    srcs = build.materialize()
    calls = SW.calls_for(S, fn, small=True)
    for v, want in (('C3', 'R-SAME-1'), ('C8', 'R-SAME-1')):
        res = SW.run(fn, srcs[v], calls)
        out = SW.verify(S, 'gold', fn, srcs[v], calls, res, SW.trace(fn, calls, res))
        same = [x for k, x in out.items() if x['req'] == want]
        assert same and same[0]['status'] == 'FAIL' and same[0]['replay'] == 'confirmed', v
