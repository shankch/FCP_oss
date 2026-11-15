import pytest

from loyalty import Account
from loyalty.points import MAX_POINTS_PER_PURCHASE, points_for_purchase
from loyalty.tiers import (
    BASIC,
    GOLD,
    SILVER,
    points_per_dollar,
    tier_for_points,
)


# ---- tiers.py (rules 1, 2) ------------------------------------------------

@pytest.mark.parametrize(
    "points, tier",
    [
        (0, BASIC),
        (1, BASIC),
        (499, BASIC),
        (500, SILVER),
        (501, SILVER),
        (1999, SILVER),
        (2000, GOLD),
        (2001, GOLD),
        (10**6, GOLD),
    ],
)
def test_tier_for_points(points, tier):
    assert tier_for_points(points) == tier


def test_tier_numbers():
    assert (BASIC, SILVER, GOLD) == (0, 1, 2)


@pytest.mark.parametrize("tier, rate", [(BASIC, 1), (SILVER, 2), (GOLD, 3)])
def test_points_per_dollar(tier, rate):
    assert points_per_dollar(tier) == rate


@pytest.mark.parametrize("tier", [-1, 3, None])
def test_points_per_dollar_unknown_tier(tier):
    with pytest.raises(ValueError):
        points_per_dollar(tier)


# ---- points.py (rules 3, 4) -----------------------------------------------

@pytest.mark.parametrize(
    "amount, tier, expected",
    [
        (1, BASIC, 0),
        (99, GOLD, 0),            # under a dollar earns nothing
        (100, BASIC, 1),
        (199, BASIC, 1),          # cents are dropped, not rounded
        (200, BASIC, 2),
        (199, SILVER, 2),
        (100, SILVER, 2),
        (100, GOLD, 3),
        (1234, BASIC, 12),
        (1234, SILVER, 24),
        (1234, GOLD, 36),
        (60000, BASIC, 600),
    ],
)
def test_points_for_purchase(amount, tier, expected):
    assert points_for_purchase(amount, tier) == expected


@pytest.mark.parametrize(
    "amount, tier, expected",
    [
        (100_000, BASIC, 1000),   # exactly at the cap
        (50_000, SILVER, 1000),   # exactly at the cap
        (33_300, GOLD, 999),      # just under
        (33_400, GOLD, 1000),     # exactly at the cap
        (50_100, SILVER, 1000),   # 1,002 capped
        (100_000, SILVER, 1000),
        (100_000, GOLD, 1000),
    ],
)
def test_cap_per_purchase(amount, tier, expected):
    assert points_for_purchase(amount, tier) == expected
    assert expected <= MAX_POINTS_PER_PURCHASE


# ---- account.py -----------------------------------------------------------

def test_new_account():
    a = Account()
    assert a.balance() == 0
    assert a.tier() == BASIC


def test_example_from_request():
    a = Account()
    a.earn(60000)
    a.redeem(50)
    assert a.balance() == 550
    assert a.tier() == 1


def test_earn_adds_and_returns():
    a = Account()
    assert a.earn(1050) == 10
    assert a.balance() == 10
    assert a.earn(250) == 2
    assert a.balance() == 12


def test_earn_under_a_dollar_returns_zero():
    a = Account()
    assert a.earn(99) == 0
    assert a.balance() == 0


def test_earn_uses_tier_before_purchase():
    # A basic account's big purchase earns at 1/dollar even though it
    # lifts the account to silver.
    a = Account()
    assert a.earn(60000) == 600
    assert a.tier() == SILVER
    # The next purchase is at the silver rate.
    assert a.earn(10000) == 200
    assert a.balance() == 800


def test_earn_cap():
    a = Account()
    assert a.earn(100_000) == 1000
    assert a.balance() == 1000
    assert a.tier() == SILVER
    assert a.earn(100_000) == 1000   # silver: 2,000 capped to 1,000
    assert a.balance() == 2000
    assert a.tier() == GOLD
    assert a.earn(100_000) == 1000   # gold: 3,000 capped to 1,000
    assert a.balance() == 3000


def test_tier_promotion_boundaries():
    a = Account()
    a.earn(49900)                    # 499 points
    assert a.balance() == 499 and a.tier() == BASIC
    a.earn(100)                      # 500 points
    assert a.balance() == 500 and a.tier() == SILVER


def test_gold_at_2000():
    a = Account()
    for _ in range(2):
        a.earn(100_000)
    assert a.balance() == 2000
    assert a.tier() == GOLD


def test_gold_just_under_2000_is_silver():
    a = Account()
    a.earn(100_000)                  # 1000, silver
    a.earn(49_900)                   # 499 * 2 = 998 -> 1998
    a.earn(100)                      # 2 -> 2000
    assert a.tier() == GOLD
    b = Account()
    b.earn(100_000)
    b.earn(49_900)
    assert b.balance() == 1998 and b.tier() == SILVER


def test_redeem_success():
    a = Account()
    a.earn(10_000)                   # 100
    assert a.redeem(30) is True
    assert a.balance() == 70


def test_redeem_exact_balance():
    a = Account()
    a.earn(10_000)
    assert a.redeem(100) is True
    assert a.balance() == 0


def test_redeem_insufficient_leaves_account_unchanged():
    a = Account()
    a.earn(60000)                    # 600, silver
    assert a.redeem(601) is False
    assert a.balance() == 600
    assert a.tier() == SILVER


def test_redeem_on_empty_account():
    a = Account()
    assert a.redeem(1) is False
    assert a.balance() == 0


def test_tier_never_goes_down_silver():
    a = Account()
    a.earn(60000)                    # 600, silver
    assert a.redeem(600) is True
    assert a.balance() == 0
    assert a.tier() == SILVER


def test_tier_never_goes_down_gold():
    a = Account()
    a.earn(100_000)
    a.earn(100_000)                  # 2000, gold
    assert a.tier() == GOLD
    assert a.redeem(2000) is True
    assert a.balance() == 0
    assert a.tier() == GOLD


def test_earn_after_redeem_uses_kept_tier():
    # "The rate of the account's tier": the tier the account holds, which
    # it keeps after redeeming below the threshold.
    a = Account()
    a.earn(100_000)
    a.earn(100_000)                  # gold
    a.redeem(2000)
    assert a.earn(10_000) == 300     # 100 dollars at gold rate 3
    assert a.tier() == GOLD
    assert a.balance() == 300


def test_tier_is_nondecreasing_over_a_sequence():
    a = Account()
    seen = []
    for step in range(30):
        a.earn(100_000 if step % 3 else 1_000)
        a.redeem(900 if step % 2 else 1)
        seen.append(a.tier())
    assert seen == sorted(seen)
    assert seen[-1] == GOLD


# ---- validation (rule 5) --------------------------------------------------

@pytest.mark.parametrize("amount", [0, -1, -100, 100_001, 10**9])
def test_earn_out_of_range(amount):
    a = Account()
    with pytest.raises(ValueError):
        a.earn(amount)
    assert a.balance() == 0
    assert a.tier() == BASIC


@pytest.mark.parametrize("amount", [1, 100_000])
def test_earn_range_edges_accepted(amount):
    Account().earn(amount)


@pytest.mark.parametrize("points", [0, -1, -50, 100_001, 10**9])
def test_redeem_out_of_range(points):
    a = Account()
    a.earn(60000)
    with pytest.raises(ValueError):
        a.redeem(points)
    assert a.balance() == 600


@pytest.mark.parametrize("points", [1, 100_000])
def test_redeem_range_edges_accepted(points):
    a = Account()
    a.earn(60000)
    assert a.redeem(points) is (points <= 600)


def test_redeem_range_checked_before_balance():
    # Out-of-range raises even though the account could never cover it.
    a = Account()
    with pytest.raises(ValueError):
        a.redeem(100_001)
    with pytest.raises(ValueError):
        a.redeem(0)


def test_redeem_large_valid_amount_with_big_balance():
    a = Account()
    for _ in range(120):
        a.earn(100_000)              # 1,000 each -> 120,000
    assert a.balance() == 120_000
    assert a.redeem(100_000) is True
    assert a.balance() == 20_000
    assert a.tier() == GOLD


@pytest.mark.parametrize("bad", [1.5, 100.0, "100", None, True])
def test_non_int_rejected(bad):
    a = Account()
    with pytest.raises(TypeError):
        a.earn(bad)
    with pytest.raises(TypeError):
        a.redeem(bad)
    assert a.balance() == 0


def test_accounts_are_independent():
    a, b = Account(), Account()
    a.earn(60000)
    assert b.balance() == 0 and b.tier() == BASIC
