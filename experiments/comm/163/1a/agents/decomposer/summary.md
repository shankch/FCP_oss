I split spec.md into 14 requirements in `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**The requirements**
- **R-IF-1** (non_functional): implement the Python function `generate_integers(a, b)`.
- **R-IN-1, R-IN-2** (assumption): `a` is a positive integer; `b` is a positive integer.
- **R-OUT-1** (guarantee): for valid arguments, the call returns a list rather than raising an error or returning another type.
- **R-SEL-1 to R-SEL-5** (guarantee): which values go in the list.
  - Every element is a digit from 0 to 9.
  - Every element lies between `a` and `b`.
  - All elements have the same parity.
  - Every qualifying digit is included.
  - No value is repeated.
- **R-ORD-1** (guarantee): the list is sorted in descending or ascending order.
- **R-EX-1, R-EX-2, R-EX-3** (scenario): the three examples, `(2, 8)`, `(8, 2)` and `(10, 14)`.
- **R-FR-1** (FRAME): the F-EMPTY rule, which design.yaml already cites as R-FR-1.

**Ambiguities flagged**
- **"positive integers"**: either calls with 0 never happen and the result for them doesn't matter, or the function must still handle 0 (for example, by listing 0 as an even digit).
- **"digits"**: either the numbers 0–9 in the range, the digits that appear in the numbers of the range, or any integers in the range. Only the first fits `(10, 14) => []`.
- **"between a and b"**: two separate questions.
  - Inclusive or exclusive: the `(2, 8)` example includes 2 and 8, so it supports inclusive.
  - Whether the order of `a` and `b` matters: the `(8, 2)` example returns a list, so it supports ignoring the order.
- **"odd or even"**: even only, odd only, all digits, one parity chosen by the implementer for every call, or a parity chosen per call.
- **"in descending or ascending order"**: always ascending, always descending, one order chosen by the implementer, an order that follows the arguments (descending when `a > b`), or descending for odd digits and ascending for even digits.

**Contradictions** (recorded on both sides)
- The general text allows odd digits and descending order, but both `(2, 8)` and `(8, 2)` return even digits in ascending order. I recorded this on R-SEL-3, R-ORD-1, R-EX-1 and R-EX-2. Each example is flagged as either binding or just one allowed answer.
- `(8, 2) => [2, 4, 6, 8]` rules out the reading where descending order applies when `a > b`.
- `(10, 14) => []` rules out the two other readings of "digits". I recorded this on R-EX-3 and R-SEL-1.