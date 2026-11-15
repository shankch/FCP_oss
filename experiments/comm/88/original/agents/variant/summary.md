I wrote `formal/variant.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I intended for every item. Every reading you specified is reading 2 in requirements.yaml, so all 11 `decisions` entries record reading 2. Each item those readings affect explains the reading in its `note`, or in its `reason` if the requirement is unformalized.

**Items: 8 formal items, plus 6 requirements under `unformalized`.**
- **Properties (4):**
  - **RV-RET-1:** every call returns a list (`outcome == 0`).
  - **RV-RET-2:** when a list is returned, it has the same values as the input, each the same number of times.
  - **RV-ORD-1:** strictly increasing when the index sum is odd.
  - **RV-ORD-2:** strictly decreasing when the index sum is even.
  - The index sum is a helper, `idx_sum = len(array) == 0 ? 0 : len(array) - 1`. So the order depends only on whether the length is even or odd, and the empty array falls under the decreasing rule.
- **Scenarios (4):** RV-EX-1 to RV-EX-4, one for each example call and its return value.

**Unformalized requirements:**
- **R-IF-1:** not something a call can show. Its visible effect (every call returns a list) is covered by RV-RET-1.
- **R-IF-2:** the function name and its parameter are fixed by `design.yaml`.
- **R-IN-1:** always true in the trace. Inputs are unsigned 8-bit lists, and the frame leaves every other kind of input out.
- **R-RET-3:** under your reading of "a copy" (only the values matter), it doesn't require a separate list object. What's left is covered by RV-RET-2 and RV-ORD-1/2. The trace doesn't record object identity anyway.
- **R-NC-1:** the trace doesn't record what the input list holds after the call. Under your reading, R-ORD-1, R-ORD-2 and R-RET-3 also contradict it.
- **R-FR-1:** already covered by the frame rule F-EMPTY, which is part of every set.

**Problems in the specification under these readings:**
1. **The requirements contradict each other for inputs with repeated values.** Strict ordering (RV-ORD-1/2), "return a list" (RV-RET-1) and "same values" (RV-RET-2) can't all hold for an input like `[1, 1]`. I expect a consistency check to flag this, but I didn't run one.
2. **The in-place sorting readings contradict "don't change the given array".** The trace can't detect it, because it doesn't record the input after the call.
3. **Two readings disagree on the empty array.** By the index rule, 0 + (len − 1) gives −1, which is odd. The empty-array rule says to count the sum as 0, which is even. I let the empty-array rule decide, so `[]` gets the decreasing order. Either way it makes no difference, since an empty result is trivially in both orders.
4. **The examples can't tell the value reading from the index reading.** In all four examples the first-plus-last-value sum and the index sum are both odd or both even.