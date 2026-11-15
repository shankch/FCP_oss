I wrote `requirements_draft.yaml` with 22 requirements. `fcp anchor` matched every quote on the first run, with no rejections, and produced `requirements.yaml` with line numbers for each one.

**Breakdown**
- **Interface (2):** R-IF-1 is the `valid_date(date)` signature (non_functional). R-ARG-1 says the argument is a string (assumption).
- **Result (2):** R-RET-1 says a valid date returns True. R-RET-2 says an invalid date returns False, which rules out raising an exception or returning anything else.
- **Validity (1):** R-VAL-1 defines "valid" as all four rules being satisfied (definition).
- **Rules (11, all guarantees):** an empty string is rejected (R-EMP-1). Each of the three month groups has its own day-range rule (R-DAY-1 to R-DAY-3), and the month must be in 1..12 (R-MON-1). Field order is a definition (R-FMT-0). The format rule is split into separate checks: the separators are `-` (R-FMT-1), mm, dd and yyyy each have the right number of digits (R-FMT-2 to R-FMT-4), and there is nothing before or after the date (R-FMT-5).
- **Scenarios (5):** R-EX-1 to R-EX-5, one per example.
- **Frame (1):** R-FR-1 is F-ZERO, using the id that `design.yaml` already refers to.

**Ambiguities flagged (7, across 6 requirements)**
1. **"valid if all … rules are satisfied" (R-VAL-1):** either the rules are the whole test, or the date must also be a real calendar date.
2. **February 29 (R-DAY-3):** either valid in every year, or only in leap years.
3. **Field widths (R-FMT-2, R-FMT-3, R-FMT-4):** mm, dd and yyyy must be exactly 2, 2 and 4 digits, or any text that reads as a whole number (so `'3-11-2000'` would be valid). The example `'04-0-2040'` doesn't settle this, because day 0 is out of range either way.
4. **Year 0000 (R-FMT-4):** either accepted, or the year must be at least 1.
5. **Spaces around the date (R-FMT-5):** `' 03-11-2000 '` is either rejected or trimmed and accepted.

I didn't flag the "not less than 1 or higher than 31" wording. It could literally be read as setting only a lower limit, but the separate limits for each month make the intended meaning clear.

**Contradictions:** I found none. All five examples agree with the rules. Rule 1 (not empty) is already covered by rule 4 (the format), but the two don't conflict.