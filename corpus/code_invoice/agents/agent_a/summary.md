I wrote `/work/ws_invoice_agent_a/formal/agent_a.yaml`. `fcp lint` reports clean, and the `fcp explain --set agent_a` output matches what each item is meant to say. I did not run `fcp check`, so the contradiction below comes from working the arithmetic by hand, not from the tool.

**Items: 11** (10 properties, 1 scenario). There are no assumptions, because the frame already keeps out-of-range calls out of the trace, and no don't-cares, because the frame rule F-ZERO fixes the outputs whenever the call does not return the dict.
- **R-RET-1:** a call with at least one item and no quantity of 0 must return the dict (outcome 0).
- **R-ERR-1:** a call with no items, or with a quantity of 0, must raise ValueError (outcome 1).
- **R-LINES-1** (two items): the returned dict has one line per item, and every line without a member discount is exactly price times quantity.
- **R-MEM-1:** for members, each line not on sale is reduced by 10% of price times quantity, rounded down. The formula is written without division as `10*d == x - x % 10`.
- **R-DISC-1** (two items): members get 10% of the summed not-on-sale amount, rounded down once; everyone else gets 0.
- **R-SUM-1:** total equals the sum of the lines.
- **R-TOT-1:** total equals the summed price times quantity of all items, minus the discount.
- **R-EX-1:** the worked example appears twice, as a property (that call must give that result) and as a scenario (that result must be possible).

Rules 2 to 6 describe the returned dict, so I made them apply only when the call returns it (outcome 0). Whether a call must return is left to R-RET-1.

**Unformalized: 3**
- **R-SIG-1** (the function signature) and **R-IN-1** (what an item is) are definitions. The interface in `design.yaml` and the adapter already encode them, so there is no behaviour to state.
- **R-FR-1** is the adapter's frame rule F-ZERO, which is added to every set. It is recorded as covered by F-ZERO.

**Problems in the specification**
1. **Rule 4 contradicts rules 2, 3, 5 and 6.** Read literally ("summed and rounded down"), the member discount is 10% of the summed amount, rounded down once. But rules 2, 3, 5 and 6 together force the discount to equal the sum of the per-line rounded-down discounts. These differ whenever the dropped fractions add up to a cent or more. Example: a member buys two items not on sale at price 5, quantity 1. The lines are [5, 5], so rule 5 gives a total of 10. Rule 4 gives a discount of 1, so rule 6 gives a total of 9. I kept the literal reading, did not repair it, and noted it in the R-DISC-1 and R-TOT-1 items. The worked example has a single item, so it cannot tell the two readings apart.
2. **Rule 3's rounding is ambiguous.** It could mean the line's discount is rounded down, or the discounted line amount is. I chose the discount: rule 2 builds a line by subtracting its discount, and the example agrees (3998 gives 3599; the other reading gives 3598).
3. **The return quote conflicts with rule 1.** "The function returns a dict" is unconditional, but rule 1 says some calls raise. I read the quote as applying only to calls that rule 1 does not reject, and said so in the item's note.
