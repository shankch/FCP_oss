I've written `formal/agent_a.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I meant for each item.

**Items (9):** 1 assumption (RA-IN-1), 4 properties (RA-RET-1, RA-RET-2, RA-ORD-1, RA-ORD-2) and 4 scenarios (RA-EX-1 to RA-EX-4, one per docstring example). All the flagged ambiguous phrases (12) are recorded under `decisions`.

**Requirements left unformalized (4):**
- **R-FR-1:** this is the adapter's frame rule. The design file already adds it to every set as F-EMPTY, so I listed it with `covered_by: [F-EMPTY]`.
- **R-API-1:** a naming and signature requirement. The function section of `design.yaml` fixes it, and it can't be expressed as a property of the trace.
- **R-DEF-1:** a definition. It is carried by the `psum` definition, which the two ordering properties use (`covered_by`).
- **R-MUT-1 ("don't change the given array"):** can't be checked. The trace records only the argument as passed and the returned list, so whether the call changes the caller's list never appears in it.

**Problems in the specification:**
1. **The sort-order rule contradicts itself.** "Ascending if the sum is odd or even" and "descending if the sum is even or odd" have conditions that are always true. Following the rules, I took the most literal reading (reading 2 for both phrases). RA-ORD-1 therefore requires every non-empty array to come back ascending, and RA-ORD-2 requires it to come back descending.
   - Together with RA-RET-2 (the result is a permutation of the input), no behaviour satisfies both for any array with two distinct values.
   - RA-EX-3 (ascending) conflicts with RA-ORD-2, and RA-EX-4 (descending) conflicts with RA-ORD-1. FCP's consistency check should flag both scenarios as unreachable.
   - The `text` fields in requirements.yaml quietly fix this to "odd → ascending, even → descending", which is what the examples show. I didn't adopt that fix, and the notes on those items say so.
2. **Some phrases conflict with "don't change the given array".** "You will sort the given array" and "sort it" could mean sorting the argument in place. I took reading 1, which sorts a copy. Neither reading changes any property, because the trace can't show the argument after the call.
3. **"First index value, last index value" is ambiguous.** It could mean the values stored at those positions or the index numbers themselves. I took the values of the array as passed (reading 1 for both phrases). Under my literal reading of the order rules the parity no longer matters, so this choice doesn't change any property.