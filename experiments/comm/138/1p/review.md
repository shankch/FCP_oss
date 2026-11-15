# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 7.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RET-1: For every given number n, the function terminates and returns normally: it does not raise an exception and does not run forever.

## Questions
1. **depends** (R-SUM-1, R-SUM-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `is_equal_to_sum_even(0) -> False`
2. **ambiguity** (R-RET-2): "Evaluate whether" can mean: Return the bool True or False. / Return any truthy or falsy value (for example 1 or 0) that encodes the answer.. Which is meant?
3. **ambiguity** (R-SUM-1): "the sum of exactly 4" can mean: exactly 4 positive even numbers: True exactly when n is even and n >= 8 (the kind suggested by the function name is_equal_to_sum_even). / exactly 4 non-negative even numbers (zero allowed): True exactly when n is even and n >= 0. / exactly 4 even integers (negative values allowed): True exactly when n is even. / exactly 4 positive integers (no parity constraint): True exactly when n >= 4. / exactly 4 non-negative integers or any integers (no constraint on the summands): True for every n >= 0.. Which is meant?
4. **ambiguity** (R-SUM-1): "exactly 4" can mean: four summands, the same value may be used more than once (for example 8 = 2 + 2 + 2 + 2). / four pairwise distinct summands (for positive even summands, True only when n is even and n >= 20 = 2 + 4 + 6 + 8).. Which is meant?
5. **ambiguity** (R-SUM-1, R-SUM-2): "is_equal_to_sum_even" can mean: The function name supplies the missing kind of summand: the 4 summands are even numbers. / The function name adds nothing; the kind of summand is not stated by the request.. Which is meant?
6. **ambiguity** (R-SUM-2): "the sum of exactly 4" can mean: exactly 4 positive even numbers: False exactly when n is odd or n < 8 (the kind suggested by the function name is_equal_to_sum_even). / exactly 4 non-negative even numbers (zero allowed): False exactly when n is odd or n < 0. / exactly 4 even integers (negative values allowed): False exactly when n is odd. / exactly 4 positive integers (no parity constraint): False exactly when n < 4. / exactly 4 non-negative integers or any integers (no constraint on the summands): never False for n >= 0.. Which is meant?
7. **ambiguity** (R-SUM-2): "exactly 4" can mean: four summands, the same value may be used more than once (for example 8 = 2 + 2 + 2 + 2). / four pairwise distinct summands (for positive even summands, False whenever n < 20 = 2 + 4 + 6 + 8).. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IF-2, "is_equal_to_sum_even": both took "The name constrains the summands: they are even numbers (the name supplies the word that the truncated docstring leaves out)."
- R-DOM-1, "the given number n": both took "n is any number, non-integer (float) values included."
- R-RET-2, "Evaluate whether": both took "Return the bool True or False."
- R-SUM-1, "the sum of exactly 4": both took "exactly 4 even integers (negative values allowed): True exactly when n is even."
- R-SUM-1, "exactly 4": both took "four summands, the same value may be used more than once (for example 8 = 2 + 2 + 2 + 2)."
- R-SUM-1, "is_equal_to_sum_even": both took "The function name supplies the missing kind of summand: the 4 summands are even numbers."
- R-SUM-2, "the sum of exactly 4": both took "exactly 4 even integers (negative values allowed): False exactly when n is odd."
- R-SUM-2, "exactly 4": both took "four summands, the same value may be used more than once (for example 8 = 2 + 2 + 2 + 2)."
- R-SUM-2, "is_equal_to_sum_even": both took "The function name supplies the missing kind of summand: the 4 summands are even numbers."
