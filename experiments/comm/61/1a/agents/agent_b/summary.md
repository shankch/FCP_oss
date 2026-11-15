Lint is clean and the English rendering reads as intended, so I'm finishing up with the summary.

## Summary

I wrote `formal/agent_b.yaml`. It has **15 items** and passes `fcp lint` with no errors. The `fcp explain` output matches what I meant for each item.

**The model:** `candidate` keeps no state between calls, so state carried from one cycle to the next (ghost state) would be wrong here. Instead, the model is a set of defs that compute the nesting depth across the argument:
- `valid`: every character is `(` or `)`.
- `never_below_zero`: no prefix has more `)` than `(`.
- `final_depth_zero`: the counts of `(` and `)` are equal at the end.
- `matched`: both of the above hold.

I checked the model by hand against all four doctests and the empty string; each gives the expected answer.

**The 15 items:**
- **Assumption (1):** `valid` (R-IN-1).
- **Don't-cares (2):** `result` and `outcome` are left free when the input is not `valid` (R-IN-1).
- **Properties (6):**
  - R-RET-1: valid and matched gives `outcome == 0 && result`.
  - R-RET-2: valid and not matched gives `outcome == 0 && !result`.
  - One property per doctest (R-SC-1 to R-SC-4): a doctest fixes the output for that input, so I stated it as a guarantee too.
- **Scenarios (5):** one cover per doctest, plus the empty string returning True (R-IN-1).

**Not formalized:**
- **R-NF-1:** the deliverable being a Python function `candidate(brackets: str)` is set by the binding in `design.yaml`, not by any trace, so FCP-PL can't express it.
- **R-FR-1:** marked `covered_by: [F-ZERO]`, the frame rule that is added to every set automatically.

**Decisions:** I took reading 1 for all eight flagged phrases.

**Problems in the specification:**
1. **The main sentence doesn't define matching on its own.** Read word for word, "every closing or opening bracket has a corresponding closing or opening bracket" pairs closing with closing and opening with opening (reading 4). That contradicts the doctests for `"()"` and `"(()())"`.
2. **Nothing in the sentence says `(` must come before `)`.** Only the example `")(()"` → False rules out simply counting each kind. Even then, a reading where one bracket can serve as the partner of several others (reading 3) still fits every doctest. I chose proper nesting because "corresponding" suggests one-to-one pairs; all of this is in the notes.
3. **"Return True if" only says when to return True.** Taken word for word it says nothing about unmatched strings. I read it as "if and only if" because the False examples show it and because the docstring describes a True/False test. The note on that property says so.
4. **The spec doesn't say what happens with other characters or the empty string.** I treated the input description as a rule on callers, so other characters are out of contract. The empty string counts as valid and returns True. The properties also check `valid` themselves, so they apply call by call even where the assumption doesn't hold.