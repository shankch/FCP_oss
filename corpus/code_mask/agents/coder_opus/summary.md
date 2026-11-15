I've written `mask_card` and its tests. All 119 tests pass under the pytest command you gave.

To check the tests can fail, I put 9 common mistakes into temporary copies of the module, then deleted the copies. Each one made at least one test fail. The mistakes were:
- ignoring the quarter rule
- doubling the wrong digits in the Luhn check
- accepting non-ASCII digits or other whitespace
- trimming the input
- moving either digit-count limit by one
- putting the number in an error message
- dropping the type check

**How it works:** the function first checks every character, then that there are 12 to 19 digits, then the Luhn check, and raises `ValueError` if any check fails. It then replaces each digit with `*` except the last few, and leaves every space and hyphen where it was, so the output is the same length as the input.

The tests cover:
- the example from the request
- hand-checked outputs for every card length from 12 to 19 digits
- unusual placements of spaces and hyphens
- published test card numbers
- random generated cards
- every rejection rule, plus 30 kinds of bad character
- a Luhn check written separately from the one in `mask_card.py`
- error messages never containing card digits
- the usage examples in the function's docstring

**Decisions where the request was unclear:**
1. **Rules 2 and 4 conflict for 12–15 digit cards.** Four digits would be more than a quarter of the number, so I let the security rule win: these cards show only their last 3 digits. For example, an Amex card `"3782 822463 10005"` becomes `"**** ****** **005"`. Cards with 16–19 digits show 4. The alternatives were rejecting these cards, which breaks rule 1, or showing 4 anyway, which breaks rule 4. **This is the one to confirm with the store team:** Amex and Diners customers will see 3 digits where they may expect 4.
2. **"Digits" means 0–9 only.** Non-ASCII digits such as fullwidth, Arabic-Indic or superscript digits are rejected, even though Python's `isdigit()` and `\d` would accept them.
3. **"Spaces" and "hyphens" mean only the plain space and the ordinary keyboard hyphen.** Tabs, newlines (including a trailing newline), non-breaking spaces, en and em dashes and other Unicode dashes are rejected.
4. **Input is never trimmed or normalised.** Spaces and hyphens may appear anywhere (at the start or end, doubled, or inside the last four digits) and are kept exactly. Group patterns are not checked.
5. **Non-string input raises `TypeError`, not `ValueError`.** Without this check, a list of digit strings would be masked as if it were valid. Callers that catch only `ValueError` will not catch `None`.
6. **Nothing is checked beyond rule 1.** There are no card-brand prefix or brand-length checks, so `"000000000000"` passes the Luhn check and is accepted.
7. **Error messages contain no card digits, since they end up in logs.** They name the rule broken, the digit count, or the position of a bad character. If several rules fail, the message names the first one in rule 1's order: characters, then digit count, then Luhn.

Files are in the working directory:
- `mask_card.py`
- `test_mask_card.py`
