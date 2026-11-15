I wrote `formal/variant.yaml`. `fcp lint` reports `lint: clean`, and I read the `fcp explain` output back: every item says what I meant. But the readings you gave contradict each other in two places, so I had to pick one over the other. I also expect the set to fail its consistency check on some inputs (point 3).

**Items: 7 formal items, plus 7 `unformalized` entries and 11 `decisions`**
- **Assumption** RV-IN-1: the list is non-empty.
- **Properties:**
  - RV-RET-1: every non-empty list gets a returned list.
  - RV-RET-2: the returned list holds exactly the argument's elements, each as often (contents only).
  - RV-ORD-1: if the sum is odd, the result is the distinct values in strictly increasing order.
  - RV-ORD-2: if the sum is even, the result is in non-increasing order.
- **Don't-cares** RV-RET-1-D1 and RV-RET-1-D2: the outcome and the returned list are unconstrained for the empty list.
- **The sum** is computed by named expressions (`lo`, `hi`, `key`): the array's minimum plus its maximum, or the single element for a one-element list.

**Requirements left unformalized**
- **R-IF-1, R-IF-2:** these are about the response and the function signature, not about a call. A missing body, a missing function or the wrong number of parameters still fails RV-RET-1.
- **R-RET-3:** with the reading you gave, "after sorting" adds no order rule of its own. Its order is set by RV-ORD-1 and RV-ORD-2 (`covered_by`).
- **R-RET-4:** the trace doesn't record the argument after the call. The literal text ("you will sort the given array") also says the argument *is* sorted, which contradicts this requirement.
- **R-RET-5:** with the reading you gave, only the contents matter, and object identity isn't visible in the trace anyway (`covered_by` RV-RET-2).
- **R-KEY-1:** it is a definition. It is realised by the named expressions used in RV-ORD-1 and RV-ORD-2 (`covered_by`).
- **R-FR-1:** it is the frame rule F-EMPTY, which is already part of every set (`covered_by` F-EMPTY).

**Problems**
1. **Your three R-KEY-1 readings can't all hold.** "Index numbers, 0 + (len − 1)" sums positions. "Minimum plus maximum" and "single element counted once" sum element values. I followed the reading for the whole quoted phrase (min + max), refined by the one-element reading, because two of the three readings sum values. Under the index-number reading, the odd case would be "the length is even".
   - The one-element reading changes nothing you can observe: a one-element list is sorted in both directions.
   - Every affected item's note records this.
2. **R-RET-3 reading vs R-ORD-2 reading.** Your R-RET-3 reading leaves the order unconstrained where the text breaks off. Your R-ORD-2 reading requires descending order when the sum is even. I let the R-ORD-2 reading decide that case.
3. **Strictly increasing vs "a copy".** Your strict reading of "ascending order" conflicts with RV-RET-2 whenever the sum is odd and a value repeats (for example `[2,2,1]`). I left the contradiction in rather than repairing it, so FCP's consistency check should flag it.
4. **Two phrases you didn't assign.** For "a copy of the given array after sorting" and "you will sort the given array" I chose reading 2, the literal one: the argument itself is sorted. Neither choice changes any item, because the trace can't see the argument after the call.
5. **The spec itself** is cut off after "or sort it": it never states the order when the sum is even. "First index value" is also ambiguous between positions and the values stored there.