I wrote `requirements_draft.yaml` with 12 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`; none had to be fixed.

**Requirements**
- **R-TASK-1, R-FIX-1** (non_functional): write `vowels_count(s)`, and the `FIX` note asking for "Add more test cases."
- **R-IN-1** (assumption): the input `s` is "a string representing a word".
- **R-OUT-1** (guarantee): the function returns a non-negative integer and doesn't raise an error.
- **R-OUT-2** (guarantee): the result is the number of vowels in `s`.
- **R-VOW-1, R-VOW-2** (definition): a, e, i, o, u are vowels, and no other character is (apart from a final y).
- **R-Y-1, R-Y-2** (definition): a 'y' at the end of the word is a vowel; a 'y' anywhere else is not.
- **R-EX-1, R-EX-2** (scenario): the two examples in the docstring.
- **R-FR-1** (FRAME, guarantee): rule F-ZERO, matching the `req: R-FR-1` link already in `design.yaml`.

**Contradictions** (each recorded as an ambiguity on both sides)
- **`vowels_count("abcde")` → 5:** by the vowel definition the answer is 2 (a, e). This conflicts with R-OUT-2, R-VOW-1 and R-VOW-2.
- **`vowels_count("ACEDY")` → 5:** the answer is 3 if case is ignored (A, E, final Y), or 0 if only lowercase counts. This conflicts with R-OUT-2, R-VOW-1, R-VOW-2 and R-Y-1.
- **Both examples give 5, which is the length of each string.** That means the consonants b, c, d / C, D are being counted, which breaks the closed vowel list (R-VOW-2). Each example has a reading where it is wrong and a reading where it is authoritative.

**Other ambiguities flagged**
- **Case:** whether uppercase A, E, I, O, U and a final 'Y' count. The definition lists only lowercase letters, but the uppercase example implies they count.
- **Count method:** whether repeated vowels each count ("aa" → 2) or only distinct vowels ("aa" → 1).
- **Accented letters:** whether letters like 'à' or 'é' count as vowels.
- **"A word":** whether this is just a description or a limit on valid inputs (letters only, no spaces), and whether the empty string is allowed.
- **"At the end of the given word":** whether only the last character counts, or a whole run of trailing y's ("syy"). Also unclear for strings with several words or a trailing non-letter ("say hi", "happy.").
- **The `FIX` note:** whether it's an instruction to add tests or a leftover comment.