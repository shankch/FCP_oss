# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 16.

## Questions
1. **scenario** (R-EX-1): the behaviour RA-EX-1 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
2. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **scenario** (R-EX-3): the behaviour RA-EX-3 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
4. **scenario** (R-EX-4): the behaviour RA-EX-4 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
5. **scenario** (R-EX-1): the behaviour RB-EX-1 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
6. **scenario** (R-EX-2): the behaviour RB-EX-2 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
7. **scenario** (R-EX-3): the behaviour RB-EX-3 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
8. **scenario** (R-EX-4): the behaviour RB-EX-4 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
9. **depends** (R-FN-1, R-FN-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `is_palindrome("\u00c0") -> True`
10. **ambiguity** (R-FN-1): "Checks if given string is a palindrome" can mean: The description (and the function name) governs: is_palindrome returns True for every palindrome. This contradicts the examples R-EX-2 (is_palindrome('aba') False), R-EX-3 (is_palindrome('aaaaa') False) and, if the empty string is a palindrome, R-EX-1 (is_palindrome('') False), which are then wrong. / The examples govern: the answer is inverted, and is_palindrome returns False for every palindrome (True exactly when text is not a palindrome), consistent with R-EX-1, R-EX-2, R-EX-3 and R-EX-4.. Which is meant?
11. **ambiguity** (R-FN-2): "Checks if given string is a palindrome" can mean: The description (and the function name) governs: is_palindrome returns False for every string that is not a palindrome. This contradicts the example R-EX-4 (is_palindrome('zbcd') True, although 'zbcd' is not a palindrome), which is then wrong. / The examples govern: the answer is inverted, and is_palindrome returns True for every string that is not a palindrome, as R-EX-4 (is_palindrome('zbcd') True) shows.. Which is meant?
12. **ambiguity** (R-FN-3): "Checks" can mean: The function returns exactly the bool True or False (as the examples print True and False). / The signature has no return annotation, so any value whose truth value gives the answer (such as 1/0, None, or a non-empty/empty value) is acceptable.. Which is meant?
13. **ambiguity** (R-EX-1): "False" can mean: The example is correct and the answer is inverted relative to the description: the empty string is a palindrome, so this contradicts R-FN-1, which requires True. / The example is correct because the empty string is not considered a palindrome (R-DEF-1, second reading of 'given string'); it is then consistent with R-FN-2. / The example is wrong: the empty string is a palindrome and the description (R-FN-1) governs, so is_palindrome('') returns True.. Which is meant?
14. **ambiguity** (R-EX-2): "False" can mean: The example is correct: is_palindrome('aba') returns False. This contradicts R-FN-1, because 'aba' reads the same backwards and the description requires True. / The example is wrong: the description (R-FN-1) governs and is_palindrome('aba') returns True.. Which is meant?
15. **ambiguity** (R-EX-3): "False" can mean: The example is correct: is_palindrome('aaaaa') returns False. This contradicts R-FN-1, because 'aaaaa' reads the same backwards and the description requires True. / The example is wrong: the description (R-FN-1) governs and is_palindrome('aaaaa') returns True.. Which is meant?
16. **ambiguity** (R-EX-4): "True" can mean: The example is correct: is_palindrome('zbcd') returns True. This contradicts R-FN-2, because 'zbcd' is not a palindrome (reversed it is 'dcbz') and the description requires False. / The example is wrong: the description (R-FN-2) governs and is_palindrome('zbcd') returns False.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-DEF-1, "palindrome": both took "Exact: the string equals its reverse with every character compared by its exact code (case-sensitive; spaces, punctuation and all other characters count), so 'Aa' and 'ab, a' are not palindromes."
- R-DEF-1, "given string": both took "Any string, including the empty string, which equals its reverse and is therefore a palindrome (as is every one-character string)."
- R-FN-1, "Checks if given string is a palindrome": both took "The description (and the function name) governs: is_palindrome returns True for every palindrome. This contradicts the examples R-EX-2 (is_palindrome('aba') False), R-EX-3 (is_palindrome('aaaaa') False) and, if the empty string is a palindrome, R-EX-1 (is_palindrome('') False), which are then wrong."
- R-FN-2, "Checks if given string is a palindrome": both took "The description (and the function name) governs: is_palindrome returns False for every string that is not a palindrome. This contradicts the example R-EX-4 (is_palindrome('zbcd') True, although 'zbcd' is not a palindrome), which is then wrong."
- R-FN-3, "Checks": both took "The function returns exactly the bool True or False (as the examples print True and False)."
- R-EX-1, "False": both took "The example is correct and the answer is inverted relative to the description: the empty string is a palindrome, so this contradicts R-FN-1, which requires True."
- R-EX-2, "False": both took "The example is correct: is_palindrome('aba') returns False. This contradicts R-FN-1, because 'aba' reads the same backwards and the description requires True."
- R-EX-3, "False": both took "The example is correct: is_palindrome('aaaaa') returns False. This contradicts R-FN-1, because 'aaaaa' reads the same backwards and the description requires True."
- R-EX-4, "True": both took "The example is correct: is_palindrome('zbcd') returns True. This contradicts R-FN-2, because 'zbcd' is not a palindrome (reversed it is 'dcbz') and the description requires False."
