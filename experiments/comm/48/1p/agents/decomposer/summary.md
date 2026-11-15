I've written `requirements_draft.yaml` and `requirements.yaml`. `fcp anchor` accepted all 7 quotes on the first run, so nothing needed fixing.

The main point: **spec.md is cut off.** The docstring stops at "Checks if given string is a", so the prompt never says what property the function should check. The checking requirements below can't be pinned down until someone picks a reading.

**Requirements**
- **R-TASK-1** (non_functional), "Complete this function:": write the body and keep the signature and docstring. Ambiguous: it could also mean finishing the cut-off docstring, which would mean choosing the property.
- **R-IF-1** (definition): the function is `candidate`, it takes one parameter `text`, and no return type is declared.
- **R-IF-2** (assumption), `text: str`: callers always pass a string. Ambiguous: either it's only a type hint, or the function must reject non-strings.
- **R-CHK-1** (guarantee): every call finishes and returns True or False. Ambiguous on "Checks if": it could also mean returning any truthy or falsy value, or raising an exception when the check fails.
- **R-CHK-2 / R-CHK-3** (guarantees, from the same clause): return True when the string has the property and False when it doesn't. I split them because each can be checked on its own. Both carry the same two ambiguities:
  - **"is a"** (the cut-off part): a palindrome compared exactly, a palindrome ignoring case and non-alphanumeric characters, or an unstated property where any answer is allowed. I suggested palindrome because the wording matches the standard "Checks if given string is a palindrome" prompt. The test alphabet `'abAB 1.'` fits that too.
  - **"given string"**: whether the empty string follows the same rule or is left unspecified.
- **R-FR-1** (FRAME, guarantee): the F-ZERO rule, that `result` is false unless `outcome` is 0. Its ID matches the `req: R-FR-1` already in design.yaml.

**Scenarios and contradictions:** the prompt has no examples, so there are no scenarios. I found no pairs of statements that contradict each other.