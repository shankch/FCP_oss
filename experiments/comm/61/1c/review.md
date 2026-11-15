# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 13.

## Questions
1. **conflict** (R-EX-2, R-RET-1): no implementation can meet these requirements on these calls: which one gives way? (also with , at 2 places)
   - `correct_bracketing("()")`
2. **conflict** (R-EX-3, R-RET-1): no implementation can meet these requirements on these calls: which one gives way? (also with , at 2 places)
   - `correct_bracketing("(()())")`
3. **open** (result): the request allows False or True: which is meant?
   - `correct_bracketing("((")`
4. **depends** (R-EX-1, R-EX-4, R-RET-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `correct_bracketing("(") -> True`
5. **ambiguity** (R-FN-2): "Complete this function" can mean: The completed function must return a bool (True or False) for every valid input, including inputs on which the docstring gives no explicit rule. / Only the behaviour the docstring and examples state is required; what the function returns (or whether it returns at all) where the docstring is silent is unconstrained. / Any value with the right truthiness (e.g. 1/0 or a non-empty/empty object) is acceptable in place of True/False.. Which is meant?
6. **ambiguity** (R-RET-1): "return True if" can mean: Sufficient condition only: True is returned whenever every opening bracket has a corresponding closing bracket; nothing is said about when False is returned. / Biconditional: True is returned exactly when every opening bracket has a corresponding closing bracket, and False otherwise.. Which is meant?
7. **ambiguity** (R-RET-1): "a corresponding closing bracket" can mean: Nested matching: each "(" is paired with its own distinct ")" later in the string, pairs nesting properly (standard left-to-right bracket matching). / Counting: the number of ")" is at least the number of "(", wherever they are in the string (a ")" before a "(" may correspond to it). / Positional but not exclusive: for each "(" some ")" occurs later in the string; one ")" may serve several "(".. Which is meant?
8. **ambiguity** (R-RET-1): "every opening bracket" can mean: Only opening brackets are constrained: closing brackets with no opening bracket (as in ")" or "())") do not prevent a True result. / The whole string must be correctly bracketed, as the name correct_bracketing suggests: a ")" with no earlier unmatched "(" also makes the bracketing incorrect.. Which is meant?
9. **ambiguity** (R-RET-1): "return True if every opening bracket has a corresponding closing bracket" can mean: This sentence is authoritative: correctly matched strings such as "()" and "(()())" return True, so examples R-EX-2 and R-EX-3 (and, under the biconditional reading, R-EX-1 and R-EX-4) are wrong. Contradicts R-EX-1, R-EX-2, R-EX-3 and R-EX-4. / The examples are authoritative: all four of them are the negation of standard bracket matching, so the function returns True exactly when the string is NOT correctly bracketed and this sentence (and the name) is inverted.. Which is meant?
10. **ambiguity** (R-EX-1): "correct_bracketing("(")" can mean: This example holds: correct_bracketing("(") returns True. This contradicts R-RET-1 under its biconditional reading (the only opening bracket has no closing bracket, so False would be required) and agrees with its sufficient-only reading, which leaves this call free. / R-RET-1 read as a biconditional holds and this example is wrong: correct_bracketing("(") returns False.. Which is meant?
11. **ambiguity** (R-EX-2): "correct_bracketing("()")" can mean: This example holds: correct_bracketing("()") returns False. This contradicts R-RET-1 under every reading, since the only opening bracket has a corresponding closing bracket and R-RET-1 then requires True. / R-RET-1 holds and this example is wrong: correct_bracketing("()") returns True.. Which is meant?
12. **ambiguity** (R-EX-3): "correct_bracketing("(()())")" can mean: This example holds: correct_bracketing("(()())") returns False. This contradicts R-RET-1 under every reading, since every opening bracket has a corresponding closing bracket and R-RET-1 then requires True. / R-RET-1 holds and this example is wrong: correct_bracketing("(()())") returns True.. Which is meant?
13. **ambiguity** (R-EX-4): "correct_bracketing(")(()")" can mean: This example holds: correct_bracketing(")(()") returns True. This contradicts R-RET-1 read as a biconditional with nested matching (the "(" at index 1 has no matching ")", so False would be required) or with whole-string correctness (the leading ")" is unmatched); it agrees with the sufficient-only, counting or positional-but-not-exclusive readings. / R-RET-1 read as a biconditional with nested matching (or whole-string correctness) holds and this example is wrong: correct_bracketing(")(()") returns False.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FN-2, "Complete this function": both took "The completed function must return a bool (True or False) for every valid input, including inputs on which the docstring gives no explicit rule."
- R-IN-1, ""(" and ")"": both took "Precondition: only "(" and ")" are passed; the result for a string containing any other character is unconstrained (don't care)."
- R-IN-1, "a string of": both took "The empty string is a valid input (a string of zero brackets), and the return rule applies to it: with no opening brackets, every opening bracket is (vacuously) matched."
- R-RET-1, "return True if": both took "Sufficient condition only: True is returned whenever every opening bracket has a corresponding closing bracket; nothing is said about when False is returned."
- R-RET-1, "a corresponding closing bracket": both took "Nested matching: each "(" is paired with its own distinct ")" later in the string, pairs nesting properly (standard left-to-right bracket matching)."
- R-RET-1, "every opening bracket": both took "Only opening brackets are constrained: closing brackets with no opening bracket (as in ")" or "())") do not prevent a True result."
- R-RET-1, "return True if every opening bracket has a corresponding closing bracket": both took "This sentence is authoritative: correctly matched strings such as "()" and "(()())" return True, so examples R-EX-2 and R-EX-3 (and, under the biconditional reading, R-EX-1 and R-EX-4) are wrong. Contradicts R-EX-1, R-EX-2, R-EX-3 and R-EX-4."
- R-EX-1, "correct_bracketing("(")": both took "This example holds: correct_bracketing("(") returns True. This contradicts R-RET-1 under its biconditional reading (the only opening bracket has no closing bracket, so False would be required) and agrees with its sufficient-only reading, which leaves this call free."
- R-EX-2, "correct_bracketing("()")": both took "This example holds: correct_bracketing("()") returns False. This contradicts R-RET-1 under every reading, since the only opening bracket has a corresponding closing bracket and R-RET-1 then requires True."
- R-EX-3, "correct_bracketing("(()())")": both took "This example holds: correct_bracketing("(()())") returns False. This contradicts R-RET-1 under every reading, since every opening bracket has a corresponding closing bracket and R-RET-1 then requires True."
- R-EX-4, "correct_bracketing(")(()")": both took "This example holds: correct_bracketing(")(()") returns True. This contradicts R-RET-1 read as a biconditional with nested matching (the "(" at index 1 has no matching ")", so False would be required) or with whole-string correctness (the leading ")" is unmatched); it agrees with the sufficient-only, counting or positional-but-not-exclusive readings."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-IN-1-A (R-IN-1): every call meets `valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-IN-1-D-RES (R-IN-1): `result` is free when `!valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-IN-1-D-OUT (R-IN-1): `outcome` is free when `!valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
