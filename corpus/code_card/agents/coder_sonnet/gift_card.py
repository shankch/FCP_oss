"""Fernwood Outfitters gift cards. All amounts are integer cents."""

MIN_AMOUNT = 1
MAX_AMOUNT = 50_000        # $500.00, the largest single load or spend
MAX_BALANCE = 50_000       # $500.00, the most a card may ever hold
BONUS_THRESHOLD = 10_000   # a load of $100.00 or more earns the bonus
BONUS = 500                # $5.00, flat per qualifying load


def _check_amount(amount) -> None:
    # bool is a subclass of int, but True/False are not money amounts.
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError(f"amount must be an int number of cents, got {type(amount).__name__}")
    if amount < MIN_AMOUNT or amount > MAX_AMOUNT:
        raise ValueError(f"amount must be between {MIN_AMOUNT} and {MAX_AMOUNT} cents, got {amount}")


class GiftCard:
    def __init__(self) -> None:
        self._balance = 0

    def load(self, amount: int) -> int:
        """Add `amount` cents to the card; return the bonus (in cents) it earned.

        The bonus is added to the balance too, so the balance cap is checked
        against amount + bonus. A rejected load leaves the card unchanged.
        """
        _check_amount(amount)
        bonus = BONUS if amount >= BONUS_THRESHOLD else 0
        if self._balance + amount + bonus > MAX_BALANCE:
            raise ValueError(
                f"loading {amount} (+{bonus} bonus) would take the balance "
                f"{self._balance} over {MAX_BALANCE}"
            )
        self._balance += amount + bonus
        return bonus

    def spend(self, amount: int) -> bool:
        """Take `amount` cents off the card. False (balance unchanged) if it does not cover it."""
        _check_amount(amount)
        if amount > self._balance:
            return False
        self._balance -= amount
        return True

    def balance(self) -> int:
        return self._balance
