I wrote `formal/variant.yaml`. `fcp lint` reports no errors, and the `fcp explain` output says what I meant for every item. The set has 6 properties and one def, `rep = n % 2 == 0 && n >= 20`, meaning "n is a sum of 4 distinct positive even numbers". There are also 2 unformalized entries and 8 decisions, all reading 2 as you instructed. Every affected item's note says it uses your reading.

**Items**
- **RV-RET-1** `outcome != 1`: the call must finish without raising. Because a value equal to True or False is acceptable, a non-bool return (outcome 2) is allowed. I applied the same reading to the value items: they only constrain the answer when the call returns a real bool (outcome 0).
- **RV-SUM-1**: if `rep` holds, a bool answer must be False (the inverted reading).
- **RV-SUM-2**: if `rep` does not hold, a bool answer must be True. That covers odd n, 0, and the even n below 20.
- **RV-EX-1 / RV-EX-2**: for n = 4 and n = 6, a bool answer must be False (the description wins over the examples).
- **RV-EX-3**: for n = 8, a bool answer must be True.

**Unformalized**
- **R-IF-1**: the function name and signature are set by the adapter, not by anything in the call trace.
- **R-FR-1**: already guaranteed by frame rule F-ZERO, which is part of every set (`covered_by: [F-ZERO]`).

**Problems in the specification and in the assigned readings**
1. **The prompt contradicts itself.** Under the usual reading (summands may repeat), the representable n are the even n ≥ 8. That means 4 and 6 should give False and 8 should give True, which is the opposite of all three examples.
2. **The assigned readings conflict with each other:**
   - The inverted reading for R-SUM-1 says it makes `is_equal_to_sum_even(8)` False. That only follows if summands may repeat. With distinct summands, 8 is not representable, so the inverted R-SUM-2 requires True at 8. I recorded the claim in the note but did not formalize it.
   - Under the R-EX readings, 4 and 6 return False, but distinct plus inverted R-SUM-2 says True. RV-EX-1 and RV-EX-2 directly contradict RV-SUM-2.
   - RV-EX-3 counts 2+2+2+2 as a valid sum, which uses repeated summands. Its value at 8 (True) agrees with RV-SUM-2 only by coincidence.
3. **The interface hides the n = 4 and n = 6 contradiction.** A non-bool return (outcome 2) is recorded without its value, so with the loose return-type reading the set can still be satisfied by returning a non-bool at 4 and 6. That is a side effect of the encoding, not a real way out, and a consistency check on this set alone will not report it.
4. **The loose return-type reading is admitted too broadly.** Outcome 2 can't tell `1`/`0` apart from `None` or a string, so RV-RET-1 also accepts returns that the reading itself would reject.