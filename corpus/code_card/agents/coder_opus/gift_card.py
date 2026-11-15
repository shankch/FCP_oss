"""Gift cards for Fernwood Outfitters.

All amounts are integer cents.
"""

MIN_AMOUNT = 1            # smallest amount accepted by load or spend
MAX_AMOUNT = 50_000       # largest amount accepted by load or spend ($500.00)
MAX_BALANCE = 50_000      # the balance is never more than $500.00
BONUS_THRESHOLD = 10_000  # loads of $100.00 or more earn a bonus
BONUS = 500               # the bonus is $5.00


class GiftCard:
    """A stored-value gift card. A new card has a balance of 0."""

    def __init__(self) -> None:
        self._balance = 0

    @staticmethod
    def _check_amount(amount: int) -> None:
        # bool is a subclass of int, but True/False are not amounts.
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError(f"amount must be an int number of cents, got {amount!r}")
        if amount < MIN_AMOUNT or amount > MAX_AMOUNT:
            raise ValueError(
                f"amount must be between {MIN_AMOUNT} and {MAX_AMOUNT} cents, got {amount}"
            )

    def load(self, amount: int) -> int:
        """Add `amount` to the balance and return the bonus earned, in cents.

        A load of BONUS_THRESHOLD or more also adds BONUS to the balance.
        Raises ValueError, leaving the balance unchanged, if `amount` is out
        of range or if the load plus its bonus would take the balance over
        MAX_BALANCE.
        """
        self._check_amount(amount)
        bonus = BONUS if amount >= BONUS_THRESHOLD else 0
        new_balance = self._balance + amount + bonus
        if new_balance > MAX_BALANCE:
            raise ValueError(
                f"load of {amount} (bonus {bonus}) would take the balance from "
                f"{self._balance} to {new_balance}, over the {MAX_BALANCE} limit"
            )
        self._balance = new_balance
        return bonus

    def spend(self, amount: int) -> bool:
        """Take `amount` off the balance if the balance covers it.

        Returns True on success. Returns False, leaving the balance
        unchanged, if the balance is less than `amount`. Raises ValueError
        if `amount` is out of range.
        """
        self._check_amount(amount)
        if amount > self._balance:
            return False
        self._balance -= amount
        return True

    def balance(self) -> int:
        """Return the balance, in cents."""
        return self._balance
