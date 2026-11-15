# FCP review

Before any code: the request alone.

Settled: 6 requirements. Questions: 14.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EMP-1: An empty date string is not valid: valid_date('') returns False.
- R-FMT-1: A valid date string consists of exactly three fields separated by hyphen characters '-'; a string that uses any other separator (such as '/') or has a different number of fields is not valid.
- R-EX-1: valid_date('03-11-2000') returns True.
- R-EX-3: valid_date('04-0-2040') returns False.
- R-EX-4: valid_date('06-04-2020') returns True.
- R-EX-5: valid_date('06/04/2020') returns False.

## Questions
1. **conflict** (R-EX-2): no implementation can meet these requirements on these calls: which one gives way?
   - `valid_date("15-01-2012")`
2. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **depends** (R-RET-1, R-RET-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `valid_date("\r\u0085\u00a0\u00851-9-4\u00a0\u0085\u0085 \f\f\r") -> False`
4. **ambiguity** (R-RET-2): "otherwise False" can mean: Every invalid string, including malformed ones (empty, wrong separators, non-digit characters, wrong field count), yields the return value False; the function never raises. / Only well-formed strings with an out-of-range day or month must yield False; for malformed strings the behaviour (e.g. raising ValueError) is not specified.. Which is meant?
5. **ambiguity** (R-DAY-1): "is not less than 1 or higher than 31 days" can mean: not (less than 1 or higher than 31): the day must lie in 1..31. / (not less than 1) or (higher than 31): taken literally as a logical formula, only day >= 1 is required, so no upper bound.. Which is meant?
6. **ambiguity** (R-DAY-2): "is not less than 1 or higher than 30 days" can mean: not (less than 1 or higher than 30): the day must lie in 1..30. / (not less than 1) or (higher than 30): taken literally as a logical formula, only day >= 1 is required, so no upper bound.. Which is meant?
7. **ambiguity** (R-DAY-3): "is not less than 1 or higher than 29" can mean: not (less than 1 or higher than 29): the day must lie in 1..29. / (not less than 1) or (higher than 29): taken literally as a logical formula, only day >= 1 is required, so no upper bound.. Which is meant?
8. **ambiguity** (R-DAY-3): "higher than 29 for the month 2" can mean: Day 29 of month 2 is accepted for every year, leap or not. / Day 29 of month 2 is accepted only when the year is a leap year (a real calendar check, since the function 'validates a given date').. Which is meant?
9. **ambiguity** (R-MON-1): "should not be less than 1 or higher than 12" can mean: should not be (less than 1 or higher than 12): the month must lie in 1..12. / (should not be less than 1) or (higher than 12): taken literally, only month >= 1 is required, so no upper bound.. Which is meant?
10. **ambiguity** (R-FMT-2): "dd-mm-yyyy or mm-dd-yyyy" can mean: dd and mm are exactly two digits each (leading zero required) and yyyy exactly four digits: the valid string has exactly 10 characters. / dd and mm are day and month numbers written with one or two digits (e.g. '4-1-2040' is acceptable), and yyyy is the year as digits.. Which is meant?
11. **ambiguity** (R-FMT-2): "The date should be in the format" can mean: Any character outside the format, including leading or trailing spaces, makes the string invalid. / Surrounding whitespace is ignored (the string is stripped) before the format is checked.. Which is meant?
12. **ambiguity** (R-FMT-2): "yyyy" can mean: Any four digits form an acceptable year, including '0000'. / The year must be a real year, at least 1 (so '0000' is invalid).. Which is meant?
13. **ambiguity** (R-FMT-3): "dd-mm-yyyy or mm-dd-yyyy" can mean: Either order is accepted: the string is valid if the day and month rules hold when it is read as dd-mm-yyyy or when it is read as mm-dd-yyyy (so '15-01-2012', 15 January, is valid; this CONTRADICTS the example valid_date('15-01-2012') => False, R-EX-2). / Only mm-dd-yyyy is accepted (the first field is the month), as the example valid_date('15-01-2012') => False requires; the dd-mm-yyyy alternative is an error in the prompt. / The implementation may choose one of the two orders and apply it consistently (which one is left open). / The string is valid only if the day and month rules hold under both orders (consistent with all examples, including '15-01-2012' => False).. Which is meant?
14. **ambiguity** (R-EX-2): "valid_date('15-01-2012') => False" can mean: The example is correct: only mm-dd-yyyy order counts, month 15 is out of range, so the result is False. This CONTRADICTS rule 4's acceptance of dd-mm-yyyy (R-FMT-3). / The example is wrong: rule 4 accepts dd-mm-yyyy, under which '15-01-2012' is 15 January 2012 and satisfies every rule, so the call should return True.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RET-2, "otherwise False": both took "Every invalid string, including malformed ones (empty, wrong separators, non-digit characters, wrong field count), yields the return value False; the function never raises."
- R-VAL-1, "The date is valid if all of the following rules are satisfied": both took "The four listed rules are the complete definition: a string that satisfies all of them is valid, with no further check (no leap-year check, no year-range check)."
- R-DAY-1, "is not less than 1 or higher than 31 days": both took "not (less than 1 or higher than 31): the day must lie in 1..31."
- R-DAY-2, "is not less than 1 or higher than 30 days": both took "not (less than 1 or higher than 30): the day must lie in 1..30."
- R-DAY-3, "is not less than 1 or higher than 29": both took "not (less than 1 or higher than 29): the day must lie in 1..29."
- R-DAY-3, "higher than 29 for the month 2": both took "Day 29 of month 2 is accepted for every year, leap or not."
- R-MON-1, "should not be less than 1 or higher than 12": both took "should not be (less than 1 or higher than 12): the month must lie in 1..12."
- R-FMT-2, "dd-mm-yyyy or mm-dd-yyyy": both took "dd and mm are exactly two digits each (leading zero required) and yyyy exactly four digits: the valid string has exactly 10 characters."
- R-FMT-2, "The date should be in the format": both took "Any character outside the format, including leading or trailing spaces, makes the string invalid."
- R-FMT-2, "yyyy": both took "Any four digits form an acceptable year, including '0000'."
- R-FMT-3, "dd-mm-yyyy or mm-dd-yyyy": both took "Either order is accepted: the string is valid if the day and month rules hold when it is read as dd-mm-yyyy or when it is read as mm-dd-yyyy (so '15-01-2012', 15 January, is valid; this CONTRADICTS the example valid_date('15-01-2012') => False, R-EX-2)."
- R-EX-2, "valid_date('15-01-2012') => False": both took "The example is correct: only mm-dd-yyyy order counts, month 15 is out of range, so the result is False. This CONTRADICTS rule 4's acceptance of dd-mm-yyyy (R-FMT-3)."

## Limits of this review
These searches stopped at their time budget. What they found stands; what lies beyond the budget was not searched:
- request points of agent_b
