# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 8.

## Questions
1. **depends** (R-FN-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `is_happy("dcbabaiagfpgflaq") -> False`
2. **ambiguity** (R-FN-2): "check" can mean: the result is returned as the bool True or False, as the examples show / any truthy or falsy return value (e.g. 1/0, a non-empty or empty value, None for not happy) counts as the answer. Which is meant?
3. **ambiguity** (R-EX-1): "is_happy(a)" can mean: a call with the string 'a', written without quotes / literal Python: a call with the value of a variable named a, which the request does not give (so not a string, at odds with R-IN-1). Which is meant?
4. **ambiguity** (R-EX-2): "is_happy(aa)" can mean: a call with the string 'aa', written without quotes / literal Python: a call with the value of a variable named aa, which the request does not give (so not a string, at odds with R-IN-1). Which is meant?
5. **ambiguity** (R-EX-3): "is_happy(abcd)" can mean: a call with the string 'abcd', written without quotes / literal Python: a call with the value of a variable named abcd, which the request does not give (so not a string, at odds with R-IN-1). Which is meant?
6. **ambiguity** (R-EX-4): "is_happy(aabb)" can mean: a call with the string 'aabb', written without quotes / literal Python: a call with the value of a variable named aabb, which the request does not give (so not a string, at odds with R-IN-1). Which is meant?
7. **ambiguity** (R-EX-5): "is_happy(adb)" can mean: a call with the string 'adb', written without quotes / literal Python: a call with the value of a variable named adb, which the request does not give (so not a string, at odds with R-IN-1). Which is meant?
8. **ambiguity** (R-EX-6): "is_happy(xyy)" can mean: a call with the string 'xyy', written without quotes / literal Python: a call with the value of a variable named xyy, which the request does not give (so not a string, at odds with R-IN-1). Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "a string": both took "any string of any characters (uppercase, digits, spaces, punctuation and other codes included) is a valid argument and must be answered"
- R-IN-1, "a string s": both took "the empty string is a valid argument and must be answered"
- R-DEF-1, "happy": both took "s has at least 3 characters and every 3 consecutive characters are pairwise distinct (s[i], s[i+1], s[i+2] all different); e.g. 'aba' is not happy, 'abca' is happy, 'ab' is not happy"
- R-DEF-1, "the string": both took "characters are compared by their exact code, so 'aA' contains two different characters"
- R-FN-2, "check": both took "the result is returned as the bool True or False, as the examples show"
- R-EX-1, "is_happy(a)": both took "a call with the string 'a', written without quotes"
- R-EX-2, "is_happy(aa)": both took "a call with the string 'aa', written without quotes"
- R-EX-3, "is_happy(abcd)": both took "a call with the string 'abcd', written without quotes"
- R-EX-4, "is_happy(aabb)": both took "a call with the string 'aabb', written without quotes"
- R-EX-5, "is_happy(adb)": both took "a call with the string 'adb', written without quotes"
- R-EX-6, "is_happy(xyy)": both took "a call with the string 'xyy', written without quotes"
