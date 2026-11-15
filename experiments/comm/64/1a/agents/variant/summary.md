I wrote `formal/variant.yaml`. `fcp lint` reports clean, and the `fcp explain` output matches what I meant for every item. I couldn't run the consistency analysis because `fcp check` is blocked for agents, so the conflicts below come from reading the formulas, not from a tool run.

**Items: 11 formal items, plus 13 entries under `decisions`** (one per flagged phrase)
- **1 assumption:** every character of `s` is a letter; the empty string is allowed.
- **7 properties:**
  - the empty string gives 0;
  - every call returns an integer (`outcome == 0`);
  - the count rule for R-RET-2;
  - one restricted property each for R-Y-1 and R-Y-2, covering only the inputs where that rule changes the result;
  - one property for each doctest example.
- **3 scenarios:** the empty string, `"abcde"` → 2, and `"ACEDY"` → 3.

**Left unformalized (5)**
- **R-IF-1:** it asks for the code to be written, which can't be seen in any call.
- **R-IF-2:** the single string argument is already fixed by `design.yaml`.
- **R-FIX-1:** under the reading you gave, it's a leftover note that places no obligation on the code.
- **R-VOW-1:** it's a definition; the vowel list is built into the formulas of RV-RET-2, RV-Y-1 and RV-Y-2 (`covered_by`).
- **R-FR-1:** it's the existing frame rule F-ZERO (`covered_by`).

**Choices I made myself**
- **"the number of characters or vowels"** (not in your list): I took reading 3. Read literally, "or" lets each call return either `len(s)` or the vowel count, so the result isn't fully determined. I picked it because it keeps every vowel and 'y' rule meaningful, and it makes your readings of the two examples matter: they rule out the character count.
- **"letters"**: I took this as all letters in the 256-character set of `frame.md` (the same characters Python's `str.isalpha()` accepts), not just a–z and A–Z. With only a–z and A–Z, your "accented vowels count" reading could never apply.
- **Doctest examples**: each one is both a property (the result is required) and a scenario.

**Problems in the specification**
1. **R-EX-2 contradicts the readings you gave.** With lowercase-only vowels and lowercase-only 'y', `"ACEDY"` gives 5 or 0, but the example requires 3. `"ACEDY"` is all letters, so it's an allowed call. RV-RET-2, RV-Y-2 and RV-EX-2-P therefore can't all hold, and the RV-EX-2-S scenario can never happen. I recorded this and did not repair it.
2. **The two R-IN-1 readings clash.** "Only letters" rules out spaces, so a string can never hold several words, and the several-words reading never applies to an allowed call. The 'y' formula still treats any space-separated word as having its own end.
3. **Counting distinct vowels hides the 'y' readings.** If any 'y' at the end of a word counts, 'y' adds exactly one, so "every 'y' in the trailing run" (R-Y-1 and R-Y-2) gives the same result as "only the last 'y'".

Every item affected by one of your readings says so in its note.