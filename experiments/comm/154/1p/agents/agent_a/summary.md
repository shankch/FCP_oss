I wrote `formal/agent_a.yaml`. `fcp lint` reports clean, and I read the `fcp explain` output back: every item says what I intended.

**15 items in total**
- **9 properties:**
  - `RA-RET-1`: every call returns a bool (`outcome == 0`).
  - `RA-RULE-1` / `RA-RULE-2`: `cyc → returns True` and `!cyc → returns False`. `cyc` is a macro meaning "b, or some rotation of b, occurs as a contiguous substring of a". It has no ghost state. A rotation's characters can't use `%` directly, because FCP-PL only allows a constant divisor and here the length of b varies, so I used a conditional expression instead.
  - `RA-EX-1`…`RA-EX-6`: each docstring example as a guarantee on that exact call.
- **6 scenarios:** `RA-EX-1-S`…`RA-EX-6-S`, one per example. The examples are marked as scenarios in requirements.yaml, but the prompt's `=>` states what the call returns, so I also made each one a property. They are the only part of the prompt that isn't open to interpretation.
- **8 decisions:** reading 1 for every flagged phrase. That means the stated rotation rule, an empty b always counts as a match (so the call returns True), letters are compared by exact code (case matters), every call must return a bool, and only the real bools True/False count.

**3 requirements left unformalized**
- **R-SIG-1:** it only defines the function's name and argument order. The function binding in design.yaml already does this, so there's nothing to check on the trace.
- **R-FR-1 and R-FR-2:** these are adapter frame rules, already in design.yaml as F-ZERO and F-CODE (`covered_by` points to those). frame.md says they need not be restated.

**Problems in the specification**
1. **The prompt states no rule, only six examples.** The rotation rule is the decomposer's inference. A second rule also fits all six: "some rotation of b *or of reversed b* is a substring". For example, `candidate("aeb","abe")` is False under my reading but True under that one, and it uses only the test alphabet `abe`. Under the most literal reading of the prompt (reading 3), only the six example calls are constrained. That's why I also stated the examples as properties: they hold whichever reading you take.
2. **No example covers an empty `b` or upper-case letters.** Those two readings are pure choices.
3. **Nothing says what happens on bad input.** Whether every call must return a bool (no exceptions, no None) is inferred from "Complete this function"; the prompt never says it.

The six examples check out by hand against the `cyc` formula. I also wrote a Python script to compare the formula with a direct rotation check over all short strings, but running it needed your approval, so it hasn't run. It's in the scratchpad as `cyc_check.py` if you want to run it.