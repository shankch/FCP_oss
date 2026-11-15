I wrote `formal/agent_a.yaml` with 12 items covering 7 of the 12 requirements. `fcp lint` reports clean, and I read back `fcp explain`: every item says what I intended.

**Items**
- **Properties (8):**
  - `RA-RET-1`: every call returns normally (`outcome == 0`).
  - `RA-RET-2`: when the call returns, the result has the same length as `array` and holds each value the same number of times.
  - `RA-ORD-1` and `RA-ORD-2`: if the array is non-empty, the result is non-decreasing when `array[0] + array[len(array)-1]` is odd and non-increasing when it is even.
  - `RA-EX-1-P` to `RA-EX-4-P`: each example also as a property, "this input gives exactly this output".
- **Scenarios (4):** `RA-EX-1-S` to `RA-EX-4-S`, one per example. Each also requires `outcome == 0`. Without that, an exception on `[]` would match `[] => []`, because `F-EMPTY` makes the result empty whenever the call doesn't return.
- No ghosts, assumptions or dont_cares.
- **Decisions:** all 11 flagged phrases are recorded, and I took reading 1 for every one.

**Unformalized (6), with reasons**
- **R-IF-1, R-IF-2:** non-functional. They are about delivering the code and naming the function, not about the calls. The visible part of R-IF-1, that every call returns, is `RA-RET-1`.
- **R-IN-1:** already guaranteed by the interface. Inputs are unsigned 8-bit values, so negative numbers can't occur and an assumption would always be true.
- **R-RET-3 (the result is a new list) and R-NC-1 (the given array is not changed):** these can't be checked. `frame.md` says the trace doesn't record whether the result is the same object as `array`, or what `array` holds after the call. So two of the prompt's explicit requirements can't be checked by running the code.
- **R-FR-1:** covered by `F-EMPTY` in `design.yaml`, which is added to every formalization set.

**Problems in the specification**
1. **"you will sort the given array" and "sort it" contradict "don't change the given array".** Read literally, the prompt says to sort the input in place. I took the copy reading, and since the trace can't see the input after the call, the contradiction can't show up in checks.
2. **"sum( first index value, last index value)" has two readings.** It could mean the values at the first and last index, or the index numbers 0 and len−1. All four examples fit both readings, so the examples can't settle it. I took the values.
3. **The empty array has no first or last value**, so the parity rule is undefined for it. I treated it as falling under neither rule. This changes nothing, because the same-values rule already forces an empty result.
4. **"ascending" and "descending" could be strict.** Strict order is impossible when values repeat, so I took non-decreasing and non-increasing.
5. **A one-element array always counts as even** (`2·array[0]`), so it falls under the descending rule. This is harmless.
6. **"returns a list" doesn't map exactly onto the outcome codes.** Outcome 2 also covers returning a list that is too long or holds out-of-range values. I wrote it as `outcome == 0`, because a correct copy of the argument always fits.