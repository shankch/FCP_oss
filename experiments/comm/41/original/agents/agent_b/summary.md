I wrote `formal/agent_b.yaml`. `fcp lint` reports it clean, and the English from `fcp explain` matches what I meant for every item.

**Items: 5** (3 more counting the scenarios as items: 2 properties + 3 scenarios), plus 9 `decisions`, one for each flagged ambiguous phrase.
- **Model:** `defs` set `ltr_cars = n` and `rtl_cars = n`, and define `meetings = ltr_cars * rtl_cars` as the expected collision count. I didn't use ghost state: the adapter says calls are independent, so a register would carry over a value from some arbitrary earlier call.
- **RB-OUT-RET** (R-OUT-1): `outcome == 0`. Every call returns an integer that fits; the largest result, 1023² = 1,046,529, is within 21 bits.
- **RB-OUT-VAL** (R-OUT-1): `collisions == n*n`, checked against the model.
- **Scenarios** (R-OUT-1):
  - n=0 returns 0.
  - n=2 returns 4. This tells the per-pair count (n·n) apart from a per-car count (n).
  - n=1023 returns 1,046,529.

**Unformalized (10), each with `covered_by`:**
- **R-TASK-1** is non-functional. It's covered by the two output properties, because an incomplete function body fails them.
- **R-SIG-1** is the interface definition, which `design.yaml` already sets up. A wrong function name or signature makes the call raise, which RB-OUT-RET rejects.
- **The seven definitions** (R-ROAD-1, R-CARS-1 to 4, R-COL-1, R-COL-2) have no signals of their own. They're the premises of the `meetings` model, so they're covered by RB-OUT-VAL. R-CARS-1 says n is non-negative; the 10-bit unsigned input already guarantees that, so it needs no assumption.
- **R-FR-1** is covered by the frame item F-ZERO, which the frame document says is added to every set and need not be restated.

**Problems in the specification:**
1. **Which side each set starts on (R-CARS-3).** The text only says the sets "start out being very far from each other". It never says the left-to-right cars start on the left. If they started on the right, the sets would drive apart and the answer would be 0. I took reading 1 (they approach, so the answer is n·n), based on "start out" implying the gap closes and on the prompt asking for a count at all. This is the main real ambiguity, and it's recorded in RB-OUT-VAL's note.
2. **Collide vs. "as if they did not collide" (R-COL-1 / R-COL-2).** These look contradictory. I took the explicit definition: every meeting counts, and the cars carry on unaffected.
3. **"Outputs" (R-OUT-1).** This could mean printing rather than returning. I read it as the return value; under the print reading the function would return None, which fails RB-OUT-RET.
4. **No effect on the answer.** The readings of "simultaneously", "same speed" and "collide" (once per pair vs. once per meeting) don't change it: on a straight line with one shared speed, each opposite-direction pair meets exactly once.