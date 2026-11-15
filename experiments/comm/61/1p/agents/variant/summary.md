I've written `formal/variant.yaml`. `fcp lint` reports it clean and the `fcp explain` output matches what each item is meant to say. The set is deliberately inconsistent: two of the readings you specified contradict the spec's example, and I kept that conflict rather than repairing it.

**Items: 7 formal items, plus the frame rule F-ZERO, which design.yaml adds to every set**
- **RV-IN-1** (assumption, R-IN-1): the argument is non-empty (`len(brackets) > 0`). Your two R-IN-1 readings combine this way: since characters other than `(` and `)` are ignored, they are allowed rather than ruled out. That leaves non-emptiness as the caller's only obligation.
- **RV-RET-1a** (R-RET-1, "False" read as truthiness): a call on a valid argument returns some value and doesn't raise (`outcome != 1`).
- **RV-RET-1b** (R-RET-1, "correct" read as a verb): a call on a valid argument returns a string that isn't a bool (`outcome == 2`).
- **RV-EX-1** (property) and **RV-EX-1-S** (scenario), both R-EX-1: `"("` returns the bool False. I didn't apply the truthiness reading here, because the example's answer is a bool and a doctest printing False isn't satisfied by 0.
- **RV-RES-1 / RV-RES-2** (dont_cares, R-RES-1 / R-RES-2): `result` is free on every valid argument except `"("`. One covers correctly bracketed arguments, the other the rest. "Correctly bracketed" uses your R-DEF-1 readings: equal counts in any order, and at least one bracket.

Every reading taken is reading 2, recorded under `decisions`. Each affected item's note says the reading was taken because you asked for it, not because it is the most natural one.

**Not formalized**
- **R-TASK-1**: a statement about the deliverable, not about call behaviour. Under your reading, the name and parameter are already fixed by design.yaml.
- **R-IF-1**: the function's name and parameter are set by the `function` section of design.yaml; that isn't a property of the trace.
- **R-DEF-1**: a definition, captured as the def `correct` and listed as covered by RV-RES-1 and RV-RES-2. Because the R-RES readings leave every answer except the example's free, this definition doesn't change any guarantee.
- **R-FR-1**: covered by the frame rule F-ZERO, so not restated.

**Problems in the specification and the readings**
1. **Contradiction:** RV-RET-1b requires a string for every non-empty argument, while RV-EX-1 requires False for `"("`. No implementation can satisfy both, and RV-EX-1-S can never be reached. Both readings state this contradiction themselves; FCP's consistency check should report it.
2. **R-EX-1 reading 1 doesn't apply here:** that reading puts `"("` outside the contract only if R-IN-1 means "contains both `(` and `)`". This set uses the non-empty reading of R-IN-1 instead, so `"("` is inside the contract and the conflict that reading describes doesn't come up.
3. **Unobservable parts:** the interface can't show the content of a non-bool return. That means the truthiness requirement and the "corrected string" content can't be checked.
4. **Thin spec:** the prompt never says what the function returns. Under your readings its behaviour is pinned down only at `"("`, so R-DEF-1 and the "ignore other characters" reading have no effect on any guarantee.