I've written `formal/agent_a.yaml` with 9 items. `fcp lint` reports clean, and the `fcp explain` output matches what I meant for every item. I also wrote a small Python script to test the subsequence formula and the R-FN formulas against a reference implementation, but running it needed approval and didn't run. So that extra check is not done; the formulas have been checked by reasoning and by lint only.

**Items**
- **Definitions:** `K = 2`, `returned` (outcome is 0), and `subseq` for R-FN-3. There's no built-in subsequence operator, so `subseq` says: some choice of positions in `numbers` (one of the 256 possible subsets of the 8 slots) gives exactly `result`, in order.
- **Properties (7):**
  - RA-IO-2: the outcome is always 0.
  - RA-FN-1: a value that occurs exactly K times is not in `result`.
  - RA-FN-2-KEEP and RA-FN-2-ADD: no other value is dropped, and nothing is added.
  - RA-FN-3: `result` is a subsequence of `numbers`.
  - RA-EX-1: the doctest input gives `[1, 3, 4]`.

  Every FN property applies only when the call returns, because the requirements talk about "the returned list". Whether a call returns at all is RA-IO-2.
- **Scenario (1):** RA-EX-1-S, the doctest call and answer must be reachable.
- **Decisions:** all 8 flagged phrases are recorded.

**Left unformalized (3)**
- **R-NF-1:** it is about the deliverable (Python code with this signature), not about any signal.
- **R-IO-1:** the interface already guarantees it. `numbers` is always a list of at most 8 integers from 0 to 255, so there is nothing left to assume.
- **R-FR-1:** covered by the frame rule F-EMPTY, which frame.md says need not be restated.

**Problems in the specification**
1. **K is never defined.** The prompt says "occur K time(s)" but gives no K, and `candidate` has no parameter for it. I took K = 2, the only value the doctest fits, and noted this on every affected item rather than treating it as settled.
2. **"time(s)" conflicts with the example.** The singular "time" allows K = 1, which would turn `[1,2,3,2,4]` into `[2,2]`. Any K of 3 or more removes nothing.
3. **"Exactly" or "at least" is open.** The doctest doesn't decide it. I took the literal "exactly K times", so a value occurring 3 or more times is kept. This is the decision most likely to differ from another formalizer, because the usual remove-duplicates task removes every repeated value.
4. **Small gaps between text and encoding:**
   - Outcome 0 also requires the list to fit the encoding, which is slightly stronger than "a list of integers". It makes no difference once the FN rules hold.
   - The "remove" reading (new list or in-place) can't be seen in the trace, so it changes no formula.
   - R-FN-3's "i.e. subsequence" says more than the quote's "keep order": it also rules out added or extra-repeated elements.