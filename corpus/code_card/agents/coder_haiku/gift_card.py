"""Fernwood Outfitters gift cards. All amounts are in cents."""

MIN_AMOUNT = 1
MAX_AMOUNT = 50_000       # $500.00
MAX_BALANCE = 50_000      # $500.00
BONUS_THRESHOLD = 10_000  # $100.00
BONUS = 500               # $5.00


class GiftCard:
    def __init__(self) -> None:
        self._balance = 0

    @staticmethod
    def _check_amount(amount: int) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("amount must be an int number of cents")
        if amount < MIN_AMOUNT or amount > MAX_AMOUNT:
            raise ValueError(
                f"amount must be between {MIN_AMOUNT} and {MAX_AMOUNT} cents"
            )

    def load(self, amount: int) -> int:
        """Add amount to the balance. Return the bonus earned (0 if none)."""
        self._check_amount(amount)
        bonus = BONUS if amount >= BONUS_THRESHOLD else 0
        new_balance = self._balance + amount + bonus
        if new_balance > MAX_BALANCE:
            raise ValueError(
                f"load would take the balance over {MAX_BALANCE} cents"
            )
        self._balance = new_balance
        return bonus

    def spend(self, amount: int) -> bool:
        """Deduct amount if the balance covers it. Return True if spent."""
        self._check_amount(amount)
        if amount > self._balance:
            return False
        self._balance -= amount
        return True

    def balance(self) -> int:
        return self._balance
