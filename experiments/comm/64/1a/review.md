# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 10.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RET-1: Every call of candidate returns an integer (a count, so not negative) and raises no exception.

## Questions
1. **open** (result): the request allows 0 or 1: which is meant?
   - `candidate("Z")`
2. **depends** (R-RET-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate("PBBBBBBBBBABBBBBBBBBBBBBBBBBVBBB") -> 1`
3. **ambiguity** (R-RET-2): "the number of characters or vowels" can mean: The number of vowels in s (the 'characters' are the characters that are vowels); this is what both examples show. / The number of characters in s, i.e. len(s). This contradicts R-EX-1 ("abcde" has 5 characters but must give 2) and R-EX-2 ("ACEDY" has 5 characters but must give 3), and makes the vowel definition of R-VOW-1 pointless. / Either count is acceptable: the implementation may return len(s) or the vowel count.. Which is meant?
4. **ambiguity** (R-RET-2): "the number of ... vowels" can mean: Every occurrence counts: "aa" gives 2. / Distinct vowels count: "aa" gives 1. (Neither example repeats a vowel, so they do not decide.). Which is meant?
5. **ambiguity** (R-Y-1): "'y'" can mean: Lowercase only: a final 'Y' does not count. This contradicts R-EX-2, where "ACEDY" must give 3 and so its final 'Y' must count. / Case-insensitive: a final 'Y' counts too, as R-EX-2 implies.. Which is meant?
6. **ambiguity** (R-Y-1): "at the end of the given word" can mean: Only the last character of s: in "ayy" only the final 'y' counts. / Every 'y' in the trailing run of 'y's: in "ayy" both count. / The last letter of each word in s, if s holds several words. / The last letter of s, ignoring trailing non-letters (e.g. "day." counts its 'y').. Which is meant?
7. **ambiguity** (R-Y-2): "'y'" can mean: Applies to lowercase 'y' only (an uppercase 'Y' is never a vowel anywhere). / Applies to 'y' and 'Y' alike: neither counts unless it is at the end.. Which is meant?
8. **ambiguity** (R-Y-2): "at the end of the given word" can mean: Only the last character of s: in "ayy" the first 'y' does not count. / Every 'y' in the trailing run of 'y's counts, so in "ayy" neither 'y' is excluded. / The last letter of each word in s, if s holds several words: a 'y' before a space can count.. Which is meant?
9. **ambiguity** (R-EX-1): "2" can mean: Consistent with counting vowels (R-RET-2, first reading). / Contradicts R-RET-2 read as 'the number of characters': "abcde" has 5 characters.. Which is meant?
10. **ambiguity** (R-EX-2): "3" can mean: Consistent with counting vowels case-insensitively, with a final 'Y' counted. / Contradicts R-RET-2 read as 'the number of characters': "ACEDY" has 5 characters. / Contradicts R-VOW-1 read as lowercase only: 'A' and 'E' would not count (the result would be at most 1). / Contradicts R-Y-1 read as lowercase 'y' only: the final 'Y' would not count (the result would be 2 or 0).. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "a string representing a word": both took "Assumption on the caller: s holds only letters (ASCII a-z, A-Z) and is not empty; the result for any other string is unconstrained."
- R-IN-1, "a word": both took "The whole string is one word, so 'the end of the given word' is the last character of s."
- R-RET-2, "the number of ... vowels": both took "Every occurrence counts: "aa" gives 2."
- R-VOW-1, "'a', 'e', 'i', 'o', 'u'": both took "Case-insensitive: 'A', 'E', 'I', 'O', 'U' are vowels too, as R-EX-2 implies."
- R-VOW-1, "Vowels in this case are": both took "An exhaustive list: accented Latin-1 letters such as 'à', 'é' or 'Ü' are not vowels."
- R-Y-1, "'y'": both took "Case-insensitive: a final 'Y' counts too, as R-EX-2 implies."
- R-Y-1, "at the end of the given word": both took "Only the last character of s: in "ayy" only the final 'y' counts."
- R-Y-2, "'y'": both took "Applies to 'y' and 'Y' alike: neither counts unless it is at the end."
- R-Y-2, "at the end of the given word": both took "Only the last character of s: in "ayy" the first 'y' does not count."
- R-EX-1, "2": both took "Consistent with counting vowels (R-RET-2, first reading)."
- R-EX-2, "3": both took "Consistent with counting vowels case-insensitively, with a final 'Y' counted."
- R-FIX-1, "Add more test cases.": both took "An instruction to the assistant: the completed code should include additional test cases (e.g. more doctests)."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `word`; `word` is `len(s) >= 1 && all(k < len(s): isalpha(s[k]))`
- agent_b, RB-IN-1 (R-IN-1): every call meets `word`; `word` is `len(s) >= 1 && all(i < len(s): isalpha(s[i]))`
