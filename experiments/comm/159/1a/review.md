# FCP review

Before any code: the request alone.

Settled: 2 requirements. Questions: 12.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-HUN-2: When the stock holds fewer carrots than the rabbit needs (remaining < need), no carrots are left in stock after the meal: the carrots left (second element under R-RET-3) are 0.
- R-EX-3: Calling eat(1, 10, 10) returns [11, 0]: having eaten 1 and needing 10 with exactly 10 in stock, the rabbit eats 10, for a total of 11, and none stay in stock.

## Questions
1. **depends** (R-RET-1, R-RET-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `eat(776, 1000, 1023) -> raised another exception or did not finish`
2. **ambiguity** (R-MEAL-1): "no or more carrots" can mean: 'zero or more': need is a non-negative count that may be 0, and the rabbit eats exactly need carrots when the stock allows (fits eat(5, 6, 10) -> [11, 4] and eat(4, 8, 9) -> [12, 1]) / 'need or more': need is only a minimum and the rabbit may eat more than need carrots when the stock allows. Which is meant?
3. **ambiguity** (R-RET-1): "an array" can mean: a Python list / any array-like sequence of two integers (list, tuple, array.array, ...). Which is meant?
4. **ambiguity** (R-RET-2): "needed or eaten" can mean: eaten: number + min(need, remaining), the carrots actually eaten (fits all four examples) / needed: number + need, regardless of the stock (fits eat(5, 6, 10), eat(4, 8, 9) and eat(1, 10, 10), but contradicts eat(2, 11, 5) -> [7, 0], which would give 13). Which is meant?
5. **ambiguity** (R-RET-2): "before or after your meals" can mean: after the meal: the count includes the carrots eaten in this meal (fits all four examples) / before the meal: the first element is number alone (contradicts every example, e.g. eat(5, 6, 10) would give 5, not 11). Which is meant?
6. **ambiguity** (R-RET-2): "total number" can mean: the total includes the carrots eaten before the meal (number) plus those eaten in it (fits all four examples) / only the carrots eaten in this meal, min(need, remaining) (contradicts every example, e.g. eat(5, 6, 10) would give 6, not 11). Which is meant?
7. **ambiguity** (R-RET-3): "needed or eaten left" can mean: carrots left in stock after the meal: max(remaining - need, 0) (fits all four examples) / carrots still needed after the meal: max(need - remaining, 0) (contradicts eat(5, 6, 10) -> [11, 4], eat(4, 8, 9) -> [12, 1] and eat(2, 11, 5) -> [7, 0], which would give 0, 0 and 6) / carrots eaten in the meal: min(need, remaining) (contradicts every example, e.g. eat(5, 6, 10) would give 6, not 4). Which is meant?
8. **ambiguity** (R-HUN-1): "not enough remaining carrots" can mean: remaining < need / remaining <= need (at remaining == need both readings give the same returned list). Which is meant?
9. **ambiguity** (R-HUN-3): "will still be hungry" can mean: narrative only: the returned list does not report the shortfall, and the second element stays the stock left, 0 / the returned list reports the unmet need need - remaining, e.g. as the second element (contradicts eat(2, 11, 5) -> [7, 0], which would then be [7, 6]). Which is meant?
10. **ambiguity** (R-EX-1): "[11, 4]" can mean: the second element is the stock left (10 - 6 = 4), as in reading 1 of R-RET-3 / the second element is the carrots still needed (reading 2 of R-RET-3), which would give [11, 0]: the example contradicts that reading. Which is meant?
11. **ambiguity** (R-EX-2): "[12, 1]" can mean: the second element is the stock left (9 - 8 = 1), as in reading 1 of R-RET-3 / the second element is the carrots still needed (reading 2 of R-RET-3), which would give [12, 0]: the example contradicts that reading. Which is meant?
12. **ambiguity** (R-EX-4): "[7, 0]" can mean: [total actually eaten, stock left] = [2 + 5, 0], as in reading 1 of R-RET-2 'needed or eaten', of R-RET-3 and of R-HUN-3 / the first element is the total needed (reading 2 of R-RET-2 'needed or eaten'), which would give 13: the example contradicts that reading / the second element is the carrots still needed, the unmet hunger of R-HUN-3 (reading 2 of R-RET-3 and of R-HUN-3), which would give 6: the example contradicts that reading. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-SIG-1, "x, y, z": both took "x is number (carrots already eaten), y is need (carrots to eat), z is remaining (carrots in stock): the docstring lists its variables in the signature's order, and this is the only order that fits eat(5, 6, 10) -> [11, 4]"
- R-MEAL-1, "no or more carrots": both took "'zero or more': need is a non-negative count that may be 0, and the rabbit eats exactly need carrots when the stock allows (fits eat(5, 6, 10) -> [11, 4] and eat(4, 8, 9) -> [12, 1])"
- R-RET-1, "an array": both took "a Python list"
- R-RET-2, "needed or eaten": both took "eaten: number + min(need, remaining), the carrots actually eaten (fits all four examples)"
- R-RET-2, "before or after your meals": both took "after the meal: the count includes the carrots eaten in this meal (fits all four examples)"
- R-RET-2, "total number": both took "the total includes the carrots eaten before the meal (number) plus those eaten in it (fits all four examples)"
- R-RET-3, "needed or eaten left": both took "carrots left in stock after the meal: max(remaining - need, 0) (fits all four examples)"
- R-HUN-1, "not enough remaining carrots": both took "remaining < need"
- R-HUN-3, "will still be hungry": both took "narrative only: the returned list does not report the shortfall, and the second element stays the stock left, 0"
- R-EX-1, "[11, 4]": both took "the second element is the stock left (10 - 6 = 4), as in reading 1 of R-RET-3"
- R-EX-2, "[12, 1]": both took "the second element is the stock left (9 - 8 = 1), as in reading 1 of R-RET-3"
- R-EX-4, "[7, 0]": both took "[total actually eaten, stock left] = [2 + 5, 0], as in reading 1 of R-RET-2 'needed or eaten', of R-RET-3 and of R-HUN-3"
- R-VAR-1, "@number": both took "number is x, the first parameter (docstring order; the only order that fits eat(5, 6, 10) -> [11, 4])"
- R-VAR-2, "@need": both took "need is y, the second parameter (docstring order; the only order that fits eat(5, 6, 10) -> [11, 4])"
- R-VAR-3, "@remaining": both took "remaining is z, the third parameter (docstring order; the only order that fits eat(5, 6, 10) -> [11, 4])"
- R-CON-1, "0 <= number <= 1000": both took "a precondition on the caller: for number outside 0..1000 (e.g. 1001 to 1023 in the trace) any behaviour is acceptable"
- R-CON-2, "0 <= need <= 1000": both took "a precondition on the caller: for need outside 0..1000 (e.g. 1001 to 1023 in the trace) any behaviour is acceptable"
- R-CON-3, "0 <= remaining <= 1000": both took "a precondition on the caller: for remaining outside 0..1000 (e.g. 1001 to 1023 in the trace) any behaviour is acceptable"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-CON-1 (R-CON-1): every call meets `number <= 1000`; `number` is `x`
- agent_a, RA-CON-2 (R-CON-2): every call meets `need <= 1000`; `need` is `y`
- agent_a, RA-CON-3 (R-CON-3): every call meets `remaining <= 1000`; `remaining` is `z`
- agent_b, RB-A-CON-1 (R-CON-1): every call meets `number <= 1000`; `number` is `x`
- agent_b, RB-A-CON-2 (R-CON-2): every call meets `need <= 1000`; `need` is `y`
- agent_b, RB-A-CON-3 (R-CON-3): every call meets `remaining <= 1000`; `remaining` is `z`
- agent_b, RB-D-CON-1-OUT (R-CON-1): `outcome` is free when `number > 1000`; `number` is `x`
- agent_b, RB-D-CON-1-RES (R-CON-1): `result` is free when `number > 1000`; `number` is `x`
- agent_b, RB-D-CON-2-OUT (R-CON-2): `outcome` is free when `need > 1000`; `need` is `y`
- agent_b, RB-D-CON-2-RES (R-CON-2): `result` is free when `need > 1000`; `need` is `y`
- agent_b, RB-D-CON-3-OUT (R-CON-3): `outcome` is free when `remaining > 1000`; `remaining` is `z`
- agent_b, RB-D-CON-3-RES (R-CON-3): `result` is free when `remaining > 1000`; `remaining` is `z`
