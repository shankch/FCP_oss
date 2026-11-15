I wrote `formal/variant.yaml` with 17 items. `fcp lint` reports clean, and `fcp explain --set variant` reads back as intended.

**Items**
- **1 assumption, `RV-IN-1`:** every character of `s` is a lower-case letter a–z. This is your reading of "a string". Calls with any other string are outside the contract.
- **8 properties:**
  - `RV-RET-1` is `outcome != 1`. Because of your reading of "check", the function may return a non-bool value and only raising or not finishing is ruled out.
  - `RV-HAP-4`: if `len(s) >= 3` and `blocks_ok` holds, the result is True or a non-bool value. `blocks_ok` checks the complete, non-overlapping blocks of three letters (letters only, non-letters skipped). Within each block, neighbouring letters must differ, ignoring case.
  - `RV-EX-1`…`RV-EX-6` state each example literally. "False" means it returns without raising and `happy` is false; "True" means `happy` is true or the value is a non-bool.
- **6 scenarios, `RV-EX-*-S`:** each example's result must be possible alongside every other item.
- **2 don't-cares on `happy`:**
  - `RV-HAP-2` covers strings shorter than 3, except 'a' and 'aa'.
  - `RV-HAP-3` covers strings of length 3 or more that fail `blocks_ok`, except 'aabb' and 'xyy'.

  Both follow from reading "happy if" as a sufficient condition only.
- **`decisions`:** all 19 flagged phrases are recorded as reading 2, and every affected item's note says which reading it uses.

**Left unformalized**
- **R-HAP-1:** it is a definition, so it is marked as covered by `RV-HAP-4`, `RV-HAP-2` and `RV-HAP-3`, and the reason lists the readings.
- **R-IF-1, R-IF-2:** these are non-functional (what the deliverable is, and the function's name and signature), and nothing in the trace can express them.
- **R-FR-1:** this is the adapter's built-in rule F-ZERO, which frame.md says need not be restated. It is marked as covered by F-ZERO.

**Problems in the specification**
1. **"happy if" leaves most answers open.** Read as a sufficient condition, it says nothing about strings that fail the condition except the four False examples. The phrase "happy or not" suggests "if and only if" was meant.
2. **The "check" reading weakens checking.** Any non-bool return is accepted, and the trace doesn't record whether it is truthy. So a wrong answer such as `0` for 'abcd' cannot be caught.
3. **The non-overlapping-blocks reading leaves gaps.** It doesn't say what happens to a leftover group of one or two letters. I took the literal reading and don't check it, so 'abcdd' must return True. "Its length" could mean characters or letters; I used `len(s)`.
4. **Two readings have no effect here.** Because `RV-IN-1` admits only lower-case letters, the "letters only" and "ignore case" readings change nothing for calls inside the contract. The items still state them, so each one means its reading even on its own.
5. **The examples don't contradict the rule here.** R-EX-4 and R-EX-6 conflict only if "distinct" means "not all three the same" or "no window repeats". Under the adjacent-letters reading, 'aab' and 'xyy' fail anyway.
6. **Small wording flaws:** the examples leave out the string quotes (`is_happy(a)`), and the rule sentence has no full stop.

I couldn't run my Python cross-check of `blocks_ok` against a direct implementation of the reading, because the command needed approval. I traced the formula by hand instead: 'abcd', 'adb', 'aba', 'abccde' and 'abcdd' pass, and 'aabb', 'xyy' and 'aAb' fail.