# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 30.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EMP-1: If the date string is empty (length 0), valid_date(date) returns False.

## Questions
1. **scenario** (R-EX-1): the behaviour RA-EX-1 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
2. **scenario** (R-EX-2): the behaviour RA-EX-2 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **scenario** (R-EX-3): the behaviour RA-EX-3 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
4. **scenario** (R-EX-4): the behaviour RA-EX-4 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
5. **scenario** (R-EX-5): the behaviour RA-EX-5 describes can never happen under agent_a: the reading's own rules forbid it. Is the example, or the rule, what is meant?
6. **scenario** (R-EX-1): the behaviour RB-EX-1 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
7. **scenario** (R-EX-2): the behaviour RB-EX-2 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
8. **scenario** (R-EX-3): the behaviour RB-EX-3 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
9. **scenario** (R-EX-4): the behaviour RB-EX-4 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
10. **scenario** (R-EX-5): the behaviour RB-EX-5 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
11. **depends** (R-FMT-2, R-RET-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `valid_date("06-06-0000") -> True`
12. **ambiguity** (R-RET-1): "returns True if the date is valid" can mean: Contradiction with R-EX-1 and R-EX-4, rules authoritative: '03-11-2000' and '06-04-2020' meet every listed rule, so valid_date returns True for them and the examples' expected False is wrong. / Contradiction with R-EX-1 and R-EX-4, examples authoritative: valid_date returns False for '03-11-2000' and '06-04-2020', so a date meeting every rule does not always yield True (validity or the return polarity means something other than stated).. Which is meant?
13. **ambiguity** (R-RET-2): "otherwise False" can mean: Contradiction with R-EX-2, R-EX-3 and R-EX-5, rules authoritative: '15-01-2012' (month 15), '04-0-2040' (day 0, one-digit day) and '06/04/2020' ('/' separators) each break a rule, so valid_date returns False for them and the examples' expected True is wrong. / Contradiction with R-EX-2, R-EX-3 and R-EX-5, examples authoritative: valid_date returns True for '15-01-2012', '04-0-2040' and '06/04/2020' even though each breaks a listed rule.. Which is meant?
14. **ambiguity** (R-RET-3): "otherwise False" can mean: Every string that is not a valid date, including malformed ones such as '--', '1-2' or 'ab-cd-efgh', yields False and never an exception. / Only strings that look like dates are covered; for malformed strings (e.g. non-numeric fields) the function may raise an exception instead of returning False.. Which is meant?
15. **ambiguity** (R-DAY-1): "is not less than 1 or higher than 31" can mean: The day is neither less than 1 nor higher than 31, i.e. 1 <= day <= 31. / Literal operator scoping: the day is not less than 1, or it is higher than 31, i.e. only day >= 1 is required.. Which is meant?
16. **ambiguity** (R-DAY-2): "is not less than 1 or higher than 30" can mean: The day is neither less than 1 nor higher than 30, i.e. 1 <= day <= 30. / Literal operator scoping: the day is not less than 1, or it is higher than 30, i.e. only day >= 1 is required.. Which is meant?
17. **ambiguity** (R-DAY-2): "not less than 1" can mean: Contradiction with R-EX-3, rule authoritative: '04-0-2040' has month 4 and day 0, which is less than 1, so it is invalid and valid_date returns False. / Contradiction with R-EX-3, example authoritative: valid_date('04-0-2040') returns True, so day 0 in month 4 is accepted.. Which is meant?
18. **ambiguity** (R-DAY-3): "is not less than 1 or higher than 29" can mean: The day is neither less than 1 nor higher than 29, i.e. 1 <= day <= 29. / Literal operator scoping: the day is not less than 1, or it is higher than 29, i.e. only day >= 1 is required.. Which is meant?
19. **ambiguity** (R-DAY-3): "higher than 29 for the month 2" can mean: Day 29 of February is allowed in every year, as the rule states (e.g. '02-29-2001' is valid). / Day 29 of February is allowed only in leap years, since a real calendar date is meant (e.g. '02-29-2001' is invalid).. Which is meant?
20. **ambiguity** (R-MON-1): "should not be less than 1 or higher than 12" can mean: The month is neither less than 1 nor higher than 12, i.e. 1 <= month <= 12. / Literal operator scoping: the month is not less than 1, or it is higher than 12, i.e. only month >= 1 is required.. Which is meant?
21. **ambiguity** (R-MON-1): "higher than 12" can mean: Contradiction with R-EX-2, rule authoritative: '15-01-2012' has month 15, which is higher than 12, so it is invalid and valid_date returns False. / Contradiction with R-EX-2, example authoritative: valid_date('15-01-2012') returns True, so month 15 is accepted (or the first field is not the month).. Which is meant?
22. **ambiguity** (R-FMT-1): "mm-dd-yyyy" can mean: Contradiction with R-EX-5, rule authoritative: the separator must be '-', so '06/04/2020' is invalid and valid_date returns False. / Contradiction with R-EX-5, example authoritative: '/' (or any separator) is also accepted, so valid_date('06/04/2020') returns True.. Which is meant?
23. **ambiguity** (R-FMT-2): "mm-dd-yyyy" can mean: Exact field widths: mm and dd are exactly two digits and yyyy exactly four, so '04-0-2040' (one-digit day) is malformed and invalid; this contradicts R-EX-3. / mm and dd may have one or two digits (yyyy four), as R-EX-3 '04-0-2040' => True suggests; this contradicts the exact two-digit reading of the format.. Which is meant?
24. **ambiguity** (R-FMT-2): "in the format" can mean: The whole string must match mm-dd-yyyy; any leading or trailing characters, including whitespace, make it invalid. / Leading and trailing whitespace is ignored (stripped) before the format is checked.. Which is meant?
25. **ambiguity** (R-FMT-2): "yyyy" can mean: Any four digits form an acceptable year, including '0000'. / The year must be a real calendar year (e.g. at least 0001), so '0000' is invalid.. Which is meant?
26. **ambiguity** (R-EX-1): "valid_date('03-11-2000') => False" can mean: Example authoritative: the call returns False, contradicting R-VAL-1 and R-RET-1, since '03-11-2000' (month 3, day 11, format mm-dd-yyyy) satisfies every listed rule. / Rules authoritative: '03-11-2000' is valid and the call returns True; the example's expected value is wrong.. Which is meant?
27. **ambiguity** (R-EX-2): "valid_date('15-01-2012') => True" can mean: Example authoritative with month 15 accepted: the call returns True, contradicting R-MON-1 (month 15 is higher than 12) and R-RET-2. / Example authoritative with fields read as dd-mm-yyyy: '15-01-2012' is 15 January 2012 and valid, contradicting R-FMT-3 (first field is the month). / Rules authoritative: month 15 is out of range, so the call returns False; the example's expected value is wrong.. Which is meant?
28. **ambiguity** (R-EX-3): "valid_date('04-0-2040') => True" can mean: Example authoritative: the call returns True, contradicting R-DAY-2 (day 0 is less than 1 in month 4), R-FMT-2 (dd is a single digit) and R-RET-2. / Rules authoritative: '04-0-2040' has day 0 and a one-digit day field, so the call returns False; the example's expected value is wrong.. Which is meant?
29. **ambiguity** (R-EX-4): "valid_date('06-04-2020') => False" can mean: Example authoritative: the call returns False, contradicting R-VAL-1 and R-RET-1, since '06-04-2020' (month 6, day 4, format mm-dd-yyyy) satisfies every listed rule. / Rules authoritative: '06-04-2020' is valid and the call returns True; the example's expected value is wrong.. Which is meant?
30. **ambiguity** (R-EX-5): "valid_date('06/04/2020') => True" can mean: Example authoritative: the call returns True, contradicting R-FMT-1 (separators must be '-') and R-RET-2. / Rules authoritative: '06/04/2020' is not in the format mm-dd-yyyy, so the call returns False; the example's expected value is wrong.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RET-1, "returns True if the date is valid": both took "Contradiction with R-EX-1 and R-EX-4, rules authoritative: '03-11-2000' and '06-04-2020' meet every listed rule, so valid_date returns True for them and the examples' expected False is wrong."
- R-RET-2, "otherwise False": both took "Contradiction with R-EX-2, R-EX-3 and R-EX-5, rules authoritative: '15-01-2012' (month 15), '04-0-2040' (day 0, one-digit day) and '06/04/2020' ('/' separators) each break a rule, so valid_date returns False for them and the examples' expected True is wrong."
- R-RET-3, "otherwise False": both took "Every string that is not a valid date, including malformed ones such as '--', '1-2' or 'ab-cd-efgh', yields False and never an exception."
- R-VAL-1, "The date is valid if": both took "If and only if: a date string is valid exactly when every listed rule holds; breaking any rule makes it invalid."
- R-VAL-1, "all of the following rules are satisfied": both took "Contradiction with R-EX-1 and R-EX-4, rules authoritative: '03-11-2000' and '06-04-2020' satisfy every rule and are therefore valid."
- R-DAY-1, "is not less than 1 or higher than 31": both took "The day is neither less than 1 nor higher than 31, i.e. 1 <= day <= 31."
- R-DAY-2, "is not less than 1 or higher than 30": both took "The day is neither less than 1 nor higher than 30, i.e. 1 <= day <= 30."
- R-DAY-2, "not less than 1": both took "Contradiction with R-EX-3, rule authoritative: '04-0-2040' has month 4 and day 0, which is less than 1, so it is invalid and valid_date returns False."
- R-DAY-3, "is not less than 1 or higher than 29": both took "The day is neither less than 1 nor higher than 29, i.e. 1 <= day <= 29."
- R-DAY-3, "higher than 29 for the month 2": both took "Day 29 of February is allowed in every year, as the rule states (e.g. '02-29-2001' is valid)."
- R-MON-1, "should not be less than 1 or higher than 12": both took "The month is neither less than 1 nor higher than 12, i.e. 1 <= month <= 12."
- R-MON-1, "higher than 12": both took "Contradiction with R-EX-2, rule authoritative: '15-01-2012' has month 15, which is higher than 12, so it is invalid and valid_date returns False."
- R-FMT-1, "mm-dd-yyyy": both took "Contradiction with R-EX-5, rule authoritative: the separator must be '-', so '06/04/2020' is invalid and valid_date returns False."
- R-FMT-2, "mm-dd-yyyy": both took "Exact field widths: mm and dd are exactly two digits and yyyy exactly four, so '04-0-2040' (one-digit day) is malformed and invalid; this contradicts R-EX-3."
- R-FMT-2, "in the format": both took "The whole string must match mm-dd-yyyy; any leading or trailing characters, including whitespace, make it invalid."
- R-FMT-2, "yyyy": both took "Any four digits form an acceptable year, including '0000'."
- R-FMT-3, "mm-dd-yyyy": both took "Contradiction with R-EX-2, format authoritative: the first field is the month, so '15-01-2012' has month 15 and is invalid."
- R-EX-1, "valid_date('03-11-2000') => False": both took "Example authoritative: the call returns False, contradicting R-VAL-1 and R-RET-1, since '03-11-2000' (month 3, day 11, format mm-dd-yyyy) satisfies every listed rule."
- R-EX-2, "valid_date('15-01-2012') => True": both took "Example authoritative with month 15 accepted: the call returns True, contradicting R-MON-1 (month 15 is higher than 12) and R-RET-2."
- R-EX-3, "valid_date('04-0-2040') => True": both took "Example authoritative: the call returns True, contradicting R-DAY-2 (day 0 is less than 1 in month 4), R-FMT-2 (dd is a single digit) and R-RET-2."
- R-EX-4, "valid_date('06-04-2020') => False": both took "Example authoritative: the call returns False, contradicting R-VAL-1 and R-RET-1, since '06-04-2020' (month 6, day 4, format mm-dd-yyyy) satisfies every listed rule."
- R-EX-5, "valid_date('06/04/2020') => True": both took "Example authoritative: the call returns True, contradicting R-FMT-1 (separators must be '-') and R-RET-2."
