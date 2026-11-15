The `loyalty` package and `test_loyalty.py` are written, and all 74 tests pass with the pytest command you gave.

**Files** (all under `/work/ws_loyal_impl_sonnet/`):
- `loyalty/tiers.py`:
  - Constants `BASIC`, `SILVER` and `GOLD` (0, 1, 2) and the thresholds 500 and 2000.
  - `tier_for_points(points)` for rule 1, and `points_per_dollar(tier)` for rule 2. It raises `ValueError` for an unknown tier.
- `loyalty/points.py`: `points_for_purchase(amount, tier)` returns `min((amount // 100) * rate, 1000)` for rules 3 and 4.
- `loyalty/account.py`: `Account` with `earn`, `redeem`, `tier` and `balance`. It holds the rule 5 range checks (1 to 100,000 for both `amount` and `points`) and the rule 9 "tier never goes down" logic.
- `loyalty/__init__.py`: re-exports `Account`. The request named only three modules; this file is what makes `from loyalty import Account` work.
- `test_loyalty.py`: covers tier boundaries (0, 499, 500, 1999, 2000), rates, whole-dollar truncation, the 1,000 cap at its edges, and the example from the request. It also covers earn, redeem and the range-check edges, the tier staying put after redeeming, and non-int inputs.

**Decisions where the request was unclear:**
1. **Which tier sets the earn rate.** A purchase earns at the account's tier before the purchase, and the tier is raised afterwards if the new balance reaches a higher one. The example forces this: `earn(60000)` on a new account must give 600 points. Earning at the new silver rate would give 1,000 and a balance of 950, not 550.
2. **Rule 9 applies to the earn rate too.** Rule 3 says "the rate of the account's tier", and `tier()` is the tier the account has kept. So a gold account that redeems down to 0 points still earns at 3 per dollar. Rating on the current balance instead would be a one-line change in `Account.earn`.
3. **How the tier is kept.** The account stores its tier and sets it to `max(stored tier, tier_for_points(balance))` after each earn. `tier_for_points` stays a pure function of the points total. Redeeming never changes the tier.
4. **"Whole dollar" means `amount // 100`.** A purchase under 100 cents is valid and earns 0 points. It does not raise.
5. **Validation order in `redeem`.** The range check on `points` runs first. So `redeem(100_001)` raises `ValueError` even though the account could never cover it. A rejected `earn` or `redeem` leaves the account unchanged.
6. **Non-integer inputs.** The request only says `ValueError` for out-of-range values. I made floats, strings, `None` and bools raise `TypeError`, which is the Python convention. A caller that catches only `ValueError` would not catch these.
7. **Where the range checks live.** `points.py` does not check that `amount` is in range. It assumes `Account` already did.
8. **Reaching exactly 2,000.** A balance of exactly 2,000 makes the account gold, and the same boundary applies at 500 for silver.
