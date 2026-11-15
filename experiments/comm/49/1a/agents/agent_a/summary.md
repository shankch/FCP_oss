I wrote `formal/agent_a.yaml`. `fcp lint` reports it clean, and I read back the `fcp explain` output: every item says what I intended. I couldn't run any semantic checks, because `fcp check` isn't available to an agent.

**Items: 14** (7 properties, 5 scenarios, 2 don't-cares), plus the frame rule F-ZERO, which is added to every set automatically.
- **RA-MOD-1:** whenever `y != 0`, the call ends normally (`outcome == 0`).
- **RA-MOD-2:** whenever `y != 0`, `result == want`. `want` is 2^x mod y, built as a table with one entry per value of `y` from 1 to 127, each `(1 << x) % k`. FCP-PL's `%` only accepts a literal divisor: the linter rejected `% y`, a rigid divisor and a quantified divisor, so the residue can't be written as one formula.
- **RA-EX-1..5 and RA-EX-1C..5C:** each docstring example is both a property ("this call returns this value") and a scenario ("this call is possible"). requirements.yaml labels the examples as scenarios, but a doctest asserts what the call returns, so I added the property too. Each item's `note` says this.
- **RA-MOD-Z1/Z2:** `outcome` and `result` are left unconstrained when `y == 0`.

**Left unformalized:**
- **R-SIG-1:** it is about the form of the deliverable (a complete implementation keeping the signature and docstring), which no call can show.
- **R-SIG-2:** a definition; it is covered by RA-MOD-1 and RA-MOD-2, which use its reading.
- **R-NUM-1:** the only part a call can show is that the result is exact, and RA-MOD-2 already requires that for every `x` up to 2047.
- **R-FR-1:** covered by the frame rule F-ZERO.

**Decisions:** I took reading 1 for all 8 flagged phrases. The argument mapping and the XOR reading of `^` are settled by the examples (2 XOR 3 = 1, but `candidate(3, 5)` returns 3). For the others I took the most literal reading.

**Problems in the specification:**
- The docstring talks about `n` and `p`, but the signature has `x` and `y`. Only the examples show which is which.
- `2^n` is XOR in Python. Only the examples rule that reading out.
- What happens when `y` is 0 is not stated, and no example uses `y = 1`.
- All the examples use prime moduli (5, 11, 101), so the spec could be read as defined only for primes.
- "be aware of numerics" is vague. Inside the adapter's input range, any meaning beyond an exact result can't be observed.

**One thing I couldn't confirm:** whether the engines compute `1 << x` exactly up to 2^2047. The IR spec says integer arithmetic is exact, and `1 << i` is an allowed form, but I couldn't run anything to check. If the shift were truncated, RA-EX-2 (`candidate(1101, 101) == 2`) would contradict RA-MOD-2, so a consistency check would expose it. These 2048-bit values may also make the spec-only analyses slow.