I've split spec.md into 14 atomic requirements and anchored them. `fcp anchor` accepted every quote on the first run, and the result is in `requirements.yaml`.

**What's in it**
- **Interface (2, non_functional):** R-IF-1 says the function must be fully implemented. R-IF-2 fixes the signature `sort_array(array)`.
- **Assumption (1):** R-IN-1 says the argument is a list of non-negative integers.
- **Return (3, guarantee):** the function returns a list rather than raising or hanging (R-RET-1). The result has the same elements, each as often, as the input (R-RET-2). The result is a new list object (R-RET-3).
- **Order (2, guarantee):** if the first and last values add up to an odd number, sort ascending (R-ORD-1). If they add up to an even number, sort descending (R-ORD-2).
- **No change (1, guarantee):** R-NC-1 says the list passed in must not be modified.
- **Scenarios (4):** R-EX-1 to R-EX-4, one for each example in the spec.
- **Frame (1):** R-FR-1 is the F-EMPTY rule from frame.md (the frame section of design.yaml points to R-FR-1).

**Ambiguities flagged**
- **"sum( first index value, last index value)":** it could mean the values at the two ends, `array[0] + array[-1]`, or the index numbers themselves, `0 + (len-1)`. Both examples give the same answer under either reading, so they don't settle it. Flagged on both ORD requirements.
- **"ascending" / "descending":** it could mean allowing equal neighbours or strictly increasing/decreasing. The strict reading can't hold together with R-RET-2 when the input has repeated values.
- **Empty array:** there are no first or last values to add up. Every reading still gives `[]`, which matches example 1.
- **"a copy":** it could mean a separate list object, or just the right values.

**Contradiction flagged:** "you will sort the given array" and "sort it" (R-ORD-1, R-ORD-2), plus "a copy of the given array after sorting" (R-RET-3), all read as sorting the input in place. That conflicts with "don't change the given array" (R-NC-1). I recorded it on all four requirements.

**For the formalizers:** two guarantees can't be checked from the trace as frame.md defines it. Whether the input list was modified (R-NC-1) and whether the result is a separate object (R-RET-3) are not recorded. They will probably need to go under `unformalized`.