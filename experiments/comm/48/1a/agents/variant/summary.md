I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I meant for every item. I also checked by hand that the two definitions give the results the readings promise ('Aba' is a palindrome and an isogram; 'ab a' is not a palindrome; 'a b ' is not an isogram). I have not run any of the other analyses, so the conflict described below comes from reading the items, not from a tool.

**The set: 11 items** (7 properties, 4 scenarios), plus two definitions:
- `pal`: case is ignored and every character counts (R-DEF-1, reading 2).
- `iso`: no character of any kind appears twice, compared exactly (R-DEF-2, reading 1).
- **RV-RET-1**: every call returns a bool (`outcome == 0`).
- **RV-CHK-1 / RV-CHK-2**: if text is both an isogram and a palindrome, the call returns True; otherwise it returns False. A raised exception does not count as False.
- **RV-EX-1..4**, each with a scenario (`-C`): '' returns True, 'aba' returns False, 'aaaaa' returns False, 'zbcd' returns True. These are the readings you gave; the last three reverse the docstring examples.
- All 8 `decisions` are recorded. Every item affected by a given reading says in its note (or reason) that the reading was imposed.

**Left unformalized (6), each with a reason:**
- **R-IF-1, R-IF-2**: these are about the function's name, signature and being a complete deliverable, not about what a call does. The part you can observe is covered by RV-RET-1.
- **R-ENV-1**: under the given reading, the function itself must handle non-str arguments, so there is no assumption on the caller. But the setup only ever passes strings, so that duty can't be stated. "Handle or reject" would also allow any outcome anyway.
- **R-DEF-1, R-DEF-2**: these are definitions, built into `pal` and `iso` and used by RV-CHK-1/2.
- **R-FR-1**: already covered by the built-in frame rule F-ZERO, which frame.md says need not be restated.

**Problems found:**
1. **The given readings contradict each other.** Under the "both are needed" reading, RV-CHK-2 makes 'zbcd' return False, because it isn't a palindrome under any reading. Under the reading you gave for R-EX-4, RV-EX-4 makes it return True. So RV-EX-4 and RV-CHK-2 can't both hold, and the scenario RV-EX-4-C can never happen. I kept both as given rather than repair it.
2. **The spec contradicts itself.** "Isogram/Palindrome" can't be squared with the examples under most readings. Treating it as palindrome-only is the only reading that matches all four examples.
3. **R-DEF-2 is broader than its text.** The requirement says no *letter* repeats; the given reading bans repeats of *any* character.
4. **The given readings combine in an odd way.** Case is ignored when checking for a palindrome but counts when checking for repeats. So the call returns True only for '', single characters, and strings whose mirrored characters are the same letter in opposite case ('Aba', 'aBbA'). Any non-letter can only be the middle character.
5. **Case folding only covers ASCII letters.** The setup's `lower()` changes only those, while Python's `str.lower()` also changes accented letters above code 127. The test alphabet is ASCII, so this doesn't matter in practice yet.