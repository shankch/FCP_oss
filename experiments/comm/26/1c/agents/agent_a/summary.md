Lint and explain both pass. The optional `fcp check` run needed approval, so I skipped it; the task only asked for lint and explain. Here is the summary.

## Summary

I wrote `formal/agent_a.yaml`. `fcp lint` reports clean, and the `fcp explain` output matches what I intended for every item.

**8 items:**
- **Properties (6):** `RA-IF-3` says every call returns a list (`outcome == 0`). `RA-RM-1`, `RA-RM-2`, `RA-RM-3-VAL`, `RA-RM-3-LEN` and `RA-ORD-1` constrain the returned list, and each applies only when the call returned. They compare values in `numbers` and `result` directly, with no extra model state.
- **Scenario (1):** `RA-EX-1` is the docstring example, written exactly as given.
- **Frame item (1):** `F-EMPTY` is added automatically from `design.yaml` and counts as the item for R-FR-1.

**Requirements left unformalized (5), each with a reason:**
- **R-FR-1:** already present as the frame item `F-EMPTY`; `frame.md` says not to restate it.
- **R-IF-1** ("Complete this function"): a statement about the deliverable, not about any call. The part you can observe is covered by `RA-IF-3`.
- **R-IF-2** (function name and signature): fixed by `design.yaml`. A wrong name or signature makes every call fail, which `RA-IF-3` forbids.
- **R-IN-1** (the argument is a list of integers): the interface encoding already guarantees this, so an assumption would say nothing.
- **R-DEF-1** (what "occurs more than once" means): a definition. It is written inline as an element count in `RA-RM-1`, `RA-RM-2` and `RA-ORD-1`.

**Readings chosen for the ambiguous phrases:**
| Requirement | Reading | Meaning |
|---|---|---|
| R-IF-3 | 1 | must return a list on every input |
| R-DEF-1 | 1 | repeats count anywhere in the list, not just adjacent ones |
| R-RM-1 | 1 | remove every copy of a repeated value |
| R-RM-3 | 2 | remove in place; the trace can't tell this from building a new list |
| R-ORD-1 | 3 | order is fixed only for values that appear once |
| R-EX-1 | 2 | the example contradicts the text |

**Problems in the specification:**
1. **The text and the example contradict each other.** "Remove all elements that occur more than once", read literally, turns `[1, 2, 3, 2, 4]` into `[1, 3, 4]`. The doctest says `[1, 2, 3, 4]`. I formalized both as written and repaired neither. Together, `RA-RM-1` and `RA-EX-1` should come out as a conflicting set, so the example scenario should be unreachable. I couldn't confirm that because the `fcp check` run didn't happen. Only the spec owner can say which one is meant; the function name and the example suggest removing just the extra copies.
2. **Outcome 2 mixes two cases.** It covers both "returned another type" and "returned a list of integers that doesn't fit". That makes `outcome == 0` slightly stronger than R-IF-3 taken alone. Any list that doesn't fit would break R-RM-3 anyway, so this rules out nothing the spec allows (explained in the item's note).
3. **The text doesn't say where a repeated value goes if it is kept.** This only matters if the example's reading wins. Under the literal reading no repeated value is kept, so the order is fully determined.