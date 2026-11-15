I've written `formal/agent_a.yaml`. `fcp lint` reports it clean, and the English rendering from `fcp explain` matches what I intended for every item.

**Items: 20**
- **3 assumptions** (R-CON-1..3): each input is at most 1000. I read the "Constrain" lines as rules the caller must follow, not checks the function must make. Values below 0 can't occur, because the inputs are unsigned and negative arguments are not part of the trace.
- **12 properties**:
  - R-RET-1: the call returns normally with a list of exactly 2 elements.
  - R-RET-2: the first element is `number + min(need, remaining)`.
  - R-RET-3: the second element is `max(remaining - need, 0)`.
  - R-MEAL-1 (2 items): when `need <= remaining`, the total is `number + need` and the stock left is `remaining - need`.
  - R-HUN-1..3: when `remaining < need`, the total is `number + remaining`, the stock left is 0, and the total falls short of `number + need` by exactly `need - remaining`.
  - R-EX-1..4: each example is also a guarantee for that exact call.
- **5 scenarios**: one per example, checking it can happen, plus one showing a call with `need == 0` returns normally.

I defined `number = x`, `need = y` and `remaining = z` as named shorthands and wrote the items with those names. 18 decisions are recorded, all reading 1.

**Unformalized: 6, all covered by other items**
- **R-SIG-1, R-CTX-1, R-VAR-1..3:** these are definitions. The shorthands above and the properties that use them carry their meaning.
- **R-FR-1:** this is the adapter's frame rule F-EMPTY. It is already part of every formalization set, and `frame.md` says it need not be restated.

**Problems in the specification**
- **Parameter names:** the signature says `x, y, z` but the docstring says `number, need, remaining`, and nothing links them. I matched them in docstring order, which is the only order that fits `eat(5, 6, 10) -> [11, 4]`.
- **The return description is garbled:** "total number of needed or eaten carrots before or after your meals" and "the number of carrots needed or eaten left". Only the examples settle it. Read literally, "needed" (`number + need`) contradicts `eat(2, 11, 5) -> [7, 0]`, and "still needed" for the second element contradicts three of the four examples.
- **"no or more carrots"** probably means "zero or more". I read it that way, so the rabbit eats exactly `need` when there is enough stock.
- **"but will still be hungry"** names a shortfall that the return value never reports. I treated it as narrative only.
- **Precondition or check:** the constraints don't say whether bad input must be rejected. Under my reading, calls with inputs from 1001 to 1023 can do anything.
- **"array" vs list:** the adapter scores a returned tuple as outcome 2 (not a list). So this choice decides whether a tuple-returning implementation passes.
- **Minor:**
  - At `remaining == need`, the two cases give the same result, so the edge choice in R-HUN-1 makes no difference.
  - There is a typo, "thet" for "that".