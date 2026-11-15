I wrote `formal/agent_a.yaml`. `fcp lint` reports clean, and I read the `fcp explain` output back item by item: each one means what I intended.

**Items: 15**, plus the frame rule F-ZERO, which is added to every set.
- **10 properties.** RA-RET-1/2 say a valid date returns True and anything else returns False. RA-RET-3 says every call returns a bool and never raises. RA-EMP-1, RA-DAY-1/2/3, RA-MON-1 and RA-FMT-1/2 each say that breaking one rule returns False. They are all direct relations between `date`, `outcome` and `valid`, built from shared defs (`fmt`, `month`, `day`, `date_ok`, …), with no ghost state.
- **5 scenarios** (RA-EX-1…5), one per docstring example, each stated as written.
- **22 decisions**, one for every flagged phrase. All take reading 1: the most literal one, which is rules-authoritative for the rule requirements and example-authoritative for the example requirements.

**Requirements left unformalized: 5**
- **R-IF-1** (function name and number of arguments): this is set by the adapter's `function` section, not by anything in the trace.
- **R-IN-1** ("date is a string"): already guaranteed by the interface. Calls with anything that isn't a string of up to 16 characters aren't part of the trace, so there's nothing left to assume.
- **R-VAL-1** and **R-FMT-3**: these are definitions. They're realized as the defs `date_ok`, `month` and `day`, and linked by `covered_by` to the properties that use them.
- **R-FR-1**: this is the frame rule F-ZERO, so it's linked by `covered_by: [F-ZERO]`.

**Problems in the specification**
1. **Every example contradicts the rules.** Each of the five expected values is the opposite of what the four rules give. '03-11-2000' and '06-04-2020' meet every rule but are listed as False. '15-01-2012' (month 15), '04-0-2040' (one-digit day) and '06/04/2020' ('/' separators) each break a rule but are listed as True. That looks like a uniform flip of the expected values. I left the contradiction in place: none of the five scenarios can happen under the rule properties, so FCP should report each one with a minimal set of conflicting items. I couldn't confirm that myself because `fcp check` isn't available to agents.
2. **Parsing of "not less than 1 or higher than N".** I read it as 1 ≤ x ≤ N. The other parse, "(not less than 1) or (higher than N)", would make the upper bound do nothing.
3. **Things the spec doesn't say,** each resolved literally and recorded in a note:
   - Field widths are exactly two, two and four digits. So '04-0-2040' fails the format before its day 0 is ever checked.
   - Leading or trailing whitespace is not stripped.
   - '0000' counts as a year.
   - February 29 is accepted in every year; there is no leap-year rule.
   - Malformed strings return False rather than raise an exception.

One defensive change: I couldn't confirm whether defs are substituted as text or as parsed expressions. Running Python for a probe needed approval, so I dropped the probe. Instead I wrapped every multi-term def in parentheses, so `!date_ok`, `shape && !dashes` and the other uses mean the same under either kind of substitution.