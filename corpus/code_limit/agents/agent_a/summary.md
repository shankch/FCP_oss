I wrote `formal/agent_a.yaml`. `fcp lint` reports clean, and I checked every `fcp explain` rendering against what I meant.

**Items: 8.** Seven properties (LA-ERR-1/2, LA-RET-1/2, LA-MAX-1, LA-FAIR-1, LA-PEN-1) and one scenario (LA-EX-1). They use one rigid, the customer `c` (0 to 1,000), and five ghosts: the times of c's last three allowed attempts, the latest time among its older allowed attempts, and the time of its last denied attempt.
- **Why ghosts:** stating the windows with `prev`/`once` alone needs a second, time-valued rigid. That makes 65.6 million rigid cases, and `fcp code` refuses anything above 4,096. I confirmed this with a throwaway implementation I wrote myself, then deleted. The ghost version runs.
- **The cost:** while `now` never goes back, the three rate-limit items say exactly what rules 2, 4 and 5 say. Time can go back only after a call that raised. After that the items still require nothing the rules don't, but they can miss attempts older than the ones tracked. Each note says this.

**Unformalized: 4, each with `covered_by`.**
- R-SIG-1 and R-IN-1 are definitions; the RET and ERR items carry them.
- R-COUNT-1 only says what the counts in rules 2 and 4 range over; LA-MAX-1 and LA-FAIR-1 count allowed attempts only.
- R-FR-1 is the frame item F-ZERO.

**Readings chosen (most literal, each stated in its note)**
- "The previous call" is the call just before, by any customer, whether or not it raised.
- "In any 60 seconds" and "in the last 60 seconds" are closed windows: attempts 60 s apart are within 60 s. requirements.yaml doesn't flag the second phrase. I gave it the same convention, because mixing conventions would make rules 2 and 4 conflict or leave a gap.
- "The next 10 seconds" includes exactly 10 s later, and every denial restarts it, including one caused by the penalty.
- Rule 4 is read as fixing the value of a call that returns. Read literally it would also require allowing calls that rule 1 rejects.

**Problems in the specification.** Neither contradiction is repaired; FCP's spec-only conflict search finds both, and I traced each by hand.
1. **Rules 4 and 5 contradict.** Take attempts at 2, 2, 3 (allowed), 61 (denied by rule 2), then 63. Rule 4 says allow, since only one allowed attempt is in [3, 63]; rule 5 says deny. This holds under either reading of the penalty phrases.
2. **The literal rule 1 lets time go back across a raised call, and then rules 2 and 4 contradict.** Take allowed attempts at 32731, 32787 and 32787, then a call at 32728 that raises, then another at 32728, which is valid. Rule 4 says allow, rule 2 forbids. The other reading ("the previous call that did not raise") avoids this.

**Tool notes**
- Any expression containing `prev`, even nested inside `once`, is skipped on the object's first call. So R-RET-1 needs a separate `after_reset` item (LA-RET-1) for the first call.
- Determinacy reports `allowed` as open, but that is an artifact. The customer rigid is too large for the analysis to handle exactly (limit 64 cases), so it fixes c = 0 while the witness's calls are by user 976.
