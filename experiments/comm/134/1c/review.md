# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 12.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RES-3: For every string txt, including the empty string, the function returns a boolean (True or False); it does not raise an exception, fail to finish, or return a value of another type.

## Questions
1. **conflict** (R-EX-4, R-RES-2): no implementation can meet these requirements on these calls: which one gives way? (also with , at 2 places)
   - `check_if_last_char_is_a_letter("")`
2. **conflict** (R-EX-1, R-RES-2): no implementation can meet these requirements on these calls: which one gives way? (also with , at 2 places)
   - `check_if_last_char_is_a_letter("apple pie")`
3. **depends** (R-RES-1, R-RES-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `check_if_last_char_is_a_letter("A") -> False`
4. **ambiguity** (R-RES-1): "the last character" can mean: The final character of txt (txt[-1]), even when it is a space. / The last non-space character of txt: trailing spaces are ignored, as example R-EX-3 ("apple pi e " gives True) suggests.. Which is meant?
5. **ambiguity** (R-RES-1): "an alphabetical character" can mean: An ASCII letter: a to z or A to Z. / Any character for which Python's str.isalpha() is true, including Latin-1 letters above code 127 such as é.. Which is meant?
6. **ambiguity** (R-RES-1): "is not a part of a word" can mean: The last character stands alone: it is the first character of txt or is preceded by a space, so the last group of txt is exactly that one character. / By the note (R-DEF-1) a one-character group is itself a word, so an alphabetical last character is always part of a word and the function never returns True.. Which is meant?
7. **ambiguity** (R-RES-1): "returns True" can mean: The rule is authoritative: "apple pi e" (last character e standing alone) returns True, contradicting example R-EX-2 which says False. / Example R-EX-2 is authoritative: "apple pi e" returns False, contradicting this rule. / The examples R-EX-1 to R-EX-4 state the intended behaviour, which is the negation of the rule: True unless the last character is an alphabetical character that is not part of a word.. Which is meant?
8. **ambiguity** (R-RES-2): "False otherwise" can mean: The rule is authoritative: every other string returns False, including "apple pie" (last character inside the word "pie"), "apple pi e " (last character a space) and "" (no last character), contradicting examples R-EX-1, R-EX-3 and R-EX-4, which say True. / The examples are authoritative exceptions: "apple pie", "apple pi e " and "" return True, contradicting this rule. / The examples state the intended behaviour, which is the negation of the rule: False exactly when the last character is an alphabetical character that is not part of a word, and True otherwise.. Which is meant?
9. **ambiguity** (R-EX-1): ""apple pie") ➞ True" can mean: The example is authoritative: "apple pie" returns True, although its last character e is part of the word "pie", so R-RES-2 gives False. / R-RES-2 is authoritative: "apple pie" returns False and the example is wrong.. Which is meant?
10. **ambiguity** (R-EX-2): ""apple pi e") ➞ False" can mean: The example is authoritative: "apple pi e" returns False, although its last character e is a letter standing alone, so R-RES-1 gives True. / R-RES-1 is authoritative: "apple pi e" returns True and the example is wrong. / A one-character group is itself a word (R-DEF-1), so the final e is part of the word "e" and False agrees with R-RES-2.. Which is meant?
11. **ambiguity** (R-EX-3): ""apple pi e ") ➞ True" can mean: The example is authoritative: "apple pi e " returns True, although its last character is a space, not an alphabetical character, so R-RES-2 gives False. / R-RES-2 is authoritative: "apple pi e " returns False and the example is wrong. / "The last character" means the last non-space character: the final e stands alone and True agrees with R-RES-1; but then "apple pi e" has the same last letter in the same position and should also return True, contradicting R-EX-2.. Which is meant?
12. **ambiguity** (R-EX-4): "("") ➞ True" can mean: The example is authoritative: the empty string returns True, although it has no last character, so R-RES-2 gives False. / R-RES-2 is authoritative: the empty string returns False and the example is wrong.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-DEF-1, "a group of characters": both took "A group has two or more characters: a single character standing alone between spaces is not a word."
- R-DEF-1, "separated by space": both took "Only the space character (code 32) separates words; a tab, newline or other whitespace character is part of a word."
- R-DEF-1, ""word" is a group": both took "A word is a maximal run of non-space characters of any kind, so in "ab 1e" the final e is part of the word "1e"."
- R-RES-1, "the last character": both took "The final character of txt (txt[-1]), even when it is a space."
- R-RES-1, "an alphabetical character": both took "An ASCII letter: a to z or A to Z."
- R-RES-1, "is not a part of a word": both took "The last character stands alone: it is the first character of txt or is preceded by a space, so the last group of txt is exactly that one character."
- R-RES-1, "returns True": both took "The rule is authoritative: "apple pi e" (last character e standing alone) returns True, contradicting example R-EX-2 which says False."
- R-RES-2, "False otherwise": both took "The rule is authoritative: every other string returns False, including "apple pie" (last character inside the word "pie"), "apple pi e " (last character a space) and "" (no last character), contradicting examples R-EX-1, R-EX-3 and R-EX-4, which say True."
- R-EX-1, ""apple pie") ➞ True": both took "The example is authoritative: "apple pie" returns True, although its last character e is part of the word "pie", so R-RES-2 gives False."
- R-EX-2, ""apple pi e") ➞ False": both took "The example is authoritative: "apple pi e" returns False, although its last character e is a letter standing alone, so R-RES-1 gives True."
- R-EX-3, ""apple pi e ") ➞ True": both took "The example is authoritative: "apple pi e " returns True, although its last character is a space, not an alphabetical character, so R-RES-2 gives False."
- R-EX-4, "("") ➞ True": both took "The example is authoritative: the empty string returns True, although it has no last character, so R-RES-2 gives False."
