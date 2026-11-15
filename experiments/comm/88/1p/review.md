# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 11.

## Questions
1. **open** (result): the request allows [0, 6] or [6, 0]: which is meant?
   - `sort_array([6, 0])`
2. **open** (result): the request allows [1, 3] or [3, 1]: which is meant?
   - `sort_array([3, 1])`
3. **depends** (R-ORD-1, R-ORD-2, R-RET-1, R-RET-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `sort_array([1, 1, 2, 5, 3, 5, 6, 5]) -> [1, 1, 2, 3, 5, 5, 5, 6]`
4. **readings** (R-ORD-2): the two readings of this requirement disagree (no separating call was found within the budget): which is meant?
5. **ambiguity** (R-RET-1): "return a copy of the given array" can mean: The function returns for every list of non-negative integers, including the empty list, for which it returns an empty list. / The empty list is not covered, because the sum of its first and last index values is undefined; the function may raise (for example an IndexError) or return anything on it.. Which is meant?
6. **ambiguity** (R-RET-3): "after sorting" can mean: The returned list is always sorted in one of the two directions, whatever the sum of the first and last index values is. / Only the cases the condition names constrain the order; where the text is cut off (after "or sort it") the order of the returned list is unconstrained.. Which is meant?
7. **ambiguity** (R-RET-4): "a copy of the given array after sorting" can mean: A copy of the given array is made and the copy is sorted and returned; the given array is left unchanged. / The given array is sorted (in place) and then a copy of it is returned; the given array is modified. This is what "you will sort the given array" says, which contradicts leaving it unchanged.. Which is meant?
8. **ambiguity** (R-RET-5): "a copy" can mean: The returned list must be a different object from the argument, even when the argument is already in the required order (or is empty or has one element). / Only the contents of the returned list matter; returning the argument object itself is acceptable as long as it holds the required elements.. Which is meant?
9. **ambiguity** (R-ORD-1): "ascending order" can mean: Non-decreasing order, keeping duplicate values (each element appears as often as in the given array). / Strictly increasing order, so duplicate values are removed; this contradicts returning a copy of the given array.. Which is meant?
10. **ambiguity** (R-ORD-1): "you will sort the given array" can mean: A sorted copy is produced and returned; the given array is left unchanged, as "return a copy of the given array" says. / The given array itself is sorted in place (and a copy of it returned); this contradicts leaving the given array unchanged.. Which is meant?
11. **ambiguity** (R-ORD-2): "or sort it" can mean: When the sum is even, the returned list is in descending (non-increasing) order, the usual counterpart of the ascending case. / When the sum is even, the returned list may be in either order: the direction is unspecified and any sorted permutation is acceptable. / When the sum is even, the returned list is in ascending order as well, the same as when the sum is odd. / The sentence is incomplete: neither the condition nor the order of this case is stated, so the order of the returned list is unconstrained when the sum is even.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "an array of non-negative integers": both took "Any such list is a valid argument, including the empty list."
- R-RET-1, "return a copy of the given array": both took "The function returns for every list of non-negative integers, including the empty list, for which it returns an empty list."
- R-RET-3, "after sorting": both took "The returned list is always sorted in one of the two directions, whatever the sum of the first and last index values is."
- R-RET-5, "a copy": both took "The returned list must be a different object from the argument, even when the argument is already in the required order (or is empty or has one element)."
- R-KEY-1, "first index value, last index value": both took "The values stored at the first and last positions of the array: array[0] + array[len(array) - 1]."
- R-KEY-1, "the sum( first index value, last index value)": both took "The first and last elements of the given array as passed in, before sorting."
- R-KEY-1, "last index value": both took "For a one-element array the first and last index values are the same element counted twice, so the sum is twice that element and always even."
- R-ORD-1, "ascending order": both took "Non-decreasing order, keeping duplicate values (each element appears as often as in the given array)."
- R-ORD-2, "or sort it": both took "When the sum is even, the returned list may be in either order: the direction is unspecified and any sorted permutation is acceptable."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_b, RB-IN-1 (R-IN-1): every call meets `all(i < len(array): array[i] >= 0)`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the comparison of agent_a and agent_b
