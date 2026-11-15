"""Tiers: which tier a points total reaches and what a tier earns."""

BASIC = 0
SILVER = 1
GOLD = 2

SILVER_THRESHOLD = 500
GOLD_THRESHOLD = 2000

# Points earned per whole dollar spent, indexed by tier.
POINTS_PER_DOLLAR = {BASIC: 1, SILVER: 2, GOLD: 3}


def tier_for_points(points: int) -> int:
    """Return the tier that a total of `points` reaches.

    Fewer than 500 points is basic, 500 to 1,999 is silver, 2,000 or more is
    gold. This looks at the number alone; an account never drops a tier it has
    reached, but that is the account's business (see account.py).
    """
    if points >= GOLD_THRESHOLD:
        return GOLD
    if points >= SILVER_THRESHOLD:
        return SILVER
    return BASIC


def points_per_dollar(tier: int) -> int:
    """Return how many points one whole dollar earns in `tier`."""
    try:
        return POINTS_PER_DOLLAR[tier]
    except KeyError:
        raise ValueError(f"unknown tier: {tier!r}") from None
