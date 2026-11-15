# FCP review

Before any code: the request alone.

Settled: 2 requirements. Questions: 16.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: pluck([4,2,3]) returns [2, 1].
- R-EX-4: pluck([5, 0, 3, 0, 4, 2]) returns [0, 1] (value 0 occurs at indices 1 and 3; the smaller index is chosen).

## Questions
1. **open** (plucked): the request allows [0, 1] or [1, 0]: which is meant?
   - `pluck([1, 0])`
2. **open** (plucked): the request allows [0, 0] or [1, 1]: which is meant?
   - `pluck([0, 1])`
3. **depends** (R-SEL-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `pluck([0, 4, 4, 0, 0, 0, 0, 0]) -> returned something else`
4. **ambiguity** (R-SEL-1): "pluck one of the nodes" can mean: a node is plucked and returned for every input; contradicts R-EMP-1 and R-EMP-2, which return [] for some inputs / a node is plucked only when arr is non-empty and some node qualifies (R-SEL-2); otherwise [] is returned (R-EMP-1, R-EMP-2). Which is meant?
5. **ambiguity** (R-SEL-1): "return it" can mean: return the plucked node itself, i.e. its value alone; contradicts R-OUT-1, which returns the list [value, index] / return the plucked node in the form R-OUT-1 gives, the list [value, index]. Which is meant?
6. **ambiguity** (R-SEL-1): "pluck" can mean: select a node and leave arr unchanged / remove the node from arr (mutate the argument) and return it. Which is meant?
7. **ambiguity** (R-SEL-2): "the node with the value" can mean: the node with the smallest even value (a qualifier seems to have been dropped; this is the only stated-style rule consistent with all four examples) / the node with the smallest value; contradicts Example 2 (R-EX-2), where [1,2,3] would give [1, 0] instead of [2, 1] / no criterion is given, so any node of arr may be plucked (only the examples constrain the choice) / the node at index 1 (every example output is [arr[1], 1]). Which is meant?
8. **ambiguity** (R-SEL-3): "the value" can mean: the smallest even value of arr (as in R-SEL-2 reading 1) / the smallest value of arr (as in R-SEL-2 reading 2) / whatever value the plucked node has, under an unconstrained choice (as in R-SEL-2 reading 3). Which is meant?
9. **ambiguity** (R-SEL-3): "return the node" can mean: return the node's value alone / return the node as the list [value, index] of R-OUT-1. Which is meant?
10. **ambiguity** (R-OUT-1): "returned in a list, [ value, its index ]" can mean: the result is the two-element list [value, index] / the result is the node itself as R-SEL-1 says ('return it'); the list form contradicts R-SEL-1. Which is meant?
11. **ambiguity** (R-OUT-2): "its index" can mean: the 0-based position of the plucked node in arr (as Examples 1, 2 and 4 show) / the 1-based position of the plucked node in arr. Which is meant?
12. **ambiguity** (R-EMP-1): "the given array is empty" can mean: an empty arr is a legal input and must return [] / an empty arr is excluded by the constraint 1 <= nodes.length (R-IN-2), so this clause is vacuous; contradicts R-IN-2. Which is meant?
13. **ambiguity** (R-EMP-1): "return []" can mean: return [] even though R-SEL-1 says a node is always plucked (this clause overrides R-SEL-1) / R-SEL-1 requires a node to be plucked for every input, contradicting this clause. Which is meant?
14. **ambiguity** (R-EMP-2): "no values" can mean: no node of arr has the value R-SEL-2 selects (e.g. no even value), so a non-empty arr can return []; seemingly contradicts R-SEL-1 ('pluck one of the nodes') / arr contains no elements, the same case as an empty array (R-EMP-1). Which is meant?
15. **ambiguity** (R-EX-2): "Output: [2, 1]" can mean: the example is authoritative: the selection rule must give [2, 1] here (e.g. smallest even value, R-SEL-2 reading 1) / the example is in error: under the smallest-value reading of R-SEL-2 the answer is [1, 0]; contradicts R-SEL-2 reading 2. Which is meant?
16. **ambiguity** (R-EX-3): "Input: []" can mean: the empty list is a legal input and the call must return [] / the empty list is excluded by the constraint 1 <= nodes.length (R-IN-2); contradicts R-IN-2. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-DEF-1, "a branch of a tree": both took "arr is a flat list of node values; the tree structure plays no role in the result"
- R-IN-2, "1 <= nodes.length": both took "the lower bound is stale or describes typical inputs only; an empty arr is a legal input that must return [] as R-EMP-1 and R-EX-3 say"
- R-IN-2, "nodes.length": both took "the length of arr"
- R-IN-3, "nodes.length": both took "the length of arr"
- R-IN-4, "node.value": both took "the integer element of arr itself"
- R-SEL-1, "pluck one of the nodes": both took "a node is plucked only when arr is non-empty and some node qualifies (R-SEL-2); otherwise [] is returned (R-EMP-1, R-EMP-2)"
- R-SEL-1, "return it": both took "return the plucked node in the form R-OUT-1 gives, the list [value, index]"
- R-SEL-1, "pluck": both took "select a node and leave arr unchanged"
- R-SEL-2, "the node with the value": both took "no criterion is given, so any node of arr may be plucked (only the examples constrain the choice)"
- R-SEL-3, "the value": both took "whatever value the plucked node has, under an unconstrained choice (as in R-SEL-2 reading 3)"
- R-SEL-3, "return the node": both took "return the node as the list [value, index] of R-OUT-1"
- R-OUT-1, "returned in a list, [ value, its index ]": both took "the result is the two-element list [value, index]"
- R-OUT-2, "its index": both took "the 0-based position of the plucked node in arr (as Examples 1, 2 and 4 show)"
- R-EMP-1, "the given array is empty": both took "an empty arr is a legal input and must return []"
- R-EMP-1, "return []": both took "return [] even though R-SEL-1 says a node is always plucked (this clause overrides R-SEL-1)"
- R-EMP-2, "no values": both took "arr contains no elements, the same case as an empty array (R-EMP-1)"
- R-EX-2, "Output: [2, 1]": both took "the example is authoritative: the selection rule must give [2, 1] here (e.g. smallest even value, R-SEL-2 reading 1)"
- R-EX-3, "Input: []": both took "the empty list is a legal input and the call must return []"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `all(i < len(arr): arr[i] >= 0)`
- agent_a, RA-IN-3 (R-IN-3): every call meets `len(arr) <= 10000`
- agent_a, RA-IN-4 (R-IN-4): every call meets `all(i < len(arr): arr[i] >= 0)`
- agent_b, RB-A-IN1 (R-IN-1): every call meets `all(i < len(arr): arr[i] >= 0)`
- agent_b, RB-A-IN3 (R-IN-3): every call meets `len(arr) <= 10000`
- agent_b, RB-A-IN4 (R-IN-4): every call meets `all(i < len(arr): arr[i] >= 0)`
