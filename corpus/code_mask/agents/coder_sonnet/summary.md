`mask_card` and its tests are written, and all 146 tests pass with the exact pytest command you gave. I also broke the implementation 19 different ways in throwaway copies, and the tests failed every time.

## Implementation

`mask_card(number)` works in four steps:
1. It rejects any character other than ASCII `0-9`, space and hyphen.
2. It checks that there are 12 to 19 digits, then runs a standard Luhn check on the digits with separators removed.
3. It replaces every digit except the trailing ones with `*`.
4. It leaves every space and hyphen where it was, so the output has the same length as the input.

`mask_card("4111 1111 1111 1111")` returns `"**** **** **** 1111"`.

## Decisions where the request was unclear

1. **Rules 2 and 4 conflict for 12 to 15 digit cards.** Showing the last four digits exposes 27% to 33% of a 12 to 15 digit number, which breaks "never show more than a quarter". The 16-digit example hides this, because there four digits is exactly a quarter.
   - **Choice:** I let rule 4 win, since it says "never" and "for security". The visible count is `min(4, digits // 4)`: the last 3 digits for 12 to 15 digit cards, the last 4 for 16 to 19.
   - **If you disagree:** always showing four would take a one-line change in `_shown_digit_count`, plus the tests listed in the test file's header comment. That would break the quarter rule for shorter cards, so it's your call.
2. **Which characters are allowed.** Only ASCII `0-9`, U+0020 space and U+002D hyphen. Tabs, newlines, no-break spaces, Unicode dashes and non-ASCII digits (Arabic-Indic, full-width) raise `ValueError`.
3. **Separators.** Nothing is stripped or normalized. Leading, trailing and repeated spaces and hyphens are accepted and kept, and their placement is not checked. "Last digits" means the last digit characters, so `"4111 1111 1111 1111 "` still shows `1111` and keeps the trailing space.
4. **Non-`str` input raises `TypeError`.** The request only defines `ValueError` for bad string contents, so I treated `None`, `int` or `bytes` as a caller bug. If your calling code catches only `ValueError`, change this.
5. **Error messages never contain the card number**, so they are safe to log. There is no check beyond the stated ones, so a number like twelve zeros, which passes Luhn, is accepted.

Files are in the working directory:
- `mask_card.py`
- `test_mask_card.py`
