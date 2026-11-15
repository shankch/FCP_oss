# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 19.

## Questions
1. **conflict** (R-EX-2, R-LEFT-1): no implementation can meet these requirements on these calls: which one gives way?
   - `eat(4, 8, 9)`
2. **conflict** (R-EX-3, R-LEFT-1): no implementation can meet these requirements on these calls: which one gives way?
   - `eat(1, 10, 10)`
3. **conflict** (R-EX-1, R-LEFT-1): no implementation can meet these requirements on these calls: which one gives way?
   - `eat(5, 6, 10)`
4. **conflict** (R-EX-4, R-LEFT-2): no implementation can meet these requirements on these calls: which one gives way?
   - `eat(2, 11, 5)`
5. **scenario** (R-EX-1): the behaviour RA-EX-1 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
6. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
7. **scenario** (R-EX-3): the behaviour RA-EX-3 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
8. **scenario** (R-EX-4): the behaviour RA-EX-4 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
9. **depends** (R-HUN-1, R-LEFT-1, R-RET-1, R-TOT-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `eat(0, 1, 1) -> [1, 0]`
10. **ambiguity** (R-RET-1): "an array" can mean: A Python list (the adapter records only a list as outcome 0). / Any two-element sequence, such as a tuple, would do.. Which is meant?
11. **ambiguity** (R-TOT-1): "total number of eaten carrots" can mean: The carrots eaten before the call (number) plus the carrots eaten in these meals: number + need (the examples follow this reading). / Only the carrots eaten in these meals: need.. Which is meant?
12. **ambiguity** (R-TOT-1): "the number of carrots that you need to eat" can mean: need is additional to number, so the first element is number + need. / need is the day's total, so the first element is max(number, need).. Which is meant?
13. **ambiguity** (R-TOT-2): "total number of eaten carrots" can mean: The carrots eaten before the call plus those eaten in these meals: number + remaining (eat(2, 11, 5) -> [7, 5] follows this reading). / Only the carrots eaten in these meals: remaining.. Which is meant?
14. **ambiguity** (R-LEFT-1): "the number of carrots left after your meals" can mean: The stock after eating: remaining - need. Under this reading the examples eat(5, 6, 10) -> [11, 10], eat(4, 8, 9) -> [12, 9] and eat(1, 10, 10) -> [11, 10] are wrong; they would be [11, 4], [12, 1] and [11, 0] (contradiction with R-EX-1, R-EX-2, R-EX-3). / The remaining argument unchanged, as all three of those examples show, so the second element is remaining (contradicting the literal prose 'left after your meals').. Which is meant?
15. **ambiguity** (R-LEFT-2): "you will eat all remaining carrots" can mean: No carrots are left after the meals, so the second element is 0. Under this reading the example eat(2, 11, 5) -> [7, 5] is wrong; it would be [7, 0] (contradiction with R-EX-4). / The second element is the remaining argument unchanged, as eat(2, 11, 5) -> [7, 5] shows, even though all of it is eaten.. Which is meant?
16. **ambiguity** (R-EX-1): "eat(5, 6, 10) -> [11, 10]" can mean: Binding as written: the second element is 10, the stock before the meals (contradicts R-LEFT-1, which gives 10 - 6 = 4). / The second element is an error; following R-LEFT-1 the intended result is [11, 4].. Which is meant?
17. **ambiguity** (R-EX-2): "eat(4, 8, 9) -> [12, 9]" can mean: Binding as written: the second element is 9, the stock before the meals (contradicts R-LEFT-1, which gives 9 - 8 = 1). / The second element is an error; following R-LEFT-1 the intended result is [12, 1].. Which is meant?
18. **ambiguity** (R-EX-3): "eat(1, 10, 10) -> [11, 10]" can mean: Binding as written: the second element is 10, the stock before the meals (contradicts R-LEFT-1, which gives 10 - 10 = 0). / The second element is an error; following R-LEFT-1 the intended result is [11, 0].. Which is meant?
19. **ambiguity** (R-EX-4): "eat(2, 11, 5) -> [7, 5]" can mean: Binding as written: the second element is 5, the stock before the meals (contradicts R-LEFT-2, which gives 0 because all remaining carrots are eaten). / The second element is an error; following R-LEFT-2 the intended result is [7, 0].. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-CTX-1, "you need to eat more carrots": both took "When enough carrots are in stock, the rabbit eats exactly `need` further carrots."
- R-DEF-2, "the number of carrots that you need to eat": both took "need is the number of additional carrots to eat on top of the number already eaten (the examples, e.g. eat(5, 6, 10) -> [11, 10], follow this reading)."
- R-RET-1, "an array": both took "A Python list (the adapter records only a list as outcome 0)."
- R-TOT-1, "total number of eaten carrots": both took "The carrots eaten before the call (number) plus the carrots eaten in these meals: number + need (the examples follow this reading)."
- R-TOT-1, "the number of carrots that you need to eat": both took "need is additional to number, so the first element is number + need."
- R-TOT-2, "total number of eaten carrots": both took "The carrots eaten before the call plus those eaten in these meals: number + remaining (eat(2, 11, 5) -> [7, 5] follows this reading)."
- R-LEFT-1, "the number of carrots left after your meals": both took "The stock after eating: remaining - need. Under this reading the examples eat(5, 6, 10) -> [11, 10], eat(4, 8, 9) -> [12, 9] and eat(1, 10, 10) -> [11, 10] are wrong; they would be [11, 4], [12, 1] and [11, 0] (contradiction with R-EX-1, R-EX-2, R-EX-3)."
- R-LEFT-2, "you will eat all remaining carrots": both took "No carrots are left after the meals, so the second element is 0. Under this reading the example eat(2, 11, 5) -> [7, 5] is wrong; it would be [7, 0] (contradiction with R-EX-4)."
- R-HUN-1, "will still be hungry": both took "Narrative only: it imposes no obligation on the returned list beyond the two elements."
- R-EX-1, "eat(5, 6, 10) -> [11, 10]": both took "Binding as written: the second element is 10, the stock before the meals (contradicts R-LEFT-1, which gives 10 - 6 = 4)."
- R-EX-2, "eat(4, 8, 9) -> [12, 9]": both took "Binding as written: the second element is 9, the stock before the meals (contradicts R-LEFT-1, which gives 9 - 8 = 1)."
- R-EX-3, "eat(1, 10, 10) -> [11, 10]": both took "Binding as written: the second element is 10, the stock before the meals (contradicts R-LEFT-1, which gives 10 - 10 = 0)."
- R-EX-4, "eat(2, 11, 5) -> [7, 5]": both took "Binding as written: the second element is 5, the stock before the meals (contradicts R-LEFT-2, which gives 0 because all remaining carrots are eaten)."
- R-ENV-1, "0 <= number <= 1000": both took "A precondition on callers: the behaviour for number outside 0..1000 is unspecified."
- R-ENV-2, "0 <= need <= 1000": both took "A precondition on callers: the behaviour for need outside 0..1000 is unspecified."
- R-ENV-3, "0 <= remaining <= 1000": both took "A precondition on callers: the behaviour for remaining outside 0..1000 is unspecified."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-ENV-1 (R-ENV-1): every call meets `number <= 1000`
- agent_a, RA-ENV-2 (R-ENV-2): every call meets `need <= 1000`
- agent_a, RA-ENV-3 (R-ENV-3): every call meets `remaining <= 1000`
- agent_b, RB-ENV-1 (R-ENV-1): every call meets `number <= 1000`
- agent_b, RB-ENV-2 (R-ENV-2): every call meets `need <= 1000`
- agent_b, RB-ENV-3 (R-ENV-3): every call meets `remaining <= 1000`
- agent_b, RB-ENV-1-DO (R-ENV-1): `outcome` is free when `number > 1000`
- agent_b, RB-ENV-1-DR (R-ENV-1): `result` is free when `number > 1000`
- agent_b, RB-ENV-2-DO (R-ENV-2): `outcome` is free when `need > 1000`
- agent_b, RB-ENV-2-DR (R-ENV-2): `result` is free when `need > 1000`
- agent_b, RB-ENV-3-DO (R-ENV-3): `outcome` is free when `remaining > 1000`
- agent_b, RB-ENV-3-DR (R-ENV-3): `result` is free when `remaining > 1000`
