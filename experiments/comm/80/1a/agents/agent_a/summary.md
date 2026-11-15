I wrote `formal/agent_a.yaml`. `fcp lint` reports it clean, and the `fcp explain` output says what I intended for every item.

**Items: 17**
- **11 properties:**
  - RA-OUT-1: every call returns a bool, and it is True exactly when the string is happy.
  - RA-OUT-2: every call returns a bool (`outcome == 0`).
  - RA-HAP-1/2/3: strings shorter than 3 characters return False; strings with a repeated letter return False; strings of 3 or more characters with no repeated letter return True.
  - RA-EX-1…6: each docstring example, as a rule that the given input must give the given result.
- **6 scenarios:** RA-EX-*-C, each saying the corresponding example call is possible.
- The adapter's frame rule F-ZERO (`happy` is false unless `outcome` is 0) is added to the set automatically.
- I added no assumptions, don't-cares or ghost state. "Happy" is one definition: `len(s) >= 3` and every letter of `s` occurs exactly once (letters checked with `isalpha`).

**Unformalized: 4**
- **R-API-1 and R-API-2:** these are non-functional (deliver an implementation; the name and the single argument). The adapter fixes the signature. A missing function or wrong number of arguments would make every call fail, which RA-OUT-2 catches.
- **R-IN-1:** I read "a string s" as any string, so the inputs need no restriction beyond the interface. It is covered by RA-OUT-2.
- **R-FR-1:** this is the frame rule F-ZERO, and the frame says it need not be restated. It is listed as `covered_by: [F-ZERO]`.

I recorded all 25 flagged phrases under `decisions`.

**Problems in the specification**
- **The core condition is garbled.** "roughly substrings of letters are distinct" gives no substring length, and "roughly" sets no tolerance. The examples fit three different rules equally well:
  - every 3 consecutive characters differ;
  - neighbouring characters differ;
  - all characters differ.

  I took the most literal reading: substrings of letters don't repeat, which means no letter occurs twice. This differs from the probable intended rule (every 3 consecutive characters differ) on strings like `abca`, which is False under my reading.
- **"Roughly" can't be checked as "approximately".** I treated it as a filler word. The `xyy` example (one repeat gives False) rules out any tolerance, so no example is overruled.
- **"Letters" versus characters.** I took "letters" literally, so non-letters don't count. As a result `!!!` and `a1b1` are happy, which is probably not what was meant.
- **Which characters are letters.** I used the built-in `isalpha`, which covers only a–z and A–Z. Accented Latin-1 letters such as é therefore count as non-letters, whereas Python's `str.isalpha` would treat them as letters. The text doesn't settle this.
- **"A string is happy if…"** is literally only a sufficient condition. I read it as a full definition, because the task asks to decide "happy or not" and the examples `a`, `aa`, `aabb` and `xyy` rely on it.
- **Case is never mentioned.** I treated `A` and `a` as different letters.

I didn't run `fcp check`, so there is no spec-level consistency or reachability result yet. I checked by hand that all six examples agree with the definition.