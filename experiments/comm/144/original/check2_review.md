# FCP review

Before any code: the request alone.

Settled: 3 requirements. Questions: 8.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: simplify("1/5", "5/1") returns True (1/5 * 5/1 = 1).
- R-EX-2: simplify("1/6", "2/1") returns False (1/6 * 2/1 = 1/3).
- R-EX-3: simplify("7/10", "10/2") returns False (7/10 * 10/2 = 7/2).

## Questions
1. **depends** (R-RET-1, R-RET-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
2. **ambiguity** (R-RET-1): "whole number" can mean: A non-negative integer (0, 1, 2, ...). / A positive integer (1, 2, 3, ...), so a product of 0 is not a whole number. / Any integer, including negative ones.. Which is meant?
3. **ambiguity** (R-RET-1): "evaluates to" can mean: The exact rational value of the product is an integer. / The product computed in floating point is integral, which can differ from the exact answer for large numerators and denominators.. Which is meant?
4. **ambiguity** (R-RET-1): "returns True" can mean: Returns the Python bool True. / Returns any truthy value (for example the integer 1).. Which is meant?
5. **ambiguity** (R-RET-1): "returns True if x * n evaluates to a whole number" can mean: The function returns a bool answer; "simplify the expression" in R-FN-1 only states the purpose. / Contradicts R-FN-1 if "simplify the expression x * n" requires the function to produce the simplified product rather than a bool.. Which is meant?
6. **ambiguity** (R-RET-2): "otherwise" can mean: Only for valid inputs whose product is not a whole number; behaviour on invalid inputs is not constrained. / In every other case, including inputs that are not valid fractions, the function returns False (and does not raise).. Which is meant?
7. **ambiguity** (R-RET-2): "False" can mean: Returns the Python bool False. / Returns any falsy value (for example 0 or None).. Which is meant?
8. **ambiguity** (R-RET-2): "False otherwise" can mean: The function returns a bool answer; "simplify the expression" in R-FN-1 only states the purpose. / Contradicts R-FN-1 if "simplify the expression x * n" requires the function to produce the simplified product rather than a bool.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FN-1, "simplify the expression x * n": both took "A statement of purpose only: the observable obligation is the True/False answer of R-RET-1 and R-RET-2."
- R-DEF-1, "x * n": both took "The arithmetic product of the fraction values represented by x and n."
- R-RET-1, "whole number": both took "A non-negative integer (0, 1, 2, ...)."
- R-RET-1, "evaluates to": both took "The exact rational value of the product is an integer."
- R-RET-1, "returns True": both took "Returns the Python bool True."
- R-RET-1, "returns True if x * n evaluates to a whole number": both took "The function returns a bool answer; "simplify the expression" in R-FN-1 only states the purpose."
- R-RET-2, "otherwise": both took "Only for valid inputs whose product is not a whole number; behaviour on invalid inputs is not constrained."
- R-RET-2, "False": both took "Returns the Python bool False."
- R-RET-2, "False otherwise": both took "The function returns a bool answer; "simplify the expression" in R-FN-1 only states the purpose."
- R-IN-2, "<numerator>/<denominator>": both took "Exactly two decimal digit strings separated by a single "/", with no spaces, signs or leading zeros."
- R-IN-2, "have the following format": both took "A promise by the caller: inputs of any other form need not be handled."
- R-IN-3, "positive whole numbers": both took "An integer of at least 1, written in decimal digits."
- R-IN-4, "positive whole numbers": both took "An integer of at least 1, written in decimal digits."
- R-IN-5, "valid fractions": both took "Strings of the format <numerator>/<denominator> with positive whole numerator and denominator (R-IN-2, R-IN-3, R-IN-4)."
- R-IN-5, "You can assume": both took "The behaviour on arguments that are not valid fractions is unconstrained (any result or exception)."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-2 (R-IN-2): every call meets `fx && fn`; `fx` is `count(i < len(x): x[i] == "/") == 1 && all(i < len(x): x[i] == "/" || isdigit(x[i])) && sx >= 1 && sx + 1 < len(x) && !(sx > 1 && x[0] == "0") && !(len(x) - sx > 2 && x[sx + 1] == "0")`; `fn` is `count(i < len(n): n[i] == "/") == 1 && all(i < len(n): n[i] == "/" || isdigit(n[i])) && sn >= 1 && sn + 1 < len(n) && !(sn > 1 && n[0] == "0") && !(len(n) - sn > 2 && n[sn + 1] == "0")`
- agent_a, RA-IN-3 (R-IN-3): every call meets `all(i < sx: isdigit(x[i])) && nx >= 1 && all(i < sn: isdigit(n[i])) && nn >= 1`; `sx` is `count(i < len(x): all(j < i + 1: x[j] != "/"))`; `nx` is `sum(i < len(x): i < sx ? (x[i] - "0") * p10[sx - 1 - i] : 0)`; `sn` is `count(i < len(n): all(j < i + 1: n[j] != "/"))`; `nn` is `sum(i < len(n): i < sn ? (n[i] - "0") * p10[sn - 1 - i] : 0)`
- agent_a, RA-IN-4 (R-IN-4): every call meets `all(i < len(x): i > sx -> isdigit(x[i])) && dx >= 1 && all(i < len(n): i > sn -> isdigit(n[i])) && dn >= 1`; `sx` is `count(i < len(x): all(j < i + 1: x[j] != "/"))`; `dx` is `sum(i < len(x): i > sx ? (x[i] - "0") * p10[len(x) - 1 - i] : 0)`; `sn` is `count(i < len(n): all(j < i + 1: n[j] != "/"))`; `dn` is `sum(i < len(n): i > sn ? (n[i] - "0") * p10[len(n) - 1 - i] : 0)`
- agent_a, RA-IN-5 (R-IN-5): every call meets `vx && vn`; `vx` is `fx && nx >= 1 && dx >= 1`; `vn` is `fn && nn >= 1 && dn >= 1`
- agent_a, RA-IN-6 (R-IN-6): every call meets `dx != 0 && dn != 0`; `dx` is `sum(i < len(x): i > sx ? (x[i] - "0") * p10[len(x) - 1 - i] : 0)`; `dn` is `sum(i < len(n): i > sn ? (n[i] - "0") * p10[len(n) - 1 - i] : 0)`
- agent_a, RA-DC-RES (R-IN-5): `result` is free when `!(vx && vn)`; `vx` is `fx && nx >= 1 && dx >= 1`; `vn` is `fn && nn >= 1 && dn >= 1`
- agent_a, RA-DC-OUT (R-IN-5): `outcome` is free when `!(vx && vn)`; `vx` is `fx && nx >= 1 && dx >= 1`; `vn` is `fn && nn >= 1 && dn >= 1`
- agent_b, RB-IN-2-X (R-IN-2): every call meets `xshape && xnlz`; `xshape` is `xs >= 1 && xs + 2 <= len(x) && all(i < len(x): i == xs || isdigit(x[i]))`; `xnlz` is `!(xs >= 2 && x[0] == "0") && !(len(x) - xs >= 3 && x[xs + 1] == "0")`
- agent_b, RB-IN-2-N (R-IN-2): every call meets `nshape && nnlz`; `nshape` is `ns >= 1 && ns + 2 <= len(n) && all(i < len(n): i == ns || isdigit(n[i]))`; `nnlz` is `!(ns >= 2 && n[0] == "0") && !(len(n) - ns >= 3 && n[ns + 1] == "0")`
- agent_b, RB-IN-3-X (R-IN-3): every call meets `xnum_pos`; `xnum_pos` is `xs >= 1 && all(i < xs: isdigit(x[i])) && xa >= 1`
- agent_b, RB-IN-3-N (R-IN-3): every call meets `nnum_pos`; `nnum_pos` is `ns >= 1 && all(i < ns: isdigit(n[i])) && na >= 1`
- agent_b, RB-IN-4-X (R-IN-4): every call meets `xden_pos`; `xden_pos` is `xs + 2 <= len(x) && all(i < len(x): i > xs -> isdigit(x[i])) && xb >= 1`
- agent_b, RB-IN-4-N (R-IN-4): every call meets `nden_pos`; `nden_pos` is `ns + 2 <= len(n) && all(i < len(n): i > ns -> isdigit(n[i])) && nb >= 1`
- agent_b, RB-IN-5 (R-IN-5): every call meets `valid`; `valid` is `xvalid && nvalid`
- agent_b, RB-IN-6-X (R-IN-6): every call meets `xb != 0`; `xb` is `sum(i < len(x): i > xs ? (x[i] - "0") * p10[len(x) - 1 - i] : 0)`
- agent_b, RB-IN-6-N (R-IN-6): every call meets `nb != 0`; `nb` is `sum(i < len(n): i > ns ? (n[i] - "0") * p10[len(n) - 1 - i] : 0)`
- agent_b, RB-IN-5-DC-OUTCOME (R-IN-5): `outcome` is free when `!valid`; `valid` is `xvalid && nvalid`
- agent_b, RB-IN-5-DC-RESULT (R-IN-5): `result` is free when `!valid`; `valid` is `xvalid && nvalid`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the conflicts and open choices of agent_a: these searches leave out RA-RET-1, RA-RET-2 (rules stated for every value of a variable); 16 calls with two answers that break them are not reported
- the conflicts and open choices of agent_b: these searches leave out RB-RET-1, RB-RET-2 (rules stated for every value of a variable)
- request points of agent_a
- request points of agent_a, agent_b
- request points of agent_a, agent_b, variant
- request points of agent_b, agent_a
- the comparison of agent_a and agent_b
- request points of agent_a, variant
- request points of variant, agent_a
- the comparison of agent_a and variant
- request points of agent_b, variant
- request points of variant, agent_b
- the comparison of agent_b and variant
