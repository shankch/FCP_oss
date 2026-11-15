I wrote `requirements_draft.yaml` with 13 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`. I spot-checked the line numbers for the examples and the frame rule, and they point at the right lines.

**What's in it:**
- **Interface (3):** the name and parameter of `candidate(text)` (definition), "complete this function" (non_functional), and the assumption that `text` is always a `str`.
- **Return (1):** R-RET-1 says every string input returns `True` or `False`. It must not raise an exception, hang, or return some other type.
- **Definitions (2):** R-DEF-1 says what a palindrome is and R-DEF-2 says what an isogram is.
- **The check (2):** R-CHK-1 says it returns `True` when the text is an "Isogram/Palindrome". R-CHK-2 says it returns `False` when it isn't. I split these so each direction can be checked on its own.
- **Examples (4):** R-EX-1 to R-EX-4 cover `''`→True, `'aba'`→True, `'aaaaa'`→True and `'zbcd'`→False, all as scenarios.
- **Frame (1):** R-FR-1 is F-ZERO (`result` is false unless `outcome` is 0). I gave it that ID because `design.yaml` refers to it as R-FR-1.

**Ambiguities and contradictions flagged:**
- **"Isogram/Palindrome"** (on R-CHK-1 and R-CHK-2) has four readings: either one is enough, both are needed, palindrome only, or isogram only. Only "palindrome only" fits all four examples.
- **The docstring contradicts the examples.** I recorded this on both sides (the CHK requirements and the examples):
  - `'aba'` and `'aaaaa'` → True rule out "both are needed" and "isogram only", because both repeat a letter.
  - `'zbcd'` → False rules out "either one is enough", because it has no repeated letter and so is an isogram.
- **Palindrome (R-DEF-1):** the spec doesn't say whether letter case matters or whether spaces and punctuation are skipped.
- **Isogram (R-DEF-2):** the spec doesn't say whether letter case matters or whether non-letters can repeat. One more reading: an isogram can also mean every letter appears the same number of times, which would make `'aaaaa'` an isogram.
- **`text: str` (R-ENV-1):** this could only limit what callers pass, or it could be something the function has to enforce.

I didn't flag one smaller point. If case is ignored, the spec doesn't say whether that applies to non-ASCII letters like 'À'. Python's `lower()` handles them, but the adapter's character functions only cover ASCII.