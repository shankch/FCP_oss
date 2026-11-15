# FCP review

Before any code: the request alone.

Settled: 3 requirements. Questions: 14.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RES-1: For every allowed argument, sort_array returns a list: it does not raise an exception, fail to finish, or return a value of another kind.
- R-EX-1: Calling sort_array([]) returns the empty list [].
- R-EX-2: Calling sort_array([5]) returns [5].

## Questions
1. **scenario** (R-EX-3): the behaviour RB-EX-3 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
2. **scenario** (R-EX-4): the behaviour RB-EX-4 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **depends** (R-ORD-1, R-ORD-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `sort_array([0, 4, 1, 3, 0, 1, 3]) -> [0, 0, 1, 1, 3, 3, 4]`
4. **ambiguity** (R-RES-2): "a copy" can mean: The returned list must be a new list object, distinct from the argument object. / Only the contents of the returned list matter; returning the argument object itself is acceptable when it already holds the right contents.. Which is meant?
5. **ambiguity** (R-RES-2): "a copy of the given array after sorting" can mean: Return a sorted copy and leave the argument as it was passed (consistent with "don't change the given array", R-MUT-1). / Sort the given array itself and then return a copy of it; this contradicts "don't change the given array" (R-MUT-1).. Which is meant?
6. **ambiguity** (R-ORD-1): "ascending order" can mean: Non-decreasing: each element is at most the next one, duplicates kept. / Strictly increasing: each element is less than the next one (impossible while keeping every element when the argument has duplicates).. Which is meant?
7. **ambiguity** (R-ORD-1): "you will sort the given array" can mean: Sort a copy of the argument; the argument itself stays unchanged (consistent with "don't change the given array", R-MUT-1). / Sort the argument itself in place; this contradicts "don't change the given array" (R-MUT-1).. Which is meant?
8. **ambiguity** (R-ORD-1): "in ascending order if the sum( first index value, last index value) is odd" can mean: The rule is right: an odd sum gives ascending order, so the example sort_array([2, 4, 3, 0, 1, 5]) => [5, 4, 3, 2, 1, 0] (R-EX-3) is wrong, since 2 + 5 = 7 is odd (and 0 + 5 = 5 under the index reading); its result should be [0, 1, 2, 3, 4, 5]. / The example R-EX-3 is right: an odd sum gives descending order, and the rule has odd and even swapped.. Which is meant?
9. **ambiguity** (R-ORD-2): "descending order" can mean: Non-increasing: each element is at least the next one, duplicates kept. / Strictly decreasing: each element is greater than the next one (impossible while keeping every element when the argument has duplicates).. Which is meant?
10. **ambiguity** (R-ORD-2): "sort it" can mean: Sort a copy of the argument; the argument itself stays unchanged (consistent with "don't change the given array", R-MUT-1). / Sort the argument itself in place; this contradicts "don't change the given array" (R-MUT-1).. Which is meant?
11. **ambiguity** (R-ORD-2): "in descending order if the sum( first index value, last index value) is even" can mean: The rule is right: an even sum gives descending order, so the example sort_array([2, 4, 3, 0, 1, 5, 6]) => [0, 1, 2, 3, 4, 5, 6] (R-EX-4) is wrong, since 2 + 6 = 8 is even (and 0 + 6 = 6 under the index reading); its result should be [6, 5, 4, 3, 2, 1, 0]. / The example R-EX-4 is right: an even sum gives ascending order, and the rule has odd and even swapped.. Which is meant?
12. **ambiguity** (R-MUT-1): "don't change the given array" can mean: This note wins: the argument is left unchanged, and "you will sort the given array" / "sort it" (R-ORD-1, R-ORD-2) and "a copy of the given array after sorting" (R-RES-2) mean sorting a copy. / The statements "you will sort the given array", "sort it" and "return a copy of the given array after sorting" win: the argument is sorted in place and then copied, contradicting this note.. Which is meant?
13. **ambiguity** (R-EX-3): "[5, 4, 3, 2, 1, 0]" can mean: The example is right: the first and last elements sum to 2 + 5 = 7 (odd; 0 + 5 = 5 under the index reading), and the result is descending, so the rule "ascending order if the sum ... is odd" (R-ORD-1) has odd and even swapped. / The rule R-ORD-1 is right: an odd sum gives ascending order, so the expected result here should be [0, 1, 2, 3, 4, 5] and this example is wrong.. Which is meant?
14. **ambiguity** (R-EX-4): "[0, 1, 2, 3, 4, 5, 6]" can mean: The example is right: the first and last elements sum to 2 + 6 = 8 (even; 0 + 6 = 6 under the index reading), and the result is ascending, so the rule "descending order if the sum ... is even" (R-ORD-2) has odd and even swapped. / The rule R-ORD-2 is right: an even sum gives descending order, so the expected result here should be [6, 5, 4, 3, 2, 1, 0] and this example is wrong.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RES-2, "a copy": both took "The returned list must be a new list object, distinct from the argument object."
- R-RES-2, "a copy of the given array after sorting": both took "Return a sorted copy and leave the argument as it was passed (consistent with "don't change the given array", R-MUT-1)."
- R-DEF-1, "first index value": both took "The values stored at the first and the last index: array[0] + array[len(array) - 1]."
- R-DEF-1, "sum( first index value, last index value)": both took "For a one-element array the single element is both first and last and is counted twice (array[0] + array[0], always even)."
- R-DEF-1, "last index value": both took "For an empty array there is no first or last value, so the sum is undefined and neither order rule applies."
- R-ORD-1, "ascending order": both took "Non-decreasing: each element is at most the next one, duplicates kept."
- R-ORD-1, "you will sort the given array": both took "Sort a copy of the argument; the argument itself stays unchanged (consistent with "don't change the given array", R-MUT-1)."
- R-ORD-1, "in ascending order if the sum( first index value, last index value) is odd": both took "The rule is right: an odd sum gives ascending order, so the example sort_array([2, 4, 3, 0, 1, 5]) => [5, 4, 3, 2, 1, 0] (R-EX-3) is wrong, since 2 + 5 = 7 is odd (and 0 + 5 = 5 under the index reading); its result should be [0, 1, 2, 3, 4, 5]."
- R-ORD-2, "descending order": both took "Non-increasing: each element is at least the next one, duplicates kept."
- R-ORD-2, "sort it": both took "Sort a copy of the argument; the argument itself stays unchanged (consistent with "don't change the given array", R-MUT-1)."
- R-ORD-2, "in descending order if the sum( first index value, last index value) is even": both took "The rule is right: an even sum gives descending order, so the example sort_array([2, 4, 3, 0, 1, 5, 6]) => [0, 1, 2, 3, 4, 5, 6] (R-EX-4) is wrong, since 2 + 6 = 8 is even (and 0 + 6 = 6 under the index reading); its result should be [6, 5, 4, 3, 2, 1, 0]."
- R-MUT-1, "don't change the given array": both took "This note wins: the argument is left unchanged, and "you will sort the given array" / "sort it" (R-ORD-1, R-ORD-2) and "a copy of the given array after sorting" (R-RES-2) mean sorting a copy."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_b, RB-IN-1 (R-IN-1): every call meets `all(i < len(array): array[i] >= 0)`
