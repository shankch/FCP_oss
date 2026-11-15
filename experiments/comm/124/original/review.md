# FCP review

Before any code: the request alone.

Settled: 11 requirements. Questions: 7.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RET-2: If the date string is not valid (as defined by R-VAL-1), valid_date returns False; it does not raise an exception or return any other value.
- R-EMP-1: If the date string is empty, valid_date returns False.
- R-DAY-1: If the month (the number in the mm field) is 1, 3, 5, 7, 8, 10 or 12 and the day (the number in the dd field) is less than 1 or greater than 31, valid_date returns False.
- R-DAY-2: If the month (the number in the mm field) is 4, 6, 9 or 11 and the day (the number in the dd field) is less than 1 or greater than 30, valid_date returns False.
- R-MON-1: If the month (the number in the mm field) is less than 1 or greater than 12, valid_date returns False.
- R-FMT-1: If the date string does not consist of three fields separated by exactly two '-' characters (for example if it uses '/' as the separator), valid_date returns False.
- R-EX-1: valid_date('03-11-2000') returns True.
- R-EX-2: valid_date('15-01-2012') returns False (month 15 is out of range).
- R-EX-3: valid_date('04-0-2040') returns False (day 0 is out of range).
- R-EX-4: valid_date('06-04-2020') returns True.
- R-EX-5: valid_date('06/04/2020') returns False (the separator is '/' instead of '-').

## Questions
1. **depends** (R-RET-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `valid_date("00002-00000001-3") -> False`
2. **ambiguity** (R-DAY-3): "higher than 29 for the month 2" can mean: February allows days 1 to 29 in every year, so '02-29-2001' is valid. / February allows day 29 only in a leap year (days 1 to 28 otherwise), so '02-29-2001' is invalid and '02-29-2000' is valid.. Which is meant?
3. **ambiguity** (R-FMT-2): "mm" can mean: The month field must be exactly two ASCII digits, so '3-11-2000' is invalid. / The month field may be any text that parses as an integer (one digit, three digits, leading '+' or spaces), so '3-11-2000' is valid.. Which is meant?
4. **ambiguity** (R-FMT-3): "dd" can mean: The day field must be exactly two ASCII digits, so '03-5-2000' is invalid (the example '04-0-2040' is invalid under either reading because its day is 0). / The day field may be any text that parses as an integer, so '03-5-2000' is valid.. Which is meant?
5. **ambiguity** (R-FMT-4): "yyyy" can mean: The year field must be exactly four ASCII digits, so '03-11-20' and '03-11-20000' are invalid. / The year field may be any text that parses as an integer, so '03-11-20' is valid.. Which is meant?
6. **ambiguity** (R-FMT-4): "yyyy" can mean: Any four-digit year is accepted, including '0000'. / The year must be at least 1, so '01-01-0000' is invalid.. Which is meant?
7. **ambiguity** (R-FMT-5): "The date should be in the format: mm-dd-yyyy" can mean: The whole string must match mm-dd-yyyy, so ' 03-11-2000' or '03-11-2000 ' is invalid. / Leading and trailing whitespace is ignored, so ' 03-11-2000 ' is valid.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-VAL-1, "The date is valid if all of the following rules are satisfied": both took "The four rules are necessary and sufficient: a string that satisfies all of them is valid, whatever else is true of it (for example '02-29-2001' and '01-01-0000' are valid)."
- R-DAY-3, "higher than 29 for the month 2": both took "February allows days 1 to 29 in every year, so '02-29-2001' is valid."
- R-FMT-2, "mm": both took "The month field must be exactly two ASCII digits, so '3-11-2000' is invalid."
- R-FMT-3, "dd": both took "The day field must be exactly two ASCII digits, so '03-5-2000' is invalid (the example '04-0-2040' is invalid under either reading because its day is 0)."
- R-FMT-4, "yyyy": both took "The year field must be exactly four ASCII digits, so '03-11-20' and '03-11-20000' are invalid."
- R-FMT-5, "The date should be in the format: mm-dd-yyyy": both took "The whole string must match mm-dd-yyyy, so ' 03-11-2000' or '03-11-2000 ' is invalid."

## Limits of this review
These searches stopped at their time budget. What they found stands; what lies beyond the budget was not searched:
- request points of agent_b
