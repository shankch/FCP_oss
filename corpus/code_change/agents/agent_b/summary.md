I wrote `formal/agent_b.yaml`. `fcp lint` reports no errors. It printed one warning on its first run, `no-observable` on F-OLD, which is a frame rule from design.yaml, not one of my items. I read the `fcp explain` output against every item. I also evaluated each item in an inline Python check over a dense grid of calls, using the real old code and a few likely bugs.

**Items: 14** (13 properties and 1 scenario, no assumptions or don't-cares)
- **Model:** calls are independent, so instead of ghost state the model is a set of definitions computed from each call. A student's discount is min(coupon + 10 for members + 15, 30), and the exact price is computed from it. Non-students are checked against the old code's answer; students are checked against the model.
- **R-STU-1** (2 items): a student with no other discount pays 85% of the subtotal, and every student pays at most 85%.
- **R-CAP-1** (2 items): below the cap the discounts add; above it the discount is exactly 30%.
- **R-SHIP-1** (2 items): free from 7500 cents, not free below, for every customer.
- **R-SAME-1** (3 items): a non-student's outcome, price and ship equal the old code's.
- **R-KEEP-1** (3 items): a student's outcome equals the old code's (same ranges and errors); the exact half-cent-up price; shipping is 0 or 499.
- **R-EX-1** (2 items): one property that the example call gets (8500, 0), and one scenario that it can happen.

The R-STU-1 and R-CAP-1 items only require the price to be within one cent; the exact rounding sits in R-KEEP-1. Banker's rounding or truncation therefore fails only R-KEEP-1, while a missing cap or multiplied discounts also fail R-CAP-1. The grid check confirmed this split.

**Left unformalized**
- **R-SIG-1:** the signature is a definition. Every call in the trace passes `student`, so the default False can't be observed. The return type is already enforced because every call's outcome must equal the old code's.
- **R-TEST-1:** updating the tests is non-functional; the tests aren't part of the trace.
- **R-FR-1, R-FR-2:** frame rules, covered by F-ZERO and F-OLD.

**Problems in the specification**
1. **Rules 2 and 3 contradict each other.** Read literally, $75 free shipping applies to everyone. For a non-student with a subtotal of 5000–7499 cents and valid arguments, the old code ships free. Rule 3 then keeps shipping at 0 while rule 2 requires a fee. I formalized both as written, so the set is unsatisfiable on those calls. The grid check confirms it: "$75 for everyone" breaks R-SAME-1 and "$75 for students only" breaks R-SHIP-1, both on the same calls. Reading rule 2 as students-only would resolve it, but that would be repairing the spec, so it's for a human to decide.
2. **"Students get 15% off" is absorbed by the cap.** If a student's other discounts are 16% or more, the 15% only partly adds. At 30% or more (for example a 20% coupon plus membership) it adds nothing. I state "at least 15% in total" for every student.
3. **"Never more than 30%" on its own is only an upper bound.** I read it as min(sum, 30), based on "adds to the other discounts" and "still".
4. **Three details aren't stated, so I took them from the old code:**
   - the threshold applies to the subtotal before discounts;
   - $75 itself ships free;
   - rounding and the $4.99 fee are unchanged.
