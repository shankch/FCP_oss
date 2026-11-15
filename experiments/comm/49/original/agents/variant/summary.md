I wrote `formal/variant.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I meant each item to say.

**Items: 10** — 5 properties and 5 scenarios. The adapter adds its rule F-ZERO on top of these.
- **R-RES-1:**
  - **RV-RES1-OUT:** for p ≥ 1, the call ends with outcome 0 or 2, never 1.
  - **RV-RES1-VAL:** for p ≥ 1 and n ≠ 0, an integer return equals (2 XOR n) mod p. FCP-PL's `%` only accepts a constant divisor, so I used a universally quantified quotient `q` (a rigid, not ghost state).
  - **RV-RES1-ZERO:** for p ≥ 1 and n = 0, an integer return is 1.
- **R-RES-2:** RV-RES2-RAISE says p = 0 gives outcome 1.
- **R-EX-3:** RV-EX3-ALL says n = 0 gives an integer return of 1 for every p.
- **R-EX-1 to R-EX-5:** one scenario per doctest, RV-EX1 to RV-EX5.
- **Decisions:** I took reading 2 for all five phrases you specified. You didn't specify R-NUM-1, so I chose reading 1 (efficiency). Every affected item's note says the reading was imposed by your request and that another reading seems more natural.

**Not formalized (4):**
- **R-TASK-1:** it describes the deliverable, not anything a call does.
- **R-SIG-1:** the name and argument order are already fixed by the `function` section of design.yaml.
- **R-NUM-1:** under reading 1, the only thing visible in the trace is "no outcome 1 for p ≥ 1", so it's covered by RV-RES1-OUT, RV-RES1-VAL and RV-RES1-ZERO.
- **R-FR-1:** this is F-ZERO, which frame.md says is part of every set by construction.

**Problems with this combination of readings:**
1. **The set contradicts itself.** Under the XOR reading, modp(3, 5) = 1, modp(1101, 101) = 93 and modp(3, 11) = 1. So scenarios RV-EX1, RV-EX2 and RV-EX4 can't be reached alongside RV-RES1-VAL. Only RV-EX3 and RV-EX5 are consistent (modp(100, 101) = 102 mod 101 = 1).
2. **No behaviour satisfies modp(0, 0).** I read "every p" in R-EX-3 literally, including p = 0. That clashes with RV-RES2-RAISE, which requires an exception at p = 0. If you'd rather limit R-EX-3 to p ≥ 1, it's a one-line change.
3. **The two R-RES-1 readings disagree about n = 0.** The "modulo p" reading says 2^0 = 1, but under the XOR reading 2^0 would be 2. I kept the value 1 as the reading states it.
4. **The "Return" reading can't be checked in the trace.** The adapter records a float as outcome 2 with result 0, so its value is invisible. To accept 3.0, RV-RES1-OUT accepts every outcome-2 return, which also lets through wrong floats, strings and negative numbers.
5. **"Must raise" can't be told apart from hanging.** Outcome 1 also covers a call that never finishes, so RV-RES2-RAISE accepts a hang at p = 0.

I haven't run `fcp check`, so I worked out problems 1 and 2 by hand; the tool hasn't confirmed them.