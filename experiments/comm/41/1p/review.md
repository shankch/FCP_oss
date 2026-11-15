# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 3.

## Questions
1. **open** (result, outcome, R-FN-1): the request allows `result` to be 0 or 1 (the reading leaves this free on purpose: RA-FN-1-VAL) and lets this call end in two ways, "returned" or "returned something else": is any answer acceptable, or which is meant?
   - `candidate(0)`
2. **depends** (R-FN-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate(256) -> 0`
3. **ambiguity** (R-FN-1): "Complete this function" can mean: return the number of collisions between the left-to-right cars and the right-to-left cars, the quantity the truncated docstring leads up to / the request never states what the function returns (the docstring stops mid-sentence), so any returned value is acceptable / also finish the truncated docstring, not only the function body. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FN-1, "Complete this function": both took "the request never states what the function returns (the docstring stops mid-sentence), so any returned value is acceptable"
- R-CAR-1, "n cars": both took "n is any non-negative count; n = 0 means there are no cars in either set"
- R-CAR-2, "simultaneously": both took "both sets are moving during the same period of time"
- R-CAR-2, "driving right to left": both took "the second set moves in the opposite direction to the first set, at the same speed magnitude (consistent with R-CAR-4)"
- R-CAR-3, "very far from each other": both took "the two sets start a large distance apart, but no ordering of their positions (which set is on which side) is implied"
- R-CAR-4, "the same speed": both took "every car has the same speed magnitude, the two sets moving in opposite directions"
- R-CAR-4, "move in the same speed": both took "all cars share the same speed at each instant, but that speed may change over time"
- R-COL-1, "Two cars are said to collide": both took "the condition is missing, so collision is undefined and nothing about it can be checked"
- R-COL-1, "collide": both took "cars that collide stop or are removed, so later cars may hit the wreck or pass freely"

## Taken as given
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-FN-1-VAL (R-FN-1): `result` is free when `outcome == 0`
- agent_b, RB-FN-1-D (R-FN-1): `result` is free when `outcome == 0`
