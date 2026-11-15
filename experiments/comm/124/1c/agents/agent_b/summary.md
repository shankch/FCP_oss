Lint is clean and the English rendering matches what I meant for every item, so I'm writing up the summary.

I wrote `formal/agent_b.yaml`. `fcp lint` reports clean, and the `fcp explain` output reads as intended for every item. I didn't run `fcp check`, so I haven't machine-confirmed that the example scenarios are unreachable. I worked that out by hand.

**Items: 15**, plus the adapter's own frame rule F-ZERO.
- **The model:** the function keeps no state between calls, so instead of ghost state I used named expressions that compute each rule and an overall `is_valid` from the `date` string. Both outputs are checked against it:
  - `outcome` must always be 0, meaning every call returns a bool (RB-RET-3).
  - `valid` must equal `is_valid` (RB-RET-1 and RB-RET-2).
- **10 properties:** RB-RET-1/2/3, RB-EMP-1, RB-DAY-1/2/3, RB-MON-1 and RB-FMT-1/2.
- **5 scenarios:** RB-EX-1 to RB-EX-5, one per example, each stating the expected result exactly as the prompt gives it.
- **22 decisions**, one for every flagged phrase, all reading 1. That means the rules are taken at their word, and each example is also taken at its word in its own scenario. The two sets of readings contradict each other, and I left it that way on purpose. Each note says so.

**Left unformalized: 5**
- **R-IF-1** (function name and arity): this is fixed by the adapter, and a trace of calls has no signal for it.
- **R-IN-1** ("date is a string"): this is true by construction, since non-string calls are not part of the trace. There is nothing left to assume.
- **R-VAL-1** and **R-FMT-3**: these are definitions. They are built into `is_valid` and the month/day expressions, and covered by the RET, DAY and MON items.
- **R-FR-1**: covered by the frame rule F-ZERO, which `frame.md` says need not be restated.

**Problems in the specification**
1. **The examples contradict the rules, all five of them.** Each expected result is the opposite of what the rules give:
   - `03-11-2000` and `06-04-2020` meet every rule but are listed as False.
   - `15-01-2012` (month 15), `04-0-2040` (day 0, one-digit day) and `06/04/2020` (`/` separators) each break a rule but are listed as True.

   It looks as if the True/False values were flipped. Under the rule properties, all five scenarios are unreachable, so FCP should report the conflict rather than have it hidden.
2. **"not less than 1 or higher than N" can be parsed two ways.** I read it as "1 ≤ value ≤ N". The other parse, "(not less than 1) or (higher than N)", would make "higher than N" mean nothing.
3. **February 29 is allowed in every year.** The rule never mentions leap years.
4. **The format leaves things open.** It doesn't say whether fields must be exactly two digits (one example uses a one-digit day), whether surrounding whitespace is allowed, or whether year `0000` counts. I read it strictly: exactly 10 characters, no trimming, any four digits as the year.
5. **Rule 1 (not empty) adds nothing**, because the format rule already rules out an empty string.
6. **The prompt doesn't say whether malformed input may raise an exception.** I read "otherwise False" as covering every string.
7. **Month and day only exist for a correctly formatted string.** So the day and month rules only apply when the format holds; anything else is rejected by the format rule.