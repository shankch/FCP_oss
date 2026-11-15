# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 19.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-OUT-1: is_happy(s) returns True when s is happy and False when s is not happy.

## Questions
1. **depends** (R-HAP-3): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `is_happy("bcdfebfcdeafgeabcstvuavrqpronppa") -> False`
2. **ambiguity** (R-OUT-2): "check if the string is happy or not" can mean: the result must be the bool True or False (as the examples show) / any truthy or falsy value (such as 1/0, or a non-empty/empty object) is an acceptable answer. Which is meant?
3. **ambiguity** (R-OUT-2): "check if the string is happy or not" can mean: every string must be answered with True or False, including strings with non-letter characters / only strings of letters must be answered; for other strings the function may raise or return anything. Which is meant?
4. **ambiguity** (R-HAP-1): "A string is happy if" can mean: 'if' means 'if and only if': a length of at least 3 is necessary, so every string shorter than 3 is not happy / 'if' gives only a sufficient condition: the sentence says nothing about strings shorter than 3 (only the examples a and aa say they are not happy). Which is meant?
5. **ambiguity** (R-HAP-1, R-HAP-3): "its length" can mean: the number of characters of s / the number of letters of s (non-letter characters not counted). Which is meant?
6. **ambiguity** (R-HAP-2): "A string is happy if" can mean: 'if' means 'if and only if': distinct substrings of letters are necessary, so a string without them is not happy / 'if' gives only a sufficient condition: the sentence says nothing about strings without distinct substrings (only the examples aabb and xyy say they are not happy). Which is meant?
7. **ambiguity** (R-HAP-2, R-HAP-3): "substrings of letters are distinct" can mean: every substring of 3 consecutive characters consists of 3 pairwise different characters (s[i], s[i+1], s[i+2] all differ) / every two adjacent characters differ (no substring of 2 equal letters) / all characters of the string are pairwise different (equivalently, no substring occurs twice) / the substrings of some fixed length (2 or 3) are all different from one another (no repeated pair or triple); this makes aabb and xyy happy, contradicting the examples. Which is meant?
8. **ambiguity** (R-HAP-2, R-HAP-3): "roughly" can mean: a hedge or filler word: the distinctness condition is strict and a single repeat makes the string unhappy / approximately: most substrings must be distinct and a small number of repeats is tolerated / the exact condition is left unspecified and is to be inferred from the examples. Which is meant?
9. **ambiguity** (R-HAP-2, R-HAP-3): "roughly substrings of letters are distinct" can mean: contradiction resolved by the examples: aabb and xyy (each with a single repeated adjacent letter) are not happy, so the condition is strict / contradiction resolved by the definition: under a tolerant reading of 'roughly' (or the reading that substrings differ from one another) xyy and aabb would be happy, so the examples is_happy(aabb) => False and is_happy(xyy) => False are overruled. Which is meant?
10. **ambiguity** (R-HAP-2, R-HAP-3): "letters" can mean: every character of s counts, whatever its kind / only alphabetic characters count: non-letters are skipped (or removed) before checking distinctness / s is assumed to contain only letters; strings with non-letters are a don't care. Which is meant?
11. **ambiguity** (R-HAP-2, R-HAP-3): "distinct" can mean: case-sensitive: 'A' and 'a' are different letters / case-insensitive: 'A' and 'a' are the same letter. Which is meant?
12. **ambiguity** (R-EX-1): "is_happy(a)" can mean: the argument is the one-character string "a" (quotes omitted) / the argument is a variable named a whose value is not given. Which is meant?
13. **ambiguity** (R-EX-2): "is_happy(aa)" can mean: the argument is the string "aa" (quotes omitted) / the argument is a variable named aa whose value is not given. Which is meant?
14. **ambiguity** (R-EX-3): "is_happy(abcd)" can mean: the argument is the string "abcd" (quotes omitted) / the argument is a variable named abcd whose value is not given. Which is meant?
15. **ambiguity** (R-EX-4): "is_happy(aabb)" can mean: the argument is the string "aabb" (quotes omitted) / the argument is a variable named aabb whose value is not given. Which is meant?
16. **ambiguity** (R-EX-4): "is_happy(aabb) => False" can mean: contradiction resolved by the example: aabb has length 4 but repeated adjacent letters, so the distinctness condition is strict and the string is not happy / contradiction resolved by the definition: 'roughly ... distinct' tolerates a few repeats, or only requires substrings of a fixed length to differ from one another (aa, ab, bb are all different; aab, abb are different), so aabb would be happy and the example is overruled. Which is meant?
17. **ambiguity** (R-EX-5): "is_happy(adb)" can mean: the argument is the string "adb" (quotes omitted) / the argument is a variable named adb whose value is not given. Which is meant?
18. **ambiguity** (R-EX-6): "is_happy(xyy)" can mean: the argument is the string "xyy" (quotes omitted) / the argument is a variable named xyy whose value is not given. Which is meant?
19. **ambiguity** (R-EX-6): "is_happy(xyy) => False" can mean: contradiction resolved by the example: xyy has length 3 but one repeated adjacent letter, so the distinctness condition is strict and the string is not happy / contradiction resolved by the definition: 'roughly ... distinct' tolerates a single repeat, or only requires substrings to differ from one another (xyy has a single substring of length 3), so xyy would be happy and the example is overruled. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "a string s": both took "any string: it may contain non-letter characters (digits, spaces, punctuation, other codes) and upper-case letters, and every such string must be answered"
- R-OUT-2, "check if the string is happy or not": both took "the result must be the bool True or False (as the examples show)"
- R-HAP-1, "A string is happy if": both took "'if' means 'if and only if': a length of at least 3 is necessary, so every string shorter than 3 is not happy"
- R-HAP-1, "its length": both took "the number of characters of s"
- R-HAP-2, "A string is happy if": both took "'if' means 'if and only if': distinct substrings of letters are necessary, so a string without them is not happy"
- R-HAP-2, "substrings of letters are distinct": both took "all characters of the string are pairwise different (equivalently, no substring occurs twice)"
- R-HAP-2, "roughly": both took "a hedge or filler word: the distinctness condition is strict and a single repeat makes the string unhappy"
- R-HAP-2, "roughly substrings of letters are distinct": both took "contradiction resolved by the examples: aabb and xyy (each with a single repeated adjacent letter) are not happy, so the condition is strict"
- R-HAP-2, "letters": both took "only alphabetic characters count: non-letters are skipped (or removed) before checking distinctness"
- R-HAP-2, "distinct": both took "case-sensitive: 'A' and 'a' are different letters"
- R-HAP-3, "substrings of letters are distinct": both took "all characters of the string are pairwise different (equivalently, no substring occurs twice)"
- R-HAP-3, "roughly": both took "a hedge or filler word: the distinctness condition is strict and a single repeat makes the string unhappy"
- R-HAP-3, "roughly substrings of letters are distinct": both took "contradiction resolved by the examples: aabb and xyy (each with a single repeated adjacent letter) are not happy, so the condition is strict"
- R-HAP-3, "letters": both took "only alphabetic characters count: non-letters are skipped (or removed) before checking distinctness"
- R-HAP-3, "distinct": both took "case-sensitive: 'A' and 'a' are different letters"
- R-HAP-3, "its length": both took "the number of characters of s"
- R-EX-1, "is_happy(a)": both took "the argument is the one-character string "a" (quotes omitted)"
- R-EX-2, "is_happy(aa)": both took "the argument is the string "aa" (quotes omitted)"
- R-EX-3, "is_happy(abcd)": both took "the argument is the string "abcd" (quotes omitted)"
- R-EX-4, "is_happy(aabb)": both took "the argument is the string "aabb" (quotes omitted)"
- R-EX-4, "is_happy(aabb) => False": both took "contradiction resolved by the example: aabb has length 4 but repeated adjacent letters, so the distinctness condition is strict and the string is not happy"
- R-EX-5, "is_happy(adb)": both took "the argument is the string "adb" (quotes omitted)"
- R-EX-6, "is_happy(xyy)": both took "the argument is the string "xyy" (quotes omitted)"
- R-EX-6, "is_happy(xyy) => False": both took "contradiction resolved by the example: xyy has length 3 but one repeated adjacent letter, so the distinctness condition is strict and the string is not happy"

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- request points of agent_b
