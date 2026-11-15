I wrote the draft and anchored it. `fcp anchor` accepted all 12 requirements on the first run, and every quote landed on the right lines. The output is in `requirements.yaml`.

The prompt never says what `candidate` should do. It is a function stub with six example calls and nothing else, so the main rule had to be worked out from the examples.

**Requirements**

| ID | Kind | Content |
|---|---|---|
| R-SIG-1 | definition | The function is `candidate(a, b)`, with `a` as the first argument and `b` as the second. |
| R-RET-1 | guarantee | Every call finishes and returns True or False: no exception, no hang, no other type. |
| R-RULE-1 | guarantee | If `b`, or some rotation of `b` (a prefix moved to the end), is a contiguous substring of `a`, the call returns True. |
| R-RULE-2 | guarantee | Otherwise it returns False. This covers `b` being longer than `a`. |
| R-EX-1…6 | scenario | One per example. Each text says why that example rules out a competing rule. |
| R-FR-1, R-FR-2 | guarantee (FRAME) | F-ZERO and F-CODE. |

**How the rule was chosen**
- The rotation-substring rule is the simplest one that matches all six examples.
- Plain substring is ruled out by `("abab","baa") => True`.
- Subsequence is ruled out by `("abcd","abd") => False`.
- "Some permutation of `b` is a substring" is ruled out by `("efef","eeff") => False`.
- I recorded the inferred rule as two requirements, one for when it returns True and one for when it returns False, so each can be checked separately. Both quote the whole set of examples, since nothing else in the prompt supports the rule.

**Flagged ambiguities**
- **No stated rule:** three readings are recorded:
  - rotations of `b`;
  - rotations of `b` or of reversed `b`, which also matches all six examples;
  - only the six example calls are constrained.
- **Empty `b`:** no example has one. The readings are True (the empty string is a substring of everything), False, or either result allowed.
- **Upper and lower case:** every example is lower case, so the prompt doesn't say whether "A" should match "a".
- **"Complete this function":** this could mean every call must return a bool, or only the example calls must.
- **`=> True` / `=> False`:** this could mean exactly the bool, or any truthy or falsy value such as 1 or None.

**Contradictions:** none. All six examples agree with the rotation rule, and no two statements conflict.

One flagged phrase quotes the prompt directly ("Complete this function"). The others are descriptive labels, like "an empty b (no example has one)", because the prompt has no text about those cases. `fcp anchor` accepted them.