I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` rendering of each item matches what I meant.

**Items: 12 formal items** (plus the adapter's frame rule F-ZERO)
- **8 properties:**
  - RV-RET-1: returns True if the character exists, is alphabetical and is not part of a word.
  - RV-RET-2a/b/c: returns False if there is no character, if it is not alphabetical, or if it is part of a word.
  - RV-EX-1…4: one for each docstring example.
- **4 scenarios** (RV-EX-1s…4s): each example call must be able to return False.
- **11 decisions**, all using the readings you assigned. Each affected item's note says the reading was imposed.

I used named helper expressions (`defs`) but no ghost state. "Alphabetical" means Python's `str.isalpha()` over Latin-1: A–Z, a–z, 170, 181, 186, 192–214, 216–246 and 248–255. "Space" means Python's `str.isspace()`: codes 9–13, 28–31, 32, 133 and 160. I took these code tables from memory because Python wasn't approved to run here, so I couldn't double-check them.

**Left unformalized (5), each with a reason**
- **R-IF-1** (deliver a complete function): a non-functional requirement. Its observable part, that every call returns a bool, is covered by the RET items, whose triggers together cover every input.
- **R-IF-2** (the signature): FCP-PL can't state a signature, and the adapter fixes it anyway. Under the imposed reading the position is unspecified. The functional items fix it only through the R-RET reading (`txt[0]`).
- **R-IF-3** (txt is a string): always true, because the adapter only passes strings.
- **R-DEF-1** (definition of a word): built into the helper expressions and covered by RV-RET-1 and RV-RET-2c.
- **R-FR-1**: covered by the adapter's frame rule F-ZERO.

**Problems in the specification under these readings**
- **The function can never return True.** The checked character is `txt[0]`, and "not part of a word" means "preceded by a space". Nothing comes before the first character, so it never qualifies. RV-RET-1 can never trigger, and RV-RET-2c applies to every non-empty string. The word-definition readings point the same way: words are runs of letters and a single letter counts as a word, so every letter is part of a word.
- **The example `candidate("apple pi e") ➞ True` contradicts the readings.** It conflicts with the position reading (`txt[0]` is 'a', part of "apple"), the single-letter-word reading and the R-EX-2 reading. As that reading directs, RV-EX-2 requires False and its note says the stated True is not honoured.
- **The signature and docstring conflict.** Under the R-IF-2 reading the position is unspecified, yet the R-RET reading fixes it at `txt[0]`. The text gives no basis for that choice.
- **Two choices of my own:** in RV-RET-2c, "part of a word" is just the negation of "preceded by a space". I also counted any whitespace as the space, which makes no difference at position 0.