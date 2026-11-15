I've written `requirements_draft.yaml`. `fcp anchor` accepted all 13 quotes on the first run and wrote `requirements.yaml`, so no quotes needed fixing.

**The 13 requirements:**
- **R-IF-1** (non_functional): the code must be a Python function `will_it_fly(q, w)`.
- **R-OUT-1** (guarantee): every call returns True or False. It never raises, hangs, or returns anything else.
- **R-FLY-1/2/3** (guarantees):
  - If q is a palindrome and its sum is at most w, the result is True.
  - If q is not a palindrome, the result is False.
  - If the sum is greater than w, the result is False.

  I split "False otherwise" into the last two because each failure can be checked on its own.
- **R-DEF-1/2/3** (definitions): what "will fly" means, that "balanced" means a palindromic list, and the weight condition.
- **R-EX-1..4** (scenarios): the four examples, each with its comment.
- **R-FR-1** (FRAME, guarantee): F-ZERO, "`flies` is false unless `outcome` is 0". I used this ID because `design.yaml` already refers to it.

**Ambiguities flagged:**
1. **"less than or equal" vs. the example comments:** the rule says the sum may equal w, but the comments justify their answers with "is less than the maximum possible weight". It's a possible contradiction about what happens when the sum equals w. I recorded it on R-DEF-3, R-FLY-1, R-FLY-3, R-EX-3 and R-EX-4. None of the examples tests a sum equal to w, so they don't settle it.
2. **The empty list:** the spec doesn't say whether `[]` counts as a palindrome. If it does, `will_it_fly([], w)` returns True; if not, False. Recorded on R-DEF-2, R-FLY-1 and R-FLY-2.
3. **"will fly if":** this can mean "if and only if", or it can be only a sufficient condition. Under the second reading, "False otherwise" doesn't decide unbalanced or overweight lists. Recorded on R-DEF-1, R-FLY-2 and R-FLY-3.
4. **True/False:** the spec doesn't say whether the result must be a real Python bool or whether values like 1 and 0 count. Recorded on R-OUT-1.

I found no other contradictions. All four examples agree with the rule under every reading above.