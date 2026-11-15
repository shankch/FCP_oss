I wrote `requirements_draft.yaml` and ran `fcp anchor` on it. All 10 quotes were accepted as verbatim on the first run, and the output is in `requirements.yaml`. (I said 11 earlier; the correct count is 10.)

**Requirements**
- **R-SIG-1** (non_functional): write a complete implementation of `candidate` ("Complete this function:").
- **R-SIG-2** (definition): the signature takes two integers, `x` first and `y` second.
- **R-MOD-1** (guarantee): `candidate(x, y)` returns 2^x modulo y, as an integer in 0..y-1.
- **R-NUM-1** (non_functional): "be aware of numerics".
- **R-EX-1…5** (scenario): the five doctests: (3,5)→3, (1101,101)→2, (0,101)→1, (3,11)→8, (100,101)→1.
- **R-FR-1** (FRAME, from F-ZERO): `result` is 0 unless `outcome` is 0.

**Ambiguities flagged**
- **Names don't match:** the docstring talks about `n` and `p`, but the signature has `x` and `y`. I treated this as a contradiction and recorded it on both R-SIG-2 and R-MOD-1, with readings n=x, p=y and the reverse. All five examples fit only n=x, p=y.
- **`2^n`:** it could mean a power, or XOR, which is what `^` means in Python. The examples rule out XOR.
- **`modulo p`:**
  - **Remainder or congruent value:** it could mean the remainder in 0..p-1, or any value congruent to it. These differ at `candidate(0, 1)`, which gives 0 or 1.
  - **p = 0:** the prompt doesn't say what happens. Readings: any outcome is acceptable, the call must raise an exception, or it returns 2^n unreduced.
- **`p` may mean a prime:** every example uses a prime (5, 11, 101). So `p` could be any positive integer, or only primes, with non-prime `y` left outside the contract.
- **"Return":** the function has no return type, so a numerically equal float such as 3.0 might count. The doctests print `3`, not `3.0`, which points to an int.
- **"be aware of numerics":** it could require exact results (no floating point), or efficient modular exponentiation, or just be a hint to the implementer.

No two statements in the prompt contradict each other apart from the `n`/`p` versus `x`/`y` names.