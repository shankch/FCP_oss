I wrote 13 requirements to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**Requirements**
- **R-API-1** (non_functional): implement `def is_happy(s):`.
- **R-IN-1** (assumption): `s` is always a string. Flagged: any string, or only strings made of letters?
- **R-OUT-1** (guarantee): every call returns a Python bool, without raising or hanging. Flagged: exactly True/False, or any truthy/falsy value?
- **R-HAP-1/2/3** (guarantees): the definition sentence split into the obligations you can check:
  - length ≥ 3 and every 3-character window pairwise distinct → True
  - length < 3 → False
  - some window has a repeated character → False
- **R-EX-1…6** (scenarios): the six docstring examples.
- **R-FR-1** (FRAME, guarantee): F-ZERO, with the id that `design.yaml` already uses.

**Contradictions (the main finding)**
Every example says the opposite of what the definition gives. Under the plain reading, `a`, `aa`, `aabb` and `xyy` should be False, and `abcd` and `adb` should be True. I recorded each clash on both sides:
- R-HAP-2 vs R-EX-1 and R-EX-2
- R-HAP-1 vs R-EX-3 and R-EX-5
- R-HAP-3 vs R-EX-4 and R-EX-6

The contradiction readings on R-HAP-1…3 also include one where `is_happy` returns True when the string is *not* happy. That is the only reading that matches all six examples.

**Other ambiguities flagged**
- **"is happy if"**: if-and-only-if, or only a sufficient condition. Under the second reading, the short-string and repeated-letter examples stop contradicting the definition, but `abcd` and `adb` still do.
- **"letters"**: every character counts; only alphabetic characters count; or a string with a non-letter is never happy. Linked to this, **"its length"** could mean characters or letters.
- **"3 consecutive letters"**: overlapping windows, or non-overlapping blocks of 3.
- **"distinct"**: pairwise different with case mattering; pairwise different ignoring case; not all three the same; or each 3-letter group different from every other group. The last two readings would make `aabb` and `xyy` agree with the definition.
- **Example arguments**: the docstring writes `is_happy(a)` without quotes, so `a` could be the string 'a' or a variable whose value isn't given.