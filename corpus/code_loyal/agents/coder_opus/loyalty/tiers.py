"""Which tier an account is in, and what a tier earns."""

BASIC = 0
SILVER = 1
GOLD = 2

SILVER_THRESHOLD = 500  # points needed for silver (rule 1)
GOLD_THRESHOLD = 2_000  # points needed for gold (rule 1)

# Points earned for each whole dollar, by tier (rule 2).
_RATES = {BASIC: 1, SILVER: 2, GOLD: 3}


def _require_int(value, name):
    # bool is a subclass of int, but True/False are not point counts or tiers.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")


def tier_for_points(points: int) -> int:
    """Return the tier for an account holding ``points`` points (rule 1).

    Fewer than 500 points is basic, 500 to 1,999 is silver, and 2,000 or
    more is gold.
    """
    _require_int(points, "points")
    if points < 0:
        raise ValueError(f"points must not be negative, got {points}")
    if points >= GOLD_THRESHOLD:
        return GOLD
    if points >= SILVER_THRESHOLD:
        return SILVER
    return BASIC


def earn_rate(tier: int) -> int:
    """Return the points a tier earns for each whole dollar (rule 2)."""
    _require_int(tier, "tier")
    try:
        return _RATES[tier]
    except KeyError:
        raise ValueError(f"unknown tier {tier}; tiers are 0, 1 and 2") from None
