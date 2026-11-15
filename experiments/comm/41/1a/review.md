# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 4.

## Questions
1. **open** (collisions): the request allows 2 or 4: which is meant?
   - `car_race_collision(1)`
2. **ambiguity** (R-OUT-1): "outputs" can mean: returns the number of collisions as an int / prints the number of collisions; the return value is unspecified. Which is meant?
3. **ambiguity** (R-OUT-2): "the number of such collisions" can mean: n*n (n cars in each direction) / 4*n*n (2*n cars in each direction) / 2*n*n (2*n cars in one direction and n in the other) / any of n*n, 2*n*n or 4*n*n is acceptable, since the car counts are given as alternatives. Which is meant?
4. **ambiguity** (R-OUT-2): "the number" can mean: a single number determined by n, so one fixed car count must be meant (R-CAR-1, R-CAR-2) / the car counts are left open (R-CAR-1, R-CAR-2), which contradicts there being one number of collisions for each n. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-ENV-1, "n: int": both took "n is a car count, so only n >= 0 is meant and negative n is outside the specification"
- R-CAR-1, "2*n or n cars": both took "the count is left open: either n or 2*n cars, at the implementer's choice"
- R-CAR-1, "2*n or n": both took "the count is genuinely open, which contradicts the function outputting one determined number of collisions for each n (R-OUT-2)"
- R-CAR-2, "2*n or n cars": both took "the count is left open: either n or 2*n cars, at the implementer's choice"
- R-CAR-2, "a different set": both took "a disjoint set of cars (no car is in both sets); its size is independent of the first set's choice and may equal it"
- R-CAR-2, "2*n or n": both took "the count is genuinely open, which contradicts the function outputting one determined number of collisions for each n (R-OUT-2)"
- R-POS-1, "start out being very far from each other": both took "the left-to-right set starts entirely to the left of the right-to-left set, so the sets approach and every opposing pair of cars meets"
- R-COL-1, "said to collide": both took "a meeting of opposite-direction cars counts as a collision even though both cars continue unaffected (R-COL-2)"
- R-COL-2, "as if they did not collide": both took "only the motion is unaffected; the collision still happened and is counted (R-COL-1)"
- R-OUT-1, "outputs": both took "returns the number of collisions as an int"
- R-OUT-2, "the number of such collisions": both took "any of n*n, 2*n*n or 4*n*n is acceptable, since the car counts are given as alternatives"
- R-OUT-2, "the number": both took "the car counts are left open (R-CAR-1, R-CAR-2), which contradicts there being one number of collisions for each n"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-ENV-1 (R-ENV-1): every call meets `n >= 0`
- agent_b, RB-ENV-1 (R-ENV-1): every call meets `n >= 0`
