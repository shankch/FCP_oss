The formalization set is written, `fcp lint` reports clean, and I read through the `fcp explain` output: every item says what I meant it to.

**File:** `formal/agent_a.yaml`. It has 13 items: 8 properties and 4 scenarios that I wrote, plus the frame rule F-EMPTY, which the adapter adds to every set. It also has 5 named expressions, no assumptions and no ghost state.

- **RA-RES-1:** every call returns a list (`outcome == 0`).
- **RA-RES-2:** a returned list has the argument's length and the same elements, each the same number of times.
- **RA-ORD-1 / RA-ORD-2:** if the first element plus the last element is odd, the result is non-decreasing; if even, non-increasing. Neither rule applies to an empty array.
- **RA-EX-1…4:** each example is stated as a property, plus a matching scenario saying the call must be possible.
- All 14 flagged ambiguous phrases have an entry under `decisions`.

**Left unformalized (5):**
- **R-IF-1:** the function name and its one parameter are fixed by the adapter; they aren't something a trace can show.
- **R-IN-1:** holds automatically. Elements are encoded as unsigned 0–255, and calls with negative elements are left out of the trace.
- **R-DEF-1:** a definition. It is built into the parity-sum expression and used by RA-ORD-1 and RA-ORD-2 (`covered_by`).
- **R-MUT-1** ("don't change the given array"): can't be checked. The trace has no signal for the argument after the call, so changing it in place would go undetected.
- **R-FR-1:** this is the frame rule F-EMPTY, which every set already includes (`covered_by: [F-EMPTY]`).

**Problems in the specification:**
1. **Both non-trivial examples contradict the rule.** In `[2,4,3,0,1,5]`, 2 + 5 = 7 is odd, so the rule says ascending, but the example shows descending. In `[2,4,3,0,1,5,6]`, 2 + 6 = 8 is even, so the rule says descending, but the example shows ascending. This is true whether "first index value" means the values or the index positions. I treated the stated rule as correct and the examples as wrong (reading 2 for R-EX-3 and R-EX-4). So RA-EX-3 and RA-EX-4 require `[0,1,2,3,4,5]` and `[6,5,4,3,2,1,0]`, not the printed results. Each item's note says this. Note that the two examples agree with each other: both fit the rule with odd and even swapped, which is the other possible reading.
2. **"Sort the given array" / "sort it" conflict with "don't change the given array".** I took the reading that a copy is sorted. The trace can't tell the difference either way.
3. **"A copy" vs. returning the same list object** can't be told apart in the trace. I took the "new object" reading, but only the list's contents are constrained.
4. **"Sum of first and last index value"** is unclear for one-element and empty arrays. I counted a single element twice, and gave the empty array no sum, so neither order rule applies to it. This doesn't change any required behaviour: a one- or zero-element result is in order either way, and RA-RES-2 and RA-EX-1 already force `[]` for an empty argument.