# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 4.

## Questions
1. **depends** (R-CNT-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate([]) -> returned something else`
2. **ambiguity** (R-CNT-1): "the number of elements that need to be changed" can mean: The minimum number of single-element changes: one per mismatched mirror pair (arr[i] != arr[n-1-i], i < n-1-i). / The number of positions whose element differs from its mirror element, counting both elements of every mismatched pair (twice the minimum).. Which is meant?
3. **ambiguity** (R-CNT-1): "number of elements" can mean: The answer counts distinct elements (positions) that are modified. / The answer counts change operations as defined by 'In one change, you can change one element to any other element' (the two coincide for a minimal set of changes, but the text names elements here and changes there).. Which is meant?
4. **ambiguity** (R-CNT-2): "find" can mean: Return the number as the function's result. / Compute and output (e.g. print) the number; the return value is unspecified.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "an array arr of integers": both took "Any list of integers, including the empty list (which is trivially palindromic, so the answer is 0)."
- R-IN-1, "integers": both took "Any integers, including negative ones."
- R-CNT-1, "the number of elements that need to be changed": both took "The minimum number of single-element changes: one per mismatched mirror pair (arr[i] != arr[n-1-i], i < n-1-i)."
- R-CNT-1, "number of elements": both took "The answer counts distinct elements (positions) that are modified."
- R-CNT-2, "find": both took "Return the number as the function's result."
- R-DEF-1, "read the same backwards and forwards": both took "Element-wise: the sequence of elements reversed equals the original sequence."
- R-DEF-2, "any other element": both took "Any other integer value (not necessarily present in the array)."
- R-DEF-2, "In one change": both took "The answer counts elements, as stated in 'find the number of elements that need to be changed'; the unit of a change is only explanatory."
