I wrote `/work/ws_card_agent_b/formal/agent_b.yaml`. `fcp lint` reports no errors, and `fcp explain` reads back as I intended. I also ran the spec-only `fcp check`: the set is consistent, has no tautologies, and every output (`outcome`, `earned`, `ok`, `bal`) is determined. All four scenarios, including the example, are reachable.

**Items:** 19 in total, 15 properties and 4 scenarios, plus the frame rule F-ZERO, which the engine adds to every set.
- **Model:** a ghost `cb` holds the card balance, driven only by `op` and `amount`. It starts at 0, an accepted load adds the amount plus its bonus, and a covered spend subtracts the amount; every other call leaves it unchanged. A second ghost `calls` counts the calls on the current card, so "new card" can be expressed.
- **Outputs against the model:** every output is checked against `cb`. The central check is GB-BAL-1: `balance()` returns `cb`.
- **Per-requirement effects:** properties for loads, bonuses and spends show each rule's effect on the next `balance()` call.

**Unformalized:** none. R-SIG-1 (the class and method signatures) became the property "a method call returns a value of its declared type or raises ValueError". R-EX-1 is both a scenario and a guarantee: on a new card, `load(2000)`, `spend(500)`, `balance()` returns 1500. R-FR-1 is covered by the frame rule F-ZERO.

**Problems in the specification (each noted in the item):**
1. **Rule 3, does the cap include the bonus?** The requirements file already flags this. I chose "balance + amount + bonus > 50,000 raises". The other reading contradicts "the balance is never more than $500.00": a load could return and leave the balance over $500.00. The consequence is that any load of 49,501 to 50,000 cents always raises, even on a new card, although rule 1 allows those amounts.
2. **Rule 1 against rule 5:** read alone, rule 5 has `spend(0)` return True and `spend(50001)` return False, while rule 1 says both raise. I let rule 1 win.
3. **A call that raises:** the prompt never says what it does to the balance. I modelled the balance as unchanged. That is the only reading that respects the $500.00 cap and doesn't invent a partial effect.
4. **Readings of "covers" and "every load":** I read "the balance covers it" as balance ≥ amount, so an equal balance covers it. I read "every load of $100.00 or more earns a bonus" as applying only to loads that return; a load that raises earns nothing.

**Not constrained:** op 0, which is not a method. I added no assumption to exclude it.
