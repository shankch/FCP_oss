import pytest

from loyalty import Account
from loyalty.points import MAX_POINTS_PER_PURCHASE, points_earned
from loyalty.tiers import BASIC, GOLD, SILVER, points_per_dollar, tier_for_points


# ---- tiers.py ----

@pytest.mark.parametrize(
    "points, tier",
    [(0, BASIC), (499, BASIC), (500, SILVER), (1999, SILVER), (2000, GOLD), (50_000, GOLD)],
)
def test_tier_for_points_boundaries(points, tier):
    assert tier_for_points(points) == tier


def test_points_per_dollar_by_tier():
    assert [points_per_dollar(t) for t in (BASIC, SILVER, GOLD)] == [1, 2, 3]


def test_points_per_dollar_rejects_unknown_tier():
    with pytest.raises(ValueError):
        points_per_dollar(3)


# ---- points.py ----

def test_points_earned_counts_whole_dollars_only():
    assert points_earned(1999, BASIC) == 19
    assert points_earned(99, GOLD) == 0


def test_points_earned_uses_tier_rate():
    assert points_earned(1000, BASIC) == 10
    assert points_earned(1000, SILVER) == 20
    assert points_earned(1000, GOLD) == 30


def test_points_earned_capped_at_1000():
    assert points_earned(100_000, BASIC) == MAX_POINTS_PER_PURCHASE
    assert points_earned(100_000, GOLD) == MAX_POINTS_PER_PURCHASE
    assert points_earned(34_000, GOLD) == 1000  # 340 dollars * 3 = 1020


@pytest.mark.parametrize("amount", [0, -5, 100_001])
def test_points_earned_rejects_bad_amount(amount):
    with pytest.raises(ValueError):
        points_earned(amount, BASIC)


# ---- account.py ----

def test_new_account_is_basic_with_no_points():
    acct = Account()
    assert acct.balance() == 0
    assert acct.tier() == BASIC


def test_spec_example():
    acct = Account()
    assert acct.earn(60000) == 600   # bought at basic rate, 1 point per dollar
    assert acct.tier() == SILVER
    assert acct.redeem(50) is True
    assert acct.balance() == 550
    assert acct.tier() == SILVER


def test_earn_returns_and_adds_points():
    acct = Account()
    assert acct.earn(1500) == 15
    assert acct.balance() == 15


def test_rate_uses_tier_before_the_purchase():
    # Basic purchase of $600 gives 600 (silver reached). The next purchase
    # uses silver rate (2/dollar), so $100 earns 200, not 100.
    acct = Account()
    acct.earn(60000)
    assert acct.earn(10000) == 200
    assert acct.balance() == 800


def test_gold_reached_and_rate_applies_next_purchase():
    acct = Account()
    acct.earn(60000)              # 600, silver
    acct.earn(60000)              # silver rate: 1000 capped, total 1600 -> silver
    assert acct.balance() == 1600
    assert acct.tier() == SILVER
    acct.earn(50000)              # silver rate: 1000 -> total 2600 -> gold
    assert acct.balance() == 2600
    assert acct.tier() == GOLD
    assert acct.earn(10000) == 300  # gold rate 3/dollar


def test_tier_does_not_go_down_after_redeem():
    acct = Account()
    acct.earn(60000)
    acct.earn(60000)
    acct.earn(50000)
    assert acct.tier() == GOLD
    assert acct.redeem(2600) is True
    assert acct.balance() == 0
    assert acct.tier() == GOLD
    assert acct.earn(100) == 3  # still gold rate


def test_redeem_insufficient_returns_false_and_leaves_account_unchanged():
    acct = Account()
    acct.earn(2000)              # 20 points
    assert acct.redeem(21) is False
    assert acct.balance() == 20
    assert acct.redeem(20) is True
    assert acct.balance() == 0


def test_redeem_on_empty_account_returns_false():
    assert Account().redeem(1) is False


def test_earn_rejects_out_of_range_amount():
    acct = Account()
    with pytest.raises(ValueError):
        acct.earn(0)
    with pytest.raises(ValueError):
        acct.earn(100_001)
    assert acct.balance() == 0


def test_earn_accepts_range_limits():
    acct = Account()
    assert acct.earn(1) == 0
    assert acct.earn(100_000) == 1000


@pytest.mark.parametrize("points", [0, -1, 100_001])
def test_redeem_rejects_out_of_range_points(points):
    acct = Account()
    acct.earn(10000)
    with pytest.raises(ValueError):
        acct.redeem(points)
    assert acct.balance() == 100


def test_redeem_accepts_upper_limit_when_funded_enough():
    acct = Account()
    for _ in range(10):
        acct.earn(100_000)       # 1000 each, capped
    assert acct.balance() == 10_000  # silver then gold, capped each time
    assert acct.redeem(100_000) is False
    assert acct.redeem(10_000) is True
    assert acct.balance() == 0


@pytest.mark.parametrize("bad", [10.0, "100", None, True])
def test_non_int_arguments_raise_type_error(bad):
    acct = Account()
    with pytest.raises(TypeError):
        acct.earn(bad)
    with pytest.raises(TypeError):
        acct.redeem(bad)
    assert acct.balance() == 0
