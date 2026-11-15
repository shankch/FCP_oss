# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 8.

## Questions
1. **depends** (R-EX-1, R-EX-2, R-EX-3, R-EX-4, R-RES-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
2. **ambiguity** (R-RES-1): "corresponding closing bracket" can mean: Order-sensitive matching: each "(" is paired one-to-one with a ")" that comes after it, matched with nesting (the usual left-to-right stack/counter matching). / Order-insensitive matching: each "(" is paired one-to-one with some ")" anywhere in the string, so only the counts matter. CONTRADICTION with R-EX-4: under this reading ")(()" (two "(", two ")") would return True, but the example says False.. Which is meant?
3. **ambiguity** (R-RES-1): "every opening bracket has" can mean: Full balance: the condition also requires that no ")" is left without a matching earlier "(" (a running count of "(" minus ")" never goes negative and ends at 0), so "())" and ")(" are not correctly bracketed. / Only opening brackets are constrained: surplus closing brackets that close nothing are allowed, so "())" is correctly bracketed (True) as long as every "(" is matched by a later ")".. Which is meant?
4. **ambiguity** (R-RES-1): "return True" can mean: The function returns the bool True. / The function returns any truthy value.. Which is meant?
5. **ambiguity** (R-RES-2): "return True if" can mean: If and only if: the function returns False whenever the condition fails (as the examples "(" and ")(()" show), so the result is exactly whether the string is correctly bracketed. / One direction only: the sentence constrains only the case where the condition holds; for other strings the result is not specified by this sentence (only the examples pin some of them to False).. Which is meant?
6. **ambiguity** (R-RES-2): "corresponding closing bracket" can mean: Order-sensitive matching: each "(" is paired one-to-one with a ")" that comes after it, matched with nesting. / Order-insensitive matching: each "(" is paired one-to-one with some ")" anywhere in the string, so only the counts matter.. Which is meant?
7. **ambiguity** (R-RES-2): "every opening bracket has" can mean: Full balance: a ")" with no matching earlier "(" also makes the condition fail, so the call returns False for "())" and ")(". / Only opening brackets are constrained: surplus closing brackets do not make the condition fail, so "())" does not have to return False.. Which is meant?
8. **ambiguity** (R-EX-4): "correct_bracketing(")(()") False" can mean: Consistent with R-RES-1 under order-sensitive matching: the ")" at position 0 closes nothing and the "(" at position 1 is never closed, so the string is not correctly bracketed. / CONTRADICTION with R-RES-1 under order-insensitive matching ("corresponding closing bracket" = any ")" anywhere): both "(" can be paired with the two ")", so R-RES-1 would require True, while this example requires False.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "a string of "(" and ")"": both took "A precondition on the caller: only "(" and ")" are ever passed; the outcome and result for a string containing any other character are unconstrained (don't care)."
- R-IN-1, "a string of": both took "Any length, including the empty string (which then has no opening bracket, so it is correctly bracketed)."
- R-RES-1, "corresponding closing bracket": both took "Order-sensitive matching: each "(" is paired one-to-one with a ")" that comes after it, matched with nesting (the usual left-to-right stack/counter matching)."
- R-RES-1, "every opening bracket has": both took "Only opening brackets are constrained: surplus closing brackets that close nothing are allowed, so "())" is correctly bracketed (True) as long as every "(" is matched by a later ")"."
- R-RES-1, "return True": both took "The function returns the bool True."
- R-RES-2, "return True if": both took "If and only if: the function returns False whenever the condition fails (as the examples "(" and ")(()" show), so the result is exactly whether the string is correctly bracketed."
- R-RES-2, "corresponding closing bracket": both took "Order-sensitive matching: each "(" is paired one-to-one with a ")" that comes after it, matched with nesting."
- R-RES-2, "every opening bracket has": both took "Only opening brackets are constrained: surplus closing brackets do not make the condition fail, so "())" does not have to return False."
- R-EX-4, "correct_bracketing(")(()") False": both took "Consistent with R-RES-1 under order-sensitive matching: the ")" at position 0 closes nothing and the "(" at position 1 is never closed, so the string is not correctly bracketed."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `chars_ok`; `chars_ok` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_a, RA-IN-1-DC-OUTCOME (R-IN-1): `outcome` is free when `!chars_ok`; `chars_ok` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_a, RA-IN-1-DC-RESULT (R-IN-1): `result` is free when `!chars_ok`; `chars_ok` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-A-IN-1 (R-IN-1): every call meets `valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-D-IN-OUTCOME (R-IN-1): `outcome` is free when `!valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`
- agent_b, RB-D-IN-RESULT (R-IN-1): `result` is free when `!valid`; `valid` is `all(i < len(brackets): brackets[i] == "(" || brackets[i] == ")")`

## Limits of this review
These searches stopped at their time budget. What they found stands; what lies beyond the budget was not searched:
- the comparison of agent_a and variant
- the comparison of agent_b and variant
