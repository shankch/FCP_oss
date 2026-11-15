I wrote `requirements_draft.yaml` with 12 requirements, and `fcp anchor` accepted every quote on the first run, so `requirements.yaml` is written with line numbers.

**What's in it:**
- **Interface (R-IF-1, R-IF-2):** two non-functional requirements: complete the stub, and keep the signature `sort_array(array)`.
- **Input (R-IN-1):** one assumption: the argument is a list of non-negative integers.
- **Return value (R-RET-1 to 5):**
  - the call returns a list without raising
  - the list has the same elements as the input, in some order
  - the list is sorted in one direction or the other
  - the argument is not modified
  - the returned list is a new object
- **Sort order:** R-KEY-1 defines the deciding sum as first element plus last element. R-ORD-1 says the result is ascending when that sum is odd. R-ORD-2 covers the even case.
- **Frame (R-FR-1):** the one frame rule, F-EMPTY.
- **Scenarios:** none, because the prompt gives no examples.

**Problems in the prompt:**
- **The prompt is cut off.** It ends at "or sort it", so the even-sum case never states a direction. I didn't assume descending. R-ORD-2 lists four readings: descending, either direction, ascending, or no constraint. R-RET-3 also flags whether the result must be sorted at all in that case.
- **Contradiction:** "return a copy of the given array" conflicts with "you will sort the given array", which suggests sorting in place. I recorded it on both R-RET-4 and R-ORD-1.
- **Other ambiguities flagged:**
  - "first index value, last index value" could mean the element values or the index numbers. The second reading makes the direction depend only on the length.
  - The sum could come from the array before sorting or after sorting (minimum plus maximum).
  - For a one-element array, the element may be counted once or twice.
  - An empty array has no first or last element, so it's unclear whether it's a valid input.
  - "Ascending" could mean non-decreasing or strictly increasing, which would drop duplicates.
  - "A copy" may or may not require a new object.

R-RET-4 (input not modified) and R-RET-5 (new object) can't be seen in the trace, because the argument is an input signal. The formalizers will probably have to list them as unformalized.