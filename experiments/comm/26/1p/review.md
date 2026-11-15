# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 7.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RM-2: The returned list contains only elements of numbers: every value appears in the returned list at most as many times as it appears in numbers (removal never adds or changes elements).

## Questions
1. **depends** (R-RM-3): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate([0]) -> []`
2. **ambiguity** (R-SIG-2): "remove" can mean: Build and return a new list without the removed elements; the argument numbers is left unchanged. / Delete the elements from the argument list numbers in place and return that same (mutated) list.. Which is meant?
3. **ambiguity** (R-RM-1): "remove all elements that occur" can mean: Literal: every element of a list occurs in it, so every element is removed and the returned list is always empty. / The sentence is cut short and means 'that occur more than once': every value that appears two or more times in numbers is removed entirely (all of its copies); values that appear exactly once remain. / Remove repeated occurrences (deduplicate): the first occurrence of each value is kept and every later occurrence of the same value is removed.. Which is meant?
4. **ambiguity** (R-RM-1): "all elements that occur" can mean: Contradiction with R-RM-3: 'all elements' read literally removes every element, since every element of numbers occurs in numbers, so nothing is kept. / Contradiction with R-RM-3: the restrictive clause 'that occur' presupposes that only some elements are removed and the others are kept, which requires a selecting condition the sentence does not state.. Which is meant?
5. **ambiguity** (R-RM-3): "remove all elements that occur" can mean: Literal: every element of a list occurs in it, so no element is kept and the returned list is always empty. / The sentence is cut short and means 'that occur more than once': every value that appears exactly once in numbers is kept; values that appear two or more times are not kept at all. / Remove repeated occurrences (deduplicate): the first occurrence of each distinct value is kept, so each distinct value of numbers appears exactly once in the returned list.. Which is meant?
6. **ambiguity** (R-RM-3): "all elements that occur" can mean: Contradiction with R-RM-1: 'all elements' read literally removes every element, since every element of numbers occurs in numbers, so nothing is kept. / Contradiction with R-RM-1: the restrictive clause 'that occur' presupposes that only some elements are removed and the others are kept, which requires a selecting condition the sentence does not state.. Which is meant?
7. **ambiguity** (R-RM-4): "remove" can mean: Removing elements leaves the remaining elements in their original relative order: the returned list is a subsequence of numbers. / The prompt states no order for the result: the remaining elements may be returned in any order.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-SIG-2, "remove": both took "Build and return a new list without the removed elements; the argument numbers is left unchanged."
- R-RM-1, "remove all elements that occur": both took "Literal: every element of a list occurs in it, so every element is removed and the returned list is always empty."
- R-RM-1, "all elements that occur": both took "Contradiction with R-RM-3: 'all elements' read literally removes every element, since every element of numbers occurs in numbers, so nothing is kept."
- R-RM-3, "remove all elements that occur": both took "Literal: every element of a list occurs in it, so no element is kept and the returned list is always empty."
- R-RM-3, "all elements that occur": both took "Contradiction with R-RM-1: 'all elements' read literally removes every element, since every element of numbers occurs in numbers, so nothing is kept."
- R-RM-4, "remove": both took "Removing elements leaves the remaining elements in their original relative order: the returned list is a subsequence of numbers."

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the comparison of agent_a and agent_b
