I've written `formal/variant2.yaml`. `fcp lint` reports it clean, and I read the `fcp explain` rendering back: every item means what I intended.

**Items: 14**
- **2 assumptions:**
  - `V2-ARGS` (R-SIG-1): the arguments don't change during a run.
  - `V2-ANSWER` (R-API-1): a charge only answers 0, 1 or 2.
- **11 properties:**
  - R-CALL-1: one item.
  - R-ERR-1: one item.
  - R-RET-1: two items, one for True and one for False.
  - R-RETRY-1: two items, "charge again after an error" (`hold_until`) and "at most 3 charges".
  - R-DECL-1: one item.
  - R-WAIT-1: two items, before the 2nd and before the 3rd charge.
  - R-ONCE-1: one item.
  - R-KEEP-1: one item.
- **1 scenario:** R-EX-1, the exact example run: charge gets error, sleep(2), charge gets ok, return True.
- **Decision recorded:** R-RET-1, "once a charge returns", reading 2, as you instructed. Both R-RET-1 notes say so: the rule fixes only the value returned, not that the function returns straight after the "ok".

**Unformalized: none.** R-FR-1 to R-FR-3 are covered by the frame items (F-END, F-ZERO, F-LIMIT), which are part of every set.

**Ghost state:** there are two counters.
- `slept` (seconds slept since the last charge) is needed because I read "wait 2 seconds before the second attempt" as the total waiting time between attempts. So sleep(1) then sleep(1) passes, and sleep(2) then sleep(2) fails.
- `charges` (charges made so far) replaces nested `once(... prev(...))` counting. With only lint and explain available, I couldn't confirm whether the tool skips those expressions in the first cycles after reset. If it did, the error on the first charge would never start a retry obligation, and two back-to-back charges would escape the wait check. A plain counter has no such risk.

**Problems in the specification**
1. **Rule 7 contradicts the rest (R-KEEP-1).** "Keep trying until the charge goes through" rules out ending without an "ok". But after "declined" (R-DECL-1) or three errors (R-RETRY-1), the function must stop charging and return False (R-RET-1). I formalized rule 7 literally and didn't repair it. It also can't be met at all when the service never answers "ok", because a run is limited to 8 calls (F-LIMIT).
2. **"False otherwise" (R-RET-1) clashes with rule 1 (R-ERR-1)** for amounts outside 1–1,000,000, where rule 1 requires a ValueError. I treated rule 1 as taking precedence, so the R-RET-1 and R-KEEP-1 items apply only to valid amounts. The notes say this; the fully literal reading would make the requirements contradict each other for every invalid amount.
3. **"Between 1 and 1,000,000" isn't flagged as ambiguous** in requirements.yaml. I read it as inclusive.
4. **Rule 1 doesn't say the function must raise before making any call**, so a charge made before the ValueError isn't forbidden.
5. **Under reading 2, nothing requires returning immediately after an "ok".** Further charges are forbidden by R-ONCE-1, but further sleeps are not.