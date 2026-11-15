I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I intended for every item. I couldn't run the deeper analyses, because `fcp monitor` and `check` aren't available to an agent. So the contradiction below is something I worked out by hand; the tool hasn't confirmed it.

**Items: 14**
- **6 properties:**
  - **RV-RES-1:** a non-empty string with as many "(" as ")" gets a truthy answer.
  - **RV-IN-1:** any two non-empty calls with the same "(" and ")" characters, in order, get the same outcome and result.
  - **RV-EX-1 to RV-EX-4:** one per doctest example.
- **4 scenarios** (RV-EX-1-S to RV-EX-4-S): each example's call and answer must be possible.
- **4 don't-cares:** `result` and `outcome` are left free for the empty string (R-IN-1), and for non-empty strings whose counts differ (R-RES-2).
- **9 `decisions`**, one per flagged phrase, using the readings you assigned. Every affected item's `note` says it uses the instructed reading.

**Not formalized**
- **R-IF-1, R-IF-2:** these are about the deliverable and the function signature, which a trace of calls can't express.
- **R-FR-1:** this is the adapter's frame rule. It is listed as `covered_by: [F-ZERO]` because frame.md says it need not be restated.

**Problems in the specification**
1. **R-RES-1 contradicts R-EX-4.** With order-insensitive matching, ")(()" has two "(" and two ")", so RV-RES-1 requires a truthy answer. The doctest requires the bool False. I formalized both literally and didn't repair it. No answer satisfies both for that input, so scenario RV-EX-4-S should be unreachable.
2. **Two readings combine awkwardly.** With order-insensitive matching plus full balance, the condition becomes simply "equal counts". Full balance's "the running count never goes negative" part has no effect once order doesn't matter. The notes say this.
3. **"Any truthy value" can't be checked exactly.** Outcome 2 means "returned something other than a bool", and the trace doesn't record whether that value is truthy. So the encoding also accepts falsy values like `None`, `0` or `""`. The doctests print the bool True or False, so they are stricter than RV-RES-1 for their own strings.
4. **Most unbalanced strings are unconstrained.** Under the one-direction reading of "return True if", the prompt never says what unbalanced strings return. Only the examples fix some of them to False, and RV-IN-1 extends those answers to strings with the same brackets plus other characters, such as "a(". The empty string is entirely unconstrained.