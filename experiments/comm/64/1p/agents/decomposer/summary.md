I wrote `requirements_draft.yaml` with 11 requirements. `fcp anchor` accepted every quote on the first run and produced `requirements.yaml`.

**What's in it:**
- **TASK-1 to TASK-3:** "Complete this function:" (non_functional), the signature `def candidate(s):` (definition), and the `FIX` note "Add more test cases." (non_functional).
- **IN-1:** the input is a string representing a word (assumption).
- **IN-2:** `candidate` returns without raising for every such input (guarantee).
- **OUT-1:** what the function returns (guarantee, heavily flagged; see below).
- **VOW-1 to VOW-4:** a/e/i/o/u are vowels anywhere; no other character is a vowel; 'y' at the end of the word is a vowel; 'y' anywhere else is not (all definitions).
- **FR-1:** frame rule F-ZERO, "`result` is 0 unless `outcome` is 0". It uses the id `R-FR-1`, which `design.yaml` already refers to.

There are no examples in the request, so there are no scenario requirements.

**Ambiguities flagged:**
- **The return value is never stated.** The prompt seems to be cut off before it says what to return. On OUT-1 I gave four readings: the number of vowel occurrences, the number of distinct vowels, whether the word contains a vowel, or nothing specified at all.
- **Upper case:** whether 'A', 'E', 'I', 'O', 'U' and 'Y' count as vowels (on VOW-1 to VOW-4). The test values in `design.yaml` include `'ACEDY'`, which suggests the hidden tests expect upper case to count.
- **"a string representing a word":** whether it must be letters only and non-empty, or can be any string (including empty), and whether it can hold several words (IN-1 and IN-2).
- **"at the end of the given word":** the last character of `s`, the last letter ignoring trailing spaces or punctuation, or the end of each word if `s` holds several (VOW-4).
- **"Add more test cases.":** an instruction to the assistant, or a leftover note that asks nothing of it.
- **Apparent contradiction:** "Vowels in this case are 'a', 'e', 'i', 'o', 'u'" reads like a closed list, but the next sentence adds 'y'. I recorded this on both VOW-1 and VOW-3. The word "also" most likely makes the second sentence an addition, but I flagged it anyway.