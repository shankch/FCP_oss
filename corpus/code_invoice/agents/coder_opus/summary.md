I wrote `invoice()` and its tests. All 23 tests pass on the first run, with nothing to fix.

**Implementation** (`invoice.py`): it uses only whole-number arithmetic, so there is no float rounding. Each line's amount is price × quantity. A member's line that is not on sale loses `amount // 10`, which is 10% rounded down to the cent. `discount` is the sum of those line discounts, and `total` is the sum of the lines. The request's example gives `{"lines": [3599], "discount": 399, "total": 3599}` as expected.

**Tests** (`test_invoice.py`) cover:
- the request's example;
- each error case;
- line order;
- non-members, sale items, rounding down and mixed orders;
- the one case where the rules disagree;
- a check over 2,000 random orders that `total == sum(lines) == gross - discount` always holds.

**Decisions where the request was unclear:**

1. **The rules contradict each other, and the team should confirm my choice.**
   - **The conflict:** rule 3 rounds the discount down on each line. Rule 4 adds up the full-price amounts and rounds down once. With more than one discounted line these give different numbers. For two non-sale items at 15 cents each, the line discounts are 1 + 1 = 2 cents, but rule 4 gives 3 cents. Then rules 5 and 6 can't both be true: the sum of the lines is 28, while gross minus the rule 4 discount is 27.
   - **What I did:** I round each line, as rule 3 says, and report `discount` as the sum of the line discounts. That keeps rules 2, 3, 5 and 6 exact and departs from rule 4 only in where the rounding happens.
   - **What it costs:** compared with the literal rule 4, a member can get up to one cent less discount for each discounted line beyond the first. The two methods agree whenever at most one line is discounted, as in the example.
   - **The alternative:** compute the discount the rule 4 way and spread the leftover cents across lines. That would round some lines up instead of down, against rule 3.
2. **Extra input checks:** the request only says to reject an empty list and a quantity of 0. I also raise `ValueError` for:
   - a negative quantity or a negative price;
   - a missing key or an item that isn't a dict;
   - a price or quantity that isn't a whole number (a float or a `True`/`False` value);
   - a `sale` or `member` value that isn't a real `True`/`False`.
3. **A price of 0 is allowed**, since a free item is a plausible order line.
4. **The input list is never changed**, and the tests check this.

Files are in /work/ws_invoice_impl_opus:
- invoice.py
- test_invoice.py
