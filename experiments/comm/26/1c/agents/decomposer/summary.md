I split the prompt into 11 atomic requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run ("anchored 11 requirements") and wrote `requirements.yaml`.

**Requirements**
- **R-FR-1** (FRAME, guarantee): F-EMPTY, meaning `result` is empty unless `outcome` is 0. I kept this ID because `design.yaml` already refers to it.
- **R-IF-1** (non_functional): the answer must be a complete implementation of the given function stub.
- **R-IF-2** (definition): the function is named `remove_duplicates` and takes one argument, `numbers`, a list of integers.
- **R-IF-3** (guarantee): the function returns a list of integers (`-> List[int]`).
- **R-IN-1** (assumption): the input is a list of integers.
- **R-DEF-1** (definition): what "occur more than once" means.
- **R-RM-1** (guarantee): what happens to values that appear more than once in the input.
- **R-RM-2** (guarantee): values that appear exactly once stay, exactly once.
- **R-RM-3** (guarantee): the result contains only values from the input and is never longer than it.
- **R-ORD-1** (guarantee): kept elements stay in their input order.
- **R-EX-1** (scenario): `[1, 2, 3, 2, 4]` returns `[1, 2, 3, 4]`.

**Contradiction (flagged on both R-RM-1 and R-EX-1)**
Read literally, "remove all elements that occur more than once" drops every copy of a repeated value, so the example would return `[1, 3, 4]`. The example instead keeps one copy and returns `[1, 2, 3, 4]`. That matches the other reading, where only the extra copies are removed, and it also fits the function name.

**Other ambiguities flagged**
- **R-DEF-1:** whether a duplicate is a repeat anywhere in the list or only next to each other, as Unix `uniq` treats it. The example settles this as "anywhere".
- **R-ORD-1:** when one copy of a repeated value is kept, whether it goes where the first copy was, where the last copy was, or anywhere. The example implies the first copy.
- **R-IF-3:** whether the return type means the function must always return normally, or doesn't rule out raising an exception.
- **R-RM-3:** whether to build a new list or remove items from `numbers` in place. The trace can't see this either way.