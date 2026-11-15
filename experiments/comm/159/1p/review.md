# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 5.

## Questions
1. **open** (result, outcome, R-OUT-1): the request allows `result` to be [] or [0] (the reading leaves this free on purpose: RA-D-RESULT) and lets this call end in two ways, "returned" or "returned something else" (the reading leaves this free on purpose: RA-D-OUTCOME): is any answer acceptable, or which is meant?
   - `eat(0, 1, 0)`
2. **ambiguity** (R-API-1): "eat(number, need, remaining)" can mean: The three arguments are integers (counts of carrots). / The arguments may be any numbers, including non-integers.. Which is meant?
3. **ambiguity** (R-EAT-1): "eat more carrots" can mean: The rabbit eats exactly need more carrots. / The rabbit eats up to need more carrots, limited by the carrots that remain (min(need, remaining)). / The rabbit eats at least need more carrots (a hungry rabbit may eat beyond its need). / Context only: the sentence describes the situation and places no obligation on the result.. Which is meant?
4. **ambiguity** (R-EAT-2): "to complete" can mean: After the call the day's meals are always complete: the rabbit has eaten all it needed. / This is only the purpose of eating; the meals are complete only when enough carrots are available.. Which is meant?
5. **ambiguity** (R-EAT-2): "complete the day's meals" can mean: Contradiction with R-DEF-3: if remaining is the stock available, the meals cannot be completed when remaining is less than need, yet this says the rabbit eats to complete them. / No contradiction: remaining does not limit what the rabbit eats, so the meals can always be completed.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-TASK-1, "Complete this function": both took "Only the body is to be written; the signature and docstring stay exactly as given."
- R-API-1, "eat(number, need, remaining)": both took "The three arguments are integers (counts of carrots)."
- R-CTX-1, "hungry rabbit": both took "Narrative framing only; it places no obligation on the result."
- R-DEF-1, "a certain number of carrots": both took "This count is the argument number."
- R-DEF-1, "already have eaten": both took "Carrots eaten so far today, counting toward the day's meals."
- R-DEF-2, "need to eat more carrots": both took "need is the number of additional carrots still to be eaten, on top of number."
- R-DEF-3, "remaining": both took "Not described, so its meaning and its effect on the result are left free."
- R-DEF-3, "need, remaining": both took "No contradiction: remaining does not limit what the rabbit eats, so the meals can always be completed."
- R-ENV-1, "a certain number": both took "Any non-negative integer, with no upper bound."
- R-ENV-2, "need to eat more carrots": both took "need is at least 1, since the rabbit needs more carrots."
- R-EAT-2, "complete the day's meals": both took "No contradiction: remaining does not limit what the rabbit eats, so the meals can always be completed."
- R-OUT-1, "complete the day's meals.": both took "The return value is unconstrained: the docstring names no result."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-ENV-1 (R-ENV-1): every call meets `number >= 0`
- agent_a, RA-ENV-2 (R-ENV-2): every call meets `need >= 1`
- agent_a, RA-ENV-3 (R-ENV-3): every call meets `remaining >= 0`
- agent_b, RB-ENV-1 (R-ENV-1): every call meets `already_eaten >= 0`; `already_eaten` is `number`
- agent_b, RB-ENV-2 (R-ENV-2): every call meets `more_needed >= 1`; `more_needed` is `need`
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-D-RESULT (R-OUT-1): `result` is free when `true`
- agent_a, RA-D-OUTCOME (R-OUT-1): `outcome` is free when `true`
- agent_b, RB-OUT-1 (R-OUT-1): `result` is free when `outcome == 0`
