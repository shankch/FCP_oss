I wrote `formal/agent_a.yaml`. `fcp lint` reports it clean, and the `fcp explain` output says what I intended.

**Items: 2 properties, both for R-OUT-1.** The frame rule F-ZERO is added to the set automatically.
- **RA-OUT-1:** `outcome == 0`. Every call returns an integer that fits. The largest count, 1023² = 1,046,529, fits in the 21-bit output.
- **RA-OUT-2:** `collisions == n * n`. Each of the n left-to-right cars meets each of the n right-to-left cars exactly once.

I added no assumptions, ghost state, scenarios or don't-cares, because the output is fully determined by the input.

**10 requirements left unformalized, each with a reason and `covered_by`:**
- **R-ROAD-1, R-CARS-1 to 4, R-COL-1, R-COL-2:** these only describe the physical setup and have no signal of their own. They matter only through the n² count, so they point to RA-OUT-2.
- **R-TASK-1** ("Complete this function") is an instruction about what to deliver. **R-SIG-1** (name and signature) is already handled by the interface in design.yaml. Both point to RA-OUT-1, since a missing body or wrong signature makes every call fail.
- **R-FR-1** is already the frame rule F-ZERO, which frame.md says need not be restated.

**Decisions:** I took reading 1 for all 9 flagged phrases. Each choice is explained in the reasons.

**Problems in the specification:**
1. **The cars are never said to approach each other.** The prompt only says the two sets "start out being very far from each other"; it never says which set is on the left. Read literally, they could be driving apart and never meet, which would make the answer 0. I assumed they approach because it's the only reading that gives a single answer and makes the talk of collisions meaningful. I flagged this as an inference in the note.
2. **The wording on collisions pulls both ways.** "Two cars are said to collide" sits awkwardly next to "as if they did not collide." I read the second phrase as describing only the cars' paths, so the meetings still count.
3. **"Outputs" is not "returns".** I read it as the return value. A function that prints the number and returns `None` would fail RA-OUT-1.
4. **Some things are never stated:**
   - the return type (I require an integer, so a float `4.0` fails);
   - that the speed is non-zero (only implied by "driving");
   - what happens for a negative `n` (the adapter keeps negative inputs out of the trace).