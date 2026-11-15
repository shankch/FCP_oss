I've split spec.md into 15 atomic requirements and written them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run ("anchored 15 requirements") and wrote `requirements.yaml`.

**Requirements by kind**
- **Interface:** R-IF-1 (non_functional) says to implement the Python function `cycpattern_check(a, b)`. R-IF-2 (definition) says the first word is `a` and the second is `b`.
- **Inputs:** R-IN-1 (assumption) says each call gets two words, both strings.
- **Definitions:** R-DEF-1 defines a rotation as a cyclic shift `b[k:]+b[:k]`, which includes `b` itself. R-DEF-2 defines a substring as a run of adjacent characters of `a`.
- **Guarantees:**
  - R-RES-1: if `b` or one of its rotations is a substring of `a`, the result is True.
  - R-RES-2: if none is, the result is False.
  - R-RES-3: every valid call returns a bool. It doesn't raise, hang, or return another type.
- **Scenarios:** R-EX-1 to R-EX-6, one for each docstring example.
- **Frame:** R-FR-1 is F-ZERO, under the ID that `design.yaml` already uses.

**Ambiguities flagged (7)**
- **"words"** (R-IN-1): any characters at all, or letters only, with other inputs left unconstrained.
- **"2 words"** (R-IN-1): an empty word may be allowed (an empty `b` would then give True), or it may be outside the contract.
- **"rotations"** (R-DEF-1): cyclic shifts, or any rearrangement of the letters. The efef/eeff example rules out the rearrangement reading.
- **"a substring"** (R-DEF-2): adjacent characters, possibly the whole of `a`; or strictly shorter than `a`; or characters in order but not adjacent. The abcd/abd example rules out the last reading.
- **"substring in the first word"** (R-DEF-2): whether letter case matters.
- **"return True if"** (R-RES-2): "if and only if", or only a sufficient condition that leaves other calls unconstrained.
- **"return True"** (R-RES-3): exactly the bools True and False, or any value Python treats as true or false (such as 1 or 0).

**Contradictions:** none. I checked all six examples against the rule and each one agrees with it. The False examples do support the "if and only if" reading of R-RES-2.