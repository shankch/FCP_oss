I wrote `requirements_draft.yaml` with 15 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**The requirements:**
- **Function setup (R-API-1, R-API-2):** non-functional. Complete the stub, keeping the `is_happy(s)` signature.
- **Input (R-IN-1):** an assumption that `s` is a string.
- **Output (R-OUT-1, R-OUT-2):** two guarantees. The return value says whether `s` is happy, and every call returns a bool rather than raising or returning another type.
- **Happiness rule (R-HAP-1 to R-HAP-3):** the definition sentence is split into three guarantees:
  - a string shorter than 3 characters is not happy;
  - a string whose substrings of letters are not distinct is not happy;
  - a string of at least 3 characters whose substrings are distinct is happy.
- **Examples (R-EX-1 to R-EX-6):** one scenario for each example in the docstring.
- **Frame rule (R-FR-1):** F-ZERO from frame.md (`happy` is false unless `outcome` is 0). It uses the id that design.yaml expects.

**Ambiguities flagged:**
- **"roughly substrings of letters are distinct"** is the main problem. I listed four readings for the condition itself:
  - every 3 consecutive characters are all different;
  - adjacent characters differ;
  - no character repeats anywhere;
  - substrings of a fixed length differ from one another.

  "roughly" is flagged separately: it could be a filler word, mean "approximately", or leave the rule to be worked out from the examples.
- **"letters":** does every character count, are non-letters skipped, or is the input assumed to be letters only? Separately, is the check case-sensitive?
- **"happy if":** "if and only if" or only a sufficient condition. This decides whether the "not happy" requirements (R-HAP-1, R-HAP-2) follow from the sentence at all, or only from the examples.
- **Smaller ones:**
  - "check … or not" could mean a strict bool or any truthy/falsy value, and the function may or may not have to answer non-letter strings;
  - "its length" could count characters or letters;
  - the examples leave out the quotes around their arguments.

**Contradiction recorded:** if "roughly" tolerates a few repeats, or if the substrings only need to differ from one another, then `aabb` and `xyy` would be happy. That clashes with the examples `is_happy(aabb) => False` and `is_happy(xyy) => False`. I recorded it as an ambiguity on both sides: R-HAP-2 and R-HAP-3, plus R-EX-4 and R-EX-6. Each gives two readings: the example wins, or the definition wins.

All six examples fit the first three readings of the condition, so they don't decide between them.