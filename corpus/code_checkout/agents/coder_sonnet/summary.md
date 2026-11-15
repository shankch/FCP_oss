`checkout()` is written and tested, but rules 6 and 7 of the request contradict each other, so rule 7 cannot hold. I implemented rule 6 as written.

The conflict: rule 6 drops shipping from $4.99 to $0 at $50.00, so adding an item lowers the amount charged at that point. With no discount, a $49.99 cart is charged 4999 + 499 = 5498 and a $50.00 cart is charged 5000. Rule 7 holds at every other step. It fails only at subtotal 4999 to 5000, for every coupon and member combination. If rule 7 must win, the fee has to be phased out below $50, which changes rule 6. I didn't make that call.

Other decisions where the request was unclear:
- Stacking is additive: member 10 plus coupon N, then capped at 30.
- The 30% cap covers a coupon on its own: coupons of 31 to 50 are accepted but act as 30.
- Rounding: one rounding, on the final price, to the nearest cent, with exact half cents rounding up. Integer arithmetic.
- Free shipping is decided on the subtotal before discounts.
- An empty cart (subtotal 0) pays the $4.99 fee.
- Both ends of the ranges are valid.
- Wrong types raise `TypeError` (not requested).

Tests: 196 passed and 1 xfailed; the strict xfail holds the full, unconditional rule 7, so every run reports the open conflict.
