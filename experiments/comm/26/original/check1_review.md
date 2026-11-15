# FCP review

Before any code: the request alone.

Settled: 2 requirements. Questions: 7.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RM-2: Every value that occurs exactly once in numbers occurs in the returned list (only elements that occur more than once are removed).
- R-RM-3: The returned list is obtained from numbers only by removing elements: no value occurs in the returned list more often than it occurs in numbers (in particular, no value absent from numbers occurs in it).

## Questions
1. **depends** (R-RM-1, R-SIG-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `remove_duplicates([4, 6, 5, 3, 0, 5, 0, 6]) -> [4, 6, 5, 3, 0]`
2. **ambiguity** (R-SIG-2): "-> List[int]" can mean: The return annotation is an obligation: for every list of integers the function returns a list of integers and never raises. / The return annotation only describes the type of the value when the function returns; raising an exception on some inputs is not excluded.. Which is meant?
3. **ambiguity** (R-RM-1): "remove all elements that occur more than once" can mean: Every occurrence of each value that occurs more than once in numbers is removed, so no such value is in the result (consistent with the example of R-EX-1). / Only the repeated (extra) occurrences are removed, so each value that occurs more than once is kept exactly once (the reading suggested by the function name remove_duplicates in R-SIG-1, which contradicts the example of R-EX-1).. Which is meant?
4. **ambiguity** (R-RM-1): "From a list of integers, remove" can mean: A new list without those elements is returned; the argument numbers is left unchanged. / The elements are deleted from the given list in place, and that list is returned.. Which is meant?
5. **ambiguity** (R-ORD-1): "Keep order of elements left the same as in the input" can mean: The remaining elements keep their relative order: the returned list is a subsequence of numbers. / The remaining elements keep their original positions (indices) in the list.. Which is meant?
6. **ambiguity** (R-ORD-1): "elements left" can mean: Under the docstring reading of R-RM-1, the elements left are those whose value occurs exactly once, ordered by their single position. / Under the deduplicating reading of R-RM-1 and R-SIG-1, a kept value is ordered by the position of its first occurrence in numbers. / Under the deduplicating reading of R-RM-1 and R-SIG-1, a kept value is ordered by the position of its last occurrence in numbers.. Which is meant?
7. **ambiguity** (R-EX-1): "[1, 3, 4]" can mean: The example is authoritative: the value 2, which occurs twice, is removed entirely, as the docstring sentence of R-RM-1 literally says. / The example contradicts the function name remove_duplicates of R-SIG-1, under which the call would return [1, 2, 3, 4].. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-SIG-1, "remove_duplicates": both took "The name only labels the function; its behaviour is given by the docstring: every element whose value occurs more than once is removed, including all of its copies (so [1, 2, 3, 2, 4] gives [1, 3, 4])."
- R-SIG-2, "-> List[int]": both took "The return annotation is an obligation: for every list of integers the function returns a list of integers and never raises."
- R-RM-1, "remove all elements that occur more than once": both took "Every occurrence of each value that occurs more than once in numbers is removed, so no such value is in the result (consistent with the example of R-EX-1)."
- R-RM-1, "From a list of integers, remove": both took "A new list without those elements is returned; the argument numbers is left unchanged."
- R-ORD-1, "Keep order of elements left the same as in the input": both took "The remaining elements keep their relative order: the returned list is a subsequence of numbers."
- R-ORD-1, "elements left": both took "Under the docstring reading of R-RM-1, the elements left are those whose value occurs exactly once, ordered by their single position."
- R-EX-1, "[1, 3, 4]": both took "The example is authoritative: the value 2, which occurs twice, is removed entirely, as the docstring sentence of R-RM-1 literally says."

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- conflict search of agent_a
