I wrote `requirements_draft.yaml`, and `fcp anchor` accepted all 11 quotes on the first run (each example and its expected result span two source lines) and wrote `requirements.yaml`.

**Requirements**
- **R-IF-1** (non_functional): fill in the body of the given function, keeping its name and signature.
- **R-IF-2** (definition): the function is `is_palindrome(text)`, taking one `str` argument.
- **R-DEF-1** (definition): a palindrome is a string that equals its reverse.
- **R-FN-1** (guarantee): returns True if `text` is a palindrome.
- **R-FN-2** (guarantee): returns False if `text` is not a palindrome.
- **R-FN-3** (guarantee): always finishes and returns a bool, never raises an exception.
- **R-EX-1…4** (scenario): the four docstring examples: `''` → False, `'aba'` → False, `'aaaaa'` → False, `'zbcd'` → True.
- **R-FR-1** (FRAME, guarantee): F-ZERO, `result` is false unless `outcome` is 0. It uses the ID that `design.yaml` already refers to.

**Contradiction**
The docstring says the function checks whether the string is a palindrome, and the name `is_palindrome` says the same. All four examples give the opposite answer. I recorded this on both sides of each pair:
- R-FN-1 against R-EX-1, R-EX-2 and R-EX-3, where palindromes return False.
- R-FN-2 against R-EX-4, where a non-palindrome returns True.

Each of these requirements offers two readings: either the description is right and the examples are wrong, or the answer is meant to be inverted. Every example agrees with the inverted reading. R-EX-1 has a third reading: the example is right because the empty string doesn't count as a palindrome.

**Other ambiguities**
- **R-DEF-1, "palindrome":** whether case matters, and whether spaces and punctuation count or are ignored.
- **R-DEF-1, "given string":** whether the empty string counts as a palindrome.
- **R-FN-3, "Checks":** the signature has no return type, so it's unclear whether the result must be exactly `True`/`False` or any value that tests true or false.