I wrote `formal/agent_b.yaml`. `fcp lint` reports `lint: clean`, and I read back the `fcp explain` output: every item says what I intended. I didn't run `fcp check`. I checked by hand that the items don't contradict each other: any string the model calls valid fails every "returns False" condition, and the five examples come out as the docstring says.

**Items: 23** (18 properties and 5 scenarios). There are no assumptions or dont_cares: under the readings I took, the spec decides the output for every input.

- **Model:** `valid_date` keeps nothing between calls, so ghost state would add nothing. The model is a set of defs that parse `date`:
  - `mm_ok`, `dd_ok`, `yyyy_ok` check the shape of each field.
  - `fmt` checks that the whole string is mm-dd-yyyy.
  - `mon` and `day` are the decimal values of the month and day fields.
  - `rule1`, `rule2` and `rule3` are rules 1–3; `ok` is the four rules together.
- **Main check:** RB-RET-1 and RB-RET-2 together say `outcome == 0 && valid == ok`.
- **Per-rule items:** each rule-level requirement (EMP-1, DAY-1/2/3, MON-1, FMT-1 to FMT-5) gets its own "if this, return False" property, worded as closely to its text as I could.
- **Examples:** each of R-EX-1 to R-EX-5 gets a scenario (the call can happen) and a property (it returns that result). The function always gives the same answer for the same input, so "`=> True`" states a fixed result, not just a possible one.

**Unformalized (5):**
- **R-IF-1:** the function's name and signature can't be observed in a call trace.
- **R-ARG-1:** the interface already makes `date` a string of at most 16 characters, so there is nothing left to assume.
- **R-VAL-1:** a definition; it is `ok`, covered by RB-RET-1 and RB-RET-2.
- **R-FMT-0:** a definition; it is `mon` and `day`, covered by RB-DAY-1/2/3 and RB-MON-1.
- **R-FR-1:** this is frame rule F-ZERO, which is already part of every set.

**Decisions:** I took reading 1, the most literal one, for all 7 flagged phrases:
- The four rules are both necessary and sufficient, so `'02-29-2001'` and `'01-01-0000'` are valid.
- February allows day 29 in every year.
- The fields must be exactly two, two and four digits.
- The whole string must match, with no whitespace stripping.

R-FMT-4 flags the phrase "yyyy" twice with the same text, so I recorded two separate decisions for it. Lint accepted that.

**Problems in the specification:**
1. **Leap years:** rule 2 allows February 29 in every year, with no leap-year check, and no year range is given, so `0000` is accepted. A reader who expects real calendar dates would read it differently.
2. **"not less than 1 or higher than 31":** grammatically this could mean "(not < 1) or (> 31)". I read it as "neither below 1 nor above 31" and said so in the notes.
3. **Rule 1 is redundant:** rule 4 already rules out the empty string.
4. **The examples don't settle the format readings:** `'04-0-2040'` is invalid both because its day field is one digit and because day 0 is out of range. Nothing in the examples tells strict "mm/dd/yyyy" apart from "any integer".
5. **Rule 4's wording:** it doesn't say whether extra characters, or fields that are empty or one digit long, are allowed. The range rules only make sense once the fields are decimal numbers. I stated DAY/MON for two-digit month and day fields (any year), and left other field shapes to RB-FMT-2 and RB-FMT-3. That narrows each of those items on its own, but not the set as a whole.
6. **Rule 2 is silent on months outside 1–12:** it only constrains the months it names, so a month like 13 fails through rule 3 alone.