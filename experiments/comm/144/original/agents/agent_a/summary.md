I wrote `formal/agent_a.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I intended for every item.

**Items (15, all `RA-`):**
- **5 assumptions** (RA-IN-2 to RA-IN-6), one per input requirement: the format, a positive numerator, a positive denominator, a valid fraction overall, and a non-zero denominator.
- **5 properties:**
  - RA-RET-1: if the product equals a whole number `q`, the call returns True.
  - RA-RET-2: if the product lies strictly between `q` and `q+1`, the call returns False.
  - RA-EX-1 to RA-EX-3: the three docstring examples. The docstring states their return values, so I made them properties as well as scenarios.
- **3 scenarios** (RA-EX-1-S to RA-EX-3-S): each example's call and answer must be possible.
- **2 don't-cares** (RA-DC-RES, RA-DC-OUT): `result` and `outcome` are left free on arguments that are not valid fractions.

**How it works:** the numerator and denominator values are read from the characters around the first `/`, using a list of powers of ten. "Is a whole number" needs division by a value that isn't a constant, which FCP-PL doesn't have (`%` only takes a constant divisor). So I used one universally quantified rigid `q` in the range 0 to 10^20 instead of ghost state. A valid numerator has at most 10 digits, so every product is below 10^20 and fits that range.

**Left unformalized (5):**
- R-IF-1: the function's name and parameter order are an interface fact, not a trace property.
- R-FN-1: a statement of purpose, covered by RA-RET-1 and RA-RET-2.
- R-DEF-1: a definition, carried by the defs and used in the RET properties.
- R-IN-1: covered by RA-IN-2 and RA-IN-5.
- R-FR-1: the frame rule F-ZERO, which design.yaml adds to every set.

**Decisions:** I recorded all 15 flagged phrases and took reading 1 for each.

**Problems in the specification:**
- **Function vs. answer:** "simplify the expression x * n" describes a function that simplifies, but the function must return a bool. I read the phrase as purpose only.
- **Format details not stated:** the spec doesn't say whether leading zeros, spaces or signs are allowed. I took the strict format (no leading zeros), which narrows the inputs the function must handle. An input like `"05/1"` is therefore unconstrained.
- **"Whole number":** the term is ambiguous, but it doesn't matter here: with positive numerators the product is always positive.
- **Invalid inputs:** the spec never says whether the function should raise or return False on them. "You can assume" leaves that behaviour free.
- **Duplicates:** R-IN-6 (denominator not zero) adds nothing beyond R-IN-4 (denominator at least 1). R-IN-5 is just R-IN-2 to R-IN-4 together.
- **Lowest terms:** "valid fractions" doesn't say whether fractions must be reduced. The example `"10/2"` shows they need not be.
- **No size limit:** the spec puts no limit on number size; only the trace's 12-character strings bound it.

**Not run:** both `fcp check` and a Python emulation of my defs needed your approval, so neither ran. Instead I traced the defs by hand on the three examples and on edge cases (`"05/1"`, `"0/5"`, `"5/"`, `"/5"`, `"1/2/3"`, `"5/0"`), and they gave the expected results. One open risk: I don't know how the runtime checker handles a rigid whose range goes up to 10^20.