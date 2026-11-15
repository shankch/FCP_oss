import random

import pytest

from loyalty.account import Account
from loyalty.points import MAX_POINTS_PER_PURCHASE, purchase_points
from loyalty.tiers import BASIC, GOLD, SILVER, earn_rate, tier_for_points


def make_account(points):
    """Build an account holding ``points`` points through the public API only."""
    acct = Account()
    while acct.balance() < points:
        need = points - acct.balance()
        rate = earn_rate(acct.tier())
        dollars = min(need // rate, MAX_POINTS_PER_PURCHASE // rate) or 1
        acct.earn(dollars * 100)
    if acct.balance() > points:
        assert acct.redeem(acct.balance() - points)
    assert acct.balance() == points
    return acct


# ---------------------------------------------------------------- tiers.py


@pytest.mark.parametrize(
    "points, tier",
    [
        (0, BASIC),
        (1, BASIC),
        (499, BASIC),
        (500, SILVER),
        (1_000, SILVER),
        (1_999, SILVER),
        (2_000, GOLD),
        (2_001, GOLD),
        (10**9, GOLD),
    ],
)
def test_tier_for_points_boundaries(points, tier):
    assert tier_for_points(points) == tier


def test_tier_values():
    assert (BASIC, SILVER, GOLD) == (0, 1, 2)


@pytest.mark.parametrize("tier, rate", [(BASIC, 1), (SILVER, 2), (GOLD, 3)])
def test_earn_rate(tier, rate):
    assert earn_rate(tier) == rate


@pytest.mark.parametrize("tier", [-1, 3, 99])
def test_earn_rate_unknown_tier(tier):
    with pytest.raises(ValueError):
        earn_rate(tier)


def test_tier_for_points_rejects_negative():
    with pytest.raises(ValueError):
        tier_for_points(-1)


@pytest.mark.parametrize("bad", [1.0, "500", None, True])
def test_tiers_reject_non_int(bad):
    with pytest.raises(TypeError):
        tier_for_points(bad)
    with pytest.raises(TypeError):
        earn_rate(bad)


# ---------------------------------------------------------------- points.py


@pytest.mark.parametrize(
    "amount, tier, expected",
    [
        (0, BASIC, 0),
        (99, BASIC, 0),  # less than a whole dollar earns nothing
        (99, GOLD, 0),
        (100, BASIC, 1),
        (199, BASIC, 1),  # leftover cents are dropped
        (200, SILVER, 4),
        (150, GOLD, 3),
        (60_000, BASIC, 600),
        (100_000, BASIC, 1_000),  # basic reaches the cap exactly at the max amount
        (50_000, SILVER, 1_000),
        (50_099, SILVER, 1_000),
        (50_100, SILVER, 1_000),  # 1,002 capped
        (49_999, SILVER, 998),
        (33_300, GOLD, 999),
        (33_400, GOLD, 1_000),  # 1,002 capped
        (100_000, GOLD, 1_000),  # 3,000 capped
    ],
)
def test_purchase_points(amount, tier, expected):
    assert purchase_points(amount, tier) == expected


def test_purchase_points_never_exceeds_cap():
    for tier in (BASIC, SILVER, GOLD):
        for amount in range(0, 100_001, 37):
            pts = purchase_points(amount, tier)
            assert 0 <= pts <= MAX_POINTS_PER_PURCHASE
            assert pts == min((amount // 100) * earn_rate(tier), 1_000)


def test_purchase_points_rejects_bad_input():
    with pytest.raises(ValueError):
        purchase_points(-1, BASIC)
    with pytest.raises(ValueError):
        purchase_points(100, 3)
    with pytest.raises(TypeError):
        purchase_points(100.0, BASIC)


# ---------------------------------------------------------------- account.py


def test_new_account():
    acct = Account()
    assert acct.balance() == 0
    assert acct.tier() == BASIC


def test_example_from_request():
    acct = Account()
    assert acct.earn(60_000) == 600
    assert acct.redeem(50) is True
    assert acct.balance() == 550
    assert acct.tier() == 1


def test_earn_returns_and_adds_points():
    acct = Account()
    assert acct.earn(1_234) == 12
    assert acct.balance() == 12
    assert acct.earn(100) == 1
    assert acct.balance() == 13


def test_earn_under_a_dollar_earns_nothing():
    acct = Account()
    assert acct.earn(1) == 0
    assert acct.earn(99) == 0
    assert acct.balance() == 0
    assert acct.tier() == BASIC


def test_earn_uses_tier_before_purchase():
    # Basic account crosses into silver with this purchase: earned at rate 1.
    acct = make_account(499)
    assert acct.earn(10_000) == 100
    assert acct.balance() == 599
    assert acct.tier() == SILVER
    # The next purchase earns at the silver rate.
    assert acct.earn(10_000) == 200
    assert acct.balance() == 799


def test_earn_rates_by_tier():
    silver = make_account(500)
    assert silver.tier() == SILVER
    assert silver.earn(1_000) == 20

    gold = make_account(2_000)
    assert gold.tier() == GOLD
    assert gold.earn(1_000) == 30


def test_earn_cap():
    gold = make_account(2_000)
    assert gold.earn(100_000) == 1_000
    assert gold.balance() == 3_000

    silver = make_account(500)
    assert silver.earn(60_000) == 1_000
    assert silver.balance() == 1_500


def test_reaching_gold():
    acct = Account()
    acct.earn(100_000)  # basic: 1,000 -> silver
    assert acct.tier() == SILVER
    acct.earn(50_000)  # silver: 1,000 -> 2,000 -> gold
    assert acct.balance() == 2_000
    assert acct.tier() == GOLD


@pytest.mark.parametrize("amount", [0, -1, -100, 100_001, 10**9])
def test_earn_out_of_range_raises(amount):
    acct = make_account(700)
    with pytest.raises(ValueError):
        acct.earn(amount)
    assert acct.balance() == 700
    assert acct.tier() == SILVER


@pytest.mark.parametrize("amount", [1, 100_000])
def test_earn_range_ends_accepted(amount):
    acct = Account()
    acct.earn(amount)


@pytest.mark.parametrize("points", [0, -1, 100_001, 10**9])
def test_redeem_out_of_range_raises(points):
    acct = make_account(700)
    with pytest.raises(ValueError):
        acct.redeem(points)
    assert acct.balance() == 700


def test_redeem_out_of_range_raises_even_with_large_balance():
    acct = make_account(100_500)
    with pytest.raises(ValueError):
        acct.redeem(100_001)
    assert acct.redeem(100_000) is True
    assert acct.balance() == 500


def test_redeem_range_checked_before_balance():
    # An empty account still raises on an out-of-range request.
    acct = Account()
    with pytest.raises(ValueError):
        acct.redeem(0)
    with pytest.raises(ValueError):
        acct.redeem(100_001)


@pytest.mark.parametrize("bad", [1.5, 100.0, "100", None, True])
def test_non_int_arguments_raise_type_error(bad):
    acct = make_account(700)
    with pytest.raises(TypeError):
        acct.earn(bad)
    with pytest.raises(TypeError):
        acct.redeem(bad)
    assert acct.balance() == 700


def test_redeem_success():
    acct = make_account(300)
    assert acct.redeem(120) is True
    assert acct.balance() == 180


def test_redeem_exact_balance():
    acct = make_account(300)
    assert acct.redeem(300) is True
    assert acct.balance() == 0


def test_redeem_insufficient_leaves_account_unchanged():
    acct = make_account(300)
    assert acct.redeem(301) is False
    assert acct.balance() == 300
    assert acct.tier() == BASIC

    empty = Account()
    assert empty.redeem(1) is False
    assert empty.balance() == 0


def test_tier_never_goes_down():
    acct = make_account(2_500)
    assert acct.tier() == GOLD
    assert acct.redeem(2_500) is True
    assert acct.balance() == 0
    assert acct.tier() == GOLD
    # Still earns at the gold rate after the balance falls.
    assert acct.earn(1_000) == 30


def test_silver_kept_after_redeeming_below_threshold():
    acct = Account()
    acct.earn(60_000)  # 600, silver
    assert acct.redeem(500) is True
    assert acct.balance() == 100
    assert acct.tier() == SILVER
    assert acct.earn(1_000) == 20


def test_accounts_are_independent():
    a, b = Account(), Account()
    a.earn(60_000)
    assert b.balance() == 0
    assert b.tier() == BASIC


def test_random_operations_against_reference_model():
    rng = random.Random(20261111)
    for _ in range(200):
        acct = Account()
        points, tier = 0, 0
        for _ in range(60):
            if rng.random() < 0.6:
                amount = rng.choice([rng.randint(1, 100_000), rng.randint(1, 500)])
                expected = min((amount // 100) * (tier + 1), 1_000)
                assert acct.earn(amount) == expected
                points += expected
                tier = max(tier, 2 if points >= 2_000 else 1 if points >= 500 else 0)
            else:
                req = rng.randint(1, max(1, points + 200))
                ok = acct.redeem(req)
                assert ok is (req <= points)
                if ok:
                    points -= req
            assert acct.balance() == points
            assert acct.tier() == tier
            assert acct.balance() >= 0
