I wrote `formal/agent_a.yaml`. `fcp lint` reports clean, and the `fcp explain` output reads as I intended. One check didn't happen: I tried to run a Python script comparing my rotation/substring formula with Python's `b in a` over all rotations, but it needed approval and didn't run. I checked the formula against the six examples by hand instead.

**Items: 9 formal items, plus 5 unformalized entries and 19 decisions**
- **1 assumption, `RA-IN-1` (R-IN-1):** a and b are non-empty strings of letters. I took "words" literally (reading 2). The letter test is FCP-PL's `isalpha`, which covers ASCII letters only, so Latin-1 letters such as é count as non-letters. The two properties also include this condition, so each call is judged on its own arguments.
- **2 properties:**
  - `RA-RES-1`: if b, or a rotation of it, appears in a, the call returns the boolean True.
  - `RA-RES-2`: otherwise it returns False. I read "return True if" as "if and only if" (reading 1), and the note says so.
  - In both, a rotation means a cyclic shift and a substring means a contiguous, case-sensitive match. These come from shared definitions (`b_in_a`, `rot_in_a`, `hit`).
- **6 scenarios, `RA-EX-1` to `RA-EX-6`:** each docstring example is written exactly as given: those inputs, returning the stated value.

**Left unformalized (none dropped silently)**
- **R-NF-1:** this is about the deliverable ("Complete this function"), not about how a call behaves.
- **R-DEF-1, R-DEF-2, R-DEF-3:** these are definitions. They are built into the shared definitions and marked as covered by `RA-RES-1` and `RA-RES-2`.
- **R-FR-1:** the frame rule `F-ZERO` in design.yaml already covers it, and frame.md says it need not be restated.

**Problems in the specification**
1. **All six examples contradict the rule.** Each one gives the opposite of what the rule produces:
   - abcd/abd, whassup/psus and efef/eeff are shown as True, but no rotation of b appears in a.
   - hello/ell, abab/baa and himenss/simen are shown as False, but b or a rotation of it does appear in a.
   - The examples fit the negated rule exactly, as if the expected outputs had been flipped.
   - Following rule 4, I didn't fix this: the rule and the examples are both written as stated, so the set contradicts itself. Expect FCP's consistency check to report all six scenarios as unreachable under `RA-RES-1` and `RA-RES-2`.
2. **"return True if" never says what happens otherwise.** Read strictly as one-way, the False case (R-RES-2) is unspecified. In that case only the three False examples would conflict with the rule.
3. **"words" is vague** about empty strings, non-letters, case and non-ASCII letters. My reading makes the empty-b question (whether an empty b counts as found) irrelevant; the formula would return True for it anyway.