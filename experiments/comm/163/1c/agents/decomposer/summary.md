I wrote `requirements_draft.yaml` with 13 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**Requirements**
- **Function and inputs:** R-IF-1 is the function name and signature (non_functional). R-IN-1 assumes a and b are positive integers.
- **Guarantees:**
  - R-OUT-1: the call returns a list and doesn't raise.
  - R-RES-1: every returned number is even.
  - R-RES-2: every returned number is a digit.
  - R-RES-3: every returned number lies between a and b.
  - R-RES-4: every even digit between a and b is in the list.
  - R-SYM-1: swapping the arguments doesn't change the result.
  - R-ORD-1: the list is in ascending order.
- **Scenarios:** R-EX-1 `(2, 8) => [8]`, R-EX-2 `(8, 2) => [8]` and R-EX-3 `(10, 14) => [14]`.
- **Frame rule:** R-FR-1 is F-EMPTY, using the id `design.yaml` already refers to.

**Ambiguities flagged**
- **"positive":** whether 0 counts, i.e. a ≥ 1 or a ≥ 0. It matters because the checked inputs include 0.
- **"digits":** single digits 0–9, any even integers (the function is called `generate_integers`), or numbers written only with even digits.
- **"between a and b":** whether a and b themselves count. Separately, whether order matters, i.e. whether nothing lies "between" them when a > b.
- **"ascending order":** strictly increasing (no repeats) or allowing repeats.

**Contradictions (recorded on both requirements)**
The examples contradict the docstring under every reasonable reading:
- `(2, 8) => [8]` and `(8, 2) => [8]` conflict with R-RES-4. The even digits between 2 and 8 are [2, 4, 6, 8], or [4, 6] if the ends don't count.
- `(10, 14) => [14]` conflicts with R-RES-2, because 14 isn't a digit. If "digits" means integers, it conflicts with R-RES-4 instead, because 10 and 12 are missing.
- Reading "between" as excluding a and b would contradict all three examples, since each returns an endpoint.

The examples fit one rule: return only the largest even number between a and b. I listed that as the "examples govern" reading on R-RES-4.