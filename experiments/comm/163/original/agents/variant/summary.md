I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what each item is meant to say. I didn't run `fcp check`, so I haven't verified whether the set is consistent.

**Items: 7 formal items**, using no ghost state, plus 5 requirements under `unformalized` and 11 `decisions`. Every decision takes reading 2, as you instructed, and each affected note says the reading was imposed.
- **RV-ENV-1** (assumption): `a >= 0 && b >= 0`. Because the inputs are 8-bit, this rules out no call. Its effect is that calls with 0 must follow the rules too.
- **RV-OUT-1**: `outcome == 0 || outcome == 2`. Under the imposed reading the digits may come back in another form (strings, tuple, generator), and the trace records any of those as outcome 2 without their contents. So the item only forbids exceptions and hangs. I didn't take the stricter sense "must not be a list of int" (`outcome == 2` only): it would make every rule about the list's contents uncheckable. The note says this.
- **RV-OUT-2**: every element is 2, 4, 6 or 8 and lies strictly between min(a, b) and max(a, b).
- **RV-OUT-3**: when the call returns a list (outcome 0), every such digit appears in it. It's limited to outcome 0 because of RV-OUT-1.
- **RV-OUT-4**: the list never decreases, so repeats like [4, 4, 6] are allowed.
- **RV-IF-2-SOUND / RV-IF-2-COMPLETE**: the name reading. With outcome 0, the list is exactly the even integers of any size strictly between the arguments. "Between" is read the same way as in R-OUT-2 and R-OUT-3.

**Unformalized:**
- **R-IF-1**: a non-functional requirement (the deliverable is code), not a property of any call.
- **R-EX-1, R-EX-2, R-EX-3**: under the imposed reading the examples are illustrative only and the docstring statement prevails, so they add no constraint of their own. They are marked `covered_by` the R-OUT and R-IF-2 items.
- **R-FR-1**: already the frame rule F-EMPTY, which is added to every set.

**Problems in the specification (under these readings):**
- **Examples contradict the statement.** With the ends excluded, (2, 8) and (8, 2) give [4, 6], not [2, 4, 6, 8]. The reason given for R-EX-2's reading talks about "from a up to b", but under the "between" reading this set takes, the clash is about the ends instead. It's still a clash.
- **The name reading clashes with the docstring.** For calls like (10, 14), R-IF-2's "even integers of any size" asks for [12], while "even digits" allows only [] or digits. Together they rule out any list answer for such calls, which forces outcome 2. A full-range call like (0, 255) also can't fit in a 10-element list.
- **Several things go unchecked.** Answers in "another form" (outcome 2) are invisible in the trace, so under RV-OUT-1 even returning `None` passes every item. The positivity assumption excludes nothing. The non-decreasing reading allows duplicates that the prompt probably doesn't intend.