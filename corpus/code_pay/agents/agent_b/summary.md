I wrote `formal/agent_b.yaml`. `fcp lint` reports no errors and one info: YB-API-ANS reads `op`/`phase` to know when a charge happens. It is still receptive, because answer 0 is always allowed. I read the `fcp explain` output item by item and every one says what I meant.

I also checked the items on 16 hand-written runs. There is no Verilog simulator here, so this was a small Python model following the compiled monitor's semantics, not the monitor itself. The ghost timing is right: a ghost's value in a cycle summarises the earlier cycles of the run.

**Items: 20**
- **Model:** 6 ghosts tracking the run (attempts so far, calls so far, latest answer, whether an "ok" or a "declined" has been seen, seconds slept since the last attempt) and 12 named definitions. Every output is checked against them.
- **2 assumptions:** the arguments stay the same through a run (R-SIG-1), and a charge only ever answers ok, declined or error (R-API-1).
- **15 properties** and **3 scenarios.** R-EX-1 gets a scenario and also two properties, because the example states exactly what the function does for that script.

**Left unformalized:** only R-FR-1, R-FR-2 and R-FR-3. These are frame rules that FCP already adds to every set, so they are listed as covered by F-END, F-ZERO and F-LIMIT. Nothing else is unformalized.

**Problems in the specification**
1. **Rule 7 contradicts rules 2, 3 and 4.** "Keep trying until the charge goes through" can't hold alongside "False otherwise", "up to 3 attempts" and "never try again after declined". The service can force the clash just by never answering "ok". I formalized rule 7 literally: the function may not stop while no charge has gone through, and the only accepted end is being cut off after 8 calls. I added two scenarios (another attempt after a decline, a fourth attempt after three errors) that rules 4 and 3 make impossible. In the test runs, a function following rules 2–6 breaks only rule 7, and a function that retries forever breaks the 3-attempt limit and "False otherwise".
2. **Rule 2's "once" is ambiguous.** I chose "as soon as": the return of True comes right after the "ok", with no further call, not even a sleep. That makes rule 6 redundant.
3. **Rule 1 has three gaps.**
   - "Between 1 and 1,000,000" could be inclusive or exclusive; I chose inclusive.
   - The rule doesn't say whether calls may come before the raise, so I didn't rule them out.
   - Read literally, rule 2's "otherwise" also covers rejected amounts and would contradict rule 1. I limited "False otherwise" and rule 7 to accepted amounts, and said so in the notes.
   - Because "Return True" has no exception, a function that meets every rule can never charge a rejected amount.
4. **Rule 5 is ambiguous in two ways.** It doesn't say whether the wait must be one `sleep(2)` call or just 2 seconds in total, or whether the 4 seconds before the third attempt are counted on their own or cumulatively. I chose per-gap totals; the example fixes a single `sleep(2)` for its script. It also gives no wait length for attempts after the third.
5. **Gap in the requirements.** The prompt's opening sentence ("charges a customer's card … retrying when the service fails") is not a requirement. So only rule 7 and the example oblige the function to charge at all; a function that returns False without charging meets rules 1–6.
6. **Frame gaps.**
   - F-ZERO doesn't force `op` to be 1 or 2 at a call, so the spec-only analyses allow calls that are neither a charge nor a sleep.
   - Outcome 2 lumps together other exceptions, more than 8 calls, and not finishing. So I recognise the cut-off as "outcome 2 after 8 calls", which can't be told apart from an exception raised right after the 8th call.
