I wrote `formal/agent_b.yaml`. `fcp lint` reports clean, and I read back every item in the `fcp explain` output and each one says what I intended. I didn't run `fcp check`, so I haven't machine-checked that the rules are consistent with each other.

**Items: 14** (8 properties and 6 scenarios), plus 5 requirements listed as unformalized and 12 decisions.

- **The model:** each call is independent, so ghost state would just lag one call behind. Instead, the model is a set of named expressions computed from the same call: `bal` (q is a palindrome), `wsum` (sum of q), `light` (`wsum <= w`), `fly` (`bal && light`), and `ret_true` / `ret_false` (the call returned that bool). Every output is checked against them.
- **Properties:**
  - RB-OUT-1: every call returns a bool, i.e. `outcome == 0`.
  - RB-FLY-1: `fly` means it returns True.
  - RB-FLY-2: not balanced means it returns False.
  - RB-FLY-3: not light enough means it returns False.
  - RB-EX-1 to RB-EX-4: each of the four examples returns its stated answer.
  - FLY-1, -2 and -3 between them fix the answer for every input.
- **Scenarios:** each example's call and answer are reachable. Two more pin down the readings I chose: a balanced list whose sum equals `w` flies (RB-FLY-1-EQ), and the empty list flies (RB-FLY-1-EMPTY).
- **Decisions:** I took reading 1 for all 12 flagged phrases.

**Not formalized:**
- **R-IF-1:** the function's name and parameters aren't behaviour, so FCP-PL can't express them. The `function` section of `design.yaml` fixes them.
- **R-DEF-1, R-DEF-2, R-DEF-3:** these are definitions. Each is written as a named expression and marked as covered by the properties and scenarios that use it.
- **R-FR-1:** this is the frame rule F-ZERO, which is added to every set automatically. `frame.md` says it need not be restated.

**Problems in the specification:**
1. **"less than or equal" vs. "is less than":** the rule says `sum <= w`, but all three example comments that mention the weight say "is less than". No example has a sum equal to `w`, so the boundary is never tested. I followed the rule and read the comments as describing their own calls only.
2. **"will fly if":** taken literally, this gives only a sufficient condition. I read it as "if and only if" because the prompt says the function returns "False otherwise", and examples 1 and 2 each explain their False by one failed condition.
3. **The empty list:** the prompt never mentions it. I treated it as a palindrome with sum 0, so `will_it_fly([], w)` returns True for any `w` ≥ 0.
4. **Return type:** the prompt doesn't say whether a truthy value like 1 is acceptable. I read "returns True/False" as the actual Python bools, so returning 1 or 0 counts as a failure.
5. **Inputs:** the prompt says nothing about input types or negative numbers. Only the adapter limits the inputs (at most 8 elements of 0 to 255, `w` up to 4,095), so no assumptions were needed.