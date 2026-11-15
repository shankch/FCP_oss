# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 5.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: vowels_count("abcde") returns 2 (the vowels a and e).

## Questions
1. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
2. **depends** (R-CNT-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `vowels_count(" ") -> 55`
3. **readings** (R-CNT-1): the two readings of this requirement disagree on these calls: which is meant?
   - `vowels_count("yBBVVByBzBzVBVBBBVyBBBBBBVzBBIVy") -> 2`
4. **ambiguity** (R-CNT-1): "the number of vowels" can mean: The number of vowel occurrences, counted with repetition (for example "aa" gives 2). / The number of distinct vowel letters that appear (for example "aa" gives 1).. Which is meant?
5. **ambiguity** (R-EX-2): "vowels_count("ACEDY")" can mean: The example is authoritative: uppercase A, E, I, O, U count as vowels and a final uppercase Y counts too, so the answer is 3. / The example contradicts the vowel definitions (R-VOW-1, R-VOW-2), which list only lowercase 'a', 'e', 'i', 'o', 'u' and 'y'. Read literally, those give 0 for "ACEDY".. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-TASK-3, "Add more test cases.": both took "An instruction to the implementer: the response must also add test cases (for example more doctests or a test function)."
- R-IN-1, "a string representing a word": both took "Callers only pass a single word (a non-empty string of letters). For other strings (empty, containing spaces, digits, punctuation or non-ASCII characters) the result is a don't-care."
- R-IN-1, "a word": both took "Exactly one word: the string contains no spaces or other separators."
- R-CNT-1, "the number of vowels": both took "The number of vowel occurrences, counted with repetition (for example "aa" gives 2)."
- R-VOW-1, "Vowels in this case are": both took "The list is exhaustive: only the ASCII letters a, e, i, o, u (and y per R-VOW-2) are vowels. Accented Latin-1 letters such as 'é' or 'à' are not."
- R-VOW-3, "at the end of the given word": both took "y is a vowel only when it is the last character of the whole string s."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `is_word`; `is_word` is `len(s) >= 1 && all(i < len(s): isalpha(s[i]))`
- agent_b, RB-IN-1 (R-IN-1): every call meets `is_word`; `is_word` is `len(s) >= 1 && all(i < len(s): isalpha(s[i]))`
- agent_b, RB-IN-1-DC-COUNT (R-IN-1): `count` is free when `!is_word`; `is_word` is `len(s) >= 1 && all(i < len(s): isalpha(s[i]))`
- agent_b, RB-IN-1-DC-OUTCOME (R-IN-1): `outcome` is free when `!is_word`; `is_word` is `len(s) >= 1 && all(i < len(s): isalpha(s[i]))`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- request points of variant, agent_b
