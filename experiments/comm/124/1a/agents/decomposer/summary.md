I've written `requirements_draft.yaml` with 19 requirements. `fcp anchor` accepted every quote on the first run, and the anchored result is in `requirements.yaml`.

**What's in it**
- **Interface and input:** `R-API-1` covers the function signature (non_functional). `R-IN-1` records that the argument is always a string (assumption).
- **Return value:** `R-RET-1` says a valid date returns True and `R-RET-2` says an invalid one returns False. `R-VAL-1` defines "valid" as meeting all four rules.
- **Rules:** `R-EMP-1` (string not empty), `R-DAY-1/2/3` (day ranges for 31-day months, 30-day months and February), `R-MON-1` (month 1–12). The format rule is split three ways: `R-FMT-1` (three fields separated by `-`), `R-FMT-2` (2, 2 and 4 digits) and `R-FMT-3` (which order the fields are read in).
- **Examples:** the five examples are scenarios `R-EX-1` to `R-EX-5`.
- **Frame:** `R-FR-1` is the F-ZERO frame rule; `design.yaml` already points to it.

**Contradiction (recorded on both `R-FMT-3` and `R-EX-2`)**
Rule 4 accepts `dd-mm-yyyy`, which makes `'15-01-2012'` a valid date (15 January 2012). But the example says `valid_date('15-01-2012') => False`, which only works if the first field is the month. `R-FMT-3` lists four readings: either order accepted, `mm-dd-yyyy` only, the implementation picks one order, or the date must be valid under both orders. The last of these is the only one that fits every example. The other four examples don't separate the readings.

**Other ambiguities flagged**
- **Negation scope:** "not less than 1 or higher than N" in each day rule and in the month rule. Read strictly as logic, it sets no upper limit.
- **Leap years:** whether 29 February is accepted every year or only in leap years (`R-DAY-3`).
- **Whether the rules are complete** (`R-VAL-1`): whether any further calendar check applies.
- **Format details** (`R-FMT-2`): whether day and month need exactly two digits or one is enough, whether spaces before or after the date are ignored, and whether `0000` is a valid year.
- **Malformed input** (`R-RET-2`): whether a malformed string must return False or is allowed to raise an error.