"""Points earned by a single purchase."""

from loyalty.tiers import points_per_dollar

MAX_POINTS_PER_PURCHASE = 1000
MIN_AMOUNT = 1          # cents
MAX_AMOUNT = 100_000    # cents


def points_earned(amount: int, tier: int) -> int:
    """Return the points a purchase of `amount` cents earns at `tier`.

    Only whole dollars count (amount // 100), each dollar earns the tier's rate,
    and no single purchase earns more than MAX_POINTS_PER_PURCHASE.
    """
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError("amount must be an int number of cents")
    if not MIN_AMOUNT <= amount <= MAX_AMOUNT:
        raise ValueError(f"amount must be between {MIN_AMOUNT} and {MAX_AMOUNT} cents")
    dollars = amount // 100
    return min(dollars * points_per_dollar(tier), MAX_POINTS_PER_PURCHASE)
