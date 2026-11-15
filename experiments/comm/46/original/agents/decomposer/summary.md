I split spec.md into 16 requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`, so no quotes needed fixing.

**Requirements by kind:**
- **Guarantees (7):**
  - R-BASE-1..4: the four starting values, fib4(0)=0, fib4(1)=0, fib4(2)=2, fib4(3)=0.
  - R-REC-1: each later value is the sum of the previous four, for n ≥ 4.
  - R-FN-1: for any n ≥ 0, `fib4(n)` returns the element at index n as an integer.
  - R-FR-1 (doc FRAME): the frame rule F-ZERO, which says `result` is 0 unless `outcome` is 0.
- **Scenarios (3):** R-EX-1..3 are the three examples, fib4(5)=4, fib4(6)=8 and fib4(7)=14. I checked them against the definition and they match.
- **Non-functional (3):** keep the given name and parameter (R-SIG-1), run efficiently (R-NF-1), and don't use recursion (R-NF-2).
- **Assumption (1):** `n` is an integer (R-IN-1).
- **Don't-care (1):** what happens for negative `n` (R-IN-2).
- **Definition (1):** what "the Fib4 number sequence" means (R-DEF-1).

**Ambiguities flagged:**
- **Apparent contradiction:** the sum-of-previous-four rule is written for every n. Read that way, and with values before index 0 taken as 0, it gives fib4(2)=0 and fib4(3)=2, which clash with the stated 2 and 0. I recorded this on R-REC-1, R-BASE-3 and R-BASE-4.
- **"n-th element":** it could count from 0 or from 1. The examples only work if it counts from 0.
- **"compute":** the function could return the value or print it; the docstring examples would look the same either way. It's also open whether the value must be an `int` or could be an equal float.
- **"efficiently":** this could mean linear time with constant memory, anything faster than naive recursion, or something like O(log n).
- **"Do not use recursion":** this could mean only that `fib4` mustn't call itself, or that no recursion at all is allowed, including helpers and memoised recursion.
- **Type of `n` and negative `n`:**
  - `n: int` might allow negative values or only non-negative ones.
  - Negative `n` could be left open, filled in by running the sum rule backwards, or treated as an error.
- **Opening sentence:** "that's defined as follows" could grammatically refer to the Fibonacci sequence rather than Fib4. It's also unclear whether "similar to Fibonacci" brings in Fibonacci conventions where the prompt says nothing.