Implemented `mask_card` and its tests. All 38 tests pass with your pytest command, so no fixes were needed.

Files:
- mask_card.py
- test_mask_card.py

What it does: it checks the characters, then the digit count (12 to 19 digits, separators not counted), then the Luhn check on the digits. Each failure raises ValueError with a message that does not include the card number. It replaces each digit with `*` except the last `min(4, digits // 4)`, and keeps spaces and hyphens in place. The output contains only digits, spaces, hyphens and `*`, so it needs no escaping in HTML or email.

Decisions where the request was unclear:
1. **Rules 2 and 4 conflict for 12 to 15 digits.** A quarter of those lengths is at most 3 digits, so those cards show only their last three digits. 16 to 19 digits show the last four (for 16, four digits is exactly a quarter, which is allowed). I treated "never" in rule 4 as binding. The alternatives were showing four digits (breaks rule 4) or rejecting 12 to 15 digits (contradicts rule 1, which accepts 12 to 19). Please confirm this, since customers with 12 to 15 digit cards will see three digits.
2. **Accepted characters:** only ASCII space and ASCII hyphen-minus. Tabs, newlines, non-breaking spaces, en dashes and non-ASCII digits such as fullwidth digits raise ValueError. Non-breaking spaces pasted from web pages will be rejected, so the caller may want to normalize them.
3. **Layout:** the request restricts characters but not placement, so any mix or repetition of separators is accepted, including leading and trailing ones. They are kept as typed and nothing is trimmed, since rule 3 requires the same length.
4. **Check order:** characters, then digit count, then Luhn. Empty or separator-only input has zero digits and raises the digit-count error.
5. **Non-string input** was not specified. It is not checked explicitly, so an int raises TypeError when the function iterates over it.
