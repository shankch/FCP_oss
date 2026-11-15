I wrote `formal/agent_b.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I meant for every item. Those were the only checks I could run: `fcp check` isn't available to agents, so the spec-only analyses (consistency, whether scenarios can be reached) haven't been run.

**Items: 12**
- **1 assumption** (`RB-IN-1`, R-IN-1): every character of the argument is `(` or `)`, and the empty string is allowed.
- **2 dont_cares** (R-IN-1): `outcome` and `result` are left unconstrained for any other argument.
- **4 properties:**
  - `RB-RET-1`: every allowed argument returns a bool.
  - `RB-RES-1`: a correctly bracketed argument returns True.
  - `RB-RES-2`: an incorrectly bracketed argument returns False.
  - `RB-EX-1`: `"("` returns False.
- **5 scenarios:**
  - `"("` returns False.
  - `""` returns True.
  - `"(()())"` returns True.
  - `")("` returns False.
  - `"())"` returns False.
- **Model:** each call is independent and the function keeps no state, so a ghost carried across cycles would model nothing. Instead, defs model the left-to-right scan within one call: the running depth (`(` minus `)`) must never go negative and must end at 0.
- **Decisions:** all 11 flagged phrases are recorded, each with reading 1 (the most literal).

**Left unformalized: 4**
- **R-TASK-1:** it's about the form of the code you deliver, which doesn't show up in the trace of calls.
- **R-IF-1:** it only names the function and its parameter; the `function` section of `design.yaml` already covers that.
- **R-DEF-1:** it's a definition, built as the scan defs; `covered_by` RB-RES-1 and RB-RES-2.
- **R-FR-1:** `covered_by` the frame rule F-ZERO, which `frame.md` says need not be restated.

**Problems in the specification**
1. **The return value is never stated.** The docstring doesn't say what the function returns. R-RES-1 and R-RES-2 quote only the signature, so their whole meaning rests on the function name. The single example `("(") → False` is the only evidence that the answer is a bool, and there's no return annotation.
2. **"Correct bracketing" is undefined.** It could mean properly nested or just equal counts. I took proper nesting, as R-DEF-1 states it.
3. **The empty string isn't covered.** I followed the literal definition, under which `""` is correct and returns True.
4. **"A string of ( and )" doesn't say how other characters are handled.** It could be a precondition on the caller, or the function could ignore them, reject them, or return False. I took it as a precondition, so behaviour on other characters is a don't-care.
5. **The assumption reaches too far with independent calls.** An assumption is required to have held in every earlier cycle, so one out-of-contract call would switch off checking for every later call. I guarded each property with the precondition so this can't happen.
6. **R-EX-1 is classed as a scenario, but a doctest asserts a result.** I formalized it as both a scenario (`RB-EX-1-S`) and a property (`RB-EX-1`), and said so in the notes.