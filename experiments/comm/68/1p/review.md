# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 12.

## Questions
1. **open** (plucked): the request allows 0 or 9: which is meant?
   - `pluck([0, 9])`
2. **open** (plucked, outcome, R-OUT-1): the request allows `plucked` to be 0 or 1 (the reading leaves this free on purpose: RB-OUT-1-D2) and lets this call end in two ways, "returned" or "returned something else" (the reading leaves this free on purpose: RB-OUT-1-D1): is any answer acceptable, or which is meant?
   - `pluck([])`
3. **depends** (R-OUT-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `pluck([1, 1, 1, 3, 1, 1, 1, 3]) -> 2`
   - `pluck([1, 1, 1, 1, 1, 1, 1, 1]) -> 1`
4. **readings** (R-OUT-1): the two readings of this requirement disagree (no separating call was found within the budget): which is meant?
5. **readings** (R-OUT-2): the two readings of this requirement disagree (no separating call was found within the budget): which is meant?
6. **ambiguity** (R-OUT-1): "one of the nodes" can mean: Any node of arr is acceptable as the plucked node (no further selection rule). / A particular node is required, as the later sentence 'The plucked node should be the node' indicates; 'one of the nodes' only says it comes from arr.. Which is meant?
7. **ambiguity** (R-OUT-1): "pluck" can mean: Select the node without modifying arr. / Remove the node from arr (mutating the caller's list) as well as selecting it.. Which is meant?
8. **ambiguity** (R-OUT-1): "one of the nodes (when arr is empty)" can mean: An empty arr never occurs (see R-IN-2), so there is always a node to pluck. / For an empty arr no node can be plucked and the behaviour is unspecified (don't care). / For an empty arr the function must still terminate normally with some agreed result, which the prompt does not state.. Which is meant?
9. **ambiguity** (R-OUT-2): "return it" can mean: Return the node's integer value itself. / Return the node's position (index) in arr. / Return the node wrapped in a container (e.g. a list holding the value, possibly with other data).. Which is meant?
10. **ambiguity** (R-OUT-2): "it (when several nodes have the same value)" can mean: Only the value matters; any node with that value is equivalent. / The specific node (position) plucked matters, so equal values at different positions are distinguishable.. Which is meant?
11. **ambiguity** (R-SEL-1): "The plucked node should be the node" can mean: The sentence is incomplete and imposes no checkable rule; any node of arr satisfies it (selection is a don't care among the elements of arr). / A specific node is required but the criterion is missing, so the correct result cannot be determined from the prompt and the requirement is unformalizable. / Read as complete: the plucked node must be the same node that is returned (consistency between R-OUT-1 and R-OUT-2), adding no new constraint.. Which is meant?
12. **ambiguity** (R-SEL-1): "the node" can mean: A particular node is required, which contradicts 'pluck one of the nodes' if that means any node is acceptable. / Any node of arr is acceptable, consistent with 'pluck one of the nodes'; 'the node' just refers to the one chosen.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FN-1, "Complete this function": both took "Fill in the body below the given signature and docstring, keeping both unchanged."
- R-IN-1, "an array": both took "arr is a Python list."
- R-IN-1, "a branch of a tree": both took "Only descriptive: arr is a flat collection of node values and the tree imposes no constraint on it."
- R-OUT-1, "one of the nodes": both took "A particular node is required, as the later sentence 'The plucked node should be the node' indicates; 'one of the nodes' only says it comes from arr."
- R-OUT-2, "return it": both took "Return the node's integer value itself."
- R-OUT-2, "it (when several nodes have the same value)": both took "Only the value matters; any node with that value is equivalent."
- R-SEL-1, "The plucked node should be the node": both took "A specific node is required but the criterion is missing, so the correct result cannot be determined from the prompt and the requirement is unformalizable."
- R-SEL-1, "the node": both took "A particular node is required, which contradicts 'pluck one of the nodes' if that means any node is acceptable."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-2 (R-IN-2): every call meets `len(arr) >= 1`
- agent_b, RB-IN-2-VAL (R-IN-2): every call meets `all(i < len(arr): arr[i] >= 0)`
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_b, RB-OUT-1-D1 (R-OUT-1): `outcome` is free when `len(arr) == 0`
- agent_b, RB-OUT-1-D2 (R-OUT-1): `plucked` is free when `len(arr) == 0`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the comparison of agent_a and agent_b
