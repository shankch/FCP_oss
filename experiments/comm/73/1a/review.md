# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 6.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-3: candidate([1, 2, 3, 2, 1]) returns 0, since the array is already palindromic.

## Questions
1. **depends** (R-CH-1, R-DEF-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate([4, 100, 0, 101, 201, 10, 0, 100, 200, 13]) -> 5`
2. **ambiguity** (R-CH-1): "the number of elements that need to be changed" can mean: the minimum number of single-element changes that make arr palindromic, i.e. the number of mirrored index pairs (i, len(arr)-1-i) with i < len(arr)-1-i whose two elements differ / the number of elements that differ from their mirrored element, i.e. both elements of every differing pair are counted (twice the number of differing pairs); this reading contradicts R-EX-1 (8, not 4) and R-EX-2 (2, not 1) / any number of changes that suffices to make arr palindromic, not necessarily the smallest. Which is meant?
3. **ambiguity** (R-CH-1): "to make the array palindromic" can mean: the function only computes and returns the count; arr itself is left as it was / the function also turns arr into a palindrome (in place) and returns how many elements it changed. Which is meant?
4. **ambiguity** (R-CH-2): "find the number" can mean: return the number as the function's integer result / output (e.g. print) the number; the return value is unspecified. Which is meant?
5. **ambiguity** (R-EX-1): "== 4" can mean: consistent with R-CH-1 read as the minimum number of changes: all 4 mirrored pairs (1,6), (2,9), (3,7), (5,4) differ / contradicts R-CH-1 read as counting every element that differs from its mirror, which gives 8. Which is meant?
6. **ambiguity** (R-EX-2): "== 1" can mean: consistent with R-CH-1 read as the minimum number of changes: only the pair (1,2) differs; the middle element 4 has no mirror / contradicts R-CH-1 read as counting every element that differs from its mirror, which gives 2. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "an array arr of integers": both took "arr may be empty; the empty array reads the same backwards and forwards, so the answer for it is 0"
- R-CH-1, "the number of elements that need to be changed": both took "the minimum number of single-element changes that make arr palindromic, i.e. the number of mirrored index pairs (i, len(arr)-1-i) with i < len(arr)-1-i whose two elements differ"
- R-CH-1, "to make the array palindromic": both took "the function only computes and returns the count; arr itself is left as it was"
- R-CH-2, "find the number": both took "return the number as the function's integer result"
- R-DEF-1, "read the same backwards and forwards": both took "element-wise: the sequence of elements equals its reverse (e.g. [12, 21] is not palindromic)"
- R-DEF-2, "any other element": both took "only the value of another element already present in the array"
- R-DEF-2, "In one change, you can change one element": both took "a change must give the element a value different from its current one"
- R-EX-1, "== 4": both took "consistent with R-CH-1 read as the minimum number of changes: all 4 mirrored pairs (1,6), (2,9), (3,7), (5,4) differ"
- R-EX-2, "== 1": both took "consistent with R-CH-1 read as the minimum number of changes: only the pair (1,2) differs; the middle element 4 has no mirror"
