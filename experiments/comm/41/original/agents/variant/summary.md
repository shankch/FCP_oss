I wrote `formal/variant.yaml`. Lint reports no errors, and the `fcp explain` output says what I intended. Under the readings you gave, nothing in the spec constrains the function's outputs, so the set has no properties of its own. Only the adapter's built-in frame rule F-ZERO checks anything.

**Items: 2 formal items, 10 requirements unformalized**
- **RV-OUT-1-VAL** (R-OUT-1): `collisions` is unconstrained whenever `outcome == 0`. When `outcome` is not 0, F-ZERO already forces `collisions` to 0.
- **RV-OUT-1-END** (R-OUT-1): `outcome` is always unconstrained. Under "outputs = prints", the text never says what the function returns. A version that prints and returns None (outcome 2) isn't ruled out. I didn't change this to "returns the count".
- All 9 flagged phrases are recorded under `decisions`, each as reading 2.

**Unformalized requirements**
- **R-TASK-1:** non-functional ("complete this function"). It doesn't require the call to return anything.
- **R-SIG-1:** the name and single argument are already fixed by the `function` section of `design.yaml`.
- **R-CARS-1:** `n` is a 10-bit unsigned input, so "n is non-negative" would be an assumption that's always true.
- **R-ROAD-1, R-CARS-2, R-CARS-3, R-CARS-4, R-COL-1, R-COL-2:** these describe the cars and road. They only affect the collision count, which under the "prints" reading goes to standard output, and the interface doesn't record that. The readings also leave the count open (0 if the sets move apart, are infinitely far apart, or meetings don't count). Either way, nothing about the interface signals follows.
- **R-FR-1:** this is F-ZERO, which is added to every set automatically.

**Notes problem:** the schema doesn't allow a `note` field on `unformalized` entries; I tried and it was rejected. So for the six car-and-road requirements, the instructed readings (and that they were taken as instructed rather than chosen) are written in each entry's `reason`. Both dont_care items carry full notes covering every reading that affects them.

**Problems in the specification**
- **R-COL-1 and R-COL-2 conflict:** "said to collide" versus "as if they did not collide" leaves it open whether a meeting counts as a collision at all. I reported this rather than resolving it.
- **"outputs" can mean print or return.** Under "print", the returned value, which is all the checker sees, is unspecified. Code written to either reading would pass this set.
- **"very far from each other"** doesn't say which set is on which side, and "very far" can be read as infinitely far. Either way the expected n² count stops being implied.
- **"the same speed"** doesn't say the speed is constant. On these readings it doesn't change the count, because cars going the same way still never meet.