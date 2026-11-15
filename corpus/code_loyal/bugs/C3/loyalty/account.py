"""The account of a member of the loyalty programme."""
from .points import earned
from .tiers import tier_of


class Account:
    def __init__(self) -> None:
        self._points = 0

    def earn(self, amount: int) -> int:
        if not 1 <= amount <= 100_000:
            raise ValueError('an amount is 1 to 100,000 cents')
        got = earned(amount, tier_of(self._points))
        self._points += got
        return got

    def redeem(self, points: int) -> bool:
        if not 1 <= points <= 100_000:
            raise ValueError('points are 1 to 100,000')
        if points > self._points:
            return False
        self._points -= points
        return True

    def tier(self) -> int:
        return tier_of(self._points)

    def balance(self) -> int:
        return self._points
