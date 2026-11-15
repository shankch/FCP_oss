I split the prompt into 11 atomic requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run (`anchored 11 requirements`) and wrote `requirements.yaml` with the line numbers filled in.

**Requirements**
- **R-FN-1, R-FN-2** (non_functional): write the complete function `candidate`, which takes one parameter, `arr`.
- **R-IN-1** (assumption): `arr` is a list of integers.
- **R-CH-1** (guarantee, depends on R-DEF-1 and R-DEF-2): it returns how many elements need to change to make `arr` palindromic.
- **R-CH-2** (guarantee): it always returns one integer, with no exception and no other return type.
- **R-DEF-1, R-DEF-2** (definition): what "palindromic array" means, and what counts as one change.
- **R-EX-1..3** (scenario): the three docstring examples (4, 1, 0).
- **R-FR-1** (FRAME, guarantee): F-ZERO, which says `changes` is 0 unless `outcome` is 0. The ID matches the `req: R-FR-1` link in `design.yaml`.

**Ambiguities flagged**
- **What the count means (R-CH-1):** it could be the smallest number of changes (mirror pairs that differ), every element that differs from its mirror (twice as many), or any number of changes that works.
- **Contradiction:** if the count includes every element that differs from its mirror, it contradicts examples 1 and 2 (8 instead of 4, 2 instead of 1). I recorded this on R-CH-1 and on both R-EX-1 and R-EX-2. Under the "smallest number of changes" reading, all three examples agree.
- **Changing `arr` (R-CH-1):** the function might also turn `arr` into a palindrome in place, or only return the count.
- **Return or print (R-CH-2):** "find" could mean return the number or print it.
- **Empty array (R-IN-1):** the answer could be 0, or the empty list could be outside the spec.
- **Reading direction (R-DEF-1):** it could be element by element, or by the written-out digits (`[12, 21]` reads "1221").
- **What a change allows (R-DEF-2):** "any other element" could mean any value or only a value already in the array. It is also unclear whether a change must actually give the element a different value.