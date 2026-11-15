from unittest.mock import Mock, call

import pytest

from charge_order import charge_order


def scripted_api(*answers):
    """Fake payment API: each charge() call returns the next answer, or raises it if it is an exception."""
    api = Mock()
    api.charge.side_effect = list(answers)
    return api


def test_ok_on_first_attempt_returns_true_without_waiting():
    api = scripted_api("ok")

    assert charge_order(api, 7, 500) is True
    assert api.mock_calls == [call.charge(7, 500)]


def test_error_then_ok_waits_two_seconds_and_returns_true():
    api = scripted_api("error", "ok")

    assert charge_order(api, 7, 500) is True
    assert api.mock_calls == [call.charge(7, 500), call.sleep(2), call.charge(7, 500)]


def test_two_errors_then_ok_waits_two_then_four_seconds():
    api = scripted_api("error", "error", "ok")

    assert charge_order(api, 7, 500) is True
    assert api.mock_calls == [
        call.charge(7, 500),
        call.sleep(2),
        call.charge(7, 500),
        call.sleep(4),
        call.charge(7, 500),
    ]


def test_three_errors_stop_after_three_attempts_and_return_false():
    api = scripted_api("error", "error", "error")

    assert charge_order(api, 7, 500) is False
    assert api.mock_calls == [
        call.charge(7, 500),
        call.sleep(2),
        call.charge(7, 500),
        call.sleep(4),
        call.charge(7, 500),
    ]


def test_declined_returns_false_without_retry():
    api = scripted_api("declined")

    assert charge_order(api, 7, 500) is False
    assert api.mock_calls == [call.charge(7, 500)]


def test_declined_after_an_error_is_not_retried():
    api = scripted_api("error", "declined")

    assert charge_order(api, 7, 500) is False
    assert api.mock_calls == [call.charge(7, 500), call.sleep(2), call.charge(7, 500)]


def test_declined_on_third_attempt_stops_there():
    api = scripted_api("error", "error", "declined")

    assert charge_order(api, 7, 500) is False
    assert api.mock_calls == [
        call.charge(7, 500),
        call.sleep(2),
        call.charge(7, 500),
        call.sleep(4),
        call.charge(7, 500),
    ]


def test_unexpected_answer_returns_false_without_retry():
    api = scripted_api("pending")

    assert charge_order(api, 7, 500) is False
    assert api.mock_calls == [call.charge(7, 500)]


def test_no_charge_after_ok():
    api = scripted_api("error", "ok", "ok")

    assert charge_order(api, 7, 500) is True
    assert api.charge.call_count == 2


def test_exception_from_charge_propagates_without_retry():
    api = scripted_api(ConnectionError("payment service unreachable"))

    with pytest.raises(ConnectionError):
        charge_order(api, 7, 500)
    assert api.mock_calls == [call.charge(7, 500)]


@pytest.mark.parametrize("amount", [1, 1_000_000])
def test_boundary_amounts_are_charged(amount):
    api = scripted_api("ok")

    assert charge_order(api, 7, amount) is True
    assert api.mock_calls == [call.charge(7, amount)]


@pytest.mark.parametrize("amount", [0, -1, 1_000_001, 10**9])
def test_amount_out_of_range_raises_before_any_api_call(amount):
    api = Mock()

    with pytest.raises(ValueError):
        charge_order(api, 7, amount)
    assert api.mock_calls == []


@pytest.mark.parametrize("amount", [1.5, 500.0, True, "500", None])
def test_non_integer_amount_raises_before_any_api_call(amount):
    api = Mock()

    with pytest.raises(ValueError):
        charge_order(api, 7, amount)
    assert api.mock_calls == []
