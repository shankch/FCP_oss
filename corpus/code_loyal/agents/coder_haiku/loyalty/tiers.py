"""Loyalty tiers and what each tier earns per dollar."""

BASIC = 0
SILVER = 1
GOLD = 2

SILVER_THRESHOLD = 500   # points needed for silver
GOLD_THRESHOLD = 2000    # points needed for gold

_POINTS_PER_DOLLAR = {BASIC: 1, SILVER: 2, GOLD: 3}


def tier_for_points(points: int) -> int:
    """Return the tier an account with this many points qualifies for.

    Fewer than 500 points is basic, 500 to 1,999 is silver, 2,000 or more is gold.
    This is the points-based tier only; an account's recorded tier can be higher
    because tiers never go down.
    """
    if points >= GOLD_THRESHOLD:
        return GOLD
    if points >= SILVER_THRESHOLD:
        return SILVER
    return BASIC


def points_per_dollar(tier: int) -> int:
    """Return how many points a tier earns for each whole dollar spent."""
    try:
        return _POINTS_PER_DOLLAR[tier]
    except KeyError:
        raise ValueError(f"unknown tier: {tier!r}") from None
