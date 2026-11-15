# FCP review

Before any code: the request alone.

Settled: 6 requirements. Questions: 8.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: candidate("abcd", "abd") returns False (no rotation of "abd" - "abd", "bda", "dab" - is a substring of "abcd", although "abd" is a subsequence of it).
- R-EX-2: candidate("hello", "ell") returns True ("ell" itself is a substring of "hello").
- R-EX-3: candidate("whassup", "psus") returns False (no rotation of "psus" - "psus", "susp", "usps", "spsu" - is a substring of "whassup").
- R-EX-4: candidate("abab", "baa") returns True (the rotation "aba" of "baa" is a substring of "abab", although "baa" itself is not).
- R-EX-5: candidate("efef", "eeff") returns False (no rotation of "eeff" - "eeff", "effe", "ffee", "feef" - equals "efef", although "efef" is a permutation of "eeff").
- R-EX-6: candidate("himenss", "simen") returns True (the rotation "imens" of "simen" is a substring of "himenss").

## Questions
1. **depends** (R-RULE-1, R-RULE-2): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate("\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001", "") -> False`
2. **ambiguity** (R-RET-1): "Complete this function" can mean: every call on any two strings must return True or False / only the calls shown in the examples must return a bool; on other calls (for example with an empty string) raising an exception or returning another type is allowed. Which is meant?
3. **ambiguity** (R-RET-1): "=> True / => False (the result notation of the examples)" can mean: the returned value is exactly the bool True (False) / any truthy (falsy) value, such as 1, 0, "" or None, is acceptable. Which is meant?
4. **ambiguity** (R-RULE-1): "the prompt states no rule, only six examples" can mean: True exactly when b or some rotation of b is a contiguous substring of a / True exactly when some rotation of b or some rotation of the reverse of b is a contiguous substring of a (also agrees with all six examples) / only the six example calls are constrained; every other call may return True or False. Which is meant?
5. **ambiguity** (R-RULE-1): "an empty b (no example has one)" can mean: True: the empty string is a substring of every string, including the empty one / False: an empty pattern never matches / unconstrained: either result is acceptable. Which is meant?
6. **ambiguity** (R-RULE-1, R-RULE-2): "upper and lower case (every example is lower case)" can mean: characters are compared by their exact codes ("A" differs from "a") / letters are compared ignoring case ("A" matches "a"). Which is meant?
7. **ambiguity** (R-RULE-2): "the prompt states no rule, only six examples" can mean: False exactly when neither b nor any rotation of b is a contiguous substring of a / False exactly when no rotation of b and no rotation of the reverse of b is a contiguous substring of a (also agrees with all six examples) / only the six example calls are constrained; every other call may return True or False. Which is meant?
8. **ambiguity** (R-RULE-2): "an empty b (no example has one)" can mean: an empty b is a substring of every a, so this rule never applies to it and the call returns True / an empty b never matches, so the call returns False / unconstrained: either result is acceptable. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RET-1, "Complete this function": both took "every call on any two strings must return True or False"
- R-RET-1, "=> True / => False (the result notation of the examples)": both took "the returned value is exactly the bool True (False)"
- R-RULE-1, "the prompt states no rule, only six examples": both took "True exactly when b or some rotation of b is a contiguous substring of a"
- R-RULE-1, "an empty b (no example has one)": both took "True: the empty string is a substring of every string, including the empty one"
- R-RULE-1, "upper and lower case (every example is lower case)": both took "characters are compared by their exact codes ("A" differs from "a")"
- R-RULE-2, "the prompt states no rule, only six examples": both took "False exactly when neither b nor any rotation of b is a contiguous substring of a"
- R-RULE-2, "an empty b (no example has one)": both took "an empty b is a substring of every a, so this rule never applies to it and the call returns True"
- R-RULE-2, "upper and lower case (every example is lower case)": both took "characters are compared by their exact codes ("A" differs from "a")"

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- request points of agent_a
- request points of agent_b
