I split spec.md into 10 atomic requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`, and each quote is anchored to the correct source line.

**Requirements**
- **R-IF-1, R-IF-2** (`non_functional`): write the function body, keeping the given signature, name and single `str` parameter.
- **R-IN-1** (`assumption`): `brackets` contains only `(` and `)`.
- **R-RES-1** (`guarantee`): if every `(` has a corresponding `)`, the function returns `True`.
- **R-RES-2** (`guarantee`): otherwise, it returns `False`.
- **R-EX-1…4** (`scenario`): the four doctest examples, `"("`→False, `"()"`→True, `"(()())"`→True, `")(()"`→False.
- **R-FR-1** (FRAME, `guarantee`): F-ZERO. Its id matches the `req: R-FR-1` link in design.yaml.

**Ambiguities flagged**
- **Other characters (R-IN-1):** the spec says the input is only `(` and `)`, but frame.md lets any character occur. The readings are: other characters are a don't-care, they are ignored, or they must be rejected.
- **Empty string (R-IN-1):** it may or may not count as a valid input.
- **"return True if" (R-RES-2):** this could mean "if and only if" (return False otherwise) or only the one direction, leaving other inputs free.
- **"corresponding closing bracket" (R-RES-1/2):** each `(` must be closed by a later `)`, or it can pair with any `)` anywhere, so only the counts matter.
- **"every opening bracket has" (R-RES-1/2):** the whole string must be balanced, so `"())"` is False. Or only the `(` are constrained, so a spare `)` is allowed and `"())"` is True. No example settles this.
- **"return True" (R-RES-1):** the literal `True` or any truthy value.

**Contradiction recorded on both R-RES-1 and R-EX-4:** if a `(` can pair with any `)`, the string `")(()"` counts as correctly bracketed, so R-RES-1 would require True. The example says False. The example therefore supports reading "corresponding" as a later `)`.