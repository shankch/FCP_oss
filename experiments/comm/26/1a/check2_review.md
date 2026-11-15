# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 10.

## Questions
1. **depends** (R-EX-1, R-FN-1, R-FN-2, R-FN-3, R-IO-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate([0]) -> []`
2. **readings** (R-FN-1): the two readings of this requirement disagree on these calls: which is meant?
   - `candidate([0, 0]) -> [0]`
3. **readings** (R-FN-2): the two readings of this requirement disagree on these calls: which is meant?
   - `candidate([0]) -> []`
4. **ambiguity** (R-FN-1, R-FN-2): "K" can mean: K is 2, the only value consistent with the example (2 occurs twice and is removed; 1, 3 and 4 occur once and are kept) / K stands for 'more than once', as in the usual remove-duplicates task: every value occurring 2 or more times is removed / K is an undefined placeholder (possibly a missing second parameter of candidate, which takes only numbers), so the removal count is not determined by the request. Which is meant?
5. **ambiguity** (R-FN-1): "occur K time(s)" can mean: exactly K times: a value occurring more than K times is kept / at least K times: a value occurring K or more times is removed. Which is meant?
6. **ambiguity** (R-FN-1): "time(s)" can mean: contradiction with the example R-EX-1: the singular 'time' admits K = 1, and removing values that occur once turns [1, 2, 3, 2, 4] into [2, 2], not [1, 3, 4]; likewise any K of 3 or more removes nothing and returns [1, 2, 3, 2, 4] / no contradiction: K = 2 (exactly or at least), which gives [1, 3, 4] as in the example; '(s)' is only template wording. Which is meant?
7. **ambiguity** (R-FN-1): "remove" can mean: return a new list without those elements, leaving the argument numbers unchanged / delete those elements from the argument numbers in place (and return that list). Which is meant?
8. **ambiguity** (R-FN-2): "occur K time(s)" can mean: exactly K times: every occurrence of a value occurring more than K times is kept / at least K times: a value occurring more than K times is also removed, so only values occurring fewer than K times are kept. Which is meant?
9. **ambiguity** (R-FN-2): "remove all elements that occur K time(s)" can mean: only the elements occurring K times are removed; every other element is kept with all of its occurrences (implied by 'elements left' and by the example) / the request only obliges the removal of those elements and states nothing about keeping the others. Which is meant?
10. **ambiguity** (R-EX-1): "[1, 3, 4]" can mean: consistent with R-FN-1 and R-FN-2 only if K = 2 (exactly 2 or at least 2); the example does not decide between 'exactly' and 'at least' / contradiction with R-FN-1: for any other K the rule gives a different result, e.g. K = 1 (allowed by the singular 'time') gives [2, 2] and K of 3 or more gives [1, 2, 3, 2, 4]. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FN-1, "K": both took "K is 2, the only value consistent with the example (2 occurs twice and is removed; 1, 3 and 4 occur once and are kept)"
- R-FN-1, "occur K time(s)": both took "exactly K times: a value occurring more than K times is kept"
- R-FN-1, "time(s)": both took "no contradiction: K = 2 (exactly or at least), which gives [1, 3, 4] as in the example; '(s)' is only template wording"
- R-FN-1, "remove": both took "return a new list without those elements, leaving the argument numbers unchanged"
- R-FN-2, "K": both took "K is 2, the only value consistent with the example (2 occurs twice and is removed; 1, 3 and 4 occur once and are kept)"
- R-FN-2, "occur K time(s)": both took "exactly K times: every occurrence of a value occurring more than K times is kept"
- R-FN-2, "remove all elements that occur K time(s)": both took "only the elements occurring K times are removed; every other element is kept with all of its occurrences (implied by 'elements left' and by the example)"
- R-EX-1, "[1, 3, 4]": both took "consistent with R-FN-1 and R-FN-2 only if K = 2 (exactly 2 or at least 2); the example does not decide between 'exactly' and 'at least'"

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the conflicts and open choices of agent_b: these searches leave out RB-FN-1, RB-FN-2 (rules stated for every value of a variable); 8 calls with two answers that break them are not reported
- the comparison of agent_a and variant
- the comparison of agent_b and variant
