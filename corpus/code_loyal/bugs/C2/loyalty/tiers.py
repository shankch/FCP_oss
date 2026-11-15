"""Which tier an account is in, and what a tier earns."""

BASIC, SILVER, GOLD = 0, 1, 2

RATES = {BASIC: 1, SILVER: 2, GOLD: 2}


def tier_of(points: int) -> int:
    if points >= 2000:
        return GOLD
    if points >= 500:
        return SILVER
    return BASIC


def rate(tier: int) -> int:
    return RATES[tier]
