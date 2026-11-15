I split spec.md into 16 requirements. `fcp anchor` accepted every quote on the first run ("anchored 16 requirements") and wrote `requirements.yaml`.

**What the requirements cover**
- **Task and interface:** R-TASK-1 says to finish the given stub. R-IF-1 says the function is named `fib4` and takes one argument, `n`. R-ENV-1 is an assumption that the caller passes an integer `n`.
- **Definition:** R-DEF-1 says the Fib4 sequence is defined by the four starting values and the recurrence that follow it.
- **Guarantees:**
  - R-BASE-1 to R-BASE-4: the starting values `fib4(0)` to `fib4(3)` are 0, 0, 2, 0.
  - R-REC-1: each later value is the sum of the four before it.
  - R-FN-1: `fib4(n)` returns the n-th element as an integer.
- **Non-functional:** R-NF-1 says "efficiently". R-NF-2 says "Do not use recursion".
- **Scenarios:** the three docstring examples, R-EX-1 to R-EX-3.
- **Frame:** R-FR-1 is the frame rule F-ZERO. Its ID matches the `req: R-FR-1` already in design.yaml.

**Main contradiction**
The recurrence and the docstring examples disagree. Starting from 0, 0, 2, 0, the recurrence gives `fib4(5)=4`, `fib4(6)=8` and `fib4(7)=14`. The examples say 0, 0 and 2. I recorded this as a two-reading ambiguity on R-REC-1 and on each of R-EX-1, R-EX-2 and R-EX-3: either the recurrence is right or the examples are.

The example `fib4(7) -> 2` is a special case: it is what the recurrence gives at n=7 if you accept the wrong values for n=5 and n=6. I noted that on R-EX-3.

**Other ambiguities flagged**
- **Which n the recurrence covers:** only n ≥ 4, or also negative n.
- **"the n-th element":** counting from 0 or from 1.
- **"compute":** must return an `int`, or only has to produce the value somehow (printed, or as a float).
- **"efficiently":** four readings, from linear time with constant memory to O(log n) to "finishes before the checker's time limit".
- **"recursion":** only `fib4` calling itself is banned, or any recursion is, including helpers and memoized recursion.
- **"n: int":** whether negative `n` can be passed.