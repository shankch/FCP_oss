The set lints clean and `fcp explain` reads back as I intended. Here's the summary.

## Summary: `formal/agent_b.yaml`

**What's in it:** 13 items: 9 properties and 4 scenarios. The frame rule F-ZERO is added automatically, so `explain` lists 14. All 9 decisions are recorded.

The function keeps no state between calls, so the specification model is a set of definitions of the argument rather than ghost state. They compute the final character, the character before it, whether it is a letter (`last_alpha`), whether it belongs to a word (`last_in_word`), and the expected answer (`want_true`). Every output is checked against that model:
- **R-RET-1:** every call returns True or False (`outcome == 0`).
- **R-LAST-1:** if the expected answer is True, the call returns True.
- **R-LAST-2:** three properties, one each for an empty string, a final character that is not a letter, and a final character that is part of a word.
- **R-EX-1 to R-EX-4:** each example is both a property (that input always gives that answer) and a scenario (the case can actually happen).

**Left unformalized (4):**
- **R-API-1:** the function's name and parameters are fixed by the adapter's `function` section. They aren't part of the trace, so the property language can't state them.
- **R-IN-1:** "txt is a string" is already guaranteed by how the input is encoded, so an assumption would say nothing.
- **R-WORD-1:** a definition. It is built into the `last_in_word` model definition (covered by RB-LAST1-1, RB-LAST2-3 and RB-EX2-P).
- **R-FR-1:** already stated by the frame rule F-ZERO (covered by F-ZERO).

**Readings I took:** reading 1 for every flagged phrase except "a group of characters", where I took reading 2 (a word has at least two characters). Concretely:
- Only the 52 ASCII letters count as alphabetical.
- "The last character" is the final one, even if it's a space.
- Only the space character separates words, and any run of non-space characters is a word.
- The result is True when the last space-separated group is exactly one letter, so the one-character string `"e"` gives True.
- The empty string gives False.
- The return value must be exactly the bool True or False.

**Problems in the specification:**
1. **The Note contradicts an example.** Read literally, "a group of characters separated by space" makes even a single letter a word. Then no letter could ever be "not part of a word", the result would always be False, and `"apple pi e"` ➞ True would be wrong. I kept the example and read "word" as at least two characters, and said so in the notes. The text never actually states that rule.
2. **No example covers a one-character string.** Nothing settles whether `"e"` (no space before it) gives True or False. I chose True, from reading the last group as exactly one character.
3. **"Alphabetical character" is unclear for non-ASCII letters.** Latin-1 letters such as é, ß, ª, µ and º are letters to Python's `str.isalpha()` but not to the ASCII-only reading I took. Code that uses `isalpha()` will therefore disagree with this set on strings ending in those characters, for example `"a é"`.
4. **Two smaller gaps:** the text doesn't say whether tabs or other whitespace separate words, or whether punctuation and digits can be part of a word (e.g. `"x.e"`, `"1e"`).