# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 6.

## Questions
1. **depends** (R-OUT-1, R-OUT-2, R-VOW-2, R-Y-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `vowels_count("") -> raised another exception or did not finish`
2. **readings** (R-OUT-1): the two readings of this requirement disagree on these calls: which is meant?
   - `vowels_count("") -> returned something else`
3. **ambiguity** (R-OUT-2): "the number of vowels" can mean: The number of occurrences of vowels: every position holding a vowel counts, so "aa" gives 2. / The number of distinct vowels present, so "aa" gives 1.. Which is meant?
4. **ambiguity** (R-OUT-2): "returns the number of vowels in the string" can mean: Contradiction with R-EX-1 and R-EX-2: by the vowel definition "abcde" has 2 vowels (a, e) and "ACEDY" has at most 3 (A, E, final Y); the examples, which give 5 for both, are wrong and the definition governs. / Contradiction with R-EX-1 and R-EX-2: the examples are authoritative and the result is something else that gives 5 for both 5-character strings (for example the length of the string), so the definition does not govern.. Which is meant?
5. **ambiguity** (R-EX-1): ">>> vowels_count("abcde") 5" can mean: Contradiction with R-OUT-2, R-VOW-1 and R-VOW-2: under the vowel definition "abcde" contains 2 vowels (a, e), so the expected 5 is an error and the correct result is 2. / The example is authoritative: the call must return 5 (the length of the string), and the vowel definition does not govern this case.. Which is meant?
6. **ambiguity** (R-EX-2): ">>> vowels_count("ACEDY") 5" can mean: Contradiction with R-OUT-2, R-VOW-1, R-VOW-2 and R-Y-1: case-insensitively with a final 'Y' counted, "ACEDY" contains 3 vowels (A, E, Y), so the expected 5 is an error and the correct result is 3. / Contradiction with R-VOW-1 and R-Y-1 read as lowercase only: "ACEDY" then contains no vowels and the correct result is 0. / The example is authoritative: the call must return 5 (the length of the string), and the vowel definition does not govern this case.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FIX-1, "Add more test cases.": both took "An instruction to the implementer to add further test cases (for example more doctest examples in the docstring) alongside the function."
- R-OUT-2, "the number of vowels": both took "The number of occurrences of vowels: every position holding a vowel counts, so "aa" gives 2."
- R-OUT-2, "returns the number of vowels in the string": both took "Contradiction with R-EX-1 and R-EX-2: by the vowel definition "abcde" has 2 vowels (a, e) and "ACEDY" has at most 3 (A, E, final Y); the examples, which give 5 for both, are wrong and the definition governs."
- R-VOW-1, "Vowels in this case are": both took "Contradiction with R-EX-1: this definition gives vowels_count("abcde") = 2 (a, e), so the example's 5 is wrong."
- R-VOW-2, "Vowels in this case are": both took "The list is exhaustive (together with the final-'y' rule): no other character is counted."
- R-VOW-2, "'a', 'e', 'i', 'o', 'u'": both took "Only these ASCII letters (and their case variants if any) are vowels; accented Latin-1 letters such as 'à' or 'é' are not."
- R-Y-1, "at the end of the given word": both took "Only the single last character of s, if it is 'y'."
- R-Y-1, "the given word": both took "The end of the whole string s, even if s holds several words or ends in a non-letter (so in "happy." or "say hi" no 'y' counts)."
- R-Y-2, "only when it is at the end": both took "Only the last character of s can be a counted 'y'; every earlier 'y' is excluded."
- R-EX-1, ">>> vowels_count("abcde") 5": both took "Contradiction with R-OUT-2, R-VOW-1 and R-VOW-2: under the vowel definition "abcde" contains 2 vowels (a, e), so the expected 5 is an error and the correct result is 2."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1-LETTERS (R-IN-1): every call meets `letters`; `letters` is `all(k < len(s): isalpha(s[k]) || (s[k] >= 192 && s[k] != 215 && s[k] != 247) || s[k] == 170 || s[k] == 181 || s[k] == 186)`
- agent_a, RA-IN-1-NONEMPTY (R-IN-1): every call meets `len(s) >= 1`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the comparison of agent_a and agent_b
- the comparison of agent_b and variant
