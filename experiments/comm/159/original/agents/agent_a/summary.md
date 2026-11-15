I've written `formal/agent_a.yaml`. `fcp lint` reports no errors, and I read the `fcp explain` output and every item says what I meant.

**Items: 19**
- **3 assumptions** (R-IN-1..3): `number`, `need` and `remaining` are each `<= 1000`. I read "Constrain" as a condition the caller must meet, so behaviour outside that range is left unspecified. Values below 0 can't occur in the trace.
- **12 properties**, using one shorthand, `returned` = `outcome == 0`:
  - **R-RET-1:** every call returns two integers.
  - **R-RET-2:** `eaten >= number`.
  - **R-RET-3:** `left == remaining - (eaten - number)`. The stock drops by exactly what was eaten in the call.
  - **R-EAT-1/2:** when `need <= remaining`, `eaten == number + need` and `left == remaining - need`.
  - **R-EAT-3/4/5:** when `remaining < need`, `eaten == number + remaining`, `left == 0` and `eaten < number + need`.
  - **R-EX-1..4:** each example call is pinned to its exact result.
- **4 scenarios** (R-EX-1..4): each example result must be reachable. I gave the examples both a scenario and a property because `->` states what a call returns, not just a possible result. All four examples agree with the EAT and RET properties.
- **13 decisions**: I took reading 1 for every flagged phrase.

**Left unformalized: 6**
- **R-FN-1 and R-FN-2:** these are non-functional. Delivering the function, its name and its argument order are set by the adapter and can't be seen in a trace.
- **R-DEF-1, R-DEF-2, R-DEF-3:** these definitions have no checkable content on their own. They are marked `covered_by` the RET and EAT properties that use them.
- **R-FR-1:** this is `covered_by: [F-ZERO]`. `frame.md` says the frame rule is part of every set and need not be restated.

**Problems in the specification**
- **"need":** the parameter text ("the number of carrots that you need to eat") could mean the day's total. Only the examples settle it as additional carrots on top of `number`.
- **"but will still be hungry":** a 2-element return can't report this. I treated it as narrative: it shows only as `eaten < number + need`.
- **"array":** no Python type is named. The adapter's `outcome 0` accepts a list or a tuple, so my reading of "array" as a Python list can't be fully enforced. My note on RA-RET-1 says this.
- **No behaviour outside 0..1000:** the spec doesn't say whether such calls should be rejected or still follow the rule. Separately, under FCP's assume-guarantee semantics, a single out-of-range call excuses every later call in the same trace. That makes the check weaker than "each call independently" for a function with no memory.
- **Typos:** "Constrain" and "thet". Neither changes the meaning.