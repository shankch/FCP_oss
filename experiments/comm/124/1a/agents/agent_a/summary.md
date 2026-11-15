I've written `formal/agent_a.yaml`. `fcp lint` reports `lint: clean`, and I read back the `fcp explain` output: every item says what I intended.

**Items: 16 formal items, plus 4 requirements listed as unformalized**
- **11 properties.** Most are rules of the form "whenever the input does X, the call does Y".
  - `RA-RET-1` and `RA-RET-2` say a valid date returns True and an invalid one returns False, with no exception (`outcome == 0`). "Valid" is a definition I wrote once and reused: exactly `dd-dd-dddd` with ASCII digits, and the day and month rules hold in at least one field order.
  - `RA-EMP-1`, `RA-DAY-1`, `RA-DAY-2`, `RA-DAY-3`, `RA-MON-1`, `RA-FMT-1`, `RA-FMT-2` each say what one rule rejects.
  - `RA-FMT-3-DM` and `RA-FMT-3-MD` say each field order is accepted.
- **5 scenarios.** `RA-EX-1` to `RA-EX-5` are the docstring examples, each stated as "the call with this input returns this value".
- **Ambiguities:** I took reading 1 for all 12 flagged phrases and recorded each under `decisions`.

**Requirements left unformalized**
- **R-API-1:** the function name and its parameter are fixed by the adapter, and a trace of calls can't observe them.
- **R-IN-1:** the interface already makes `date` a string, and calls with anything else aren't in the trace, so there's nothing left to assume.
- **R-VAL-1:** it's a definition, not a requirement on its own. It is the definition behind `RA-RET-1` and `RA-RET-2`.
- **R-FR-1:** frame rule F-ZERO already covers it and is part of every set. Lint accepted listing F-ZERO as the covering item.

**Problems in the specification**
1. **The prompt contradicts itself.** Rule 4 accepts "dd-mm-yyyy or mm-dd-yyyy", so `'15-01-2012'` is 15 January 2012 and valid. The example says it returns False. I formalized both literally, so the `RA-EX-2` scenario can't be reached under `RA-FMT-3-DM`. I made the examples scenarios rather than properties so this shows up as one unreachable scenario instead of making the whole property set impossible to satisfy.
2. **The rules only work together.** With either field order allowed, a bad month in one order doesn't invalidate the string (`'13-01-2000'` is valid read day-first), so `RA-MON-1` only rejects when neither field is a month from 1 to 12. A day-rule violation in either order does make the string invalid, because the other order then has a month outside 1 to 12. The notes on each item explain this.
3. **"Is not less than 1 or higher than 31"** can be parsed as having no upper bound at all. I read the "not" as covering both parts (day from 1 to 31), because otherwise the numbers 31, 30 and 29 would mean nothing.
4. **Literal results that may surprise:**
   - There's no leap-year check, so `'29-02-2001'` is valid.
   - Year `0000` is accepted.
   - One-digit fields (`'4-1-2040'`) are rejected.
   - Surrounding whitespace is rejected.
   - Latin-1 superscript digits count as non-digits, so those strings must return False. Code using Python's `str.isdigit` treats them as digits and will likely raise on them instead.

I also wrote a small Python script in the scratchpad to check points 1 and 2 by brute force over every possible pair of first and second fields. Running it needed approval and it didn't run, so those two claims rest on my own working, not a machine check.