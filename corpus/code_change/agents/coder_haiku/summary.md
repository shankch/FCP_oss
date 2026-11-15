The change is made and all 22 tests pass (10 existing, 12 new). Item 2 conflicts with item 3, so I applied the $75 threshold to students only.

**Change** (`checkout.py`)
- New parameter `student: bool = False`, so existing callers are unaffected.
- Students get 15% off, added to the coupon and membership discounts before the existing 30% cap.
- Free shipping starts at $75 for students and stays at $50 for everyone else.
- Docstring describes the new parameter and threshold.

**Tests** (`test_checkout.py`)
- The 10 existing tests are unchanged. I only removed "as it was before the change" from the module docstring, since it is no longer accurate.
- The 12 new tests cover stacking with a coupon and with membership, the cap, rounding, the $75 threshold for students, and that non-students still get free shipping from $50 with no student discount.

**Decisions where the request was unclear**
1. **Items 2 and 3 conflict.** Applying $75 to everyone would charge non-students $4.99 on $50 to $74.99 orders, which item 3 forbids. I applied it to students only. So a student with a $60 cart pays $4.99 shipping, while a non-student with the same cart ships free. If you want $75 for everyone, tell me and I will change the threshold for all customers and update the non-student shipping test. That breaks item 3 for non-students in that band, so please confirm which you want.
2. The threshold is compared with the subtotal before discounts, as the $50 rule was.
3. "Starts at $75" is inclusive: a $75.00 order ships free, matching "$50 or more".
