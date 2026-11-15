# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 5.

## Questions
1. **open** (result, R-CHK-2, R-CHK-3): the request allows False or True (the reading leaves this free on purpose: RA-CHK-2, RA-CHK-3): is any answer acceptable, or which is meant?
   - `candidate("")`
2. **depends** (R-CHK-1, R-CHK-2, R-CHK-3): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate("") -> returned something else`
3. **ambiguity** (R-CHK-1): "Checks if" can mean: returns the answer as a bool, True or False / returns any truthy or falsy value (such as 1/0, the string itself, or None for no) / reports a failed check by raising an exception or failing an assertion instead of returning False. Which is meant?
4. **ambiguity** (R-CHK-2, R-CHK-3): "is a" can mean: a palindrome compared exactly: text equals its reverse character by character, with case, spaces and punctuation significant / a palindrome ignoring case and non-alphanumeric characters: only letters and digits are compared, case-insensitively / some other property the prompt does not state, so no particular answer is required for any string. Which is meant?
5. **ambiguity** (R-CHK-2, R-CHK-3): "given string" can mean: every string, including the empty string, is judged by the same rule (under a palindrome reading the empty string is one) / only non-empty strings are meant; the answer for the empty string is unspecified. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-TASK-1, "Complete this function": both took "write only the body of candidate below the given signature and docstring, leaving both as they are"
- R-IF-2, "text: str": both took "a type hint only: callers always pass a str, and behaviour for other types is unconstrained"
- R-CHK-1, "Checks if": both took "returns the answer as a bool, True or False"
- R-CHK-2, "is a": both took "some other property the prompt does not state, so no particular answer is required for any string"
- R-CHK-2, "given string": both took "every string, including the empty string, is judged by the same rule (under a palindrome reading the empty string is one)"
- R-CHK-3, "is a": both took "some other property the prompt does not state, so no particular answer is required for any string"
- R-CHK-3, "given string": both took "every string, including the empty string, is judged by the same rule (under a palindrome reading the empty string is one)"

## Taken as given
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-CHK-2 (R-CHK-2): `result` is free when `outcome == 0`
- agent_a, RA-CHK-3 (R-CHK-3): `result` is free when `outcome == 0`
- agent_b, RB-CHK2-FREE (R-CHK-2): `result` is free when `returned`; `returned` is `outcome == spec_outcome`
- agent_b, RB-CHK3-FREE (R-CHK-3): `result` is free when `returned`; `returned` is `outcome == spec_outcome`
