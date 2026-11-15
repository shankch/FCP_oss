"""How many points a purchase earns."""

from loyalty.tiers import _require_int, earn_rate

CENTS_PER_DOLLAR = 100
MAX_POINTS_PER_PURCHASE = 1_000  # rule 4


def purchase_points(amount: int, tier: int) -> int:
    """Return the points a purchase of ``amount`` cents earns at ``tier``.

    Each whole dollar of ``amount`` earns the tier's rate (rule 3); any
    leftover cents earn nothing. The result is capped at 1,000 points
    (rule 4), the cap applying after the tier's rate is applied.

    The 1 to 100,000 cent range of rule 5 is enforced by ``Account``; here
    ``amount`` only has to be a non-negative int.
    """
    _require_int(amount, "amount")
    if amount < 0:
        raise ValueError(f"amount must not be negative, got {amount}")
    dollars = amount // CENTS_PER_DOLLAR
    return min(dollars * earn_rate(tier), MAX_POINTS_PER_PURCHASE)
