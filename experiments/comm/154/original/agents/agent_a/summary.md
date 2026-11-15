I've written `formal/agent_a.yaml`. `fcp lint` reports it clean, and I read every item back with `fcp explain`: each one says what I intended.

**Items: 11**
- **2 assumptions (R-IN-1):** both arguments contain only letters, and neither is empty.
- **3 properties:**
  - RA-RES-1: if `b` or one of its rotations appears in `a`, the call returns True.
  - RA-RES-2: if none does, the call returns False.
  - RA-RES-3: the call always returns a real `True` or `False` (`outcome == 0`).

  "Appears in `a`" is spelled out in a few named expressions (`defs`) that look for `b` and each rotation `b[k:]+b[:k]` inside `a`. I added no extra model state.
- **6 scenarios:** one per docstring example.
- **7 decisions:** recorded for all seven flagged phrases.

I checked the six examples against the definitions by hand and they all agree. I also wrote a script to compare the formulas with a straightforward Python version on many strings, but running it needed your approval, so it hasn't run. `fcp check` can't be used by an agent, so nothing has been checked automatically beyond lint.

**Left unformalized: 5**
- **R-IF-1** ("Complete this function"): this is about delivering the code, not about any single call. A call that crashes or never finishes is already ruled out by RA-RES-3.
- **R-IF-2, R-DEF-1, R-DEF-2:** these are definitions (which argument is which word, what a rotation is, what a substring is). They live inside the named expressions, so I marked them as covered by RA-RES-1 and RA-RES-2.
- **R-FR-1:** this is the design's frame rule F-ZERO, which is already part of every set. Marked as covered by F-ZERO.

**Readings I chose, and problems in the specification**
1. **"words" is never defined.** I took it literally: non-empty strings of letters only (reading 2 for both "words" and "2 words"). This is the choice with the biggest effect. Under it, calls with an empty argument or a non-letter character are outside the contract, so a common implementation that returns False for an empty `b` passes. Under the other reading it would fail, because an empty string is a substring of every word.
2. **Empty `b` is unclear even under the other reading.** R-DEF-1 allows rotations only for `0 <= k < len(b)`, so an empty `b` has no rotations. The answer then depends on `b` itself being named separately in "the second word or any of its rotations".
3. **"Letters" ends up meaning ASCII only.** That is all FCP-PL's `isalpha` covers, so Latin-1 letters such as é fall outside the contract. The text doesn't settle this either way.
4. **The False case is never stated.** "Return True if" only says when True is returned. I read it as "if and only if" (reading 1), based on the three examples that return False and the fact that the function returns a bool. I also read "returns False" as a normal return, so RA-RES-2 overlaps with RA-RES-3.
5. **Case sensitivity isn't stated.** I compare characters exactly.

The examples themselves are consistent with the readings I chose. The efef/eeff example rules out reading "rotations" as rearrangements, and abcd/abd rules out reading "substring" as letters in order with gaps.