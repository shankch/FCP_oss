I wrote `formal/agent_a.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I intended for each item.

**Items: 3, plus the frame item F-ZERO, which the tool adds automatically.**
- **RA-IN-1** (assumption, R-IN-1): the argument `s` is a word, meaning a non-empty string of letters only. FCP-PL's `isalpha` only covers ASCII letters, so a word like "café" falls outside the contract.
- **RA-IN-2** (property, R-IN-2): `outcome != 1`, i.e. for a word the call returns without raising. Returning a value that isn't an integer from 0 to 63 (outcome 2) is still allowed.
- **RA-OUT-1a** (don't-care, R-OUT-1): `result` is left free whenever `outcome == 0`. I took reading 4: the prompt never says what the function returns.

I recorded all 12 flagged phrases under `decisions`. Every one takes reading 1 except two: R-OUT-1 takes reading 4 and R-TASK-3 takes reading 2.

**Left unformalized (8):**
- **R-TASK-1 and R-TASK-3** are non-functional. I read "Add more test cases." as just the value of the `FIX` string constant, not an instruction.
- **R-TASK-2** is about the interface, which the `function` section of design.yaml already fixes.
- **R-VOW-1 to R-VOW-4** are definitions that nothing observable depends on. No sentence connects vowels to the returned value, so no item can use them. Each one's `reason` field records the reading I took: lower-case `a e i o u` anywhere, plus a lower-case `y` only as the last character of `s`.
- **R-FR-1** is `covered_by: [F-ZERO]`, the frame rule.

**Problems in the specification:**
1. **The return value is never stated.** This is the main gap. The prompt defines vowels and then stops, so the guarantee that remains is only "doesn't raise on a word." Counting vowels is the obvious intent, but I didn't assume it.
2. **Case is unclear.** The text lists only lower-case vowels and `'y'`. But the checker's test inputs include upper-case letters and `'ACEDY'`, which suggests case-insensitive behaviour was intended.
3. **The vowel list contradicts itself slightly.** "Vowels … are 'a', 'e', 'i', 'o', 'u'" reads as a closed list, then the next sentence adds `'y'`. I read "also" as extending the list.
4. **"A word" doesn't define what inputs are allowed.** It's unclear whether the empty string, spaces, digits or non-ASCII letters are valid.
5. **The return type is undetermined.** Nothing decides between returning an integer from 0 to 63 (outcome 0) and anything else (outcome 2), so a determinacy check will flag it. Under reading 4 that freedom is intended. I didn't mark `outcome` as a don't-care because RA-IN-2 still rules out outcome 1.
6. **One non-word call switches off checking for the rest of a trace.** Under the assume-guarantee rule (IR spec §6), properties are only checked while the assumption has held on every earlier call. Since reset is never re-asserted (`reset_anytime: false`), every later call after a non-word goes unchecked.