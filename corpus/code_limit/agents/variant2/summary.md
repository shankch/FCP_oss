I wrote `formal/variant2.yaml`. `fcp lint` reports `lint: clean`, and the `fcp explain` output matches what I meant for every item. I did not run `fcp check`, because it might try to run code that isn't in the workspace. So the contradiction described below and whether the scenario can actually happen come from my own reasoning, not from the tool.

**Items: 7 formal items**, plus the frame item F-ZERO, which is added to every set automatically.
- **Properties (6):**
  - `V2-ERR-USER` and `V2-ERR-TIME` (R-ERR-1): a user above 1,000, or a `now` earlier than the previous call that did not raise, makes the call raise ValueError.
  - `V2-RET` (R-RET-1): every other call returns True or False.
  - `V2-MAX` (R-MAX-1): no customer gets more than 3 allowed attempts in any 60 seconds.
  - `V2-FAIR` (R-FAIR-1): an attempt is allowed when the customer had fewer than 3 allowed attempts in the last 60 seconds.
  - `V2-PEN` (R-PEN-1): attempts are denied for 10 seconds after an attempt denied by the limit.
- **Scenario (1):** `V2-EX` (R-EX-1): one customer's calls at 0, 1 and 2 seconds return True and a fourth at 3 seconds returns False.
- **Supporting state:** one arbitrary customer `u` (from 0 to 1,000) and ghost state that tracks:
  - the time of the last call that did not raise;
  - `u`'s last three allowed attempt times;
  - `u`'s last attempt denied by the limit.

  The rules depend on time windows, so they can't be stated without this state.
- **Decisions:** I took reading 2 for all four flagged phrases, as instructed, and said so in the note of every item each one affects.

**Left unformalized (all with `covered_by`):**
- **R-SIG-1:** it only defines the interface, which `design.yaml` already encodes. There is no behaviour to state.
- **R-IN-1:** a definition. The 0–1,000 range is used in `V2-ERR-USER`, `V2-RET` and `V2-FAIR`.
- **R-COUNT-1:** it says what rules 2 and 4 count. The ghost state records only allowed attempts, so it is covered by `V2-MAX`, `V2-FAIR` and `V2-PEN`.
- **R-FR-1:** already the frame item F-ZERO.

**Problems in the specification:**
1. **Rules 4 and 5 contradict each other.** Take attempts allowed at 0, 1 and 2, and one denied by the limit at 59. An attempt at 60 has only 2 allowed attempts in the last 60 seconds, so rule 4 says allow it. It is also within 10 seconds of the denial, so rule 5 says deny it. I formalized both as written and noted the conflict in both items.
2. **Rules 1 and 4 overlap.** A call with `now` going backwards must raise under rule 1, but rule 4 would allow it. I applied rule 4 only to calls that rule 1 doesn't make raise.
3. **"In the last 60 seconds" (rule 4) is not flagged as ambiguous, but it has the same edge question as rule 2.** I read it the same way as rule 2: an attempt exactly 60 seconds earlier doesn't count. Under that reading, rules 2 and 4 together say an attempt is allowed exactly when the customer is under the limit.
4. **Other gaps the text leaves open, and what I chose:**
   - **Calls that raise:** they neither count toward the limit nor count as denied attempts.
   - **"Denied by the limit":** an attempt is denied by the limit even if it was also inside a penalty.
   - **Same-second calls:** later calls in the same second as a denial fall inside the penalty.
   - **A newer denial by the limit** restarts the 10 seconds.
   - **The example** doesn't say the object is new, so the scenario doesn't require it.