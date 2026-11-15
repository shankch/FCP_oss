I wrote `formal/variant1.yaml` with 13 items covering all 13 requirements. `fcp lint` reports no errors, and I read the `fcp explain` output back to confirm each item says what I meant. I did not run `fcp check`, so the contradiction described below is my own working, not a tool result.

**Items (13):** 12 properties and 1 scenario, with no ghosts. A few shared definitions do the work: whether the arguments are in range, the two discounts added up and capped at 30%, and the exact discounted price.
- **R-RET-1, R-ERR-1:** valid arguments return a pair; out-of-range arguments raise ValueError.
- **R-MEM-1, R-COUP-1, R-STACK-1 (two items: under the cap, at the cap):** each says the price is within one cent of the discounted amount. Which cent is decided separately by R-ROUND-1.
- **R-ROUND-1:** the price is at most half a cent from the exact discounted price, so either neighbour is allowed at exactly half a cent.
- **R-SHIP-1 (two items):** 499 cents under a 5,000-cent subtotal, free at 5,000 or more.
- **R-MONO-1:** compares two consecutive calls, which frame.md allows to be any pair of calls.
- **R-EX-1:** both a guarantee and a scenario showing the call can happen.

**Readings taken:** all reading 1, as instructed, recorded under `decisions` and in each affected note:
- "Discounts stack": the percentages add up.
- "the nearest cent": at exactly half a cent, either neighbour.
- "Orders under $50": the subtotal before discounts.

**Left unformalized (5), all for the same reason:** they are definitions rather than behaviour, and each is realized elsewhere.
- **R-SIG-1:** the function signature, fixed by design.yaml; covered by the R-RET-1 item.
- **R-IN-1, R-IN-2, R-IN-3:** argument ranges and meanings, captured in the shared definitions and covered by the items that use them. They are not assumptions, because rule 1 requires out-of-range calls to be handled.
- **R-FR-1:** already the frame item F-ZERO, which every set includes automatically.

**Problems in the specification:**
1. **Rules 6 and 7 contradict each other** under either reading of "Orders under $50". A non-member with no coupon is charged 4,999 + 499 = 5,498 at a 4,999-cent subtotal, but only 5,000 at 5,000 cents. So adding items lowers the amount charged. I formalized both rules as written and noted the conflict rather than repairing it.
2. **Coupons of 31–50% can never take their stated percentage off.** Rule 3 says a coupon takes its percentage off, but rule 4's 30% cap overrides it, even though those values are valid inputs. For members the same happens above 20%. I formalized rule 3 only up to 30% and said so in the note.
3. **The 30% cap conflicts with rounding if it applies to the final price.** For example, 30% off a 3-cent cart is 2.1 cents, which rounds to 2, an actual discount of 33%. I read the cap as applying to the discount percentage before rounding, and noted it.
4. **The cap itself is open to interpretation.** "Never more than 30%" only sets an upper limit. I read it as "the total discount is exactly 30% whenever the sum exceeds 30" and noted that choice.