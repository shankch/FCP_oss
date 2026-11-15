# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 6.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-SC-1: candidate("(") returns False.

## Questions
1. **depends** (R-RET-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate(")(())()()))((())(((()((()())))()") -> False`
2. **ambiguity** (R-RET-1, R-RET-2): "has a corresponding closing or opening bracket" can mean: Proper nesting: each ')' is paired with the nearest earlier unpaired '(', each bracket is used in at most one pair, and every bracket is paired (no prefix has more ')' than '(', and the totals are equal). / Equal counts: the number of '(' equals the number of ')', in any order (each '(' paired one-to-one with any ')'). This contradicts the example candidate(")(()") == False, which has two of each. / Directional but not exclusive: every '(' has some ')' after it and every ')' has some '(' before it, and a bracket may serve as the partner of several others (so "(()" and "())" count as matched). / Literal respective reading: a closing bracket corresponds to another closing bracket and an opening bracket to another opening bracket. This contradicts the examples candidate("()") == True and candidate("(()())") == True.. Which is meant?
3. **ambiguity** (R-RET-2): "return True if" can mean: If and only if: every string in which some bracket is unmatched returns False, as the False examples show. / A sufficient condition only: the text says nothing about strings with an unmatched bracket, so any result (including None or an exception) is allowed for them.. Which is meant?
4. **ambiguity** (R-SC-2): "candidate("()")" can mean: Consistent with R-RET-1: an opening bracket corresponds to a closing bracket, so "()" is matched and the result is True. / Contradicts the literal respective reading of R-RET-1 (a closing bracket corresponds to a closing one, an opening to an opening), under which the lone '(' and ')' are unmatched and the result would not be True.. Which is meant?
5. **ambiguity** (R-SC-3): "candidate("(()())")" can mean: Consistent with R-RET-1: each opening bracket has a closing partner, so "(()())" is matched and the result is True. / Contradicts the literal respective reading of R-RET-1 (same-kind partners), under which three '(' and three ')' cannot all be paired and the result would not be True.. Which is meant?
6. **ambiguity** (R-SC-4): "candidate(")(()")" can mean: Consistent with R-RET-1 under the order-sensitive (nesting) reading: the first ')' has no earlier '(' to correspond to, so the result is False. / Contradicts R-RET-1 under the equal-count reading: ")(()" has two '(' and two ')', so every bracket can be given a partner and the result would be True.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "a string of "(" and ")"": both took "A precondition on the caller: strings containing any other character are outside the contract, and the function's behaviour on them is unconstrained."
- R-IN-1, "brackets is a string": both took "The empty string is a valid argument; it has no unmatched bracket, so the function returns True for it."
- R-RET-1, "has a corresponding closing or opening bracket": both took "Proper nesting: each ')' is paired with the nearest earlier unpaired '(', each bracket is used in at most one pair, and every bracket is paired (no prefix has more ')' than '(', and the totals are equal)."
- R-RET-2, "return True if": both took "If and only if: every string in which some bracket is unmatched returns False, as the False examples show."
- R-RET-2, "has a corresponding closing or opening bracket": both took "Proper nesting: each ')' is paired with the nearest earlier unpaired '(', each bracket is used in at most one pair, and every bracket is paired (no prefix has more ')' than '(', and the totals are equal)."
- R-SC-2, "candidate("()")": both took "Consistent with R-RET-1: an opening bracket corresponds to a closing bracket, so "()" is matched and the result is True."
- R-SC-3, "candidate("(()())")": both took "Consistent with R-RET-1: each opening bracket has a closing partner, so "(()())" is matched and the result is True."
- R-SC-4, "candidate(")(()")": both took "Consistent with R-RET-1 under the order-sensitive (nesting) reading: the first ')' has no earlier '(' to correspond to, so the result is False."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `only_brackets`; `only_brackets` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_a, RA-IN-1-D-RESULT (R-IN-1): `result` is free when `!only_brackets`; `only_brackets` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_a, RA-IN-1-D-OUTCOME (R-IN-1): `outcome` is free when `!only_brackets`; `only_brackets` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-IN-1-A1 (R-IN-1): every call meets `valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-IN-1-D1 (R-IN-1): `result` is free when `!valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-IN-1-D2 (R-IN-1): `outcome` is free when `!valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
