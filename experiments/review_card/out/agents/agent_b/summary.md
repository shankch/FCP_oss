I wrote `formal/agent_b.yaml`. `fcp lint` reports it clean, and I read the `fcp explain` output back to check that each item means what I intended. I did not run `fcp check`, so nothing has confirmed that the example scenario is actually reachable.

**Items: 29 in total** (27 properties, 1 assumption, 1 scenario, no don't-cares).
- **Model:** a ghost `bal` holds the card's balance before each call, ranges from 0 to 50,000, starts at 0, and is driven only by `op` and `amount`. A second ghost, `calls`, counts calls on a new card and is used for the first-call and example items. Every output is checked against the model: `outcome` and `bonus` for load, `outcome` and `spent` for spend, and `outcome` and `balance` for balance().
- **State changes:** the effects of a load, a spend, a spend that isn't covered, and a call that raises are each also checked on a balance() call made right after. `RB-BAL-1` checks `balance == bal` at every balance() call.
- **Assumption:** `RB-A-OP` (`op != 0`), taken from R-IF-1: every call is one of the three methods.
- **Example:** R-EX-1 is both a scenario (the sequence is possible) and a property (on a new card, balance() then returns 1500).
- **Ghost timing:** I assumed the ghosts hold their initial values in the first call after a reset. That follows from IR_spec §4.4 and frame.md, but no tool run has confirmed it.

**Left unformalized (3):**
- **R-UNIT-1** is only a definition of units; it's `covered_by` the items that use the cent constants.
- **R-FR-1 and R-FR-2** are the adapter's frame rules F-ZERO and F-OTHER. design.yaml already adds them to every set, so I didn't restate them.

**Readings taken (20 decisions recorded):**
- A call that raises ValueError leaves the balance unchanged (reading 1). The text never says this; I followed the Python convention that a raised call is rejected.
- Rule 1 applies to spend as well as load. For spend, rule 5 then only covers amounts from 1 to 50,000.
- "Covers" means the balance is at least the amount.
- The bonus is a flat 500 cents and is added to the balance.
- The $500 cap is absolute and counts the bonus, so a load that the bonus would push over the cap raises and earns nothing.

**Problems in the specification:**
1. **Rule 1 contradicts rule 5 for spend.** Read literally, spend(0) must both raise and return True (every balance covers 0), and spend(50001) must both raise and return False. I resolved this by treating rule 1 as a check that runs before rule 5, and said so in the notes.
2. **Rule 3 contradicts rule 4.** If the cap ignores the bonus, load(50000) on a new card leaves 50,500, which breaks "never more than $500.00". If the cap counts the bonus, the spec isn't contradictory, but any load of 49,501 to 50,000 cents always raises, even though rule 1 allows loads up to 50,000. Capping or dropping the bonus would break "every load … earns".
3. **The spec never says what a raised call does to the balance.** The cap rule's wording ("would take it over") suggests the load simply doesn't happen, but that is an inference.
4. **"Earns a $5.00 bonus on the card"** doesn't say whether the bonus goes into the balance. "Adds `amount` to the balance" read on its own would mean it doesn't. I read it as going into the balance.