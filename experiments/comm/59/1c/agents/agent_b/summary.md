I've written `formal/agent_b.yaml`. `fcp lint` reports clean, and the `fcp explain` rendering says what I intended. I couldn't test the model by running it, though: `fcp check` is blocked for agents, so the number-theory model is checked by hand only.

**Items: 9** (plus the frame rule F-ZERO, which is added automatically)
- **2 assumptions:** RB-ENV-1 (`n > 1`) and RB-ENV-2 (n is not prime).
- **1 property:** RB-FN-1. Whenever n > 1 and n is not prime, the call returns an integer (outcome 0) equal to the largest prime factor of n.
- **2 scenarios:** RB-EX-1 (13195 returns 5) and RB-EX-2 (2048 returns 2).
- **4 don't-cares:** for n ≤ 1 and for prime n, any outcome and any returned value are accepted.

The model is computed from n alone, since the function keeps no state between calls:
- **Primality:** trial division by the 54 primes below 256.
- **`smooth`:** the part of n made of primes below 256. If `smooth < n`, n has exactly one prime factor above 255, and that factor is `n / smooth`.
- **Otherwise:** the answer is the largest prime below 256 that divides n.

The expressions are long because lint only accepts a literal (or an entry of a literal list) after `%`. A shorter version that tried every cofactor below 256 ran lint out of memory.

**Left unformalized (3)**
- **R-IF-1:** it asks for a finished implementation, which isn't something a call can show.
- **R-IF-2:** the function name and its one argument are already fixed by `design.yaml`.
- **R-FR-1:** marked `covered_by: [F-ZERO]`, the frame rule that is already part of every set.

**Readings recorded under `decisions`**
- R-FN-1 "the largest prime factor of n": reading 1, the words as written.
- R-ENV-1 "Assume n > 1": reading 1, a condition on the caller.
- R-ENV-2 "and is not a prime": reading 1, a condition on the caller.
- R-EX-1 "largest_prime_factor(13195) 5": reading 2, the example taken as written. I did not let it change the meaning of "largest".

**Problems in the specification**
1. **The first example contradicts the text.** 13195 = 5 × 7 × 13 × 29, so its largest prime factor is 29. The example says 5, which is the smallest. I kept both as written, so RB-EX-1 can never happen alongside RB-FN-1, and the conflict check should report the pair instead of me quietly fixing it. The 2048 example fits either reading.
2. **"Assume n > 1 and is not a prime" is unclear.** It could be a condition the caller must meet or rules the function must enforce. If it's enforcement, should n ≤ 1 raise an error, and should a prime n return n itself? I took the caller-condition reading.

**Things to watch**
- **Hand-typed constants:** about 200 primes and prime powers. I rechecked each one by hand, but no tool has executed the model.
- **Lint inconsistency:** lint accepts `n % primes[j]` but rejects `n % d` when `d` is a quantifier variable. The model depends on that being treated as a constant divisor after expansion.
- **Assumption semantics:** if one call that breaks an assumption turns off checking for the rest of the trace, a call with n = 0 early in the sweep would leave every later call unchecked. RB-FN-1 repeats the precondition in its trigger so each call is judged on its own. Whether that actually avoids the problem depends on the engine, which I couldn't confirm.