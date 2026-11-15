I wrote `formal/variant.yaml`. `fcp lint` reports `lint: clean`, and the `fcp explain` output says what I intended for every item. I did not run `fcp check`. The contradictions listed below are worked out by hand, not confirmed by the tool.

**Items: 16 in total.**
- **1 assumption:** RV-IN-1.
- **12 properties:** RV-OUT-1, RV-RES-1, RV-RES-2, RV-RES-3, RV-RES-4-TOP, RV-RES-4-ONLY, RV-SYM-1, RV-ORD-1 and RV-EX-1/2/3.
- **3 scenarios:** RV-EX-1-S, RV-EX-2-S and RV-EX-3-S.
- **4 helper definitions**, no ghost state: `lo`/`hi` are min/max of a and b, `top_even` is the largest even number below `hi`, and `has_even` means `top_even > lo`.
- **Decisions:** one for each of the 11 flagged phrases. All the phrases you listed use your readings, and every affected note says so. R-ORD-1 "ascending order" wasn't on your list, so I took reading 1 (strictly ascending) as the most literal.

**Choices worth checking:**
- **R-RES-4:** the "even integers" reading says every even number in the range must appear, but the "examples govern" reading says only the largest is returned. The second governs the structure of the requirement, and I used the first only to say candidates aren't limited to 0–9. I took "only" literally, so the list must be exactly `[top_even]`, or `[]` when there is none. This is split into RV-RES-4-TOP and RV-RES-4-ONLY.
- **RV-RES-2:** reading "digits" as integers places no limit, so the property is deliberately always true. I kept it as an item rather than leaving it out, so it can still be compared against the other sets.
- **RV-IN-1:** the 6-bit inputs can't be negative, so the assumption excludes nothing; it only records the reading. Because 0 counts, every property applies to calls with 0 as well.
- **Examples:** each one is both a property (the call returns that list) and a scenario (that answer must be possible), because an example fixes the answer of a deterministic call.

**Left unformalized (2):**
- **R-IF-1:** the function name and its two arguments are set in the design file, not by anything visible in the trace.
- **R-FR-1:** the adapter's built-in frame rule F-EMPTY already covers it (`covered_by: [F-EMPTY]`).

**Problems in the specification and the readings:**
1. The prompt contradicts itself. "Return the even digits between a and b" conflicts with all three examples: (2, 8) gives `[8]` rather than all the even digits, and (10, 14) gives `[14]`, which is not a digit.
2. With the readings you gave, the set cannot be satisfied for these calls:
   - **(2, 8):** RV-EX-1 requires `[2,4,6,8]`, RV-RES-3 excludes 2 and 8, and RV-RES-4 requires exactly `[6]`.
   - **(8, 2):** RV-EX-2 requires `[2,4,6,8]`, RV-SYM-1 requires `[]`, and RV-RES-4 requires `[6]`.
   - **(10, 14):** RV-EX-3 requires `[]`, but RV-RES-4-TOP requires 12.

   As a result, none of the three scenarios can be reached.
3. Two readings disagree on the same word. The R-EX-3 reading treats "digit" as 0–9, while the R-RES-2 and R-RES-4 readings treat it as any integer.
4. R-SYM-1 read as "ordered" (a up to b) conflicts with R-RES-3 and R-RES-4, whose readings use min(a, b) and max(a, b). It also means the symmetry that R-SYM-1's own text claims no longer holds.