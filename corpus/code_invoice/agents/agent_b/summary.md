I wrote `/work/ws_invoice_agent_b/formal/agent_b.yaml`. `fcp lint` reports clean, and the `fcp explain` rendering of every item says what I intended.

**Items: 12 formal items, plus 3 requirements under `unformalized`.** The frame item F-ZERO is added to the set automatically.
- 11 properties:
  - IB-RET-1: a valid call returns a dict.
  - IB-ERR-1 and IB-ERR-2: empty items, or an item with quantity 0, raises ValueError.
  - IB-LINES-1 and IB-LINES-2: one line per item, and each line's amount.
  - IB-MEM-1: a member's line not on sale gets 10% off.
  - IB-DISC-1 and IB-DISC-2: the discount for members and for everyone else.
  - IB-SUM-1: total is the sum of lines.
  - IB-TOT-1: total is price times quantity of all items minus discount.
  - IB-EX-2: the example's answer is the only one allowed.
- 1 scenario: IB-EX-1, the example must be possible.
- Model: the expected values are computed from the current call's arguments (`defs`, plus a rigid item index `k`), and each output is checked against them. I used no ghost state: frame.md says calls are independent, so there is nothing to carry from one call to the next.
- Rounding: FCP-PL has no division, so "10% rounded down" is written as ten times the value, `x - x % 10`, compared with ten times the output.

**Left unformalized:**
- R-SIG-1 and R-IN-1 are definitions of the signature and the item fields. The interface encoding realizes them, and R-SIG-1 is marked `covered_by: [IB-RET-1]`.
- R-FR-1 is the frame's own definition. F-ZERO already carries it in every set, so restating it would duplicate it.

**Problems in the specification:**
1. **The rules contradict each other.** I read rule 4 literally: sum first, then round down once, so discount = floor(sum of price × qty of non-sale items / 10). Rules 2, 3 and 5 instead round each line separately. For a member with two or more items not on sale whose cents-digits (price × qty mod 10) add up to 10 or more, no answer meets every rule. Example: two items of 9 cents, quantity 1. The lines are [9, 9], so rule 5 gives total 18, but the discount is 1, so rule 6 gives 17. Rule 1 does not reject this call, so the function must return something, and nothing it returns is correct. I left this as written, not repaired.
2. **"Rounded down to the cent" in rule 3 is ambiguous.** It could round the line's discount down or the discounted line down. I took the discount being rounded down, floor(price × qty / 10), which is also how the example works out: 3998 gives 3599, not 3598. "Every line" is read as price × qty of the line, not per unit.
3. **Some cases are only implied.** No rule states that sale lines and non-members' lines have no discount, but no rule gives them one either. I read their discount as 0, which matches the decomposer's text.
4. **The example settles only one of the two ambiguities.** It has a single item, so it supports reading 2 but cannot tell the two roundings of rule 4 apart.

Two smaller reading choices, both recorded in the item notes:
- The rules about what the returned dict contains apply only when the call returns (`outcome == 0`). Whether it returns is covered by IB-RET-1 and IB-ERR-1/2.
- R-SUM-1 and R-TOT-1 refer to the returned `lines` and `discount`, as the text does, rather than to the model's values.
