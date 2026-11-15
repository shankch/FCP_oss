"""Tests for RateLimiter (request P-LIMIT-1).

Tests marked "decision" pin down a reading of a part of the request that is
open to more than one; the RateLimiter docstring lists them.
"""

import random
import threading
import time
from collections import Counter, deque

import pytest

import rate_limiter
from rate_limiter import RateLimiter


def attempts(limiter, user, times):
    """Make one attempt by ``user`` at each time in ``times``; return the answers."""
    return [limiter.allow(user, t) for t in times]


def full_then_denied(user=1):
    """A limiter where ``user`` was allowed at 0, 1, 2 and then denied at 59.

    At 59 all three allowed attempts are still within the last 60 seconds, so
    the attempt is denied and a cooldown runs from 59 up to (not including) 69.
    From 60 on, the window alone would have room again: the attempt at 0 has
    expired.
    """
    limiter = RateLimiter()
    assert attempts(limiter, user, [0, 1, 2, 59]) == [True, True, True, False]
    return limiter


# --- the example in the request -------------------------------------------


def test_example_from_request():
    limiter = RateLimiter()
    assert attempts(limiter, 7, [0, 1, 2, 3]) == [True, True, True, False]


# --- rule 1: invalid input -------------------------------------------------


@pytest.mark.parametrize("user", [0, 1, 500, 999, 1000])
def test_customer_ids_0_to_1000_inclusive_are_valid(user):
    # decision: "from 0 to 1,000" includes both ends
    assert RateLimiter().allow(user, 0) is True


@pytest.mark.parametrize("user", [-1, 1001, -(10**12), 10**12])
def test_out_of_range_customer_raises_value_error(user):
    with pytest.raises(ValueError):
        RateLimiter().allow(user, 0)


@pytest.mark.parametrize("bad", [1.0, 2.5, "3", None, True, False])
def test_non_integer_customer_raises_type_error(bad):
    # decision: wrong types are a TypeError, not a ValueError
    with pytest.raises(TypeError):
        RateLimiter().allow(bad, 0)


@pytest.mark.parametrize("bad", [1.0, 2.5, "3", None, True])
def test_non_integer_time_raises_type_error(bad):
    with pytest.raises(TypeError):
        RateLimiter().allow(1, bad)


def test_time_earlier_than_previous_call_raises_value_error():
    limiter = RateLimiter()
    limiter.allow(1, 10)
    with pytest.raises(ValueError):
        limiter.allow(1, 9)


def test_same_time_as_previous_call_is_fine():
    limiter = RateLimiter()
    assert attempts(limiter, 1, [5, 5]) == [True, True]


def test_time_order_is_checked_across_customers():
    # decision: "the previous call" is the previous call for any customer
    limiter = RateLimiter()
    limiter.allow(1, 10)
    with pytest.raises(ValueError):
        limiter.allow(2, 9)


def test_denied_call_still_counts_as_the_previous_call():
    limiter = RateLimiter()
    attempts(limiter, 1, [0, 1, 2])
    assert limiter.allow(1, 30) is False
    with pytest.raises(ValueError):
        limiter.allow(2, 29)


def test_first_call_accepts_any_integer_time():
    # decision: the request puts no lower or upper bound on now
    assert RateLimiter().allow(0, -5) is True
    assert RateLimiter().allow(0, 10**12) is True


def test_call_that_raises_is_not_an_attempt():
    # decision: a call that raises leaves the limiter unchanged
    limiter = RateLimiter()
    assert attempts(limiter, 1, [0, 0]) == [True, True]
    for bad_call in [(1001, 0), (-1, 0), (1, 0.0), (1, -1)]:
        with pytest.raises((ValueError, TypeError)):
            limiter.allow(*bad_call)
    # Exactly one attempt is left, and no cooldown was started.
    assert attempts(limiter, 1, [0, 0]) == [True, False]


def test_call_that_raises_does_not_move_the_clock():
    limiter = RateLimiter()
    limiter.allow(1, 100)
    with pytest.raises(ValueError):
        limiter.allow(1001, 200)  # bad customer id: its time is ignored
    assert limiter.allow(1, 150) is True
    with pytest.raises(ValueError):
        limiter.allow(1, 120)  # earlier than 150
    with pytest.raises(ValueError):
        limiter.allow(1, 130)  # still earlier than 150; 120 was never recorded


# --- rules 2 and 4: at most 3 allowed attempts in any 60 seconds ------------


def test_fourth_attempt_in_the_same_second_is_denied():
    limiter = RateLimiter()
    assert attempts(limiter, 1, [5, 5, 5, 5]) == [True, True, True, False]


def test_attempt_still_counts_59_seconds_later():
    limiter = RateLimiter()
    attempts(limiter, 1, [0, 1, 2])
    assert limiter.allow(1, 59) is False


def test_attempt_has_expired_60_seconds_later():
    # decision: "any 60 seconds" is 60 consecutive whole seconds, t to t + 59
    limiter = RateLimiter()
    attempts(limiter, 1, [0, 1, 2])
    assert limiter.allow(1, 60) is True  # 0 has expired; 1 and 2 remain
    assert limiter.allow(1, 60) is False  # 1, 2 and 60 are all within 60 s


def test_steady_three_per_minute_is_always_allowed():
    limiter = RateLimiter()
    assert all(attempts(limiter, 1, range(0, 3600, 20)))


def test_customers_are_limited_independently():
    limiter = RateLimiter()
    assert attempts(limiter, 1, [0, 0, 0, 0]) == [True, True, True, False]
    assert attempts(limiter, 2, [0, 0, 0, 0]) == [True, True, True, False]
    assert limiter.allow(1000, 0) is True


# --- rule 3: denied attempts do not count -----------------------------------


def test_denied_attempts_do_not_count_towards_the_limit():
    limiter = RateLimiter()
    assert attempts(limiter, 1, [0, 1, 2]) == [True, True, True]
    assert attempts(limiter, 1, range(3, 13)) == [False] * 10
    # The last denial was at 12, so its cooldown is over, and only the allowed
    # attempts at 1 and 2 are within the last 60 seconds.
    assert limiter.allow(1, 60) is True


# --- rule 5: cooldown after a denied attempt ---------------------------------


def test_cooldown_overrides_the_fewer_than_three_rule():
    # decision: rule 5 takes precedence over rule 4
    limiter = full_then_denied()
    # Only 1 and 2 are within the last 60 seconds, but 59 was denied.
    assert limiter.allow(1, 60) is False


@pytest.mark.parametrize("t, expected", [(61, False), (68, False), (69, True), (75, True)])
def test_cooldown_lasts_ten_seconds(t, expected):
    # decision: a denial at d blocks d to d + 9; the customer may try at d + 10
    limiter = full_then_denied()
    assert limiter.allow(1, t) is expected


def test_retrying_during_cooldown_restarts_it():
    # decision: every denied attempt starts a cooldown, even one denied by a cooldown
    limiter = full_then_denied()  # denied at 59
    assert limiter.allow(1, 65) is False  # within 10 s of 59
    assert limiter.allow(1, 74) is False  # within 10 s of 65, though not of 59
    assert limiter.allow(1, 84) is True  # 10 s after the last denial, at 74


def test_cooldown_applies_only_to_that_customer():
    limiter = full_then_denied(user=1)
    assert limiter.allow(2, 60) is True
    assert limiter.allow(1, 60) is False


# --- random traffic, checked against the rules applied to the whole history --


def rules_decision(history, user, now):
    """What the rules say about this attempt, worked out from every earlier call.

    ``history`` holds ``(user, time, allowed)`` for each earlier call.  Returns
    ``(allowed, reason)``, with reason "limit" (3 allowed attempts in the last
    60 seconds), "cooldown" (fewer than 3, but a denied attempt in the last 10
    seconds) or "allowed".
    """
    recent_allowed = sum(1 for u, t, ok in history if u == user and ok and now - t < 60)
    if recent_allowed >= 3:
        return False, "limit"
    if any(u == user and not ok and now - t < 10 for u, t, ok in history):
        return False, "cooldown"
    return True, "allowed"


def assert_at_most_3_allowed_in_any_60_seconds(history):
    for user in {u for u, _, _ in history}:
        times = [t for u, t, ok in history if u == user and ok]
        # A span holding k allowed attempts can be moved to start at the
        # earliest of them, so checking spans that start at one is enough.
        for start in times:
            in_span = [t for t in times if start <= t < start + 60]
            assert len(in_span) <= 3, (user, in_span)


def random_gap(rng):
    r = rng.random()
    if r < 0.5:
        return rng.randint(0, 3)
    if r < 0.85:
        return rng.randint(4, 12)
    return rng.randint(13, 70)


def test_random_traffic_follows_the_rules():
    reasons = Counter()
    for seed in range(30):
        rng = random.Random(seed)
        limiter = RateLimiter()
        history = []
        now = rng.randint(-1000, 1000)
        for step in range(400):
            now += random_gap(rng)
            user = rng.choice([0, 0, 1, 2, 1000])
            expected, reason = rules_decision(history, user, now)
            got = limiter.allow(user, now)
            assert got is expected, f"seed={seed} step={step} user={user} now={now}"
            reasons[reason] += 1
            history.append((user, now, got))
        assert_at_most_3_allowed_in_any_60_seconds(history)
    # Make sure the traffic really exercised every kind of answer.
    assert min(reasons[r] for r in ("allowed", "limit", "cooldown")) >= 50, reasons


# --- concurrency ---------------------------------------------------------------


def test_concurrent_attempts_cannot_take_the_same_slot(monkeypatch):
    # Make every length check on the per-customer queue read the length, then
    # pause and let other threads run.  Without the lock, several threads would
    # then all see a free slot before any of them took it, and more than 3
    # would get in.
    length_checks = []

    class YieldingDeque(deque):
        def __len__(self):
            length = super().__len__()
            length_checks.append(length)
            time.sleep(0.001)
            return length

    monkeypatch.setattr(rate_limiter, "deque", YieldingDeque)
    limiter = RateLimiter()
    n_threads = 8
    results = [None] * n_threads
    start = threading.Barrier(n_threads)

    def worker(i):
        start.wait()
        results[i] = limiter.allow(42, 1000)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert length_checks, "RateLimiter no longer uses deque; update this test"
    assert results.count(True) == 3
