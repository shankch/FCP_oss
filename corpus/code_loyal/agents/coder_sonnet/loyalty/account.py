"""Account: the class the shop uses."""

from loyalty.points import points_for_purchase
from loyalty.tiers import tier_for_points

MIN_AMOUNT = 1
MAX_AMOUNT = 100_000
MIN_REDEEM = 1
MAX_REDEEM = 100_000


def _check_int(value: int, name: str, low: int, high: int) -> None:
    # bool is a subclass of int, but True/False are not amounts of anything.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if value < low or value > high:
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")


class Account:
    def __init__(self) -> None:
        self._balance = 0
        self._tier = tier_for_points(0)

    def earn(self, amount: int) -> int:
        """Record a purchase of `amount` cents and return the points it earned.

        The purchase earns at the rate of the account's tier before the
        purchase; the tier is then raised if the new balance reaches a higher
        one.
        """
        _check_int(amount, "amount", MIN_AMOUNT, MAX_AMOUNT)
        earned = points_for_purchase(amount, self._tier)
        self._balance += earned
        self._tier = max(self._tier, tier_for_points(self._balance))
        return earned

    def redeem(self, points: int) -> bool:
        """Take `points` off the account if it has that many.

        Returns True on success. Otherwise returns False and changes nothing.
        Redeeming never lowers the tier.
        """
        _check_int(points, "points", MIN_REDEEM, MAX_REDEEM)
        if points > self._balance:
            return False
        self._balance -= points
        return True

    def tier(self) -> int:
        """Return the highest tier the account has reached."""
        return self._tier

    def balance(self) -> int:
        """Return the account's points."""
        return self._balance
