# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 15.

## Questions
1. **depends** (R-RES-1, R-RES-2, R-RES-3): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
2. **readings** (R-RES-1): the two readings of this requirement were not shown to agree, and no call that separates them was found: do they mean the same?
3. **readings** (R-RES-2): the two readings of this requirement were not shown to agree, and no call that separates them was found: do they mean the same?
4. **ambiguity** (R-OP-1): "simplify the expression x * n" can mean: Describes the purpose only: the function decides whether the product is a whole number and returns just True or False (R-RES-3). / The function must produce the simplified product (for example the reduced fraction), which contradicts the statement that it returns True or False (R-RES-3).. Which is meant?
5. **ambiguity** (R-RES-1): "returns True if x * n evaluates to a whole number" can mean: As stated: the call returns True when the product is a whole number; the example simplify("1/5", "5/1") = False (product 1, a whole number) is wrong. / As all three examples show: the call returns True only when the product is not a whole number, so simplify("1/5", "5/1") (product 1) returns False; the sentence has True and False swapped.. Which is meant?
6. **ambiguity** (R-RES-1): "evaluates to" can mean: Exact rational arithmetic: the product is a whole number when the product of the numerators is divisible by the product of the denominators. / Floating-point evaluation (for example a/b * c/d in floats, or eval of the string x*n): the float result is integer-valued, which differs from exact arithmetic on some calls, such as 1/49 * 49/1 giving 0.9999999999999999.. Which is meant?
7. **ambiguity** (R-RES-1): "whole number" can mean: Any integer. / A non-negative integer (0, 1, 2, ...). / A positive integer (1, 2, 3, ...).. Which is meant?
8. **ambiguity** (R-RES-2): "False otherwise" can mean: As stated: the call returns False when the product is not a whole number; the examples simplify("1/6", "2/1") = True (product 1/3) and simplify("7/10", "10/2") = True (product 7/2) are wrong. / As all three examples show: the call returns True when the product is not a whole number; the sentence has True and False swapped.. Which is meant?
9. **ambiguity** (R-RES-2): "otherwise" can mean: Only among calls where x and n are valid fractions: a product that is not a whole number gives False; other calls are unconstrained (R-IN-6). / Every call that does not have a whole-number product, including calls where x or n is not a valid fraction, returns False instead of raising, which contradicts leaving invalid inputs unconstrained (R-IN-6).. Which is meant?
10. **ambiguity** (R-RES-2): "evaluates to a whole number" can mean: Exact rational arithmetic: the product is not a whole number when the product of the numerators is not divisible by the product of the denominators. / Floating-point evaluation (for example a/b * c/d in floats, or eval of the string x*n): the float result is not integer-valued, which differs from exact arithmetic on some calls, such as 1/49 * 49/1 giving 0.9999999999999999.. Which is meant?
11. **ambiguity** (R-RES-3): "The function returns" can mean: The function returns only the bool True or False. / The function returns the simplified expression x * n (R-OP-1), not a bool.. Which is meant?
12. **ambiguity** (R-RES-3): "True" can mean: The bool object True (and False for the other case). / Any truthy value, such as 1 (and any falsy value, such as 0, for the other case).. Which is meant?
13. **ambiguity** (R-EX-1): "simplify("1/5", "5/1") = False" can mean: The example is wrong: 1/5 * 5/1 = 1 is a whole number, so by the stated rule (R-RES-1) the call returns True. / The example is right: the call returns False, which contradicts the stated rule (R-RES-1) and matches a rule with True and False swapped.. Which is meant?
14. **ambiguity** (R-EX-2): "simplify("1/6", "2/1") = True" can mean: The example is wrong: 1/6 * 2/1 = 1/3 is not a whole number, so by the stated rule (R-RES-2) the call returns False. / The example is right: the call returns True, which contradicts the stated rule (R-RES-2) and matches a rule with True and False swapped.. Which is meant?
15. **ambiguity** (R-EX-3): "simplify("7/10", "10/2") = True" can mean: The example is wrong: 7/10 * 10/2 = 7/2 is not a whole number, so by the stated rule (R-RES-2) the call returns False. / The example is right: the call returns True, which contradicts the stated rule (R-RES-2) and matches a rule with True and False swapped.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-OP-1, "simplify the expression x * n": both took "Describes the purpose only: the function decides whether the product is a whole number and returns just True or False (R-RES-3)."
- R-RES-1, "returns True if x * n evaluates to a whole number": both took "As stated: the call returns True when the product is a whole number; the example simplify("1/5", "5/1") = False (product 1, a whole number) is wrong."
- R-RES-1, "evaluates to": both took "Exact rational arithmetic: the product is a whole number when the product of the numerators is divisible by the product of the denominators."
- R-RES-1, "whole number": both took "A non-negative integer (0, 1, 2, ...)."
- R-RES-2, "False otherwise": both took "As stated: the call returns False when the product is not a whole number; the examples simplify("1/6", "2/1") = True (product 1/3) and simplify("7/10", "10/2") = True (product 7/2) are wrong."
- R-RES-2, "otherwise": both took "Only among calls where x and n are valid fractions: a product that is not a whole number gives False; other calls are unconstrained (R-IN-6)."
- R-RES-2, "evaluates to a whole number": both took "Exact rational arithmetic: the product is not a whole number when the product of the numerators is not divisible by the product of the denominators."
- R-RES-3, "The function returns": both took "The function returns only the bool True or False."
- R-RES-3, "True": both took "The bool object True (and False for the other case)."
- R-IN-2, "<numerator>/<denominator>": both took "Exactly the numerator, one '/' and the denominator, with no other characters (no spaces or signs)."
- R-IN-3, "positive": both took "At least 1: neither the numerator nor the denominator is zero."
- R-IN-3, "whole numbers": both took "Any non-empty string of decimal digits with a positive value, leading zeros allowed (such as "05")."
- R-IN-4, "valid fractions": both took "Exactly strings of the form <numerator>/<denominator> where both are positive whole numbers (R-IN-2, R-IN-3)."
- R-IN-5, "do not have zero as denominator": both took "A restatement of part of R-IN-3: numerators are also positive, so neither number in either fraction is zero."
- R-IN-6, "You can assume": both took "Calls with an invalid fraction or a zero denominator impose no obligation: any outcome and result is acceptable."
- R-EX-1, "simplify("1/5", "5/1") = False": both took "The example is right: the call returns False, which contradicts the stated rule (R-RES-1) and matches a rule with True and False swapped."
- R-EX-2, "simplify("1/6", "2/1") = True": both took "The example is right: the call returns True, which contradicts the stated rule (R-RES-2) and matches a rule with True and False swapped."
- R-EX-3, "simplify("7/10", "10/2") = True": both took "The example is right: the call returns True, which contradicts the stated rule (R-RES-2) and matches a rule with True and False swapped."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-2-X (R-IN-2): every call meets `x_form`; `x_form` is `count(i < len(x): x[i] == "/") == 1 && x[0] != "/" && x[len(x) - 1] != "/"`
- agent_a, RA-IN-2-N (R-IN-2): every call meets `n_form`; `n_form` is `count(i < len(n): n[i] == "/") == 1 && n[0] != "/" && n[len(n) - 1] != "/"`
- agent_a, RA-IN-3-X (R-IN-3): `G( x_form -> x_digits && x_num >= 1 && x_den >= 1 )`; `x_form` is `count(i < len(x): x[i] == "/") == 1 && x[0] != "/" && x[len(x) - 1] != "/"`; `x_digits` is `all(i < len(x): x[i] == "/" || isdigit(x[i]))`; `x_num` is `(x[x_slash - 1] - "0") + 10 * (x_slash >= 2 ? x[x_slash - 2] - "0" : 0) + 100 * (x_slash >= 3 ? x[x_slash - 3] - "0" : 0) + 1000 * (x_slash >= 4 ? x[x_slash - 4] - "0" : 0) + 10000 * (x_slash >= 5 ? x[x_slash - 5] - "0" : 0) + 100000 * (x_slash >= 6 ? x[x_slash - 6] - "0" : 0)`; `x_den` is `(x[len(x) - 1] - "0") + 10 * (len(x) - x_slash >= 3 ? x[len(x) - 2] - "0" : 0) + 100 * (len(x) - x_slash >= 4 ? x[len(x) - 3] - "0" : 0) + 1000 * (len(x) - x_slash >= 5 ? x[len(x) - 4] - "0" : 0) + 10000 * (len(x) - x_slash >= 6 ? x[len(x) - 5] - "0" : 0) + 100000 * (len(x) - x_slash >= 7 ? x[len(x) - 6] - "0" : 0)`
- agent_a, RA-IN-3-N (R-IN-3): `G( n_form -> n_digits && n_num >= 1 && n_den >= 1 )`; `n_form` is `count(i < len(n): n[i] == "/") == 1 && n[0] != "/" && n[len(n) - 1] != "/"`; `n_digits` is `all(i < len(n): n[i] == "/" || isdigit(n[i]))`; `n_num` is `(n[n_slash - 1] - "0") + 10 * (n_slash >= 2 ? n[n_slash - 2] - "0" : 0) + 100 * (n_slash >= 3 ? n[n_slash - 3] - "0" : 0) + 1000 * (n_slash >= 4 ? n[n_slash - 4] - "0" : 0) + 10000 * (n_slash >= 5 ? n[n_slash - 5] - "0" : 0) + 100000 * (n_slash >= 6 ? n[n_slash - 6] - "0" : 0)`; `n_den` is `(n[len(n) - 1] - "0") + 10 * (len(n) - n_slash >= 3 ? n[len(n) - 2] - "0" : 0) + 100 * (len(n) - n_slash >= 4 ? n[len(n) - 3] - "0" : 0) + 1000 * (len(n) - n_slash >= 5 ? n[len(n) - 4] - "0" : 0) + 10000 * (len(n) - n_slash >= 6 ? n[len(n) - 5] - "0" : 0) + 100000 * (len(n) - n_slash >= 7 ? n[len(n) - 6] - "0" : 0)`
- agent_a, RA-IN-4-X (R-IN-4): every call meets `x_valid`; `x_valid` is `x_form && x_digits && x_num >= 1 && x_den >= 1`
- agent_a, RA-IN-4-N (R-IN-4): every call meets `n_valid`; `n_valid` is `n_form && n_digits && n_num >= 1 && n_den >= 1`
- agent_a, RA-IN-5-X (R-IN-5): `G( x_form && x_digits -> x_den != 0 )`; `x_form` is `count(i < len(x): x[i] == "/") == 1 && x[0] != "/" && x[len(x) - 1] != "/"`; `x_digits` is `all(i < len(x): x[i] == "/" || isdigit(x[i]))`; `x_den` is `(x[len(x) - 1] - "0") + 10 * (len(x) - x_slash >= 3 ? x[len(x) - 2] - "0" : 0) + 100 * (len(x) - x_slash >= 4 ? x[len(x) - 3] - "0" : 0) + 1000 * (len(x) - x_slash >= 5 ? x[len(x) - 4] - "0" : 0) + 10000 * (len(x) - x_slash >= 6 ? x[len(x) - 5] - "0" : 0) + 100000 * (len(x) - x_slash >= 7 ? x[len(x) - 6] - "0" : 0)`
- agent_a, RA-IN-5-N (R-IN-5): `G( n_form && n_digits -> n_den != 0 )`; `n_form` is `count(i < len(n): n[i] == "/") == 1 && n[0] != "/" && n[len(n) - 1] != "/"`; `n_digits` is `all(i < len(n): n[i] == "/" || isdigit(n[i]))`; `n_den` is `(n[len(n) - 1] - "0") + 10 * (len(n) - n_slash >= 3 ? n[len(n) - 2] - "0" : 0) + 100 * (len(n) - n_slash >= 4 ? n[len(n) - 3] - "0" : 0) + 1000 * (len(n) - n_slash >= 5 ? n[len(n) - 4] - "0" : 0) + 10000 * (len(n) - n_slash >= 6 ? n[len(n) - 5] - "0" : 0) + 100000 * (len(n) - n_slash >= 7 ? n[len(n) - 6] - "0" : 0)`
- agent_b, RB-IN-2-X (R-IN-2): every call meets `x_shape && x_digits`; `x_shape` is `count(j < len(x): x[j] == "/") == 1 && x_sl >= 1 && x_sl <= len(x) - 2`; `x_digits` is `all(j < len(x): j == x_sl || isdigit(x[j]))`
- agent_b, RB-IN-2-N (R-IN-2): every call meets `n_shape && n_digits`; `n_shape` is `count(j < len(n): n[j] == "/") == 1 && n_sl >= 1 && n_sl <= len(n) - 2`; `n_digits` is `all(j < len(n): j == n_sl || isdigit(n[j]))`
- agent_b, RB-IN-3-X (R-IN-3): every call meets `x_shape -> x_digits && x_num >= 1 && x_den >= 1`; `x_shape` is `count(j < len(x): x[j] == "/") == 1 && x_sl >= 1 && x_sl <= len(x) - 2`; `x_digits` is `all(j < len(x): j == x_sl || isdigit(x[j]))`; `x_num` is `sum(i < len(x): i < x_sl && isdigit(x[i]) ? (x[i] - "0") * (x_sl - i == 1 ? 1 : x_sl - i == 2 ? 10 : x_sl - i == 3 ? 100 : x_sl - i == 4 ? 1000 : x_sl - i == 5 ? 10000 : x_sl - i == 6 ? 100000 : 1000000) : 0)`; `x_den` is `sum(i < len(x): i > x_sl && isdigit(x[i]) ? (x[i] - "0") * (len(x) - i == 1 ? 1 : len(x) - i == 2 ? 10 : len(x) - i == 3 ? 100 : len(x) - i == 4 ? 1000 : len(x) - i == 5 ? 10000 : len(x) - i == 6 ? 100000 : 1000000) : 0)`
- agent_b, RB-IN-3-N (R-IN-3): every call meets `n_shape -> n_digits && n_num >= 1 && n_den >= 1`; `n_shape` is `count(j < len(n): n[j] == "/") == 1 && n_sl >= 1 && n_sl <= len(n) - 2`; `n_digits` is `all(j < len(n): j == n_sl || isdigit(n[j]))`; `n_num` is `sum(i < len(n): i < n_sl && isdigit(n[i]) ? (n[i] - "0") * (n_sl - i == 1 ? 1 : n_sl - i == 2 ? 10 : n_sl - i == 3 ? 100 : n_sl - i == 4 ? 1000 : n_sl - i == 5 ? 10000 : n_sl - i == 6 ? 100000 : 1000000) : 0)`; `n_den` is `sum(i < len(n): i > n_sl && isdigit(n[i]) ? (n[i] - "0") * (len(n) - i == 1 ? 1 : len(n) - i == 2 ? 10 : len(n) - i == 3 ? 100 : len(n) - i == 4 ? 1000 : len(n) - i == 5 ? 10000 : len(n) - i == 6 ? 100000 : 1000000) : 0)`
- agent_b, RB-IN-4 (R-IN-4): every call meets `x_valid && n_valid`; `x_valid` is `x_shape && x_digits && x_num >= 1 && x_den >= 1`; `n_valid` is `n_shape && n_digits && n_num >= 1 && n_den >= 1`
- agent_b, RB-IN-5-X (R-IN-5): every call meets `x_shape -> x_den != 0`; `x_shape` is `count(j < len(x): x[j] == "/") == 1 && x_sl >= 1 && x_sl <= len(x) - 2`; `x_den` is `sum(i < len(x): i > x_sl && isdigit(x[i]) ? (x[i] - "0") * (len(x) - i == 1 ? 1 : len(x) - i == 2 ? 10 : len(x) - i == 3 ? 100 : len(x) - i == 4 ? 1000 : len(x) - i == 5 ? 10000 : len(x) - i == 6 ? 100000 : 1000000) : 0)`
- agent_b, RB-IN-5-N (R-IN-5): every call meets `n_shape -> n_den != 0`; `n_shape` is `count(j < len(n): n[j] == "/") == 1 && n_sl >= 1 && n_sl <= len(n) - 2`; `n_den` is `sum(i < len(n): i > n_sl && isdigit(n[i]) ? (n[i] - "0") * (len(n) - i == 1 ? 1 : len(n) - i == 2 ? 10 : len(n) - i == 3 ? 100 : len(n) - i == 4 ? 1000 : len(n) - i == 5 ? 10000 : len(n) - i == 6 ? 100000 : 1000000) : 0)`
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-IN-6-OUTCOME (R-IN-6): `outcome` is free when `!valid`; `valid` is `x_valid && n_valid`
- agent_a, RA-IN-6-RESULT (R-IN-6): `result` is free when `!valid`; `valid` is `x_valid && n_valid`
- agent_b, RB-IN-6-OUT (R-IN-6): `outcome` is free when `!valid`; `valid` is `x_valid && n_valid`
- agent_b, RB-IN-6-RES (R-IN-6): `result` is free when `!valid`; `valid` is `x_valid && n_valid`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the conflicts and open choices of agent_a: these searches leave out RA-RES-1, RA-RES-2 (rules stated for every value of a variable); 8 calls with two answers that break them are not reported
- the conflicts and open choices of agent_b: these searches leave out RB-RES-1, RB-RES-2 (rules stated for every value of a variable); 8 calls with two answers that break them are not reported
- request points of agent_a
- request points of agent_b
- request points of agent_a, agent_b
- request points of agent_a, agent_b, variant
- request points of agent_b, agent_a
- the comparison of agent_a and agent_b
- the comparison of agent_a and agent_b: it cannot assume RA-RES-1, RA-RES-2, RB-RES-1, RB-RES-2 (rules stated for every value of a variable), and requirements they bear on stay undecided
- request points of agent_a, variant
- request points of variant, agent_a
- the comparison of agent_a and variant
- the comparison of agent_a and variant: it cannot assume RA-RES-1, RA-RES-2, RV-RES-1, RV-RES-2 (rules stated for every value of a variable), and requirements they bear on stay undecided
- request points of agent_b, variant
- request points of variant, agent_b
- the comparison of agent_b and variant
- the comparison of agent_b and variant: it cannot assume RB-RES-1, RB-RES-2, RV-RES-1, RV-RES-2 (rules stated for every value of a variable), and requirements they bear on stay undecided
