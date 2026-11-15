I wrote the `loyalty` package and its tests. The full suite passes: `pytest -q` on the directory gives 72 passed, and nothing needed fixing.

**What the package does** (all under /work/ws_loyal_impl_opus/loyalty/):
- `tiers.py` defines the tiers BASIC=0, SILVER=1 and GOLD=2, with thresholds at 500 and 2,000 points. `tier_for_points(points)` gives the tier for a number of points (rule 1). `earn_rate(tier)` gives 1, 2 or 3 points per dollar (rule 2).
- `points.py` has `purchase_points(amount, tier)`, which works out `min((amount // 100) * earn_rate(tier), 1000)` (rules 3 and 4).
- `account.py` has `Account` with `earn`, `redeem`, `tier` and `balance`. It stores the balance and the highest tier reached so far, so the tier never goes down.
- `__init__.py` re-exports the public names.

**Tests** are in /work/ws_loyal_impl_opus/test_loyalty.py. They cover:
- the example in the request;
- every tier and cap boundary;
- validation errors leaving the account unchanged;
- a failed redeem leaving the account unchanged, and redeeming exactly the balance;
- the tier not going down;
- a random check of 200 accounts × 60 operations against a small reference model.

**Decisions where the request was unclear:**
1. **Which tier sets the earning rate.** The rate comes from the tier `tier()` returns, which is the highest tier the account has reached. So a gold member who spends their balance down to 0 still earns 3 points per dollar.
2. **When a purchase moves an account up a tier.** A purchase earns at the tier held before it. If that purchase lifts the account into a new tier, only later purchases earn at the new rate. For example, at 499 points, `earn(10000)` earns 100 points, not 200.
3. **What "points" means for tiers.** Tiers go by the current balance, the same number `balance()` returns, not lifetime points earned. Because the tier never goes down, the tier is in effect set by the highest balance the account has ever had.
4. **Order of the cap.** The 1,000-point cap applies after multiplying by the tier rate. So silver reaches the cap at $500 and gold at about $334. Basic only reaches it at the $1,000 maximum.
5. **Purchases under $1.** Amounts from 1 to 99 cents are valid, earn 0 points, and `earn` returns 0. Leftover cents are dropped, not rounded.
6. **Redeem checks.** The 1 to 100,000 range check runs before the balance check. An out-of-range request raises ValueError even on an empty account. Redeeming exactly the balance succeeds. Redeeming never changes the tier.
7. **Wrong argument types.** The request says nothing about these. Non-int arguments, including `True`/`False` and floats like `100.0`, raise TypeError rather than ValueError.
8. **Where the range check lives.** The 1 to 100,000 checks of rule 5 are in `Account`. The helpers in `tiers.py` and `points.py` only reject negatives (ValueError) and unknown tiers (ValueError).
9. **Constructor.** `Account()` takes no arguments and starts at 0 points, basic. There is no upper limit on the balance.
