# FCP review

Before any code: the request alone.

Settled: 2 requirements. Questions: 13.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: Calling sort_array with the empty list returns the empty list.
- R-EX-2: Calling sort_array with [5] returns [5].

## Questions
1. **conflict** (R-ORD-1, R-ORD-2, R-RET-2): no implementation can meet these requirements on these calls: which one gives way?
   - `sort_array([1, 0])`
2. **conflict** (R-ORD-1, R-ORD-2, R-RET-1, R-RET-2): no implementation can meet these requirements on these calls: which one gives way?
   - `sort_array([1, 0])`
3. **depends** (R-ORD-1, R-ORD-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `sort_array([2, 4, 0]) -> [4, 2, 0]`
4. **ambiguity** (R-RET-2): "a copy of the given array after sorting" can mean: copy the given array, then sort the copy and return it; the given array is left unchanged (consistent with R-MUT-1) / sort the given array itself, then return a copy of the sorted array; the given array is changed by the call, which contradicts R-MUT-1 (don't change the given array). Which is meant?
5. **ambiguity** (R-ORD-1): "is odd or even" can mean: odd only: ascending exactly when the parity sum is odd; 'or even' is a slip (matches examples R-EX-3 and R-EX-4 and makes the rule complementary to the even case of R-ORD-2) / literally odd or even, i.e. every non-empty array is sorted ascending; this contradicts R-ORD-2 (read literally, descending for every non-empty array) and example R-EX-4 (sum 2 + 6 = 8, result descending) / even only: ascending exactly when the parity sum is even (the second disjunct taken as the condition); contradicts examples R-EX-3 and R-EX-4. Which is meant?
6. **ambiguity** (R-ORD-1): "in ascending order" can mean: non-decreasing: each element is less than or equal to the next, duplicates kept / strictly increasing: duplicates removed, which contradicts R-RET-2 (the result is a copy with the same elements). Which is meant?
7. **ambiguity** (R-ORD-1): "you will sort the given array" can mean: sort a copy of the given array and return it, leaving the argument unchanged (consistent with R-RET-2 and R-MUT-1) / sort the given array itself, in place; this contradicts R-MUT-1 (don't change the given array). Which is meant?
8. **ambiguity** (R-ORD-2): "is even or odd" can mean: even only: descending exactly when the parity sum is even; 'or odd' is a slip (matches examples R-EX-3 and R-EX-4 and makes the rule complementary to the odd case of R-ORD-1) / literally even or odd, i.e. every non-empty array is sorted descending; this contradicts R-ORD-1 (read literally, ascending for every non-empty array) and example R-EX-3 (sum 2 + 5 = 7, result ascending) / odd only: descending exactly when the parity sum is odd (the second disjunct taken as the condition); contradicts examples R-EX-3 and R-EX-4. Which is meant?
9. **ambiguity** (R-ORD-2): "in descending order" can mean: non-increasing: each element is greater than or equal to the next, duplicates kept / strictly decreasing: duplicates removed, which contradicts R-RET-2 (the result is a copy with the same elements). Which is meant?
10. **ambiguity** (R-ORD-2): "sort it" can mean: 'it' is the copy that is returned: sort the copy, leaving the argument unchanged (consistent with R-RET-2 and R-MUT-1) / 'it' is the given array itself, sorted in place; this contradicts R-MUT-1 (don't change the given array). Which is meant?
11. **ambiguity** (R-MUT-1): "don't change the given array" can mean: the argument list is left unmodified; the sorting described in the docstring is applied to a copy / contradicted by 'you will sort the given array' (R-ORD-1), 'sort it' (R-ORD-2) and 'a copy of the given array after sorting' (R-RET-2) read as sorting the argument itself, under which the argument is changed. Which is meant?
12. **ambiguity** (R-EX-3): "[0, 1, 2, 3, 4, 5]" can mean: the intended result: the sum 2 + 5 = 7 is odd, so the result is ascending, consistent with the odd-only reading of R-ORD-1 / contradicts R-ORD-2 read literally ('even or odd', i.e. descending for every non-empty array), under which the result would be [5, 4, 3, 2, 1, 0]. Which is meant?
13. **ambiguity** (R-EX-4): "[6, 5, 4, 3, 2, 1, 0]" can mean: the intended result: the sum 2 + 6 = 8 is even, so the result is descending, consistent with the even-only reading of R-ORD-2 / contradicts R-ORD-1 read literally ('odd or even', i.e. ascending for every non-empty array), under which the result would be [0, 1, 2, 3, 4, 5, 6]. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RET-2, "a copy of the given array after sorting": both took "copy the given array, then sort the copy and return it; the given array is left unchanged (consistent with R-MUT-1)"
- R-DEF-1, "first index value, last index value": both took "the values stored at the first and last positions: array[0] + array[len(array) - 1]"
- R-DEF-1, "the sum( first index value, last index value)": both took "the first and last values of the given array as passed (unsorted)"
- R-ORD-1, "is odd or even": both took "literally odd or even, i.e. every non-empty array is sorted ascending; this contradicts R-ORD-2 (read literally, descending for every non-empty array) and example R-EX-4 (sum 2 + 6 = 8, result descending)"
- R-ORD-1, "in ascending order": both took "non-decreasing: each element is less than or equal to the next, duplicates kept"
- R-ORD-1, "you will sort the given array": both took "sort a copy of the given array and return it, leaving the argument unchanged (consistent with R-RET-2 and R-MUT-1)"
- R-ORD-2, "is even or odd": both took "literally even or odd, i.e. every non-empty array is sorted descending; this contradicts R-ORD-1 (read literally, ascending for every non-empty array) and example R-EX-3 (sum 2 + 5 = 7, result ascending)"
- R-ORD-2, "in descending order": both took "non-increasing: each element is greater than or equal to the next, duplicates kept"
- R-ORD-2, "sort it": both took "'it' is the copy that is returned: sort the copy, leaving the argument unchanged (consistent with R-RET-2 and R-MUT-1)"
- R-MUT-1, "don't change the given array": both took "the argument list is left unmodified; the sorting described in the docstring is applied to a copy"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `all(i < len(array): array[i] >= 0)`
- agent_b, RB-IN-1 (R-IN-1): every call meets `all(i < len(array): array[i] >= 0)`
