I wrote `formal/agent_a.yaml` with 5 properties, 4 requirements left unformalized and 6 decisions. `fcp lint` reports no errors, and I read the `fcp explain` output back to confirm each item says what I intended.

**Items**
- **RA-SIG-2** (R-SIG-2): every call returns normally, `outcome == 0`.
- **RA-RM-1** (R-RM-1): no value of `numbers` appears in `result`.
- **RA-RM-2** (R-RM-2): each value appears in `result` at most as many times as in `numbers`.
- **RA-RM-3** (R-RM-3): `len(result) == 0`.
- **RA-RM-4** (R-RM-4): `result` is a subsequence of `numbers`. I wrote this as "some set of positions in `numbers` (an 8-bit mask), read in order, gives exactly `result`", using no ghost state. I tried to test this formula against a brute-force subsequence check, but the command needed your approval and didn't run. I've only checked it by reasoning.

For every flagged phrase I took reading 1, the most literal one.

**Left unformalized**
- **R-TASK-1, R-SIG-1:** these are about how the code is written (header, names, type annotation), which the trace can't see. A missing or misnamed function would still show up as `outcome != 0`, which RA-SIG-2 rejects.
- **R-IN-1:** the input encoding already guarantees it, so an assumption would always be true and add nothing.
- **R-FR-1:** `covered_by: [F-EMPTY]`, the adapter's frame rule, which is part of every set.

**Problems in the specification**
1. **The prompt looks cut off.** "remove all elements that occur" names no condition. Every element of a list occurs in it, so read literally the function always returns `[]`. I formalized that literal reading, as the rules require, and did not supply the missing condition (probably "more than once"). Under this reading R-RM-1 and R-RM-3 don't contradict each other; the "kept" part of R-RM-3 just applies to nothing. Any normal deduplicating code will fail RA-RM-1 and RA-RM-3.
2. **The prompt states no order for the result.** RA-RM-4 relies on reading "remove" as keeping the remaining elements in order.
3. **R-SIG-2 is slightly stronger than the prompt.** The encoding reports a list of integers outside 0..255 under the same `outcome == 2` as returning the wrong type, so the closest I could get was `outcome == 0`. RA-RM-2 keeps returned values inside `numbers`, so a correct answer always fits.
4. **The encoding is narrower than "a list of integers".** It allows at most 8 numbers, each 0..255, and no negatives.
5. **"Remove" is ambiguous but can't be told apart in the trace.** Making a new list and deleting in place give identical traces, because only the argument as passed and the returned list are recorded.