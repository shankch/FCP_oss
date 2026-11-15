I wrote `formal/variant.yaml` (set `variant`). Lint reports no errors, and the English rendering from `fcp explain` matches what I intended for every item. I did not run the consistency or code checks.

**Items: 10** (6 properties, 4 scenarios). There are no assumptions or don't-cares. The `decisions` list has 12 entries: the 10 readings you gave, plus reading 1 for the two example phrases in R-EX-3 and R-EX-4.
- **R-RET-1:** every call returns a list normally (outcome 0).
- **R-RET-2:** the result is a rearrangement of the argument: same length, and each value appears as often as in the argument.
- **R-ORD-1 and R-ORD-2:** two items each, for strictly ascending and strictly descending order. Each pair has one item that uses len(array) − 1 as the sum and one that uses min(array) + max(array).
- **R-EX-1 to R-EX-4:** one scenario per example.

Every affected item's note says that its reading was taken as you instructed.

**Requirements left unformalized (5):**
- **R-FR-1:** already stated by the frame rule F-EMPTY.
- **R-API-1:** the function name and signature come from `design.yaml`, not the trace. A function the adapter can't call ends with outcome 1, which the R-RET-1 property rejects.
- **R-IN-1:** the encoding already guarantees it, since the trace only carries lists of integers from 0 to 255. An assumption would constrain nothing.
- **R-DEF-1:** it is a definition, so I wrote it as named expressions used by the four order items.
- **R-MUT-1:** it can't be observed. The trace records only the argument as passed and the returned list, so whether the call changes the argument is invisible. Under your readings the call does change it, so this requirement contradicts R-ORD-1, R-ORD-2 and R-RET-2.

**Problems in the specification and the given readings:**
1. **The two readings you gave for R-DEF-1 contradict each other.** One makes the sum len(array) − 1, the other min(array) + max(array). I didn't choose between them, so each order rule has a version for each sum. As a result the set allows no valid output when the two sums differ in parity: [0, 2] must be both ascending and descending, and so must [0, 1, 3].
2. **"Strictly increasing/decreasing" contradicts R-RET-2.** Duplicates would have to be removed, but R-RET-2 keeps every element. No output satisfies both for an array of length 2 or more with a repeated value. I left this as is, as the readings themselves note.
3. **The in-place sorting readings contradict "don't change the given array".** The trace can't show this conflict, because it records only the argument as passed.
4. **The spec text itself says "odd or even" and "even or odd".** I read these as odd only and even only, as you gave. All four examples are consistent with the rest of the set under these readings.