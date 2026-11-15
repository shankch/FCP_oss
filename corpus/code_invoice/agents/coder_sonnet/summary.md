I wrote `invoice.py` and `test_invoice.py` in the directory, and all 35 tests pass.

`invoice(items, member)` works in integer cents with no floats. For each item it takes the gross amount, `price * qty`. A member gets `gross // 10` off that line unless the item is on sale. Each line is gross minus its discount, `discount` is the sum of the line discounts, and `total` is the sum of the lines. The example from the request returns `{"lines": [3599], "discount": 399, "total": 3599}`.

The tests cover the example, member vs non-member, sale items, line order and rounding. They also check the request's rules 2–6 on 2000 random orders, plus the error cases and edge cases (free items, very large amounts, input not mutated).

Decisions where the request was unclear:

1. **Rules 3–6 contradict each other on rounding.** Rule 3 rounds each line's discount down. Rule 4 can be read as rounding the combined discount once. These give different answers with two or more non-sale lines. For example, two lines of 1999 give 199 + 199 = 398 per line, but floor(399.8) = 399 combined. With the combined reading, rules 5 and 6 (`total` equals the sum of the lines and also gross minus `discount`) could not both hold.
   - **What I did:** I rounded per line and summed the rounded discounts. For that example the output is `lines [1800, 1800], discount 398, total 3600`. Rules 2, 3, 5 and 6 and the example all hold, and the invoice adds up exactly.
   - **Where it differs:** A reading of rule 4 as "sum first, then round" would give 399 in cases like that. It's worth confirming with the store team that per-line rounding is what they want. If not, I'd need to know whether the lines or the total should be the one that doesn't add up.
2. **Extra rejections beyond rule 1.** The request only names empty `items` and `qty == 0`. I also raise `ValueError` for negative `qty` or `price`, non-integer `price` or `qty` (floats, strings, `None`, `True`/`False`), a missing `price`, `qty` or `sale` key, and an item that isn't a dict. Floats are likely dollars passed by mistake. A missing `sale` could silently give members a discount on a sale item. Negative values would make "rounded down" ambiguous. A price of 0 is allowed.
3. **Rounding applies to the whole line, not the unit price.** The discount is 10% of `price * qty`, rounded once. Price 5 with qty 2 gives 1 cent off, not 0.
4. **`sale` and `member` truthiness.** Both are treated as plain truthy/falsy values.
5. **Input type.** `items` can be any iterable of dicts, not just a list. It is copied first, so the caller's input is never changed.

Files are in `/work/ws_invoice_impl_sonnet/`:
- `invoice.py`
- `test_invoice.py`
