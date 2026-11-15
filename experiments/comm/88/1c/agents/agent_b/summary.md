I've written `formal/agent_b.yaml`. `fcp lint` reports "lint: clean", and the `fcp explain` output matches what each item is meant to say.

**Items: 9.** They are 1 assumption, 4 properties and 4 scenarios, all starting with `RB-`. Calls don't share state, so there's nothing for ghost state to track. Instead, a set of named expressions computed from each call's `array` acts as the model:
- `psum` and `sum_odd`/`sum_even` give the first-plus-last sum and its parity.
- `same_multiset` is the expected contents of the result.
- `ascending`/`descending` are the expected orders.

Every output is checked against these:
- **RB-RES-1:** `outcome == 0`, so every call returns a list.
- **RB-RES-2:** a returned list has the same length and the same elements, with the same counts, as the argument.
- **RB-ORD-1 / RB-ORD-2:** an odd sum gives a non-decreasing result and an even sum a non-increasing one. Empty arrays are left out of both rules.
- **RB-EX-1 to RB-EX-4:** the four docstring examples, each as a behaviour that must be possible.
- **RB-IN-1:** the "non-negative integers" assumption. The 0–255 list encoding already guarantees this, so it rules out no call; it's kept only to record the obligation.

I recorded a choice for all 14 flagged ambiguous phrases, taking the most literal reading (reading 1) for each.

**Requirements left unformalized:**
- **R-IF-1** (function name and parameter): this is an interface fact, already given by the `function` section of `design.yaml`, not something visible in the trace.
- **R-MUT-1** ("don't change the given array"): the trace has no signal for the argument after the call, so it can't be checked.
- **R-DEF-1** (definition of the sum): covered by the named expressions, which RB-ORD-1 and RB-ORD-2 use.
- **R-FR-1:** covered by the frame rule F-EMPTY, which every set includes automatically.

**Problems in the specification:**
1. **Both non-trivial examples contradict the sorting rule.** For `[2,4,3,0,1,5]`, 2+5=7 is odd, so the rule says ascending, but the example shows descending. For `[2,4,3,0,1,5,6]`, 2+6=8 is even, so the rule says descending, but the example shows ascending. Reading the sum as the indices (0+5, 0+6) gives the same parities, so no reading fixes it. I wrote both the rule and the examples exactly as stated, so this set contradicts itself on purpose: RB-EX-3 can't happen under RB-ORD-1, nor RB-EX-4 under RB-ORD-2. A consistency check should report those two pairs. A human needs to decide which side is wrong.
2. **The text disagrees with itself about changing the argument.** "You will sort the given array" and "sort it" read as sorting in place, which the note "don't change the given array" forbids. I took the note's side (sort a copy). The trace can't see either the argument after the call or whether a new list object is returned ("a copy"), so this choice doesn't change any formula.
3. **Small notes:** a one-element array counts its element twice, so its sum is always even. An empty array has no sum. Neither case affects the result, since such lists are in both orders anyway.