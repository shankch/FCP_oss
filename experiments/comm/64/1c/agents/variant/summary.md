I've written `formal/variant.yaml`. `fcp lint` reports clean, and I read back the `fcp explain` output: every item says what I meant it to.

**Items: 11 in total**, 9 properties and 2 scenarios, plus 5 helper definitions. The `decisions` list covers all 15 flagged phrases. Every item affected by one of your given readings says in its note that the reading was taken as instructed.

- **R-OUT-1:** every call returns normally with an integer (`outcome == 0`).
- **R-OUT-2:** your two readings for it conflict. The length gives 2 for "aa", but the distinct-vowels reading requires 1. So I didn't make the length the result. Instead R-OUT-2 has two bounds:
  - **Lower bound:** each distinct vowel the definition names counts once (a, e, i, o, u, their accented forms, and a 'y' that ends a word).
  - **Upper bound:** the result is at most the number of distinct characters in `s`.
- **The definition requirements** each add one bound:
  - **R-VOW-1:** each of a, e, i, o, u present counts.
  - **R-VOW-2:** accented forms count too. The list isn't exhaustive, so this requirement puts no upper limit on the result.
  - **R-Y-1:** a 'y' at the end of any word counts (so "happy." and "say hi" qualify).
  - **R-Y-2:** any other 'y' adds nothing.
- **R-EX-1 and R-EX-2:** each is a property that the call returns 5, plus a scenario that the call is possible. Both apply to those two strings only and aren't generalised to other strings.

For the phrases you didn't assign, I took the most literal reading:
- Only lowercase vowels and lowercase 'y' count.
- R-IN-1 just describes the input, so there is no assumption limiting it; every string, including the empty one, is a valid input.
- R-EX-2 takes reading 3: the example is authoritative.

**Left unformalized (4):**
- **R-TASK-1:** the function name and its single parameter are fixed by `design.yaml`; they aren't something a trace can show.
- **R-FIX-1:** your reading makes it a leftover note with no obligation.
- **R-IN-1:** no assumption is needed. It's covered by RV-OUT-1 and RV-OUT-2-HI.
- **R-FR-1:** this is the adapter's built-in frame rule, covered by F-ZERO.

**Problems in the specification:**
- **The examples contradict the definition.** "abcde" has 2 vowels, not 5. "ACEDY" has 3, or 0 if only lowercase counts.
- **The readings you gave don't fully agree** (length vs. distinct vowels, and "the definition does not govern" vs. the y and accent rules). So this set leaves the result open on most inputs; "bcd", for example, may return 0 to 3. FCP's check for undetermined outputs will report this. I didn't hide it with don't-cares, because the gap comes from the contradiction, not from deliberate freedom in the spec.
- **The trailing-run reading of R-Y-1 changes nothing here.** When distinct vowels are counted, a run of 'y's adds at most one.
- **The case of the vowels is never stated.** The spec doesn't say whether uppercase letters are vowels, and it says "word" where the argument is any string.
- **I had to choose some boundaries the spec never defines:**
  - **Letters:** a word ends where the next character isn't a letter. I counted as letters whatever Python's `str.isalpha` accepts among Latin-1 codes.
  - **Accented forms:** I left out ø and æ as separate letters rather than accented vowels.