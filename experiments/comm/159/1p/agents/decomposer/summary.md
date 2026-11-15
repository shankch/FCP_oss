I wrote 13 atomic requirements in `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run, so no fixes were needed, and the anchored file is at `requirements.yaml`.

**The prompt is very thin.** The docstring is one sentence, which looks truncated. It never mentions `remaining` and never says what `eat` returns or in what form. Most of the decomposition is therefore definitions and flagged ambiguities rather than firm guarantees.

| Area | IDs | Kind | What they cover |
|---|---|---|---|
| Task | R-TASK-1 | non_functional | "Complete this function:" (may the signature and docstring change, or only the body?) |
| API | R-API-1 | guarantee | `eat` takes `number, need, remaining` in that order (the argument types aren't stated) |
| Context | R-CTX-1 | definition | "hungry rabbit": just story, eats all it can, or can stay hungry? |
| Definitions | R-DEF-1/2/3 | definition | `number` is carrots already eaten. `need` is either the extra carrots still needed or the day's total. `remaining` is either the carrots in stock, the carrots still to eat, or undefined. |
| Environment | R-ENV-1/2/3 | assumption | Each argument is a non-negative count. For `need`, does "more carrots" mean it must be at least 1? |
| Eating | R-EAT-1/2 | guarantee | "eat more carrots": exactly `need`, up to `min(need, remaining)`, at least `need`, or just context? "to complete the day's meals": always completed, or only the goal? |
| Output | R-OUT-1 | dont_care | The return value is unspecified. The readings include the usual `[number + min(need, remaining), max(remaining - need, 0)]`, which I recorded as one reading, not a requirement. |
| Frame | R-FR-1 | guarantee | F-EMPTY: `result` is the empty list unless `outcome` is 0 |

**Possible contradiction:** if `remaining` means the carrots in stock, the rabbit can't "complete the day's meals" when `remaining < need`. I recorded this as an ambiguity on both R-DEF-3 and R-EAT-2. One reading treats it as a real contradiction; the other says `remaining` doesn't limit what the rabbit eats.

Every ambiguity phrase is a verbatim substring of its requirement's quote, and phrases are unique within each requirement.