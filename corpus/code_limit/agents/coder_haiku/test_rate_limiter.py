"""Tests for RateLimiter. Run with: python -m pytest -q <this directory>"""

import random
import threading

import pytest

from rate_limiter import RateLimiter


def run(limiter, user, times):
    return [limiter.allow(user, t) for t in times]


def rules_say(history, user, now):
    """Apply the rules to every earlier accepted call, without shortcuts.

    history holds (time, user, allowed) for each earlier accepted call.
    """
    allowed_in_window = sum(
        1 for t, u, ok in history if u == user and ok and now - t < 60
    )
    locked_out = any(
        u == user and not ok and now - t < 10 for t, u, ok in history
    )
    return allowed_in_window < 3 and not locked_out


# Rule 1: argument checks and time order


@pytest.mark.parametrize("user", [0, 1000])
def test_user_ids_at_both_ends_of_the_range_are_accepted(user):
    assert RateLimiter().allow(user, 0) is True


@pytest.mark.parametrize("user", [-1, 1001, 10**9])
def test_user_outside_0_to_1000_raises_value_error(user):
    with pytest.raises(ValueError):
        RateLimiter().allow(user, 0)


def test_now_earlier_than_the_previous_call_raises_value_error():
    limiter = RateLimiter()
    assert limiter.allow(1, 10) is True
    with pytest.raises(ValueError):
        limiter.allow(1, 9)


def test_time_order_is_checked_across_customers():
    limiter = RateLimiter()
    limiter.allow(1, 10)
    with pytest.raises(ValueError):
        limiter.allow(2, 9)


def test_same_second_as_the_previous_call_is_not_earlier():
    limiter = RateLimiter()
    assert limiter.allow(1, 10) is True
    assert limiter.allow(2, 10) is True


def test_rejected_calls_do_not_move_the_clock():
    limiter = RateLimiter()
    assert limiter.allow(1, 10) is True
    with pytest.raises(ValueError):
        limiter.allow(5000, 100)
    assert limiter.allow(1, 50) is True


@pytest.mark.parametrize("user", [1.0, "5", None, True])
def test_non_int_user_raises_type_error(user):
    with pytest.raises(TypeError):
        RateLimiter().allow(user, 0)


@pytest.mark.parametrize("now", [1.5, "3", None, False])
def test_non_int_time_raises_type_error(now):
    with pytest.raises(TypeError):
        RateLimiter().allow(1, now)


# Rules 2 and 4: at most 3 allowed attempts in any 60 seconds


def test_request_example():
    limiter = RateLimiter()
    assert run(limiter, 7, [0, 1, 2, 3]) == [True, True, True, False]


def test_fourth_attempt_within_60_seconds_is_denied():
    limiter = RateLimiter()
    assert run(limiter, 1, [0, 20, 40]) == [True, True, True]
    assert limiter.allow(1, 59) is False


def test_slot_frees_exactly_60_seconds_after_the_oldest_allowed_attempt():
    limiter = RateLimiter()
    assert run(limiter, 1, [0, 20, 40]) == [True, True, True]
    assert limiter.allow(1, 60) is True


def test_customers_have_separate_limits():
    limiter = RateLimiter()
    assert run(limiter, 1, [0, 1, 2]) == [True, True, True]
    assert limiter.allow(1, 3) is False
    assert limiter.allow(2, 3) is True


# Rule 3: denied attempts do not count


def test_denied_attempt_does_not_take_a_slot():
    limiter = RateLimiter()
    assert run(limiter, 1, [0, 1, 2, 3]) == [True, True, True, False]
    # Only the attempts at 1 and 2 are in the window at 60, so this is allowed.
    assert limiter.allow(1, 60) is True


# Rule 5: lockout


def test_lockout_applies_even_when_the_window_has_room():
    limiter = RateLimiter()
    assert run(limiter, 1, [0, 1, 2]) == [True, True, True]
    assert limiter.allow(1, 55) is False  # cap full, locked out until 65
    # Only two allowed attempts are left in the window at 60, but still locked.
    assert limiter.allow(1, 60) is False


@pytest.mark.parametrize("retry_at, expected", [(64, False), (65, True)])
def test_lockout_lasts_exactly_10_seconds(retry_at, expected):
    limiter = RateLimiter()
    assert run(limiter, 1, [0, 1, 2]) == [True, True, True]
    assert limiter.allow(1, 55) is False  # locked out from 55 to 65
    assert limiter.allow(1, retry_at) is expected


def test_each_denied_attempt_restarts_the_lockout():
    limiter = RateLimiter()
    assert run(limiter, 1, [0, 1, 2]) == [True, True, True]
    assert limiter.allow(1, 55) is False  # locked out until 65
    assert limiter.allow(1, 60) is False  # still locked, restarts: until 70
    assert limiter.allow(1, 69) is False  # still locked, restarts: until 79
    assert limiter.allow(1, 79) is True


def test_lockout_is_per_customer():
    limiter = RateLimiter()
    assert run(limiter, 1, [0, 1, 2]) == [True, True, True]
    assert limiter.allow(1, 55) is False
    assert limiter.allow(2, 56) is True


# Thread safety


def test_concurrent_calls_respect_the_cap():
    limiter = RateLimiter()
    outcomes = []
    outcomes_lock = threading.Lock()

    def hammer():
        results = [limiter.allow(42, 0) for _ in range(200)]
        with outcomes_lock:
            outcomes.extend(results)

    threads = [threading.Thread(target=hammer) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert outcomes.count(True) == 3


# Random call sequences checked against the rules


@pytest.mark.parametrize("seed", range(20))
def test_random_call_sequences_follow_the_rules(seed):
    rng = random.Random(seed)
    limiter = RateLimiter()
    history = []
    now = 0
    for _ in range(400):
        now += rng.choice([0, 0, 1, 3, 9, 10, 11, 30, 59, 60, 61])
        user = rng.choice([0, 1, 2, 1000])
        expected = rules_say(history, user, now)
        actual = limiter.allow(user, now)
        assert actual == expected, f"seed={seed}: call at t={now} for user {user}"
        history.append((now, user, actual))
    assert {ok for _, _, ok in history} == {True, False}
