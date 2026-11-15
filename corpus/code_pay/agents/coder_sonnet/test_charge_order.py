"""Tests for charge_order (request P-PAY-1: Fernwood Outfitters payment retry).

The payment service is replaced by a scripted fake that records every call it receives, in
order, so each test can assert the exact sequence of api.charge / api.sleep calls. The expected
numbers (3 attempts, waits of 2 and 4 seconds, 1..1,000,000 cents) are written out literally
from the request rather than imported from the implementation.
"""

import itertools
import time

import pytest

from charge_order import charge_order

ORDER_ID = 4711
AMOUNT = 1999

CHARGE = ("charge", ORDER_ID, AMOUNT)
SLEEP_2 = ("sleep", 2)
SLEEP_4 = ("sleep", 4)

# A retry loop that never stops must fail the test, not hang the suite.
MAX_RECORDED_CALLS = 25


class FakeApi:
    """Payment service stand-in: replays scripted charge results and logs every call."""

    def __init__(self, results):
        self._results = iter(results)
        self.calls = []

    def _record(self, call):
        self.calls.append(call)
        if len(self.calls) > MAX_RECORDED_CALLS:
            raise AssertionError("runaway retry loop: the payment service is called without end")

    def charge(self, *args):  # positional only, exactly as the request writes api.charge(order_id, amount)
        self._record(("charge", *args))
        try:
            result = next(self._results)
        except StopIteration:
            raise AssertionError("api.charge was called more often than the test scripted") from None
        if isinstance(result, BaseException):
            raise result
        return result

    def sleep(self, *args):  # positional only, exactly as the request writes api.sleep(seconds)
        self._record(("sleep", *args))


@pytest.fixture(autouse=True)
def forbid_real_sleep(monkeypatch):
    """Waiting must go through api.sleep; a real time.sleep would also slow the suite."""

    def fail(seconds):
        raise AssertionError(f"time.sleep({seconds}) called; charge_order must wait via api.sleep")

    monkeypatch.setattr(time, "sleep", fail)


# --- Rule 1: amount validation ---------------------------------------------------------


@pytest.mark.parametrize("amount", [0, -1, -1999, 1_000_001, 10**9])
def test_amount_out_of_range_raises_value_error_before_any_api_call(amount):
    api = FakeApi(["ok"])
    with pytest.raises(ValueError):
        charge_order(api, ORDER_ID, amount)
    assert api.calls == []


@pytest.mark.parametrize("amount", [1, 2, 999_999, 1_000_000])
def test_amount_in_range_is_charged_unchanged_and_bounds_are_inclusive(amount):
    api = FakeApi(["ok"])
    assert charge_order(api, ORDER_ID, amount) is True
    assert api.calls == [("charge", ORDER_ID, amount)]


@pytest.mark.parametrize("amount", [1.5, 100.0, "100", None, True, False])
def test_amount_that_is_not_a_whole_number_of_cents_raises_value_error(amount):
    api = FakeApi(["ok"])
    with pytest.raises(ValueError):
        charge_order(api, ORDER_ID, amount)
    assert api.calls == []


# --- Rules 2 to 6: outcome, retries and waits ------------------------------------------
#
# Extra scripted results after the expected last call are deliberate: if the function made one
# more call than it should, the call list would show it and the test would fail.

OUTCOME_CASES = [
    pytest.param(["ok"], True, [CHARGE], id="ok-on-first-attempt"),
    pytest.param(["declined"], False, [CHARGE], id="declined-is-final"),
    pytest.param(["declined", "ok"], False, [CHARGE], id="declined-is-not-retried-even-if-a-retry-would-pass"),
    pytest.param(["error", "ok"], True, [CHARGE, SLEEP_2, CHARGE], id="error-then-ok-example-from-request"),
    pytest.param(["error", "declined", "ok"], False, [CHARGE, SLEEP_2, CHARGE], id="error-then-declined-stops"),
    pytest.param(
        ["error", "error", "ok"], True, [CHARGE, SLEEP_2, CHARGE, SLEEP_4, CHARGE], id="ok-on-third-attempt"
    ),
    pytest.param(
        ["error", "error", "declined"], False, [CHARGE, SLEEP_2, CHARGE, SLEEP_4, CHARGE], id="declined-on-third-attempt"
    ),
    pytest.param(
        ["error", "error", "error", "ok"],
        False,
        [CHARGE, SLEEP_2, CHARGE, SLEEP_4, CHARGE],
        id="three-errors-give-up-no-fourth-attempt-and-no-wait-after-the-last",
    ),
    pytest.param(["ok", "ok"], True, [CHARGE], id="never-charged-again-after-ok"),
    pytest.param(["error", "ok", "ok"], True, [CHARGE, SLEEP_2, CHARGE], id="never-charged-again-after-ok-on-retry"),
    pytest.param(
        ["error", "error", "ok", "ok"],
        True,
        [CHARGE, SLEEP_2, CHARGE, SLEEP_4, CHARGE],
        id="never-charged-again-after-ok-on-third-attempt",
    ),
]


@pytest.mark.parametrize("script, expected, expected_calls", OUTCOME_CASES)
def test_outcome_and_exact_call_sequence(script, expected, expected_calls):
    api = FakeApi(script)
    assert charge_order(api, ORDER_ID, AMOUNT) is expected
    assert api.calls == expected_calls


def test_service_that_always_errors_is_tried_exactly_three_times_then_gives_up():
    # Rule 7 ("keep trying until the charge goes through") conflicts with rule 3 (at most 3
    # attempts) and rule 2 (False otherwise). The explicit cap wins, and the call must return.
    api = FakeApi(itertools.repeat("error"))
    assert charge_order(api, ORDER_ID, AMOUNT) is False
    assert api.calls == [CHARGE, SLEEP_2, CHARGE, SLEEP_4, CHARGE]


def test_every_attempt_charges_the_same_order_and_amount():
    api = FakeApi(["error", "error", "ok"])
    assert charge_order(api, 42, 250) is True
    assert api.calls == [("charge", 42, 250), SLEEP_2, ("charge", 42, 250), SLEEP_4, ("charge", 42, 250)]


def test_each_call_starts_with_a_fresh_attempt_count():
    api = FakeApi(["error", "error", "error", "error", "ok"])
    assert charge_order(api, 1, 100) is False
    assert charge_order(api, 2, 200) is True
    assert api.calls == [
        ("charge", 1, 100),
        SLEEP_2,
        ("charge", 1, 100),
        SLEEP_4,
        ("charge", 1, 100),
        ("charge", 2, 200),
        SLEEP_2,
        ("charge", 2, 200),
    ]


# --- Results and failures the request does not describe --------------------------------


@pytest.mark.parametrize("unexpected", ["pending", "OK", "", None, 0])
def test_unrecognised_result_is_false_and_is_not_retried(unexpected):
    api = FakeApi([unexpected, "ok"])
    assert charge_order(api, ORDER_ID, AMOUNT) is False
    assert api.calls == [CHARGE]


def test_unrecognised_result_after_an_error_ends_the_attempts():
    api = FakeApi(["error", "pending", "ok"])
    assert charge_order(api, ORDER_ID, AMOUNT) is False
    assert api.calls == [CHARGE, SLEEP_2, CHARGE]


def test_exception_from_the_service_propagates_and_is_not_retried():
    api = FakeApi([ConnectionError("connection reset"), "ok"])
    with pytest.raises(ConnectionError, match="connection reset"):
        charge_order(api, ORDER_ID, AMOUNT)
    assert api.calls == [CHARGE]
