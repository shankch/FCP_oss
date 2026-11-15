I made the change to `checkout.py` and updated `test_checkout.py`. All 45 tests pass with your pytest command.

**The change**
- `checkout()` now has the signature from the request, with `student: bool = False`. Existing three-argument calls behave exactly as before.
- Students get 15 points added to the coupon and membership discounts, and the total is still capped at 30%.
- Students get free shipping from $75. Everyone else still gets it from $50.
- I updated the docstring to match.

**Tests**
- I kept all the old tests.
- I added a test that compares non-student results with a frozen copy of the old function. It covers every coupon value, both membership values and 16 cart totals, including the $50 and $75 edges.
- I added student tests for:
  - the example from the request, `(8500, 0)`;
  - the 15% adding to the coupon and the membership, and the 30% cap;
  - rounding;
  - $74.99 paying shipping and $75.00 shipping free;
  - the lowest and highest allowed inputs;
  - invalid inputs, with `student` both True and False.

**Decisions where the request was unclear**
1. **Who gets the $75 threshold.** Point 2 doesn't say, and if it applied to everyone, point 3 would break: a non-student with a $60 cart would start paying $4.99. I applied it to students only, because that satisfies all four points.
   - This has an odd result. If a student's coupon and membership already add up to 21% or more, the 15% adds little or nothing under the cap, but they now pay shipping on carts of $50.00 to $74.99. So the student flag can raise their total, by up to $4.99 when they are already at 30%. I checked this by running every coupon, membership and cart total in that range.
   - If the team meant $75 for everyone, it's a one-line change (`free_shipping_from = 7500`), but it breaks point 3 and two of the new tests.
2. **What the $75 is compared with.** I kept comparing it with the cart total before discounts, as the existing code does for $50. The request's example doesn't settle this. So a student's $80 cart, priced at $68 after the discount, ships free.
3. **Everything else is unchanged:** rounding, the $4.99 fee and the input limits. `student` isn't type-checked, the same as `member`.

Running pytest also created `__pycache__` and `.pytest_cache` in the directory.

Files are in the working directory:
- `checkout.py`
- `test_checkout.py`
