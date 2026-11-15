I've written `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I intended for each item. I also checked the formulas by hand on the four examples and on `"e"` and `"   "`.

**Items:** 8 properties of my own (RV-RET-1, RV-LAST-1, RV-LAST-2, RV-WORD-1, RV-EX-1 to RV-EX-4), plus the frame rule F-ZERO from `design.yaml`. There are also 8 helper definitions and 9 entries under `decisions`. I used no ghost state and no assumptions. Every item using a reading you specified says so in its note.

**Left unformalized (3):**
- **R-API-1:** the function's name and argument are a coding requirement. The function section of `design.yaml` already fixes them, and there is no signal to check.
- **R-IN-1:** `txt` is always a string by construction of the interface, so an assumption would just be "true".
- **R-FR-1:** this is frame rule F-ZERO, which is already part of every set. It is listed with `covered_by: [F-ZERO]`.

**How the readings are encoded:**
- **"returns True" (truthy counts):** every call must return something (no exception, no hang). The adapter records a returned value as bool or as "anything else", and in the second case it doesn't record whether the value was truthy. So I accept a non-bool return as either True or False. That means a returned 1 passes, but so does a returned 0.
- **"alphabetical":** the built-in `isalpha` here is ASCII-only, so I spelled out the Latin-1 letters: codes 170, 181, 186 and 192–255 except 215 (×) and 247 (÷). Python wasn't available to check this list, so it comes from the Unicode letter categories.

**Problems in the specification:**
1. **The examples contradict the Note.** "apple pi e ➞ True" only works if a lone letter is not a word, but the Note says a word is any group of characters. With your readings, RV-EX-2 requires False for "apple pi e", the opposite of what the example says.
2. **These readings contradict each other.** For R-LAST-1, "not part of a word" means the previous character is a space, so RV-LAST-1 gives True for "apple pi e" and "apple pi e ". The R-WORD-1 readings make every letter part of a word, so RV-WORD-1 gives False whenever the last non-space character is a letter. RV-EX-2 and RV-EX-3 also require False on those inputs. A function returning True or False cannot satisfy all of them.
3. **The contradiction partly hides itself.** Because a non-bool return is accepted as either answer, a function that returns a non-bool on those inputs satisfies everything. A consistency check may therefore report "only a non-bool return is allowed" instead of flagging the conflict directly.
4. **The empty string is pinned only by its example.** "Otherwise" covers only non-empty strings under your reading, so RV-EX-4 is the only item that requires `""` to give False.
5. **"Space" means code 32 for R-LAST-1** (both "ignoring trailing spaces" and "the character before is a space"). The R-WORD-1 "any whitespace" reading doesn't change the result: once a single letter counts as a word, the whitespace and letters-only readings make no difference.
6. **Wrong-type returns are now allowed.** The requirement text for R-RET-1 forbids returning a value of another type, but the truthy reading permits it. The note on RV-RET-1 records this.