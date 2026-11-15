I wrote `formal/variant.yaml`, `fcp lint` reports it clean, and the `fcp explain` output matches what I meant for every item. Under the readings you set, the spec contradicts itself in three places, so no implementation can satisfy the whole set.

**Items: 12 in total, plus the frame rule F-ZERO, which is added automatically.**
- **Properties (8):**
  - `RV-IN-1-ANSWER`: for any lower-case strings, including empty ones and non-letters, the function must return something rather than raise or hang.
  - `RV-RET-1`: if some rearrangement of b is a subsequence of a (ignoring case), the call returns True or a non-bool. An empty b always counts as related, so it returns True.
  - `RV-EX-1` to `RV-EX-6`: each example call returns exactly the bool True or False it shows.
- **Don't-cares (4):** `result` and `outcome` are left free when either word contains an upper-case letter (R-IN-1), and when b is not related to a (R-RET-2, "if" as a sufficient condition only).
- **Helper definitions:** `has_upper` and `related`. "Some rearrangement of b is a subsequence of a" is exactly the same as "every character of b appears in a at least as often as in b", so `related` is written as that count comparison. No ghost state was needed.
- **Decisions:** all 14 flagged phrases are recorded with the reading numbers you gave, and every affected item's note says the reading was imposed by your request.

**Not formalized (3):**
- **R-IF-1:** "deliver a Python function" describes the code, not anything a call does. The adapter covers it.
- **R-IF-2:** a definition (first word = a, second word = b). It's covered by the items that use a and b.
- **R-FR-1:** already the frame rule F-ZERO, which frame.md says need not be restated.

**Problems in the specification:**
1. **Three examples contradict R-RET-1 under these readings.** "Related" means subsequence and "rotations" means any rearrangement, so b only needs its characters to appear in a, with multiplicity. That makes abcd/abd, whassup/psus and efef/eeff all "related", so R-RET-1 requires a True answer while `RV-EX-1`, `RV-EX-3` and `RV-EX-5` require False. I recorded the conflicts in the notes and didn't fix them. The other three examples agree with R-RET-1.
2. **A truthy non-bool can't be checked.** Under the "any truthy value" reading, a returned non-bool only shows up as `outcome == 2`, and the signals can't tell whether it was truthy. So `RV-RET-1` also accepts falsy non-bools.
3. **The examples are held to the literal bool True.** That's stricter than the "any truthy value" rule in `RV-RET-1`.
4. **The don't-care case has no example.** Because R-RET-2 is only a sufficient condition, the answer when b is not related is entirely open. Every example call counts as related, so none of them pins down that case.
5. **Upper-case only covers ASCII.** `isupper` and `lower` look only at A–Z, so Latin-1 capitals such as À are treated as ordinary characters. This can't cause a false failure: any pair related under ASCII case-folding is also related under Python's `.lower()`.