I wrote `requirements_draft.yaml` with 12 requirements, and `fcp anchor` accepted every quote on the first run, writing `requirements.yaml`.

**Requirements:**
- **R-IF-1** (non_functional): deliver a completed body for the `candidate(s)` stub.
- **R-IF-2** (definition): `candidate` takes one string argument, `s`.
- **R-IN-1** (assumption): the string passed in is a word.
- **R-RET-1** (guarantee): every call returns a non-negative integer and raises no exception.
- **R-RET-2** (guarantee): the returned integer is the number of vowels in `s`.
- **R-VOW-1** (definition): the vowels are a, e, i, o and u.
- **R-Y-1** (guarantee): a `y` at the end of the word counts as a vowel.
- **R-Y-2** (guarantee): a `y` anywhere else does not count.
- **R-EX-1** and **R-EX-2** (scenarios): `candidate("abcde")` returns 2, and `candidate("ACEDY")` returns 3.
- **R-FIX-1** (non_functional): the `FIX` note, "Add more test cases."
- **R-FR-1** (FRAME, guarantee): the F-ZERO rule, `result` is 0 unless `outcome` is 0.

**Contradictions** (each recorded as an ambiguity on both sides):
1. **"Number of characters or vowels" vs both examples:** if it means the length of the string, both examples should return 5, not 2 and 3. That reading would also make the vowel definition pointless. Recorded on R-RET-2, R-EX-1 and R-EX-2.
2. **Lowercase vowel list vs "ACEDY" → 3:** the list gives only lowercase letters, but the example counts uppercase `A` and `E`. Recorded on R-VOW-1 and R-EX-2.
3. **Lowercase `'y'` vs the final `Y` in "ACEDY":** the rule names lowercase `y`, but the example counts a final uppercase `Y`. Recorded on R-Y-1 and R-EX-2.

**Other ambiguities flagged:**
- **What counts as "a word":** it could mean letters only, with or without the empty string, or any string at all. It also could mean one word or several.
- **Counting:** it is unclear whether every occurrence of a vowel counts or only distinct vowels. The examples don't decide this, because neither repeats a vowel.
- **Accented letters:** it is unclear whether Latin-1 letters such as `é` count as vowels.
- **"At the end of the word":** it could mean the last character only, every `y` in a trailing run (as in `"ayy"`), the end of each word, or the last letter ignoring trailing punctuation.
- **"Add more test cases.":** it could be an instruction to add tests, or a leftover note that places no obligation on the code.

The example scenarios are the only source of case-insensitive counting, so there is no separate requirement for it. It is covered by the ambiguity readings above.