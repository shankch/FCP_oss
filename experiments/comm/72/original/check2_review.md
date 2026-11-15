# FCP review

Before any code: the request alone.

Settled: 2 requirements. Questions: 10.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: will_it_fly([1, 2], 5) returns False: the sum 3 is within the weight 5, but [1, 2] is not a palindrome.
- R-EX-2: will_it_fly([3, 2, 3], 1) returns False: [3, 2, 3] is a palindrome, but its sum 8 is greater than the weight 1.

## Questions
1. **depends** (R-FLY-1, R-FLY-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `will_it_fly([1, 1], 2) -> False`
2. **ambiguity** (R-OUT-1): "returns True if the object q will fly, and False otherwise" can mean: the returned value must be the Python bool True or False / any truthy or falsy value (such as 1 or 0, or a non-empty or empty list) is acceptable as the answer. Which is meant?
3. **ambiguity** (R-FLY-1): "less than or equal the maximum possible weight w" can mean: sum(q) <= w, as the rule states: a balanced q whose sum equals w flies (True) / sum(q) < w, as the example comments phrase it ("is less than the maximum possible weight"): a balanced q whose sum equals w does not fly. Which is meant?
4. **ambiguity** (R-FLY-1): "palindromic list" can mean: the empty list is palindromic (it equals its reverse), so will_it_fly([], w) returns True for every w >= 0 / the empty list is not a balanced object, so will_it_fly([], w) returns False. Which is meant?
5. **ambiguity** (R-FLY-2): "The object q will fly if" can mean: 'if' means 'if and only if': q flies exactly when it is balanced and light enough, so an unbalanced q must return False / 'if' gives only a sufficient condition: the prompt does not say when q does not fly, so the answer for an unbalanced q is not determined by 'False otherwise'. Which is meant?
6. **ambiguity** (R-FLY-2): "palindromic list" can mean: the empty list is palindromic, so it is never covered by this requirement / the empty list is not a balanced object, so will_it_fly([], w) returns False. Which is meant?
7. **ambiguity** (R-FLY-3): "The object q will fly if" can mean: 'if' means 'if and only if': q flies exactly when it is balanced and light enough, so a q heavier than w must return False / 'if' gives only a sufficient condition: the prompt does not say when q does not fly, so the answer for a q heavier than w is not determined by 'False otherwise'. Which is meant?
8. **ambiguity** (R-FLY-3): "less than or equal the maximum possible weight w" can mean: sum(q) <= w flies: False is required only when sum(q) > w / sum(q) < w flies, as the example comments phrase it: False is also required when sum(q) == w. Which is meant?
9. **ambiguity** (R-EX-3): "is less than the maximum possible weight" can mean: the comment only describes this call (8 < 9); the rule 'less than or equal' still decides a sum equal to w, which flies / the comment states the rule: the sum must be strictly less than w, contradicting 'less than or equal' for a sum equal to w. Which is meant?
10. **ambiguity** (R-EX-4): "is less than the maximum possible weight" can mean: the comment only describes this call (3 < 5); the rule 'less than or equal' still decides a sum equal to w, which flies / the comment states the rule: the sum must be strictly less than w, contradicting 'less than or equal' for a sum equal to w. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-OUT-1, "returns True if the object q will fly, and False otherwise": both took "the returned value must be the Python bool True or False"
- R-FLY-1, "less than or equal the maximum possible weight w": both took "sum(q) <= w, as the rule states: a balanced q whose sum equals w flies (True)"
- R-FLY-1, "palindromic list": both took "the empty list is palindromic (it equals its reverse), so will_it_fly([], w) returns True for every w >= 0"
- R-FLY-2, "The object q will fly if": both took "'if' means 'if and only if': q flies exactly when it is balanced and light enough, so an unbalanced q must return False"
- R-FLY-2, "palindromic list": both took "the empty list is palindromic, so it is never covered by this requirement"
- R-FLY-3, "The object q will fly if": both took "'if' means 'if and only if': q flies exactly when it is balanced and light enough, so a q heavier than w must return False"
- R-FLY-3, "less than or equal the maximum possible weight w": both took "sum(q) <= w flies: False is required only when sum(q) > w"
- R-DEF-1, "The object q will fly if": both took "'if' means 'if and only if': q flies exactly when it is balanced and the sum of its elements is at most w"
- R-DEF-2, "palindromic list": both took "the empty list is palindromic (it equals its reverse), hence balanced"
- R-DEF-3, "less than or equal the maximum possible weight w": both took "sum(q) <= w, as the rule states: a sum equal to w meets the condition"
- R-EX-3, "is less than the maximum possible weight": both took "the comment only describes this call (8 < 9); the rule 'less than or equal' still decides a sum equal to w, which flies"
- R-EX-4, "is less than the maximum possible weight": both took "the comment only describes this call (3 < 5); the rule 'less than or equal' still decides a sum equal to w, which flies"
