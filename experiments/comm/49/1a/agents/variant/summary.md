Status: the file is written, lint is clean, and the `fcp explain` output reads as intended. The brute-force Python check of the `congruent` def needed approval and didn't run, so I checked it by hand instead.

## Summary

**`formal/variant.yaml`** has 10 formal items: 1 assumption, 3 properties and 5 scenarios, plus the frame rule F-ZERO, which is added automatically. It also has 8 `decisions`, all reading 2 as you instructed. Every note on an affected item says which instructed reading it uses.

- **RV-MOD-PRIME** (assumption): y is prime. The instructed reading for "p" names y, so x is left unconstrained.
- **RV-MOD-VAL**: when outcome is 0, `result` is congruent to `2 XOR y` modulo x. FCP-PL's `%` only allows a constant divisor, so I wrote this as "the difference equals k·x for some k in −127..127". Because the difference is at most 127 either way, that range is enough. For x = 0 it reduces to equality.
- **RV-MOD-RET**: if y ≠ 0, outcome is not 1. Outcome 2 stays allowed because the instructed "Return" and "modulo p" readings accept values the trace can only record as outcome 2: a float like 3.0, or a negative or >127 congruent integer.
- **RV-MOD-ZERO**: if y = 0, outcome is 1.
- **RV-EX-1..5**: one scenario per doctest, each requiring outcome 0 and the printed integer.

**Not formalized:**
- **R-SIG-1**: whether the function is complete and keeps its docstring is a fact about the source code, not something a call trace shows.
- **R-SIG-2**: this defines the interface, which design.yaml already sets up. The instructed reading is applied through the defs `p` and `n` (covered by RV-MOD-VAL and RV-EX-*).
- **R-NUM-1**: efficiency can't be seen in a trace, except as a call that never finishes. Outcome 1 lumps that together with exceptions, so the requirement is covered by RV-MOD-RET rather than stated on its own.
- **R-FR-1**: this is frame rule F-ZERO (covered by F-ZERO).

## Problems with the instructed readings
1. **All five examples contradict them**, so every RV-EX scenario is unreachable. For example, candidate(3, 5) gives 2 XOR 5 = 7 ≡ 1 (mod 3), but the doctest expects 3 ≡ 0. The same happens for (1101, 101), (0, 101), (3, 11) and (100, 101). All five examples fit the other readings: x is the exponent, y the modulus, and `^` means "to the power of".
2. **The readings conflict with each other.**
   - "Non-prime y is outside the contract" rules out y = 0, so the "y = 0 must raise" property (RV-MOD-ZERO) can never trigger. I kept both as written rather than reconciling them.
   - Both of those readings name y, even though the R-SIG-2 and "2^n modulo p" readings make x the modulus. As a result, the modulus x = 0 is handled by the general congruence rule, which literally means equality. A plain Python `%` would raise there instead, and RV-MOD-RET rejects that for y ≠ 0.
3. **R-NUM-1 has nothing to act on.** With `^` read as XOR, `2^n` is at most 127, so no large power ever comes up.
4. **The trace encoding limits what can be checked.** Outcome 2 can't separate the values these readings accept (a float, a negative or large congruent integer) from wrong return types. Outcome 1 can't separate a raise from a hang. So RV-MOD-RET and RV-MOD-ZERO are weaker than the readings themselves.

The spec itself also never says what happens when the modulus is 0.