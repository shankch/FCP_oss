# FCP review

Before any code: the request alone.

Settled: 2 requirements. Questions: 7.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-BASE-1: fib4(0) returns 0.
- R-BASE-2: fib4(1) returns 0.

## Questions
1. **open** (result, outcome, R-NTH-1): the request allows `result` to be 0 or 1 (the reading leaves this free on purpose: RA-NTH-2) and lets this call end in two ways, "returned" or "raised another exception or did not finish" (the reading leaves this free on purpose: RA-NTH-3): is any answer acceptable, or which is meant?
   - `fib4(4)`
2. **depends** (R-NTH-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `fib4(6) -> 0`
3. **ambiguity** (R-BASE-3): "fib4(2) -> 2" can mean: fib4(2) is a starting value of the sequence: fib4(2) returns 2, and the Fibonacci-like rule of R-SEQ-1 does not apply to it / the Fibonacci rule of R-SEQ-1 applies from fib4(2) on (each element the sum of the two before it), so fib4(2) would be fib4(1) + fib4(0) = 0, which contradicts the listed value 2. Which is meant?
4. **ambiguity** (R-BASE-4): "fib4(3) -> 0" can mean: fib4(3) is a starting value of the sequence: fib4(3) returns 0, and the Fibonacci-like rule of R-SEQ-1 does not apply to it / the Fibonacci rule of R-SEQ-1 applies from fib4(2) on (each element the sum of the two before it), so fib4(3) would be fib4(2) + fib4(1) = 2, which contradicts the listed value 0. Which is meant?
5. **ambiguity** (R-NTH-1): "n-th element" can mean: elements are counted from 0, as in the list: fib4(n) returns the element the list writes as fib4(n), so fib4(0) is the 0th element / elements are counted from 1: the first element is the one written fib4(0), so fib4(n) returns the element written fib4(n-1) and fib4(0) has no element; this conflicts with the listed values read as calls (fib4(2) would return 0, not 2). Which is meant?
6. **ambiguity** (R-NTH-1): "the fib4 number sequence" can mean: the sequence extends to every n through the Fibonacci-like rule of R-SEQ-1, so the n-th element exists and must be returned for every n / the sequence is only what R-SEQ-1 lists, fib4(0) to fib4(3), so for n >= 4 there is no n-th element and the result is unconstrained; this contradicts the request to compute the n-th element for every n. Which is meant?
7. **ambiguity** (R-NTH-1): "compute" can mean: fib4 returns the element as a Python int (the declared return type is left out, but the elements are integers) / fib4 may return any number equal to the element, so a float such as 2.0 also meets the requirement. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IF-1, "n: int": both took "n may be any integer, negative ones included; the prompt defines no element for a negative n, so what fib4 does for n < 0 is left open"
- R-SEQ-1, "similar to the Fibbonacci sequnece": both took "only a resemblance is claimed and no rule is given: the four listed values are the whole definition, the elements after fib4(3) are not defined and fib4(n) for n >= 4 is unconstrained; this contradicts R-NTH-1, which asks for the n-th element for every n"
- R-BASE-3, "fib4(2) -> 2": both took "fib4(2) is a starting value of the sequence: fib4(2) returns 2, and the Fibonacci-like rule of R-SEQ-1 does not apply to it"
- R-BASE-4, "fib4(3) -> 0": both took "fib4(3) is a starting value of the sequence: fib4(3) returns 0, and the Fibonacci-like rule of R-SEQ-1 does not apply to it"
- R-NTH-1, "n-th element": both took "elements are counted from 0, as in the list: fib4(n) returns the element the list writes as fib4(n), so fib4(0) is the 0th element"
- R-NTH-1, "the fib4 number sequence": both took "the sequence is only what R-SEQ-1 lists, fib4(0) to fib4(3), so for n >= 4 there is no n-th element and the result is unconstrained; this contradicts the request to compute the n-th element for every n"
- R-NTH-1, "compute": both took "fib4 returns the element as a Python int (the declared return type is left out, but the elements are integers)"
- R-NF-2, "recursion": both took "no function of the implementation may call itself, directly or indirectly; this covers fib4, any helper and memoized recursion (e.g. functools.lru_cache)"

## Taken as given
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-NTH-2 (R-NTH-1): `result` is free when `n >= 4`
- agent_a, RA-NTH-3 (R-NTH-1): `outcome` is free when `n >= 4`
- agent_b, RB-NTH-2 (R-NTH-1): `result` is free when `!listed`; `listed` is `n <= 3`
- agent_b, RB-NTH-3 (R-NTH-1): `outcome` is free when `!listed`; `listed` is `n <= 3`
