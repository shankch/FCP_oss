# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 13.

## Questions
1. **depends** (R-RET-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
2. **ambiguity** (R-RET-1): "related to the first word" can mean: occurs as a contiguous substring of the first word (consistent with all six examples) / occurs as a subsequence (not necessarily contiguous) of the first word; this contradicts the example cycpattern_check("abcd","abd") => False, since abd is a subsequence of abcd / all of its characters occur in the first word, counting multiplicity (an anagram of part of it); this contradicts the examples whassup/psus => False (whassup contains p, s, s, u) and efef/eeff => False (eeff is an anagram of efef) / is equal to the first word (b is a rotation of a); this contradicts the examples hello/ell => True, abab/baa => True and himenss/simen => True, where the lengths differ / either one contains the other: the rotation occurs in the first word, or the first word occurs in the rotation (consistent with all six examples, but differs when the first word is shorter, e.g. a = "ab", b = "bab"). Which is meant?
3. **ambiguity** (R-RET-1): "related" can mean: characters are compared exactly (case-sensitive) / characters are compared ignoring letter case. Which is meant?
4. **ambiguity** (R-RET-1): "any of its rotations" can mean: the cyclic shifts of the second word (moving leading characters to the end), e.g. abd, bda, dab (consistent with all six examples) / any rearrangement (permutation) of the characters of the second word; this contradicts the example efef/eeff => False, since efef is a rearrangement of eeff and equals the first word. Which is meant?
5. **ambiguity** (R-RET-1): "the second word" can mean: an empty second word has the single rotation "", which occurs in every first word, so the call returns True / an empty second word is not a word, so the result for it is unspecified. Which is meant?
6. **ambiguity** (R-RET-1): "return True" can mean: return the bool value True / return any truthy value. Which is meant?
7. **ambiguity** (R-RET-2): "if" can mean: if and only if: when no rotation is related, the call returns False (as the examples abcd/abd, whassup/psus and efef/eeff show) / a sufficient condition only: the text states nothing for the case where no rotation is related, so the result there is unspecified apart from the examples. Which is meant?
8. **ambiguity** (R-EX-1): "=> False" can mean: consistent with R-RET-1 when related means contiguous substring: none of abd, bda, dab occurs in abcd / contradicts R-RET-1 when related means subsequence: abd itself is a subsequence of abcd, so the call would return True. Which is meant?
9. **ambiguity** (R-EX-2): "=> True" can mean: consistent with R-RET-1 when related means contiguous substring: ell occurs in hello / contradicts R-RET-1 when related means equal to the first word (b is a rotation of a): no rotation of ell equals hello. Which is meant?
10. **ambiguity** (R-EX-3): "=> False" can mean: consistent with R-RET-1 when related means contiguous substring: none of psus, susp, usps, spsu occurs in whassup / contradicts R-RET-1 when related means the characters occur in the first word counting multiplicity: whassup contains p, s, s and u. Which is meant?
11. **ambiguity** (R-EX-4): "=> True" can mean: consistent with R-RET-1 when related means contiguous substring: the rotation aba occurs in abab / contradicts R-RET-1 when related means equal to the first word (b is a rotation of a): no rotation of baa equals abab. Which is meant?
12. **ambiguity** (R-EX-5): "=> False" can mean: consistent with R-RET-1 when related means contiguous substring and rotations are cyclic shifts: none of eeff, effe, ffee, feef occurs in efef / contradicts R-RET-1 when rotations means any rearrangement, or related means the characters occur in the first word counting multiplicity: efef is a rearrangement of eeff. Which is meant?
13. **ambiguity** (R-EX-6): "=> True" can mean: consistent with R-RET-1 when related means contiguous substring: the rotation imens occurs in himenss / contradicts R-RET-1 when related means equal to the first word (b is a rotation of a): no rotation of simen equals himenss. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "2 words": both took "two non-empty strings of letters only; calls with an empty string or non-letter characters are outside the contract and their result is a don't-care"
- R-IN-1, "words": both took "words may mix upper- and lower-case letters, and case is significant"
- R-RET-1, "related to the first word": both took "occurs as a contiguous substring of the first word (consistent with all six examples)"
- R-RET-1, "related": both took "characters are compared exactly (case-sensitive)"
- R-RET-1, "any of its rotations": both took "the cyclic shifts of the second word (moving leading characters to the end), e.g. abd, bda, dab (consistent with all six examples)"
- R-RET-1, "the second word": both took "an empty second word is not a word, so the result for it is unspecified"
- R-RET-1, "return True": both took "return the bool value True"
- R-RET-2, "if": both took "if and only if: when no rotation is related, the call returns False (as the examples abcd/abd, whassup/psus and efef/eeff show)"
- R-EX-1, "=> False": both took "consistent with R-RET-1 when related means contiguous substring: none of abd, bda, dab occurs in abcd"
- R-EX-2, "=> True": both took "consistent with R-RET-1 when related means contiguous substring: ell occurs in hello"
- R-EX-3, "=> False": both took "consistent with R-RET-1 when related means contiguous substring: none of psus, susp, usps, spsu occurs in whassup"
- R-EX-4, "=> True": both took "consistent with R-RET-1 when related means contiguous substring: the rotation aba occurs in abab"
- R-EX-5, "=> False": both took "consistent with R-RET-1 when related means contiguous substring and rotations are cyclic shifts: none of eeff, effe, ffee, feef occurs in efef"
- R-EX-6, "=> True": both took "consistent with R-RET-1 when related means contiguous substring: the rotation imens occurs in himenss"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `word_a && word_b`; `word_a` is `len(a) >= 1 && all(i < len(a): isalpha(a[i]))`; `word_b` is `len(b) >= 1 && all(i < len(b): isalpha(b[i]))`
- agent_b, RB-IN-1 (R-IN-1): every call meets `a_word && b_word`; `a_word` is `len(a) >= 1 && all(i < len(a): isalpha(a[i]))`; `b_word` is `len(b) >= 1 && all(i < len(b): isalpha(b[i]))`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- request points of agent_a
- request points of agent_b
- request points of agent_a, variant
- request points of agent_a, agent_b, variant
- the comparison of agent_a and variant
