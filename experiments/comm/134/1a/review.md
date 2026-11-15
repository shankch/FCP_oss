# FCP review

Before any code: the request alone.

Settled: 3 requirements. Questions: 5.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: candidate("apple pie") returns False.
- R-EX-3: candidate("apple pi e ") (with a trailing space) returns False.
- R-EX-4: candidate("") (the empty string) returns False.

## Questions
1. **depends** (R-RET-1, R-RET-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate("A") -> False`
2. **ambiguity** (R-RET-1, R-RET-2): "the character with given position" can mean: The last character of txt (txt[-1]); this is consistent with all four examples. / The first character of txt (txt[0]); the example candidate("apple pi e") ➞ True contradicts this reading, since 'a' starts the word 'apple'. / The last non-space character of txt; the example candidate("apple pi e ") ➞ False contradicts this reading, since the last non-space 'e' stands alone. / A position supplied by the caller; the signature def candidate(txt): has no parameter for it, so this contradicts the signature and the position is unspecified.. Which is meant?
3. **ambiguity** (R-RET-1, R-RET-2): "an alphabetical character" can mean: An ASCII letter only: A to Z or a to z. / Any character for which Python's str.isalpha() is true, which in Latin-1 also includes letters such as 'é' (233), 'ß' (223), 'ª' (170) and 'µ' (181).. Which is meant?
4. **ambiguity** (R-RET-1, R-RET-2): "is not a part of a word" can mean: The character stands alone: every neighbouring character that exists (before and after it) is a space, i.e. it forms a one-character group; for the last character this means txt has length 1 or the character before it is a space. / The character is preceded by a space: a character at the very start of txt (e.g. txt == 'e') does not qualify, because there is no space before it. / Literally, the character belongs to no space-separated group of characters; since every non-space character belongs to some group (by the definition of 'word'), the condition can never hold and the function always returns False, contradicting the example candidate("apple pi e") ➞ True.. Which is meant?
5. **ambiguity** (R-EX-2): "candidate("apple pi e") ➞ True" can mean: The example is authoritative: a lone letter separated by spaces (here the final 'e') is not part of a word, so a one-character group does not count as a word. / The definition of 'word' (a group of characters separated by space) is authoritative: the final 'e' is a one-character word, so it is part of a word and the expected value would be False; the example contradicts the definition.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IF-2, "def candidate(txt):": both took "The one-parameter signature is authoritative: the position of the checked character is fixed by the function itself (it is not an argument), so the 'given position' of the docstring must be read as a fixed position such as the last character."
- R-DEF-1, "separated by space": both took "Only the space character (code 32) separates words; tabs, newlines and other whitespace are ordinary characters inside a word."
- R-DEF-1, "a group of characters": both took "A word is any maximal run of non-space characters, whatever they are (letters, digits, punctuation): in 'pi 1e' the 'e' is part of the word '1e'."
- R-DEF-1, ""word" is a group of characters": both took "A word has at least two characters, so a lone letter between spaces (or at the start/end of the string) is not part of a word; this agrees with the example candidate("apple pi e") ➞ True."
- R-RET-1, "the character with given position": both took "The last character of txt (txt[-1]); this is consistent with all four examples."
- R-RET-1, "an alphabetical character": both took "An ASCII letter only: A to Z or a to z."
- R-RET-1, "is not a part of a word": both took "The character stands alone: every neighbouring character that exists (before and after it) is a space, i.e. it forms a one-character group; for the last character this means txt has length 1 or the character before it is a space."
- R-RET-2, "the character with given position": both took "The last character of txt (txt[-1]); this is consistent with all four examples."
- R-RET-2, "an alphabetical character": both took "An ASCII letter only: A to Z or a to z."
- R-RET-2, "is not a part of a word": both took "The character stands alone: every neighbouring character that exists (before and after it) is a space, i.e. it forms a one-character group; for the last character this means txt has length 1 or the character before it is a space."
- R-EX-2, "candidate("apple pi e") ➞ True": both took "The example is authoritative: a lone letter separated by spaces (here the final 'e') is not part of a word, so a one-character group does not count as a word."
