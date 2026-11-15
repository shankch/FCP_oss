I wrote `formal/agent_a.yaml`. It has 17 items: 12 properties and 5 scenarios, all derived from `spec.md`. `fcp lint` reports no errors, and I read back the `fcp explain` output: every item says what I meant. I also tried to run a Python cross-check of my definitions against a regex reference, but the run was not approved, so I checked the definitions by hand on the key cases instead ("1h30m", "24h", "007s", "0100s", "00s", "10h0s", "1h2h", "30m1h", "").

**Items**
- **Properties:** R-CONV-1, R-ERR-1, R-ERR-2, R-FMT-4, R-FMT-5, R-NUM-1, R-FMT-6, R-IF-2, R-EX-1, R-EX-2, and two for R-MAX-1 (a well-formed text over 86400 s raises ValueError; a normal return is never above 86400).
- **Scenarios:** "1h30m" returns 5400, "45s" returns 45, "24h" returns 86400, "1h99m99s" returns 9639 (both number bounds are inclusive and minutes/seconds have no clock limit), and "1h5s" returns 3605 (a unit can be skipped).
- **No ghost state.** Everything is stated directly on `text`, `outcome` and `seconds`, using a few definitions for a well-formed text, a zero part, a part above 99, and the total.

**Requirements left unformalized (6)**
- **R-NF-1 and R-IF-1:** "it's a Python function" and the function's name and signature are fixed by the function adapter, not by anything visible in a call's result.
- **R-FMT-1, R-FMT-2 and R-FMT-3:** these are definitions. They are covered by the definitions used in the R-CONV-1, R-ERR-1 and R-ERR-2 items, and the reason for each entry states the reading chosen.
- **R-FR-1:** this is frame rule F-ZERO, which is already part of every set.

**Problems in the specification**
1. **Rules 3 and 6 overlap.** Allowing 1–99 for every unit admits texts up to "99h99m99s" (362,439 s), but rule 6 says no duration is longer than one day. The text doesn't say whether "25h" returns 90000, raises ValueError, or is something callers simply never send. I took rule 6 as part of what a duration is ("A duration is…", like rule 1), so "25h" raises ValueError.
2. **R-CONV-1's requirement text contradicts R-MAX-1.** Its definition of a duration lists only rules 1–4, so read literally it requires "25h" to return 90000 while R-MAX-1 requires ValueError. My R-CONV-1 item includes rule 6 and its note says so.
3. **Rule 5 ("anything else") comes before rule 6.** I read it as covering rules 1–4 only. Combined with my R-MAX-1 item, every non-duration still raises ValueError.
4. **Several points are unspecified, so I took the most literal reading of each and noted it:**
   - Leading zeros are allowed ("01h" is 3600 s) and signs are not ("+1h" raises).
   - Units must be lowercase.
   - A unit in the middle can be skipped ("1h5s" is valid).
   - 1 and 99 are both allowed, and 60–99 minutes or seconds are fine.
   - "Spaces" means the space character only, with no trimming. Other whitespace is still rejected because it isn't a digit or a unit.
5. **R-IF-2 can't be stated exactly.** The `outcome` signal uses the same value for "returned something that isn't an int" and "returned an int out of range". I formalized it as "outcome is never 3", which is slightly stronger than the requirement on its own. Together with the other requirements it means the same thing.