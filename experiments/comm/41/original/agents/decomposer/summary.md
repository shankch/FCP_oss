I wrote `requirements_draft.yaml` and ran `fcp anchor` on it. All 11 quotes matched the source text on the first run, and the result is in `requirements.yaml`.

**The requirements** (10 from the spec, 1 from the frame):
- **R-TASK-1** (non-functional): write the body of the function.
- **R-SIG-1** (definition): the function is `car_race_collision`, with one integer argument `n`.
- **R-ROAD-1, R-CARS-1..4, R-COL-1, R-COL-2** (definitions): these describe the scene. The road is one straight, infinitely long line. There are two separate sets of `n` cars, one driving each way at the same time. The two sets start far apart. All cars move at the same speed. A collision is a left-to-right car hitting a right-to-left car, and cars carry on unaffected after a collision.
- **R-OUT-1** (guarantee): the function returns the total number of collisions. It lists the definitions above as what it depends on. Under the most likely reading, the answer is `n*n`.
- **R-FR-1** (frame rule F-ZERO, guarantee): `collisions` is 0 unless `outcome` is 0.

The spec gives no examples, so there are no scenario requirements.

**Ambiguities flagged:**
- **"start out being very far from each other" (R-CARS-3):** the spec never says the two sets are moving toward each other. If they aren't, the answer could be 0 rather than `n*n`. "Very far" could also mean infinitely far, in which case they never meet. This is the one that matters most.
- **"outputs" (R-OUT-1):** could mean return the number or print it.
- **"the number of such collisions" (R-OUT-1):** the count depends on how R-CARS-3 and R-COL-1 are read: `n*n`, 0, or `n`.
- **"collide" (R-COL-1):** unclear whether a pair of cars can be counted more than once.
- **"simultaneously" (R-CARS-2) and "the same speed" (R-CARS-4):** minor. Neither changes the count.
- **Apparent contradiction:** R-COL-1 says the two cars "collide" when one "hits" the other, but R-COL-2 says they continue "as if they did not collide". I recorded this on both requirements: either every meeting counts as a collision, or a meeting with no effect isn't a collision at all.