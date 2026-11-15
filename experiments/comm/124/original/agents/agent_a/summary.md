I wrote `formal/agent_a.yaml`. `fcp lint` reports no errors, and I read back the `fcp explain` output for every item; each one means what I intended. I also wrote a Python script that copies the definitions, to check that no "returns False" rule can fire on a string the validity definition accepts. Running it needed approval and didn't happen, so that check rests on working through each rule by hand. It's in the scratchpad (`mirror.py`) if you want to run it.

**Items: 23.** That's 18 properties and 5 scenarios, plus 7 entries under `decisions`.
- **Valid / invalid:** `RA-RET-1` says a valid date returns True. `RA-RET-2` says anything else returns the bool False; it never raises an exception or returns another value.
- **Single rules:** one "returns False" property each for the empty string, the three day-range rules, the month range, and the format rules (exactly two `-`, a two-digit month, a two-digit day, a four-digit year, and no extra characters before or after the date).
- **Examples:** each of the five docstring examples is both a guarantee (that exact input gives that result) and a scenario (the call can happen).
- **Readings:** for every flagged ambiguity I took reading 1, the most literal one:
  - February allows day 29 in every year, so `02-29-2001` is valid.
  - Year `0000` is accepted.
  - The month and day must be exactly two digits and the year exactly four.
  - The whole string must match mm-dd-yyyy, so leading or trailing spaces make it invalid.
  - The four listed rules are enough on their own to make a date valid.
- **No extra state:** everything is written directly on the `date`, `outcome` and `valid` signals.

**Left unformalized (5 requirements):**
- **R-IF-1** (function name and signature): the adapter already fixes this, so there is nothing to check on the trace.
- **R-ARG-1** (the argument is a string): the interface guarantees it, so an assumption would always be true.
- **R-VAL-1 and R-FMT-0** are definitions. They are built into the shared definitions and marked as covered by the properties that use them.
- **R-FR-1** is marked as covered by the adapter rule F-ZERO ("valid is false unless outcome is 0"), which is added to every set automatically.

**Problems in the specification:**
1. **Calendar dates:** the prompt only gives day ranges per month. It never says whether `02-29-2001` or year `0000` are real dates, so code that checks the actual calendar will disagree with my reading.
2. **Field width:** "mm-dd-yyyy" doesn't say whether one-digit or padded fields are allowed. The `04-0-2040` example is invalid either way because the day is 0, so none of the examples settles this.
3. **Undefined numbers:** the range rules refer to the month and day numbers, which only exist once the format is right. I applied them only when the month and day fields are both two digits, and said so in the notes.
4. **Extra characters rule:** "characters before the month field or after the year field" only makes sense if a field can start somewhere other than the beginning of the string. I read it as a complete mm-dd-yyyy with something before or after it. Because I treat the year as everything after the second `-`, trailing characters also break the year rule, so the two rules overlap.
5. **Missing separators:** "before the first `-`" and "between the two `-`" assume the separators exist. With fewer of them I treat the field as malformed; the "exactly two `-`" rule rejects those strings anyway.
6. **Rule 1 is redundant:** "not empty" is already implied by the format rule.

R-FMT-4 has two flagged ambiguities with the same phrase "yyyy", so it has two `decisions` entries that look identical. Lint accepts this, but nothing in an entry says which of the two ambiguities it refers to.