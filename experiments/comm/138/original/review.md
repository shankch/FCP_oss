# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 8.

## Questions
1. **depends** (R-SUM-1, R-SUM-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `is_equal_to_sum_even(10) -> False`
2. **ambiguity** (R-OUT-1): "Evaluate whether" can mean: the function returns the bool True or False / the function may return any value that compares equal to True or False (such as 1 or 0), which the `== True` / `== False` examples would also accept. Which is meant?
3. **ambiguity** (R-OUT-1): "the given number n" can mean: every non-negative integer n must get an answer / every integer n, including negative ones, must get an answer (False for n <= 0) / n may be any number, including non-integers such as 8.0 or 7.5, and must get an answer. Which is meant?
4. **ambiguity** (R-EX-1): "is_equal_to_sum_even(4) == False" can mean: consistent with R-DEF-1 when 'positive' excludes zero: the least sum of four positive even numbers is 8, so 4 gives False / contradicts R-DEF-1 / R-SUM-1 when 'positive' includes zero: 4 = 4 + 0 + 0 + 0 would make the answer True. Which is meant?
5. **ambiguity** (R-EX-1, R-EX-2): "== False" can mean: the call returns the bool False / the call returns any value equal to False, such as 0. Which is meant?
6. **ambiguity** (R-EX-2): "is_equal_to_sum_even(6) == False" can mean: consistent with R-DEF-1 when 'positive' excludes zero: the least sum of four positive even numbers is 8, so 6 gives False / contradicts R-DEF-1 / R-SUM-1 when 'positive' includes zero: 6 = 2 + 2 + 2 + 0 would make the answer True. Which is meant?
7. **ambiguity** (R-EX-3): "is_equal_to_sum_even(8) == True" can mean: consistent with R-DEF-2 when the four terms may repeat: 8 = 2 + 2 + 2 + 2 / contradicts R-DEF-2 / R-SUM-2 when the four terms must be distinct: 8 is below the least distinct sum 20, so the answer would be False. Which is meant?
8. **ambiguity** (R-EX-3): "== True" can mean: the call returns the bool True / the call returns any value equal to True, such as 1. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-OUT-1, "Evaluate whether": both took "the function returns the bool True or False"
- R-DEF-1, "positive": both took "strictly greater than zero: 0 is not a positive even number (consistent with R-EX-1 and R-EX-2)"
- R-DEF-2, "exactly 4 positive even numbers": both took "four terms, not necessarily distinct (8 = 2 + 2 + 2 + 2 qualifies; consistent with R-EX-3)"
- R-EX-1, "is_equal_to_sum_even(4) == False": both took "consistent with R-DEF-1 when 'positive' excludes zero: the least sum of four positive even numbers is 8, so 4 gives False"
- R-EX-1, "== False": both took "the call returns the bool False"
- R-EX-2, "is_equal_to_sum_even(6) == False": both took "consistent with R-DEF-1 when 'positive' excludes zero: the least sum of four positive even numbers is 8, so 6 gives False"
- R-EX-2, "== False": both took "the call returns the bool False"
- R-EX-3, "is_equal_to_sum_even(8) == True": both took "consistent with R-DEF-2 when the four terms may repeat: 8 = 2 + 2 + 2 + 2"
- R-EX-3, "== True": both took "the call returns the bool True"
