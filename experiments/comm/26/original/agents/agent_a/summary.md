I wrote `formal/agent_a.yaml`. `fcp lint` reports clean, and the `fcp explain` rendering matches what I meant for every item.

**Items: 7 formal items** (6 properties and 1 scenario), plus 8 helper definitions and 7 recorded decisions.
- **RA-SIG-2:** `outcome == 0` at every call, so the function always returns a list and never raises.
- **RA-RM-1:** no value that occurs more than once in `numbers` is in `result`.
- **RA-RM-2:** every value that occurs exactly once in `numbers` is in `result`.
- **RA-RM-3:** no value occurs in `result` more often than it does in `numbers`.
- **RA-ORD-1:** `result` is a subsequence of `numbers`, i.e. the kept elements stay in their original relative order.
- **RA-EX-1 and RA-EX-1-S:** the docstring example, as both a guarantee and a scenario (see the last problem below).

The helper definitions (`matched1`..`matched8`) do the subsequence test for RA-ORD-1. They walk through the 8 slots of `numbers`, matching `result` from left to right, and need no ghost state. I wanted to brute-force them against a reference subsequence check in Python, but running it needed approval that wasn't given, so that check wasn't run. I'm relying on this being the standard exact test.

The properties about the result only apply when the call returns (outcome 0). Returning at all is required only by RA-SIG-2, so a reviewer who reads the return type differently disagrees only on that one item.

**Requirements left unformalized (4):**
- **R-TASK-1:** it describes the deliverable ("complete this function"), not anything visible in a call.
- **R-SIG-1:** it defines the interface, which `design.yaml` already fixes. I took reading 1: the name is just a label and the docstring defines the behaviour.
- **R-IN-1:** it is true by construction, since `numbers` is always a list of integers 0–255 in the trace. An assumption would say nothing.
- **R-FR-1:** `covered_by: [F-EMPTY]`, the frame rule that is added to every set.

**Problems in the specification:**
1. **The name contradicts the docstring.** `remove_duplicates` suggests keeping one copy of each value, giving `[1, 2, 3, 4]` for the example. The docstring ("remove all elements that occur more than once") and the doctest's `[1, 3, 4]` say to drop every copy. I followed the docstring and the example throughout and noted the conflict on each affected item.
2. **It's unclear whether the function may raise.** The return type `-> List[int]` only describes the returned value. I took it as an obligation (reading 1), and said in the note that this goes beyond what the annotation literally states.
3. **"Keep order of elements left" is only clear under the docstring reading.** Under the keep-one-copy reading it doesn't say whether a value's first or last occurrence sets its position. My subsequence property doesn't depend on which elements are kept.
4. **The example is classified as a scenario, but the doctest says the call *returns* `[1, 3, 4]`.** A scenario only requires that output to be possible. So I stated it both as a guarantee for that input and as the scenario. If the guarantee goes too far, drop RA-EX-1.
5. **"From a list, remove" could mean editing the list in place.** That can't be seen in the trace, so both readings give the same formula. I recorded reading 1 (a new list is returned).