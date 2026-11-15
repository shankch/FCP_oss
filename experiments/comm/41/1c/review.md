# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 4.

## Questions
1. **depends** (R-OUT-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `is_prime(25) -> returned something else`
2. **ambiguity** (R-OUT-1): "This function outputs the number of such collisions" can mean: is_prime(n) returns the collision count for n cars in each set; the docstring governs and the name is_prime is a misnomer. / is_prime(n) decides whether n is prime and returns a bool, as its name says (R-FN-2); this sentence then contradicts the function's name.. Which is meant?
3. **ambiguity** (R-OUT-1): "outputs" can mean: The count is the function's return value (an int). / The count is printed (e.g. to standard output); the return value is not specified.. Which is meant?
4. **ambiguity** (R-OUT-1): "the number of such collisions" can mean: The number of (left-to-right car, right-to-left car) pairs that meet over the whole, unbounded duration of the scenario; with the sets approaching each other (R-CAR-3 reading 1) and cars passing through (R-COL-2), every pair meets exactly once, giving n*n. / The number of distinct collision events, where several cars meeting at the same point at the same time count as a single collision.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FN-2, "is_prime": both took "is_prime is only the function's name; its behaviour is the collision count described by the docstring (R-OUT-1), and the name is a misnomer."
- R-CAR-3, "very far from each other": both took "Every left-to-right car starts to the left of every right-to-left car, so the two sets approach each other and every pair of oppositely moving cars eventually meets."
- R-OUT-1, "This function outputs the number of such collisions": both took "is_prime(n) returns the collision count for n cars in each set; the docstring governs and the name is_prime is a misnomer."
- R-OUT-1, "outputs": both took "The count is the function's return value (an int)."
- R-OUT-1, "the number of such collisions": both took "The number of (left-to-right car, right-to-left car) pairs that meet over the whole, unbounded duration of the scenario; with the sets approaching each other (R-CAR-3 reading 1) and cars passing through (R-COL-2), every pair meets exactly once, giving n*n."
