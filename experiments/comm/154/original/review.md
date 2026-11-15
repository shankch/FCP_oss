# FCP review

Before any code: the request alone.

Settled: 6 requirements. Questions: 5.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: cycpattern_check("abcd", "abd") returns False (no rotation of "abd" -- "abd", "bda", "dab" -- is a substring of "abcd").
- R-EX-2: cycpattern_check("hello", "ell") returns True ("ell" itself is a substring of "hello").
- R-EX-3: cycpattern_check("whassup", "psus") returns False (no rotation of "psus" -- "psus", "susp", "usps", "spsu" -- is a substring of "whassup").
- R-EX-4: cycpattern_check("abab", "baa") returns True (the rotation "aba" of "baa" is a substring of "abab", although "baa" itself is not).
- R-EX-5: cycpattern_check("efef", "eeff") returns False (no rotation of "eeff" -- "eeff", "effe", "ffee", "feef" -- is a substring of "efef").
- R-EX-6: cycpattern_check("himenss", "simen") returns True (the rotation "imens" of "simen" is a substring of "himenss", although "simen" itself is not).

## Questions
1. **depends** (R-RES-1, R-RES-3): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `cycpattern_check(" ", "") -> False`
2. **readings** (R-RES-1): the two readings of this requirement disagree on these calls: which is meant?
   - `cycpattern_check("", "") -> False`
3. **readings** (R-RES-2): the two readings of this requirement disagree on these calls: which is meant?
   - `cycpattern_check("", " ") -> True`
4. **ambiguity** (R-RES-2): "return True if" can mean: if and only if: the function returns False whenever no rotation of b (b included) is a substring of a, as the examples returning False suggest / a sufficient condition only: the text states when True is returned and says nothing about the other calls, whose result is unconstrained. Which is meant?
5. **ambiguity** (R-RES-3): "return True" can mean: the bool values True and False exactly; returning another type (such as 1, 0 or None) breaks the requirement / any value Python treats as true or false; returning 1 or 0 (or None for false) is acceptable. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-DEF-1, "rotations": both took "cyclic shifts of b only: b[k:] + b[:k] for 0 <= k < len(b)"
- R-DEF-2, "a substring": both took "a contiguous run of characters of a, which may be the whole of a"
- R-DEF-2, "substring in the first word": both took "characters are compared exactly (case-sensitive): 'A' and 'a' differ"
- R-RES-2, "return True if": both took "if and only if: the function returns False whenever no rotation of b (b included) is a substring of a, as the examples returning False suggest"
- R-RES-3, "return True": both took "the bool values True and False exactly; returning another type (such as 1, 0 or None) breaks the requirement"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1-LETTERS (R-IN-1): every call meets `a_letters && b_letters`; `a_letters` is `all(i < len(a): isalpha(a[i]))`; `b_letters` is `all(i < len(b): isalpha(b[i]))`
- agent_a, RA-IN-1-NONEMPTY (R-IN-1): every call meets `len(a) > 0 && len(b) > 0`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- request points of agent_b
- request points of agent_a, agent_b
- request points of agent_a, agent_b, variant
- the comparison of agent_a and agent_b
- request points of agent_a, variant
- the comparison of agent_a and variant
