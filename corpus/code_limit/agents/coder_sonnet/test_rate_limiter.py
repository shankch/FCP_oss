"""Tests for rate_limiter.RateLimiter (request P-LIMIT-1).

Every expected value is worked out by hand from the rules in the request, using
the choices spelled out in the RateLimiter docstring: an allowed attempt at
second e counts until e+59, a denial at second d blocks d..d+9, rule 5 beats
rule 4, and a denial inside a block starts a fresh block.
"""

import random
import threading
from collections import Counter

import pytest

from rate_limiter import RateLimiter

T, F = True, False


def attempts(limiter, user, times):
    """Outcome of one attempt by `user` at each second in `times`."""
    return [limiter.allow(user, t) for t in times]


# --- the example in the request ----------------------------------------------


def test_example_from_the_request():
    # Attempts at 0, 1 and 2 seconds are allowed, a fourth at 3 seconds is denied.
    assert attempts(RateLimiter(), 1, [0, 1, 2, 3]) == [T, T, T, F]


# --- rule 1: ValueError ------------------------------------------------------


@pytest.mark.parametrize("user", [0, 1, 500, 1000])
def test_user_ids_0_to_1000_are_accepted(user):
    assert RateLimiter().allow(user, 0) is True


@pytest.mark.parametrize("user", [-1, 1001, -(10**9), 10**9])
def test_user_out_of_range_raises(user):
    with pytest.raises(ValueError):
        RateLimiter().allow(user, 0)


@pytest.mark.parametrize("user", [1.5, 2.0, "3", None, True])
def test_user_that_is_not_an_int_raises(user):
    with pytest.raises(ValueError):
        RateLimiter().allow(user, 0)


@pytest.mark.parametrize("now", [1.5, 3.0, "3", None, False])
def test_now_that_is_not_whole_seconds_raises(now):
    with pytest.raises(ValueError):
        RateLimiter().allow(1, now)


def test_now_earlier_than_the_previous_call_raises():
    rl = RateLimiter()
    rl.allow(1, 10)
    with pytest.raises(ValueError):
        rl.allow(1, 9)


def test_the_previous_call_may_have_been_for_another_customer():
    rl = RateLimiter()
    rl.allow(1, 10)
    with pytest.raises(ValueError):
        rl.allow(2, 9)


def test_now_equal_to_the_previous_call_is_fine():
    rl = RateLimiter()
    assert [rl.allow(1, 10), rl.allow(2, 10), rl.allow(1, 10)] == [T, T, T]


def test_a_denied_call_also_moves_the_clock():
    rl = RateLimiter()
    assert attempts(rl, 1, [0, 0, 0, 5]) == [T, T, T, F]
    with pytest.raises(ValueError):
        rl.allow(2, 4)


def test_first_call_may_use_any_time():
    assert RateLimiter().allow(1, 10**12) is True
    assert RateLimiter().allow(1, -5) is True


def test_a_call_that_raises_does_not_move_the_clock():
    rl = RateLimiter()
    assert rl.allow(1, 100) is True
    with pytest.raises(ValueError):
        rl.allow(5000, 500)
    assert rl.allow(1, 101) is True  # 101 is not "earlier than the previous call"


def test_a_call_that_raises_does_not_use_up_quota():
    rl = RateLimiter()
    assert attempts(rl, 1, [10, 11]) == [T, T]
    with pytest.raises(ValueError):
        rl.allow(1, 5)
    assert attempts(rl, 1, [12, 13]) == [T, F]  # only two had been used


# --- rules 2-4: at most 3 allowed attempts in the last 60 seconds ------------


def test_three_attempts_in_one_second_then_denied():
    assert attempts(RateLimiter(), 1, [7, 7, 7, 7]) == [T, T, T, F]


def test_an_attempt_still_counts_59_seconds_later():
    rl = RateLimiter()
    assert attempts(rl, 1, [0, 1, 2]) == [T, T, T]
    assert rl.allow(1, 59) is False


def test_an_attempt_stops_counting_60_seconds_later():
    rl = RateLimiter()
    assert attempts(rl, 1, [0, 1, 2]) == [T, T, T]
    assert rl.allow(1, 60) is True  # only the attempts at 1 and 2 are left


def test_window_slides_attempt_by_attempt():
    rl = RateLimiter()
    # Never more than 3 in any 60 seconds, so nothing is denied.
    assert attempts(rl, 1, [0, 30, 59, 60, 90]) == [T] * 5


def test_denied_attempts_do_not_count():
    rl = RateLimiter()
    assert attempts(rl, 1, [0, 1, 2]) == [T, T, T]
    assert attempts(rl, 1, [3, 20, 40]) == [F, F, F]  # spaced beyond any block
    # Had the three denied attempts counted, 60, 61 and 62 would be refused.
    assert attempts(rl, 1, [60, 61, 62, 63]) == [T, T, T, F]


def test_customers_do_not_affect_each_other():
    rl = RateLimiter()
    assert attempts(rl, 1, [0, 1, 2, 3]) == [T, T, T, F]  # customer 1 is blocked
    assert attempts(rl, 2, [3, 3, 3, 3]) == [T, T, T, F]
    assert rl.allow(1000, 4) is True


def test_every_customer_id_has_its_own_quota():
    rl = RateLimiter()
    for user in range(1001):
        assert attempts(rl, user, [0, 0, 0, 0]) == [T, T, T, F]


def test_separate_limiters_do_not_share_state():
    a, b = RateLimiter(), RateLimiter()
    assert attempts(a, 1, [5, 5, 5, 5]) == [T, T, T, F]
    assert attempts(b, 1, [0, 0, 0, 0]) == [T, T, T, F]


# --- rule 5: ten seconds of denials after a denial ---------------------------


def after_denial_at_59():
    """Customer 1 was allowed at 0, 1, 2 and denied at 59 (window full).

    From second 60 only the attempts at 1 and 2 are in the window, so rule 4
    ("fewer than 3 allowed in the last 60 seconds: allow") and rule 5 ("deny for
    10 seconds after a denial") disagree about attempts at 60 .. 68.
    """
    rl = RateLimiter()
    assert attempts(rl, 1, [0, 1, 2, 59]) == [T, T, T, F]
    return rl


@pytest.mark.parametrize("t", [60, 61, 68])
def test_rule_5_beats_rule_4_inside_the_10_seconds(t):
    assert after_denial_at_59().allow(1, t) is False


def test_the_10_seconds_are_over_10_seconds_after_the_denial():
    assert after_denial_at_59().allow(1, 69) is True


def test_a_denial_inside_a_block_starts_a_fresh_10_seconds():
    def after_second_denial():
        rl = after_denial_at_59()
        assert rl.allow(1, 65) is False  # inside the block; restarts it
        return rl

    # Without the restart the block would have ended at 69.
    assert after_second_denial().allow(1, 74) is False
    assert after_second_denial().allow(1, 75) is True


def test_a_customer_who_keeps_retrying_stays_blocked():
    # Retrying every second keeps restarting the block, even long after the
    # attempts at 0, 1 and 2 have left the window.
    assert attempts(RateLimiter(), 1, range(200)) == [T, T, T] + [F] * 197


def test_a_customer_who_backs_off_gets_back_in_once_the_window_has_room():
    rl = RateLimiter()
    assert attempts(rl, 1, [0, 1, 2, 3]) == [T, T, T, F]
    assert rl.allow(1, 60) is True  # the block from 3 is long over; 0 has left


# --- everything at once, against a reference written from the definitions ----


def reference(history, user, now):
    """Decide from the rules and the complete history; no stored state.

    `history` holds (user, now, allowed) for every earlier call.  Returns
    (allowed, window_full, blocked).
    """
    mine = [(t, ok) for (u, t, ok) in history if u == user]
    window_full = sum(1 for t, ok in mine if ok and now - t < 60) >= 3
    blocked = any(not ok and now - t < 10 for t, ok in mine)
    return (not window_full and not blocked), window_full, blocked


GAPS = [0, 0, 1, 1, 2, 3, 5, 8, 9, 10, 11, 20, 40, 55, 58, 59, 60, 61, 70]


def test_matches_the_reference_on_random_traces():
    rng = random.Random(20260101)
    seen = Counter()
    for _ in range(200):
        rl = RateLimiter()
        history = []
        now = rng.choice([0, 7, 1000])
        for _ in range(100):
            now += rng.choice(GAPS)
            user = rng.choice([0, 1, 1000])
            expected, window_full, blocked = reference(history, user, now)
            assert rl.allow(user, now) is expected, (history, user, now)
            history.append((user, now, expected))
            seen[window_full, blocked] += 1

        # Rule 2: never more than 3 allowed attempts in any 60 seconds.
        for u, t, ok in history:
            if ok:
                in_window = sum(
                    1 for u2, t2, ok2 in history if u2 == u and ok2 and t - 60 < t2 <= t
                )
                assert in_window <= 3

    # The traces must reach every kind of decision, including a denial that only
    # rule 5 causes (window has room, customer is blocked).
    assert seen[F, F] and seen[T, F] and seen[T, T] and seen[F, T]


# --- threads -----------------------------------------------------------------


def test_concurrent_attempts_are_serialised():
    rl = RateLimiter()
    n = 32
    barrier = threading.Barrier(n)
    results = []

    def attempt():
        barrier.wait()
        results.append(rl.allow(7, 100))

    threads = [threading.Thread(target=attempt) for _ in range(n)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(results) == [F] * (n - 3) + [T] * 3
