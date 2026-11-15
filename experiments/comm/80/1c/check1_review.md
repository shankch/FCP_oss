# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 33.

## Questions
1. **conflict** (R-EX-1, R-HAP-2): no implementation can meet these requirements on these calls: which one gives way?
   - `is_happy("a")`
2. **conflict** (R-EX-5, R-HAP-1): no implementation can meet these requirements on these calls: which one gives way?
   - `is_happy("adb")`
3. **conflict** (R-EX-6, R-HAP-3): no implementation can meet these requirements on these calls: which one gives way?
   - `is_happy("xyy")`
4. **conflict** (R-EX-4, R-HAP-3): no implementation can meet these requirements on these calls: which one gives way?
   - `is_happy("aabb")`
5. **scenario** (R-EX-1): the behaviour RA-EX-1 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
6. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
7. **scenario** (R-EX-3): the behaviour RA-EX-3 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
8. **scenario** (R-EX-4): the behaviour RA-EX-4 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
9. **scenario** (R-EX-5): the behaviour RA-EX-5 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
10. **scenario** (R-EX-6): the behaviour RA-EX-6 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
11. **depends** (R-HAP-1, R-HAP-2, R-HAP-3, R-OUT-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `is_happy("abcd") -> True`
12. **ambiguity** (R-OUT-1): "check if the string is happy or not" can mean: return the bool True when the string is happy and the bool False when it is not / return any truthy value when the string is happy and any falsy value when it is not (for example 1 and 0, or None). Which is meant?
13. **ambiguity** (R-HAP-1, R-HAP-3): "letters" can mean: every character of s counts as a letter, whatever its class / only alphabetic characters count: other characters are dropped before the groups of 3 consecutive letters are formed / a string that contains a character other than a letter is not happy. Which is meant?
14. **ambiguity** (R-HAP-1, R-HAP-2): "its length" can mean: the number of characters of s / the number of letters (alphabetic characters) in s. Which is meant?
15. **ambiguity** (R-HAP-1, R-HAP-3): "3 consecutive letters" can mean: every overlapping window s[i], s[i+1], s[i+2], for each start i from 0 to len(s)-3 / the non-overlapping blocks s[0..2], s[3..5], ... (a trailing block shorter than 3 is ignored). Which is meant?
16. **ambiguity** (R-HAP-1, R-HAP-3): "distinct" can mean: the three characters are pairwise different by exact character code (so 'a' and 'A' differ) / the three characters are pairwise different when letter case is ignored / the three characters are not all the same (at least two of them differ) / each group of 3 consecutive letters differs, as a substring, from every other such group. Which is meant?
17. **ambiguity** (R-HAP-1): "A string is happy if its length is at least 3 and every 3 consecutive letters are distinct" can mean: the definition is authoritative: 'abcd' and 'adb' meet both conditions, so is_happy returns True for them, which contradicts the examples R-EX-3 and R-EX-5 / the examples are authoritative: is_happy('abcd') and is_happy('adb') return False, so meeting both conditions does not force the result True / every example is the negation of the definition, so is_happy returns True exactly when the string is not happy. Which is meant?
18. **ambiguity** (R-HAP-2): "is happy if" can mean: if and only if: a string with fewer than 3 characters is not happy, so is_happy returns False for it / if only (a sufficient condition): the definition does not say whether a string with fewer than 3 characters is happy, so either answer is allowed. Which is meant?
19. **ambiguity** (R-HAP-2): "its length is at least 3" can mean: the definition is authoritative: 'a' and 'aa' are shorter than 3, so is_happy returns False for them, which contradicts the examples R-EX-1 and R-EX-2 / the examples are authoritative: is_happy('a') and is_happy('aa') return True, so a string shorter than 3 can be happy / every example is the negation of the definition, so is_happy returns True exactly when the string is not happy. Which is meant?
20. **ambiguity** (R-HAP-3): "is happy if" can mean: if and only if: a string with a repeated character among some 3 consecutive letters is not happy, so is_happy returns False for it / if only (a sufficient condition): the definition does not say whether such a string is happy, so either answer is allowed. Which is meant?
21. **ambiguity** (R-HAP-3): "every 3 consecutive letters are distinct" can mean: the definition is authoritative: 'aabb' (window 'aab') and 'xyy' (window 'xyy') repeat a character, so is_happy returns False for them, which contradicts the examples R-EX-4 and R-EX-6 / the examples are authoritative: is_happy('aabb') and is_happy('xyy') return True, so a repeated character among 3 consecutive letters does not force the result False / every example is the negation of the definition, so is_happy returns True exactly when the string is not happy. Which is meant?
22. **ambiguity** (R-EX-1): "is_happy(a)" can mean: the argument is the string 'a' (the quotes are omitted) / a is a variable whose value is not given, so the example fixes no particular call. Which is meant?
23. **ambiguity** (R-EX-1): "is_happy(a) => True" can mean: the example is authoritative: is_happy('a') returns True / the definition is authoritative: 'a' is shorter than 3 characters, so it is not happy and is_happy('a') returns False (R-HAP-2); the example contradicts the definition. Which is meant?
24. **ambiguity** (R-EX-2): "is_happy(aa)" can mean: the argument is the string 'aa' (the quotes are omitted) / aa is a variable whose value is not given, so the example fixes no particular call. Which is meant?
25. **ambiguity** (R-EX-2): "is_happy(aa) => True" can mean: the example is authoritative: is_happy('aa') returns True / the definition is authoritative: 'aa' is shorter than 3 characters, so it is not happy and is_happy('aa') returns False (R-HAP-2); the example contradicts the definition. Which is meant?
26. **ambiguity** (R-EX-3): "is_happy(abcd)" can mean: the argument is the string 'abcd' (the quotes are omitted) / abcd is a variable whose value is not given, so the example fixes no particular call. Which is meant?
27. **ambiguity** (R-EX-3): "is_happy(abcd) => False" can mean: the example is authoritative: is_happy('abcd') returns False / the definition is authoritative: 'abcd' has 4 characters and its windows 'abc' and 'bcd' are each pairwise distinct, so it is happy and is_happy('abcd') returns True (R-HAP-1); the example contradicts the definition. Which is meant?
28. **ambiguity** (R-EX-4): "is_happy(aabb)" can mean: the argument is the string 'aabb' (the quotes are omitted) / aabb is a variable whose value is not given, so the example fixes no particular call. Which is meant?
29. **ambiguity** (R-EX-4): "is_happy(aabb) => True" can mean: the example is authoritative: is_happy('aabb') returns True / the definition is authoritative: the window 'aab' repeats 'a', so 'aabb' is not happy and is_happy('aabb') returns False (R-HAP-3); the example contradicts the definition. Which is meant?
30. **ambiguity** (R-EX-5): "is_happy(adb)" can mean: the argument is the string 'adb' (the quotes are omitted) / adb is a variable whose value is not given, so the example fixes no particular call. Which is meant?
31. **ambiguity** (R-EX-5): "is_happy(adb) => False" can mean: the example is authoritative: is_happy('adb') returns False / the definition is authoritative: 'adb' has 3 characters that are pairwise distinct, so it is happy and is_happy('adb') returns True (R-HAP-1); the example contradicts the definition. Which is meant?
32. **ambiguity** (R-EX-6): "is_happy(xyy)" can mean: the argument is the string 'xyy' (the quotes are omitted) / xyy is a variable whose value is not given, so the example fixes no particular call. Which is meant?
33. **ambiguity** (R-EX-6): "is_happy(xyy) => True" can mean: the example is authoritative: is_happy('xyy') returns True / the definition is authoritative: 'xyy' repeats 'y', so it is not happy and is_happy('xyy') returns False (R-HAP-3); the example contradicts the definition. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "a string": both took "any string, including the empty string and strings that contain characters other than letters"
- R-OUT-1, "check if the string is happy or not": both took "return the bool True when the string is happy and the bool False when it is not"
- R-HAP-1, "letters": both took "every character of s counts as a letter, whatever its class"
- R-HAP-1, "its length": both took "the number of characters of s"
- R-HAP-1, "3 consecutive letters": both took "every overlapping window s[i], s[i+1], s[i+2], for each start i from 0 to len(s)-3"
- R-HAP-1, "distinct": both took "the three characters are pairwise different by exact character code (so 'a' and 'A' differ)"
- R-HAP-1, "A string is happy if its length is at least 3 and every 3 consecutive letters are distinct": both took "the definition is authoritative: 'abcd' and 'adb' meet both conditions, so is_happy returns True for them, which contradicts the examples R-EX-3 and R-EX-5"
- R-HAP-2, "is happy if": both took "if and only if: a string with fewer than 3 characters is not happy, so is_happy returns False for it"
- R-HAP-2, "its length": both took "the number of characters of s"
- R-HAP-2, "its length is at least 3": both took "the definition is authoritative: 'a' and 'aa' are shorter than 3, so is_happy returns False for them, which contradicts the examples R-EX-1 and R-EX-2"
- R-HAP-3, "is happy if": both took "if and only if: a string with a repeated character among some 3 consecutive letters is not happy, so is_happy returns False for it"
- R-HAP-3, "letters": both took "every character of s counts as a letter, whatever its class"
- R-HAP-3, "3 consecutive letters": both took "every overlapping window s[i], s[i+1], s[i+2], for each start i from 0 to len(s)-3"
- R-HAP-3, "distinct": both took "the three characters are pairwise different by exact character code (so 'a' and 'A' differ)"
- R-HAP-3, "every 3 consecutive letters are distinct": both took "the definition is authoritative: 'aabb' (window 'aab') and 'xyy' (window 'xyy') repeat a character, so is_happy returns False for them, which contradicts the examples R-EX-4 and R-EX-6"
- R-EX-1, "is_happy(a)": both took "the argument is the string 'a' (the quotes are omitted)"
- R-EX-1, "is_happy(a) => True": both took "the example is authoritative: is_happy('a') returns True"
- R-EX-2, "is_happy(aa)": both took "the argument is the string 'aa' (the quotes are omitted)"
- R-EX-2, "is_happy(aa) => True": both took "the example is authoritative: is_happy('aa') returns True"
- R-EX-3, "is_happy(abcd)": both took "the argument is the string 'abcd' (the quotes are omitted)"
- R-EX-3, "is_happy(abcd) => False": both took "the example is authoritative: is_happy('abcd') returns False"
- R-EX-4, "is_happy(aabb)": both took "the argument is the string 'aabb' (the quotes are omitted)"
- R-EX-4, "is_happy(aabb) => True": both took "the example is authoritative: is_happy('aabb') returns True"
- R-EX-5, "is_happy(adb)": both took "the argument is the string 'adb' (the quotes are omitted)"
- R-EX-5, "is_happy(adb) => False": both took "the example is authoritative: is_happy('adb') returns False"
- R-EX-6, "is_happy(xyy)": both took "the argument is the string 'xyy' (the quotes are omitted)"
- R-EX-6, "is_happy(xyy) => True": both took "the example is authoritative: is_happy('xyy') returns True"

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the comparison of agent_a and variant
