I've written `formal/variant.yaml`. `fcp lint` reports clean, and the `fcp explain` output says what each item is meant to say. I also wanted to test the two helper formulas (`lone`, `in_word`) on the example strings with a short Python script, but that command needed approval and didn't run. I checked those cases by hand instead.

**14 items:** 9 properties and 5 scenarios, with no assumptions or ghost state. All 12 flagged phrases have a `decisions` entry, using the readings you specified. Each affected item's `note` says which reading it uses.

- **R-RET-1:** the call must finish without an exception. It may return a bool or any other value (outcome 0 or 2).
- **R-RET-2:** the last non-space character is an ASCII letter, and either nothing or a space comes before it. If so, the result must be truthy (`result || outcome == 2`). Your reading says "txt has length 1", but that was written for the final character. Once trailing spaces are ignored, I took it to mean "no character before the letter", so `"e "` returns True.
- **R-RET-3:** a non-empty string without that property returns False. The empty string is left to R-EX-4.
- **R-DEF-1:** a final letter that is part of a word (a run of 2 or more letters) returns False.
- **R-EX-1 to R-EX-4:** each is a property (the stated result is required) plus a scenario (returning that bool must be possible).
- **R-IN-1:** a scenario saying the empty string is a possible call. The interface already makes `txt` a string, so no assumption is needed.

**Left unformalized (3):**
- **R-FR-1:** marked as covered by frame rule F-ZERO, which is already part of every set.
- **R-NF-1:** it describes the deliverable, not the behaviour of a call.
- **R-IF-1:** the function name and signature are fixed in `design.yaml`, and a trace can't express them.

**Problems in the specification:**
1. **The property is missing.** "is ," leaves out what the last character should be, and the literal reading (a comma) contradicts R-EX-2.
2. **R-RET-2 contradicts R-EX-3.** Under your "last non-space character" reading, `"apple pi e "` has to be truthy, but R-EX-3 says False. I formalized both literally and did not repair it.
3. **The interface hides that contradiction.** It doesn't record whether a non-bool return is truthy or falsy. So the "any truthy/falsy value" reading has to accept outcome 2 for both True and False. That means a non-bool return satisfies both properties on `"apple pi e "`. Scenario RV-EX-3-S (returning the bool False there) should be unreachable, which is what exposes the contradiction. More generally, the set can't tell a correct non-bool answer from a wrong one.
4. **Two definitions of "standing alone" disagree.** Under your word readings (a run of letters, with any non-letter as a separator), the final letters of `"apple,e"` and `"\te"` are not part of a word. Your R-RET-2 reading needs a space before the letter, so it gives False. I only formalized the direction of R-DEF-1 that doesn't conflict: "part of a word → False".
5. **All-space strings are an unclear case.** Under the last-non-space reading, `"   "` has no last character. I followed the reading's wording ("non-empty strings") and required False, and flagged it in the note.
6. **The R-EX-1 reading doesn't apply here.** Its contradiction only arises if the property is "any letter". With the "letter standing alone" property used here, `"apple pie"` → False is consistent.