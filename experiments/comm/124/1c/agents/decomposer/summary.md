I've written `requirements_draft.yaml` with 20 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**What's in it**
- **Interface (2):** R-IF-1 is the function signature (non_functional). R-IN-1 says the argument is a string (assumption).
- **Return value (3):** R-RET-1: a valid date returns True. R-RET-2: an invalid date returns False. R-RET-3: the function always returns a bool and never raises.
- **Validity (1):** R-VAL-1 defines a valid date as one that meets all four rules.
- **Rules (8):**
  - R-EMP-1: the string is not empty.
  - R-DAY-1/2/3: the day is in range for each month group (31, 30 and 29 days).
  - R-MON-1: the month is 1 to 12.
  - The format rule is split three ways: R-FMT-1 is the `-` separator, R-FMT-2 is the field widths (2-2-4 digits, length 10), R-FMT-3 says which field is month, day and year.
- **Examples (5):** R-EX-1 to R-EX-5 are scenarios, one per example.
- **Frame (1):** R-FR-1 is the frame rule F-ZERO.

**Contradictions: all five examples conflict with the rules.** Each one is recorded as an ambiguity on both the example and the requirement it conflicts with.
- `'03-11-2000' => False` and `'06-04-2020' => False` meet every rule, so they conflict with R-VAL-1 and R-RET-1.
- `'15-01-2012' => True` has month 15, so it conflicts with R-MON-1 and R-RET-2. It would also fit if the format were day first, which conflicts with R-FMT-3.
- `'04-0-2040' => True` has day 0 and a one-digit day, so it conflicts with R-DAY-2, R-FMT-2 and R-RET-2.
- `'06/04/2020' => True` uses `/` as separator, so it conflicts with R-FMT-1 and R-RET-2.

Every example is the opposite of what the rules give. Most likely the expected outputs in the examples are wrong.

**Other ambiguities flagged**
- **"if" in the validity definition:** it could mean "if and only if", or only that meeting the rules is enough.
- **"not less than 1 or higher than N":** this is usually read as 1 ≤ x ≤ N. Read literally, it could mean only x ≥ 1. Flagged on each day rule and the month rule.
- **February 29:** allowed in every year, or only in leap years.
- **Malformed strings:** they must return False, or they may raise an exception.
- **Surrounding whitespace:** rejected, or stripped before the format check.
- **Year:** any four digits (including `0000`), or only a real year.