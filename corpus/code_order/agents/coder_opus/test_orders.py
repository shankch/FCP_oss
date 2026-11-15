"""Tests for orders.place_order.  The three services are stubs, so every test
replaces their functions with recorders whose answers the test chooses."""

import itertools

import pytest

import inventory
import payments
import shipping
from orders import place_order

STEPS = ('reserve', 'charge', 'book')
ERRORS = {
    'reserve': inventory.InventoryError,
    'charge': payments.PaymentError,
    'book': shipping.ShippingError,
}

# The request's example order: place_order(7, 3, 2, 500).
ORDER_ID, SKU, QTY, AMOUNT = 7, 3, 2, 500
RESERVE = ('reserve', SKU, QTY)
CHARGE = ('charge', ORDER_ID, AMOUNT)
BOOK = ('book', ORDER_ID)
REFUND = ('refund', ORDER_ID, AMOUNT)
RELEASE = ('release', SKU, QTY)


class Services:
    """Records every service call, in order, as (name, *args).

    outcome[step] is "ok", "refused", any other answer, "raise" (raise the
    service's own error) or an exception instance to raise instead."""

    def __init__(self, monkeypatch):
        self.calls = []
        self.outcome = {step: 'ok' for step in STEPS}
        monkeypatch.setattr(inventory, 'reserve', self._step('reserve'))
        monkeypatch.setattr(payments, 'charge', self._step('charge'))
        monkeypatch.setattr(shipping, 'book', self._step('book'))
        monkeypatch.setattr(inventory, 'release', self._undo('release'))
        monkeypatch.setattr(payments, 'refund', self._undo('refund'))

    def _step(self, name):
        def fake(*args):
            self.calls.append((name, *args))
            outcome = self.outcome[name]
            if outcome == 'raise':
                raise ERRORS[name](f'{name}: service unreachable')
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome
        return fake

    def _undo(self, name):
        def fake(*args):
            self.calls.append((name, *args))
        return fake

    @property
    def names(self):
        return [call[0] for call in self.calls]


@pytest.fixture
def services(monkeypatch):
    return Services(monkeypatch)


# Rule 1: validation, before any service call.

@pytest.mark.parametrize('qty', [0, -1, 101, 1000])
def test_qty_out_of_range_raises_value_error_and_calls_nothing(services, qty):
    with pytest.raises(ValueError):
        place_order(ORDER_ID, SKU, qty, AMOUNT)
    assert services.calls == []


@pytest.mark.parametrize('amount', [0, -500, 1_000_001])
def test_amount_out_of_range_raises_value_error_and_calls_nothing(services, amount):
    with pytest.raises(ValueError):
        place_order(ORDER_ID, SKU, QTY, amount)
    assert services.calls == []


@pytest.mark.parametrize('qty, amount', [(1, 1), (100, 1_000_000), (1, 1_000_000), (100, 1)])
def test_range_bounds_are_accepted(services, qty, amount):
    assert place_order(ORDER_ID, SKU, qty, amount) is True
    assert services.calls == [('reserve', SKU, qty), ('charge', ORDER_ID, amount), BOOK]


# Rules 2 and 5: the success path.

def test_success_takes_the_three_steps_in_order_and_nothing_else(services):
    assert place_order(ORDER_ID, SKU, QTY, AMOUNT) is True
    assert services.calls == [RESERVE, CHARGE, BOOK]


# Rules 6 and 7: failure at each step.

def test_example_from_the_request(services):
    services.outcome['charge'] = 'refused'
    assert place_order(7, 3, 2, 500) is False
    assert services.calls == [('reserve', 3, 2), ('charge', 7, 500), ('release', 3, 2)]


@pytest.mark.parametrize('failure', ['refused', 'raise'])
def test_reserve_failure_stops_with_nothing_to_undo(services, failure):
    services.outcome['reserve'] = failure
    assert place_order(ORDER_ID, SKU, QTY, AMOUNT) is False
    assert services.calls == [RESERVE]


@pytest.mark.parametrize('failure', ['refused', 'raise'])
def test_charge_failure_releases_the_stock(services, failure):
    services.outcome['charge'] = failure
    assert place_order(ORDER_ID, SKU, QTY, AMOUNT) is False
    assert services.calls == [RESERVE, CHARGE, RELEASE]


@pytest.mark.parametrize('failure', ['refused', 'raise'])
def test_book_failure_refunds_then_releases(services, failure):
    # Five calls: rules 6 and 7 require both undos here, which rule 8's
    # cap of four cannot accommodate.  The undos take precedence.
    services.outcome['book'] = failure
    assert place_order(ORDER_ID, SKU, QTY, AMOUNT) is False
    assert services.calls == [RESERVE, CHARGE, BOOK, REFUND, RELEASE]


# Every combination of answers, checked against rules 2 to 8.

@pytest.mark.parametrize('answers', list(itertools.product(['ok', 'refused', 'raise'], repeat=3)))
def test_rules_hold_for_every_combination_of_answers(services, answers):
    services.outcome.update(zip(STEPS, answers))
    reserve, charge, book = answers
    reserved = reserve == 'ok'
    charged = reserved and charge == 'ok'
    booked = charged and book == 'ok'

    result = place_order(ORDER_ID, SKU, QTY, AMOUNT)   # rule 6: no error escapes
    names = services.names

    assert result is booked                                            # rule 5
    expected_args = {'reserve': RESERVE, 'charge': CHARGE, 'book': BOOK,
                     'refund': REFUND, 'release': RELEASE}
    assert all(call == expected_args[call[0]] for call in services.calls)
    for step in STEPS:
        assert names.count(step) <= 1                                  # rule 4
    steps_taken = [n for n in names if n in STEPS]
    assert steps_taken == list(STEPS[:len(steps_taken)])               # rule 2
    assert ('charge' in names) == reserved                             # rules 3, 6
    assert ('book' in names) == charged                                # rules 3, 6
    assert names.count('refund') == int(charged and not booked)        # rule 7
    assert names.count('release') == int(reserved and not booked)      # rule 7
    undos = names[len(steps_taken):]
    assert all(n in ('refund', 'release') for n in undos)              # undo after the steps
    assert undos == sorted(undos, key=['refund', 'release'].index)     # refund before release
    if booked:
        assert undos == []                                             # rule 5
    if charged and not booked:
        assert len(names) == 5                                         # rule 8 conflict
    else:
        assert len(names) <= 4                                         # rule 8


# Answers and exceptions the request does not describe.

def test_an_answer_other_than_ok_counts_as_a_refusal(services):
    services.outcome['charge'] = 'pending'
    assert place_order(ORDER_ID, SKU, QTY, AMOUNT) is False
    assert services.calls == [RESERVE, CHARGE, RELEASE]


@pytest.mark.parametrize('step', STEPS)
def test_another_services_error_is_not_swallowed(services, step):
    # Each step catches only its own service's error.
    other = next(ERRORS[s] for s in STEPS if s != step)
    services.outcome[step] = other('wrong service')
    with pytest.raises(other):
        place_order(ORDER_ID, SKU, QTY, AMOUNT)


def test_an_unexpected_exception_propagates_without_undoing(services):
    # The charge's effect is unknown, so releasing the stock could leave the
    # customer charged for stock we do not hold (rule 3).
    services.outcome['charge'] = RuntimeError('bug in the payments client')
    with pytest.raises(RuntimeError):
        place_order(ORDER_ID, SKU, QTY, AMOUNT)
    assert services.calls == [RESERVE, CHARGE]
