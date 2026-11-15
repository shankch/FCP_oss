I've written `formal/agent_a.yaml`. Lint reports it clean, and I read the `fcp explain` output back: every item says what I intended.

**Items: 14 in the set plus 7 unformalized entries**
- **Assumptions (3):** RA-ENV-1/2/3 say `number`, `need` and `remaining` are each at most 1000. I took the limits as a condition on callers (reading 1). The lower bound of 0 holds automatically because the signals are unsigned.
- **Properties (5):**
  - RA-RET-1: the call returns a list of exactly two integers (`outcome == 0 && len(result) == 2`).
  - RA-TOT-1: if `remaining >= need`, then `result[0] == number + need`.
  - RA-TOT-2: if `remaining < need`, then `result[0] == number + remaining`.
  - RA-LEFT-1: if `remaining >= need`, then `result[1] == remaining - need`.
  - RA-LEFT-2: if `remaining < need`, then `result[1] == 0`.
- **Scenarios (4):** RA-EX-1 to RA-EX-4, one for each docstring example, taken exactly as written.
- **Decisions:** I recorded all 16 flagged phrases, and took reading 1 for every one (the most literal reading).
- No ghost state was needed, since the function keeps nothing between calls.

**Left unformalized (none dropped silently)**
- **R-API-1:** it asks for a Python implementation, which is about the deliverable, not about what any call does.
- **R-CTX-1, R-DEF-1/2/3:** these are definitions. Each is marked as covered by the TOT/LEFT properties that use it.
- **R-HUN-1:** "still hungry" is narrative and adds no requirement on the result. Its meaning is already in RA-TOT-2: the rabbit eats `number + remaining`, which is less than `number + need`.
- **R-FR-1:** it is already the frame rule F-EMPTY in `design.yaml`, which is added to every set. Marked as covered by F-EMPTY.

**Problems in the specification**
1. **The prose and every example contradict each other on the second element.** The prose ("the number of carrots left after your meals", "you will eat all remaining carrots") gives `remaining - need`, or 0 when stock runs out. All four examples instead return `remaining` unchanged:
   - `eat(5, 6, 10)` shows `[11, 10]`; the prose gives `[11, 4]`.
   - `eat(4, 8, 9)` shows `[12, 9]`; the prose gives `[12, 1]`.
   - `eat(1, 10, 10)` shows `[11, 10]`; the prose gives `[11, 0]`.
   - `eat(2, 11, 5)` shows `[7, 5]`; the prose gives `[7, 0]`.

   I kept both sides as written rather than picking one. As a result, the set is deliberately inconsistent: RA-LEFT-1/2 make all four example scenarios impossible to reach. The notes on those items say so, and FCP's consistency check should report it. The first elements agree with the prose in every example.
2. **Minor wording issues:**
   - "array" here means a Python list. A tuple would be recorded as outcome 2 and fail RA-RET-1.
   - "still hungry" has no visible effect on the returned value.
   - The ranges under "Constrain" don't say whether the function must reject values outside them. I took them as caller obligations, so any out-of-range call is unconstrained.
   - Typos: "thet", "Constrain".