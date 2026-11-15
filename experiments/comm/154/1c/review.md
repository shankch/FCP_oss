# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 28.

## Questions
1. **scenario** (R-EX-1): the behaviour RA-EX-1 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
2. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **scenario** (R-EX-3): the behaviour RA-EX-3 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
4. **scenario** (R-EX-4): the behaviour RA-EX-4 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
5. **scenario** (R-EX-5): the behaviour RA-EX-5 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
6. **scenario** (R-EX-6): the behaviour RA-EX-6 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
7. **scenario** (R-EX-1): the behaviour RB-EX-1 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
8. **scenario** (R-EX-2): the behaviour RB-EX-2 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
9. **scenario** (R-EX-3): the behaviour RB-EX-3 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
10. **scenario** (R-EX-4): the behaviour RB-EX-4 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
11. **scenario** (R-EX-5): the behaviour RB-EX-5 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
12. **scenario** (R-EX-6): the behaviour RB-EX-6 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
13. **depends** (R-RES-1, R-RES-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `cycpattern_check("\u0001\u0001\u0001", "") -> True`
14. **ambiguity** (R-RES-1): "return True" can mean: The function returns the boolean True. / Any truthy value (such as 1 or a non-empty string) counts as returning True.. Which is meant?
15. **ambiguity** (R-RES-1): "the second word or any of its rotations" can mean: When b is empty, the empty string is a substring of every a, so the call returns True. / When b is empty there is nothing to find, so the condition does not hold and the call does not return True.. Which is meant?
16. **ambiguity** (R-RES-1): "cycpattern_check("hello","ell") => False" can mean: The rule wins: "ell" is a substring of "hello" ("hello"[1:4]), so cycpattern_check("hello", "ell") returns True and the example R-EX-2 is wrong. / The example R-EX-2 wins: the call returns False, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).. Which is meant?
17. **ambiguity** (R-RES-1): "cycpattern_check("abab","baa") => False" can mean: The rule wins: the rotation "aba" of "baa" is a substring of "abab" ("abab"[0:3]), so cycpattern_check("abab", "baa") returns True and the example R-EX-4 is wrong. / The example R-EX-4 wins: the call returns False, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).. Which is meant?
18. **ambiguity** (R-RES-1): "cycpattern_check("himenss","simen") => False" can mean: The rule wins: the rotation "imens" of "simen" is a substring of "himenss" ("himenss"[1:6]), so cycpattern_check("himenss", "simen") returns True and the example R-EX-6 is wrong. / The example R-EX-6 wins: the call returns False, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).. Which is meant?
19. **ambiguity** (R-RES-2): "return True if" can mean: "if" means "if and only if": when the condition does not hold, the function returns False. / Only the True case is specified: when the condition does not hold, the result is not specified (any outcome allowed).. Which is meant?
20. **ambiguity** (R-RES-2): "cycpattern_check("abcd","abd") => True" can mean: The rule wins: no rotation of "abd" ("abd", "bda", "dab") is a substring of "abcd" (whose 3-character substrings are "abc", "bcd"), so cycpattern_check("abcd", "abd") returns False and the example R-EX-1 is wrong. / The example R-EX-1 wins: the call returns True, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).. Which is meant?
21. **ambiguity** (R-RES-2): "cycpattern_check("whassup","psus") => True" can mean: The rule wins: no rotation of "psus" ("psus", "susp", "usps", "spsu") is a substring of "whassup" (whose 4-character substrings are "whas", "hass", "assu", "ssup"), so cycpattern_check("whassup", "psus") returns False and the example R-EX-3 is wrong. / The example R-EX-3 wins: the call returns True, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).. Which is meant?
22. **ambiguity** (R-RES-2): "cycpattern_check("efef","eeff") => True" can mean: The rule wins: no rotation of "eeff" ("eeff", "effe", "ffee", "feef") is a substring of "efef" (whose only 4-character substring is "efef"), so cycpattern_check("efef", "eeff") returns False and the example R-EX-5 is wrong. / The example R-EX-5 wins: the call returns True, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).. Which is meant?
23. **ambiguity** (R-EX-1): "cycpattern_check("abcd","abd") => True" can mean: The example is right: the call returns True, although no rotation of "abd" ("abd", "bda", "dab") is a substring of "abcd", which contradicts R-RES-2. / The rule R-RES-2 is right: the call returns False and the example is wrong.. Which is meant?
24. **ambiguity** (R-EX-2): "cycpattern_check("hello","ell") => False" can mean: The example is right: the call returns False, although "ell" is a substring of "hello", which contradicts R-RES-1. / The rule R-RES-1 is right: the call returns True and the example is wrong.. Which is meant?
25. **ambiguity** (R-EX-3): "cycpattern_check("whassup","psus") => True" can mean: The example is right: the call returns True, although no rotation of "psus" ("psus", "susp", "usps", "spsu") is a substring of "whassup", which contradicts R-RES-2. / The rule R-RES-2 is right: the call returns False and the example is wrong.. Which is meant?
26. **ambiguity** (R-EX-4): "cycpattern_check("abab","baa") => False" can mean: The example is right: the call returns False, although the rotation "aba" of "baa" is a substring of "abab", which contradicts R-RES-1. / The rule R-RES-1 is right: the call returns True and the example is wrong.. Which is meant?
27. **ambiguity** (R-EX-5): "cycpattern_check("efef","eeff") => True" can mean: The example is right: the call returns True, although no rotation of "eeff" ("eeff", "effe", "ffee", "feef") is a substring of "efef", which contradicts R-RES-2. / The rule R-RES-2 is right: the call returns False and the example is wrong.. Which is meant?
28. **ambiguity** (R-EX-6): "cycpattern_check("himenss","simen") => False" can mean: The example is right: the call returns False, although the rotation "imens" of "simen" is a substring of "himenss", which contradicts R-RES-1. / The rule R-RES-1 is right: the call returns True and the example is wrong.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-DEF-2, "rotations": both took "Cyclic shifts only: b[k:] + b[:k] for 0 <= k < len(b) ("abd" has the rotations "abd", "bda", "dab")."
- R-DEF-3, "substring": both took "Contiguous: s occurs in a as a run of adjacent characters (Python `s in a`)."
- R-DEF-3, "is a substring in the first word": both took "Characters are compared exactly (case-sensitive): "Ell" is not a substring of "hello"."
- R-IN-1, "words": both took "A non-empty string of letters only; calls where a or b is empty or contains a non-letter character are outside the contract (any outcome allowed)."
- R-RES-1, "return True": both took "The function returns the boolean True."
- R-RES-1, "the second word or any of its rotations": both took "When b is empty, the empty string is a substring of every a, so the call returns True."
- R-RES-1, "cycpattern_check("hello","ell") => False": both took "The rule wins: "ell" is a substring of "hello" ("hello"[1:4]), so cycpattern_check("hello", "ell") returns True and the example R-EX-2 is wrong."
- R-RES-1, "cycpattern_check("abab","baa") => False": both took "The rule wins: the rotation "aba" of "baa" is a substring of "abab" ("abab"[0:3]), so cycpattern_check("abab", "baa") returns True and the example R-EX-4 is wrong."
- R-RES-1, "cycpattern_check("himenss","simen") => False": both took "The rule wins: the rotation "imens" of "simen" is a substring of "himenss" ("himenss"[1:6]), so cycpattern_check("himenss", "simen") returns True and the example R-EX-6 is wrong."
- R-RES-2, "return True if": both took ""if" means "if and only if": when the condition does not hold, the function returns False."
- R-RES-2, "cycpattern_check("abcd","abd") => True": both took "The rule wins: no rotation of "abd" ("abd", "bda", "dab") is a substring of "abcd" (whose 3-character substrings are "abc", "bcd"), so cycpattern_check("abcd", "abd") returns False and the example R-EX-1 is wrong."
- R-RES-2, "cycpattern_check("whassup","psus") => True": both took "The rule wins: no rotation of "psus" ("psus", "susp", "usps", "spsu") is a substring of "whassup" (whose 4-character substrings are "whas", "hass", "assu", "ssup"), so cycpattern_check("whassup", "psus") returns False and the example R-EX-3 is wrong."
- R-RES-2, "cycpattern_check("efef","eeff") => True": both took "The rule wins: no rotation of "eeff" ("eeff", "effe", "ffee", "feef") is a substring of "efef" (whose only 4-character substring is "efef"), so cycpattern_check("efef", "eeff") returns False and the example R-EX-5 is wrong."
- R-EX-1, "cycpattern_check("abcd","abd") => True": both took "The example is right: the call returns True, although no rotation of "abd" ("abd", "bda", "dab") is a substring of "abcd", which contradicts R-RES-2."
- R-EX-2, "cycpattern_check("hello","ell") => False": both took "The example is right: the call returns False, although "ell" is a substring of "hello", which contradicts R-RES-1."
- R-EX-3, "cycpattern_check("whassup","psus") => True": both took "The example is right: the call returns True, although no rotation of "psus" ("psus", "susp", "usps", "spsu") is a substring of "whassup", which contradicts R-RES-2."
- R-EX-4, "cycpattern_check("abab","baa") => False": both took "The example is right: the call returns False, although the rotation "aba" of "baa" is a substring of "abab", which contradicts R-RES-1."
- R-EX-5, "cycpattern_check("efef","eeff") => True": both took "The example is right: the call returns True, although no rotation of "eeff" ("eeff", "effe", "ffee", "feef") is a substring of "efef", which contradicts R-RES-2."
- R-EX-6, "cycpattern_check("himenss","simen") => False": both took "The example is right: the call returns False, although the rotation "imens" of "simen" is a substring of "himenss", which contradicts R-RES-1."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `words`; `words` is `len(a) > 0 && len(b) > 0 && all(i < len(a): isalpha(a[i])) && all(j < len(b): isalpha(b[j]))`
- agent_b, RB-IN-1 (R-IN-1): every call meets `words`; `words` is `word_a && word_b`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- request points of agent_a
- request points of agent_b
