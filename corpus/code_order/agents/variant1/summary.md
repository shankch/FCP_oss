Lint passes with no errors and the `fcp explain` output matches what I meant each item to say. Writing up the summary now.

I wrote `formal/variant1.yaml`. It contains **32 items**: 29 properties, 2 assumptions and 1 scenario, plus the two `decisions` (reading 1 for both flagged R-UNDO-1 phrases). The only lint message is an info note: V1-API-ANS depends on the outputs `op` and `phase`, so its receptiveness still has to be checked. It always allows `answer = 0`, so that check should pass. I did not run `fcp check`.

**What each requirement became**
- **R-SIG-1:** an assumption that the four arguments stay the same through a run. `frame.md` says this in its inputs table, but it isn't one of the frame rules. Without it the inputs could change mid-run and produce conflicts that aren't real.
- **R-API-1:** an assumption that reserve, charge and book only answer 0, 1 or 2. I also took "a call that raises has done nothing" to mean a charge or reservation only counts if it answered "ok".
- **R-UNDO-1:** read as you instructed, and the notes on all six items say so:
  - **Either order:** nothing requires the refund to come before the release, or the other way round.
  - **Only then:** no refund unless the charge answered "ok", and no release unless the reservation did. Because undoing is a response to a failure, both also require that a step has failed.
- **The rest:** stated directly in terms of the signals, using `once`, `since`, `hist`, `prev` and the `implies`/`next` patterns. I used no ghost state.

**Left unformalized:** only R-FR-1 to R-FR-4. They are the adapter's frame rules, which are already part of every set, so each is listed as covered by F-END, F-ZERO, F-LIMIT and F-ANS.

**Problems in the specification**
1. **Rule 8 contradicts rules 2, 6 and 7.** If the reservation and charge answer "ok" and the booking is refused or raises, the function must also refund and release. That is five calls, but rule 8 allows at most four. I kept both as written; the notes on V1-LIMIT-4 and the two undo items flag this. The consistency check should report it.
2. **Rule 2 can't apply to invalid arguments**, because rule 1 says to call no service then. I limited the "returns only after a failure or a successful booking" item to valid arguments, and said so in its note.
3. **Rule 3 is stronger than the requirement's wording.** "Stock we do not hold" and "an order that is not paid" literally mean: reserved and not released since, and charged and not refunded since. I used that reading. It is stricter than the requirement's "after the reservation answered ok", but makes no difference given the other rules.
4. **"False otherwise" isn't in the quoted rule 5.** It comes from the requirement's text and from rule 6. I formalized it as "returns True only when all three steps answered ok" and said where it comes from in the note.
5. **Minor points:**
   - "Goes on to the next step" is read as the very next call.
   - "Call nothing else" is read as no refund or release anywhere in a successful run.
   - Argument stability across a run is missing from the frame rules (see R-SIG-1 above).