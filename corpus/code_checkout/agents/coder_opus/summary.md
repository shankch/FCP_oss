I wrote `checkout()` and its tests, and all 745 tests pass. The request has one real conflict, between rules 6 and 7, so the function has to bend rule 6 slightly to keep rule 7.

Decisions where the request was unclear:
1. Rule 6 vs rule 7. Taken literally, rule 6 makes a $49.99 cart cost $54.98 while a $50.00 cart costs $50.00. Rule 7 says "must never", so it wins. Orders under $50 still pay $4.99, but the fee is cut so that price plus shipping never goes over $50.00: orders up to $45.01 pay the full $4.99; orders from $45.02 to $49.99 pay exactly enough to total $50.00; orders of $50 or more always ship free.
2. The $50 is measured on the discounted, rounded price, not the cart total before discounts.
3. Discounts add up: a member with a 15% coupon gets 25% off.
4. The 30% cap applies to everyone, including a non-member with only a coupon. The team should confirm this one.
5. Rounding: a price that lands exactly on a half cent rounds up, unlike Python's built-in `round()`.
6. Shipping is decided on the rounded price, so $49.995 becomes $50.00 and ships free.
7. A $0 cart returns `(0, 499)`, which is rule 6 taken literally.
8. Ranges include both ends.
9. Wrong types raise `TypeError`, not `ValueError`.
10. Rule 7 is read as: with the same coupon and membership, a bigger cart never lowers price plus shipping.
