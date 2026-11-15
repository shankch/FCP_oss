I wrote 15 requirements to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**Breakdown:**
- **Interface (R-IF-1, R-IF-2):** fill in the body of the given function, which is named `is_happy` and takes one parameter `s`.
- **Input (R-IN-1, assumption):** `s` is a Python string.
- **Result (R-RET-1, guarantee):** every call returns `True` or `False`, without raising an error or hanging.
- **Rule:** R-HAP-1 defines "happy". Three guarantees follow from it:
  - R-HAP-2: a string shorter than 3 gives `False`.
  - R-HAP-3: a run of 3 characters with a repeat in it gives `False`.
  - R-HAP-4: otherwise, a string of length 3 or more gives `True`.
- **Examples (R-EX-1…6):** one scenario per example.
- **Frame (R-FR-1):** F-ZERO, so `happy` is false whenever `outcome` is not 0.

**Ambiguities flagged:**
- **"if"**: either "if and only if" or only a sufficient condition. Under the second reading, the rule doesn't say that failing strings give `False`.
- **"every 3 consecutive"**: overlapping windows, or separate blocks of three. Under blocks, `abccde` would be happy.
- **"letters"**: any character counts; or only letters, with other characters skipped; or a non-letter makes the window fail.
- **"distinct"**:
  - all three different;
  - only neighbours differ, so `aba` would be happy;
  - not all three the same;
  - no 3-character window appears twice.
- **Case**: whether `a` and `A` count as the same letter.
- **"a string"**: any string, or only lower-case letters as in the examples.
- **"check"**: return exactly `True`/`False`, or any truthy/falsy value.

**Contradictions:** the examples `aabb => False` and `xyy => False` conflict with the rule under the "not all three the same" and "no window repeats" readings of "distinct". I recorded this on both sides: the rule requirements (R-HAP-1, R-HAP-3, R-HAP-4) and the two example scenarios (R-EX-4, R-EX-6).

**Not settled by any example:** "only neighbours differ" (`aba` happy), the separate-blocks reading, how non-letters are handled, and case sensitivity. All six examples fit these readings, so different implementations can disagree on them.