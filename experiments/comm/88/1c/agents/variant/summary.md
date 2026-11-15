I wrote `formal/variant.yaml`. `fcp lint` reports "lint: clean", and I read back the `fcp explain` rendering: each item says what I meant it to say.

**Items: 9 formal items**, plus the adapter's frame item F-EMPTY, which every set includes.
- **Assumption:** RV-IN-1 says every element is non-negative. The adapter already limits elements to 0–255, so this only spells the obligation out.
- **Properties:**
  - RV-RES-1: every call returns a list (`outcome == 0`).
  - RV-RES-2: a returned list has the same length and the same elements, with the same counts, as the argument.
  - RV-ORD-1: an even sum means the result must be strictly increasing.
  - RV-ORD-2: an odd sum means the result must be strictly decreasing.
- **Scenarios:** RV-EX-1 to RV-EX-4 are the four examples. Each requires `outcome == 0`, so a call that fails can't pass the `[] => []` example.
- **Definition:** the sum is the def `psum = len(array) == 0 ? 0 : 0 + (len(array) - 1)`. That is the index reading, so parity depends only on length: odd length gives an even sum and ascending order; even length of at least 2 gives descending order.
- **Decisions:** all 14 flagged phrases are recorded. The 12 you specified all use reading 2, and every affected item's note says so. For R-EX-3 and R-EX-4 I chose reading 1 ("the example is right"), which matches the swapped-rule reading.

**Left unformalized:**
- **R-IF-1** (the function's name and parameter): this is a fact about the interface, not something a trace can show. A missing or wrongly shaped function fails every call, so it is listed as covered by RV-RES-1.
- **R-DEF-1:** it's a definition. The def `psum` implements it, and it is covered by RV-ORD-1 and RV-ORD-2.
- **R-MUT-1:** the trace has no signal for the argument after the call, so this can't be checked. Also, under the reading you gave, the in-place-sort statements override the note, so it requires nothing.
- **R-FR-1:** the frame item F-EMPTY already states it, and `frame.md` says it need not be restated.

**Problems in the specification and in the given readings:**
1. **The rule and the examples disagree.** The rule says an odd sum gives ascending order. But in the example [2,4,3,0,1,5], 2+5 = 7 is odd and the result is descending; [2,4,3,0,1,5,6] has the same problem the other way round. Under the readings you gave, I swapped odd and even in the rule.
2. **"Don't change the given array" contradicts "you will sort the given array" and "sort it".** It can't be checked with this adapter in any case.
3. **Strict ordering conflicts with the other requirements.** With strictly increasing or decreasing order, any argument of length 2 or more with a repeated value (e.g. [1,1]) has no valid answer: RV-RES-1, RV-RES-2 and the order rule can't all hold. Expect the consistency and conflict checks to report this, and expect any correct sorting code to fail RV-ORD-1 or RV-ORD-2 on such calls.
4. **Two of the readings you gave conflict, so I picked one.**
   - **One-element arrays:** the "(array[0])" in the one-element reading clashes with "the parity depends only on the length". I counted the single index 0 once, so the sum is 0.
   - **Empty arrays:** the empty-array reading says "the descending rule applies", but once the rules are swapped an even sum picks ascending.

   Neither choice changes anything when the result has the right length, because a list of 0 or 1 elements is in both orders. Both are explained in the notes.