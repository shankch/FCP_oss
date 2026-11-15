I split spec.md into 7 requirements, 6 from the spec and one frame rule, and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run ("anchored 7 requirements") and wrote `requirements.yaml`.

| ID | Kind | What it requires |
|---|---|---|
| R-IF-1 | non_functional | A complete Python function `candidate` that takes one argument, `arr` |
| R-IN-1 | assumption | `arr` is a list of integers |
| R-CNT-1 | guarantee | The result is the smallest number of elements that must change to make `arr` a palindrome, i.e. the number of mirror pairs whose two values differ |
| R-CNT-2 | guarantee | The function ends normally and returns that count as a non-negative integer |
| R-DEF-1 | definition | A palindromic array: `a[i] == a[n-1-i]` for every `i` |
| R-DEF-2 | definition | One change sets one element to another value |
| R-FR-1 (FRAME, rule F-ZERO) | guarantee | `changes` is 0 unless `outcome` is 0. The ID matches the one design.yaml already uses for this rule. |

**Ambiguities flagged:**
- **Empty list:** it may be a valid input (answer 0) or outside what the function must handle. Negative integers are also unclear.
- **What gets counted:** the minimum (one per mismatched pair), or every element that differs from its mirror (twice as many).
- **"find":** it may mean return the number or print it.
- **"read the same backwards":** element by element, or as a string of decimal digits (e.g. `[12, 1]` reads "121").
- **"any other element":** any value at all, or only a value already in the array. The minimum comes out the same either way.

**Apparent contradiction:** the spec says to count "the number of elements that need to be changed", but then defines the answer's unit as one "change". For a minimal set of changes the two counts are equal, but the text names different units. I recorded it as an ambiguity on both R-CNT-1 and R-DEF-2.

The spec gives no examples, so there are no scenario requirements.