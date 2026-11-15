I split spec.md into 15 atomic requirements. `fcp anchor` accepted every quote on the first run ("anchored 15 requirements") and wrote `requirements.yaml`.

**The requirements**
- **Interface and purpose:** `R-IF-1` is the `simplify(x, n)` signature. `R-FN-1` is "simplify the expression x * n". Both are non-functional.
- **Definition:** `R-DEF-1` says x * n means the product of the two fractions.
- **Guarantees:** `R-RET-1` says the function returns True when the product is a whole number. `R-RET-2` says it returns False otherwise.
- **Assumptions about the inputs** (`R-IN-1`…`R-IN-6`):
  - each argument is a string representing a fraction
  - it has the `<numerator>/<denominator>` format
  - the numerator is a positive whole number
  - the denominator is a positive whole number
  - both are valid fractions
  - the denominator is not zero

  I split the positive numerator and positive denominator into two requirements, so `R-IN-3` and `R-IN-4` quote the same clause.
- **Scenarios:** `R-EX-1`…`R-EX-3` are the three examples. I checked each one against the stated rule and they all agree: 1, 1/3 and 7/2.
- **Frame:** `R-FR-1` is F-ZERO, the one frame rule in frame.md. It uses the ID that design.yaml already cites.

**Contradiction**
- "simplify the expression x * n" suggests returning a simplified fraction, but the next sentence says the function returns True or False. I recorded this as an ambiguity on `R-FN-1`, `R-RET-1` and `R-RET-2`.

**Ambiguities flagged**
- **x * n:** the product of the fractions, or Python's `*` applied to the two strings, which raises an error.
- **whole number:** whether it includes 0, only positive integers, or any integer. The phrase "positive whole numbers" in the input description hints that whole numbers include 0.
- **evaluates to:** exact arithmetic or floating point, which can give the wrong answer for large inputs.
- **returns True / False:** the Python booleans exactly, or any truthy or falsy value.
- **otherwise:** only for valid inputs, or also return False (rather than raise) for invalid ones.
- **The input format:**
  - whether leading zeros, whitespace or `+` signs are allowed
  - whether it is a promise by the caller or something the function must check
- **valid fractions:**
  - whether a zero numerator counts; this sentence doesn't exclude it, though the format sentence does
  - whether fractions must be in lowest terms; the example "10/2" argues against that
- **You can assume:** whether behaviour on invalid inputs is left unconstrained.