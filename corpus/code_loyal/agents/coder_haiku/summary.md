Implemented the loyalty package in /work/ws_loyal_impl_haiku/. The test run `/repo/.venv/bin/python -m pytest -q <that dir>` passes: 32 passed.

Files:
- loyalty/tiers.py: tier constants (BASIC=0, SILVER=1, GOLD=2), tier_for_points (<500 basic, 500-1999 silver, >=2000 gold), points_per_dollar (1/2/3).
- loyalty/points.py: points_earned(amount, tier) = min((amount // 100) * rate, 1000).
- loyalty/account.py: Account with earn, redeem, tier, balance. Starts at 0 points, basic tier.
- loyalty/__init__.py: re-exports Account and the helpers.
- test_loyalty.py: tests for the boundaries, the spec example (earn(60000) then redeem(50) gives 550 and tier 1), the cap, range checks, failed redeem leaving state unchanged, and tier never dropping.

Decisions where the request was unclear:
1. Earn rate: the rate uses the tier held before the purchase. The spec example requires this: with the post-purchase tier, the first $600 purchase would earn 1,000 (capped) and the balance would not be 550.
2. Tier persistence: the account stores the highest tier reached. After each earn it is raised to tier_for_points(balance) if that is higher. Redeem never changes it.
3. Whole dollars: amount // 100, so 99 cents earns 0 points. earn returns 0 without error.
4. Cap: the 1,000-point cap applies per purchase, after the tier rate.
5. Range checks: earn and redeem raise ValueError for out-of-range values, checked before any state change. For redeem, the range check runs before the balance check, so an out-of-range value raises even when the balance is short. An insufficient balance returns False.
6. Non-int arguments (including bool, float, str, None): I chose TypeError, because the request only specifies ValueError for range errors.
7. Range limits are inclusive: 1 and 100,000 are accepted.
8. Extra API beyond the spec: points.py and tiers.py also validate their inputs, and the package exposes tier_for_points, points_per_dollar and points_earned.
