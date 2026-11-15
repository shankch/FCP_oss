I've written the draft and anchored it. The anchor run accepted all 9 quotes on the first try (`anchored 9 requirements`), and each one landed on the correct source lines. The output is in `requirements.yaml`.

**Requirements**
| ID | Kind | What it says |
|---|---|---|
| R-FN-1 | definition | The function is `correct_bracketing(brackets: str)` |
| R-FN-2 | guarantee | On valid input, a call finishes, raises nothing and returns True or False ("Complete this function:") |
| R-IN-1 | assumption | `brackets` contains only `(` and `)` |
| R-RET-1 | guarantee | Return True if every opening bracket has a corresponding closing bracket |
| R-EX-1…4 | scenario | `"("`→True, `"()"`→False, `"(()())"`→False, `")(()"`→True |
| R-FR-1 | guarantee (FRAME) | F-ZERO: `result` is false unless `outcome` is 0 (this ID matches `design.yaml`) |

**Main finding: the four examples contradict the docstring.** Each one is the exact opposite of normal bracket matching:
- `"()"` and `"(()())"` → False contradicts R-RET-1 however it's read, because every opening bracket there is matched, so the rule requires True.
- `"("` → True and `")(()"` → True contradict R-RET-1 only if "if" means "if and only if". (`")(()"` also fits looser readings of "corresponding".)
- I recorded this as an ambiguity on R-RET-1 and on each of R-EX-1 to R-EX-4. The two readings are "the sentence is right and the examples are wrong" and "the examples are right, so the function returns True exactly when the bracketing is *incorrect*".

**Other ambiguities I flagged**
- **"return True if":** either True only when the condition holds, with no rule for False, or True exactly when it holds and False otherwise.
- **"a corresponding closing bracket":** three readings: proper nested matching, simply counting brackets, or "some `)` appears later" (one `)` could serve several `(`).
- **"every opening bracket":** whether a `)` with no opening bracket before it (as in `")"` or `"())"`) is ignored or makes the bracketing incorrect, as the function name suggests.
- **`"(" and ")"`:** whether other characters are don't-care, should be skipped, or should be rejected. The frame does put such strings in the trace.
- **"a string of":** whether the empty string is valid input. If it is, the rule gives True, since there are no opening brackets to match.
- **"Complete this function":** whether a True/False answer is required for every input, and whether truthy/falsy values other than True/False are acceptable.