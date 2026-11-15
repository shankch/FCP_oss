# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 10.

## Questions
1. **open** (result): the request allows False or True: which is meant?
   - `simplify("2/3", "1/11211")`
2. **depends** (R-OUT-1, R-OUT-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `simplify("11211111/1011011", "11/2111100112213") -> returned something else`
   - `simplify("/212/\u0001//1./20", "2//./\u0001\u0001/////\u00021/2") -> True`
3. **readings** (R-OUT-1): the two readings of this requirement disagree on these calls: which is meant?
   - `simplify("51/17659", "29/4") -> returned something else`
4. **readings** (R-OUT-2): the two readings of this requirement disagree on these calls: which is meant?
   - `simplify("001111111111/111", "001111111/111114") -> True`
   - `simplify("0011111111111/0", "\u00010111111111111/0") -> raised another exception or did not finish`
5. **ambiguity** (R-OUT-1): "will simplify the expression" can mean: the function must return normally on every valid input (it delivers the simplified expression as its returned value) / the function may signal some valid inputs (for example an expression that cannot be simplified further) by raising an exception; only the inputs it can simplify must return. Which is meant?
6. **ambiguity** (R-OUT-1): "simplify the expression" can mean: the returned value is a boolean (True or False), which is how the adapter records the result; any other returned value is outcome 2 / the returned value is the simplified expression itself (a fraction string such as "1/2", a number, or a Fraction object), which the adapter records as outcome 2 rather than as a returned boolean; this conflicts with the adapter's boolean result. Which is meant?
7. **ambiguity** (R-OUT-2): "the expression" can mean: the product x * n / the quotient x / n / each of x and n on its own (the two fractions are simplified separately) / some other expression in x and n; the request names no operator and the docstring gives no antecedent for 'the expression'. Which is meant?
8. **ambiguity** (R-OUT-2): "simplify" can mean: return True if the expression evaluates to a whole number and False otherwise (a boolean, matching the adapter's boolean result) / return the expression reduced to lowest terms as a fraction string '<numerator>/<denominator>' (for example '2/4' * '1/1' gives '1/2') / return the reduced value as a number or Fraction object (a whole number when the denominator becomes 1). Which is meant?
9. **ambiguity** (R-OUT-2): "simplify the expression" can mean: the returned value is a boolean, as the adapter records it (frame.md: the returned value is recorded as a boolean, anything else is outcome 2) / the returned value is the simplified expression (string, number or Fraction), which contradicts the adapter's boolean result: every such answer would be recorded as outcome 2. Which is meant?
10. **ambiguity** (R-OUT-2): "simplify (form of a simplified fraction)" can mean: a whole-number result is written without a denominator (for example '2') / a whole-number result keeps the denominator 1 (for example '2/1'). Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-OUT-1, "will simplify the expression": both took "the function must return normally on every valid input (it delivers the simplified expression as its returned value)"
- R-OUT-2, "the expression": both took "some other expression in x and n; the request names no operator and the docstring gives no antecedent for 'the expression'"
- R-OUT-2, "simplify (form of a simplified fraction)": both took "a whole-number result is written without a denominator (for example '2')"
- R-IN-1, "valid fractions": both took "a string '<numerator>/<denominator>' in which the numerator may be zero"
- R-IN-1, "valid fractions, and do not have zero as denominator": both took "'valid' refers only to the textual form, so a valid fraction could have a zero denominator were it not for the second clause"
- R-IN-2, "valid fractions": both took "a string '<numerator>/<denominator>' in which the numerator may be zero"
- R-IN-2, "valid fractions, and do not have zero as denominator": both took "'valid' refers only to the textual form, so a valid fraction could have a zero denominator were it not for the second clause"
- R-IN-3, "zero as denominator": both took "the denominator's numeric value is not 0 (so '1/00' is also excluded)"
- R-IN-4, "zero as denominator": both took "the denominator's numeric value is not 0 (so '1/00' is also excluded)"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `x_frac`; `x_frac` is `count(i < len(x): x[i] == "/") == 1 && all(i < len(x): isdigit(x[i]) || x[i] == "/") && x[0] != "/" && x[len(x) - 1] != "/"`
- agent_a, RA-IN-2 (R-IN-2): every call meets `n_frac`; `n_frac` is `count(i < len(n): n[i] == "/") == 1 && all(i < len(n): isdigit(n[i]) || n[i] == "/") && n[0] != "/" && n[len(n) - 1] != "/"`
- agent_a, RA-IN-3 (R-IN-3): every call meets `x_frac -> !x_den_zero`; `x_frac` is `count(i < len(x): x[i] == "/") == 1 && all(i < len(x): isdigit(x[i]) || x[i] == "/") && x[0] != "/" && x[len(x) - 1] != "/"`; `x_den_zero` is `all(i < len(x): (any(j < i: x[j] == "/") -> x[i] == "0"))`
- agent_a, RA-IN-4 (R-IN-4): every call meets `n_frac -> !n_den_zero`; `n_frac` is `count(i < len(n): n[i] == "/") == 1 && all(i < len(n): isdigit(n[i]) || n[i] == "/") && n[0] != "/" && n[len(n) - 1] != "/"`; `n_den_zero` is `all(i < len(n): (any(j < i: n[j] == "/") -> n[i] == "0"))`
- agent_b, RB-IN1-A (R-IN-1): every call meets `x_form`; `x_form` is `count(i < len(x): x[i] == "/") == 1 && all(i < len(x): isdigit(x[i]) || x[i] == "/") && x[0] != "/" && x[len(x) - 1] != "/"`
- agent_b, RB-IN2-A (R-IN-2): every call meets `n_form`; `n_form` is `count(i < len(n): n[i] == "/") == 1 && all(i < len(n): isdigit(n[i]) || n[i] == "/") && n[0] != "/" && n[len(n) - 1] != "/"`
- agent_b, RB-IN3-A (R-IN-3): every call meets `!x_den_zero`; `x_den_zero` is `any(p < len(x): x[p] == "/" && count(j < p: x[j] == "/") == 0 && p + 1 < len(x) && all(k < len(x): k <= p || x[k] == "0"))`
- agent_b, RB-IN4-A (R-IN-4): every call meets `!n_den_zero`; `n_den_zero` is `any(p < len(n): n[p] == "/" && count(j < p: n[j] == "/") == 0 && p + 1 < len(n) && all(k < len(n): k <= p || n[k] == "0"))`
- agent_b, RB-IN1-D-OUT (R-IN-1): `outcome` is free when `!x_form`; `x_form` is `count(i < len(x): x[i] == "/") == 1 && all(i < len(x): isdigit(x[i]) || x[i] == "/") && x[0] != "/" && x[len(x) - 1] != "/"`
- agent_b, RB-IN1-D-RES (R-IN-1): `result` is free when `!x_form`; `x_form` is `count(i < len(x): x[i] == "/") == 1 && all(i < len(x): isdigit(x[i]) || x[i] == "/") && x[0] != "/" && x[len(x) - 1] != "/"`
- agent_b, RB-IN2-D-OUT (R-IN-2): `outcome` is free when `!n_form`; `n_form` is `count(i < len(n): n[i] == "/") == 1 && all(i < len(n): isdigit(n[i]) || n[i] == "/") && n[0] != "/" && n[len(n) - 1] != "/"`
- agent_b, RB-IN2-D-RES (R-IN-2): `result` is free when `!n_form`; `n_form` is `count(i < len(n): n[i] == "/") == 1 && all(i < len(n): isdigit(n[i]) || n[i] == "/") && n[0] != "/" && n[len(n) - 1] != "/"`
- agent_b, RB-IN3-D-OUT (R-IN-3): `outcome` is free when `x_den_zero`; `x_den_zero` is `any(p < len(x): x[p] == "/" && count(j < p: x[j] == "/") == 0 && p + 1 < len(x) && all(k < len(x): k <= p || x[k] == "0"))`
- agent_b, RB-IN3-D-RES (R-IN-3): `result` is free when `x_den_zero`; `x_den_zero` is `any(p < len(x): x[p] == "/" && count(j < p: x[j] == "/") == 0 && p + 1 < len(x) && all(k < len(x): k <= p || x[k] == "0"))`
- agent_b, RB-IN4-D-OUT (R-IN-4): `outcome` is free when `n_den_zero`; `n_den_zero` is `any(p < len(n): n[p] == "/" && count(j < p: n[j] == "/") == 0 && p + 1 < len(n) && all(k < len(n): k <= p || n[k] == "0"))`
- agent_b, RB-IN4-D-RES (R-IN-4): `result` is free when `n_den_zero`; `n_den_zero` is `any(p < len(n): n[p] == "/" && count(j < p: n[j] == "/") == 0 && p + 1 < len(n) && all(k < len(n): k <= p || n[k] == "0"))`
