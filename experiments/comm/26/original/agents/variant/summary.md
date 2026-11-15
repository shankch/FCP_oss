I wrote `formal/variant.yaml` and it passes lint with no errors. Reading back `fcp explain` shows every item means what I intended. I did not run any of the consistency analyses.

**Items: 7** (6 properties and 1 scenario), plus the frame rule F-EMPTY, which is added automatically.
- **RV-SIG-1** (R-SIG-1, read as removing duplicates): a returned list is exactly the first occurrences of `numbers`, in order.
- **RV-SIG-2** (R-SIG-2, read as allowing exceptions): `outcome != 2`. This is a little stronger than the annotation on its own, because outcome 2 also covers a returned list of integers that is too long or has values outside 0–255. The note says so.
- **RV-RM-1**: each value that occurs more than once is kept exactly once. The in-place reading of "From a list of integers, remove" can't be seen in the trace: it only records the argument as passed and the contents of the returned list, so that reading adds no constraint. The note says so.
- **RV-RM-2**: each value that occurs exactly once is in the result.
- **RV-RM-3**: no value appears in the result more often than it does in `numbers`.
- **RV-ORD-1** (positions reading, first occurrence kept): every first occurrence at index i is at index i of the result.
- **RV-EX-1**: a scenario in which `remove_duplicates([1, 2, 3, 2, 4])` returns `[1, 2, 3, 4]`, per the reading you gave for that example.

Every property about the result applies only when the call returns (`outcome == 0`), because of the reading you gave for R-SIG-2. Each item's note names the readings you imposed that affect it, and all 7 flagged phrases are recorded under `decisions` as reading 2.

**Left unformalized (3):**
- **R-TASK-1**: a non-functional deliverable. The signature is fixed by `design.yaml`, and the behaviour is covered by the other items.
- **R-IN-1**: true by construction, since `numbers` is always a list of at most 8 integers from 0 to 255 and frame.md excludes any other call.
- **R-FR-1**: it is frame rule F-EMPTY, which frame.md says need not be restated.

**Problems in the specification:**
1. **Name against docstring.** The name `remove_duplicates` means "keep each value once", but the docstring sentence and the example `[1, 3, 4]` mean "drop every value that repeats". The requirement text written for R-RM-1 follows the docstring, which is the opposite of the reading I was told to use.
2. **The readings you gave contradict each other.** Keeping original positions (R-ORD-1) can't be combined with deleting elements: whenever a deleted element comes before a kept one, the kept one has to move. Together with RV-SIG-1, a returned list is only possible when all repeats come after every first occurrence. For inputs like `[1, 1, 2]` or `[1, 2, 3, 2, 4]`, the set leaves raising as the only allowed outcome. So the RV-EX-1 scenario can never happen alongside RV-ORD-1, and the same goes for the `[1, 2, 3, 4]` example in the R-SIG-1 reading. I left this visible rather than fixing it, so FCP's consistency checks should report it.
3. **No contract for raising.** The prompt never says when the function may raise. Under the R-SIG-2 reading, a function that always raises meets every property. Only the scenario would rule it out, and the scenario can't be reached anyway, as point 2 explains.