I wrote `formal/agent_b.yaml`. `fcp lint` reports no errors, and the `fcp explain` rendering of every item says what I intended. I couldn't run any further analysis: `fcp check` isn't available to agents, so I haven't confirmed the expected conflicts below with the tool.

**Items: 11** (3 properties, 8 scenarios), plus the frame item F-ZERO that every set gets.
- **Model:** the function keeps no state between calls, so the specification model is a set of named expressions over the current call rather than ghost state:
  - `balanced`: q reads the same forwards and backwards.
  - `total`: the sum of q's elements.
  - `light`: `total <= w`.
  - `fly`: `balanced && light`.
- **Properties:** these check the output against the model. RB-RET-1 says `fly` means the call returns True. RB-RET-2 says an unbalanced q means it returns False. RB-RET-3 says a sum over w means it returns False. Together they cover every input, so they also require the call to return a bool every time.
- **Scenarios:** RB-EX-1..4 are the four examples exactly as written. RB-WHY-1..4 are the example comments: each checks the facts it states (the sum, whether q is a palindrome) against the model, plus the result the comment explains.
- **Decisions:** all 13 flagged phrases are recorded, and I took reading 1 (the literal one) for each. Two of these are judgement calls:
  - **Empty list:** it counts as a palindrome, so it flies for any w.
  - **"will fly if":** I read it as "if and only if". That sentence is the only definition of "will fly", and "and False otherwise" needs one.

**Requirements left unformalized: 7, each with a reason.**
- **R-API-1 (name and parameter order):** this isn't behaviour in the trace; the adapter fixes it. A wrong signature would make every call raise, which the RB-RET properties already reject.
- **R-IN-1 and R-IN-2 (what the caller passes):** these hold by construction. The interface can only carry a list of up to 8 integers from 0 to 255 and a w from 0 to 2,047, so there's nothing left to assume.
- **R-DEF-1, R-DEF-2, R-DEF-3 (definitions):** the model expressions realize them, and each lists the items that use them under `covered_by`.
- **R-FR-1:** covered by the frame item F-ZERO.

**Problems in the specification:**
1. **All four examples contradict the rule.** Each expected value is the opposite of what the rule gives, and the opposite of what that example's own comment explains: `[1,2],5 ➞ True`, `[3,2,3],1 ➞ True`, `[3,2,3],9 ➞ False`, `[3],5 ➞ False`. I kept this rather than fixing it. Each RB-EX scenario should therefore be impossible under the RB-RET properties, which is meant to make the conflict show up in FCP's consistency analysis. The WHY scenarios agree with the rule.
2. **The empty list isn't addressed.**
3. **"will fly if"** could mean either "if and only if" or only "this is enough".
4. **Minor wording mismatch:** the comments say "less than" where the rule says "less than or equal". This doesn't matter for the examples, since none of them has a sum equal to w.