I wrote `requirements_draft.yaml` with 15 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**The requirements**
- **R-TASK-1** (non_functional): "Complete this function:" — fill in the body of `fib4`.
- **R-IF-1** (assumption): `def fib4(n: int):` — the function takes one int, `n`.
- **R-DEF-1** (definition): the sentence that introduces the Fib4 sequence.
- **R-BASE-1..4** (guarantee): fib4(0)=0, fib4(1)=0, fib4(2)=2, fib4(3)=0.
- **R-REC-1** (guarantee): the recurrence, for n ≥ 4.
- **R-FUN-1** (guarantee): fib4(n) returns the n-th element.
- **R-NF-1** (non_functional): "efficiently".
- **R-NF-2** (non_functional): "Do not use recursion."
- **R-EX-1..3** (scenario): the three doctests, fib4(5)=2, fib4(6)=4, fib4(7)=6.
- **R-FR-1** (FRAME, guarantee): the frame rule F-ZERO, which `design.yaml` already links to R-FR-1.

**Ambiguities flagged**
- **`n: int`**: the prompt doesn't say whether negative `n` is allowed or what should happen if it is passed.
- **`+/-` in the recurrence**: four readings — all plus, alternating signs, one fixed set of signs left to the implementer, or any sign for each n. The minus readings give negative values, such as fib4(4) = -2.
- **"n-th element"**: counting from 0 or from 1. Counting from 1 with all plus signs matches two of the three examples, but not fib4(7)=6.
- **"efficiently"**: linear time with constant memory, linear time with any memory, logarithmic time, or just not exponential.
- **"recursion"**: either only `fib4` may not call itself, or no function in the code may be recursive.
- **The range of the recurrence isn't stated.** I wrote n ≥ 4 into the text instead of flagging it, because no other range makes sense.

**Contradiction between the definition and the examples**
I recorded this on R-REC-1 and on each of R-EX-1..3. I worked the numbers out by hand; running a Python check needed approval, so I didn't run it.
- **fib4(5)=2 is impossible.** From the base values, the recurrence gives -4, 0 or 4 for fib4(5), whatever the signs are.
- **With all plus signs,** the sequence runs 0, 0, 2, 0, 2, 4, 8, 14, so the examples should be 4, 8 and 14.
- **No fixed set of signs** produces both fib4(6)=4 and fib4(7)=6.
- **The examples would all fit** the all-plus recurrence if fib4(4) were 0, but no choice of signs gives 0 from the base values.

The two readings recorded are "the definition is right and the examples are wrong" and "the examples are right and the definition is wrong as stated."