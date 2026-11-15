I wrote `requirements_draft.yaml` with 14 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`, so no quotes needed fixing.

**Requirements**
- **R-API-1/2** (non_functional): complete the Python stub; the function is named `is_happy` and takes one parameter, `s`.
- **R-IN-1** (assumption): the caller passes a string.
- **R-DEF-1** (definition): a string is either happy or not happy.
- **R-FN-1** (guarantee): returns True exactly when `s` is happy, otherwise False.
- **R-FN-2** (guarantee): every call finishes and returns a bool, with no exception and no other type.
- **R-EX-1…6** (scenario): the six examples, one each (`a`, `aa`, `aabb` and `xyy` give False; `abcd` and `adb` give True).
- **R-FR-1/2** (FRAME, guarantee): the frame rules F-ZERO and F-CODE, using the ids that `design.yaml` already cites.

**Main finding:** the prompt never says what "happy" means. Only the examples define it. On R-DEF-1 I flagged four readings that all fit the examples but give different answers:
- at least 3 characters, and every 3 consecutive characters are all different
- at least 3 characters, and no two neighbouring characters are equal
- at least 3 characters, and all characters are different
- at least 2 characters, and no two neighbouring characters are equal

The strings `aba`, `abca` and `ab` tell these readings apart. R-DEF-1 also has a second ambiguity: whether case matters (`aA`).

**Other ambiguities**
- **R-IN-1:** whether any characters are allowed or only lowercase letters, and whether the empty string must be answered or is a don't-care.
- **R-FN-2:** whether the answer must be the bool True/False, or any truthy/falsy value would do.
- **R-EX-1…6:** the arguments are written without quotes (`is_happy(a)`). Read as Python, that passes an undefined variable rather than a string, which is at odds with R-IN-1. It's almost certainly just informal notation, but I flagged it on each example.

**Contradictions:** none. No two statements conflict, and all the examples fit together under each reading above.