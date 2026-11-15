# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 20.

## Questions
1. **scenario** (R-EX-1): the behaviour RA-EX-1 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
2. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **scenario** (R-EX-3): the behaviour RA-EX-3 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
4. **scenario** (R-EX-4): the behaviour RA-EX-4 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
5. **scenario** (R-EX-1): the behaviour RB-EX-1 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
6. **scenario** (R-EX-2): the behaviour RB-EX-2 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
7. **scenario** (R-EX-3): the behaviour RB-EX-3 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
8. **scenario** (R-EX-4): the behaviour RB-EX-4 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
9. **depends** (R-RET-1, R-RET-2, R-RET-3): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `will_it_fly([0], 0) -> True`
10. **ambiguity** (R-RET-1): "returns True if the object q will fly" can mean: As stated: a balanced q with sum at most w makes the call return True. / As the examples show (contradiction): a balanced q with sum at most w makes the call return False, e.g. will_it_fly([3, 2, 3], 9) ➞ False and will_it_fly([3], 5) ➞ False; all four examples return the opposite of the stated rule.. Which is meant?
11. **ambiguity** (R-RET-2): "False otherwise" can mean: As stated: an unbalanced q makes the call return False. / As the example shows (contradiction): an unbalanced q with sum at most w makes the call return True, e.g. will_it_fly([1, 2], 5) ➞ True.. Which is meant?
12. **ambiguity** (R-RET-3): "False otherwise" can mean: As stated: a q whose sum exceeds w makes the call return False. / As the example shows (contradiction): a balanced q whose sum exceeds w makes the call return True, e.g. will_it_fly([3, 2, 3], 1) ➞ True.. Which is meant?
13. **ambiguity** (R-EX-1): "➞ True" can mean: As written: the call returns True. This contradicts the rule (R-RET-2: [1, 2] is not a palindrome, so the call returns False) and the example's own comment (R-WHY-1: it's unbalanced). / The expected value is an error: the call returns False, as the rule and the comment imply.. Which is meant?
14. **ambiguity** (R-WHY-1): "but it's unbalanced" can mean: The comment explains a False result: an unbalanced list does not fly. This contradicts the stated result will_it_fly([1, 2], 5) ➞ True (R-EX-1). / The comment is consistent with the stated result True, i.e. the returned value is True when q does not fly (inverted output).. Which is meant?
15. **ambiguity** (R-EX-2): "➞ True" can mean: As written: the call returns True. This contradicts the rule (R-RET-3: 3+2+3 = 8 is greater than 1, so the call returns False) and the example's own comment (R-WHY-2: more than the maximum possible weight). / The expected value is an error: the call returns False, as the rule and the comment imply.. Which is meant?
16. **ambiguity** (R-WHY-2): "but 3+2+3 is more than the maximum possible weight" can mean: The comment explains a False result: an overweight list does not fly. This contradicts the stated result will_it_fly([3, 2, 3], 1) ➞ True (R-EX-2). / The comment is consistent with the stated result True, i.e. the returned value is True when q does not fly (inverted output).. Which is meant?
17. **ambiguity** (R-EX-3): "➞ False" can mean: As written: the call returns False. This contradicts the rule (R-RET-1: [3, 2, 3] is a palindrome and 3+2+3 = 8 is at most 9, so the call returns True) and the example's own comment (R-WHY-3: less than the maximum weight, and balanced). / The expected value is an error: the call returns True, as the rule and the comment imply.. Which is meant?
18. **ambiguity** (R-WHY-3): "and it's balanced" can mean: The comment explains a True result: a balanced list within the weight limit flies. This contradicts the stated result will_it_fly([3, 2, 3], 9) ➞ False (R-EX-3). / The comment is consistent with the stated result False, i.e. the returned value is False when q flies (inverted output).. Which is meant?
19. **ambiguity** (R-EX-4): "➞ False" can mean: As written: the call returns False. This contradicts the rule (R-RET-1: [3] is a palindrome and 3 is at most 5, so the call returns True) and the example's own comment (R-WHY-4: less than the maximum weight, and balanced). / The expected value is an error: the call returns True, as the rule and the comment imply.. Which is meant?
20. **ambiguity** (R-WHY-4): "and it's balanced" can mean: The comment explains a True result: a balanced list within the weight limit flies. This contradicts the stated result will_it_fly([3], 5) ➞ False (R-EX-4). / The comment is consistent with the stated result False, i.e. the returned value is False when q flies (inverted output).. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-DEF-1, "palindromic list": both took "The empty list is a palindrome, so it is balanced."
- R-DEF-3, "will fly if": both took "If and only if: q flies exactly when it is balanced and its sum is at most w; in every other case it does not fly."
- R-RET-1, "returns True if the object q will fly": both took "As stated: a balanced q with sum at most w makes the call return True."
- R-RET-2, "False otherwise": both took "As stated: an unbalanced q makes the call return False."
- R-RET-3, "False otherwise": both took "As stated: a q whose sum exceeds w makes the call return False."
- R-EX-1, "➞ True": both took "As written: the call returns True. This contradicts the rule (R-RET-2: [1, 2] is not a palindrome, so the call returns False) and the example's own comment (R-WHY-1: it's unbalanced)."
- R-WHY-1, "but it's unbalanced": both took "The comment explains a False result: an unbalanced list does not fly. This contradicts the stated result will_it_fly([1, 2], 5) ➞ True (R-EX-1)."
- R-EX-2, "➞ True": both took "As written: the call returns True. This contradicts the rule (R-RET-3: 3+2+3 = 8 is greater than 1, so the call returns False) and the example's own comment (R-WHY-2: more than the maximum possible weight)."
- R-WHY-2, "but 3+2+3 is more than the maximum possible weight": both took "The comment explains a False result: an overweight list does not fly. This contradicts the stated result will_it_fly([3, 2, 3], 1) ➞ True (R-EX-2)."
- R-EX-3, "➞ False": both took "As written: the call returns False. This contradicts the rule (R-RET-1: [3, 2, 3] is a palindrome and 3+2+3 = 8 is at most 9, so the call returns True) and the example's own comment (R-WHY-3: less than the maximum weight, and balanced)."
- R-WHY-3, "and it's balanced": both took "The comment explains a True result: a balanced list within the weight limit flies. This contradicts the stated result will_it_fly([3, 2, 3], 9) ➞ False (R-EX-3)."
- R-EX-4, "➞ False": both took "As written: the call returns False. This contradicts the rule (R-RET-1: [3] is a palindrome and 3 is at most 5, so the call returns True) and the example's own comment (R-WHY-4: less than the maximum weight, and balanced)."
- R-WHY-4, "and it's balanced": both took "The comment explains a True result: a balanced list within the weight limit flies. This contradicts the stated result will_it_fly([3], 5) ➞ False (R-EX-4)."
