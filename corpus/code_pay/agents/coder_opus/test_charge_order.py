"""Tests for charge_order (request P-PAY-1: Fernwood Outfitters payment retry)."""

import itertools

import pytest

from charge_order import charge_order

ORDER_ID = 4321
AMOUNT = 2599  # cents
CHARGE = ("charge", ORDER_ID, AMOUNT)


def wait(seconds):
    return ("sleep", seconds)


class FakePaymentApi:
    """Scripted payment service: charge() returns the given statuses in order.

    Every charge() and sleep() call is recorded, in order, in ``calls``.
    Charging more times than scripted fails the test.
    """

    def __init__(self, *statuses):
        self._statuses = list(statuses)
        self.calls = []

    def charge(self, order_id, amount):
        self.calls.append(("charge", order_id, amount))
        if not self._statuses:
            raise AssertionError("api.charge called more times than scripted")
        return self._statuses.pop(0)

    def sleep(self, seconds):
        self.calls.append(("sleep", seconds))


# Rule 1: amount validation ---------------------------------------------------


@pytest.mark.parametrize("amount", [0, -1, -2599, 1_000_001, 10**12])
def test_out_of_range_amount_raises_before_any_charge(amount):
    api = FakePaymentApi("ok")
    with pytest.raises(ValueError):
        charge_order(api, ORDER_ID, amount)
    assert api.calls == []


@pytest.mark.parametrize("amount", [1, 1_000_000])
def test_range_limits_are_inclusive(amount):
    api = FakePaymentApi("ok")
    assert charge_order(api, ORDER_ID, amount) is True
    assert api.calls == [("charge", ORDER_ID, amount)]


@pytest.mark.parametrize("amount", [25.99, 100.0, "2599", None, True])
def test_non_integer_amount_raises_before_any_charge(amount):
    api = FakePaymentApi("ok")
    with pytest.raises(ValueError):
        charge_order(api, ORDER_ID, amount)
    assert api.calls == []


# Rules 2-6: individual scenarios ---------------------------------------------


def test_ok_on_first_attempt():
    api = FakePaymentApi("ok", "ok")
    assert charge_order(api, ORDER_ID, AMOUNT) is True
    assert api.calls == [CHARGE]


def test_declined_on_first_attempt_is_not_retried():
    api = FakePaymentApi("declined", "ok")
    assert charge_order(api, ORDER_ID, AMOUNT) is False
    assert api.calls == [CHARGE]


def test_example_from_request():
    # First charge "error", second "ok": charge, sleep(2), charge -> True.
    api = FakePaymentApi("error", "ok", "ok")
    assert charge_order(api, ORDER_ID, AMOUNT) is True
    assert api.calls == [CHARGE, wait(2), CHARGE]


def test_ok_on_third_attempt():
    api = FakePaymentApi("error", "error", "ok", "ok")
    assert charge_order(api, ORDER_ID, AMOUNT) is True
    assert api.calls == [CHARGE, wait(2), CHARGE, wait(4), CHARGE]


def test_gives_up_after_three_errors():
    # A 4th charge would succeed, but the limit is 3 attempts in total,
    # and there is no wait after the last one.
    api = FakePaymentApi("error", "error", "error", "ok")
    assert charge_order(api, ORDER_ID, AMOUNT) is False
    assert api.calls == [CHARGE, wait(2), CHARGE, wait(4), CHARGE]


@pytest.mark.parametrize(
    "statuses, expected_calls",
    [
        (("error", "declined"), [CHARGE, wait(2), CHARGE]),
        (("error", "error", "declined"), [CHARGE, wait(2), CHARGE, wait(4), CHARGE]),
    ],
)
def test_declined_after_error_is_not_retried(statuses, expected_calls):
    api = FakePaymentApi(*statuses, "ok")
    assert charge_order(api, ORDER_ID, AMOUNT) is False
    assert api.calls == expected_calls


@pytest.mark.parametrize("status", ["OK", "pending", "", None])
def test_unrecognised_status_is_final(status):
    api = FakePaymentApi(status, "ok")
    assert charge_order(api, ORDER_ID, AMOUNT) is False
    assert api.calls == [CHARGE]


def test_exception_from_charge_propagates_and_is_not_retried():
    class ServiceDown(Exception):
        pass

    class FailingApi(FakePaymentApi):
        def charge(self, order_id, amount):
            self.calls.append(("charge", order_id, amount))
            raise ServiceDown("connection reset")

    api = FailingApi()
    with pytest.raises(ServiceDown):
        charge_order(api, ORDER_ID, AMOUNT)
    assert api.calls == [CHARGE]


# All rules, over every possible sequence of service responses ----------------


@pytest.mark.parametrize(
    "script",
    list(itertools.product(["ok", "declined", "error"], repeat=4)),
    ids="-".join,
)
def test_rules_hold_for_every_sequence_of_statuses(script):
    api = FakePaymentApi(*script)
    result = charge_order(api, ORDER_ID, AMOUNT)

    attempts = sum(1 for call in api.calls if call[0] == "charge")
    seen = script[:attempts]  # the statuses the function actually received

    # Rule 3: at most 3 attempts in total.
    assert 1 <= attempts <= 3
    # Rules 3, 4, 6: another attempt follows only an "error";
    # "ok" and "declined" are final.
    assert all(status == "error" for status in seen[:-1])
    # Rules 3, 7: an "error" is accepted as the outcome only once all
    # 3 attempts have been used.
    if seen[-1] == "error":
        assert attempts == 3
    # Rule 2: True exactly when a charge returned "ok".
    assert result is ("ok" in seen)
    # Rule 5: 2 s before the 2nd attempt, 4 s before the 3rd, no other waits.
    assert api.calls == [CHARGE, wait(2), CHARGE, wait(4), CHARGE][: 2 * attempts - 1]
