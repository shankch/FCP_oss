I split the request into 11 requirements in `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml` with line numbers filled in.

**What's in it**
- **The function itself (2):** R-FN-1 says the job is to complete the function. R-FN-2 is the signature `is_prime(n: int)`.
- **The car model (7, all definitions):**
  - the road is a straight line that goes on forever (R-ROAD-1)
  - n cars drive left to right (R-CAR-1), and a separate set of n cars drives right to left at the same time (R-CAR-2)
  - the two sets start very far apart (R-CAR-3)
  - all cars move at the same speed (R-CAR-4)
  - a collision means a left-to-right car meets a right-to-left car (R-COL-1)
  - cars pass through each other without changing course (R-COL-2)
- **The result (1):** R-OUT-1 says the function outputs the number of collisions.
- **Frame rule (1):** R-FR-1 (F-ZERO): `collisions` is 0 unless `outcome` is 0. This is the only frame rule, and it matches `req: R-FR-1` in `design.yaml`.
- The request contains no examples, so there are no scenarios.

**Ambiguities flagged**
- **Contradiction:** the function is named `is_prime`, which suggests a prime-number test returning a bool. The docstring says it outputs the number of collisions. I recorded this on both R-FN-2 and R-OUT-1, with one reading where the docstring wins and one where the name wins.
- **"outputs"** (R-OUT-1): the count could be returned or printed.
- **"the number of such collisions"** (R-OUT-1): it could count each pair of cars that meet (n·n under the usual reading) or count distinct collision events, where cars meeting at the same place and time count once.
- **"very far from each other"** (R-CAR-3): it could mean every left-to-right car starts to the left of every right-to-left car, so the sets approach and every pair meets. Or it could leave their order open, so they might be moving apart and never collide.