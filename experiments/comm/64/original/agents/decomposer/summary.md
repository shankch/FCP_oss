I split spec.md into 11 requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run ("anchored 11 requirements"), so `requirements.yaml` is written and each requirement has its line range.

**Requirements**
- **Task:** R-TASK-1 says to write a complete function (non_functional). R-TASK-2 gives the signature `vowels_count(s)` (definition). R-TASK-3 is the FIX note "Add more test cases." (non_functional).
- **Input:** R-IN-1 assumes `s` is a string representing a word.
- **Behaviour:** R-CNT-1 guarantees the function returns the number of vowels. It depends on three definitions:
  - R-VOW-1: a, e, i, o, u are vowels.
  - R-VOW-2: a 'y' at the end is a vowel.
  - R-VOW-3: a 'y' anywhere else is not.
- **Examples:** R-EX-1 is `"abcde"` → 2 and R-EX-2 is `"ACEDY"` → 3, both scenarios.
- **Frame:** R-FR-1 is the F-ZERO rule from frame.md, using the R-FR-1 id that design.yaml already gives it.

**Contradictions** (recorded as an ambiguity on both sides)
- R-VOW-1 lists only lowercase vowels, but the example R-EX-2 counts uppercase A and E.
- R-VOW-2 says lowercase 'y', but R-EX-2 counts the final uppercase Y.
- Read literally, those two definitions give 0 for `"ACEDY"`, not 3.

**Other ambiguities flagged**
- Is "Add more test cases." an instruction to whoever writes the code, or a leftover note?
- "a string representing a word": are non-word inputs (empty string, spaces, digits) a don't-care, or must the function still count them? Can the string hold more than one word?
- "the number of vowels": every occurrence, or distinct vowel letters?
- Do accented Latin-1 vowels (é, à) count? The input can contain them.
- "at the end of the given word": the last character of the whole string, the end of each word, or the last letter even when punctuation or spaces follow?
- Does the "not at the end" rule for 'y' apply to uppercase Y too?