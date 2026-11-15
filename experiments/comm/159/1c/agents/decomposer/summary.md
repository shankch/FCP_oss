I've written `requirements_draft.yaml` with 19 requirements, and `fcp anchor` accepted every quote on the first run (`anchored 19 requirements`), so `requirements.yaml` is ready.

**What the 19 requirements cover**
- **Task:** one non-functional requirement (R-API-1): deliver a Python `eat(number, need, remaining)`.
- **Definitions:** the rabbit story (R-CTX-1), what each of the three arguments means (R-DEF-1..3), and "will still be hungry" (R-HUN-1).
- **Guarantees:**
  - R-RET-1: the function returns a list of exactly two elements.
  - R-TOT-1: if `remaining >= need`, the first element is `number + need`.
  - R-TOT-2: if `remaining < need`, the first element is `number + remaining`.
  - R-LEFT-1: if `remaining >= need`, the second element is `remaining - need`.
  - R-LEFT-2: if `remaining < need`, the second element is `0`.
- **Scenarios:** the four examples (R-EX-1..4).
- **Assumptions:** the three `0 <= x <= 1000` input limits (R-ENV-1..3).
- **Frame rule:** F-EMPTY (R-FR-1), which matches the `req` that `design.yaml` already uses.

**Contradictions, each recorded as an ambiguity on both sides**
- **R-LEFT-1 vs R-EX-1, R-EX-2, R-EX-3:** the prose says the second element is "the number of carrots left after your meals". But in every example the second element is just the `remaining` argument, unchanged: `[11, 10]`, `[12, 9]` and `[11, 10]` instead of `[11, 4]`, `[12, 1]` and `[11, 0]`.
- **R-LEFT-2 vs R-EX-4:** "you will eat all remaining carrots" means none are left, but `eat(2, 11, 5) -> [7, 5]` gives 5 rather than 0.

The first elements of all four examples agree with the prose.

**Other ambiguities flagged**
- **"an array":** a list or a tuple. The adapter only counts a list as a normal return.
- **"total number of eaten carrots":** whether it includes the carrots already eaten (`number`). The examples say it does.
- **What `need` means:** extra carrots on top of `number`, or the day's total. The examples say extra.
- **"need to eat more carrots":** eat exactly `need`, or at least `need`.
- **"will still be hungry":** just part of the story, or the return value must show the unmet need.
- **Each input limit:** a promise by the caller (anything outside the range is unspecified), or something the function must check and reject.

I left out "Have fun :)" because it isn't a requirement.