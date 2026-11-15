I wrote `formal/variant2.yaml`. `fcp lint` reports no errors, and I read the `fcp explain` output back: every item says what I meant it to. I couldn't run `fcp check` because it isn't available to agents, so I haven't machine-checked consistency or whether the example scenario can be reached.

**Items: 28** (2 assumptions, 25 properties, 1 scenario). No ghost state; everything is a direct relation, `once`/`hist`/`since`, or a standard pattern.
- **R-SIG-1:** an assumption that the arguments don't change during a run (the frame states this but has no rule for it).
- **R-API-1:** an assumption that `answer <= 2`.
- **R-ARGS-1:** 5 properties, one per service call, checking it uses this order's arguments.
- **R-ERR-1:** 1 property.
- **R-STEPS-1:** 3 properties: it returns only after a step fails or the booking answers ok, and the charge comes after the reserve and the booking after the charge.
- **R-ORDER-1:** 2 properties.
- **R-ONCE-1:** 3 properties.
- **R-RET-1:** 3 properties.
- **R-STOP-1:** 2 properties.
- **R-UNDO-1:** 5 properties: a refund and a release when due, at most once each, and the refund first.
- **R-LIMIT-1:** 1 property (`bounded_wait` on calls, max 4).
- **R-EX-1:** 1 scenario: reserve(3,2) ok, charge(7,500) refused, release(3,2), returns False, exactly three calls.

**Imposed readings.** Both are recorded under `decisions` as reading 2 and stated in every affected note:
- **Order:** the refund comes before the release.
- **"if the customer was charged ... if it was reserved":** read as "at least then", so a refund or release with nothing to undo is never forbidden.

**Unformalized:** only R-FR-1 to R-FR-4. They are the adapter's frame rules, which are already added to every set, so they are marked `covered_by` F-END, F-ZERO, F-LIMIT and F-ANS.

**Problems in the specification:**
1. **Rules 7 and 8 contradict each other.** If the booking is refused or raises, the run has already made 3 calls (reserve, charge, book). Rules 6 and 7 then require both a refund and a release, which makes 5 calls, but rule 8 allows at most 4. An answer script of ok, ok, refused/error therefore forces every implementation to break a rule. I formalized both rules as written and noted the conflict in V2-LIMIT.
2. **"Call nothing else in that case" (rule 5) is ambiguous but not flagged.** I took the literal reading: in an all-ok run, the only calls are the three steps. The requirement's own text says only "no call after the booking". The difference is a stray refund or release before the steps all succeed, which the imposed "at least then" reading otherwise leaves allowed.
3. **"Stock we do not hold" and "an order that is not paid" (rule 3)** literally mean a release or refund in between also counts. So my R-ORDER-1 items are slightly stronger than the requirement text, which says only "after the reservation/charge answered ok".
4. **The example doesn't match the imposed reading.** It shows no refund after a refused charge, which suggests the "only then" reading. It is still consistent with "at least then", so the scenario holds as written.
5. **"Take no later step" (rule 6)** is read as no step at all after a failure. This gives the same result as "no later step", because rule 4 already forbids repeating a step.