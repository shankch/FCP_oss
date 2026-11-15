"""How many points a purchase earns."""
from .tiers import rate

CAP = 1000


def earned(amount: int, tier: int) -> int:
    dollars = amount // 100
    return min(CAP, dollars * rate(tier))
