# Prompt P-LOY-1: Fernwood Outfitters loyalty points

Write a Python package `loyalty` for our loyalty programme, in three modules:

- `loyalty/tiers.py`: which tier an account is in and what a tier earns;
- `loyalty/points.py`: how many points a purchase earns;
- `loyalty/account.py`: the class our shop uses:

      class Account:
          def earn(self, amount: int) -> int:
          def redeem(self, points: int) -> bool:
          def tier(self) -> int:
          def balance(self) -> int:

A new account has 0 points. `amount` is the price of a purchase in cents. The tiers are 0 (basic), 1 (silver) and 2 (gold).

Rules for `tiers.py`:

1. An account with fewer than 500 points is basic, one with 500 to 1,999 points is silver, and one with 2,000 points or more is gold.
2. Basic earns 1 point for each dollar, silver 2 and gold 3.

Rules for `points.py`:

3. A purchase earns points for each whole dollar of `amount`, at the rate of the account's tier.
4. No purchase earns more than 1,000 points.

Rules for `account.py`:

5. Raise ValueError if `amount` is less than 1 or more than 100,000, or if `points` is less than 1 or more than 100,000.
6. `earn` adds the points the purchase earns to the account and returns them.
7. `redeem` takes `points` off the account and returns True if the account has that many; otherwise it returns False and the account stays as it was.
8. `tier` returns the account's tier, and `balance` returns its points.
9. Members keep what they have reached: the tier that `tier` returns never goes down.

Example: after `earn(60000)` and `redeem(50)`, `balance()` returns 550 and `tier()` returns 1.
