I've written `formal/variant1.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what each item is meant to say.

**Items: 12 properties and 1 scenario (13 in total).**
- **R-STU-1 (V1-STU-1):** a student with no coupon and no membership pays 85% of the subtotal, to the nearest cent.
- **R-CAP-1 (V1-CAP-1):** for students, the coupon %, the 10% member discount and the 15% student discount add up as percentage points, capped at 30%. "Still never more than 30%" is read as the old code's cap: a sum above 30% gives exactly 30%.
- **R-SHIP-1 (V1-SHIP-1/2):** read as "for every customer", as you instructed, and noted in both items. A subtotal of 7,500 cents or more ships free; below that the fee is 499 cents, the old code's fee.
- **R-SAME-1 (V1-SAME-1/2/3):** for non-students, outcome, price and shipping equal the old code's answer.
- **R-KEEP-1 (V1-KEEP-1/2):** a student's call ends the same way as the old call (same ranges and `ValueError` cases), and the price rounds half a cent up, as before. The shipping-fee part of this requirement is stated in V1-SHIP-2.
- **R-EX-1:** the scenario V1-EX-1 says the example answer must be possible. I also added a property, V1-EX-2, requiring that exact answer for those inputs, because the example says what the student "gets".
- **Decision:** R-SHIP-1, "Free shipping now starts at $75", reading 1.

**Left unformalized:**
- **R-SIG-1:** the `student` argument is just the input signal. Its default of False can't be observed, because every call in the trace passes it explicitly.
- **R-TEST-1:** it is about the test file, not the function's behaviour.
- **R-FR-1 / R-FR-2:** marked as covered by the frame rules F-ZERO and F-OLD.

**Problems in the specification:**
1. **The spec contradicts itself under the required reading.** If free shipping starts at $75 for every customer, a non-student with a subtotal from 5,000 to 7,499 cents must pay 499 cents. Rule 3 says nothing may change for non-students, and the old code charges 0 there. Both are written literally (V1-SHIP-2 against V1-SAME-1 and V1-SAME-3), and their notes flag the conflict. I didn't repair it.
2. **Facts that only the old code supplies.** The change request doesn't say:
   - whether the $75 is checked before or after discounts (I used the subtotal before discounts, as the old code does);
   - that "adds to" means adding percentage points rather than applying the discounts one after another;
   - how the price rounds;
   - how much "the shipping fee" is.

   I took all of these from `impl/old.py`, through "keep everything else as it is".
3. **"15% off" can't be exact in whole cents.** So V1-STU-1 and V1-CAP-1 allow either cent at a tie, and V1-KEEP-2 fixes the rounding as half a cent up.