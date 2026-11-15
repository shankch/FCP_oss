I wrote `formal/agent_a.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I meant for each item.

**Items: 4 formal items, plus 4 requirements recorded as unformalized and 8 decisions.**
- **`RA-RES-1-OK`** (R-RES-1): when p ≥ 1, the call returns an integer (`outcome == 0`).
- **`RA-RES-1-VAL`** (R-RES-1): when p ≥ 1, `result == pow2n_mod_p`, which is (2**n) % p. FCP-PL only allows `%` with a constant divisor, and lint also rejects a rigid there. So the def splits p into its values in four chunks, because a quantifier can cover at most 256 values. I checked the split by hand: each p from 1 to 1023 picks exactly one term. I couldn't run a script to confirm it because the command wasn't approved.
- **`RA-RES-2-OUTCOME`, `RA-RES-2-RESULT`** (R-RES-2): `outcome` and `result` are don't-cares when p = 0.

**Unformalized (4):**
- **R-FR-1:** this is the frame rule F-ZERO, which is added to every set automatically. I marked it `covered_by: [F-ZERO]`.
- **R-TASK-1:** a non-functional statement about the deliverable, not about any call. If the function is missing or never finishes, the call ends with outcome 1, which `RA-RES-1-OK` rejects.
- **R-SIG-1:** a signature can't be seen in the trace; the adapter always calls `modp(n, p)`. A wrong signature would raise an error, which `RA-RES-1-OK` also rejects.
- **R-SIG-2:** the trace only ever carries integers from 0 to 1023. Under the readings I took (any int, p = 0 allowed), this obligation rules out no trace value, so I added no assumption.

**Decisions:** I took reading 1 for every flagged phrase except R-RES-2 "modulo", where I took reading 3 (p = 0 is unconstrained). Requiring an exception or returning 2^n would add behaviour the text never states.

**Problems in the specification:**
1. **The docstring is cut off.** "Return 2^n modulo." never names the modulus, and p is never mentioned. Strictly, the most literal reading of "modulo." would be reading 2: the value is unconstrained. I didn't take it, because it leaves R-RES-1 constraining nothing and gives p no role. I took p as the modulus and said so in the item's note. This is the one place I didn't take the most literal reading.
2. **2^n mod 0 is undefined**, yet the signature (`p: int`) allows p = 0 and no exception is named anywhere. This conflicts with R-SIG-2.
3. **"2^n" is XOR in Python.** I read it as exponentiation.
4. **"modulo" could mean any congruent value.** Under my reading (the least non-negative remainder), `modp(0, 1)` must be 0. An implementation returning 1 there would pass under the "any congruent value" reading but fail mine.