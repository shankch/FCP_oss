# FCP review

Before any code: the request alone.

Settled: 2 requirements. Questions: 8.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RET-1: For every string argument, candidate(text) returns a bool (True or False); it does not raise an exception, fail to finish, or return a value of another type such as None, a number or a string.
- R-EX-1: candidate('') (the empty string) returns True.

## Questions
1. **conflict** (R-CHK-1, R-EX-4): no implementation can meet these requirements on these calls: which one gives way?
   - `candidate("zbcd")`
2. **scenario** (R-EX-4): the behaviour RA-EX-4 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **depends** (R-CHK-1, R-CHK-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate("yCUAbWxvzZVXwBaucY") -> False`
4. **ambiguity** (R-CHK-1): "Isogram/Palindrome" can mean: either suffices: True when text is an isogram or a palindrome; contradicts R-EX-4, since 'zbcd' has no repeated letter and so is an isogram / both are needed: True only when text is both an isogram and a palindrome; contradicts R-EX-2 and R-EX-3, since 'aba' and 'aaaaa' repeat a letter / palindrome only: the check is whether text is a palindrome and 'Isogram' is a mislabel; the only reading consistent with all four examples / isogram only: the check is whether text is an isogram; contradicts R-EX-2, R-EX-3 and R-EX-4. Which is meant?
5. **ambiguity** (R-CHK-2): "Isogram/Palindrome" can mean: either suffices: False only when text is neither an isogram nor a palindrome; contradicts R-EX-4, since 'zbcd' has no repeated letter and so is an isogram / both are needed: False whenever text is not an isogram or not a palindrome; contradicts R-EX-2 and R-EX-3, since 'aba' and 'aaaaa' repeat a letter / palindrome only: False exactly when text is not a palindrome and 'Isogram' is a mislabel; the only reading consistent with all four examples / isogram only: False exactly when text is not an isogram; contradicts R-EX-2, R-EX-3 and R-EX-4. Which is meant?
6. **ambiguity** (R-EX-2): "candidate('aba')" can mean: the example is right: 'aba' returns True although the letter 'a' repeats, so being an isogram is not required; this contradicts R-CHK-1/R-CHK-2 when 'Isogram/Palindrome' is read as 'both' or 'isogram only' / the docstring is right and requires an isogram: 'aba' is not an isogram and returns False, so the example is wrong. Which is meant?
7. **ambiguity** (R-EX-3): "candidate('aaaaa')" can mean: the example is right: 'aaaaa' returns True although the letter 'a' repeats, so being an isogram (in the usual no-repeated-letter sense) is not required; this contradicts R-CHK-1/R-CHK-2 when 'Isogram/Palindrome' is read as 'both' or 'isogram only' / the docstring is right and requires an isogram: 'aaaaa' is not an isogram and returns False, so the example is wrong. Which is meant?
8. **ambiguity** (R-EX-4): "candidate('zbcd')" can mean: the example is right: 'zbcd' returns False although no letter repeats, so being an isogram is not enough for True; this contradicts R-CHK-1/R-CHK-2 when 'Isogram/Palindrome' is read as 'either suffices' or 'isogram only' / the docstring is right and an isogram suffices: 'zbcd' is an isogram and returns True, so the example is wrong. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-ENV-1, "text: str": both took "a type hint that constrains only the caller: candidate is only ever called with a str, and behaviour on other types is unspecified"
- R-DEF-1, "Palindrome": both took "exact: every character is compared as is, so letter case and spaces matter ('Aba' and 'ab a' are not palindromes)"
- R-DEF-2, "Isogram": both took "no letter occurs twice ignoring case; spaces, hyphens and other non-letters may repeat: 'aA' is not an isogram, 'a b c' is"
- R-CHK-1, "Isogram/Palindrome": both took "either suffices: True when text is an isogram or a palindrome; contradicts R-EX-4, since 'zbcd' has no repeated letter and so is an isogram"
- R-CHK-2, "Isogram/Palindrome": both took "either suffices: False only when text is neither an isogram nor a palindrome; contradicts R-EX-4, since 'zbcd' has no repeated letter and so is an isogram"
- R-EX-2, "candidate('aba')": both took "the example is right: 'aba' returns True although the letter 'a' repeats, so being an isogram is not required; this contradicts R-CHK-1/R-CHK-2 when 'Isogram/Palindrome' is read as 'both' or 'isogram only'"
- R-EX-3, "candidate('aaaaa')": both took "the example is right: 'aaaaa' returns True although the letter 'a' repeats, so being an isogram (in the usual no-repeated-letter sense) is not required; this contradicts R-CHK-1/R-CHK-2 when 'Isogram/Palindrome' is read as 'both' or 'isogram only'"
- R-EX-4, "candidate('zbcd')": both took "the example is right: 'zbcd' returns False although no letter repeats, so being an isogram is not enough for True; this contradicts R-CHK-1/R-CHK-2 when 'Isogram/Palindrome' is read as 'either suffices' or 'isogram only'"
