I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and I read the `fcp explain` output back: each item says what I meant. I couldn't run any deeper analysis because `fcp check` isn't available to an agent, so the hand-worked examples below are the only check on the values beyond lint.

**Items: 14** (8 properties, 6 scenarios), no assumptions, no don't-cares, no ghost state.
- **The main property (RV-CNT-1):** every call must return a value, and that value is the number of distinct vowel letters in `s`. It is built from short named expressions: one per letter a, e, i, o, u, plus one for "a y ends a word".
- **R-IN-1:** every string must be accepted, and the empty string gives 0.
- **R-VOW-1/2/3:** one property each, isolating that requirement's effect on the count.
- **The two docstring examples:** each is both a property and a scenario.
- **Scenarios for your readings:** `"aa"`→1, `"café"`→2, `"say no"`→3, and a call on a string containing spaces.
- **Hand checks:** `"abcde"`→2, `"ACEDY"`→3, `"say no"`→3, `"café"`→2, `"aa"`→1, `""`→0, all consistent with the set.

I used your readings for all six phrases you listed, and every affected item's note says so. For the phrases you didn't list, I took case-insensitive matching for a/e/i/o/u and for y, and treated the `"ACEDY"` example as authoritative. All 10 flagged phrases are recorded under `decisions`.

**Unformalized (4), with reasons:**
- **R-TASK-1** ("complete implementation"): this is about the code, not about any one call. Its observable part is covered by RV-IN-1a and RV-CNT-1, since a stub would break them.
- **R-TASK-2** (name and signature): this is fixed by the adapter in `design.yaml` and can't be written in FCP-PL. It is covered by RV-IN-1a, because a wrongly named function makes every call fail.
- **R-TASK-3:** under your reading it is a leftover note that places no obligation.
- **R-FR-1:** the frame rule F-ZERO already covers it.

**Choices I made beyond your readings** (these could cause disagreements in review):
- **What a "word" is:** a run of characters without ASCII whitespace. The y must be its last character, so `"day!"` doesn't count; that case belongs to reading 3.
- **Which accented forms count:** the Latin-1 letters that decompose to a vowel plus an accent mark. That leaves out Æ, Ø and accented y (Ý, ý, ÿ).
- **What "distinct" means:** case and accent are ignored, so `a`, `A` and `à` are one letter. The result is therefore at most 6.

**Problems in the specification:**
1. **Case conflict:** the vowel list gives only lowercase letters, but `vowels_count("ACEDY") == 3` needs uppercase A, E and Y to count. Read literally, the definition gives 0.
2. **"Word" vs "string":** "a word" and "the end of the given word" aren't defined for strings with spaces, punctuation or nothing in them, while the result is described as "the number of vowels in the string".
3. **The examples don't decide the counting rule:** no vowel appears twice in either example, so they can't tell distinct counting from counting every occurrence.
4. **Non-ASCII characters:** nothing says what happens to accented letters, even though the input allows codes up to 255.
5. **The FIX constant:** "Add more test cases." sits in the prompt and nothing says who it is addressed to.