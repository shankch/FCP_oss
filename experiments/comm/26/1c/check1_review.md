# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 8.

## Questions
1. **scenario** (R-EX-1): the behaviour RA-EX-1 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
2. **scenario** (R-EX-1): the behaviour RB-EX-1 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **depends** (R-IF-3, R-RM-1, R-RM-2, R-RM-3): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `remove_duplicates([0, 1, 1, 1]) -> raised another exception or did not finish`
4. **ambiguity** (R-IF-3): "-> List[int]" can mean: the return annotation obliges the function to return normally with a list of integers for every list of integers passed in / the annotation only describes the type of the value when the function returns; raising an exception on some inputs is not excluded. Which is meant?
5. **ambiguity** (R-RM-1): "remove all elements that occur more than once" can mean: remove every occurrence of each value that occurs more than once, so no such value appears in the result (remove_duplicates([1, 2, 3, 2, 4]) would be [1, 3, 4]); this contradicts the example R-EX-1, which returns [1, 2, 3, 4] / remove only the extra (repeated) occurrences of each value that occurs more than once, so exactly one occurrence of it remains in the result (remove_duplicates([1, 2, 3, 2, 4]) == [1, 2, 3, 4]); this agrees with the example R-EX-1 and the function name remove_duplicates. Which is meant?
6. **ambiguity** (R-RM-3): "From a list of integers, remove" can mean: build and return a new list; the list passed as numbers is left unchanged / remove the elements from the list passed as numbers in place (and return that list). Which is meant?
7. **ambiguity** (R-ORD-1): "Keep order of elements left the same as in the input" can mean: a value that is kept once out of several occurrences takes the position of its first occurrence in numbers (the example R-EX-1 gives [1, 2, 3, 4]) / a value that is kept once out of several occurrences takes the position of its last occurrence in numbers (would give [1, 3, 2, 4] for [1, 2, 3, 2, 4]) / the order only constrains elements that occur exactly once; the position of a kept repeated value is free. Which is meant?
8. **ambiguity** (R-EX-1): "[1, 2, 3, 4]" can mean: the example is authoritative: one occurrence (the first) of the repeated value 2 is kept, so R-RM-1 means removing only the extra copies / the example contradicts R-RM-1 read literally (remove every element that occurs more than once), under which the call returns [1, 3, 4]; the example is in error. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IF-3, "-> List[int]": both took "the return annotation obliges the function to return normally with a list of integers for every list of integers passed in"
- R-DEF-1, "occur more than once": both took "the value appears at two or more positions anywhere in numbers (not necessarily adjacent)"
- R-RM-1, "remove all elements that occur more than once": both took "remove every occurrence of each value that occurs more than once, so no such value appears in the result (remove_duplicates([1, 2, 3, 2, 4]) would be [1, 3, 4]); this contradicts the example R-EX-1, which returns [1, 2, 3, 4]"
- R-EX-1, "[1, 2, 3, 4]": both took "the example contradicts R-RM-1 read literally (remove every element that occurs more than once), under which the call returns [1, 3, 4]; the example is in error"

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- request points of variant, agent_a
- the comparison of agent_a and variant
