I wrote `formal/agent_a.yaml`. It has 6 formal items plus 15 reading decisions. `fcp lint` reports clean, and the `fcp explain` output matches what I intended for each item.

**Items**
- **Assumptions:** `RA-ENV-1` (`number >= 0`), `RA-ENV-2` (`need >= 1`) and `RA-ENV-3` (`remaining >= 0`).
- **Property:** `RA-API-1`, `outcome != 1`: every call with valid arguments returns, without raising or hanging. This is stronger than the requirement's wording. The trace can't tell a rejected call from any other exception, so I read "the call is accepted" as "the call is answered". The note says so.
- **Don't-cares (both for R-OUT-1):** `RA-D-RESULT` leaves `result` free. `RA-D-OUTCOME` leaves the return form free (a fitting list, outcome 0, or anything else, outcome 2), but `RA-API-1` still rules out outcome 1. `fcp explain` calls `outcome` "intentionally unconstrained", which overstates it; the note explains the split.

**Left unformalized (8)**
- **R-CTX-1, R-DEF-1, R-DEF-2, R-DEF-3:** definitions and narrative. Nothing in the prompt connects them to the result.
- **R-TASK-1:** non-functional. It concerns the shape of the response (keep the signature and docstring), which a trace of calls can't observe. Its observable part is `RA-API-1`.
- **R-EAT-1 and R-EAT-2:** I read them as context and purpose (readings 4 and 2). Under any reading, the prompt never says whether or how the return value shows the carrots eaten, so there is no signal to constrain.
- **R-FR-1:** marked `covered_by: [F-EMPTY]`, the frame rule `design.yaml` already adds to every set.

**Problems in the specification**
1. **The docstring looks truncated.** It never says what `eat` returns or what `remaining` means. As a result, the formalization only constrains the inputs and requires that calls return.
2. **`remaining` is never described**, apart from appearing in the signature. Read as "carrots in stock", it would contradict "to complete the day's meals" whenever `remaining < need`. I took the literal reading (meaning left open), under which no contradiction arises, and recorded that.
3. **R-ENV-2's wording disagrees with its quote.** The requirement says `need` is "non-negative", but the quoted "you need to eat more carrots" implies `need >= 1`. I used the quote, so calls with `need == 0` fall outside the checked environment. Under the other reading they would be checked.
4. **"Accepted" in R-API-1 can't be observed exactly in the trace**, as explained under `RA-API-1` above.
5. **R-ENV-1 and R-ENV-3 always hold.** The 11-bit unsigned input signals can't carry negative values. I kept them anyway, because they record what the prompt expects of the caller.