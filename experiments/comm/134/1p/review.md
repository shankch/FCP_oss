# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 11.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-4: candidate("") returns False (the empty string has no last character).

## Questions
1. **conflict** (R-EX-2, R-RET-3): no implementation can meet these requirements on these calls: which one gives way?
   - `candidate("apple pi e")`
2. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **depends** (R-RET-2, R-RET-3): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate("\u0001!\u0001!!!!!!\u0001!!!\u0001!!!!!!!!!! A      ") -> False`
4. **ambiguity** (R-RET-1): "returns True" can mean: the returned value is exactly the bool True or False / any truthy or falsy value (such as 1 and 0, or a non-empty and an empty string) is acceptable. Which is meant?
5. **ambiguity** (R-RET-2): "is ," can mean: literal: the last character is a comma ','; this contradicts R-EX-2, since "apple pi e" ends in 'e' yet must give True / the last character is an ASCII letter (a-z, A-Z) that stands alone: txt has length 1 or the character before it is a space (an alphabetical character that is not part of a longer word); consistent with every example / as the previous reading, but the character before the letter must be a space, so a one-character string such as "e" gives False / the last character is a letter standing alone, where 'letter' is whatever Python's str.isalpha accepts, so non-ASCII Latin-1 letters such as 'é' or 'ß' also count / the last character is a letter and the character before it, if any, is not a letter (a ',', '.', digit or space before it all qualify) / the last character is any alphabetical character, whatever precedes it; this contradicts R-EX-1, since "apple pie" ends in the letter 'e' yet must give False / the last character is an alphabetical character that is not part of a word as R-DEF-1 defines it; a single letter between spaces is itself a word, so no letter qualifies and the result is always False, which contradicts R-EX-2. Which is meant?
6. **ambiguity** (R-RET-2): "the last character" can mean: the final character of txt, whatever it is, so a trailing space is the last character; consistent with R-EX-3 / the last non-space character of txt, ignoring trailing spaces; then "apple pi e " is judged on its lone 'e' and would give True, which contradicts R-EX-3. Which is meant?
7. **ambiguity** (R-RET-3): "otherwise" can mean: whenever the last character lacks the property of R-RET-2, and also when txt is empty and so has no last character / only for non-empty strings whose last character lacks the property; the empty string, which has no last character, is not covered by this sentence (R-EX-4 gives it False). Which is meant?
8. **ambiguity** (R-RET-3): "False otherwise" can mean: consistent with R-EX-2 when the property of R-RET-2 is a letter standing alone at the end of txt / contradicts R-EX-2 under the literal property 'the last character is ,': "apple pi e" does not end in a comma, so this sentence requires False where R-EX-2 requires True. Which is meant?
9. **ambiguity** (R-EX-1): "candidate("apple pie") ➞ False" can mean: consistent with R-RET-2 when the property requires the final letter to stand alone, not to end a longer word / contradicts R-RET-2 when the property is only 'the last character is an alphabetical character': 'e' is a letter, so True would be required. Which is meant?
10. **ambiguity** (R-EX-2): "candidate("apple pi e") ➞ True" can mean: consistent with R-RET-2 when the property is a letter standing alone at the end of txt / contradicts R-RET-2 and R-RET-3 under the literal property 'the last character is ,': 'e' is not a comma, so False would be required / contradicts R-DEF-1 together with the property 'not a part of a word': by the note a lone 'e' is itself a word, so the last letter is part of a word and False would be required. Which is meant?
11. **ambiguity** (R-EX-3): "candidate("apple pi e ") ➞ False" can mean: consistent with R-RET-2 when the last character is the final character of txt, here a space / contradicts R-RET-2 when the last character means the last non-space character: the lone 'e' would then give True. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RET-1, "returns True": both took "the returned value is exactly the bool True or False"
- R-RET-2, "is ,": both took "literal: the last character is a comma ','; this contradicts R-EX-2, since "apple pi e" ends in 'e' yet must give True"
- R-RET-2, "the last character": both took "the final character of txt, whatever it is, so a trailing space is the last character; consistent with R-EX-3"
- R-RET-3, "otherwise": both took "whenever the last character lacks the property of R-RET-2, and also when txt is empty and so has no last character"
- R-RET-3, "False otherwise": both took "contradicts R-EX-2 under the literal property 'the last character is ,': "apple pi e" does not end in a comma, so this sentence requires False where R-EX-2 requires True"
- R-DEF-1, ""word"": both took "the note is left over and constrains nothing, since the request never uses the term 'word' elsewhere"
- R-DEF-1, "group of characters": both took "one or more characters, so a single letter between spaces is a word; then a lone final letter is part of a word, which contradicts R-EX-2 if the intended property is 'not a part of a word'"
- R-DEF-1, "space": both took "only the space character ' ' (code 32)"
- R-DEF-1, "separated by space": both took "a word is a maximal run of non-space characters, so digits and punctuation such as ',' or '.' belong to the word they touch"
- R-EX-1, "candidate("apple pie") ➞ False": both took "consistent with R-RET-2 when the property requires the final letter to stand alone, not to end a longer word"
- R-EX-2, "candidate("apple pi e") ➞ True": both took "contradicts R-RET-2 and R-RET-3 under the literal property 'the last character is ,': 'e' is not a comma, so False would be required"
- R-EX-3, "candidate("apple pi e ") ➞ False": both took "consistent with R-RET-2 when the last character is the final character of txt, here a space"
