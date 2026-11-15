"""Points: how many points a purchase earns."""

from loyalty.tiers import points_per_dollar

CENTS_PER_DOLLAR = 100
MAX_POINTS_PER_PURCHASE = 1000


def points_for_purchase(amount: int, tier: int) -> int:
    """Return the points a purchase of `amount` cents earns at `tier`.

    Only whole dollars count (the cents are dropped), each earning the tier's
    rate, and no single purchase earns more than 1,000 points. Checking that
    `amount` is in range is the account's job; this function assumes it is.
    """
    dollars = amount // CENTS_PER_DOLLAR
    return min(dollars * points_per_dollar(tier), MAX_POINTS_PER_PURCHASE)
