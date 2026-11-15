I've written `formal/variant.yaml`. `fcp lint` reports it clean, and `fcp explain` reads back as intended for every item. I took every reading you specified and said so in the note (or the `reason`) of each item it affects.

**Items: 8 formal items, plus 4 `unformalized` entries and 9 `decisions`.**
- **RV-IF-1** (assumption): `n >= 0`. This changes nothing in practice, because the 7-bit `n` already rules out negative arguments.
- **RV-BASE-1 / RV-BASE-2:** `fib4(0)` and `fib4(1)` each return the integer 0.
- **RV-BASE-3:** `fib4(2)` returns 0, per your reading. This contradicts the listed value 2.
- **RV-BASE-4:** `fib4(3)` returns 2, per your reading. This contradicts the listed value 0.
- **RV-NTH-1:** for every `n >= 1`, the call does not raise or hang.
- **RV-NTH-2:** for every `n >= 1`, an integer result equals `elem[n-1]`. `elem` is the four-term sequence 0, 0, 2, 0, 2, 4, 8, … from your R-SEQ-1 reading, listed up to its 127th element (index 126), which fits in 128 bits.
- **RV-NF-1:** no call raises or hangs.

I chose reading 3 of "efficiently" myself (no complexity bound, only "finishes promptly"), since you didn't specify one and it is the most literal.

**Left unformalized:**
- **R-SEQ-1:** it only defines the sequence. With elements counted from 1, it reaches the calls only through R-NTH-1, so it is `covered_by` RV-NTH-2, and its values are the `elem` table.
- **R-IF-2:** keeping the stub's name and parameter is a property of the source code, not of the calls. What can be observed (calls succeed and return integers where required) is `covered_by` RV-NF-1, RV-NTH-1 and RV-BASE-1 to 4.
- **R-NF-2:** whether fib4 calls itself (helpers allowed, per your reading) can't be seen in a trace of arguments and results.
- **R-FR-1:** this is the adapter's frame rule F-ZERO, `covered_by` it.

**Problems in the specification:**
- The prompt gives no rule for elements after `fib4(3)`; "similar to the Fibbonacci sequnece" (misspelled) is the only hint. The four-term rule comes from the name and from your reading.
- The R-BASE-3 and R-BASE-4 readings assume a two-term rule starting at `fib4(2)`, which conflicts with the four-term rule starting at `fib4(4)` imposed for R-SEQ-1.
- Those two readings also disagree with each other: R-BASE-4 adds the listed `fib4(2) = 2`, while R-BASE-3 makes `fib4(2)` return 0. I used the values each reading states (0 and 2). They happen to equal what counting from 1 gives, so the set as a whole is consistent.
- With counting from 1, `fib4(0)` has no element, so only R-BASE-1 constrains that call.
- The trace records a float return without its value, so allowing a float equal to the element can't be fully checked: a wrong non-integer return gets through. I also didn't extend that allowance to the listed starting values, so a float for n = 1 to 3 fails RV-BASE-2 to 4.
- Neither "efficiently" nor "Do not use recursion" can be observed beyond calls that time out or fail.

**How the table was checked:** python3, bc and awk all need approval here, so I built the table with literal shell arithmetic. I then confirmed every entry from index 4 to 126 is the sum of the four before it, and confirmed with grep that the file holds exactly those values. I created a temporary check set during this and deleted it afterwards.