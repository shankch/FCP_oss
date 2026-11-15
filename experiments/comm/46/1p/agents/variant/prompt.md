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
- R-IF-1, "n: int": n is an index into the sequence, so only non-negative integers are valid arguments
- R-SEQ-1, "similar to the Fibbonacci sequnece": fib4(0) to fib4(3) are the starting values and every later element is the sum of the four elements before it, fib4(n) = fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4) for n >= 4 (as the name Fib4 suggests), giving 0, 0, 2, 0, 2, 4, 8, 14, 28, 54, 104, ...
- R-BASE-3, "fib4(2) -> 2": the Fibonacci rule of R-SEQ-1 applies from fib4(2) on (each element the sum of the two before it), so fib4(2) would be fib4(1) + fib4(0) = 0, which contradicts the listed value 2
- R-BASE-4, "fib4(3) -> 0": the Fibonacci rule of R-SEQ-1 applies from fib4(2) on (each element the sum of the two before it), so fib4(3) would be fib4(2) + fib4(1) = 2, which contradicts the listed value 0
- R-NTH-1, "n-th element": elements are counted from 1: the first element is the one written fib4(0), so fib4(n) returns the element written fib4(n-1) and fib4(0) has no element; this conflicts with the listed values read as calls (fib4(2) would return 0, not 2)
- R-NTH-1, "the fib4 number sequence": the sequence extends to every n through the Fibonacci-like rule of R-SEQ-1, so the n-th element exists and must be returned for every n
- R-NTH-1, "compute": fib4 may return any number equal to the element, so a float such as 2.0 also meets the requirement
- R-NF-2, "recursion": only fib4 itself must not call itself, directly or indirectly; a recursive helper function is allowed

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