I wrote `formal/variant1.yaml`. `fcp lint` reports no errors, and I read back the `fcp explain` output: every item says what I meant. I didn't run `fcp check`, so the consistency and reachability analyses haven't been run. I did walk the example run (`save_balance(1250)`) through every item by hand: it meets them all and reaches the scenario.

**Items: 13**
- **1 assumption:** `cents` stays the same through a run (from R-SIG-1 and frame.md).
- **11 properties:** the result is always a bool; out-of-range input raises ValueError and makes no file calls (2 items); the balance is stored; `balance.txt` is never opened; the digits are written before the move; the move happens; fsync then close before the move; the return value; no temporary file is left; the temporary file is kept on failure.
- **1 scenario:** the example run, with its exact sequence of calls.

There are 2 ghosts. One remembers which file object is the temporary file; the other records whether `balance.txt.tmp` exists before each call. That second one is needed because `prev()` isn't evaluated at a run's first call. The rest is plain definitions built from `since`, `once` and `prev`. Both readings are recorded under `decisions` (reading 1 each) and mentioned in the note of every item they affect.

**Left unformalized:** only R-FR-1, R-FR-2 and R-FR-3. They are the frame rules already in design.yaml, so they're marked `covered_by` F-END, F-ZERO and F-LIMIT.

**Problems in the specification:**
1. **R-CLEAN-1 and R-KEEP-1 contradict each other.** With the reading given (no temporary file when the function returns), they can't both hold when `os.replace` fails. Every in-range call must call `os.replace`, and the script can always make it fail, so the set has no conforming behaviour on that input. I kept both rules as written.
2. **R-STORE-1 can't always be met.** It says the balance must be stored, with no exception, but a scripted `os.replace` failure makes that impossible and contradicts rules 5 and 7. I only require storage on runs where the script didn't make `os.replace` raise. This weakens the rule; the item's note says so.
3. **R-RET-1 vs R-ERR-1.** Taken literally, "return False otherwise" also covers out-of-range `cents`, where rule 1 says raise ValueError. I applied rule 5 to in-range values only.
4. **R-RET-1 vs R-KEEP-1.** If the function retries a failed `os.replace` and the retry succeeds, rule 5 requires True but rule 7 requires False.
5. **Things the trace can't show:**
   - Negative `cents` can't occur, because the signal is unsigned 27-bit.
   - The file contents aren't recorded, only the number each write spells. So leading zeros or a trailing newline can't be told apart from the exact digits.
   - For `cents` 0, writing "0" looks the same as a write that spells no number.
   - Digits written in two separate writes count as not stored.
6. **The required fsync reading doesn't make the save crash-safe.** It requires no flush first, so the digits can still be in Python's buffer when fsync runs. That falls short of the prompt's goal that a crash never leaves a damaged file. The prompt's own example has no flush either.