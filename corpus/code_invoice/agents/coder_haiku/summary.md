Implemented `invoice(items, member)` in `invoice.py` and wrote 19 pytest tests. All 19 pass under `/repo/.venv/bin/python -m pytest -q`.

- `/work/ws_invoice_impl_haiku/invoice.py`
- `/work/ws_invoice_impl_haiku/test_invoice.py`

All amounts are integer cents. The member discount is `gross // 10`, which rounds down, and each line is its gross minus that discount. The tests cover the request's example, non-members, sale lines, line order, rounding, the error cases, and 500 seeded random orders checked against a reference calculation.

Decisions where the request was unclear:

1. **Rules 3 and 4 round differently.** Rule 3 rounds each line's discount down. Rule 4 sums the 10% amounts and rounds once. Rules 5 and 6 both define `total`, and they only agree when the invoice discount equals the sum of the line discounts. I used the per-line sum. For example, two member lines of 15 cents each, neither on sale, give lines `[14, 14]`, discount `2`, total `28`. The aggregate reading gives discount `3`, and then rule 5 (total 28) and rule 6 (total 27) disagree. The team should confirm this. If they want the aggregate, rules 5 and 6 need to change.
2. **Quantities below 1 raise ValueError.** The request only names 0. I also reject negatives, because floor division would turn a negative quantity into a negative discount, which is a surcharge.
3. **Negative prices raise ValueError.** The request is silent.
4. **Non-integer prices or quantities raise TypeError.** This covers floats, strings and bools, so money stays in whole cents. The request is silent.
5. **Zero-price items are allowed** and produce zero amounts. The request is silent.
