I split spec.md into 10 atomic requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`, with line numbers filled in by the tool.

**Requirements**
- **R-TASK-1** (non_functional): write the body of the given function and keep its signature.
- **R-SIG-1** (definition): the function is named `remove_duplicates` and takes one argument, `numbers`, a list of integers.
- **R-SIG-2** (guarantee): every call returns a list of integers (outcome 0).
- **R-IN-1** (assumption): `numbers` is a list of integers.
- **R-RM-1** (guarantee): no value that appears more than once in the input is in the result.
- **R-RM-2** (guarantee): every value that appears exactly once in the input is in the result.
- **R-RM-3** (guarantee): the result only removes things. No value appears in it more often than in the input, so nothing is added or copied.
- **R-ORD-1** (guarantee): the remaining elements keep their relative order from the input.
- **R-EX-1** (scenario): `remove_duplicates([1, 2, 3, 2, 4])` returns `[1, 3, 4]`.
- **R-FR-1** (FRAME, guarantee): F-EMPTY, i.e. `result` is empty unless `outcome` is 0.

**Ambiguities and contradictions**
- **Main contradiction:** the name `remove_duplicates` suggests keeping one copy of each value, which would give `[1, 2, 3, 4]`. The docstring sentence and the example both say every copy of a repeated value is removed, giving `[1, 3, 4]`. I recorded this on all three affected requirements: R-SIG-1, R-RM-1 and R-EX-1.
- **R-RM-1:** "remove" could mean returning a new list or deleting from `numbers` in place. The trace can't show the difference, because it only records the returned list.
- **R-ORD-1:** "keep order" could mean relative order or original positions. Under the keep-one-copy reading, it's also unclear whether a kept value is placed by its first or its last occurrence.
- **R-SIG-2:** the `-> List[int]` annotation could be a promise that the function never raises, or just a description of the return type when it does return.