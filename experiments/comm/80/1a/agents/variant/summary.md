I wrote `formal/variant.yaml`. `fcp lint` reports clean, and the `fcp explain` read-back matches what I intended for every item.

**Items: 9**
- **1 assumption:** RV-IN-1 says the string contains only letters. Strings with anything else are outside the contract, so any answer for them is acceptable.
- **2 properties:**
  - RV-OUT-2: every call returns something (outcome 0 or 2), and never raises or fails to answer.
  - RV-HAP-3: a string with at least 3 letters whose 3-character substrings are "roughly distinct" must be answered True (or with a non-bool value).
- **4 scenarios:** RV-EX-1, -2, -3 and -5. Because the example arguments are read as variables with unknown values, each example only says that some call returns False (or True).
- **2 don't-cares:** RV-HAP-1 and RV-HAP-2 leave `happy` free for strings under 3 letters and for strings that are not roughly distinct. Under the "if = sufficient condition" reading, the text says nothing about those strings.
- **25 decisions**, one per flagged phrase. Every item's note says when it follows your reading rather than the more natural one.

**Requirements left unformalized: 6**
- **R-API-1 and R-API-2:** these are about the code itself (it completes the stub; the name and single argument are fixed by `design.yaml`), not about how calls behave.
- **R-OUT-1:** realized by RV-HAP-3 and RV-OUT-2. "False when not happy" never applies, because no string is ever shown to be unhappy.
- **R-EX-4 and R-EX-6:** dropped, as your reading says the definition overrules these two examples.
- **R-FR-1:** already covered by the frame rule F-ZERO.

**Problems in the specification**
- **"roughly" has no threshold.** I chose to tolerate at most two 3-character substrings with a repeated letter, compared case-insensitively. Two is the smallest number that makes both xyy and aabb happy, which your contradiction reading requires. As a result aaa and aaaa also count as happy, and "most substrings must be distinct" can't hold for short strings.
- **The trace can't fully check the truthy reading.** For a non-bool return (outcome 2), the trace doesn't record whether the value is truthy. So RV-HAP-3 and the scenarios accept any outcome-2 answer, and can't reject a falsy answer to a happy string.
- **R-OUT-2 flags the same phrase twice, and your instructions cover only the first.** For the second I took reading 2 (only letter strings need an answer). It's the only one consistent with your readings for R-IN-1 and the truthy answer.
- **Two of your readings seem to conflict, but it doesn't matter here.** "letters" means every character counts, while "its length" counts only letters. They give the same result because RV-IN-1 already limits strings to letters.
- **The underlying issues in the text:** "is happy if" can mean "if" or "if and only if"; the definition contradicts the aabb and xyy examples; and the example arguments have no quotes, so it's unclear whether they are strings.