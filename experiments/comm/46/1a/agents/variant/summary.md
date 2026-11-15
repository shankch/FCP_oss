I wrote `formal/variant.yaml`. `fcp lint` reports no errors, and the `fcp explain` rendering matches what each item is meant to say. Under the readings you assigned, though, the set contradicts itself, so no implementation can satisfy all of it.

**Items: 14**, plus the frame rule F-ZERO from design.yaml, which covers R-FR-1.
- **Assumption (1):** RV-IF-1 says `n >= 0`. This is your reading of "n: int"; the interface already makes n unsigned.
- **Properties (10):**
  - RV-BASE-1 to RV-BASE-4: the four base values, taken literally as what the call returns.
  - RV-REC-1 and RV-REC-2: the recurrence with every sign as '+', and the examples taken as right. The recurrence holds from n = 5, and fib4(4) = 0, the only value that makes the examples fit.
  - RV-FUN-1: counting from 1, fib4(n) returns the stated definition's element n−1, with fib4(0) left open.
  - RV-EX-1 to RV-EX-3: each example is a required return value.
- **Scenarios (3):** RV-EX-1-S to RV-EX-3-S say each example call is possible.
- **Decisions:** all 9 flagged phrases are recorded. For the three examples, which you didn't assign, I chose reading 1 (the example is right), to match your reading of the recurrence.

**Lookup tables.** Calls are independent, so the sequences are written out as two lists: `seq_def` is the definition as stated, and `seq_ex` is the version the examples fit. Values go up to about 1.2·10^35, so all of them fit in `result`.
- I computed the values by hand, because Python and `bc` weren't permitted. Building them from FCP `defs` that refer to each other doesn't work either: expansion is exponential, so a 32-step chain never finished linting.
- Checks: each list was built one way and checked against the four-term sum every five steps and at the end. An identity linking the two lists also holds at n = 81 and at n = 127. I compared every entry in the file against my working.
- No tool evaluated these numbers, so they rest on those manual checks.

**Left unformalized (4):**
- **R-TASK-1:** it describes the deliverable, not how a call behaves.
- **R-DEF-1:** a definition; it's covered by the base-value and recurrence items.
- **R-NF-1** (linear time, constant memory) and **R-NF-2** (fib4 must not call itself): neither time, memory nor which functions are called shows up in the trace. The one visible effect of slowness, a call that never finishes, is already excluded because the other items require outcome 0.

**Problems in the specification:**
1. **The definition contradicts the examples.** With any signs, the base values give fib4(5) = −4, 0 or 4, never 2. With all '+', the definition gives 4, 8, 14 where the examples say 2, 4, 6.
2. **Your readings conflict with each other.** Counting from 1 (RV-FUN-1) contradicts RV-BASE-3 at n = 2, RV-BASE-4 at n = 3, RV-EX-3 at n = 7, and RV-REC-1 for every n ≥ 7. RV-EX-3-S can never be reached alongside RV-FUN-1. FCP's consistency checks should report all of this.
3. **"The definition" means two things.** Your R-REC-1 reading says the definition is wrong as stated, while your R-FUN-1 reading uses "the value the definition gives". I followed the R-FUN-1 reading's own example values, which come from the definition as stated, and said so in the note.
4. **"+/-" leaves the signs undefined**, and nothing says what happens for a negative n. The typos ("Fibbonacci sequnece") are harmless.