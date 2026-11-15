# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 4.

## Questions
1. **open** (result, outcome, R-OUT-1): the request allows `result` to be 0 or 1 (the reading leaves this free on purpose: RA-OUT-1a) and lets this call end in two ways, "returned" or "returned something else": is any answer acceptable, or which is meant?
   - `candidate("A")`
2. **open** (outcome): the request lets this call end in two ways, "returned" or "returned something else": which is meant?
   - `candidate("E")`
3. **ambiguity** (R-IN-2): "takes a string representing a word as input" can mean: candidate must return normally for every such string, including edge cases such as the empty string / the phrase only describes the parameter type; behaviour on unusual strings (for example the empty string) is unconstrained. Which is meant?
4. **ambiguity** (R-OUT-1): "Write a function candidate" can mean: candidate returns the number of vowel characters (occurrences) in s, with vowels as defined by the request / candidate returns the number of distinct vowels in s / candidate returns whether s contains a vowel (True/False or 1/0) / the return value is not specified at all, so any returned value is acceptable. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-TASK-3, "Add more test cases.": both took "a leftover maintainer note stored in the FIX constant, addressed to nobody, which places no obligation on the assistant"
- R-IN-1, "a string representing a word": both took "s is a non-empty sequence of letters only (no spaces, digits or punctuation); other strings are outside the contract"
- R-IN-1, "a word": both took "a single word: s contains no spaces"
- R-IN-2, "takes a string representing a word as input": both took "candidate must return normally for every such string, including edge cases such as the empty string"
- R-OUT-1, "Write a function candidate": both took "the return value is not specified at all, so any returned value is acceptable"
- R-VOW-1, "'a', 'e', 'i', 'o', 'u'": both took "only the lower-case letters a, e, i, o, u are vowels; 'A', 'E', 'I', 'O', 'U' are not"
- R-VOW-1, "Vowels in this case are 'a', 'e', 'i', 'o', 'u'.": both took "the list is complete except for the final-'y' rule added by the next sentence"
- R-VOW-2, "'a', 'e', 'i', 'o', 'u'": both took "upper-case 'A', 'E', 'I', 'O', 'U' are among the characters that are not vowels"
- R-VOW-3, "'y'": both took "only lower-case 'y' is a vowel at the end; a final 'Y' is not"
- R-VOW-3, "'y' is also a vowel": both took "'y' is added to the vowels listed in the previous sentence, under the end-of-word condition"
- R-VOW-4, "at the end of the given word": both took "the 'y' is the last character of the string s (s[len(s) - 1])"
- R-VOW-4, "'y'": both took "the rule concerns lower-case 'y' only; 'Y' is never a vowel"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `word`; `word` is `len(s) >= 1 && all(i < len(s): isalpha(s[i]))`
- agent_b, RB-A-WORD (R-IN-1): every call meets `word`; `word` is `len(s) >= 1 && all(i < len(s): isalpha(s[i]))`
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-OUT-1a (R-OUT-1): `result` is free when `outcome == 0`
- agent_b, RB-D-RESULT (R-OUT-1): `result` is free when `outcome == 0`
