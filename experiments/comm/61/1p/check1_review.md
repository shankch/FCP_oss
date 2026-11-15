# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 7.

## Questions
1. **depends** (R-RET-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `correct_bracketing("\u0001\u0001") -> raised another exception or did not finish`
2. **ambiguity** (R-RET-1): "False" can mean: the function returns a bool, as the example's False suggests (no return annotation is given) / the function may return any value whose truthiness gives the answer (e.g. 0/1). Which is meant?
3. **ambiguity** (R-RET-1): "correct_bracketing" can mean: 'correct' is an adjective: the function tells whether the bracketing is correct and returns a bool / 'correct' is a verb: the function corrects the bracketing and returns a fixed string; this reading contradicts the example R-EX-1, which returns False. Which is meant?
4. **ambiguity** (R-RES-1): "correct_bracketing" can mean: the function returns True exactly when the argument is correctly bracketed; this meaning is inferred from the name only, since the docstring never states what is returned / the function's meaning is fixed only by the example, and any answer is acceptable on other arguments. Which is meant?
5. **ambiguity** (R-RES-2): "correct_bracketing" can mean: the function returns False exactly when the argument is not correctly bracketed; this meaning is inferred from the name only, since the docstring never states what is returned / the function's meaning is fixed only by the example, and any answer is acceptable on other arguments. Which is meant?
6. **ambiguity** (R-EX-1): "correct_bracketing("(")" can mean: "(" is a valid argument (every character is '(' or ')'), so the example is within the input contract of R-IN-1 / "(" lacks a ')', so under the reading of R-IN-1 that the string contains both '(' and ')' the example lies outside the input contract, contradicting R-IN-1. Which is meant?
7. **ambiguity** (R-EX-1): "False" can mean: the function answers with a bool, consistent with R-RET-1 / under the verb reading of correct_bracketing (return a corrected string) a bool answer contradicts R-RET-1. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-TASK-1, "Complete this function": both took "write the body only, keeping the given signature and docstring unchanged"
- R-IN-1, "a string of "(" and ")"": both took "every character is '(' or ')', and the empty string is allowed"
- R-IN-1, "brackets is a string of "(" and ")"": both took "a precondition on the caller: arguments with other characters are out of contract and any outcome is acceptable"
- R-RET-1, "False": both took "the function returns a bool, as the example's False suggests (no return annotation is given)"
- R-RET-1, "correct_bracketing": both took "'correct' is an adjective: the function tells whether the bracketing is correct and returns a bool"
- R-DEF-1, "correct_bracketing": both took "properly nested: no prefix has more ')' than '(' and the totals are equal (")(" is not correct)"
- R-DEF-1, "correct_bracketing(brackets: str)": both took "the empty string is correctly bracketed (no unmatched bracket)"
- R-RES-1, "correct_bracketing": both took "the function returns True exactly when the argument is correctly bracketed; this meaning is inferred from the name only, since the docstring never states what is returned"
- R-RES-2, "correct_bracketing": both took "the function returns False exactly when the argument is not correctly bracketed; this meaning is inferred from the name only, since the docstring never states what is returned"
- R-EX-1, "correct_bracketing("(")": both took ""(" is a valid argument (every character is '(' or ')'), so the example is within the input contract of R-IN-1"
- R-EX-1, "False": both took "the function answers with a bool, consistent with R-RET-1"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1-OUT (R-IN-1): `outcome` is free when `!valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_a, RA-IN-1-RES (R-IN-1): `result` is free when `!valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-IN-1 (R-IN-1): every call meets `only_brackets`; `only_brackets` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-IN-DC-OUTCOME (R-IN-1): `outcome` is free when `!only_brackets`; `only_brackets` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-IN-DC-RESULT (R-IN-1): `result` is free when `!only_brackets`; `only_brackets` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
