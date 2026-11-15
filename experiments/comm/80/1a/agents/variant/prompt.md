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
- R-IN-1, "a string s": a string of letters only (as 'substrings of letters' suggests): strings containing non-letters are outside the contract and their result is a don't care
- R-OUT-2, "check if the string is happy or not": any truthy or falsy value (such as 1/0, or a non-empty/empty object) is an acceptable answer
- R-HAP-1, "A string is happy if": 'if' gives only a sufficient condition: the sentence says nothing about strings shorter than 3 (only the examples a and aa say they are not happy)
- R-HAP-1, "its length": the number of letters of s (non-letter characters not counted)
- R-HAP-2, "A string is happy if": 'if' gives only a sufficient condition: the sentence says nothing about strings without distinct substrings (only the examples aabb and xyy say they are not happy)
- R-HAP-2, "substrings of letters are distinct": every substring of 3 consecutive characters consists of 3 pairwise different characters (s[i], s[i+1], s[i+2] all differ)
- R-HAP-2, "roughly": approximately: most substrings must be distinct and a small number of repeats is tolerated
- R-HAP-2, "roughly substrings of letters are distinct": contradiction resolved by the definition: under a tolerant reading of 'roughly' (or the reading that substrings differ from one another) xyy and aabb would be happy, so the examples is_happy(aabb) => False and is_happy(xyy) => False are overruled
- R-HAP-2, "letters": every character of s counts, whatever its kind
- R-HAP-2, "distinct": case-insensitive: 'A' and 'a' are the same letter
- R-HAP-3, "substrings of letters are distinct": every substring of 3 consecutive characters consists of 3 pairwise different characters (s[i], s[i+1], s[i+2] all differ)
- R-HAP-3, "roughly": approximately: most substrings must be distinct and a small number of repeats is tolerated
- R-HAP-3, "roughly substrings of letters are distinct": contradiction resolved by the definition: under a tolerant reading of 'roughly' (or the reading that substrings differ from one another) xyy and aabb would be happy, so the examples is_happy(aabb) => False and is_happy(xyy) => False are overruled
- R-HAP-3, "letters": every character of s counts, whatever its kind
- R-HAP-3, "distinct": case-insensitive: 'A' and 'a' are the same letter
- R-HAP-3, "its length": the number of letters of s (non-letter characters not counted)
- R-EX-1, "is_happy(a)": the argument is a variable named a whose value is not given
- R-EX-2, "is_happy(aa)": the argument is a variable named aa whose value is not given
- R-EX-3, "is_happy(abcd)": the argument is a variable named abcd whose value is not given
- R-EX-4, "is_happy(aabb)": the argument is a variable named aabb whose value is not given
- R-EX-4, "is_happy(aabb) => False": contradiction resolved by the definition: 'roughly ... distinct' tolerates a few repeats, or only requires substrings of a fixed length to differ from one another (aa, ab, bb are all different; aab, abb are different), so aabb would be happy and the example is overruled
- R-EX-5, "is_happy(adb)": the argument is a variable named adb whose value is not given
- R-EX-6, "is_happy(xyy)": the argument is a variable named xyy whose value is not given
- R-EX-6, "is_happy(xyy) => False": contradiction resolved by the definition: 'roughly ... distinct' tolerates a single repeat, or only requires substrings to differ from one another (xyy has a single substring of length 3), so xyy would be happy and the example is overruled

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