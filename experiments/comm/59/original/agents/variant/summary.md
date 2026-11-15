I wrote `formal/variant.yaml`. `fcp lint` reports clean, and the `fcp explain` rendering matches what I intended for every item. I also tried to check the prime and largest-prime-factor definitions by brute force over every n with a Python script, but running Python needs your approval, so it didn't run. Those definitions are checked only by hand.

**Items: 5 formal items, plus the adapter's own frame rule F-ZERO.** Your three readings are recorded under `decisions` (reading 2 each) and explained in the note of each affected item.
- **RV-FN-1** (R-FN-1): for n > 1 that is not prime, the call returns either an int equal to the largest prime factor (outcome 0) or some other value (outcome 2). Outcome 2 is allowed because of your "Return" reading: a value like 29.0 counts.
- **RV-ENV-1** (R-ENV-1): n ≤ 1 must give outcome 1. Under your reading this is a rule on the function, not on the caller.
- **RV-ENV-2** (R-ENV-2): a prime n must return n (as an int, or outcome 2). This is also a rule on the function, not an assumption.
- **RV-EX-1 and RV-EX-2**: scenarios saying the calls on 13195 and 2048 can return exactly the ints 29 and 2.
- **No assumptions:** under your readings, the spec puts no obligation on the caller.
- **The definition of "largest prime factor"** is written as reusable definitions in the file: factor is a prime, it divides n, and no larger prime divides n. Divisibility only allows a fixed divisor and loops are limited to 256 steps, so it needs nested loops of about 65,000 terms in total. Lint takes about 6 seconds on it.

**Left unformalized (each points to the items that cover it):**
- **R-IF-1** (function name and signature): this is set in design.yaml and can't be seen in the trace. If the function can't be called, every call fails, which RV-FN-1 rejects.
- **R-DEF-1**: it's a definition. It is built into the definitions that RV-FN-1 and RV-ENV-2 use.
- **R-FR-1**: already covered by F-ZERO, which applies to every set.

**Problems in the specification and the adapter:**
1. **Outcome 2 hides the returned value, so your "Return" reading can only be checked loosely.** A string, a negative number, a number above 65,535 or a wrong float all look the same as 29.0 in the trace, so RV-FN-1 and RV-ENV-2 accept them too.
2. **Outcome 1 covers both "raised an exception" and "never finished".** So RV-ENV-1 can't require an actual raise; a function that hangs on n ≤ 1 passes.
3. **The doctests clash with your "Return" reading.** They print the ints `29` and `2`, so a float return would fail them as written. I kept the two scenarios literal (int results) rather than loosening them to match the reading.
4. **The requirement kinds no longer fit.** R-ENV-1 and R-ENV-2 are marked as assumptions in requirements.yaml, but under your readings both are rules on the function, so I wrote them as properties.