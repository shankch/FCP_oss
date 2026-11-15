I wrote `formal/agent_b.yaml` with 17 items covering every requirement. `fcp lint` reports it clean, and the `fcp explain` rendering of each item says what I intended. I could not run the encoding on any implementation, because the agent mode only allows `lint`, `explain` and `anchor`. Instead I checked it by hand on the three prompt examples and on ("1/2","1/2") and ("12/5","5/3").

**How it works.** There is no ghost state, because `simplify` keeps nothing between calls. The model is a set of definitions that:
- parse `a` (x) and `b` (n) into a numerator and denominator each, and check that each string is a valid fraction;
- decide whether x·n and x+n are whole numbers using exact integer arithmetic.

FCP-PL's `%` only accepts a constant divisor. So whether `den_a*den_b` divides each numerator is computed by long division over the digits: four chains of 14 steps, about 60 definitions. This is exact for strings up to 16 characters, but it is large for the solvers.

**Items:**
- **5 assumptions** (R-IN-1 for each argument, R-IN-2, R-IN-3, R-IN-4): the fraction format and positive values.
- **6 properties:**
  - R-RES-1 has two halves: if the product is whole the call returns True, and if the sum is whole it returns True.
  - R-RES-2: if neither is whole, the call returns False.
  - Each example (R-EX-1..3) is also a required input/output pair.

  The result properties only apply to calls with valid arguments.
- **4 scenarios:** the three examples, plus `("1/2","1/2")` returning True. That case shows the "either expression" reading: the sum is 1 but the product is 1/4.
- **2 don't-cares:** `outcome` and `result` are unconstrained for invalid arguments.
- **14 decisions:** reading 1 for every flagged phrase, except reading 3 ("both expressions considered") for "x * n, or x + n".

**Left unformalized:**
- **R-FN-1** (the function's name and two parameters) has no trace meaning; design.yaml already fixes it.
- **R-FN-2 and R-FN-3** are definitions. They are realized by the parsing and whole-number definitions and point to the result properties.
- **R-FR-1** is the frame rule F-ZERO, which is already part of every set.

**Problems in the specification:**
1. **"x * n, or x + n" is unclear.** I took the literal "either one is whole" reading. None of the three examples can tell it apart from "product only", because every example has a non-whole sum. The "sum only" and "both" readings contradict example 1 (1/5 + 5/1 = 26/5).
2. **"Simplify the expression"** suggests the function returns a simplified expression, but the next sentence says it returns True or False.
3. **x and n are never tied to the parameters a and b.** The answer doesn't depend on the mapping, since both operations are commutative.
4. **"Positive whole numbers" plus "do not have zero as denominator"** is redundant. The second phrase hints that a zero numerator might occur; I read "positive" literally, so it can't.
5. **The format is loose.** Leading zeros, spaces and signs are not addressed; I excluded them.

One note on process: I first tried a scratch copy of the bundle in the session scratchpad, but `fcp` refuses to run outside the workspace, so all linting was done on the workspace itself. Running a Python generator for the repetitive definitions needed approval, so I wrote them by hand and checked them line by line.