# Prompt P-CARD-1: Fernwood Outfitters gift cards

Write a Python class for our gift cards:

    class GiftCard:
        def load(self, amount: int) -> int:
        def spend(self, amount: int) -> bool:
        def balance(self) -> int:

All amounts are in cents. A new card has a balance of 0.

Rules:

1. Raise ValueError if `amount` is less than 1 or more than 50,000.
2. `load` adds `amount` to the balance.
3. The balance is never more than $500.00: raise ValueError for a load that would take it over.
4. Every load of $100.00 or more earns a $5.00 bonus on the card. `load` returns the bonus it earned, in cents (0 if none).
5. `spend` takes `amount` off the balance and returns True if the balance covers it; otherwise it returns False and the balance stays as it was.
6. `balance` returns the balance.

Example: after `load(2000)` and `spend(500)`, `balance()` returns 1500.
