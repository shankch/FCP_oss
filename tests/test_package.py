"""An implementation of several modules: a package entered at the dotted
module the design names, with relative imports between its modules.  The
cart of tests/test_methods.py, split into shop/cart.py and shop/store.py."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))

from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402
import test_methods as TM  # noqa: E402

CART = '''
from .store import Units


class Cart:
    def __init__(self):
        self.units = Units()

    def add(self, sku, qty):
        self.units.put(sku, qty)

    def remove(self, sku):
        self.units.take(sku)

    def total(self):
        return self.units.count()
'''
STORE = '''
LIMIT = 37            # a constant in a module other than the entry


class Units:
    def __init__(self):
        self.d = {}

    def put(self, sku, qty):
        self.d[sku] = self.d.get(sku, 0) + qty

    def take(self, sku):
        if self.d.get(sku, 0) == 0:
            raise KeyError(sku)
        self.d[sku] -= 1

    def count(self):
        return sum(self.d.values())
'''


@pytest.fixture(scope='module')
def corpus(tmp_path_factory):
    d = tmp_path_factory.mktemp('shop')
    (d / 'formal').mkdir()
    (d / 'design.yaml').write_text(TM.DESIGN.replace('  module: cart\n', '  module: shop.cart\n'))
    (d / 'requirements.yaml').write_text(TM.REQS)
    (d / 'spec.md').write_text(TM.SPEC)
    (d / 'formal' / 'gold.yaml').write_text(TM.GOLD)
    return d


def package(root, store=STORE):
    (root / 'shop').mkdir(parents=True)
    (root / 'shop' / '__init__.py').write_text('')
    (root / 'shop' / 'cart.py').write_text(CART)
    (root / 'shop' / 'store.py').write_text(store)
    (root / 'test_cart.py').write_text('LIMIT_IN_TESTS = 991\n')
    return str(root)


def test_package_runs_and_verifies(corpus, tmp_path):
    S = Session(str(corpus), sets=['gold'])
    fn = SW.function(S)
    assert fn.module == 'shop.cart'
    good = package(tmp_path / 'good')
    assert SW.entry_file(fn, good).endswith(os.path.join('shop', 'cart.py'))
    assert 37 in SW.constants(S, [good]) and 991 not in SW.constants(S, [good])     # tests are not the code
    calls = SW.calls_for(S, fn, [good], small=True)
    res = SW.run(fn, good, calls)
    assert res['load_error'] is None
    out = SW.verify(S, 'gold', fn, good, calls, res, SW.trace(fn, calls, res))
    assert [k for k, x in out.items() if x['status'] == 'FAIL'] == []
    bad = package(tmp_path / 'bad', STORE.replace('self.d[sku] -= 1', 'self.d[sku] = 0'))   # the bug is not in the entry module
    res = SW.run(fn, bad, calls)
    out = SW.verify(S, 'gold', fn, bad, calls, res, SW.trace(fn, calls, res))
    assert out['G-TOT']['status'] == 'FAIL'


def test_package_mutants(corpus, tmp_path):
    """Mutants of the entry module run among the package's other modules."""
    S = Session(str(corpus), sets=['gold'])
    fn = SW.function(S)
    good = package(tmp_path / 'm')
    calls = SW.calls_for(S, fn, [good], small=True)
    m = SW.mutation(S, ['gold'], fn, good, calls, limit=12, jobs=4)
    assert m['mutants'] > 0 and m['observable'] > 0
    assert all('ImportError' not in str(r.get('example', '')) for r in m['all'])


def test_review_takes_a_package(tmp_path):
    """fcp review on a package: the signature of the entry module, and the
    design's module set to it whatever the adapter agent wrote."""
    from fcp import review as RV
    root = package(tmp_path / 'p')
    sig = RV.signature(root, 'shop.cart')
    assert sig.startswith('# a package; the entry point is in module shop.cart\nclass Cart:')
    assert '    def add(self, sku, qty): ...' in sig
    with pytest.raises(ValueError):
        RV.signature(root)
    design = tmp_path / 'design.yaml'
    design.write_text(TM.DESIGN)
    RV._set_module(str(design), 'shop.cart')
    import yaml
    assert yaml.safe_load(design.read_text())['function']['module'] == 'shop.cart'
