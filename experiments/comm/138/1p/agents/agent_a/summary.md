I wrote `formal/agent_a.yaml`. `fcp lint` reports no errors, and the English from `fcp explain` matches what I meant for every item.

**Items: 4 properties.** The frame rule F-ZERO is added to every set automatically.
- **RA-RET-1** (R-RET-1): every call returns normally, i.e. `outcome == 0 || outcome == 2`. This rules out code 1 (raised or didn't finish) and also code 3, which the adapter never produces.
- **RA-RET-2** (R-RET-2): `outcome != 2`, so the function never returns something other than True or False.
- **RA-SUM-1** (R-SUM-1): if n is even, the call returns True (`outcome == 0 && result`).
- **RA-SUM-2** (R-SUM-2): if n is odd, the call returns False (`outcome == 0 && !result`).

**Not formalized (4):**
- **R-IF-1 and R-IF-2:** non-functional. "A complete implementation" and the function name and parameter are properties of the code and the adapter setup, not of any call trace.
- **R-DOM-1:** there's nothing for the environment to guarantee. Every 16-bit value of n is a valid "given number" under any of the readings, so any assumption would always be true.
- **R-FR-1:** `covered_by: [F-ZERO]`, the frame item in design.yaml. frame.md says frame rules don't need restating.

**Readings chosen (9 decisions):**
- **The function name supplies "even" (reading 1).** Taking the name as part of the text is a judgement call. Under the other reading the summands' kind is stated nowhere, and R-SUM-1/R-SUM-2 couldn't be formalized at all.
- **"the sum of exactly 4" means any 4 even integers (reading 3), repeats allowed ("exactly 4" reading 1).** That makes "can be written" the same as "n is even". On the trace, where n ≥ 0, reading 2 gives the same condition.
- **"the given number n" means any number (reading 3).**
- **"Evaluate whether" means return a bool (reading 1).**

**Problems in the specification:**
1. **The docstring stops mid-sentence** after "the sum of exactly 4" and never says what the summands are. The only hint is "even" in the function name.
2. **Nothing says the summands are positive.** The natural intent is "positive even numbers" (n even and n ≥ 8), but the text doesn't say so. Under my literal reading, n = 0, 2, 4, 6 return True; under the positive reading they return False. A formalizer or implementation that assumes "positive" will disagree with this set on exactly those four values. My reading also makes "exactly 4" meaningless, since any even n is n + 0 + 0 + 0. That hints the text is missing a word, but I didn't add one.
3. **No return type, input domain, error behaviour or examples are given.** Those requirements depend entirely on readings of "Evaluate whether" and "the given number".