# FCP review

Before any code: the request alone.

Settled: 4 requirements. Questions: 6.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: The call eat(5, 6, 10) returns [11, 4] (enough carrots in stock).
- R-EX-2: The call eat(4, 8, 9) returns [12, 1] (enough carrots in stock).
- R-EX-3: The call eat(1, 10, 10) returns [11, 0] (stock exactly equals need).
- R-EX-4: The call eat(2, 11, 5) returns [7, 0] (not enough carrots in stock).

## Questions
1. **depends** (R-RET-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `eat(0, 1, 0) -> returned something else`
2. **ambiguity** (R-RET-1): "array" can mean: a Python list / a list or a tuple / any array-like sequence, such as array.array or a numpy array. Which is meant?
3. **ambiguity** (R-RET-1): "return an array of [ total number of eaten carrots after your meals, the number of carrots left after your meals ]" can mean: exactly these two elements are returned and nothing else; that the rabbit is still hungry (R-EAT-5) is not reported separately / the result must also report that the rabbit is still hungry (R-EAT-5), which contradicts returning exactly two elements. Which is meant?
4. **ambiguity** (R-EAT-1, R-EAT-2): "you need to eat more carrots" can mean: when there are enough carrots the rabbit eats exactly need carrots, no more (the examples follow this reading) / the rabbit eats at least need carrots and may eat more, e.g. all remaining carrots. Which is meant?
5. **ambiguity** (R-EAT-3, R-EAT-4): "not enough remaining carrots" can mean: remaining < need / remaining <= need (gives the same result when remaining == need). Which is meant?
6. **ambiguity** (R-EAT-5): "but will still be hungry" can mean: narrative only: it follows from eating fewer than need carrots and is not reported by any extra element / the result must report that the rabbit is still hungry (a flag or the shortfall), which contradicts returning exactly two elements (R-RET-1). Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-DEF-2, "the number of carrots that you need to eat": both took "need is the number of additional carrots to eat on top of the number already eaten (the examples, e.g. eat(5, 6, 10) -> [11, 4], follow this reading)"
- R-RET-1, "return an array of [ total number of eaten carrots after your meals, the number of carrots left after your meals ]": both took "exactly these two elements are returned and nothing else; that the rabbit is still hungry (R-EAT-5) is not reported separately"
- R-RET-2, "total number of eaten carrots": both took "number plus the carrots eaten in this call (the examples follow this reading)"
- R-RET-3, "the number of carrots left": both took "the carrots left in stock: remaining minus the carrots eaten in this call (the examples follow this reading)"
- R-EAT-1, "you need to eat more carrots": both took "when there are enough carrots the rabbit eats exactly need carrots, no more (the examples follow this reading)"
- R-EAT-2, "you need to eat more carrots": both took "when there are enough carrots the rabbit eats exactly need carrots, no more (the examples follow this reading)"
- R-EAT-3, "not enough remaining carrots": both took "remaining < need"
- R-EAT-4, "not enough remaining carrots": both took "remaining < need"
- R-EAT-5, "but will still be hungry": both took "narrative only: it follows from eating fewer than need carrots and is not reported by any extra element"
- R-IN-1, "Constrain": both took "a precondition the caller meets; behaviour for number outside 0..1000 is unspecified"
- R-IN-2, "Constrain": both took "a precondition the caller meets; behaviour for need outside 0..1000 is unspecified"
- R-IN-3, "Constrain": both took "a precondition the caller meets; behaviour for remaining outside 0..1000 is unspecified"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `number <= 1000`
- agent_a, RA-IN-2 (R-IN-2): every call meets `need <= 1000`
- agent_a, RA-IN-3 (R-IN-3): every call meets `remaining <= 1000`
- agent_b, RB-IN-1 (R-IN-1): every call meets `number <= 1000`
- agent_b, RB-IN-2 (R-IN-2): every call meets `need <= 1000`
- agent_b, RB-IN-3 (R-IN-3): every call meets `remaining <= 1000`
