# FCP review

Certified: 5 requirements. Questions: 13.

## Certified (the code meets them under both readings, which agree; no conflict)
- R-IF-2: Whenever parse_duration returns normally, the returned value is an int (not a float, a str, None or any other type).
- R-FMT-4: parse_duration raises ValueError for a text in which the same unit letter (h, m or s) ends more than one part, such as "1h2h" or "5s5s".
- R-ERR-2: parse_duration("") raises ValueError.
- R-EX-1: parse_duration("1h30m") returns 5400.
- R-EX-2: "45s" is a duration: parse_duration("45s") returns 45.

## Questions
1. **code** (R-CONV-1): the code breaks this requirement here (replayed): a bug, or a reading to change?
   - `parse_duration("002h") -> raised ValueError`
2. **ambiguity** (R-CONV-1): "a duration" can mean: any text that meets rules 1 to 4 of the request is a duration and is converted, including one longer than one day: "25h" returns 90000 (this contradicts R-MAX-1) / a text is a duration only if it meets rules 1 to 4 and is also at most one day (86400 seconds) long; a longer text such as "25h" is not converted (it raises ValueError or is out of scope, see R-MAX-1). Which is meant?
3. **ambiguity** (R-FMT-5): "in the order h, m, s" can mean: the units present keep the relative order h before m before s, and a unit may be skipped: "1h5s" is valid (3605 seconds) / the units present form a contiguous run of h, m, s with none skipped in between: "1h5s" raises ValueError. Which is meant?
4. **ambiguity** (R-NUM-1): "between 1 and 99" can mean: inclusive: 1 and 99 are allowed ("1s" and "99s" are valid) / exclusive: only 2 to 98 are allowed ("1s" and "99s" raise ValueError). Which is meant?
5. **ambiguity** (R-NUM-1): "Every number" can mean: the same range 1 to 99 applies to every unit: "90m" and "1h90m" are valid / minutes and seconds stay below 60 as on a clock, at least after a larger unit: "1h90m" or "1m75s" raises ValueError. Which is meant?
6. **ambiguity** (R-NUM-1): "Every number is between 1 and 99. / A duration is never longer than one day." can mean: contradiction with R-MAX-1: this rule admits up to 99 hours ("99h" is 356400 seconds, "99h99m99s" is 362439), while R-MAX-1 says no duration is longer than one day (86400 seconds); if every number from 1 to 99 is valid for every unit, "25h" must be converted to 90000 / no contradiction if R-MAX-1 is an extra restriction: numbers 1 to 99 are necessary but not sufficient, and "25h" or "24h1s" raises ValueError because it is longer than one day. Which is meant?
7. **ambiguity** (R-FMT-6): "Spaces" can mean: only the space character (code 32) is meant; other whitespace such as tab or newline is rejected only because it is not part of the duration syntax / every whitespace character (space, tab, newline, carriage return, ...) is meant / spaces are forbidden inside the duration, but surrounding whitespace may be trimmed first, so "45s " returns 45. Which is meant?
8. **ambiguity** (R-ERR-1): "anything else" can mean: anything that does not meet rules 1 to 4, which precede this rule; a text meeting them but longer than one day (rule 6, which follows) is not covered by this rule / anything that does not meet rules 1 to 4 or rule 6; a text longer than one day, such as "25h", also raises ValueError. Which is meant?
9. **ambiguity** (R-MAX-1): "A duration is never longer than one day." can mean: a validity rule: a text totalling more than 86400 seconds is not a duration, so parse_duration raises ValueError for it / an assumption about callers: the scheduling app never passes a text longer than one day, so the behaviour on such texts is left free (a dont_care) / a bound on the result only: parse_duration never returns more than 86400, for example by clamping "25h" to 86400 rather than raising. Which is meant?
10. **ambiguity** (R-MAX-1): "A duration is never longer than one day. / Every number is between 1 and 99." can mean: contradiction with R-NUM-1 and R-CONV-1: rules 1 to 4 admit up to 99 hours ("99h" is 356400 seconds, "99h99m99s" is 362439), and R-CONV-1 converts every such duration, yet this rule says no duration is longer than one day; "25h" cannot both return 90000 and be rejected / no contradiction if this rule is an extra restriction on top of rules 1 to 4: "25h" meets every number range but is still rejected for being longer than one day. Which is meant?
11. **ambiguity** (R-FMT-2): "a whole number" can mean: leading zeros are allowed and the number is the value of its digits: "01h" is 1 hour and "007s" is 7 seconds / leading zeros are not allowed: "01h" is not a part, so it raises ValueError / a number has at most two digits, leading zero allowed: "01h" is a part, "001h" is not. Which is meant?
12. **ambiguity** (R-FMT-2): "a whole number" can mean: only the decimal digits 0 to 9, with no sign: "+1h" raises ValueError / an optional sign may precede the digits, as Python int() accepts: "+1h" is 1 hour. Which is meant?
13. **ambiguity** (R-FMT-3): "`h` for hours, `m` for minutes, `s` for seconds" can mean: only the lowercase letters h, m and s are units: "1H30M" raises ValueError / units are case-insensitive: "1H30M" is the same duration as "1h30m". Which is meant?

## Outside this review
A review judges what calls return and do. The request also asks for these, which were marked non-functional when it was split into requirements. They are not certified, and nothing is said about them except where the report above names one:
- R-NF-1: The deliverable is a Python function, meant to be used by a scheduling application.
- R-IF-1: The function is named parse_duration and takes exactly one parameter, text, of type str.

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- request points of agent_a
- request points of agent_b
- request points of agent_b, agent_a
- request points of agent_a, agent_b
