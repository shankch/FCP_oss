# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 2.

## Questions
1. **ambiguity** (R-OUT-1): "outputs" can mean: returns the number as the function's return value / prints the number (to standard output). Which is meant?
2. **ambiguity** (R-OUT-1): "the number of such collisions" can mean: the total count of collision events between pairs of one left-to-right car and one right-to-left car over all time (each such pair meets once, so n * n) / the number of collisions under a different count of meetings (for example none, if the sets never approach each other, or one per car, n), depending on how R-CARS-3 and R-COL-1 are read. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-CARS-2, "simultaneously": both took "both sets of cars are on the road and moving during the same period of time"
- R-CARS-3, "start out being very far from each other": both took "every left-to-right car starts to the left of every right-to-left car, so the two sets approach each other and every left-to-right car eventually meets every right-to-left car"
- R-CARS-3, "very far": both took "far enough that no collision has happened before the start, but at a finite distance, so all meetings happen in finite time"
- R-CARS-4, "the same speed": both took "one constant speed shared by all cars for all time"
- R-COL-1, "Two cars are said to collide when a car that's moving left to right hits a car that's moving right to left": both took "every meeting of a left-to-right car with a right-to-left car counts as a collision, even though neither car is affected by it"
- R-COL-1, "collide": both took "each pair of one left-to-right car and one right-to-left car collides at most once"
- R-COL-2, "as if they did not collide": both took "the cars pass through each other unchanged, and the meeting is still counted as a collision (R-COL-1)"
- R-OUT-1, "outputs": both took "returns the number as the function's return value"
- R-OUT-1, "the number of such collisions": both took "the total count of collision events between pairs of one left-to-right car and one right-to-left car over all time (each such pair meets once, so n * n)"
