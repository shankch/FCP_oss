I've written `formal/variant2.yaml`. `fcp lint` reports no errors, and I read back the `fcp explain` output: every item says what I meant it to. I also wanted to run a small Python script to double-check the numbers quoted in the notes, but it needed approval and didn't run. I worked those numbers out by hand instead (they're simple integer sums), so the script never ran.

**Items: 12** (11 properties and 1 scenario; the frame rule F-ZERO is added to the set automatically)
- Return and error: `V2-RET-1` (arguments in range → outcome 0) and `V2-ERR-1` (out of range → ValueError).
- Price: `V2-MEM-1`, `V2-COUP-1`, `V2-STACK-1` (both discounts, applied one after the other), `V2-STACK-2` (the 30% cap) and `V2-ROUND-1` (the full price formula). Each states the rounding to the nearest cent as an exact range on `10000*price`.
- Shipping: `V2-SHIP-1` and `V2-SHIP-2`, decided by the returned price.
- Monotonicity: `V2-MONO-1` compares two calls using `prev`.
- Example: `V2-EX-1` (a property, because the example gives a definite answer) and `V2-EX-2` (a scenario).
- Decisions: reading 2 for all three flagged phrases, as you instructed. Every affected item says so in its note.

**Unformalized: 5 requirements**
- **R-SIG-1:** the function's name and arguments are part of the adapter. The result type is covered by `V2-RET-1`.
- **R-IN-1, R-IN-2, R-IN-3:** these are definitions. They are realized by the `in_range` definition and the price items, recorded with `covered_by`.
- **R-FR-1:** this is frame rule F-ZERO, which holds by construction.

**Problems in the specification**
1. **Rules 6 and 7 contradict each other** under either reading of "Orders under $50". When the price steps from 4999 to 5000 cents, the amount charged drops from 5498 to 5000, which breaks the monotonicity rule. I wrote both down as stated, so this set has no consistent implementation.
2. **The 30% cap clashes with rounding to the nearest cent** if the cap applies to the final price. For a 19-cent cart with the cap applied, the exact price is 13.3 cents; rounded, that's 13, a 31.6% discount. I applied the cap before rounding and explained why in the note.
3. **Coupons from 31 to 50 are valid but can never take their full percentage off**, because of the cap. Rule 3 alone would give the full discount; I limited `V2-COUP-1` to coupons up to 30 and said so in its note.
4. **Shipping depends on which price you mean**, unrounded or rounded. A member with a 5555-cent cart has a price of 4999.5 cents before rounding and 5000 after. I used the returned (rounded) price, so that order ships free.
5. **Monotonicity has to be limited to valid calls.** Otherwise a subtotal above 1,000,000 raises ValueError and charges 0, which would break rule 7.
6. **Minor:** under the literal text, an empty cart (subtotal 0) pays $4.99 shipping.