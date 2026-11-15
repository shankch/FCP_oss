I wrote `requirements_draft.yaml` with 9 requirements. `fcp anchor` accepted every quote on the first run ("anchored 9 requirements") and wrote `requirements.yaml`.

**Requirements**
- **R-TASK-1** (non_functional): write the body of `candidate` in Python and keep the given header.
- **R-SIG-1** (non_functional): the function is named `candidate` and takes one parameter, `numbers`, of type `List[int]`.
- **R-IN-1** (assumption): the argument is a list of integers.
- **R-SIG-2** (guarantee): the function always returns a list of integers and never raises an exception or fails to finish.
- **R-RM-1** (guarantee): no element picked for removal appears in the result.
- **R-RM-2** (guarantee): the result only holds elements taken from the input, and no value appears more times than it does in the input.
- **R-RM-3** (guarantee): every element not picked for removal stays in the result.
- **R-RM-4** (guarantee): kept elements stay in the same order as in the input.
- **R-FR-1** (FRAME, F-EMPTY): `result` is the empty list unless `outcome` is 0.

**Ambiguities flagged**
- **The removal sentence is cut off** (R-RM-1, R-RM-3). "remove all elements that occur" has three readings:
  1. Taken literally, every element occurs, so the result is always empty.
  2. "occur more than once": drop every copy of any repeated value.
  3. Remove duplicates: keep the first copy of each value.
- **Contradiction** (recorded on both R-RM-1 and R-RM-3). "all elements" taken literally removes everything. But "that occur" implies only some elements are removed, and the prompt never says which.
- **Order** (R-RM-4): "remove" may mean the remaining elements keep their order, or the prompt may leave order open.
- **Changing the input** (R-SIG-2): the function may build a new list or delete from `numbers` itself. The trace can't show the difference.

The prompt gives no examples, so there are no scenario requirements. I took only F-EMPTY from `frame.md`, because it is the document's only frame rule.