# FCP review

Before any code: the request alone.

Settled: 4 requirements. Questions: 3.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: Called with the empty string, is_palindrome returns True.
- R-EX-2: Called with the string 'aba', is_palindrome returns True.
- R-EX-3: Called with the string 'aaaaa', is_palindrome returns True.
- R-EX-4: Called with the string 'zbcd', is_palindrome returns False.

## Questions
1. **depends** (R-PAL-1, R-PAL-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `is_palindrome("\u00c0\u00e0") -> False`
2. **ambiguity** (R-PAL-1, R-PAL-2): "palindrome" can mean: Strict: text equals its reversal character by character (case, spaces and punctuation count). / Case-insensitive: text equals its reversal after letters are mapped to one case; all other characters count. / Phrase palindrome: the letters and digits of text, compared ignoring case, read the same in both directions; spaces, punctuation and other characters are ignored.. Which is meant?
3. **ambiguity** (R-RET-1): "Checks" can mean: The function returns the answer as a bool, exactly True or False (as the doctest outputs show). / The function returns any value whose truthiness gives the answer (e.g. 1/0 or a non-empty/empty object would be acceptable).. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IF-1, "Complete this function": both took "Only the body is to be written; the given signature and docstring (with its doctests) are kept unchanged."
- R-DEF-1, "palindrome": both took "Strict: the string equals its reversal character by character; case, spaces, punctuation and every other character count (e.g. 'Aba' and 'a ba' are not palindromes)."
- R-PAL-1, "palindrome": both took "Strict: text equals its reversal character by character (case, spaces and punctuation count)."
- R-PAL-2, "palindrome": both took "Strict: text equals its reversal character by character (case, spaces and punctuation count)."
- R-RET-1, "Checks": both took "The function returns the answer as a bool, exactly True or False (as the doctest outputs show)."
