# FCP review

Before any code: the request alone.

Settled: 6 requirements. Questions: 11.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RET-1: For every argument that is a list of non-negative integers, sort_array returns a list (it does not raise an exception and does finish).
- R-RET-2: The returned list is a rearrangement of the given array: it has the same length and contains every value exactly as many times as the given array does.
- R-EX-1: Called with the empty list, sort_array returns the empty list.
- R-EX-2: Called with [5], sort_array returns [5].
- R-EX-3: Called with [2, 4, 3, 0, 1, 5] (first plus last value 2 + 5 = 7, odd), sort_array returns [0, 1, 2, 3, 4, 5].
- R-EX-4: Called with [2, 4, 3, 0, 1, 5, 6] (first plus last value 2 + 6 = 8, even), sort_array returns [6, 5, 4, 3, 2, 1, 0].

## Questions
1. **depends** (R-ORD-1, R-ORD-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `sort_array([1, 1, 7, 1, 1, 6, 1, 1]) -> [7, 6, 1, 1, 1, 1, 1, 1]`
2. **ambiguity** (R-RET-3): "a copy of the given array after sorting" can mean: a new list holding the elements of the given array in sorted order; the given array itself is left as it was / the given array is sorted (in place) and then a copy of it is returned; this contradicts "don't change the given array" (R-NC-1). Which is meant?
3. **ambiguity** (R-RET-3): "a copy" can mean: a distinct list object, so the caller can modify the result without affecting the given array / only the values matter; returning the given list object itself is acceptable when its order already matches. Which is meant?
4. **ambiguity** (R-ORD-1, R-ORD-2): "first index value, last index value" can mean: the values stored at the first and the last index: array[0] + array[len(array) - 1] / the first and the last index numbers themselves: 0 + (len(array) - 1), i.e. the parity of len(array) - 1 (the examples agree with both readings). Which is meant?
5. **ambiguity** (R-ORD-1): "ascending order" can mean: non-decreasing order, equal values kept: result[i] <= result[i + 1] / strictly increasing order: result[i] < result[i + 1] (impossible together with R-RET-2 when the array has repeated values). Which is meant?
6. **ambiguity** (R-ORD-1): "you will sort the given array" can mean: the values of the given array are sorted into the returned copy; the given array itself is not modified / the given list itself is sorted in place; this contradicts "don't change the given array" (R-NC-1). Which is meant?
7. **ambiguity** (R-ORD-1): "the sum( first index value, last index value) is odd" can mean: the condition is defined only for a non-empty array; the empty array falls under neither order rule / for the empty array the sum is taken over the missing values as 0 (even), so the descending rule applies instead. Which is meant?
8. **ambiguity** (R-ORD-2): "descending order" can mean: non-increasing order, equal values kept: result[i] >= result[i + 1] / strictly decreasing order: result[i] > result[i + 1] (impossible together with R-RET-2 when the array has repeated values). Which is meant?
9. **ambiguity** (R-ORD-2): "sort it" can mean: "it" is the copy to be returned; the values of the given array are sorted into the returned list and the given array is not modified / "it" is the given array, sorted in place; this contradicts "don't change the given array" (R-NC-1). Which is meant?
10. **ambiguity** (R-ORD-2): "the sum( first index value, last index value) is even" can mean: the condition is defined only for a non-empty array; the empty array falls under neither order rule / for the empty array the sum is taken over the missing values as 0, which is even, so this descending rule applies. Which is meant?
11. **ambiguity** (R-NC-1): "don't change the given array" can mean: the list passed as array keeps its elements and their order; only a copy is sorted / contradicted by "you will sort the given array" and "sort it" (R-ORD-1, R-ORD-2) and by "a copy of the given array after sorting" (R-RET-3), which read as sorting the given list itself. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RET-3, "a copy of the given array after sorting": both took "a new list holding the elements of the given array in sorted order; the given array itself is left as it was"
- R-RET-3, "a copy": both took "a distinct list object, so the caller can modify the result without affecting the given array"
- R-ORD-1, "first index value, last index value": both took "the values stored at the first and the last index: array[0] + array[len(array) - 1]"
- R-ORD-1, "ascending order": both took "non-decreasing order, equal values kept: result[i] <= result[i + 1]"
- R-ORD-1, "you will sort the given array": both took "the values of the given array are sorted into the returned copy; the given array itself is not modified"
- R-ORD-1, "the sum( first index value, last index value) is odd": both took "the condition is defined only for a non-empty array; the empty array falls under neither order rule"
- R-ORD-2, "first index value, last index value": both took "the values stored at the first and the last index: array[0] + array[len(array) - 1]"
- R-ORD-2, "descending order": both took "non-increasing order, equal values kept: result[i] >= result[i + 1]"
- R-ORD-2, "sort it": both took ""it" is the copy to be returned; the values of the given array are sorted into the returned list and the given array is not modified"
- R-ORD-2, "the sum( first index value, last index value) is even": both took "the condition is defined only for a non-empty array; the empty array falls under neither order rule"
- R-NC-1, "don't change the given array": both took "the list passed as array keeps its elements and their order; only a copy is sorted"
