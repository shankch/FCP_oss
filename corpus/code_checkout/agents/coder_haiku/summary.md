Implemented `checkout` with a pytest suite. All 134 tests pass on the first run. I also checked rule 7 exhaustively over the full subtotal range for all 31 discount levels, with no violations.

How it works: integer-only math. The discount is 10 (member) plus the coupon, capped at 30%. The price is `subtotal × (100 − discount) / 100`, rounded half up to the cent. Shipping is $4.99 if the price is under $50. Otherwise it is `max(0, 5498 − price)` cents.

Decisions where the request was unclear:

1. Rules 6 and 7 conflict at $50. A full-price $49.99 order costs $54.98 with shipping, but a $50.00 order with free shipping would cost only $50.00, so adding an item would lower the charge. I kept the discounted price exact and made shipping taper on orders of $50 or more. A $50.00 cart pays $4.98, and shipping reaches $0 at a $54.98 charge. This never charges less than the literal rules would. The cost is that "ship free" does not hold for discounted prices from $50.00 to $54.98.
2. "Discounts stack" means additive. Member 10% plus coupon, capped at 30%.
3. The $50 shipping threshold uses the discounted price, not the pre-discount subtotal.
4. Ties round half up. A $10.05 member cart gives 905 cents. Python's `round()` would give 904.
5. Validation. Out-of-range subtotal or coupon raises `ValueError`; the ranges are inclusive. Non-integers, including floats and bools, raise `TypeError`. `member` is used for truthiness.
6. Empty cart. A subtotal of 0 is accepted and pays $4.99 shipping, because rule 6 applies literally.
