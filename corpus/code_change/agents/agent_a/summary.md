I wrote `formal/agent_a.yaml`. `fcp lint` reports no errors, and the `fcp explain` read-back matches what I meant for every item. Its one warning is about the adapter's frame item F-OLD, which only mentions inputs; it is not one of my items.

**Items: 11** (10 properties and 1 scenario, all `CA-`). There are no ghosts and no assumptions; two `defs` hold the student's discount and price formula.
- **R-STU-1:** a student with no coupon and no membership pays 85% of the subtotal.
- **R-CAP-1:** a student's discount is min(coupon + 10 if member + 15, 30) percent, rounded as the old code does (nearest cent, half a cent up).
- **R-SHIP-1:** shipping is free from 7500 cents, and not free below that, for every customer.
- **R-SAME-1:** for non-students, outcome, price and ship each equal the old code's answer.
- **R-KEEP-1:** a student's call ends the same way as the old call (this keeps the ranges and the ValueError cases), and any shipping fee a student pays is 499.
- **R-EX-1:** the example is both a property and a cover: student, 10000, no coupon, no membership gives (8500, 0).

I checked the predicates in Python over about 3 million calls. A correct version of the change under either reading of rule 2 fails exactly one item. I also tried seven common wrong implementations, and each was caught by the item meant for it.

**Not formalized (4):**
- **R-SIG-1:** the default `student=False` cannot be seen in the trace, because every call passes `student`. The part that can be seen (every call is accepted and ends like the old call) is `covered_by` CA-SAME-1 and CA-KEEP-1.
- **R-TEST-1:** it is about the test file, which is not part of the call trace.
- **R-FR-1 and R-FR-2:** these are frame rules, `covered_by` the frame items F-ZERO and F-OLD that are added to every set.

**Problems in the specification:**
1. **Rules 2 and 3 contradict each other.** Rule 2 names no customer group, so its literal reading covers every customer. For a non-student with a subtotal of 5000–7499 cents and a coupon of 0–50, the old code ships free. Rule 3 then requires ship 0, while rule 2 requires a fee. That is 255,000 calls in my sweep, and no implementation can meet both CA-SHIP-2 and CA-SAME-3 on them. I left it unrepaired and noted it on CA-SHIP-1, CA-SHIP-2 and CA-SAME-3; only the students-only reading removes it, and the text doesn't say that.
2. **Rule 2 doesn't say what $75 is compared with.** It could be the subtotal or the discounted price. I used the subtotal, as the old code does (rule 4). The choice matters for students: an $80 cart is $68 after the discount.
3. **Rule 1 gives no rounding.** I took the old code's rounding through rule 4.
4. **Rule 1's combination wording needed a reading.** I read "adds to the other discounts" as adding percentage points with the old cap at 30. I read "the total discount" as the student's total, since the old code already caps non-students.

**Tooling:** `fcp lint` does not check that every requirement is covered: it stayed clean with R-TEST-1 deleted, so I checked coverage myself. Also, `fcp explain` prints defs by name only, so the price formula cannot be read from its output alone.
