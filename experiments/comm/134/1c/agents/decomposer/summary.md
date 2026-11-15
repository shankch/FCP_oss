I wrote `requirements_draft.yaml`, and `fcp anchor` accepted all 11 quotes on the first run, writing them to `requirements.yaml`. No quotes needed fixing. I checked the line numbers it assigned: each example landed on its own line, even though three of them look nearly identical once spaces are ignored.

**Requirements**
- **R-IF-1** (non_functional): the function's name and its single argument `txt`.
- **R-IN-1** (assumption): `txt` is a string.
- **R-DEF-1** (definition): a "word" is a group of characters separated by space.
- **R-RES-1** (guarantee): returns True when the last character is a letter and not part of a word.
- **R-RES-2** (guarantee): returns False otherwise.
- **R-RES-3** (guarantee): every string, including the empty one, gets True or False back, with no exception and no other type.
- **R-EX-1 to R-EX-4** (scenario): the four examples.
- **R-FR-1** (FRAME, from F-ZERO): `result` is false unless `outcome` is 0.

**Ambiguities flagged**
- **"group of characters":** a single character on its own may or may not count as a word. If it does, a letter is always part of a word, so the True case can never happen.
- **"separated by space":** this may mean only the space character, or any whitespace.
- **What a word contains:** any non-space characters, or only letters. For example, in `"ab 1e"` the final e may or may not be part of a word.
- **"the last character":** literally `txt[-1]`, or the last character that isn't a space.
- **"alphabetical character":** ASCII letters only, or Python's `str.isalpha`, which also accepts accented Latin-1 letters such as é.

**Contradictions** (each recorded as an ambiguity on both requirements involved)
The rule and the examples disagree throughout:
- `"apple pie" ➞ True`: the e is part of the word "pie", so R-RES-2 says False.
- `"apple pi e" ➞ False`: the e stands alone, so R-RES-1 says True.
- `"apple pi e " ➞ True`: the last character is a space, so R-RES-2 says False. If "last character" skips trailing spaces instead, this example and the previous one should give the same answer, but they don't.
- `"" ➞ True`: there is no last character, so R-RES-2 says False.

All four examples fit the exact opposite of the stated rule: True unless the string ends in a letter standing alone. I added that as an extra reading on R-RES-1 and R-RES-2. Someone needs to decide whether the rule or the examples are correct before the formal properties are written.