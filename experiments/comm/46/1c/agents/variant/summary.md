I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` read-back matches what I meant for every item. I couldn't run `fcp monitor` or `fcp check` because they aren't available to an agent, so the set has been linted but not compiled into monitors or run.

**Items: 13**, plus one shared def:
- **1 assumption:** RV-ENV-1, `n >= 0`.
- **9 properties:**
  - RV-BASE-1 to RV-BASE-4: the four base values.
  - RV-REC-1: the recurrence.
  - RV-FN-1: the n-th-element rule.
  - RV-EX-1 to RV-EX-3: the three examples.
- **3 scenarios:** RV-EX-1-S to RV-EX-3-S, one per example.
- **Def `fib4_seq`:** a fixed table of the sequence for n = 0 to 63 under the given readings: 0, 0, 2, 0, 2, then 0 and 0 at n = 5 and 6 from the examples, then the four-term sum (2, 4, 6, 12, …). I worked the table out by hand because running scripts needed approval, and checked it a second way, with the identity s[k] = 2·s[k−1] − s[k−5].
- R-FR-1 is covered by the existing frame rule F-ZERO.
- Every one of your prescribed readings is recorded under `decisions` and stated in the note of each item it affects.

**Left unformalized:**
- **R-TASK-1, R-IF-1:** they describe the deliverable and the interface (the interface is fixed by `design.yaml`), not the values calls return.
- **R-DEF-1:** a definition, marked as covered by the base and recurrence items. Under your readings the examples, not just the base values and recurrence, also fix the values at n = 5 and 6.
- **R-NF-1 ("efficiently" = linear time, constant memory):** a trace can't show how long a call took or how much memory it used. A call that doesn't finish shows as outcome 1, but so does an exception, so the two can't be told apart.
- **R-NF-2 ("recursion" = fib4 calling itself directly):** this is about how the code is written, which the call trace can't show.

**Problems in the specification:**
1. **The examples contradict the definition.** Base values plus the recurrence give fib4(5) = 4, fib4(6) = 8 and fib4(7) = 14, but the examples say 0, 0 and 2. Taking the examples as authoritative breaks the recurrence at n = 5 and 6. The reading leaves larger n unclear; I took the most literal choice, that the recurrence still holds there, which gives 2 at n = 7 (matching the example), then 4, 6, 12, ….
2. **Under the prescribed readings, no implementation can satisfy the set, and I left it that way on purpose.** Counting from 1 in R-FN-1 makes fib4(n) the value at index n−1. That disagrees with fib4(2) = 2, fib4(3) = 0, the recurrence at n = 4 and every n ≥ 8, and the examples fib4(5) = 0 and fib4(7) = 2. Only fib4(1) and fib4(6) agree. Expect FCP's consistency check to report RV-FN-1 as conflicting with those items. The same reading says fib4(0) has no meaning, while R-BASE-1 still requires it to return 0.
3. **Two readings can't be tested on the trace.** n is an unsigned 6-bit signal, so the negative-n part of R-REC-1 and the R-ENV-1 assumption never affect anything in the trace.
4. **"compute" makes RV-FN-1 weak.** Because the form of the answer isn't fixed, RV-FN-1 only constrains calls that return an integer; it never requires one.
5. **Typos:** "Fibbonacci sequnece".