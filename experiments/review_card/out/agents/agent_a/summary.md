I've written `formal/agent_a.yaml`. `fcp lint` reports it clean, and I read the `fcp explain` output for every item; each one says what I meant. I didn't run `fcp check`, so the conflicts below and whether the example scenario can be reached are my own reasoning, not machine-confirmed.

**What's in the set:** 21 items: 20 properties and 1 scenario. They use 9 named expressions and 3 pieces of tracked model state. One is the card's balance, which is internal to the object, so this was the only way to state the balance rules. One is a "known" flag, explained below. One is a call counter, used only by the example scenario to pin "a new card". There are also 20 decisions, one for each flagged phrase.

**Requirements left unformalized (4), all with `covered_by`:**
- **R-IF-1** (class and method names): this is about the code's structure, not the trace. The adapter fixes the names, and a missing method shows up as an "other exception" outcome, which the signature properties RA-IF-2/3/4 rule out.
- **R-UNIT-1** (everything is in cents): a definition. It's built into every constant ($500 = 50000, $100 = 10000, $5 = 500).
- **R-FR-1 / R-FR-2**: these are the adapter's frame rules. F-ZERO and F-OTHER already add them to every set.

**Problems in the specification:**
1. **Rule 1 contradicts rule 5.** Rule 1 refers to `amount`, which `spend` also takes, so read literally it covers `spend`. But `spend(0)` must then both raise ValueError and return True (every balance covers 0). Likewise `spend(50001)` must both raise and return False. As instructed, I kept the contradiction rather than repairing it, and flagged it in the notes of RA-VAL-3/RA-SPD-2 and RA-VAL-4/RA-SPD-3. `spend(0)` as the very first call on a card already forces it, so no implementation can satisfy this set.
2. **The cap clashes with the bonus.** If rule 3 ignores the bonus, `load(50000)` on a new card leaves 50,500, which breaks "never more than $500.00". I counted the bonus, so that load raises ValueError. That's the only reading under which "never" and "every load of $100 or more earns $5" both hold.
3. **The prompt never says what a rejected call does to the balance.** Taking that literally, after a load that rules 1 or 3 reject, the model treats the balance as unknown. The balance-dependent checks pause until the next `balance()` call returns normally, then resume from the value it shows. This makes the set noticeably weaker after any rejected load. The usual "a rejected call leaves the balance unchanged" reading is the other option, which `fcp review` will probe.
4. **Other readings I took:**
   - "covers it" means balance ≥ amount.
   - The bonus is a flat $5 per load of $100 or more, and it's added to the balance.
   - The example (`load(2000)`, `spend(500)`, `balance()` returns 1500) must be on a new card. The prompt only implies this.
5. **One inference beyond the decomposer's texts (RA-LOAD-1).** Those texts only constrain loads "that do not raise ValueError", so nothing in them forbids raising on a valid load. I added RA-LOAD-1, which requires a load that neither rule rejects to complete normally. I based it on rules 2 and 4, which say what such a load does and returns.