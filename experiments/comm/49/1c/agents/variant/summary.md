I wrote `formal/variant.yaml`. `fcp lint` reports no errors, and `fcp explain` shows every item means what I intended. However, the readings you gave contradict each other, so the set has no valid result on any of the five docstring calls. I kept the readings exactly as given and recorded the conflict in the notes rather than fixing it.

**Items: 19** (14 properties, 5 scenarios), plus 9 `decisions`.
- **R-RET-1 (7 properties):**
  - For p ≥ 1, except on the five docstring calls, the result is `(n ^ 2) % p` (XOR, as instructed). FCP-PL only allows `%` by a constant, so the property spells out the modulus separately for each of the 127 possible values of p.
  - For p = 0, the call raises an exception (outcome 1).
  - On each docstring call, the docstring's value applies: 5, 101, 101, 11, 101.
- **R-EX-1…5:** each has a property and a scenario pinning the value you gave: 3, 2, 1, 8, 1.
- **R-NUM-1:** I chose "exactness" (reading 1) myself, since it wasn't on your list. It becomes `outcome != 2`: the call never returns a float or an out-of-range value.
- Every note says when an instructed reading was used, even where another reading seemed more natural.

**Left unformalized:**
- **R-IF-1:** this defines the function's name and parameter order. The `function` section of `design.yaml` already covers it.
- **R-IF-2:** this is an instruction about how the code is written, with no effect a call could observe.
- **R-FR-1:** this is the frame rule F-ZERO, which applies to every set anyway (`covered_by: [F-ZERO]`).

**Problems with the readings:**
1. **R-RET-1 against R-EX-k on the same calls.** For R-RET-1 the docstring values govern, but for R-EX-k "the examples are erroneous and R-RET-1 governs". So modp(3, 5) has to be both 5 and 3, and likewise for all five calls. The five R-EX scenarios therefore cannot all be met together with the R-RET-1 properties.
2. **The XOR reading against the R-EX values.** The values given for R-EX (3, 2, 1, 8, 1) are what `2 ** n % p` gives, i.e. exponentiation. They are not what R-RET-1 gives under either of its readings here. The XOR formula gives 1, 93, 2, 1, 1, which matches only modp(100, 101).
3. **Python operator precedence.** `2 ^ n % p` in Python actually means `2 ^ (n % p)`. I read the text "2^n modulo p" as `(2 ^ n) % p` and said so in the note.

**Problems in the specification itself:** all five docstring examples return p. No reading of "2^n modulo p" can do that, because a value mod p is always below p.

I only ran `lint` and `explain`. I didn't run `fcp check`, so a solver hasn't yet confirmed the conflicts above or how the XOR/modulo expression is evaluated.