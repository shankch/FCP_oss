I wrote `formal/agent_b.yaml`. `fcp lint` reports clean, and the `fcp explain` rendering of every item reads as I intended.

**Items: 13**, plus the frame rule F-ZERO that fcp adds to every set.
- **10 properties:**
  - RB-BASE-1 to RB-BASE-4 check the four base values with literal constants.
  - RB-REC-1 checks every call with n ≥ 4 against the model.
  - RB-REC-2 states the recurrence directly between consecutive calls n-4 … n-1, n, without using the model.
  - RB-FN-1 says every call returns normally with the element at index n.
  - RB-EX-1 to RB-EX-3 require the three doctest values. These requirements are tagged as scenarios, but I also made them properties because a doctest fixes the value every call must return.
- **3 scenarios** (RB-EX-1S to RB-EX-3S) say the doctest results must be possible.
- **12 decisions**, one for each flagged phrase. I took reading 1 everywhere except "efficiently" and "Do not use recursion.", where I took reading 2.

**The model and how far I checked it.** fib4 keeps no state between calls, so there is no ghost state to drive; the model is a def computed from n. I couldn't compute a table of values outside fcp: Python, bc and shell arithmetic all needed approval, and only lint/explain/anchor are open to an agent. A chain of defs (f4 = f3+f2+f1+f0, …) also doesn't work, because lint expands defs naively and already hung at f40. So `fib4_n` uses an exact closed form: it reads the base values [0, 0, 2, 0] off the coefficients of xⁿ mod (x⁴ − x³ − x² − x − 1), taken from 2^(128n) mod p(2^128).
- I checked it by hand for n = 0 to 7 only.
- The literal-value items (RB-BASE, RB-EX) and RB-REC-2 will cross-check it in the later consistency analyses, which I could not run.
- It creates constant intermediates up to 2^16256, so the downstream engines must fold constants for it to be fast.
- fib4(127) is about 2^117.5, so every value fits the 128-bit `result`.

**Unformalized: 7**
- **R-SIG-1** (name and signature): fixed by the adapter, not visible in the trace.
- **R-IN-1** (n is an int): always true by construction, since n is 0 to 127.
- **R-IN-2** (negative n is free): negative arguments never appear in the trace.
- **R-DEF-1**: a definition; it is realized by the model, so I listed the items that use it under `covered_by`.
- **R-NF-1** (efficiently): the trace records no time or memory. The only visible effect, a call that never finishes, is already rejected by RB-FN-1.
- **R-NF-2** (no recursion): a property of the code's structure, not visible in calls.
- **R-FR-1**: covered by the frame rule F-ZERO.

**Problems in the specification**
- **The recurrence line has no domain.** Read for every n, with terms before index 0 taken as 0, it contradicts fib4(2) = 2 and fib4(3) = 0. It only fits the base values if negative-index terms come from running the recurrence backward (−2, 4, …). I read it as applying from n = 4; inside the trace the two readings agree.
- **The prompt never says what fib4 should do for negative n.**
- **"Similar to the Fibbonacci sequnece" has two typos** and doesn't say what, if anything, carries over from Fibonacci.
- **"Efficiently" is vague,** and neither it nor "Do not use recursion" can be checked by running calls.
- **The examples are consistent.** fib4(5) = 4, fib4(6) = 8 and fib4(7) = 14 match counting from 0 with the base values and recurrence.