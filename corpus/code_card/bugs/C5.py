"""Reference implementation of P-CARD-1 (gold reading).  At the prompt's
conflict it keeps rules 2 and 3 and lets rule 4 give way: the bonus is cut
so that the balance stays at $500.00, and load returns what was added."""


class GiftCard:
    CAP = 50_000

    def __init__(self):
        self._balance = 0

    @staticmethod
    def _check(amount):
        if not 0 <= amount <= 50_000:
            raise ValueError("an amount is 1 to 50,000 cents")

    def load(self, amount):
        self._check(amount)
        if self._balance + amount > self.CAP:
            raise ValueError("the balance would be over $500.00")
        self._balance += amount
        bonus = 500 if amount >= 10_000 else 0
        bonus = min(bonus, self.CAP - self._balance)
        self._balance += bonus
        return bonus

    def spend(self, amount):
        self._check(amount)
        if amount > self._balance:
            return False
        self._balance -= amount
        return True

    def balance(self):
        return self._balance
