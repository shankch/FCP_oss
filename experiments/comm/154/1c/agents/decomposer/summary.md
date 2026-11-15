I split spec.md into 14 atomic requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`; each quote points to the right source line, with the frame rule at frame.md line 52.

**The main finding is that all six examples contradict the rule they illustrate.** Each one gives the opposite of what "return True if b or any of its rotations is a substring of a" produces:

| Example | Spec says | Rule gives | Why |
|---|---|---|---|
| `("abcd","abd")` | True | False | no rotation fits |
| `("hello","ell")` | False | True | `"ell"` is in `"hello"` |
| `("whassup","psus")` | True | False | no rotation fits |
| `("abab","baa")` | False | True | rotation `"aba"` fits |
| `("efef","eeff")` | True | False | no rotation fits |
| `("himenss","simen")` | False | True | rotation `"imens"` fits |

All six do fit the opposite rule: True exactly when neither b nor any rotation of b is in a. I recorded each contradiction as an ambiguity on both sides. It sits on the scenario, and on R-RES-1 for the three True-direction cases or R-RES-2 for the three False-direction cases. Each entry has two readings: "the rule is right" and "the example is right".

**Requirements:**
- **R-NF-1** (non-functional): deliver a Python `cycpattern_check(a, b)`.
- **R-DEF-1/2/3** (definitions): a is the first word and b the second; a rotation is a cyclic shift `b[k:]+b[:k]`; a substring is a run of adjacent characters.
- **R-IN-1** (assumption): both arguments are words.
- **R-RES-1** (guarantee): returns True if b or a rotation of b is a substring of a.
- **R-RES-2** (guarantee): returns False otherwise. I wrote this separately because the spec only says when to return True.
- **R-EX-1 to R-EX-6** (scenarios): the six examples.
- **R-FR-1** (frame rule F-ZERO): `result` is 0 unless `outcome` is 0.

**Other ambiguities flagged:**
- **"words":** any string, including empty, vs. non-empty letters only, with other calls outside the contract.
- **"rotations":** cyclic shifts vs. any rearrangement of b's characters.
- **"substring":** adjacent characters vs. characters in order but with gaps; also case-sensitive vs. ignoring case.
- **"return True":** the boolean True vs. any truthy value.
- **Empty b:** True (the empty string is in every string) vs. False.
- **"return True if":** if-and-only-if (False otherwise) vs. leaving the result open when the condition fails.