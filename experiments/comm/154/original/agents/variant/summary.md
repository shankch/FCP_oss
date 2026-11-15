I've written `formal/variant.yaml` with 9 items. `fcp lint` reports it clean, and the `fcp explain` output matches what I meant for each item.

**Items**
- **RV-RES-1** (property, R-RES-1): when the second word `b` or one of its rearrangements is a substring of the first word `a` (the definition `hit`), the call must return True or a non-bool value.
- **RV-RES-3** (property, R-RES-3): every call returns something; it never raises and never fails to finish.
- **RV-RES-2** (dont_care, R-RES-2): the returned value is free whenever `hit` is false.
- **RV-EX-1 … RV-EX-6** (scenarios): each docstring example's literal True/False must be a possible result.

**The five readings you set**
Each is noted in every item it affects and recorded under `decisions`:
- **"rotations"** means any rearrangement of `b`'s characters.
- **"a substring"** means strictly shorter than `a`, so `b` equal to all of `a` doesn't count.
- **Case is ignored** when comparing letters. FCP-PL's `lower()` only maps ASCII letters, so accented Latin-1 letters such as À and à are still compared exactly. The language offers nothing better.
- **"return True if"** is a sufficient condition only, which is why the result is free on all other calls.
- **"return True"** accepts any truthy or falsy value. The trace can't see the truth value of a non-bool return, so RV-RES-1 accepts any non-bool on a match. That is slightly weaker than "truthy". The scenarios still name the exact bool, because a looser version would hide the conflict below.

For R-IN-1, which you didn't specify, I took reading 1 for both flagged phrases: any strings, empty ones included.

**Left unformalized**
- **R-IF-1**: it's about delivering the code, not something a call trace can show.
- **R-IN-1**: under the readings I took, it only says the arguments are strings, and the interface already guarantees that.
- **R-IF-2, R-DEF-1, R-DEF-2** are definitions, realized by the `hit` definition and the signal names (`covered_by: RV-RES-1, RV-RES-2`).
- **R-FR-1** is the built-in frame rule F-ZERO, which every set already includes.

**Problems in the specification**
1. **The whassup/psus example contradicts the "any rearrangement" reading.** "ssup" (`a[3:7]`) has the same letters as "psus" and is shorter than "whassup". So RV-RES-1 requires True, and scenario RV-EX-3 (the documented False) is unreachable. I left the conflict as written rather than repairing it, so FCP's consistency check should report it.
2. **The efef/eeff example does not rule this reading out once combined with the "strictly shorter" reading**, although the reading's own note says it does. The only rearrangement that fits is all of "efef", which doesn't count, so the call is unconstrained and False is allowed.
3. **Under these readings, an empty `b` must return True only when `a` is non-empty.** When both are empty, the result is unconstrained.

I hand-checked the `hit` definition against all six examples. I also wrote a small script to test it against a brute-force model, but running it needed your approval, so it hasn't been run.