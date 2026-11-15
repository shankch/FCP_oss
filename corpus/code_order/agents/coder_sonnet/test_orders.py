"""Tests for orders.place_order.  The three services are replaced by fakes
that record every call in one shared log, in call order."""

import itertools

import pytest

import inventory
import orders
import payments
import shipping

OK, REFUSED, ERROR = "ok", "refused", "error"
OUTCOMES = (OK, REFUSED, ERROR)

ORDER_ID, SKU, QTY, AMOUNT = 7, 3, 2, 500

RESERVE = ("reserve", SKU, QTY)
CHARGE = ("charge", ORDER_ID, AMOUNT)
BOOK = ("book", ORDER_ID)
REFUND = ("refund", ORDER_ID, AMOUNT)
RELEASE = ("release", SKU, QTY)


@pytest.fixture
def world(monkeypatch):
    """Install fakes for the services.  Returns a function
    run(reserve=OK, charge=OK, book=OK, **order) -> (result, calls)."""

    def run(reserve=OK, charge=OK, book=OK, order_id=ORDER_ID, sku=SKU,
            qty=QTY, amount=AMOUNT):
        calls = []

        def answer(outcome, error, name, *args):
            calls.append((name, *args))
            if outcome == ERROR:
                raise error("service unreachable")
            return outcome

        monkeypatch.setattr(
            inventory, "reserve",
            lambda s, q: answer(reserve, inventory.InventoryError, "reserve", s, q))
        monkeypatch.setattr(
            inventory, "release", lambda s, q: calls.append(("release", s, q)))
        monkeypatch.setattr(
            payments, "charge",
            lambda o, a: answer(charge, payments.PaymentError, "charge", o, a))
        monkeypatch.setattr(
            payments, "refund", lambda o, a: calls.append(("refund", o, a)))
        monkeypatch.setattr(
            shipping, "book",
            lambda o: answer(book, shipping.ShippingError, "book", o))
        result = orders.place_order(order_id, sku, qty, amount)
        return result, calls

    return run


@pytest.fixture
def no_services(monkeypatch):
    """Replace every service function by one that records the call; the
    returned list must stay empty when validation fails."""
    calls = []
    for mod, names in ((inventory, ("reserve", "release")),
                       (payments, ("charge", "refund")),
                       (shipping, ("book",))):
        for name in names:
            monkeypatch.setattr(mod, name, lambda *a, _n=name: calls.append(_n))
    return calls


# --- rule 5: success ------------------------------------------------------

def test_all_ok_returns_true_and_calls_only_the_three_steps(world):
    result, calls = world()
    assert result is True
    assert calls == [RESERVE, CHARGE, BOOK]


# --- rule 6 and 7: each failure point, refused and raising -----------------

@pytest.mark.parametrize("outcome", [REFUSED, ERROR])
def test_reserve_fails_nothing_else_is_called(world, outcome):
    result, calls = world(reserve=outcome)
    assert result is False
    assert calls == [RESERVE]


@pytest.mark.parametrize("outcome", [REFUSED, ERROR])
def test_charge_fails_stock_is_released_and_nothing_refunded(world, outcome):
    result, calls = world(charge=outcome)
    assert result is False
    assert calls == [RESERVE, CHARGE, RELEASE]


@pytest.mark.parametrize("outcome", [REFUSED, ERROR])
def test_book_fails_charge_is_refunded_and_stock_released(world, outcome):
    result, calls = world(book=outcome)
    assert result is False
    assert calls == [RESERVE, CHARGE, BOOK, REFUND, RELEASE]


def test_example_from_the_request(world):
    result, calls = world(charge=REFUSED)
    assert result is False
    assert calls == [("reserve", 3, 2), ("charge", 7, 500), ("release", 3, 2)]


def test_arguments_are_passed_through(world):
    result, calls = world(order_id=91, sku=12, qty=100, amount=1_000_000)
    assert result is True
    assert calls == [("reserve", 12, 100), ("charge", 91, 1_000_000), ("book", 91)]

    result, calls = world(book=REFUSED, order_id=92, sku=13, qty=1, amount=1)
    assert result is False
    assert calls == [
        ("reserve", 13, 1), ("charge", 92, 1), ("book", 92),
        ("refund", 92, 1), ("release", 13, 1),
    ]


def test_service_errors_never_leave_the_function(world):
    for reserve, charge, book in itertools.product(OUTCOMES, repeat=3):
        result, _ = world(reserve=reserve, charge=charge, book=book)  # no raise
        assert result is (reserve == charge == book == OK)


def test_an_answer_other_than_ok_counts_as_refused(world):
    # The services only answer "ok" or "refused"; anything else must not be
    # taken for success.
    for bad in ("pending", "OK", "", None):
        result, calls = world(reserve=bad)
        assert (result, calls) == (False, [RESERVE])
        result, calls = world(charge=bad)
        assert (result, calls) == (False, [RESERVE, CHARGE, RELEASE])
        result, calls = world(book=bad)
        assert (result, calls) == (False, [RESERVE, CHARGE, BOOK, REFUND, RELEASE])


# --- rules 2, 3, 4, 6, 7, 8 over every combination of service outcomes -----

@pytest.mark.parametrize(
    "reserve,charge,book", list(itertools.product(OUTCOMES, repeat=3)))
def test_properties_over_all_outcome_combinations(world, reserve, charge, book):
    result, calls = world(reserve=reserve, charge=charge, book=book)
    names = [c[0] for c in calls]

    # Rule 4 and 7: every service call at most once, undo calls exactly once.
    for name in ("reserve", "charge", "book", "refund", "release"):
        assert names.count(name) <= 1

    # Rule 2: the steps are taken in order.
    steps = [n for n in names if n in ("reserve", "charge", "book")]
    assert steps == ["reserve", "charge", "book"][:len(steps)]

    # Rule 3: charge only after a successful reserve, book only after a
    # successful charge.
    if "charge" in names:
        assert reserve == OK
    if "book" in names:
        assert reserve == OK and charge == OK

    # Rule 6: stop at the first failure.
    outcomes = {"reserve": reserve, "charge": charge, "book": book}
    first_failure = next((s for s in ("reserve", "charge", "book")
                          if outcomes[s] != OK), None)
    if first_failure is not None:
        assert steps[-1] == first_failure
    else:
        # Rule 5: success calls nothing else.
        assert result is True and names == ["reserve", "charge", "book"]

    # Rule 7: refund iff the customer was charged, release iff stock was
    # reserved, when the order failed; neither when it succeeded.
    charged = charge == OK and reserve == OK
    reserved = reserve == OK
    if result:
        assert "refund" not in names and "release" not in names
    else:
        assert ("refund" in names) == charged
        assert ("release" in names) == reserved
        # undo comes after every step, refund before release
        undo = [i for i, n in enumerate(names) if n in ("refund", "release")]
        assert all(i > max(j for j, n in enumerate(names)
                           if n in ("reserve", "charge", "book")) for i in undo)
        if charged:
            assert names.index("refund") < names.index("release")


def test_call_budget_rule_8_and_its_one_exception(world):
    # Rule 8 caps an order at four calls.  That is met on every path but one:
    # when the booking fails after a successful reserve and charge, rules 6
    # and 7 require reserve, charge, book, refund and release (five calls).
    # The request is contradictory there; the implementation undoes fully.
    for reserve, charge, book in itertools.product(OUTCOMES, repeat=3):
        _, calls = world(reserve=reserve, charge=charge, book=book)
        if reserve == OK and charge == OK and book != OK:
            assert len(calls) == 5
        else:
            assert len(calls) <= 4


# --- rule 1: validation -----------------------------------------------------

@pytest.mark.parametrize("qty", [0, -1, 101, 1000])
def test_bad_qty_raises_and_calls_nothing(no_services, qty):
    with pytest.raises(ValueError):
        orders.place_order(ORDER_ID, SKU, qty, AMOUNT)
    assert no_services == []


@pytest.mark.parametrize("amount", [0, -1, 1_000_001, 10**9])
def test_bad_amount_raises_and_calls_nothing(no_services, amount):
    with pytest.raises(ValueError):
        orders.place_order(ORDER_ID, SKU, QTY, amount)
    assert no_services == []


def test_both_bad_raises_and_calls_nothing(no_services):
    with pytest.raises(ValueError):
        orders.place_order(ORDER_ID, SKU, 0, 0)
    assert no_services == []


@pytest.mark.parametrize("qty,amount", [
    (1, 1), (100, 1_000_000), (1, 1_000_000), (100, 1), (50, 500_000)])
def test_boundary_values_are_accepted(world, qty, amount):
    result, calls = world(qty=qty, amount=amount)
    assert result is True
    assert len(calls) == 3
