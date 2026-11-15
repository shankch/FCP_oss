I've written `formal/agent_b.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I meant for every item. I couldn't run the set against an implementation, because `fcp code` isn't available to agents. Instead I checked the formula by hand, and it gives the documented values for (3,5)→3, (1101,101)→2 and (100,101)→1.

**Items: 15, plus 8 decisions**
- **The reference model (`want`)** is the value every call must return: 2^x mod y, for each y from 1 to 127. It has no ghost state, because the function keeps nothing between calls. The IR only allows `%` by a constant, and it rejected a rigid (a fixed-but-arbitrary value) as the divisor. So `want` is a sum over every possible modulus in which only the term for the actual y counts. Inside that term, 2^x is the product of the constant factors 2^(2^i) mod y for each set bit i of x.
- **Properties (8):**
  - R-MOD-1: two properties. When y ≠ 0, the call must return an integer, and `result == want`.
  - R-NUM-1: one property, the same exact-residue check.
  - R-EX-1 to R-EX-5: one property each, saying that call always returns the documented value.
- **Scenarios (5):** each example call returning its documented value must be possible.
- **Don't-cares (2):** `outcome` and `result` are left free when y = 0.
- **Decisions:** I took reading 1 for all 8 flagged phrases. That means x is the exponent and y the modulus, `^` means "to the power of", the result is the least non-negative remainder, y = 0 is undefined, the modulus can be any positive number, and the return value must be a Python int. For "be aware of numerics" it means the result must be exact.

**Requirements left unformalized (3)**
- **R-SIG-1** ("Complete this function"): an instruction about what to deliver, which can't be seen in a trace of calls.
- **R-SIG-2** (the signature): a definition, covered by the two R-MOD-1 properties, which use reading 1.
- **R-FR-1**: already added to every set as frame rule F-ZERO, which frame.md says need not be restated.

**Problems in the specification**
1. **Names don't match.** The docstring talks about n and p, but the parameters are x and y, and nothing says which is which. Only the examples settle it.
2. **"2^n" means XOR in Python.** Only the examples show it means "to the power of".
3. **y = 0 isn't covered.** Modulo 0 is undefined, so I left both outputs free rather than requiring an exception or the unreduced 2^x.
4. **y = 1 relies on reading 1.** Under that reading the result is 0; the alternative "any congruent value" reading would also allow 1.
5. **"p" may suggest a prime.** Every example uses a prime (5, 11, 101), but the text never says so. I constrained every y from 1 to 127, so composite and even moduli are checked with no example to support them.
6. **The return type isn't stated.** I required an int, so a float such as 3.0 counts as a failure.
7. **"Be aware of numerics" can't be observed in the trace.** Whether the code avoids floats or computes efficiently doesn't show in a call's output; only the exact result does. So R-NUM-1 adds nothing beyond R-MOD-1, and RB-NUM-1 duplicates its two properties.