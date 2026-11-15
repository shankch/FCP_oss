# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 8.

## Questions
1. **scenario** (R-EX-1): the behaviour RA-EX-1 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
2. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **scenario** (R-EX-3): the behaviour RA-EX-3 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
4. **depends** (R-CH-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `smallest_change([0, 1, 0]) -> 0`
5. **ambiguity** (R-CH-1): "the minimum number of elements that need to be changed" can mean: the number of mirror pairs whose two elements differ, as the definition gives (4, 1 and 0 for the three examples); the examples, which contradict this, are wrong / the value the examples give (8, 7 and 5), which in all three cases is len(arr); the examples are authoritative over the stated definition. Which is meant?
6. **ambiguity** (R-EX-1): "== 8" can mean: the example is erroneous and contradicts R-CH-1: all four mirror pairs (1,6), (2,9), (3,7), (5,4) differ, so the minimum is 4 and the call should return 4 / the example is authoritative: the call returns 8 (the length of the array), overriding the minimum-change definition. Which is meant?
7. **ambiguity** (R-EX-2): "== 7" can mean: the example is erroneous and contradicts R-CH-1: only the mirror pair (1,2) differs, so the minimum is 1 and the call should return 1 / the example is authoritative: the call returns 7 (the length of the array), overriding the minimum-change definition. Which is meant?
8. **ambiguity** (R-EX-3): "== 5" can mean: the example is erroneous and contradicts R-CH-1 and R-DEF-1: [1, 2, 3, 2, 1] is already palindromic, so the minimum is 0 and the call should return 0 / the example is authoritative: the call returns 5 (the length of the array), overriding the minimum-change definition. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "an array arr of integers": both took "any list of integers, including the empty list (for which the answer is 0, since an empty array is already palindromic)"
- R-DEF-2, "any other element": both took "any other integer value (not restricted to values present in the array)"
- R-CH-1, "the minimum number of elements that need to be changed": both took "the number of mirror pairs whose two elements differ, as the definition gives (4, 1 and 0 for the three examples); the examples, which contradict this, are wrong"
