"""Tests for orders.place_order. The three services are replaced by fakes that
record every call, so no real service is reached."""

import pytest

import inventory
import orders
import payments
import shipping


class Services:
    """Scripted fakes: each step returns its scripted answer, or raises it if it
    is an exception instance. Every call is appended to `calls`."""

    def __init__(self):
        self.calls = []
        self.answers = {"reserve": "ok", "charge": "ok", "book": "ok"}

    def _step(self, name):
        def call(*args):
            self.calls.append((name, *args))
            answer = self.answers[name]
            if isinstance(answer, BaseException):
                raise answer
            return answer
        return call

    def _void(self, name):
        def call(*args):
            self.calls.append((name, *args))
        return call

    def install(self, monkeypatch):
        monkeypatch.setattr(inventory, "reserve", self._step("reserve"))
        monkeypatch.setattr(payments, "charge", self._step("charge"))
        monkeypatch.setattr(shipping, "book", self._step("book"))
        monkeypatch.setattr(inventory, "release", self._void("release"))
        monkeypatch.setattr(payments, "refund", self._void("refund"))
        return self


@pytest.fixture
def svc(monkeypatch):
    return Services().install(monkeypatch)


ORDER = dict(order_id=7, sku=3, qty=2, amount=500)
RESERVE = ("reserve", 3, 2)
CHARGE = ("charge", 7, 500)
BOOK = ("book", 7)
RELEASE = ("release", 3, 2)
REFUND = ("refund", 7, 500)


# Success path

def test_success_returns_true_and_takes_three_steps_in_order(svc):
    assert orders.place_order(**ORDER) is True
    assert svc.calls == [RESERVE, CHARGE, BOOK]


# Validation

@pytest.mark.parametrize("qty", [0, -1, 101, 1000])
def test_qty_out_of_range_raises_before_any_call(svc, qty):
    with pytest.raises(ValueError):
        orders.place_order(7, 3, qty, 500)
    assert svc.calls == []


@pytest.mark.parametrize("amount", [0, -5, 1_000_001])
def test_amount_out_of_range_raises_before_any_call(svc, amount):
    with pytest.raises(ValueError):
        orders.place_order(7, 3, 2, amount)
    assert svc.calls == []


@pytest.mark.parametrize("qty, amount", [(1, 1), (100, 1_000_000), (1, 1_000_000), (100, 1)])
def test_boundary_values_are_accepted(svc, qty, amount):
    assert orders.place_order(7, 3, qty, amount) is True
    assert svc.calls == [("reserve", 3, qty), ("charge", 7, amount), BOOK]


# Failure at each step

def test_reserve_refused_stops_with_nothing_to_undo(svc):
    svc.answers["reserve"] = "refused"
    assert orders.place_order(**ORDER) is False
    assert svc.calls == [RESERVE]


def test_reserve_raising_stops_with_nothing_to_undo(svc):
    svc.answers["reserve"] = inventory.InventoryError("down")
    assert orders.place_order(**ORDER) is False
    assert svc.calls == [RESERVE]


def test_charge_refused_releases_stock(svc):
    svc.answers["charge"] = "refused"
    assert orders.place_order(**ORDER) is False
    assert svc.calls == [RESERVE, CHARGE, RELEASE]


def test_charge_raising_releases_stock_and_does_not_refund(svc):
    svc.answers["charge"] = payments.PaymentError("down")
    assert orders.place_order(**ORDER) is False
    assert svc.calls == [RESERVE, CHARGE, RELEASE]


def test_book_refused_refunds_then_releases(svc):
    svc.answers["book"] = "refused"
    assert orders.place_order(**ORDER) is False
    assert svc.calls == [RESERVE, CHARGE, BOOK, REFUND, RELEASE]


def test_book_raising_refunds_then_releases(svc):
    svc.answers["book"] = shipping.ShippingError("down")
    assert orders.place_order(**ORDER) is False
    assert svc.calls == [RESERVE, CHARGE, BOOK, REFUND, RELEASE]


# Invariants

@pytest.mark.parametrize("answers", [
    {},
    {"reserve": "refused"},
    {"charge": "refused"},
    {"book": "refused"},
    {"charge": payments.PaymentError("x")},
    {"book": shipping.ShippingError("x")},
])
def test_no_service_call_is_repeated(svc, answers):
    svc.answers.update(answers)
    orders.place_order(**ORDER)
    names = [c[0] for c in svc.calls]
    assert len(names) == len(set(names))


def test_never_charge_without_stock(svc):
    svc.answers["reserve"] = "refused"
    orders.place_order(**ORDER)
    assert not any(c[0] == "charge" for c in svc.calls)


def test_never_book_without_payment(svc):
    svc.answers["charge"] = "refused"
    orders.place_order(**ORDER)
    assert not any(c[0] == "book" for c in svc.calls)


def test_unexpected_answer_counts_as_refused(svc):
    svc.answers["charge"] = "maybe"
    assert orders.place_order(**ORDER) is False
    assert svc.calls == [RESERVE, CHARGE, RELEASE]


@pytest.mark.parametrize("answers", [
    {"reserve": "refused"},
    {"charge": "refused"},
    {"charge": payments.PaymentError("x")},
    {"reserve": inventory.InventoryError("x")},
])
def test_at_most_four_calls_on_paths_that_do_not_reach_booking(svc, answers):
    svc.answers.update(answers)
    orders.place_order(**ORDER)
    assert len(svc.calls) <= 4


@pytest.mark.xfail(
    strict=True,
    reason="Conflict in the request: a refused or failed booking needs "
           "reserve, charge, book, refund and release = 5 calls, but rule 8 "
           "allows at most 4. The implementation follows the undo rule.",
)
def test_at_most_four_calls_when_booking_fails(svc):
    svc.answers["book"] = "refused"
    orders.place_order(**ORDER)
    assert len(svc.calls) <= 4
