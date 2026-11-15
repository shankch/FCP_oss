I wrote `requirements_draft.yaml` with 9 requirements. `fcp anchor` accepted every quote and wrote `requirements.yaml`. I ran it a second time after giving each ambiguity within a requirement a distinct phrase, so that a `decisions` entry can name exactly one; it accepted everything again.

**Requirements**
| ID | Kind | What it says |
|---|---|---|
| R-TASK-1 | non_functional | "Complete this function": write the function, keeping its given signature |
| R-IF-1 | definition | The function is named `correct_bracketing` and takes one `str` parameter, `brackets` |
| R-IN-1 | assumption | The argument contains only `(` and `)`; behaviour on other arguments is unspecified |
| R-RET-1 | guarantee | On a valid argument the call returns a bool, without raising and without hanging |
| R-DEF-1 | definition | What "correctly bracketed" means: properly nested and balanced |
| R-RES-1 / R-RES-2 | guarantee | Returns True when correctly bracketed, False when not (split into two separately checkable directions) |
| R-EX-1 | scenario | `correct_bracketing("(")` returns False |
| R-FR-1 | FRAME guarantee | F-ZERO: `result` is false unless `outcome` is 0 |

**Ambiguities flagged**
- **The function's meaning comes only from its name.** The docstring never says what is returned, so R-DEF-1, R-RES-1 and R-RES-2 all rest on reading the name.
- **What counts as "correct":** properly nested, equal counts only, or every `(` closed with stray `)` allowed.
- **The empty string:** it could be correct (True), not correct (False), or not a valid input.
- **What `a string of "(" and ")"` allows:** possibly empty, non-empty, or must contain both characters.
- **Other characters:** they could be out of contract, ignored, make the answer False, or require an exception.
- **The return type:** the signature has no return annotation, so it could be a strict bool or any truthy/falsy value.
- **"Complete":** keep the signature and docstring exactly, or allow changes to them.

**Possible contradictions, each recorded on both requirements**
- **R-IN-1 vs R-EX-1:** if "a string of `(` and `)`" means the string must contain both, the example argument `"("` is not a valid input.
- **R-RET-1 vs R-EX-1:** if "correct" is read as a verb (the function fixes the brackets and returns a string), that clashes with the example returning `False`.