# FCP review

Before any code: the request alone.

Settled: 3 requirements. Questions: 7.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: check_if_last_char_is_a_letter("apple pie") returns False.
- R-EX-3: check_if_last_char_is_a_letter("apple pi e ") (with a trailing space) returns False.
- R-EX-4: check_if_last_char_is_a_letter("") (the empty string) returns False.

## Questions
1. **depends** (R-LAST-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `check_if_last_char_is_a_letter(" a                              ") -> False`
2. **ambiguity** (R-RET-1): "returns True" can mean: the function must return the Python bool values True and False exactly / any truthy value (e.g. 1) counts as True and any falsy value (e.g. 0 or None) counts as False. Which is meant?
3. **ambiguity** (R-LAST-1): "an alphabetical character" can mean: only the 52 ASCII letters a-z and A-Z / any character Python str.isalpha() accepts, including Latin-1 letters such as é, ß, ª, µ and º (codes 128-255). Which is meant?
4. **ambiguity** (R-LAST-1): "is not a part of a word" can mean: the last space-separated group (the text after the last space, or the whole string if it has no space) is exactly that one character, so a one-character string such as "e" gives True (matches the example "apple pi e" ➞ True) / the character immediately before the last character is a space, so a one-character string such as "e" gives False / literally per the Note, the last character belongs to no group of characters separated by space; every non-space character belongs to such a group, so the result is never True (contradicts the example "apple pi e" ➞ True). Which is meant?
5. **ambiguity** (R-LAST-1): "the last character" can mean: the final character of the string, even if it is a space (so "apple pi e " gives False, as its example says) / the last non-space character, ignoring trailing spaces (so "apple pi e " would give True, contradicting its example). Which is meant?
6. **ambiguity** (R-LAST-2): "otherwise" can mean: covers every string that does not meet the True condition, including the empty string, which has no last character, so "" gives False (matches the example "" ➞ False) / covers only non-empty strings, since the condition presupposes a last character; the result for the empty string is left unspecified. Which is meant?
7. **ambiguity** (R-EX-2): "("apple pi e") ➞ True" can mean: the example is correct and a lone letter between spaces is not part of a word, so a word needs at least two characters (overriding the Note) / the Note is correct and the lone final "e" is a one-character word, so the example contradicts the definition of "word" and the result should be False. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RET-1, "returns True": both took "the function must return the Python bool values True and False exactly"
- R-LAST-1, "an alphabetical character": both took "only the 52 ASCII letters a-z and A-Z"
- R-LAST-1, "is not a part of a word": both took "the last space-separated group (the text after the last space, or the whole string if it has no space) is exactly that one character, so a one-character string such as "e" gives True (matches the example "apple pi e" ➞ True)"
- R-LAST-1, "the last character": both took "the final character of the string, even if it is a space (so "apple pi e " gives False, as its example says)"
- R-LAST-2, "otherwise": both took "covers every string that does not meet the True condition, including the empty string, which has no last character, so "" gives False (matches the example "" ➞ False)"
- R-WORD-1, "a group of characters": both took "a word has at least two characters, so a lone character between spaces is not a word and "apple pi e" gives True, as its example says"
- R-WORD-1, "separated by space": both took "only the space character (code 32) separates words, so "apple\te" (with a tab) is one word"
- R-WORD-1, "group of characters": both took "any run of non-space characters is a word, including digits and punctuation, so "1e" and "x.e" are each one word ending in "e""
- R-EX-2, "("apple pi e") ➞ True": both took "the example is correct and a lone letter between spaces is not part of a word, so a word needs at least two characters (overriding the Note)"
