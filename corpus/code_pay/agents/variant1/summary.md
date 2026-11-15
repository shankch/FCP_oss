I wrote `formal/variant1.yaml`. `fcp lint` reports no errors (one info message: the answer assumption depends on the output `op`, so its receptiveness has to be checked). I read the `fcp explain` output and every item says what I intended. I couldn't run `fcp check`, because it isn't available to agents, so nothing beyond lint and explain has been checked.

**Items: 14 formal items, plus 3 entries covered by frame rules**
- **2 assumptions:**
  - `order_id` and `amount` stay the same for the whole run (R-SIG-1).
  - A charge only ever answers ok, declined or error (R-API-1).
- **11 properties:**
  - Each charge uses the order and amount the function was called with.
  - ValueError for an invalid amount.
  - Return True right after an "ok"; return False otherwise.
  - Retry after "error" on the first or second attempt; no more than 3 charges.
  - No charge after "declined", and none after "ok".
  - Wait 2 seconds before the second attempt and 4 before the third.
  - Keep trying until a charge goes through.
- **1 scenario:** the example run exactly (charge returns error, sleep 2 seconds, charge returns ok, return True).
- **2 ghosts:**
  - `attempts` counts the charges made so far. Without it, the first charge (the first step of a run) couldn't trigger the retry rule.
  - `waited` adds up the seconds slept since the last charge.
- **Decision:** R-RET-1, "once a charge returns", reading 1, as instructed. The notes on V1-RET-1a and V1-RET-1b say so.

**Left unformalized:** only R-FR-1, R-FR-2 and R-FR-3. They are the adapter's frame rules, so they're marked `covered_by` F-END, F-ZERO and F-LIMIT, which are added to every set anyway.

**Problems in the specification**
1. **Rule 7 contradicts rules 3 and 4.** I formalized it literally: with a valid amount, the function may not return until some charge has returned "ok". But no charge is allowed after "declined" or after 3 errors, and a run makes at most 8 calls. So when the service never answers "ok", no function can satisfy the rules. It also means "False otherwise" in rule 2 can never happen. I left this as it is, and it should show up as a consistency conflict.
2. **Rule 1 overlaps with "False otherwise" in rule 2.** If an invalid amount gets no "ok", both rules apply. I limited the "return False" case to valid amounts and said so in the note.
3. **Rule 1 doesn't say whether the amount is checked before charging.** "Return True after ok" applies to any charge. Combined with rule 1, that means in practice a function can't charge an invalid amount.
4. **"Wait 2 seconds" isn't flagged as ambiguous, but it is.** I read it as 2 seconds of sleep in total between the two attempts, so two calls of `sleep(1)` also pass. Another reader could require exactly one call of `sleep(2)`, which would make the formalizations disagree.
5. **Rule 6 adds nothing under this reading.** Since the function returns as soon as a charge returns "ok", it can never charge again anyway. I kept V1-ONCE-1 as a separate property.