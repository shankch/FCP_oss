I wrote `requirements_draft.yaml` and ran `fcp anchor`. All 12 quotes matched verbatim on the first run, so `requirements.yaml` has been written.

**Requirements (12)**
- **R-FR-1** (FRAME, guarantee): F-ZERO, which says `result` is false unless `outcome` is 0.
- **R-NF-1** (non_functional): fill in the given Python function, keeping its signature.
- **R-IF-1** (definition): the function is `candidate`, with one parameter, `txt`.
- **R-IN-1** (assumption): `txt` is a string, and it may be empty.
- **R-RET-1** (guarantee): for every string, the function returns a bool and never raises.
- **R-RET-2** (guarantee): it returns True if the last character has the property the request describes.
- **R-RET-3** (guarantee): it returns False otherwise.
- **R-DEF-1** (definition): the note defining "word".
- **R-EX-1…4** (scenario): the four examples.

**The main problem:** the key sentence is broken. It reads "returns True if the last character … is , and False otherwise", so the actual condition is missing. I listed seven readings on R-RET-2:
- **Literal:** the last character is a comma.
- **Lone letter:** an ASCII letter with nothing or a space before it.
- **Lone letter, space required:** same, but a space must come before it, so a one-character string doesn't count.
- **Lone letter, Python's definition:** same as the lone-letter reading, but "letter" means whatever Python's `str.isalpha` accepts, so letters like é count.
- **Letter after a non-letter:** a letter whose previous character is not a letter.
- **Any letter.**
- **Not part of a word, using the note's definition:** this can never be true.

The lone-letter reading is the only one that fits every example.

**Contradictions, each recorded on both requirements involved**
- If the condition is read literally as "is a comma", R-RET-2 and R-RET-3 contradict R-EX-2, which expects `"apple pi e"` to return True.
- If the condition is "any letter", R-RET-2 contradicts R-EX-1, which expects `"apple pie"` to return False.
- The note says a word is a group of characters, so a single letter like "e" counts as a word. That makes "not part of a word" conflict with R-EX-2.
- If "last character" means the last non-space character, R-RET-2 contradicts R-EX-3, which expects `"apple pi e "` to return False.

**Other ambiguities flagged**
- Does "returns True/False" require an actual bool, or would 1/0 or other truthy and falsy values do?
- Does "otherwise" cover the empty string, which has no last character?
- In R-DEF-1:
  - Does "space" mean only the space character, or any whitespace?
  - Can a "group of characters" be a single character?
  - Do punctuation and digits separate words?
  - The term "word" is never used anywhere else in the request, so the note may have no effect.