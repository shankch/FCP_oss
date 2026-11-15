# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 20.

## Questions
1. **scenario** (R-EX-3): the behaviour RA-EX-3 describes can never happen under agent_a: its formal example is impossible in itself (a formalization error). Is the example, or the rule, what is meant?
2. **scenario** (R-EX-1): the behaviour RA-EX-1 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
4. **scenario** (R-EX-4): the behaviour RA-EX-4 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
5. **readings** (R-EMP-2): the two readings of this requirement disagree on these calls: which is meant?
   - `pluck([]) -> [1]`
6. **readings** (R-PL-2): the two readings of this requirement disagree (no separating call was found within the budget): which is meant?
7. **readings** (R-PL-3): the two readings of this requirement disagree (no separating call was found within the budget): which is meant?
8. **ambiguity** (R-PL-1): "pluck" can mean: select the node and report it, leaving arr unchanged / remove the node from arr (mutating the argument) and report it. Which is meant?
9. **ambiguity** (R-PL-1): "return it" can mean: return the node in the [value, index] list form given later (R-OUT-1) / return the node's value alone. Which is meant?
10. **ambiguity** (R-PL-2): "the smallest even value" can mean: the minimum among the even elements of arr, as this sentence states / the largest element of arr of any parity, which is what Examples 1, 2 and 4 show ([4,2,3] -> [4, 0], [1,2,3] -> [3, 2], [5, 0, 3, 0, 4, 2] -> [5, 0]); contradicts R-EX-1, R-EX-2 and R-EX-4. Which is meant?
11. **ambiguity** (R-PL-2): "even" can mean: 0 counts as an even value / 0 is not counted as an even value. Which is meant?
12. **ambiguity** (R-PL-3): "return the node that has smallest index" can mean: ties are broken by the smallest index, so pluck([5, 0, 3, 0, 4, 2]) returns [0, 1] / Example 4 (R-EX-4) is right and pluck([5, 0, 3, 0, 4, 2]) returns [5, 0], so the tie on 0 does not decide the result; contradicts this sentence. Which is meant?
13. **ambiguity** (R-OUT-1): "smalest_value" can mean: the smallest even value, i.e. the value of the plucked node (R-PL-2) / the smallest value of arr of any parity / the largest value of arr, as Examples 1, 2 and 4 show; contradicts R-PL-2. Which is meant?
14. **ambiguity** (R-OUT-2): "its index" can mean: the 0-based Python index of the node in arr (consistent with every example) / the 1-based position of the node in arr. Which is meant?
15. **ambiguity** (R-EMP-1): "no even values" can mean: 0 is even, so an array whose only even elements are 0 does have even values and a node is plucked / 0 is not counted, so such an array has no even values and the call returns []. Which is meant?
16. **ambiguity** (R-EMP-2): "the given array is empty" can mean: the empty array is a valid input and pluck([]) must return [] / the empty array is excluded by the Constraints (1 <= nodes.length, R-IN-2), so this clause never applies; contradicts R-IN-2. Which is meant?
17. **ambiguity** (R-EX-1): "Output: [4, 0]" can mean: [4, 0] is the intended output (the largest value 4 at index 0); contradicts R-PL-2, under which the smallest even value is 2 at index 1 / the rule of R-PL-2 holds and the intended output is [2, 1]; the example is wrong. Which is meant?
18. **ambiguity** (R-EX-2): "Output: [3, 2]" can mean: [3, 2] is the intended output (the largest value 3 at index 2); contradicts R-PL-2, since 3 is odd and the only even value is 2 at index 1 / the rule of R-PL-2 holds and the intended output is [2, 1]; the example is wrong. Which is meant?
19. **ambiguity** (R-EX-3): "Input: []" can mean: the empty array is a valid input whose result is [] / the empty array violates the Constraints (1 <= nodes.length, R-IN-2), so this example lies outside the input domain; contradicts R-IN-2. Which is meant?
20. **ambiguity** (R-EX-4): "Output: [5, 0]" can mean: [5, 0] is the intended output (the largest value 5 at index 0); contradicts R-PL-2 and R-PL-3, under which the smallest even value 0 first occurs at index 1 / the rules of R-PL-2 and R-PL-3 hold and the intended output is [0, 1]; the example is wrong. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-DEF-1, "representing a branch of a tree": both took "arr is a flat list of node values; position carries no tree meaning beyond being the node's index"
- R-PL-1, "pluck": both took "select the node and report it, leaving arr unchanged"
- R-PL-1, "return it": both took "return the node in the [value, index] list form given later (R-OUT-1)"
- R-PL-2, "the smallest even value": both took "the minimum among the even elements of arr, as this sentence states"
- R-PL-2, "even": both took "0 counts as an even value"
- R-PL-3, "return the node that has smallest index": both took "ties are broken by the smallest index, so pluck([5, 0, 3, 0, 4, 2]) returns [0, 1]"
- R-OUT-1, "smalest_value": both took "the smallest even value, i.e. the value of the plucked node (R-PL-2)"
- R-OUT-2, "its index": both took "the 0-based Python index of the node in arr (consistent with every example)"
- R-EMP-1, "no even values": both took "0 is even, so an array whose only even elements are 0 does have even values and a node is plucked"
- R-EMP-2, "the given array is empty": both took "the empty array is a valid input and pluck([]) must return []"
- R-EX-3, "Input: []": both took "the empty array is a valid input whose result is []"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `all(i < len(arr): arr[i] >= 0)`
- agent_a, RA-IN-2 (R-IN-2): every call meets `len(arr) >= 1`
- agent_a, RA-IN-3 (R-IN-3): every call meets `len(arr) <= 10000`
- agent_a, RA-IN-4 (R-IN-4): every call meets `all(i < len(arr): arr[i] >= 0)`
- agent_b, RB-IN-1 (R-IN-1): every call meets `all(i < len(arr): arr[i] >= 0)`
- agent_b, RB-IN-3 (R-IN-3): every call meets `len(arr) <= 10000`
- agent_b, RB-IN-4 (R-IN-4): every call meets `all(i < len(arr): arr[i] >= 0)`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- request points of agent_a
- request points of agent_b
- request points of agent_a, agent_b
- request points of agent_a, agent_b, variant
- the comparison of agent_a and agent_b
- request points of agent_b, agent_a
