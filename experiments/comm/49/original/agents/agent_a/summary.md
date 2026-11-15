I've written `formal/agent_a.yaml`. `fcp lint` reports no errors, and the `fcp explain` output reads back as intended for every item. I also wrote a small Python script to check the reference `pow(2, n, p)` against the base, step and range properties, but running it needed your approval, so I skipped it. I checked the examples against them by hand instead.

**What the set contains: 16 items**
- **9 properties:**
  - **R-RES-1 (four items):** for p ≥ 1 the call returns an int (`outcome == 0`) and `result < p`; for n = 0 the result is `p == 1 ? 0 : 1`; and when the previous call was modp(n-1, p), this result is twice the previous one, minus p if that reaches p.
  - FCP-PL has no power operator and `%` needs a constant divisor, so I couldn't write 2^n mod p directly. Instead the result is pinned down by induction on n, comparing each call with the previous one. This works because the function keeps no state and the checker picks the order of calls freely. It uses no ghost state.
  - **R-EX-1 to R-EX-5 (one each):** the doctest value for that exact call. The examples also agree with RES-1: 1101 ≡ 1 and 100 ≡ 0 modulo 100, and 2^100 ≡ 1 (mod 101).
- **5 scenarios:** one cover per doctest example. I stated each example both as a scenario and as a property, because a doctest asserts the value rather than just showing it is possible.
- **2 don't-cares (R-RES-2):** `outcome` and `result` are unconstrained when p = 0. The frame rule F-ZERO still applies.
- **6 decisions:** I took reading 1 for every flagged phrase: 2^n is a power, "modulo p" always reduces into 0..p-1, "Return" means a Python int, p = 0 is outside the contract, "be aware of numerics" means efficiency, and modp(0, 101) is a single data point.

**Left unformalized (4)**
- **R-TASK-1:** it describes the deliverable, not anything visible in the trace of calls.
- **R-SIG-1:** it defines the function name and parameters, which the adapter's interface binding already realizes.
- **R-NUM-1:** how the result is computed can't be seen in the trace. What can be seen (calls finish, and the result is exact) is covered by the four RES-1 properties.
- **R-FR-1:** this is the frame rule F-ZERO, which is added to every set automatically.

**Problems in the specification**
1. **p = 0 is undefined.** "2^n modulo p" has no meaning there, and the prompt says nothing about it. Python's own `2**n % 0` and `pow(2, n, 0)` raise exceptions, so implementations will differ.
2. **modp(0, 1) is ambiguous.** If you generalise the example modp(0, 101) = 1 to every p, you get modp(0, 1) = 1. That contradicts the reduced answer 2^0 mod 1 = 0. I took the reduced answer, 0.
3. **`2^n` is XOR in Python.** In the docstring of Python code it could be read as `2 ^ n`. Only the examples rule that out.
4. **"be aware of numerics" is vague.** It could mean speed, exactness or overflow. Only speed and exactness can be observed, and both are covered by RES-1.
5. **Negative n isn't addressed.** 2^-1 is not an integer. The frame keeps negative arguments out of the trace, so this doesn't affect the set.