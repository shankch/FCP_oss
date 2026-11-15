# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 11.

## Questions
1. **conflict** (R-EX-1, R-SUM-2): no implementation can meet these requirements on these calls: which one gives way? (also with , at 2 places)
   - `is_equal_to_sum_even(4)`
2. **conflict** (R-EX-2, R-SUM-2): no implementation can meet these requirements on these calls: which one gives way? (also with , at 2 places)
   - `is_equal_to_sum_even(6)`
3. **conflict** (R-EX-3, R-SUM-1): no implementation can meet these requirements on these calls: which one gives way? (also with , at 2 places)
   - `is_equal_to_sum_even(8)`
4. **depends** (R-EX-3, R-SUM-1, R-SUM-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `is_equal_to_sum_even(8) -> True`
5. **ambiguity** (R-RET-1): "Evaluate whether" can mean: the function must return a Python bool, True or False / any value that compares equal to True or False (such as 1 or 0) is acceptable, since the examples only check `== True` / `== False`. Which is meant?
6. **ambiguity** (R-SUM-1, R-SUM-2): "exactly 4 positive even numbers" can mean: the four summands may repeat (e.g. 2+2+2+2), so the representable n are exactly the even n >= 8 / the four summands must be distinct, so the representable n are exactly the even n >= 20. Which is meant?
7. **ambiguity** (R-SUM-1): "can be written as the sum of exactly 4 positive even numbers" can mean: the description is authoritative: 8 = 2+2+2+2 is representable, so is_equal_to_sum_even(8) returns True, which contradicts the example is_equal_to_sum_even(8) == False (R-EX-3) / the examples are authoritative and the description is inverted: the function returns True exactly when n can NOT be written as such a sum, so is_equal_to_sum_even(8) returns False. Which is meant?
8. **ambiguity** (R-SUM-2): "can be written as the sum of exactly 4 positive even numbers" can mean: the description is authoritative: 4 and 6 are below the minimum sum 2+2+2+2 = 8, so is_equal_to_sum_even(4) and is_equal_to_sum_even(6) return False, which contradicts the examples is_equal_to_sum_even(4) == True (R-EX-1) and is_equal_to_sum_even(6) == True (R-EX-2) / the examples are authoritative and the description is inverted: the function returns True exactly when n can NOT be written as such a sum, so is_equal_to_sum_even(4) and is_equal_to_sum_even(6) return True. Which is meant?
9. **ambiguity** (R-EX-1): "is_equal_to_sum_even(4) == True" can mean: the example is authoritative: is_equal_to_sum_even(4) returns True, although 4 is less than the minimum sum of 4 positive even numbers (2+2+2+2 = 8), contradicting R-SUM-2 / the description is authoritative: 4 is not a sum of 4 positive even numbers, so is_equal_to_sum_even(4) returns False and this example is wrong. Which is meant?
10. **ambiguity** (R-EX-2): "is_equal_to_sum_even(6) == True" can mean: the example is authoritative: is_equal_to_sum_even(6) returns True, although 6 is less than the minimum sum of 4 positive even numbers (2+2+2+2 = 8), contradicting R-SUM-2 / the description is authoritative: 6 is not a sum of 4 positive even numbers, so is_equal_to_sum_even(6) returns False and this example is wrong. Which is meant?
11. **ambiguity** (R-EX-3): "is_equal_to_sum_even(8) == False" can mean: the example is authoritative: is_equal_to_sum_even(8) returns False, although 8 = 2+2+2+2 is a sum of 4 positive even numbers, contradicting R-SUM-1 (consistent with R-SUM-1 only under the distinct-summands reading) / the description is authoritative: 8 = 2+2+2+2, so is_equal_to_sum_even(8) returns True and this example is wrong. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RET-1, "Evaluate whether": both took "the function must return a Python bool, True or False"
- R-SUM-1, "exactly 4 positive even numbers": both took "the four summands may repeat (e.g. 2+2+2+2), so the representable n are exactly the even n >= 8"
- R-SUM-1, "can be written as the sum of exactly 4 positive even numbers": both took "the description is authoritative: 8 = 2+2+2+2 is representable, so is_equal_to_sum_even(8) returns True, which contradicts the example is_equal_to_sum_even(8) == False (R-EX-3)"
- R-SUM-2, "exactly 4 positive even numbers": both took "the four summands may repeat (e.g. 2+2+2+2), so the representable n are exactly the even n >= 8"
- R-SUM-2, "can be written as the sum of exactly 4 positive even numbers": both took "the description is authoritative: 4 and 6 are below the minimum sum 2+2+2+2 = 8, so is_equal_to_sum_even(4) and is_equal_to_sum_even(6) return False, which contradicts the examples is_equal_to_sum_even(4) == True (R-EX-1) and is_equal_to_sum_even(6) == True (R-EX-2)"
- R-EX-1, "is_equal_to_sum_even(4) == True": both took "the example is authoritative: is_equal_to_sum_even(4) returns True, although 4 is less than the minimum sum of 4 positive even numbers (2+2+2+2 = 8), contradicting R-SUM-2"
- R-EX-2, "is_equal_to_sum_even(6) == True": both took "the example is authoritative: is_equal_to_sum_even(6) returns True, although 6 is less than the minimum sum of 4 positive even numbers (2+2+2+2 = 8), contradicting R-SUM-2"
- R-EX-3, "is_equal_to_sum_even(8) == False": both took "the example is authoritative: is_equal_to_sum_even(8) returns False, although 8 = 2+2+2+2 is a sum of 4 positive even numbers, contradicting R-SUM-1 (consistent with R-SUM-1 only under the distinct-summands reading)"
