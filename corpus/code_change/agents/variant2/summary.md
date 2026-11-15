I wrote `formal/variant2.yaml`. It has 7 items: 6 properties and 1 scenario. `fcp lint` reports no errors, and the `fcp explain` read-back says what I intended for every item.

**Items**
- **V2-STU-1 (R-STU-1):** a student with no coupon and no membership pays 85% of the subtotal, rounded to the nearest cent with half a cent rounded up.
- **V2-CAP-1 (R-CAP-1):** for a student, the price uses a discount of `min(coupon + 10*member + 15, 30)`, rounded the same way. I read "adds to" literally: the percentages are added together, not applied one after another.
- **V2-SHIP-1 / V2-SHIP-2 (R-SHIP-1):** a student with a subtotal of 7500 cents or more ships free; below that, a student pays 499.
- **V2-SAME-1 (R-SAME-1):** when `student` is false, the outcome, price and shipping fee all equal the old code's answer.
- **V2-KEEP-1 (R-KEEP-1):** for a student, the outcome equals the old code's outcome. That keeps the old ranges and errors. The rest of R-KEEP-1 (rounding and the shipping fee) is built into the items above.
- **V2-EX-1 (R-EX-1):** a scenario that can be reached in which a student with a 10000-cent cart, no coupon and no membership gets `(8500, 0)`.

There are no ghosts, only two macros (`disc`, `due`). The rounding is written as `100*price - 50 <= due < 100*price + 50`, because FCP-PL has no division. That is exactly `(due + 50) // 100`.

**Decision:** for R-SHIP-1, "Free shipping now starts at $75" uses reading 2 ("for students only"), as you instructed. The notes of V2-SHIP-1, V2-SHIP-2 and V2-SAME-1 say so.

**Left unformalized**
- **R-SIG-1:** the signature is already the interface. The default `student=False` can't be seen in the trace, because the adapter passes `student` on every call.
- **R-TEST-1:** updating the tests concerns the repository, and no call of the function can show it.
- R-FR-1 and R-FR-2 are covered by the frame items F-ZERO and F-OLD, which are added to every set automatically.

**Problems in the specification**
1. **Rules 2 and 3 contradict each other.** If $75 free shipping applied to every customer (reading 1), non-students with a subtotal from $50 to $74.99 would start paying shipping, which rule 3 forbids. Reading 2 removes the conflict.
2. **The $75 threshold doesn't say which amount it applies to:** the subtotal before discounts or the discounted price. I compared it with the subtotal, as the old code does for $50, and the item notes record this. The example doesn't settle it, since $100 and $85 are both above $75.
3. **"Students get 15% off" isn't always true.** With a coupon of 15% or more, or a member with a coupon above 5%, the 30% cap gives the student less than 15%. That's why V2-STU-1 only covers students with no other discount.
4. **The spec never states the rounding rule or the $4.99 fee.** Both come only from the old code, through rule 4 ("Keep everything else as it is").