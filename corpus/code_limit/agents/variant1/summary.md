I've written `formal/variant1.yaml`. `fcp lint` reports no errors, and I read back the `fcp explain` output: every item says what I meant.

**Items: 7 formal items.** Six are properties: V1-ERR-USER, V1-ERR-TIME, V1-RET-1, V1-MAX-1, V1-FAIR-1 and V1-PEN-1. One is a scenario, V1-EX-1. All four flagged phrases are recorded under `decisions` with reading 1, as you specified, and each affected item says so in its note.
- **Counting:** I used three fixed-value placeholders that range over all values (customer `u`, window end `e`, denial time `d`) and nested `once(prev(...))` to count earlier attempts. This avoids extra tracking state, and windows are measured in `now` values rather than call order.
- **One tracked value:** `last`, the time of the previous call, which is 0 before the first call. It's needed because "valid" must also be checked on the first call, where `prev(now)` isn't evaluated.
- **Not verified:** `fcp monitor` isn't available to agents, so I couldn't check two things against the compiled monitor. I'm relying on the IR document for both: a tracked value equals its `init` on the first call after reset, and a `prev` nested inside `once` counts as false on that call.

**Left unformalized (4), all with `covered_by`:**
- **R-SIG-1:** the signature is fixed by the interface; that a valid call returns a bool is V1-RET-1.
- **R-IN-1:** a definition; the customer range is used by V1-ERR-USER, V1-RET-1, V1-FAIR-1 and the range of `u`.
- **R-COUNT-1:** a statement about what is counted, not a separate behaviour; V1-MAX-1 and V1-FAIR-1 count only attempts that returned True.
- **R-FR-1:** already stated by frame rule F-ZERO.

**Problems in the specification (formalized as written and noted in the items, not fixed):**
1. **Rule 4 contradicts rule 5 under every reading.** One customer is allowed at 0, 50 and 55, which rule 4 forces, and denied at 58, which rule 2 forces. At 61 only 50 and 55 are in the last 60 seconds, so rule 4 requires True while rule 5 requires a denial.
2. **The given reading of "the previous call" lets time go backward**, which causes a second contradiction. After a call that raised, a valid call can carry an earlier time: u is allowed at 100, 110 and 120, a raising call comes at 0, then u calls at 90. No allowed attempt lies in [30, 90], so rule 4 requires True. But [90, 150] would then hold 4 allowed attempts, which rule 2 forbids.
3. **Penalties chain.** With "every denied attempt starts 10 seconds", a customer who keeps retrying at most 10 seconds apart is locked out indefinitely. This makes problem 1 worse.
4. **Gaps in the text I had to fill (each noted in the item):**
   - It doesn't say whether rule 1 takes precedence. I read rule 4 as applying only to calls that rule 1 doesn't make raise.
   - The endpoints of "the last 60 seconds" aren't flagged. I used the same convention as the given R-MAX-1 reading: an attempt exactly 60 seconds ago counts.
   - It doesn't say whether a call that raised counts as a "denied attempt". I took it as not counting.
   - It doesn't say whether a later attempt in the same second as a denial falls in "the next 10 seconds". I included it.