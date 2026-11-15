I wrote `formal/agent_a.yaml`. `fcp lint` reports `lint: clean`, and the `fcp explain` output reads as I intended for every item. I checked the `balanced` definition by hand on a few strings: `""` and `"()"` count as correctly bracketed; `"("`, `")("` and `"())("` don't. I didn't run it through any engine.

**Items: 7 in the set** (4 properties, 1 scenario, 2 don't-cares), plus the frame rule F-ZERO that design.yaml adds to every set.
- **RA-RET-1** (R-RET-1): for an allowed argument, the call returns True or False (`outcome == 0`).
- **RA-RES-1 / RA-RES-2** (R-RES-1 / R-RES-2): for an allowed argument, the call returns True if it is correctly bracketed and False if not. "Correctly bracketed" means properly nested: no prefix has more `)` than `(`, the totals are equal, and the empty string counts as correct.
- **RA-EX-1** (property) and **RA-EX-1-S** (scenario) (R-EX-1): every call with `"("` returns False, and such a call can happen. requirements.yaml calls R-EX-1 a scenario, but the doctest states a fixed result, so I made it a property and kept the scenario as well.
- **RA-IN-1-OUT / RA-IN-1-RES** (R-IN-1): `outcome` and `result` are left free when the argument contains any character other than `(` or `)`.

**One choice you should look at:** I wrote R-IN-1 as don't-cares plus a validity guard on each property, not as an FCP assumption. Under the IR's semantics, once an assumption fails, every later check in the trace is switched off. frame.md says calls are independent, so one out-of-contract call shouldn't excuse the calls after it. A set that writes R-IN-1 as an assumption will disagree with this one on traces where an invalid call comes before a valid one that gets the wrong answer.

**Unformalized (4):**
- **R-TASK-1**: about the source code you deliver, not the interface; it can't be stated in FCP-PL.
- **R-IF-1**: the function's name and parameter are already fixed by the `function` and `interface` sections of design.yaml.
- **R-DEF-1**: a definition; I wrote it as the defs `prefix_ok`, `totals_equal` and `balanced`, used by RA-RES-1 and RA-RES-2.
- **R-FR-1**: the frame rule F-ZERO, which is in every set already.

**Decisions:** all 11 flagged phrases are recorded, and I took reading 1 for each, the most literal one.

**Problems in the specification:**
- The prompt never says what the function returns or what "correct bracketing" means. R-DEF-1, R-RES-1 and R-RES-2 all quote only the signature line, so their meaning comes from the function name alone.
- There is a single example, `"("` → False, and it is wrong under all three readings of R-DEF-1, so it can't tell them apart. R-RET-1's "always returns a bool" is also a generalisation from that one example.
- There is no return annotation, and the prompt doesn't cover the empty string or characters other than `(` and `)`.
- Two flagged readings contradict the example itself: R-IN-1 reading 3 ("must contain both brackets") and R-RET-1 reading 2 ("correct" as a verb).