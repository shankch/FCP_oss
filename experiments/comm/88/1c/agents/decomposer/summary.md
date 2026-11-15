I wrote `requirements_draft.yaml` with 13 requirements and ran `fcp anchor` on it. All 13 quotes were accepted on the first run (`anchored 13 requirements`), and `requirements.yaml` now has their line numbers.

**Requirements**
- **R-IF-1** (non_functional): the code defines a Python function `sort_array(array)`.
- **R-IN-1** (assumption): every element of `array` is a non-negative integer.
- **R-RES-1 / R-RES-2** (guarantee): the call returns a list, and that list has exactly the input's elements, each as many times as in the input.
- **R-DEF-1** (definition): the sum is `array[0] + array[len-1]`.
- **R-ORD-1 / R-ORD-2** (guarantee): an odd sum gives ascending order, an even sum gives descending order.
- **R-MUT-1** (guarantee): the argument list is left unchanged.
- **R-EX-1..4** (scenario): the four examples.
- **R-FR-1** (FRAME, guarantee): rule F-EMPTY, which `design.yaml` already links to this ID.

**Contradictions** (each is recorded as an ambiguity on both requirements involved)
1. **The order rule and the examples disagree.** In `[2,4,3,0,1,5]` the first and last values sum to 7, which is odd, but the expected result is descending. In `[2,4,3,0,1,5,6]` they sum to 8, which is even, but the expected result is ascending. The same conflict appears if "first/last index value" means the indices (5 and 6). The examples only fit if odd and even are swapped. This is recorded on R-ORD-1 with R-EX-3, and on R-ORD-2 with R-EX-4.
2. **Sorting the argument vs. leaving it alone.** "You will sort the given array", "sort it" and "a copy of the given array after sorting" can be read as sorting the argument in place, which conflicts with "don't change the given array". This is recorded on R-ORD-1, R-ORD-2, R-RES-2 and R-MUT-1.

**Other ambiguities**
- "first index value" can mean the value at index 0 or the index 0 itself.
- For a one-element array, the single element may count once or twice in the sum. Both orders give the same result.
- For an empty array, the sum may be undefined or taken as 0. Both orders give the same result.
- "ascending" and "descending" can mean strict or non-strict order when there are duplicates.
- "a copy" may or may not require a new list object rather than the argument itself.