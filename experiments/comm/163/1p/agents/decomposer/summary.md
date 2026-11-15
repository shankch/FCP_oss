I split the prompt into 10 requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run ("anchored 10 requirements") and wrote `requirements.yaml`.

The prompt is cut off mid-sentence. All it says is "Given two positive integers a and b, return the even digits between", and it has no examples, so there are no scenario requirements.

**Requirements**
- **R-IF-1, R-IF-2** (non_functional): write the body of the Python stub, and keep the function named `generate_integers` with two parameters, `a` then `b`.
- **R-IN-1** (assumption): `a` and `b` are positive integers.
- **R-RET-1** (guarantee): when the inputs are valid, the function finishes without an exception and returns a list.
- **R-RET-2** (guarantee): every element is an even digit (0, 2, 4, 6 or 8).
- **R-RET-3** (guarantee): every element lies between `a` and `b`. I read the missing words after "between" as "a and b".
- **R-RET-4** (guarantee): every even digit between `a` and `b` appears in the list.
- **R-RET-5** (guarantee): no value appears twice.
- **R-RET-6** (dont_care): the prompt doesn't say what order the list is in.
- **R-FR-1** (FRAME, from F-EMPTY): `result` is empty unless `outcome` is 0.

**Ambiguities flagged**
- **"positive":** either at least 1, so calls with 0 are left unconstrained, or loosely non-negative, so 0 must be handled. The checked inputs run from 0 to 127, so this choice matters.
- **"a and b":** either order is allowed, or `a <= b` is assumed. For the range, either it runs from min to max, or it runs from `a` up to `b` and is empty when `a > b`.
- **"between":** whether `a` and `b` themselves count (inclusive) or only the values strictly between them (exclusive).
- **"even digits":** this has three readings:
  - the single digits 0–8 that fall inside the range;
  - all even numbers in the range, of any size;
  - the even digits that appear when the numbers in the range are written out.
- **"return":** a Python list, or any kind of collection.
- **Duplicates:** each value once, or one entry for each time it occurs.
- **Order:** any order, ascending, or running from `a` towards `b`.

**Contradiction:** the function's name, `generate_integers`, points to integers of any size, but the docstring asks for "even digits". I recorded this as an ambiguity on both R-IF-2 and R-RET-2, and listed it again in the "even digits" readings on R-RET-4.