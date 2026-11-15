I wrote `formal/agent_a.yaml`. `fcp lint` reports no errors, and the `fcp explain` read-back matches what I meant for every item. I checked the four examples against the properties by hand; I did not run `fcp check`.

**Items: 6 formal items with the `RA-` prefix.**
- **`RA-RET-1` and `RA-RET-2`:** two rules that cover every input. If the last character of `txt` is an ASCII letter and stands alone (`txt` has length 1, or the character before it is a space), the function returns `True`. In every other case it returns `False`. Both rules also require that a bool is returned (`outcome == 0`). They are built from four named expressions; no extra state is needed.
- **`RA-EX-1` to `RA-EX-4`:** one scenario for each example in the prompt (`"apple pie"`, `"apple pi e"`, `"apple pi e "`, `""`), checking that the stated answer is possible.
- **Decisions:** I recorded a reading for all 11 phrases flagged as ambiguous.

**Requirements left unformalized: 5**
- **R-IF-1** (complete the function): not a behaviour in itself. Its observable part, that every call returns a bool, is covered by `RA-RET-1` and `RA-RET-2`.
- **R-IF-2** (the signature): already fixed by the interface in `design.yaml`, which has no position input.
- **R-IF-3** (`txt` is a string): true by construction, since the input signal can only hold a string. There is nothing left to assume.
- **R-DEF-1** (definition of "word"): has no behaviour of its own. It is used inside `RA-RET-1` and `RA-RET-2`, which cover it.
- **R-FR-1**: this is the adapter's frame rule F-ZERO, which is already part of every set, so it is covered by F-ZERO.

**Problems in the specification**
1. **"Given position" contradicts the signature.** The docstring talks about "the character with given position", but `candidate(txt)` takes no position argument. I read it as the last character, the only reading that fits all four examples.
2. **The definition of "word" contradicts an example.** Read literally, a lone letter between spaces is still "a group of characters", so it would be a word. Then the "not part of a word" condition could never hold, and `candidate("apple pi e") ➞ True` would be wrong. I took "characters" (plural) to mean a word has at least two characters, which agrees with the example. Each affected item's note says so.
3. **"Alphabetical character" is unclear.** I read it as ASCII letters A–Z and a–z. Python's `str.isalpha()` also accepts Latin-1 letters such as `é`, so an implementation that uses it will return `True` where this set requires `False`, for example on `"pi é"`. Expect this split between implementations.
4. **Other whitespace is unspecified.** "Separated by space" doesn't say whether tabs or other whitespace separate words. I took the space character only, so `"pi\te"` returns `False`.