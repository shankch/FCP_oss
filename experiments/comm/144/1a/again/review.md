# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 7.

## This review is partial
6 of the 10 steps of the check did not end. What the other steps found stands; no requirement is settled that rests on one of these:
- the conflicts of agent_b: did not end in 900 s
- the open choices of agent_b: was stopped: the check reached its time limit of 2340 s
- the comparison of agent_a and agent_b: not run: the check reached its time limit of 2340 s
- the comparison of agent_a and agent_b, in context: not run: the check reached its time limit of 2340 s
- the comparison of agent_a and variant: not run: the check reached its time limit of 2340 s
- the comparison of agent_b and variant: not run: the check reached its time limit of 2340 s

## Questions
1. **ambiguity** (R-RES-1): "x * n or x + n evaluates to a whole number" can mean: True when at least one of the product x * n and the sum x + n is a whole number. / True when the product x * n is a whole number; the sum is not considered (matches all three examples). / True when the sum x + n is a whole number; contradicts R-EX-1, since 1/5 + 5/1 = 26/5 is not whole yet the expected answer is True. / True only when both x * n and x + n are whole numbers; contradicts R-EX-1 for the same reason.. Which is meant?
2. **ambiguity** (R-RES-1): "evaluates" can mean: Exact rational arithmetic: the value is a whole number exactly. / Floating-point evaluation (e.g. float division) whose result has an integral value, which can differ from exact arithmetic through rounding.. Which is meant?
3. **ambiguity** (R-RES-1): "whole number" can mean: Any integer value. / A non-negative integer (0 counts as whole). / A positive integer (0 does not count); differs from the other readings only if a numerator of 0 can occur.. Which is meant?
4. **ambiguity** (R-RES-1): "returns True" can mean: The function returns a bool. / R-FN-3 says the function simplifies the expression, suggesting it returns the simplified expression; this contradicts returning True or False.. Which is meant?
5. **ambiguity** (R-RES-2): "otherwise" can mean: False when neither the product x * n nor the sum x + n is a whole number. / False when the product x * n is not a whole number, whatever the sum. / False when the sum x + n is not a whole number; contradicts R-EX-1 (1/5 + 5/1 = 26/5, expected True). / False when at least one of x * n and x + n is not a whole number; contradicts R-EX-1.. Which is meant?
6. **ambiguity** (R-RES-2): "False" can mean: The function returns a bool. / R-FN-3 says the function simplifies the expression, suggesting it returns the simplified expression; this contradicts returning True or False.. Which is meant?
7. **ambiguity** (R-EX-1): "simplify("1/5", "5/1") = True" can mean: Consistent with R-RES-1 if the product decides (1/5 * 5/1 = 1) or if either expression being whole suffices. / Contradicts R-RES-1 if the sum must be whole (alone or together with the product): 1/5 + 5/1 = 26/5 is not a whole number.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FN-2, "a, b": both took "x is the first argument a and n is the second argument b (by position)."
- R-FN-3, "simplify the expression": both took "A loose description of the task: the function only reports whether the expression is a whole number, returning a bool as the next sentence says."
- R-FN-3, "x * n, or x + n": both took "Both the product x * n and the sum x + n are considered."
- R-IN-1, "<numerator>/<denominator>": both took "Exactly the decimal digits of the numerator, one '/', and the decimal digits of the denominator, with no leading zeros, signs or spaces."
- R-IN-2, "positive whole numbers": both took "Integers of at least 1: neither the numerator nor the denominator is ever zero."
- R-IN-3, "valid fractions": both took "A string in the stated <numerator>/<denominator> format whose numerator and denominator are positive whole numbers."
- R-IN-4, "do not have zero as denominator": both took "A redundant restatement: R-IN-2 already makes the denominator positive."
- R-RES-1, "x * n or x + n evaluates to a whole number": both took "True when at least one of the product x * n and the sum x + n is a whole number."
- R-RES-1, "evaluates": both took "Exact rational arithmetic: the value is a whole number exactly."
- R-RES-1, "whole number": both took "Any integer value."
- R-RES-1, "returns True": both took "The function returns a bool."
- R-RES-2, "otherwise": both took "False when neither the product x * n nor the sum x + n is a whole number."
- R-RES-2, "False": both took "The function returns a bool."
- R-EX-1, "simplify("1/5", "5/1") = True": both took "Consistent with R-RES-1 if the product decides (1/5 * 5/1 = 1) or if either expression being whole suffices."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `fmt_a && fmt_b`; `fmt_a` is `count(i < len(a): a[i] == "/") == 1 && all(i < len(a): a[i] == "/" || isdigit(a[i])) && pa >= 1 && pa <= len(a) - 2 && (a[0] == "0" -> pa == 1) && (a[pa + 1] == "0" -> pa + 2 == len(a))`; `fmt_b` is `count(i < len(b): b[i] == "/") == 1 && all(i < len(b): b[i] == "/" || isdigit(b[i])) && pb >= 1 && pb <= len(b) - 2 && (b[0] == "0" -> pb == 1) && (b[pb + 1] == "0" -> pb + 2 == len(b))`
- agent_a, RA-IN-2 (R-IN-2): every call meets `pos_a && pos_b`; `pos_a` is `na >= 1 && da >= 1`; `pos_b` is `nb >= 1 && db >= 1`
- agent_a, RA-IN-3 (R-IN-3): every call meets `fmt_a && fmt_b && pos_a && pos_b`; `fmt_a` is `count(i < len(a): a[i] == "/") == 1 && all(i < len(a): a[i] == "/" || isdigit(a[i])) && pa >= 1 && pa <= len(a) - 2 && (a[0] == "0" -> pa == 1) && (a[pa + 1] == "0" -> pa + 2 == len(a))`; `fmt_b` is `count(i < len(b): b[i] == "/") == 1 && all(i < len(b): b[i] == "/" || isdigit(b[i])) && pb >= 1 && pb <= len(b) - 2 && (b[0] == "0" -> pb == 1) && (b[pb + 1] == "0" -> pb + 2 == len(b))`; `pos_a` is `na >= 1 && da >= 1`; `pos_b` is `nb >= 1 && db >= 1`
- agent_a, RA-IN-4 (R-IN-4): every call meets `da != 0 && db != 0`; `da` is `sum(i < len(a): i > pa ? (a[i] - "0") * p10[len(a) - 1 - i] : 0)`; `db` is `sum(i < len(b): i > pb ? (b[i] - "0") * p10[len(b) - 1 - i] : 0)`
- agent_b, RB-A-IN-1-A (R-IN-1): every call meets `fmt_a`; `fmt_a` is `sl_a == 1 && pa >= 1 && pa + 2 <= len(a) && all(i < len(a): a[i] == "/" || isdigit(a[i])) && a[0] != "0" && a[pa + 1] != "0"`
- agent_b, RB-A-IN-1-B (R-IN-1): every call meets `fmt_b`; `fmt_b` is `sl_b == 1 && pb >= 1 && pb + 2 <= len(b) && all(i < len(b): b[i] == "/" || isdigit(b[i])) && b[0] != "0" && b[pb + 1] != "0"`
- agent_b, RB-A-IN-2 (R-IN-2): every call meets `num_a >= 1 && den_a >= 1 && num_b >= 1 && den_b >= 1`; `num_a` is `sum(k < 16: k < pa ? (a[pa - 1 - k] - "0") * (k == 0 ? 1 : k == 1 ? 10 : k == 2 ? 100 : k == 3 ? 1000 : k == 4 ? 10000 : k == 5 ? 100000 : k == 6 ? 1000000 : k == 7 ? 10000000 : k == 8 ? 100000000 : k == 9 ? 1000000000 : k == 10 ? 10000000000 : k == 11 ? 100000000000 : k == 12 ? 1000000000000 : k == 13 ? 10000000000000 : k == 14 ? 100000000000000 : 1000000000000000) : 0)`; `den_a` is `sum(k < 16: k < len(a) - 1 - pa ? (a[len(a) - 1 - k] - "0") * (k == 0 ? 1 : k == 1 ? 10 : k == 2 ? 100 : k == 3 ? 1000 : k == 4 ? 10000 : k == 5 ? 100000 : k == 6 ? 1000000 : k == 7 ? 10000000 : k == 8 ? 100000000 : k == 9 ? 1000000000 : k == 10 ? 10000000000 : k == 11 ? 100000000000 : k == 12 ? 1000000000000 : k == 13 ? 10000000000000 : k == 14 ? 100000000000000 : 1000000000000000) : 0)`; `num_b` is `sum(k < 16: k < pb ? (b[pb - 1 - k] - "0") * (k == 0 ? 1 : k == 1 ? 10 : k == 2 ? 100 : k == 3 ? 1000 : k == 4 ? 10000 : k == 5 ? 100000 : k == 6 ? 1000000 : k == 7 ? 10000000 : k == 8 ? 100000000 : k == 9 ? 1000000000 : k == 10 ? 10000000000 : k == 11 ? 100000000000 : k == 12 ? 1000000000000 : k == 13 ? 10000000000000 : k == 14 ? 100000000000000 : 1000000000000000) : 0)`; `den_b` is `sum(k < 16: k < len(b) - 1 - pb ? (b[len(b) - 1 - k] - "0") * (k == 0 ? 1 : k == 1 ? 10 : k == 2 ? 100 : k == 3 ? 1000 : k == 4 ? 10000 : k == 5 ? 100000 : k == 6 ? 1000000 : k == 7 ? 10000000 : k == 8 ? 100000000 : k == 9 ? 1000000000 : k == 10 ? 10000000000 : k == 11 ? 100000000000 : k == 12 ? 1000000000000 : k == 13 ? 10000000000000 : k == 14 ? 100000000000000 : 1000000000000000) : 0)`
- agent_b, RB-A-IN-3 (R-IN-3): every call meets `valid_a && valid_b`; `valid_a` is `fmt_a && num_a >= 1 && den_a >= 1`; `valid_b` is `fmt_b && num_b >= 1 && den_b >= 1`
- agent_b, RB-A-IN-4 (R-IN-4): every call meets `den_a != 0 && den_b != 0`; `den_a` is `sum(k < 16: k < len(a) - 1 - pa ? (a[len(a) - 1 - k] - "0") * (k == 0 ? 1 : k == 1 ? 10 : k == 2 ? 100 : k == 3 ? 1000 : k == 4 ? 10000 : k == 5 ? 100000 : k == 6 ? 1000000 : k == 7 ? 10000000 : k == 8 ? 100000000 : k == 9 ? 1000000000 : k == 10 ? 10000000000 : k == 11 ? 100000000000 : k == 12 ? 1000000000000 : k == 13 ? 10000000000000 : k == 14 ? 100000000000000 : 1000000000000000) : 0)`; `den_b` is `sum(k < 16: k < len(b) - 1 - pb ? (b[len(b) - 1 - k] - "0") * (k == 0 ? 1 : k == 1 ? 10 : k == 2 ? 100 : k == 3 ? 1000 : k == 4 ? 10000 : k == 5 ? 100000 : k == 6 ? 1000000 : k == 7 ? 10000000 : k == 8 ? 100000000 : k == 9 ? 1000000000 : k == 10 ? 10000000000 : k == 11 ? 100000000000 : k == 12 ? 1000000000000 : k == 13 ? 10000000000000 : k == 14 ? 100000000000000 : 1000000000000000) : 0)`
- agent_b, RB-D-IN-3-OUTCOME (R-IN-3): `outcome` is free when `!valid`; `valid` is `valid_a && valid_b`
- agent_b, RB-D-IN-3-RESULT (R-IN-3): `result` is free when `!valid`; `valid` is `valid_a && valid_b`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the conflicts and open choices of agent_a: these searches leave out RA-RES-1-PROD, RA-RES-1-SUM, RA-RES-2 (rules stated for every value of a variable); 6 calls with two answers that break them are not reported
- the scenarios of agent_b: RB-S-EX-1, RB-S-EX-2, RB-S-EX-3, RB-S-RES-1-SUM
- request points of agent_a
- conflict search of agent_a
