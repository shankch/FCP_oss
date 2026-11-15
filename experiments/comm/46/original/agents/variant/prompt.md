You are an independent formal-verification engineer acting as an FCP formalization agent.

Workspace: <work>/out/ws_variant
It contains spec.md (the specification), design.yaml (interface and parameters),
requirements.yaml (the atomic requirements to formalize, each with a verbatim
source quote) and docs/IR_spec.md (the FCP IR and the FCP-PL property language).
frame.md defines how calls of the code become cycles of the trace; read it
before formalizing.

Task: write <work>/out/ws_variant/formal/variant.yaml, a formalization set (FCP IR v0.1, `set: variant`)
for every requirement in requirements.yaml, derived from the specification text.

Both other readers of this request read the phrases below the same way. Read
each of them instead as given here, even where another reading seems more
natural, and say so in the note of every item it affects:
- R-IN-1, "n: int": n is a non-negative integer only, since it indexes a sequence that starts at fib4(0)
- R-IN-2, "the n-th element": values at negative n are determined by running the recurrence backward (fib4(-1) = -2, fib4(-2) = 4, ...), so they are not free
- R-DEF-1, "that's defined as follows": the rules that follow define the Fibonacci sequence the Fib4 sequence is similar to
- R-DEF-1, "similar to the Fibbonacci sequnece": Fibonacci conventions apply where the listed rules are silent (for example the indexing or the domain of n)
- R-BASE-3, "fib4(2) -> 2": apparent contradiction with the recurrence read for every n: fib4(2) would be fib4(1) + fib4(0) + fib4(-1) + fib4(-2) = 0 + 0 + 0 + 0 = 0 if terms before the start are 0, not 2
- R-BASE-4, "fib4(3) -> 0": apparent contradiction with the recurrence read for every n: fib4(3) would be fib4(2) + fib4(1) + fib4(0) + fib4(-1) = 2 + 0 + 0 + 0 = 2 if terms before the start are 0, not 0
- R-REC-1, "fib4(n)": the recurrence holds for every n, which seems to contradict the base values fib4(2) -> 2 and fib4(3) -> 0 (and defines values at negative n)
- R-FN-1, "the n-th element": counting from 1: the n-th element is the value the definition gives for index n-1 (this disagrees with the examples)
- R-FN-1, "compute": print the element (the doctest output would look the same)
- R-FN-1, "compute the n-th element": any value numerically equal to the element is acceptable, such as a float
- R-NF-1, "efficiently": linear time in n with constant memory (an iterative loop keeping the last four values)
- R-NF-2, "Do not use recursion.": fib4 must not call itself

Rules:
1. Read docs/IR_spec.md first. Use only the operators and patterns it defines.
2. Work only from the files in the workspace. There is no RTL and you must not
   look for one; do not read or list any file outside <work>/out/ws_variant.
3. Every requirement must appear as one or more formal items carrying `req: <id>`
   (properties for guarantees, assumptions for environment obligations,
   dont_cares for intentionally unconstrained outputs, scenarios for behaviours
   that must be possible), or under `unformalized` with a reason (use
   `covered_by` if other items realize it).
4. Formalize what the text says. Where it is ambiguous or contradictory, choose
   the most literal reading and say so in the item's `note`. Do not silently
   repair the specification.
5. Every item id starts with "RV-". Set `origin: {kind: agent, role: formalizer, id: variant}`.
6. Validate with `<fcp>/bin/fcp lint <work>/out/ws_variant` until it reports no errors, and read back the
   English rendering with `<fcp>/bin/fcp explain <work>/out/ws_variant --set variant` to check that every
   item means what you intend.
7. Style: Prefer direct relations between interface signals and the standard patterns; introduce ghost state only where a requirement cannot be stated otherwise.
8. For every phrase that requirements.yaml flags under `ambiguity`, record the
   reading you took under `decisions`: `{req: <id>, phrase: <the phrase>,
   reading: <its number in the list, from 1>}`.

When done, reply with a short summary: number of items, requirements left
unformalized and why, and any problems you noticed in the specification.