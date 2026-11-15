I split spec.md into 8 requirements. `fcp anchor` accepted all 8 quotes on the first run, so `requirements_draft.yaml` and `requirements.yaml` are both written.

| ID | Kind | Obligation |
|---|---|---|
| R-NF-1 | non_functional | Write the body of `candidate` and keep its signature. |
| R-IO-1 | assumption | The argument `numbers` is a list of integers. |
| R-IO-2 | guarantee | Each call returns a list of integers: no exception, no hang, no other type. |
| R-FN-1 | guarantee | A value that occurs K times in the input does not appear in the output at all. |
| R-FN-2 | guarantee | Every other value appears in the output as many times as in the input; nothing is removed or added. |
| R-FN-3 | guarantee | The output keeps the input's relative order, so it is a subsequence of the input. |
| R-EX-1 | scenario | `candidate([1, 2, 3, 2, 4])` returns `[1, 3, 4]`. |
| R-FR-1 (FRAME) | guarantee | F-EMPTY: `result` is the empty list unless `outcome` is 0. |

**Ambiguities flagged:**
- **What K is (on R-FN-1 and R-FN-2):** the spec never defines it. It could be 2, "more than once" (as in the usual remove-duplicates task), or an undefined placeholder, possibly a missing second parameter.
- **"occur K time(s)" (on R-FN-1 and R-FN-2):** it could mean exactly K times or at least K times. The two readings differ only for values that occur more than K times.
- **Are the other elements kept? (on R-FN-2):** the text says what to remove but doesn't say outright that everything else stays. "Elements left" and the example imply it does.
- **In place or a new list? (on R-FN-1):** "remove" could mean returning a new list or deleting from the argument itself. The trace can't tell these apart, because it only sees the returned list.

**Contradiction (recorded on both R-FN-1 and R-EX-1):** the example only works if K = 2. The singular "time" allows K = 1, which would turn `[1, 2, 3, 2, 4]` into `[2, 2]`. Any K of 3 or more would remove nothing. The example doesn't settle "exactly" versus "at least" either.

I left out the adapter's input bounds (at most 8 elements, values 0 to 255) because they aren't a frame rule. The task asked for frame rules only from frame.md.