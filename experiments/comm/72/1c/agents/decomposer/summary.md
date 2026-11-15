I wrote `requirements_draft.yaml` and ran `fcp anchor`. All 18 quotes were accepted on the first run, and `requirements.yaml` now exists. I checked the line each quote was matched to, including the two similar comments on lines 17 and 20.

**Requirements**
- **Interface:** R-API-1 (the function signature, non_functional); R-IN-1 and R-IN-2 (q is a list of numbers and w is a number, both assumptions).
- **Definitions:** R-DEF-1 (balanced means the list is a palindrome); R-DEF-2 (sum of elements ≤ w, with equal counting as within the limit); R-DEF-3 (q flies when it is balanced and within the weight limit).
- **Guarantees:**
  - R-RET-1: balanced and within the limit → True.
  - R-RET-2: not balanced → False.
  - R-RET-3: sum greater than w → False.
- **Scenarios:** R-EX-1 to R-EX-4 are the four example calls. R-WHY-1 to R-WHY-4 are the comments under them, recorded separately because each comment disagrees with its own example's result.
- **Frame:** R-FR-1 is F-ZERO (`flies` is false unless `outcome` is 0). It uses the id that `design.yaml` already refers to.

**Contradictions (recorded on both sides of each pair)**
- **All four example results contradict the rule.** `[1, 2], 5 ➞ True` and `[3, 2, 3], 1 ➞ True` should be False under the rule. `[3, 2, 3], 9 ➞ False` and `[3], 5 ➞ False` should be True. Each example is flagged against the rule it breaks (R-RET-1, -2 or -3) and against its own comment.
- **The examples follow a consistent pattern:** every result is the exact opposite of the rule. So one possible reading is "the function returns True when q does *not* fly." I offered this as the second reading on R-RET-1 to -3 and on each comment, with the rule as written as the first reading.

**Other ambiguities**
- **"will fly if"** (R-DEF-3): this could mean "if and only if", or only that the condition is enough to fly. If it only means "enough", the spec doesn't say what happens to other lists, so "False otherwise" no longer clearly applies to unbalanced or overweight ones.
- **"palindromic list"** (R-DEF-1): it's unclear whether the empty list counts as balanced.