I wrote `requirements_draft.yaml`, and `fcp anchor` accepted all 11 quotes on the first run. The anchored output is in `requirements.yaml`.

**The requirements:**
- **Interface:** R-IF-1 (definition: the function is `fib4(n: int)`) and R-IF-2 (non-functional: complete the given function stub).
- **The sequence:** R-SEQ-1 (definition: the Fib4 sequence is "similar to the Fibonacci sequence" and "defined as follows").
- **Starting values:** R-BASE-1 to R-BASE-4 (guarantees: fib4(0)=0, fib4(1)=0, fib4(2)=2, fib4(3)=0).
- **Main obligation:** R-NTH-1 (guarantee: `fib4(n)` returns the n-th element).
- **Implementation constraints:** R-NF-1 ("efficiently") and R-NF-2 ("Do not use recursion"), both non-functional.
- **Frame rule:** R-FR-1 (`result` is 0 unless `outcome` is 0). It uses the id that `design.yaml` gives for F-ZERO.

The request has no worked examples, so there are no scenarios. I treated the four listed values as guarantees, because the request says they define the sequence.

**The biggest problem:** the prompt never states how elements after fib4(3) are computed. The ambiguity on R-SEQ-1 gives four readings:
1. Sum of the previous four elements (0, 0, 2, 0, 2, 4, 8, 14, …), which the name "Fib4" suggests.
2. Sum of the previous two elements, starting at fib4(4).
3. The Fibonacci rule from fib4(2) onward.
4. No rule at all, so only fib4(0) to fib4(3) are defined.

**Contradictions, each recorded on both sides:**
- **Reading 3 vs. R-BASE-3 and R-BASE-4:** that rule gives fib4(2) = 0 instead of 2, and fib4(3) = 2 instead of 0.
- **Reading 4 vs. R-NTH-1:** a definition with only four values conflicts with the request to compute the n-th element for every n.

**Other ambiguities:**
- **R-NTH-1, counting:** "n-th element" could count from 0 or from 1. Counting from 1 clashes with the listed values read as calls.
- **R-NTH-1, return type:** no return type is declared, so it's unclear whether a float like 2.0 is acceptable or the answer must be an int.
- **R-IF-1:** the prompt doesn't say what happens for negative n. This doesn't affect checking, since negative arguments aren't part of the trace.
- **R-NF-1:** "efficiently" could mean linear time, faster than linear, or just finishing quickly.
- **R-NF-2:** it's unclear whether the recursion ban also covers helper functions and cached recursion.