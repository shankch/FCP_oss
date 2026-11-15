I wrote 13 requirements to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**What's in it**
- **Deliverable and interface:** R-IF-1 says the job is to complete the given stub (non_functional). R-IF-2 defines the signature `will_it_fly(q, w)` (definition).
- **Result:** R-FLY-1 says it returns True when q will fly; R-FLY-2 says it returns False otherwise. Both are guarantees.
- **Weight:** R-WT-1 defines q's weight as the sum of its elements, and R-WT-2 defines w as the maximum possible weight. R-WT-3 is the guarantee that a q heavier than w returns False.
- **Balance:** R-BAL-1 is the guarantee that an unbalanced q returns False.
- **Scenarios:** R-EX-1 to R-EX-4 cover the four examples.
- **Frame:** R-FR-1 is F-ZERO (`flies` is false unless `outcome` is 0). Its ID matches the `req` that `design.yaml` uses.

**The main gap:** the prompt never says what "will fly" means. The only clues are the comment on the first example ("less than the maximum possible weight, but it's unbalanced") and the four examples. So the weight and balance rules are inferred, and they are only stated as conditions a list must meet to fly.

**Ambiguities flagged**
- **"will fly"** (R-FLY-1): either balanced and within weight are the only conditions, or flying is left undefined beyond those two conditions and the examples.
- **"returns True" / "False"** (R-FLY-1, R-FLY-2): the actual bools, or any truthy/falsy value. This matters because the design records any non-bool return as outcome 2.
- **"the object q"** (R-FLY-1): for an empty list, three readings: it flies, it doesn't fly, or the result is left open.
- **"less than the maximum possible weight"** (R-WT-3): whether a sum exactly equal to w is allowed (`sum <= w`) or not (`sum < w`).
- **"unbalanced"** (R-BAL-1): q isn't a palindrome, its first and last elements differ, or its two halves have different sums. The examples can't tell these apart, but lists of length 4 or more can.

I found no contradictions: all four examples fit every reading.