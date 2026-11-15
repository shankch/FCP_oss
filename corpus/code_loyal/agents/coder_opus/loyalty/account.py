"""The loyalty account the shop uses."""

from loyalty.points import purchase_points
from loyalty.tiers import BASIC, _require_int, tier_for_points

MIN_AMOUNT = 1  # cents (rule 5)
MAX_AMOUNT = 100_000  # cents (rule 5)
MIN_REDEEM = 1  # points (rule 5)
MAX_REDEEM = 100_000  # points (rule 5)


def _check_range(value, name, low, high):
    _require_int(value, name)
    if value < low or value > high:
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")


class Account:
    """A loyalty account. A new account has 0 points and is basic."""

    def __init__(self) -> None:
        self._points = 0
        # Highest tier the account has reached; never goes down (rule 9).
        self._tier = BASIC

    def earn(self, amount: int) -> int:
        """Credit a purchase of ``amount`` cents and return the points earned.

        The purchase earns at the account's tier as it stands before the
        purchase (the tier ``tier()`` returns); the points it earns can then
        lift the account into a higher tier for later purchases.
        """
        _check_range(amount, "amount", MIN_AMOUNT, MAX_AMOUNT)
        earned = purchase_points(amount, self._tier)
        self._points += earned
        self._tier = max(self._tier, tier_for_points(self._points))
        return earned

    def redeem(self, points: int) -> bool:
        """Take ``points`` off the account if it holds that many.

        Returns True on success. Returns False, leaving the account
        unchanged, if the balance is smaller than ``points``.
        """
        _check_range(points, "points", MIN_REDEEM, MAX_REDEEM)
        if points > self._points:
            return False
        self._points -= points
        return True

    def tier(self) -> int:
        """Return the highest tier the account has reached (0, 1 or 2)."""
        return self._tier

    def balance(self) -> int:
        """Return the account's points."""
        return self._points

    def __repr__(self) -> str:
        return f"Account(balance={self._points}, tier={self._tier})"
