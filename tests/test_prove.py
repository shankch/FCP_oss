"""Proofs beyond the scope (fcp.prove): a pure function on integers and
booleans translated to z3 terms, checked first against what the code did
on the scope, then over every call the interface can carry
(corpus/code_checkout)."""
import os
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_checkout')
sys.path.insert(0, ROOT)

from fcp import prove as P  # noqa: E402
from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402


@pytest.fixture(scope='module')
def ck():
    S = Session(B, sets=['gold'])
    fn = SW.function(S)
    return S, fn, SW.calls_for(S, fn, small=True)


def write(tmp_path, body, name='impl.py'):
    p = tmp_path / name
    p.write_text(textwrap.dedent(body))
    return str(p)


FEATURES = '''
    from numbers import Integral

    LIMIT = 1_000_000
    CAP = 30
    FEE = 4 * 100 + 99

    def _whole(name, value):
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise TypeError(name)
        return int(value)

    def _pct(member, coupon):
        extra = 10 if member else 0
        return min(coupon + extra, CAP)

    def checkout(subtotal, coupon, member):
        for name, value in (("subtotal", subtotal), ("coupon", coupon)):
            _whole(name, value)
        if type(member) is not bool:
            raise TypeError("member")
        assert coupon >= 0 or subtotal >= 0 or True
        if not 0 <= subtotal <= LIMIT:
            raise ValueError("subtotal")
        if not (0 <= coupon <= 50):
            raise ValueError("coupon")
        d = _pct(member, coupon)
        q, r = divmod(subtotal * (100 - d), 100)
        price = q + (1 if r >= 50 else 0)
        total = 0
        for i in range(3):
            total += i
        shipping = (subtotal < 5000) * FEE or 0
        price = max(price, 0) + total * 0
        if coupon in (7, 13) and subtotal == 0:
            price = abs(-price)
        return price, shipping
'''


def test_translation_matches_the_code(ck, tmp_path):
    """Helpers that raise, isinstance and type(), a loop over a tuple, divmod,
    and/or returning operands, chained comparisons, `in` a tuple: the
    translation gives what the code gives on every call of the scope."""
    S, fn, calls = ck
    src = write(tmp_path, FEATURES)
    res = SW.run(fn, src, calls)
    assert P.check_translation(fn, P.Translator(src, fn.name), calls, res) is None
    ref = os.path.join(B, 'impl', 'ref.py')
    assert P.check_translation(fn, P.Translator(ref, fn.name), calls, SW.run(fn, ref, calls)) is None
    # a value that is a bool on some paths and an int on others is refused, not guessed
    mixed = write(tmp_path, FEATURES.replace('(subtotal < 5000) * FEE or 0', '(subtotal < 5000 and FEE) or 0'),
                  'mixed.py')
    with pytest.raises(P.Untranslatable):
        P.Translator(mixed, fn.name).call(fn, [P.Translator(mixed, fn.name).z3.Int(f'v{i}') for i in range(2)] +
                                          [P.Translator(mixed, fn.name).z3.Bool('m')])


def test_untranslatable_and_differences(ck, tmp_path):
    S, fn, calls = ck
    src = write(tmp_path, '''
        def checkout(subtotal, coupon, member):
            return int(subtotal * (1 - coupon / 100)), 0
    ''')
    out = P.prove(S, 'gold', fn, src, calls, SW.run(fn, src, calls))
    assert out['status'] == 'untranslatable' and 'Div' in out['why']
    ref = os.path.join(B, 'impl', 'ref.py')
    res = SW.run(fn, ref, calls)
    res['ret']['price'][5] += 1                # as if the code had answered otherwise once
    out = P.prove(S, 'gold', fn, ref, calls, res)
    assert out['status'] == 'translation differs' and out['why']['call'] == list(calls[5])


def test_proved_and_broken_beyond_the_scope(ck, tmp_path):
    """The reference: proved except the requirement in the planted conflict,
    whose counterexample is replayed and confirmed on the monitors.  A bug at
    one subtotal the scope never calls: the scope passes, the proof finds it."""
    S, fn, calls = ck
    ref = os.path.join(B, 'impl', 'ref.py')
    out = P.prove(S, 'gold', fn, ref, calls, SW.run(fn, ref, calls), only={'R-ROUND-1', 'R-MONO-1', 'R-ERR-1'})
    st = {r: x['status'] for r, x in out['requirements'].items()}
    assert out['exact'] and st == {'R-ROUND-1': 'PROVED', 'R-MONO-1': 'FAILS', 'R-ERR-1': 'PROVED'}
    mono = out['requirements']['R-MONO-1']
    assert mono['confirmed'] and mono['items'] == ['G-MONO']
    assert mono['calls'][0][0] < 5000 <= mono['calls'][1][0]
    odd = 777_777
    assert all(c[0] != odd for c in calls)
    src = write(tmp_path, open(ref).read().replace(
        '    return price, shipping', f'    if subtotal == {odd}:\n        price += 1\n    return price, shipping'))
    res = SW.run(fn, src, calls)
    scope = SW.verify(S, 'gold', fn, src, calls, res, SW.trace(fn, calls, res))
    assert all(v['status'] != 'FAIL' for v in scope.values() if v['req'] == 'R-ROUND-1')
    out = P.prove(S, 'gold', fn, src, calls, res, only={'R-ROUND-1'})
    rnd = out['requirements']['R-ROUND-1']
    assert rnd['status'] == 'FAILS' and rnd['confirmed'] and any(c[0] == odd for c in rnd['calls'])


def test_a_change_is_proved_against_the_old_code():
    """A change (corpus/code_change): the old code is translated and checked
    too, so "nothing changes for non-students" is proved for every call;
    the refactoring that sums a list translates as well."""
    B2 = os.path.join(ROOT, 'corpus', 'code_change')
    S = Session(B2, sets=['gold'])
    fn = SW.function(S)
    calls = SW.calls_for(S, fn, small=True)
    for src in (os.path.join(B2, 'impl', 'ref.py'), os.path.join(B2, 'bugs', 'C9.py')):
        out = P.prove(S, 'gold', fn, src, calls, SW.run(fn, src, calls), only={'R-SAME-1', 'R-SHIP-1'})
        assert out['status'] == 'ok', out
        assert out['requirements']['R-SAME-1']['status'] == 'PROVED'
        assert out['requirements']['R-SHIP-1']['status'] == 'FAILS' and out['requirements']['R-SHIP-1']['confirmed']


def test_the_encoding_is_checked_against_the_monitors(ck):
    """The reading's integer encoding must say a property fails exactly where
    the compiled monitor does, on every cycle of the scope; an encoding that
    has lost an item is caught before anything is proved."""
    S, fn, calls = ck
    c7 = os.path.join(B, 'bugs', 'C7.py')
    res = SW.run(fn, c7, calls)
    k, _ = SW.horizon(S, ['gold'])
    enc = SW._IntSpec(S, ['gold'], fn, k)
    assert P.check_encoding(S, 'gold', fn, enc, calls, res) is None
    for i in range(1, k + 1):                  # as if G-COUP held whatever the call
        enc.raw_holds[('gold', 'G-COUP', i)] = enc.z3.BoolVal(True)
    bad = P.check_encoding(S, 'gold', fn, enc, calls, res)
    assert bad['item'] == 'G-COUP' and bad['encoding'] == 'holds' and bad['monitor'] == 'fails'


def test_code_with_effects_is_proved_over_every_run():
    """The payment retry (corpus/code_pay): calls on `api` are events, each
    answer a free choice; every requirement is decided for every amount and
    every script of answers.  The reference keeps the 3-attempt limit, so
    the planted conflict fails at three errors in a row, replayed; tampering
    with a recorded run or with the encoding is caught before any proof."""
    import copy
    import z3
    from fcp import effects as FX
    B3 = os.path.join(ROOT, 'corpus', 'code_pay')
    S = Session(B3, sets=['gold'])
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    runs = FX.scope(S, fn, ifc, small=True)
    src = os.path.join(B3, 'impl', 'ref.py')
    res = FX.run(fn, ifc, src, runs)
    out = P.prove_effects(S, 'gold', fn, ifc, src, runs, res)
    assert out['status'] == 'ok'
    st = {r: x['status'] for r, x in out['requirements'].items()}
    assert st.pop('R-KEEP-1') == 'FAILS' and set(st.values()) == {'PROVED'}
    keep = out['requirements']['R-KEEP-1']
    assert keep['confirmed'] and keep['call'].endswith('with answers ["error", "error", "error"]')
    assert keep['conversation'][-1] == 'returns False'
    tr = P.Translator(src, fn.name, ifc)
    args = P._arg_vars(z3, fn)
    ends = tr.ends(fn, args)
    bad = copy.deepcopy(res)
    j = next(i for i, r in enumerate(bad) if len(r['events']) >= 3)
    bad[j]['events'][2][1][0] += 1             # as if the third call had another order id
    assert P.check_effects_translation(fn, ifc, tr, ends, args, runs, bad)['run'] == j
    enc = SW._IntSpec(S, ['gold'], fn, ifc.max_calls + 1, extra=tuple(P.effects_signals(fn, ifc)))
    for i in range(1, ifc.max_calls + 2):
        enc.raw_holds[('gold', 'G-KEEP', i)] = z3.BoolVal(True)
    assert P.check_effects_encoding(S, 'gold', fn, ifc, enc, runs, res)['item'] == 'G-KEEP'


def test_a_helper_that_is_passed_the_call_and_its_error_is_proved(tmp_path):
    """Placing an order (corpus/code_order): Opus's code passes each step
    through one helper, `_answered_ok(step, service_error, *args)`, which
    calls `step(*args)` and catches `service_error`; its limits are
    constants assigned two at a time.  The translation agrees with the code
    on every run of the scope, and every requirement but the planted
    conflict is proved for every argument and every script of answers.  A
    helper that catches the wrong service's error is told apart."""
    from fcp import effects as FX
    B5 = os.path.join(ROOT, 'corpus', 'code_order')
    S = Session(B5, sets=['gold'])
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    runs = FX.scope(S, fn, ifc, small=True)
    src = os.path.join(B5, 'agents', 'coder_opus', 'orders.py')
    code = open(src).read()
    assert 'MIN_QTY, MAX_QTY = 1, 100' in code and 'def _answered_ok(step, service_error, *args)' in code
    out = P.prove_effects(S, 'gold', fn, ifc, src, runs, FX.run(fn, ifc, src, runs))
    assert out['status'] == 'ok' and out['exact'], out
    st = {r: x['status'] for r, x in out['requirements'].items()}
    assert st.pop('R-LIMIT-1') == 'FAILS' and set(st.values()) == {'PROVED'}
    assert out['requirements']['R-LIMIT-1']['confirmed']
    # the booking step now catches the payment service's error: a booking
    # that raises leaves the function
    bad = code.replace('_answered_ok(shipping.book, shipping.ShippingError, order_id)',
                       '_answered_ok(shipping.book, payments.PaymentError, order_id)')
    assert bad != code
    wrong = write(tmp_path, bad, name='orders.py')
    out = P.prove_effects(S, 'gold', fn, ifc, wrong, runs, FX.run(fn, ifc, wrong, runs))
    assert out['status'] == 'ok' and out['exact'], out
    assert out['requirements']['R-STOP-1']['status'] == 'FAILS' and out['requirements']['R-STOP-1']['confirmed']


def test_files_the_code_opens_are_proved():
    """The atomic save (corpus/code_save): open returns an object whose calls
    are events, a with block closes it, try/except OSError catches the failed
    os.replace, and the path's own view of the disk decides os.path.exists
    and FileNotFoundError.  The reference breaks only rule 6, at the failed
    move; removing the file in `finally` after the move (C5) is proved to
    crash there, as the scope saw."""
    from fcp import effects as FX
    B4 = os.path.join(ROOT, 'corpus', 'code_save')
    S = Session(B4, sets=['gold'])
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    runs = FX.scope(S, fn, ifc, small=True)
    for name, broken in (('impl/ref.py', {'R-CLEAN-1'}), ('bugs/C5.py', {'R-KEEP-1', 'R-RET-1'})):
        src = os.path.join(B4, name)
        res = FX.run(fn, ifc, src, runs)
        out = P.prove_effects(S, 'gold', fn, ifc, src, runs, res)
        assert out['status'] == 'ok', out
        st = {r: x['status'] for r, x in out['requirements'].items()}
        assert {r for r, v in st.items() if v == 'FAILS'} == broken and set(st.values()) <= {'PROVED', 'FAILS'}
        assert all(out['requirements'][r]['confirmed'] for r in broken)
    ref = P.prove_effects(S, 'gold', fn, ifc, os.path.join(B4, 'impl', 'ref.py'), runs,
                          FX.run(fn, ifc, os.path.join(B4, 'impl', 'ref.py'), runs))
    assert ref['requirements']['R-CLEAN-1']['conversation'][-2:] == [
        "os.replace('balance.txt.tmp', 'balance.txt') -> \"fail\"", 'returns False']


def _short_sequences(S, fn, longest=4):
    calls, cur = [], []
    for c in SW.calls_for(S, fn, small=True) + [None]:
        if c is None:
            if 0 < len(cur) <= longest:
                calls += [None] + cur
            cur = []
        else:
            cur.append(c)
    return calls


def test_objects_are_proved_over_bounded_sequences():
    """The gift card (corpus/code_card): the constructor's fields, then one
    method per call chosen by op; every sequence of up to k calls with every
    amount.  Under the literal reading the reference keeps the load rule and
    Sonnet's code breaks it (it counts the bonus toward the cap), at a
    sequence z3 chose, replayed."""
    B5 = os.path.join(ROOT, 'corpus', 'code_card')
    S = Session(B5, sets=['gold'])
    fn = SW.function(S)
    calls = _short_sequences(S, fn)
    for name, want in (('impl/ref.py', 'PROVED-BOUNDED'), ('agents/coder_sonnet/gift_card.py', 'FAILS')):
        src = os.path.join(B5, name)
        out = P.prove_object(S, 'gold', fn, src, calls, SW.run(fn, src, calls), only={'R-LOAD-1'}, induct=False)
        assert out['status'] == 'ok' and out['k'] == 4 and not out['exact'], out
        load = out['requirements']['R-LOAD-1']
        assert load['status'] == want
        if want == 'FAILS':
            assert load['confirmed'] and load['calls'][-1].startswith('load(')


def test_objects_are_proved_for_every_sequence_by_induction():
    """Sequences of any length: an invariant over the object's fields, the
    reading's ghosts and its once/hist registers, found by Houdini, proves
    each requirement at every call.  The proof of R-BAL-1 needs that the
    field is the reading's model balance and stays within 0 .. 50,000; the
    proof of R-NEW-1 that the card is empty until a load went through.
    Readings that look back (prev, next: a window of two or three calls)
    are proved the same way, and a failure is still a replayed sequence."""
    B5 = os.path.join(ROOT, 'corpus', 'code_card')
    S = Session(B5, sets=['gold', 'agent_a', 'agent_b'])
    fn = SW.function(S)
    calls = _short_sequences(S, fn)
    src = os.path.join(B5, 'impl', 'ref.py')
    res = SW.run(fn, src, calls)
    out = P.prove_object(S, 'gold', fn, src, calls, res)
    st = {r: x['status'] for r, x in out['requirements'].items()}
    assert st.pop('R-BONUS-1') == 'FAILS' and set(st.values()) == {'PROVED'}, st   # the reference cuts the bonus
    assert out['induction']['window'] == 1 and not out['exact']
    # the conjuncts reported are a core of z3's, cut down until none can go: which
    # of several such sets it is depends on what the process asked z3 before.  The
    # field is the model balance, so each bound may be stated on either of the two
    bal = set(out['requirements']['R-BAL-1']['invariant'])
    assert 'b == self._balance' in bal or {'b <= self._balance', 'b >= self._balance'} <= bal, bal
    assert bal & {'b <= 50000', 'self._balance <= 50000'} and bal & {'b >= 0', 'self._balance >= 0'}, bal
    new = out['requirements']['R-NEW-1']['invariant']
    assert new in (['!once(op == 1 && outcome == 0) -> self._balance <= 0'],
                   ['!once(op == 1 && outcome == 0) -> b <= 0', 'b >= self._balance'],
                   ['!once(op == 1 && outcome == 0) -> b <= 0', 'b == self._balance']), new
    src = os.path.join(B5, 'agents', 'coder_sonnet', 'gift_card.py')
    res = SW.run(fn, src, calls)
    for s, window in (('agent_a', 2), ('agent_b', 3)):
        out = P.prove_object(S, s, fn, src, calls, res)
        assert out['exact'] and out['induction']['window'] == window, out
        assert {x['status'] for x in out['requirements'].values()} == {'PROVED'}
    out = P.prove_object(S, 'gold', fn, src, calls, res, only={'R-LOAD-1', 'R-SPEND-1'})
    assert out['requirements']['R-LOAD-1']['status'] == 'FAILS' and out['requirements']['R-LOAD-1']['confirmed']
    assert out['requirements']['R-SPEND-1']['status'] == 'PROVED'


DEEP = '''
    class GiftCard:
        CAP = 50_000

        def __init__(self):
            self._balance = 0
            self._asked = 0

        def _check(self, amount):
            if not 1 <= amount <= 50_000:
                raise ValueError("an amount is 1 to 50,000 cents")

        def load(self, amount):
            self._check(amount)
            if self._balance + amount > self.CAP:
                raise ValueError("the balance would be over $500.00")
            self._balance += amount
            bonus = min(500 if amount >= 10_000 else 0, self.CAP - self._balance)
            self._balance += bonus
            return bonus

        def spend(self, amount):
            self._check(amount)
            if amount > self._balance:
                return False
            self._balance -= amount
            return True

        def balance(self):
            self._asked += 1
            if self._asked > 6:            # wrong from the seventh balance() on
                return self._balance + 1
            return self._balance
'''


def test_induction_does_not_prove_what_fails_beyond_the_bound(tmp_path):
    """A card that answers balance() wrongly from the seventh time on.  No
    sequence of the scope is that long, and every sequence of up to four
    calls is correct: the bounded proof passes.  The induction finds no
    invariant that excludes the bad states, so the two requirements about
    balance() stay PROVED-BOUNDED, while the ones that do not depend on the
    counter are proved for every length.  Unrolled far enough, z3 finds the
    sequence."""
    B5 = os.path.join(ROOT, 'corpus', 'code_card')
    S = Session(B5, sets=['gold'])
    fn = SW.function(S)
    calls = _short_sequences(S, fn)
    src = write(tmp_path, DEEP, 'gift_card.py')
    res = SW.run(fn, src, calls)
    out = P.prove_object(S, 'gold', fn, src, calls, res)
    st = {r: x['status'] for r, x in out['requirements'].items()}
    assert st['R-BAL-1'] == 'PROVED-BOUNDED' and st['R-CAP-1'] == 'PROVED-BOUNDED', st
    assert st['R-LOAD-1'] == 'PROVED' and st['R-SPEND-1'] == 'PROVED' and st['R-RANGE-1'] == 'PROVED', st
    deep = P.prove_object(S, 'gold', fn, src, calls, res, only={'R-BAL-1'}, k=7)
    bal = deep['requirements']['R-BAL-1']
    assert bal['status'] == 'FAILS' and bal['confirmed'] and bal['calls'] == ['balance()'] * 7


def test_bounded_verdicts_of_the_card_study_fail_beyond_the_bound():
    """The four verdicts the gift-card study leaves PROVED-BOUNDED are on
    variants whose balance drifts, under the literal reading, whose model
    balance is a ghost with a declared range.  A long enough sequence takes
    the model out of its range and the requirement fails on the compiled
    monitors: at call 21 (C3), 41 (C6) and 4,155 (C7), far beyond the
    10 calls of the scope.  The induction must not prove them."""
    sys.path.insert(0, os.path.join(ROOT, 'experiments'))
    import card_deep as D
    B5 = os.path.join(ROOT, 'corpus', 'code_card')
    S = Session(B5, sets=['gold'])
    fn = SW.function(S)
    for name, reqs, call in (('C3', {'R-LOAD-1', 'R-CAP-1'}, 21), ('C6', {'R-LOAD-1'}, 41), ('C7', {'R-LOAD-1'}, 4155)):
        src = os.path.join(B5, 'bugs', f'{name}.py')
        seq = D.SEQUENCES[name]
        fails = D.first_failures(S, 'gold', fn, src, seq)
        assert all(fails[r] == call for r in reqs), (name, fails)
        assert not reqs & set(D.first_failures(S, 'gold', fn, src, seq[:call - 1])), name
        assert not reqs & set(D.first_failures(S, 'gold', fn, os.path.join(B5, 'impl', 'ref.py'), seq)), name
    calls = _short_sequences(S, fn)
    src = os.path.join(B5, 'bugs', 'C7.py')
    out = P.prove_object(S, 'gold', fn, src, calls, SW.run(fn, src, calls), only={'R-LOAD-1', 'R-NEW-1'})
    st = {r: x['status'] for r, x in out['requirements'].items()}
    assert st == {'R-LOAD-1': 'PROVED-BOUNDED', 'R-NEW-1': 'PROVED'}, st
