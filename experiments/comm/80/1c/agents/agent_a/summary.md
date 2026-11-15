The sandbox won't let me copy the bundle into the scratchpad, and that runtime check was optional (the task only asks for lint and explain), so I'm skipping it rather than running `fcp code` against the real workspace, where it might write files. Wrapping up.

## Summary

I wrote `formal/agent_a.yaml` with **10 items**. `fcp lint` reports no errors, and I checked the `fcp explain` output item by item: each one means what I intended.

- **Properties (4):**
  - `RA-OUT-1`: every call returns a bool (`outcome == 0`).
  - `RA-HAP-1`: at least 3 characters and every overlapping 3-character window pairwise distinct → returns True.
  - `RA-HAP-2`: fewer than 3 characters → returns False.
  - `RA-HAP-3`: some window repeats a character → returns False.
- **Scenarios (6):** `RA-EX-1` to `RA-EX-6`, one per example, each exactly as written (e.g. `is_happy('a')` returns True).
- **Decisions:** all 27 flagged phrases are recorded, every one with reading 1. That means characters count as "letters", length is `len(s)`, windows overlap, "distinct" means different character codes, and the definition's "if" means "if and only if". Each statement, definition or example, is taken as written.
- **No ghost state.** Four macros (`defs`) describe the windows and the two return values.

**Left unformalized (3):**
- `R-API-1`: the function name and its single parameter are fixed by the adapter. There is nothing to state about the calls themselves.
- `R-IN-1`: with reading 1 ("any string"), the interface already guarantees this. Calls with an argument that isn't a string never reach the trace, so no assumption is needed.
- `R-FR-1`: this is frame rule F-ZERO, which is added to every set automatically (`fcp explain` lists it).

**Not checked:** I didn't run a test implementation through `fcp code`. In particular, I haven't confirmed how the window checks behave on strings shorter than 2 characters, where the loop bound goes negative. Lint accepts it, and the docs define the quantifier over the range 0 to n−1, which is empty in that case.

**Problems in the specification:**
1. **Every example contradicts the definition, and the set reflects that on purpose.**

   | Example | Spec says | Definition gives | Clashing items |
   |---|---|---|---|
   | `a`, `aa` | True | False: shorter than 3 | `RA-HAP-2`, `RA-EX-1/2` |
   | `abcd`, `adb` | False | True: windows all distinct | `RA-HAP-1`, `RA-EX-3/5` |
   | `aabb`, `xyy` | True | False: a window repeats a character | `RA-HAP-3`, `RA-EX-4/6` |

   All six examples are exactly the opposite of the definition, which suggests the expected outputs were flipped. I didn't fix this. Each item's `note` names the item it clashes with, so FCP's consistency check should report six minimal conflicts. No implementation can meet both the definition and the examples.
2. The definition says "letters" while the input is any string. It doesn't say what happens with characters that aren't letters, or whether upper and lower case count as different.
3. "is happy if" is literally only a sufficient condition. The False cases (`R-HAP-2/3`) only follow if it is read as "if and only if", which is the usual meaning in a definition.
4. Minor: the examples leave out the quotes around strings (`is_happy(a)`), and the definition sentence has no full stop.