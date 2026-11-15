# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 12.

## Questions
1. **conflict** (R-EX-1, R-FN-2): no implementation can meet these requirements on these calls: which one gives way? (also with , at 2 places)
   - `candidate(4)`
2. **conflict** (R-EX-2, R-FN-2): no implementation can meet these requirements on these calls: which one gives way? (also with , at 2 places)
   - `candidate(6)`
3. **depends** (R-FN-1, R-FN-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate(62639) -> returned something else`
4. **ambiguity** (R-FN-1): "Evaluate whether" can mean: the function returns the bool True or False / the function returns any value that compares equal to True or False (e.g. 1 or 0), not necessarily of type bool. Which is meant?
5. **ambiguity** (R-FN-2): "4 numbers" can mean: any integers, negatives allowed: every n qualifies, so the result is always True / non-negative integers (zero allowed): every n >= 0 qualifies, so the result is always True / positive integers: True exactly when n >= 4 / positive even integers: True exactly when n is even and n >= 8 / integers of at least 2, or primes: True exactly when n >= 8 / distinct positive integers: True exactly when n >= 10 (1+2+3+4). Which is meant?
6. **ambiguity** (R-FN-2): "the sum of 4" can mean: exactly four summands / four or more summands. Which is meant?
7. **ambiguity** (R-FN-2): "can be written as" can mean: contradiction with the examples: read literally (any four integers, non-negative integers or positive integers), 4 = 1+1+1+1 and 6 = 1+1+2+2 qualify, so candidate(4) and candidate(6) would be True, against candidate(4) == False and candidate(6) == False / the statement is abbreviated and the examples fix the kind of number (e.g. four positive even numbers), so the examples take precedence / contradiction with the example candidate(8) == True if the summands must be distinct: the smallest sum of four distinct positive integers is 10. Which is meant?
8. **ambiguity** (R-EX-1): "candidate(4)" can mean: the example holds, so the main statement must be read narrowly (e.g. four positive even numbers, or four integers of at least 2), under which 4 does not qualify / contradiction: the main statement read literally (four positive or non-negative integers) makes 4 qualify (1+1+1+1 or 4+0+0+0), so candidate(4) would be True. Which is meant?
9. **ambiguity** (R-EX-1, R-EX-2): "== False" can mean: the call returns the bool False / the call returns any value equal to False (e.g. 0). Which is meant?
10. **ambiguity** (R-EX-2): "candidate(6)" can mean: the example holds, so the main statement must be read narrowly (e.g. four positive even numbers, or four integers of at least 2), under which 6 does not qualify / contradiction: the main statement read literally (four positive or non-negative integers) makes 6 qualify (1+1+2+2 or 6+0+0+0), so candidate(6) would be True. Which is meant?
11. **ambiguity** (R-EX-3): "candidate(8)" can mean: 8 qualifies because summands may repeat (2+2+2+2, 1+1+3+3) / contradiction: if the four numbers must be distinct positive integers, the smallest such sum is 10, so 8 would not qualify and candidate(8) would be False. Which is meant?
12. **ambiguity** (R-EX-3): "== True" can mean: the call returns the bool True / the call returns any value equal to True (e.g. 1). Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FN-1, "Evaluate whether": both took "the function returns the bool True or False"
- R-FN-2, "4 numbers": both took "any integers, negatives allowed: every n qualifies, so the result is always True"
- R-FN-2, "the sum of 4": both took "exactly four summands"
- R-FN-2, "can be written as": both took "contradiction with the examples: read literally (any four integers, non-negative integers or positive integers), 4 = 1+1+1+1 and 6 = 1+1+2+2 qualify, so candidate(4) and candidate(6) would be True, against candidate(4) == False and candidate(6) == False"
- R-EX-1, "candidate(4)": both took "contradiction: the main statement read literally (four positive or non-negative integers) makes 4 qualify (1+1+1+1 or 4+0+0+0), so candidate(4) would be True"
- R-EX-1, "== False": both took "the call returns the bool False"
- R-EX-2, "candidate(6)": both took "contradiction: the main statement read literally (four positive or non-negative integers) makes 6 qualify (1+1+2+2 or 6+0+0+0), so candidate(6) would be True"
- R-EX-2, "== False": both took "the call returns the bool False"
- R-EX-3, "candidate(8)": both took "8 qualifies because summands may repeat (2+2+2+2, 1+1+3+3)"
- R-EX-3, "== True": both took "the call returns the bool True"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `n >= 0 && n <= 65535`
- agent_b, RB-IN-1 (R-IN-1): every call meets `n >= 0 && n <= 65535`
