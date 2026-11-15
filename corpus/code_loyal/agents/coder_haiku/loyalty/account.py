"""The loyalty account used by the shop."""

from loyalty.points import MAX_AMOUNT, MIN_AMOUNT, points_earned
from loyalty.tiers import BASIC, tier_for_points

MIN_POINTS = 1
MAX_POINTS = 100_000


def _check_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, not {type(value).__name__}")
    return value


class Account:
    """A member account holding points and the highest tier it has reached."""

    def __init__(self) -> None:
        self._balance = 0
        self._tier = BASIC

    def earn(self, amount: int) -> int:
        """Record a purchase of `amount` cents and return the points it earned.

        The rate is set by the tier the account holds before the purchase.
        Afterwards the tier is raised if the new balance qualifies for a higher one.
        """
        _check_int("amount", amount)
        if not MIN_AMOUNT <= amount <= MAX_AMOUNT:
            raise ValueError(f"amount must be between {MIN_AMOUNT} and {MAX_AMOUNT} cents")
        earned = points_earned(amount, self._tier)
        self._balance += earned
        self._tier = max(self._tier, tier_for_points(self._balance))
        return earned

    def redeem(self, points: int) -> bool:
        """Take `points` off the balance if there are enough; return whether it succeeded.

        On failure the account is left unchanged. The tier never goes down.
        """
        _check_int("points", points)
        if not MIN_POINTS <= points <= MAX_POINTS:
            raise ValueError(f"points must be between {MIN_POINTS} and {MAX_POINTS}")
        if points > self._balance:
            return False
        self._balance -= points
        return True

    def tier(self) -> int:
        """Return the highest tier the account has reached."""
        return self._tier

    def balance(self) -> int:
        """Return the points the account currently holds."""
        return self._balance
