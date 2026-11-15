I wrote `formal/agent_b.yaml` (set `agent_b`). It has 11 items, `fcp lint` is clean, and the `fcp explain` rendering reads as intended for every item.

**Items**
- **7 properties:**
  - LB-ERR-USER and LB-ERR-TIME (R-ERR-1)
  - LB-RET-1 (R-RET-1)
  - LB-MAX-1 (R-MAX-1)
  - LB-COUNT-1 (R-COUNT-1)
  - LB-FAIR-1 (R-FAIR-1)
  - LB-PEN-1 (R-PEN-1)
- **4 scenarios:** LB-EX-1 is the spec's example. LB-ERR-S1, LB-MAX-S1 and LB-PEN-S1 each pin down my reading of one ambiguity listed in requirements.yaml.
- **Model:** one customer `u` (a rigid over every id 0 to 1,000). Ghosts hold the previous call's `now`, the times of `u`'s three most recent allowed attempts, the time of `u`'s most recent denial, and a flag for whether `u`'s calls are still in time order. The ghosts follow what the object actually returned, not a predicted answer, because predicting the answer would mean settling the contradiction below.

**Left unformalized** (both are definitions): R-SIG-1 (covered by LB-RET-1) and R-IN-1 (covered by LB-ERR-USER, LB-RET-1 and the window items). R-FR-1 is already formalized by the frame item F-ZERO, so I did not restate it.

**Readings chosen (each stated in a note)**
- "The previous call" is the call immediately before, from any customer, even if it raised.
- "60 seconds" means 60 consecutive whole seconds, so attempts at t and t+60 do not fall in the same 60 seconds.
- The 10 seconds after a denial at T are T to T+9, so an attempt at T+10 is not penalised.
- Every denial, including one caused by the penalty, starts a new 10 seconds.
- A call that raised is neither allowed nor denied.
- Rule 1 comes first: rules 4 and 5 apply only to calls that do not raise.

**Problems in the specification**
1. **Rules 4 and 5 contradict each other, under any reading of the boundaries.** Example: allowed at 0, 50 and 51; denied at 54 by the limit; then at 60 rule 4 says allow and rule 5 says deny.
2. **Rule 5 never adds anything.** When calls are in time order, rules 2 and 4 already decide every valid call, so rule 5 either repeats their answer or contradicts rule 4.
3. **The literal "previous call" lets time go backwards.** A valid call can be earlier than earlier valid calls, after a call that raised. Rules 2 and 4 then contradict each other: allowed at 50, 50, 50; a call at 10 raises; at 20 rule 4 says allow and rule 2 says deny.
4. **The window edges are ambiguous.** Rules 2 and 4 must be read the same way, or they contradict at exactly 60 seconds. The 10-second edge, and whether a penalty denial restarts the penalty, are unclear too.
5. **Smaller gaps:** rule 3 repeats what rules 2 and 4 already say, and the text says neither whether raised calls count nor that rule 1 takes priority.

**Limitation you should know about**
- My first version counted windows exactly using a second rigid over every second. `fcp code` refused it: 65.6 million rigid cases against its limit of 4,096.
- The current version uses only the customer rigid (1,001 cases). It is exact whenever a customer's calls are in time order, which I checked on 179,335 random calls.
- When a customer's calls go back in time after a raised call, LB-FAIR-1 and LB-COUNT-1 stop checking that customer. LB-MAX-1 and LB-PEN-1 keep checking: they are never stricter than the text, but can miss a violation involving older attempts.

**Extra checks beyond lint and explain:** I ran `fcp code --small` on two throwaway implementations of my own readings. One lets the penalty win when the rules collide; the other lets rule 4 win. Each failed only one side of problem 1, on the same call sequence (0, 36, 36 allowed, 55 denied, 64), and everything else passed. The bounded model checking step reached all four scenarios. I then deleted these implementations and fcp's `.fcp` cache, so the workspace holds only the original files plus `formal/agent_b.yaml`.
