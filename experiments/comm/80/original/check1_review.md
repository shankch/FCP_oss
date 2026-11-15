# FCP review

Before any code: the request alone.

Settled: 4 requirements. Questions: 13.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: is_happy('a') returns False.
- R-EX-2: is_happy('aa') returns False.
- R-EX-3: is_happy('abcd') returns True.
- R-EX-5: is_happy('adb') returns True.

## Questions
1. **depends** (R-HAP-4, R-RET-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `is_happy("wfaafjifbcdaeghjklmnopqrstuvwxyz") -> False`
2. **ambiguity** (R-RET-1): "check" can mean: is_happy returns the Python bool True or False. / is_happy may return any truthy or falsy value (for example 1 or 0, or a non-empty or empty object).. Which is meant?
3. **ambiguity** (R-HAP-2): "happy if" can mean: 'if' means 'if and only if' (supported by 'happy or not'): every string shorter than 3 is not happy, so is_happy returns False. / 'if' gives only a sufficient condition: the rule leaves the result for strings shorter than 3 open, and only the examples 'a' and 'aa' give False.. Which is meant?
4. **ambiguity** (R-HAP-3): "happy if" can mean: 'if' means 'if and only if': a string with a window that is not distinct is not happy, so is_happy returns False. / 'if' gives only a sufficient condition: the rule leaves the result for such strings open.. Which is meant?
5. **ambiguity** (R-HAP-3): "every 3 consecutive letters" can mean: every overlapping window s[i], s[i+1], s[i+2] for i from 0 to len(s)-3. / non-overlapping blocks of three (positions 0-2, 3-5, ...), so 'abccde' (blocks 'abc', 'cde') would be happy.. Which is meant?
6. **ambiguity** (R-HAP-3, R-HAP-4): "letters" can mean: any characters: every window of 3 consecutive characters is checked, whatever the characters are. / only alphabetic letters count: non-letter characters are skipped and windows are taken over the sequence of letters. / a window that contains a non-letter character does not meet the condition, so such strings are not happy.. Which is meant?
7. **ambiguity** (R-HAP-3): "distinct" can mean: the three characters of each window are pairwise distinct (no two equal), so 'aba' gives False. / only adjacent characters must differ (s[i] != s[i+1] and s[i+1] != s[i+2]), so 'aba' gives True. This matches every example. / the three characters of a window are not all the same. This contradicts the examples is_happy(aabb) => False and is_happy(xyy) => False. / no 3-character window occurs twice in the string. This contradicts the examples is_happy(aabb) => False and is_happy(xyy) => False.. Which is meant?
8. **ambiguity** (R-HAP-3): "letters are distinct" can mean: characters are compared by code (case-sensitive), so 'aAb' gives True. / characters are compared ignoring case, so 'aAb' gives False.. Which is meant?
9. **ambiguity** (R-HAP-4): "every 3 consecutive letters" can mean: every overlapping window s[i], s[i+1], s[i+2] for i from 0 to len(s)-3. / non-overlapping blocks of three (positions 0-2, 3-5, ...), so 'abccde' (blocks 'abc', 'cde') gives True.. Which is meant?
10. **ambiguity** (R-HAP-4): "distinct" can mean: the three characters of each window are pairwise distinct (no two equal). / only adjacent characters must differ (s[i] != s[i+1] and s[i+1] != s[i+2]), so 'aba' gives True. This matches every example. / the three characters of a window are not all the same. This contradicts the examples is_happy(aabb) => False and is_happy(xyy) => False. / no 3-character window occurs twice in the string. This contradicts the examples is_happy(aabb) => False and is_happy(xyy) => False.. Which is meant?
11. **ambiguity** (R-HAP-4): "letters are distinct" can mean: characters are compared by code (case-sensitive), so 'aAb' gives True. / characters are compared ignoring case, so 'aAb' does not meet the condition.. Which is meant?
12. **ambiguity** (R-EX-4): "is_happy(aabb) => False" can mean: Matches the rule when 'distinct' means pairwise distinct or adjacent characters differ: the window 'aab' repeats 'a'. / Contradicts the rule when 'distinct' means 'not all three the same' or 'no 3-character window repeats': 'aab' and 'abb' then pass, so the rule gives True.. Which is meant?
13. **ambiguity** (R-EX-6): "is_happy(xyy) => False" can mean: Matches the rule when 'distinct' means pairwise distinct or adjacent characters differ: 'y' is repeated in the window 'xyy'. / Contradicts the rule when 'distinct' means 'not all three the same' or 'no 3-character window repeats': the single window 'xyy' then passes, so the rule gives True.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "a string": both took "s may be any string: any characters, including digits, spaces, punctuation, upper-case letters, and the empty string."
- R-RET-1, "check": both took "is_happy returns the Python bool True or False."
- R-HAP-1, "happy if": both took "'if' means 'if and only if': a string that fails either condition is not happy."
- R-HAP-1, "every 3 consecutive letters": both took "every overlapping window s[i], s[i+1], s[i+2] for i from 0 to len(s)-3."
- R-HAP-1, "letters": both took "any characters: every window of 3 consecutive characters is checked, whatever the characters are."
- R-HAP-1, "distinct": both took "the three characters of each window are pairwise distinct (no two equal), so 'aba' is not happy."
- R-HAP-1, "letters are distinct": both took "characters are compared by code (case-sensitive), so 'a' and 'A' are distinct."
- R-HAP-2, "happy if": both took "'if' means 'if and only if' (supported by 'happy or not'): every string shorter than 3 is not happy, so is_happy returns False."
- R-HAP-3, "happy if": both took "'if' means 'if and only if': a string with a window that is not distinct is not happy, so is_happy returns False."
- R-HAP-3, "every 3 consecutive letters": both took "every overlapping window s[i], s[i+1], s[i+2] for i from 0 to len(s)-3."
- R-HAP-3, "letters": both took "any characters: every window of 3 consecutive characters is checked, whatever the characters are."
- R-HAP-3, "distinct": both took "the three characters of each window are pairwise distinct (no two equal), so 'aba' gives False."
- R-HAP-3, "letters are distinct": both took "characters are compared by code (case-sensitive), so 'aAb' gives True."
- R-HAP-4, "every 3 consecutive letters": both took "every overlapping window s[i], s[i+1], s[i+2] for i from 0 to len(s)-3."
- R-HAP-4, "letters": both took "any characters: every window of 3 consecutive characters is checked, whatever the characters are."
- R-HAP-4, "distinct": both took "the three characters of each window are pairwise distinct (no two equal)."
- R-HAP-4, "letters are distinct": both took "characters are compared by code (case-sensitive), so 'aAb' gives True."
- R-EX-4, "is_happy(aabb) => False": both took "Matches the rule when 'distinct' means pairwise distinct or adjacent characters differ: the window 'aab' repeats 'a'."
- R-EX-6, "is_happy(xyy) => False": both took "Matches the rule when 'distinct' means pairwise distinct or adjacent characters differ: 'y' is repeated in the window 'xyy'."

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the comparison of agent_a and variant
- the comparison of agent_b and variant
