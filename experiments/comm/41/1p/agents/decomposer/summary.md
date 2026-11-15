I've written `requirements_draft.yaml` with 9 requirements, and `fcp anchor` accepted every quote on the first run ("anchored 9 requirements"), producing `requirements.yaml`.

**The main finding is that the request is cut off.** The docstring ends at "Two cars are said to collide", so it never says when two cars collide or what `candidate(n)` should return. Both gaps are flagged as ambiguities, and they will drive most of the disagreement between formalizations.

**Requirements:**
- **R-FN-1** (guarantee): "Complete this function:". Three readings for the return value:
  - the number of collisions;
  - not specified, so any value is acceptable;
  - also finish the docstring.
- **R-FN-2** (definition): the signature `candidate(n: int)`, with no return type declared.
- **R-RD-1** (definition): the road is a straight line of infinite length.
- **R-CAR-1** (definition): n cars drive left to right. Ambiguous whether n = 0 (no cars) is allowed.
- **R-CAR-2** (definition): at the same time, a separate set of n cars drives right to left. Ambiguous whether "simultaneously" means moving during the same period or starting at the same instant.
- **R-CAR-3** (assumption): the two sets start very far apart. Ambiguous whether this means every left-to-right car starts to the left of every right-to-left car, just a large gap with no ordering, or only that nothing has collided yet at the start.
- **R-CAR-4** (definition): all cars move at the same speed. Ambiguous whether that speed is constant over time or only equal at each moment.
- **R-COL-1** (definition): the unfinished collision sentence. Readings:
  - only cars going opposite ways collide;
  - any two cars at the same point collide;
  - collision is undefined.
  
  A second ambiguity covers what happens afterwards: the cars keep going, or they stop.
- **R-FR-1** (FRAME, guarantee): F-ZERO, i.e. `result` is 0 unless `outcome` is 0.

**Possible contradiction:** if "the same speed" in R-CAR-4 means the same velocity (speed and direction), it conflicts with the two sets driving in opposite directions (R-CAR-1 and R-CAR-2). I recorded it as an ambiguity on both R-CAR-4 and R-CAR-2. I found no other conflicting pairs.