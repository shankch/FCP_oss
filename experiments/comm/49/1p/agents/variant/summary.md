I wrote `formal/variant.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I meant for every item. One problem up front: two of the readings you gave for R-RES-1 contradict each other, so I could only formalize one of them.

**Items: 4**, plus F-ZERO, which the frame adds to every set.
- **RV-SIG-2** (assumption): `p >= 1`. This is the "p is a positive int" reading. The "n is non-negative" reading already holds because the trace only carries n from 0 to 1,023, so it needs no formula.
- **RV-RES-1-RET** (property): if `p >= 1`, then `outcome != 1`. The call must return something, and under the "Return" reading a float (outcome 2) counts as returning.
- **RV-RES-1-VAL** (don't-care): `result` is unconstrained when `p >= 1`. This is the "modulo." reading: no modulus is stated, so the returned value is not constrained.
- **RV-RES-2** (property): if `p == 0`, then `outcome == 1` (the call raises an exception).

The `decisions` section records all 8 flagged phrases: reading 2 for everything except R-RES-2's "modulo", where I took reading 1. Every affected note says the reading was used because you asked for it.

**Left unformalized: 3**
- **R-FR-1**: this is frame rule F-ZERO, which every set gets automatically. It is marked `covered_by: [F-ZERO]`.
- **R-TASK-1**: a non-functional requirement about delivering the code. It is not something a trace of calls can show.
- **R-SIG-1**: it only defines the function's name and parameter order, which `design.yaml` already maps to signals. Under your reading of "p: int", p need not affect the result, so no item makes the result depend on p.

**Problems in the specification and the readings**
1. **The R-RES-1 readings conflict.** The "modulo." reading says the returned value is not constrained at all. The "2^n modulo" reading says the value must be congruent to 2^n modulo p. Both can't hold. I kept the "modulo." reading because it is the more literal one (the sentence names no modulus) and it fits your reading of R-SIG-1. As a result, the "2^n modulo" reading and the "2 XOR n" reading change no formula; they appear only in the notes. If you'd rather encode the congruence-with-XOR version, I can. It's more work because `%` only accepts a constant divisor, so it needs a case split on p plus a bounded quantifier.
2. **RV-RES-2 never applies.** The assumption `p >= 1` rules out p = 0, which is the only case RV-RES-2 covers. Lint did not flag this. Treating p = 0 as "modulo 0" also clashes with the "no modulus is stated" reading.
3. **The request itself is defective.** The docstring is cut off ("Return 2^n modulo."), it never mentions p, and it doesn't say what should happen when p = 0.