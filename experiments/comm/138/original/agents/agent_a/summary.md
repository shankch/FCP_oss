I wrote `formal/agent_a.yaml`. `fcp lint` reports it clean, and the `fcp explain` output reads as I intended for every item.

**Items: 9.** 6 properties and 3 scenarios, plus the frame rule F-ZERO, which the tool adds to every set automatically.
- **Main idea:** n can be written as the sum of four positive even numbers exactly when n is even and n ≥ 8. Each term is at least 2, and every even n ≥ 8 equals 2+2+2+(n−6). That closed form is the def `sum4`; the derivation is in the file.
- **RA-OUT-1:** every call returns a real bool (`outcome == 0`).
- **RA-SUM-1 / RA-SUM-2:** if `sum4` holds the call returns True, otherwise it returns False.
- **RA-EX-1/2/3:** each example (n = 4, 6, 8) is both a property on every call with that n and a scenario that must be reachable. A scenario alone would not constrain the result, and the docstring states these as facts.

**Requirements without their own formal item:**
- **R-API-1** (deliver a complete function body): this is about the source code, not the calls. Its visible effect is covered by RA-OUT-1 and RA-SUM-1/2, since a stub fails on every call.
- **R-API-2** (the function name and its single parameter `n`): set by the adapter in `design.yaml`, so no trace can check it. Nothing covers it.
- **R-DEF-1, R-DEF-2** (the definitions): built into `sum4`, so covered by RA-SUM-1/2.
- **R-FR-1:** covered by F-ZERO. `frame.md` says frame rules need not be restated.

**Readings taken:** reading 1 for every flagged phrase except "the given number n", where I took reading 3 (any number), as the most literal.

**Problems in the specification:**
1. **The domain of n is not stated.** "The given number n" could include negatives or non-integers, but the trace only has integers 0 to 65,535. The checks therefore say nothing about other inputs; on that range, all three readings give the same property.
2. **"Positive" and "exactly 4" are only pinned down by the examples.** The other readings (0 counts as positive; the four terms must be different) contradict the examples for 4, 6 and 8. The text alone doesn't settle them.
3. **The examples are weaker than the rule.** `== False` and `== True` also accept 0 and 1. Under the literal reading I took, a function that returns 0/1 fails RA-OUT-1 even though it passes the docstring examples.
4. **The spec never states the simple rule** "n is even and n ≥ 8". That is my derivation from the definitions, so anyone reading the definitions differently will disagree with RA-SUM-1/2.