I wrote `formal/variant.yaml`, and `fcp lint` reports no errors. I read back the `fcp explain` output and every item says what I meant it to say. I tried to run a small Python check of the date-parsing definitions on the example strings, but it needed approval and didn't run. I worked the key strings through by hand instead.

**What's in the file:** 27 items: 22 properties and 5 scenarios, one scenario per example. All 22 ambiguous phrases are recorded under `decisions` with reading 2, the reading you gave. Every item affected by one of your readings says so in its note.

**Requirements left unformalized:**
- **R-IF-1:** the function name and single argument are fixed in `design.yaml`; they aren't something a call can show.
- **R-IN-1:** "the argument is a string" is true by construction, since non-string calls aren't part of the trace.
- **R-VAL-1:** it defines validity, which has no output of its own. It is covered by RV-RET-1a/1b and RV-RET-2a/2b.
- **R-FR-1:** covered by frame rule F-ZERO.

**Problems in the specification under these readings.** The readings contradict each other, and I left the contradictions in place rather than fixing them:
- **'03-11-2000' and '06-04-2020':** RV-RET-1b and RV-RET-2b say they return False; RV-EX-1 and RV-EX-4 say True. Scenarios RV-EX-1s and RV-EX-4s can't be reached.
- **'04-0-2040':** RV-RET-2a and RV-DAY-2b say True; RV-EX-3 says False. Read day-month-year (R-FMT-3), the string has month 0, so RV-MON-1a also forces False. The R-DAY-2 reading calls this string "day 0 in month 4", which only works if the month comes first.
- **'06/04/2020':** RV-FMT-1 and RV-RET-2a say True, and so does the general rule RV-RET-1a; RV-EX-5 says False.
- **R-VAL-1's two readings contradict each other.** "The rules are a sufficient condition" and "two dates that meet every rule are invalid" can't both hold. I applied the second only to those two strings.
- **R-RET-3's permission to raise has no effect.** It lets malformed strings raise an exception, but R-FMT-2 and R-EMP-1 still say "returns False" for them. I kept each requirement's own wording, so the full set still forbids raising.
- **The literal "not less than 1 or higher than N" readings drop every upper bound.** Strings like '99-99-9999' therefore meet all the rules, and RV-RET-1a requires them to return True.
- **The February 29 example is written month-first.** '02-29-2001' doesn't fit the day-first field order from R-FMT-3; in this set that date is '29-02-2001'.

**Judgement calls you may want to review:**
- **Separator:** I took "any separator" to mean any non-digit character.
- **"Looks like a date"** for R-RET-3 means the shape of the format, whatever the field values.
- **Month 4 has no lower day bound**, following "day 0 in month 4 is accepted".
- **Leap years** follow the usual calendar rule: divisible by 4, except century years unless divisible by 400.

Only '15-01-2012' gets the same answer from every requirement.