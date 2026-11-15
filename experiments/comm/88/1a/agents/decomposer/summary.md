I broke spec.md into 13 requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted all 13 quotes on the first run, so no fixes were needed, and it wrote `requirements.yaml` with line numbers filled in.

**The requirements:**
- **R-FR-1 (FRAME):** the frame rule F-EMPTY: `result` is the empty list unless `outcome` is 0. I used this id because `design.yaml` already points to it.
- **R-API-1** (non_functional): the code must be a Python function `sort_array(array)`.
- **R-IN-1** (assumption): the input is a list of non-negative integers.
- **R-RET-1** (guarantee): every valid call returns a list normally (`outcome` 0).
- **R-RET-2** (guarantee): the returned list has exactly the input's elements, in some order.
- **R-DEF-1** (definition): the "sum of first and last" value whose odd/even result picks the sort order.
- **R-ORD-1** (guarantee): odd sum → ascending.
- **R-ORD-2** (guarantee): even sum → descending.
- **R-MUT-1** (guarantee): the input list is not changed.
- **R-EX-1 to R-EX-4** (scenarios): the four examples in the docstring.

**Ambiguities flagged:**
- **"is odd or even" / "is even or odd":** I gave three readings: only odd (or only even), literally always, or swapped. Read literally, both order rules apply to every array, so R-ORD-1 and R-ORD-2 contradict each other. I recorded that on both.
- **"first index value, last index value":** it could mean the values `array[0] + array[-1]` or the index numbers themselves (`len-1`).
- **Sum taken on which list:** the input as passed, or the sorted list (where it's always min + max).
- **"ascending" / "descending":** duplicates kept, or strictly increasing/decreasing. The strict reading conflicts with returning a copy of the same elements.

Both examples with more than one element fit all three readings of the sum, so the examples can't tell them apart.

**Contradictions, each recorded on both requirements:**
- "you will sort the given array" (R-ORD-1), "sort it" (R-ORD-2) and "a copy … after sorting" (R-RET-2) can all be read as sorting the input in place. That clashes with R-MUT-1, "don't change the given array".
- Example R-EX-4 (sum 8, descending) contradicts R-ORD-1 read literally.
- Example R-EX-3 (sum 7, ascending) contradicts R-ORD-2 read literally.

R-MUT-1 is kept as a guarantee, but the trace can't check it: the frame says the trace records the input as passed, and the frame says nothing else about the call is recorded, so a changed input never shows up.