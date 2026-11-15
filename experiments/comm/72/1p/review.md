# FCP review

Before any code: the request alone.

Settled: 4 requirements. Questions: 7.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: The call will_it_fly([1, 2], 5) returns False: its weight 3 is below 5 but [1, 2] is unbalanced.
- R-EX-2: The call will_it_fly([3, 2, 3], 1) returns False.
- R-EX-3: The call will_it_fly([3, 2, 3], 9) returns True.
- R-EX-4: The call will_it_fly([3], 5) returns True.

## Questions
1. **depends** (R-FLY-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `will_it_fly([2], 3) -> False`
2. **ambiguity** (R-FLY-1): "will fly" can mean: q flies exactly when it is balanced (R-BAL-1) and its weight, the sum of its elements, is within the maximum possible weight w (R-WT-3); there is no other condition / the prompt never defines flying, so only the necessary conditions in the example comment (R-BAL-1, R-WT-3) and the four examples are fixed; a balanced list within the weight limit may or may not fly. Which is meant?
3. **ambiguity** (R-FLY-1): "returns True" can mean: returns the bool True itself / returns any truthy value (for example 1 or a non-empty list). Which is meant?
4. **ambiguity** (R-FLY-1): "the object q" can mean: q may be the empty list; it is balanced and weighs 0, so it flies whenever 0 is within the maximum weight w / an empty q is no object and does not fly, so the function returns False for it / the result for an empty q is left open. Which is meant?
5. **ambiguity** (R-FLY-2): "False" can mean: returns the bool False itself / returns any falsy value (for example 0, None or an empty list). Which is meant?
6. **ambiguity** (R-WT-3): "less than the maximum possible weight" can mean: a weight equal to w is allowed: q can fly when sum(q) <= w, since w is the maximum possible weight / the weight must be strictly less than w, as the comment phrases it: q does not fly when sum(q) >= w. Which is meant?
7. **ambiguity** (R-BAL-1): "unbalanced" can mean: q is not a palindrome: q[i] != q[len(q)-1-i] for some i / the first and last elements of q differ / the sum of the first half of q differs from the sum of the second half (the middle element of an odd-length list belongs to neither). Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FLY-1, "will fly": both took "q flies exactly when it is balanced (R-BAL-1) and its weight, the sum of its elements, is within the maximum possible weight w (R-WT-3); there is no other condition"
- R-FLY-1, "returns True": both took "returns the bool True itself"
- R-FLY-1, "the object q": both took "q may be the empty list; it is balanced and weighs 0, so it flies whenever 0 is within the maximum weight w"
- R-FLY-2, "False": both took "returns the bool False itself"
- R-WT-3, "less than the maximum possible weight": both took "a weight equal to w is allowed: q can fly when sum(q) <= w, since w is the maximum possible weight"
- R-BAL-1, "unbalanced": both took "q is not a palindrome: q[i] != q[len(q)-1-i] for some i"
