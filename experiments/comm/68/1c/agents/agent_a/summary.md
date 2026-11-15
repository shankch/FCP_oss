Lint is clean and the English rendering reads as I intended. I'm writing up the summary now.

## Summary

I wrote `formal/agent_a.yaml`. `fcp lint` reports no errors (`lint: clean`), and I read every item back with `fcp explain` to check it says what I meant.

**15 formal items:**
- **4 assumptions:** RA-IN-1 to RA-IN-4.
- **7 properties:** RA-PL-1/2/3, RA-OUT-1/2, RA-EMP-1/2.
- **4 scenarios:** RA-EX-1 to RA-EX-4, one per example as written.
- **3 helper definitions:** `has_even`, `min_even_pos` and `min_even`. There is no ghost state.
- **15 decisions** are recorded, all reading 1. That is the literal reading of each sentence on its own.

**2 requirements are not formalized:**
- **R-FR-1** is the frame rule `F-EMPTY`, which is added to every set automatically (`covered_by: [F-EMPTY]`).
- **R-DEF-1** is a definition, not a behaviour: arr is a flat list, and a node's index is its 0-based position. The items that rely on it are listed under `covered_by`.

**Problems in the specification.** Following the rule not to repair the spec, I formalized each sentence as written and noted each contradiction on the items involved. As a result, **the set contradicts itself**, and FCP's consistency check should report these conflicts:
1. **Examples 1, 2 and 4 contradict the rules.** In each one the output is the largest element and its index ([4,0], [3,2], [5,0]). The rules give [2,1], [2,1] and [0,1]. In Example 2 the value returned, 3, isn't even. So RA-EX-1, 2 and 4 conflict with RA-PL-2 and RA-OUT-1, and RA-EX-4 also conflicts with the tie-break rule RA-PL-3. Any implementation will fail either the rules or the examples.
2. **The constraint `1 <= nodes.length` excludes the empty array**, but the text says "or the given array is empty, return []" and Example 3 shows `[] -> []`. With assumption RA-IN-2 in place, RA-EMP-2 can never trigger and RA-EX-3 can never happen. If the checker stops checking after a call that breaks an assumption, an empty-array call could also hide failures in later calls.
3. **Smaller issues:**
   - The Constraints line names `nodes`, not the argument `arr`.
   - The output format has a typo: "smalest_value".
   - "pluck" could mean removing the node from arr. The trace can't see changes to the argument, so this isn't constrained.
   - RA-IN-1, RA-IN-3 and RA-IN-4 always hold, because the input only carries 0 to 16 elements valued 0 to 255. I kept them only so the obligations are written down.