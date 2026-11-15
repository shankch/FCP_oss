# FCP review

Before any code: the request alone.

Settled: 3 requirements. Questions: 2.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: will_it_fly([1, 2], 5) returns False: the sum 1+2 = 3 is less than w = 5, but [1, 2] is not balanced (not a palindrome).
- R-EX-3: will_it_fly([3, 2, 3], 9) returns True: the sum 3+2+3 = 8 is less than the maximum possible weight w = 9, and [3, 2, 3] is balanced.
- R-EX-4: will_it_fly([3], 5) returns True: the sum 3 is less than the maximum possible weight w = 5, and the one-element list [3] is balanced.

## Questions
1. **depends** (R-RET-1, R-RET-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `will_it_fly([], 0) -> False`
2. **ambiguity** (R-EX-2): "3+2+3 is more than the maximum possible weight" can mean: contradiction with the rule 'the sum of its elements is more than or less than or equal the maximum possible weight w': the example governs, so a balanced q whose sum is more than w does not fly and the result is False / contradiction with the rule 'the sum of its elements is more than or less than or equal the maximum possible weight w': the rule governs, so [3, 2, 3] with w = 1 flies and the example's expected False is wrong. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FLY-1, "will fly if": both took "q will fly exactly when (if and only if) it is balanced and meets the weight condition; if either condition fails, q does not fly"
- R-FLY-2, "palindromic list": both took "the empty list [] is palindromic (it equals its own reverse), so [] is balanced"
- R-FLY-3, "more than or less than or equal": both took "taken literally, 'more than, less than or equal' covers every sum, so the weight condition always holds and only balance matters"
- R-FLY-3, "the sum of its elements is more than": both took "contradiction with the example will_it_fly([3, 2, 3], 1) ➞ False: the rule governs, so a balanced q whose sum is more than w still flies and the example's expected False is wrong"
- R-EX-2, "3+2+3 is more than the maximum possible weight": both took "contradiction with the rule 'the sum of its elements is more than or less than or equal the maximum possible weight w': the rule governs, so [3, 2, 3] with w = 1 flies and the example's expected False is wrong"
