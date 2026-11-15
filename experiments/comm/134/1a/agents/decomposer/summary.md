I've written `requirements_draft.yaml` with 11 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**Requirements:**
- **Interface:** `R-IF-1` asks for the function to be completed (non_functional). `R-IF-2` is the signature `def candidate(txt):` (non_functional). `R-IF-3` is the assumption that `txt` is a string.
- **Definition:** `R-DEF-1` defines a word as a group of characters separated by space.
- **Guarantees:** `R-RET-1` says it returns True when the character at the given position is alphabetical and not part of a word. `R-RET-2` says it returns False otherwise, including when there is no such character.
- **Scenarios:** `R-EX-1` to `R-EX-4`, one for each of the four examples.
- **Frame:** `R-FR-1` (FRAME) is F-ZERO, `result` is false unless `outcome` is 0. This is the ID that `design.yaml` already points to.

**Ambiguities flagged:**
- **"the character with given position"** (`R-RET-1` and `R-RET-2`): the readings are the last character, the first character, the last non-space character, or a position passed in by the caller. Only "last character" fits all four examples. The first-character reading contradicts `apple pi e ➞ True`, and the last-non-space reading contradicts `apple pi e  ➞ False`.
- **"alphabetical character"**: either ASCII letters only, or anything Python's `str.isalpha()` accepts. The inputs allow Latin-1 codes, where letters like é, ß, ª and µ count under the second reading.
- **"is not a part of a word"**: either the character stands alone, or it is preceded by a space (so a one-letter `txt` like `"e"` fails), or the literal reading, under which no non-space character can ever qualify.
- **"separated by space"** (`R-DEF-1`): either only the space character, or any whitespace.
- **"a group of characters"** (`R-DEF-1`): either any run of non-space characters, or runs of letters only.

**Contradictions, each recorded on both sides:**
1. **"Given position" vs. the signature** (`R-RET-1` and `R-RET-2` vs. `R-IF-2`): the text talks about a given position, but the function only takes `txt`, so nothing supplies one.
2. **The word definition vs. an example** (`R-DEF-1` and `R-RET-1` vs. `R-EX-2`): by the definition, the lone `e` in `"apple pi e"` is itself a one-character word. That would make the answer False, but the example says True.