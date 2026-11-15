# FCP review

Before any code: the request alone.

Settled: 2 requirements. Questions: 10.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-PL-3: When the smallest even value of arr occurs at several positions, the returned index is the smallest position i with arr[i] equal to that value.
- R-EMP-1: When arr is non-empty and contains no even element, pluck returns the empty list [].

## Questions
1. **ambiguity** (R-PL-1): "return it" can mean: return the plucked node as the list [value, index], as the later sentence specifies / return the node's value alone (a bare integer). Which is meant?
2. **ambiguity** (R-PL-1): "pluck" can mean: only select and report the node; arr is left unchanged / remove the node from arr (mutate the argument) and return it. Which is meant?
3. **ambiguity** (R-PL-2): "the smallest even value" can mean: the smallest value among the even elements of arr (odd elements are ignored) / the smallest value of arr overall, which is plucked only if it is even. Which is meant?
4. **ambiguity** (R-OUT-1): "smalest_value" can mean: the smallest even value (the plucked node's value); 'smalest' is a typo of 'smallest' / the smallest value of arr overall, even if it is odd. Which is meant?
5. **ambiguity** (R-OUT-1): "its index" can mean: the 0-based position of the plucked node in arr (as Examples 1, 2 and 4 show) / the 1-based position of the plucked node in arr. Which is meant?
6. **ambiguity** (R-EMP-2): "the given array is empty" can mean: An empty arr is a valid call and pluck must return [] for it; the constraint '1 <= nodes.length' is not a real precondition. / Contradicted by the constraint '1 <= nodes.length': an empty arr is outside the precondition, so its result is unconstrained (don't care).. Which is meant?
7. **ambiguity** (R-EX-1): "2 has the smallest index" can mean: 2 has the smallest index among the nodes holding the smallest even value (it is the only one) / 2 has the smallest index in arr, which is false here because the even node 4 is at index 0; the explanation is misleading. Which is meant?
8. **ambiguity** (R-EX-2): "2 has the smallest even value, and 2 has the smallest index." can mean: 2 has the smallest index among the nodes holding the smallest even value (it is the only even node) / 2 has the smallest index in arr, which is false here because 1 is at index 0; the explanation is copied from Example 1. Which is meant?
9. **ambiguity** (R-EX-3): "Input: []" can mean: An empty arr is a valid call and pluck must return [] for it; the constraint '1 <= nodes.length' is not a real precondition. / Contradicted by the constraint '1 <= nodes.length': an empty arr is outside the precondition, so this example illustrates a don't-care case.. Which is meant?
10. **ambiguity** (R-EX-4): "0 is the smallest value" can mean: 0 is the smallest even value (it also happens to be the smallest value overall) / the node is chosen as the smallest value overall, suggesting the rule is about the overall minimum rather than the minimum even value. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-DEF-1, "an array representing a branch of a tree": both took "arr is just a flat sequence of node values; the tree structure plays no role in the result."
- R-IN-2, "1 <= nodes.length": both took "Contradicted by 'the given array is empty, return []' and Example 3: an empty arr is a valid call and pluck must return [] for it; the lower bound is not a real precondition."
- R-IN-2, "nodes.length": both took "the length of the argument arr"
- R-PL-1, "return it": both took "return the plucked node as the list [value, index], as the later sentence specifies"
- R-PL-1, "pluck": both took "only select and report the node; arr is left unchanged"
- R-PL-2, "the smallest even value": both took "the smallest value among the even elements of arr (odd elements are ignored)"
- R-OUT-1, "smalest_value": both took "the smallest even value (the plucked node's value); 'smalest' is a typo of 'smallest'"
- R-OUT-1, "its index": both took "the 0-based position of the plucked node in arr (as Examples 1, 2 and 4 show)"
- R-EMP-2, "the given array is empty": both took "An empty arr is a valid call and pluck must return [] for it; the constraint '1 <= nodes.length' is not a real precondition."
- R-EX-1, "2 has the smallest index": both took "2 has the smallest index among the nodes holding the smallest even value (it is the only one)"
- R-EX-2, "2 has the smallest even value, and 2 has the smallest index.": both took "2 has the smallest index among the nodes holding the smallest even value (it is the only even node)"
- R-EX-3, "Input: []": both took "An empty arr is a valid call and pluck must return [] for it; the constraint '1 <= nodes.length' is not a real precondition."
- R-EX-4, "0 is the smallest value": both took "0 is the smallest even value (it also happens to be the smallest value overall)"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `all(i < len(arr): arr[i] >= 0)`
- agent_a, RA-IN-3 (R-IN-3): every call meets `len(arr) <= 10000`
- agent_a, RA-IN-4 (R-IN-4): every call meets `all(i < len(arr): arr[i] >= 0)`
- agent_b, RB-IN-1 (R-IN-1): every call meets `all(i < len(arr): arr[i] >= 0)`
- agent_b, RB-IN-3 (R-IN-3): every call meets `len(arr) <= 10000`
- agent_b, RB-IN-4 (R-IN-4): every call meets `all(i < len(arr): arr[i] >= 0)`
