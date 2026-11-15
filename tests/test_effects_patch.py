"""Effects the code does not receive: it imports the payment client and
calls time.sleep itself.  The sandbox patches those names with the recording
stub (a module it lacks, `payments`, is created), so the same readings check
it as the payment retry that receives `api` (corpus/code_pay)."""
import os
import shutil
import sys
import textwrap

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fcp import effects as FX  # noqa: E402
from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402

GOOD = '''
import time
from payments import charge, ServiceError


def charge_order(order_id, amount):
    if not 1 <= amount <= 1_000_000:
        raise ValueError('amount out of range')
    for attempt in range(3):
        if attempt:
            time.sleep(2 ** attempt)
        try:
            answer = charge(order_id, amount)
        except ServiceError:
            continue
        return answer == 'ok'
    return False
'''


@pytest.fixture(scope='module')
def corpus(tmp_path_factory):
    d = tmp_path_factory.mktemp('pay_patch') / 'code_pay'
    shutil.copytree(os.path.join(ROOT, 'corpus', 'code_pay'), d,
                    ignore=shutil.ignore_patterns('agents', 'bugs', '__pycache__'))
    design = yaml.safe_load((d / 'design.yaml').read_text())
    ifc = design['function']['interface']
    ifc['position'] = None
    for m in ifc['methods']:
        m['patch'] = {'charge': 'payments.charge', 'sleep': 'time.sleep'}[m['name']]
        if m['name'] == 'charge':
            m['raises'] = {'error': 'payments.ServiceError'}
    (d / 'design.yaml').write_text(yaml.safe_dump(design, sort_keys=False))
    return d


@pytest.fixture(scope='module')
def setup(corpus):
    S = Session(str(corpus), sets=['gold'])
    fn = SW.function(S)
    return S, fn, FX.interface(S, fn)


def test_patched_calls_are_recorded(setup, tmp_path):
    S, fn, ifc = setup
    src = tmp_path / 'pay.py'
    src.write_text(textwrap.dedent(GOOD))
    runs = [((7, 100), (2, 0)), ((7, 100), (2, 2, 2))]
    res = FX.run(fn, ifc, str(src), runs)
    assert [(e[0], e[2]) for e in res[0]['events']] == [(1, 2), (2, 0), (1, 0)]
    assert res[0]['events'][1][1] == [2] and res[0]['ret'] is True
    assert res[1]['ret'] is False and len(res[1]['events']) == 5
    lines = FX.conversation(fn, ifc, runs, res, 0)
    assert lines == ['payments.charge(7, 100) -> "error"', 'time.sleep(2)', 'payments.charge(7, 100) -> "ok"',
                     'returns True']
    assert FX.call_text(fn, ifc, runs, 0) == 'charge_order(7, 100) with answers ["error", "ok"]'


def test_patched_code_against_the_reading(setup, tmp_path):
    """The reference's behaviour, written against imported names, fails only
    the prompt's own conflict (R-KEEP-1), as the reference does; without the
    waits it also fails the waiting rule."""
    S, fn, ifc = setup
    runs = FX.scope(S, fn, ifc, small=True)
    good = tmp_path / 'good.py'
    good.write_text(textwrap.dedent(GOOD))
    out = FX.verify(S, 'gold', fn, ifc, str(good), runs, FX.run(fn, ifc, str(good), runs))
    assert {x['req'] for x in out.values() if x['status'] == 'FAIL'} == {'R-KEEP-1'}
    bad = tmp_path / 'bad.py'
    bad.write_text(textwrap.dedent(GOOD.replace('            time.sleep(2 ** attempt)\n', '            pass\n')))
    out = FX.verify(S, 'gold', fn, ifc, str(bad), runs, FX.run(fn, ifc, str(bad), runs))
    failing = {x['req'] for x in out.values() if x['status'] == 'FAIL'}
    assert 'R-WAIT-1' in failing and all(x['replay'] == 'confirmed' for x in out.values() if x['status'] == 'FAIL')


def test_module_attribute_and_validation(setup, corpus, tmp_path):
    """`import payments; payments.charge(...)` reaches the stub too; a method
    of an interface the code does not receive must name its patch."""
    S, fn, ifc = setup
    src = tmp_path / 'attr.py'
    src.write_text('import payments\n\ndef charge_order(order_id, amount):\n'
                   '    return payments.charge(order_id, amount) == "ok"\n')
    res = FX.run(fn, ifc, str(src), [((7, 100), (0,))])
    assert res[0]['ret'] is True and res[0]['events'][0][0] == 1
    d = tmp_path / 'nopatch'
    shutil.copytree(corpus, d)
    design = yaml.safe_load((d / 'design.yaml').read_text())
    del design['function']['interface']['methods'][1]['patch']
    (d / 'design.yaml').write_text(yaml.safe_dump(design, sort_keys=False))
    S2 = Session(str(d), sets=['gold'])
    with pytest.raises(SW.SoftwareError):
        FX.interface(S2, SW.function(S2))
