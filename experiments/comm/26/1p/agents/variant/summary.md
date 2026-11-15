I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and `fcp explain --set variant` reads each item back the way I intended. I couldn't run any deeper check: `fcp check` isn't available to an agent, and running my small Python script that tests the properties against each other needed approval and didn't run. So whether the properties can all hold together and fix the result up to order rests on my own reasoning, not a test.

**Items: 5 properties, all in set `variant`, ids starting `RV-`:**
- **RV-SIG-2:** every call returns a fitting list (`outcome == 0`).
- **RV-RM-1:** no value that appears two or more times in `numbers` appears in `result`.
- **RV-RM-2:** each value appears in `result` at most as often as in `numbers`.
- **RV-RM-3:** every value that appears exactly once in `numbers` is in `result`.
- **RV-RM-3-EXACT:** the "so … exactly the elements of numbers minus the removed ones" clause. `result` contains exactly the values that appear once, each once, in no particular order.

The three removal properties apply only when a list is returned (`outcome == 0`). All six decisions use reading 2, as you instructed. Each item a forced reading affects says so in its note.

**Requirements left unformalized (5):**
- **R-TASK-1, R-SIG-1:** these are about the form of the submission (the function body, its name, the parameter annotation). None of that shows up in a trace of calls.
- **R-IN-1:** the interface already guarantees it. `numbers` is always a list of at most 8 integers from 0 to 255, and frame.md drops every other call from the trace, so any assumption would always be true.
- **R-RM-4:** under the forced reading ("any order") there is no order to constrain. I marked it as covered by the four removal properties, which fix which elements remain and how many times regardless of order. I didn't add a scenario that requires a reordered result, because "may" allows reordering but doesn't demand it.
- **R-FR-1:** this is the frame rule F-EMPTY, which is added to every set automatically; marked as covered by it.

**Problems in the specification:**
1. The docstring "remove all elements that occur" is cut short. Read literally, it removes everything, since every element occurs in the list. The restrictive clause implies a condition for choosing which elements go, but the prompt never states it. The "occur more than once" condition comes entirely from your instructed reading, not from the prompt.
2. The forced reading of R-SIG-2 doesn't change anything visible. Deleting in place and returning the same list object can't be seen in the trace, so its formal content is the same as reading 1.
3. Two forced readings pull against each other. Deleting elements in place (R-SIG-2) naturally keeps the remaining elements in their original order, but R-RM-4 is read as "any order". I followed R-RM-4 and didn't constrain order; the notes on RV-SIG-2 and R-RM-4 point this out.
4. The return annotation `-> List[int]` is the only thing that says the function returns, and nothing at all says whether the argument may be changed.