I've written `formal/agent_b.yaml`. `fcp lint` reports it clean, and the `fcp explain` rendering matches what I meant for every item. The main limitation: R-RES-1 is only partly formalized. For many calls with large `n`, the exact answer is not checked.

**Items: 15**
- **8 properties:**
  - R-RES-1: the call returns an int that fits whenever `p >= 1`; `result < p`; and `result` equals the model's expected value whenever the model knows it.
  - R-EX-1 to R-EX-5: one property per doctest, requiring that exact value.
- **5 scenarios:** one per doctest, saying the call is possible.
- **2 don't-cares:** `result` and `outcome` are left free when `p == 0` (R-RES-2).
- **Decisions:** reading 1 for every flagged phrase except "be aware of numerics", where I took reading 2 (exactness).

**The model.** A memoryless function has no protocol state, so the reference model is a set of defs plus ghosts that see only `n` and `p`, never `result`:
- **Direct window:** when 2^n < 1024·p, the residue is computed exactly by long division. That covers every `n <= 9` for any `p >= 1`, and up to `n <= 25` when `p` is 65,535.
- **Chain:** when the previous call was modp(n−1, p) with the same `p` and a known value e, the expected value is 2e mod p. This covers ascending sweeps over `n`.

I checked a handful of values by hand, including modp(16, 101) = 88 and the chain step to modp(17, 101) = 75. I couldn't run the automated comparison against Python's `pow` because running the script needed your approval.

**Unformalized: 4**
- **R-TASK-1:** says what the deliverable is, not how calls behave; its observable part is covered by the "returns an int" property.
- **R-SIG-1:** the function name and parameter order are fixed by the binding in `design.yaml`, not by the trace.
- **R-NUM-1:** advice on how to compute; its observable effects (an exact int, and the call finishing) are already required by the R-RES-1 properties.
- **R-FR-1:** already in every set as the frame rule F-ZERO.

**Problems noticed**
- **R-RES-1 can't be stated in full.** FCP-PL's `%` only accepts a constant divisor, and the linter expands `defs` inline, so cost grows exponentially with depth. In my tests a chain 15 levels deep took 13 s and one 20 levels deep hit lint's 120 s limit. Full exponentiation up to n = 65,535 is out of reach. A call outside the window, with no preceding call at n−1 and the same `p`, gets only "returns an int" and `result < p`. A wrong answer for modp(65535, 7) on its own would not be caught. The note on that item says so.
- **"2^n" in a Python docstring** is XOR in Python. Only the examples settle it as a power.
- **p = 0 is undefined** in the prompt. It could mean "anything goes", "must raise", or "return 2^n unreduced". I took "anything goes".
- **modp(0, 1):** reducing gives 0, but the example modp(0, 101) = 1 invites reading modp(0, p) = 1 for every `p`, which contradicts that.
- **"Be aware of numerics"** adds nothing you can observe beyond a correct answer and the call finishing.
- **`fcp explain` doesn't show ghosts,** so the model is documented only in the YAML header comment.

I also saved a short memory note about these FCP-PL limits for future formalization runs.