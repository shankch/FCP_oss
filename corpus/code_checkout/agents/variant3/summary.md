I couldn't run my Python check of the reference model (running it needed approval), so I checked the key cases by hand instead. Linting the formalization passes, and the English rendering from `fcp explain` matches what I meant for every item.

## Summary

I wrote `formal/variant3.yaml` with **14 items**: 12 properties, 1 scenario and the frame rule F-ZERO, which is added to every set automatically. It has 4 helper definitions (`valid`, `disc`, `exact`, `err`) and no ghost state.

| Requirement | Items |
|---|---|
| R-RET-1 | V3-RET-1: inputs in range → the call returns a valid pair (outcome 0) |
| R-ERR-1 | V3-ERR-1: inputs out of range → ValueError (outcome 1) |
| R-MEM-1 | V3-MEM-1: a member with no coupon pays 90% of the subtotal, rounded to a whole cent |
| R-COUP-1 | V3-COUP-1: a non-member pays (100 − coupon)% of the subtotal, for coupons up to 30 |
| R-STACK-1 | V3-STACK-1: discount = min(10·member + coupon, 30)%; V3-STACK-2: the 30% cap, true under either stacking reading |
| R-ROUND-1 | V3-ROUND-1: price is within half a cent of the exact discounted price; V3-ROUND-2: at exactly half a cent the price is even |
| R-SHIP-1 | V3-SHIP-1: shipping is 499 if the subtotal is under 5000, else 0 |
| R-MONO-1 | V3-MONO-1: comparing two calls, a larger subtotal never gives a smaller price + shipping |
| R-IN-2 | V3-IN-2: a non-member with no coupon pays exactly the subtotal |
| R-EX-1 | V3-EX-1 (scenario) and V3-EX-2 (property): (member, 10000, 0) → (9000, 0) |

**Readings taken** (all recorded under `decisions`):
- **R-ROUND-1, "the nearest cent":** reading 3, round half to even, as you directed. The notes of V3-ROUND-1 and V3-ROUND-2 say so.
- **R-STACK-1, "Discounts stack":** reading 1, the percentages add up.
- **R-SHIP-1, "Orders under $50":** reading 1, the subtotal before discounts.

**Not formalized, each with a reason and `covered_by`:**
- **R-SIG-1:** the function signature is fixed by the adapter.
- **R-IN-1:** a range definition, used in `valid`.
- **R-IN-3:** a definition of `member`.
- **R-FR-1:** this is frame rule F-ZERO.

## Problems in the specification

1. **Rule 7 contradicts rule 6, so no function can meet all requirements.** The $4.99 shipping cliff makes the amount charged drop as the subtotal grows. For example, with no membership and no coupon, a 4999-cent cart costs 4999 + 499 = 5498, but a 5000-cent cart costs 5000. This happens at every discount rate and under both readings of "Orders under $50". As instructed, I formalized V3-MONO-1 literally rather than repairing it, so FCP should report this conflict.
2. **Rule 4 overrides rule 3 for coupons 31–50.** The prompt accepts coupons up to 50%, but the 30% cap means coupons 31–50 all act like 30 (and for members, coupons 20–50 act the same). I read "never more than 30%" as winning over "a coupon takes `coupon` percent off" and restricted V3-COUP-1 to coupons up to 30. The note says so.
3. **The cap and rounding to the nearest cent can't both hold on the final price.** For example, a 2-cent cart with membership and a 20% coupon is exactly 1.4 cents, which rounds to 1: a 50% discount. I applied the cap to the discount rate before rounding (rule 5 rounds the already-discounted price). V3-STACK-2 allows the shortfall from rounding, and its note explains this.
4. **Two more ambiguous phrases.** "Discounts stack" and "Orders under $50" are flagged ambiguous, but you didn't specify a reading for either. The example (a member, a $100 cart, no coupon) can't tell the readings apart.