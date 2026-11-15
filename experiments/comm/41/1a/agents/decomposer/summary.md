I wrote `requirements_draft.yaml` with 12 requirements, and `fcp anchor` accepted every quote on the first run ("anchored 12 requirements"). It wrote `requirements.yaml` with the line numbers filled in.

**The requirements**
- **Task and input:** R-IF-1 (non_functional) asks for the completed Python stub. R-ENV-1 (assumption) says `n` is a non-negative count of cars.
- **The road and the cars (definitions):**
  - R-RD-1: the road is an infinite straight line.
  - R-CAR-1 and R-CAR-2: how many cars drive in each direction.
  - R-POS-1: the two sets start far apart.
  - R-SPD-1: all cars have the same speed, so cars going the same way never meet.
  - R-COL-1: what counts as a collision.
  - R-COL-2: cars pass through each other unchanged.
- **What the function must do (guarantees):**
  - R-OUT-1: it returns a non-negative int without raising.
  - R-OUT-2: the result is the number of left-to-right cars times the number of right-to-left cars. It lists the definitions it relies on under `depends`.
- **Frame rule:** R-FR-1 (doc FRAME) is F-ZERO, and its ID matches the one `design.yaml` uses.
- **Scenarios:** none, because the request gives no examples.

**Flagged ambiguities and contradictions**
- **"2\*n or n cars" (R-CAR-1, R-CAR-2, R-OUT-2):** this is the main problem. The answer could be n², 4n² or 2n², or any of them if the count is the implementer's choice. "A different set" adds two more readings: the second set could have a different size from the first, or the same size.
- **Contradiction, car count vs. single answer:** the request says the function outputs one number, but the car count is given as two options. This is recorded on R-CAR-1, R-CAR-2 and R-OUT-2.
- **Contradiction, collide vs. "as if they did not collide":** one reading is that pass-throughs don't count as collisions, which would make the answer always 0. This is recorded on both R-COL-1 and R-COL-2.
- **"very far from each other" (R-POS-1):** it doesn't say which side each set starts on. If the sets start moving apart, there are no collisions at all.
- **"outputs" (R-OUT-1):** it could mean return or print.
- **"n: int" (R-ENV-1):** it's unclear whether negative `n` must be handled.