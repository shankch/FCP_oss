I wrote `formal/variant.yaml`. `fcp lint` reports clean, and the `fcp explain` rendering of every item matches what I intended. I also tried to run a small Python check of the digit formula against `str(d) in str(n)` for all n from 0 to 255, but it needed your approval and didn't run. I checked the formula by hand instead.

**Items: 12**
- **7 properties:** `RV-OUT-1`, `RV-SEL-1` to `RV-SEL-5`, `RV-ORD-1`.
- **5 scenarios:** `RV-IN-1`, `RV-IN-2`, `RV-EX-1`, `RV-EX-2`, `RV-EX-3`.
- **No ghosts or assumptions.** The only definitions are `lo = min(a,b)` and `hi = max(a,b)`.
- **10 decisions** cover every flagged phrase.
- **Notes:** every item affected by one of your readings says so in its `note`.

**What the readings add up to:** the result is the even decimal digits that occur in some integer n with min(a,b) < n < max(a,b), in ascending order, with no repeats. There is no "a, b ≥ 1" assumption, and every property applies to every call, including a = 0 and b = 0. The two "positive integers" requirements (R-IN-1, R-IN-2) are scenarios saying that a call with 0 as an argument still returns a list.

**Left unformalized (2)**
- **R-IF-1:** it is about the deliverable (the function name and its parameters), not the behaviour of a call. design.yaml already fixes these.
- **R-FR-1:** this is the frame rule F-EMPTY, which every set already includes. It is listed as `covered_by: [F-EMPTY]`.

**Problems in the specification**
1. **None of the three examples is possible under these readings.** I recorded them as written and did not repair them:
   - (2,8) and (8,2) must return [4, 6], because the exclusive reading of "between a and b" leaves only 3 to 7. So `RV-EX-1` and `RV-EX-2` can never happen.
   - (10,14) must return [2], because 2 is a digit of 12, which lies strictly between 10 and 14. So `RV-EX-3` can never happen. Read inclusively, it would be [0, 2, 4].
2. **The prose itself leaves choices open.** "odd or even" and "descending or ascending" both allow either option, and "digits" doesn't fit well with "between a and b". Only the examples settle these, which is why so many readings were flagged.
3. **R-SEL-2 lists the same phrase twice.** Both of its ambiguity entries use the phrase "between a and b", so the two decisions can only be told apart by their order. Your instructions fixed only the first one (exclusive, reading 2). For the second I chose reading 1, order-independent (min/max), because it is the literal sense of "between" and it fits the (8,2) example.