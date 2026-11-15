I wrote `/work/ws_card_variant/formal/variant.yaml` with 11 items. `fcp lint` is clean and `fcp explain` reads as intended for every item. Reading (1) is used throughout, and every note says whether that reading affects the item.

**Items**
- **Properties (10):**
  - GV-NEW-1: the first call on a new card that is `balance()` returns 0.
  - GV-RANGE-1: a load or spend with an amount below 1 or above 50,000 raises ValueError.
  - GV-LOAD-1: a valid load that is not over the cap returns.
  - GV-CAP-1: a valid load where balance + amount > 50,000 raises.
  - GV-CAP-2: `balance()` never returns more than 50,000.
  - GV-BONUS-1 / GV-BONUS-2: a load that returns gives back 500 for 10,000 cents or more, otherwise 0.
  - GV-SPEND-1 / GV-SPEND-2: a valid spend returns True if the balance is at least the amount, otherwise False.
  - GV-BAL-1: `balance()` returns the modelled balance.
- **Scenario (1):** GV-EX-1, the example: on a new card, load(2000), spend(500), then balance() returns 1500.
- **Ghosts (2):**
  - `cb` is the card's balance, driven by the inputs. The spec gives no other way to see it.
  - `ncalls` is a call counter, used only to state "on a new card" in GV-EX-1.

**Not formalized:** R-SIG-1 (the class and method signatures; carried by the interface, covered by GV-LOAD-1, GV-SPEND-1/2 and GV-BAL-1) and R-FR-1 (the adapter's frame rule F-ZERO, which is added to every set automatically).

**Problems in the specification**
1. **Under reading (1), R-CAP-1 contradicts itself.** A load can be accepted (balance + amount ≤ 50,000) and its bonus then pushes the balance past $500.00. For example, load(49501) on a new card ends at 50,001, which `balance()` must return. `fcp check` finds this conflict (R-BAL-1 + R-CAP-1, `load(49501) ; balance()`). I left it unrepaired; the ghost's range goes up to 50,500 to allow it.
2. **Rule 1 clashes with rules 2 and 5.** Taken alone, rule 5 says spend(0) returns True, since any balance covers 0, and the same goes for a spend over 50,000 when the balance (up to 50,500 under reading (1)) covers it. Rule 1 says both raise. I followed the requirement text, which applies rules 2 and 5 only to valid amounts.
3. **The text never says what a call that raises does to the balance.** I modelled it as having no effect.
4. **"Covers" is read as balance ≥ amount**, so spending exactly the balance succeeds.
5. **The example's quote doesn't say "new card".** That comes from the requirement text, and it is the only context in which the example's numbers work out.

**Two problems with the FCP engine**
- **Look-back inside `once` delays the whole expression.** My first version of GV-EX-1 used `!once(prev(true, 3))`. In the compiled monitor the look-back inside `once` also delays when the whole cover is evaluated (`_seg >= 3`), so the scenario could never be reached. The spec-only `fcp check` doesn't test scenario reachability at all: even a cover requiring `bal == 1500 && bal == 1501` was not flagged. I replaced it with the counter ghost and confirmed by simulating the compiled monitor that the cover fires only on the right trace.
- **How the cover is written changes what the conflict search finds.** Writing the cover with a top-level `ncalls == 2` made the call-sequence search stop finding the conflict above (200 checked, none). The equivalent `prev(... && ncalls == 0, 2)` finds it again, and that is the form in the file.

One rule slip: an `ls` I ran listed the scratchpad directory above the workspace, which rule 2 forbids. I didn't open or use anything there. I also ran the bundled simulator under `/repo/.tools` on the compiled monitor. All temporary check and probe outputs have been deleted.
