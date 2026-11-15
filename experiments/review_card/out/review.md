# FCP review

Certified: 7 requirements. Questions: 24.

## Certified (the code meets them under both readings, which agree; no conflict)
- R-IF-2: A call of load(amount) that does not raise ValueError returns an int.
- R-IF-3: A call of spend(amount) that does not raise ValueError returns a bool (True or False).
- R-IF-4: A call of balance() returns an int.
- R-INIT-1: A newly created GiftCard has a balance of 0 cents.
- R-BON-3: A call of load(amount) that does not raise ValueError and earns no bonus returns 0; in particular a load of less than 10,000 cents returns 0.
- R-BAL-1: A call of balance() returns the card's current balance in cents, as left by the earlier calls on the same card.
- R-EX-1: On a new card, the calls load(2000), spend(500) and balance(), in that order, are possible, and that balance() returns 1500.

## Questions
1. **conflict** (R-SPD-2, R-VAL-3): no implementation can meet these requirements on these calls: which one gives way?
   - `spend(0)`
2. **open** (balance): the request allows 0 or 1: which is meant?
   - `load(0); balance()`
3. **open** (outcome): the request allows 0 or 1: which is meant?
   - `load(0); spend(0); load(2000)`
4. **depends** (R-BON-2, R-CAP-2, R-SPD-2, R-SPD-3, R-VAL-3, R-VAL-4): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
5. **readings** (R-CAP-2): the two readings of this requirement disagree (no separating call was found within the budget): which is meant?
6. **readings** (R-SPD-2): the two readings of this requirement disagree (no separating call was found within the budget): which is meant?
7. **readings** (R-SPD-3): the two readings of this requirement disagree (no separating call was found within the budget): which is meant?
8. **ambiguity** (R-VAL-1, R-VAL-2, R-VAL-3, R-VAL-4): "Raise ValueError" can mean: a call that raises ValueError leaves the balance unchanged / the request does not say what happens to the balance when a call raises ValueError. Which is meant?
9. **ambiguity** (R-VAL-3): "Raise ValueError if `amount` is less than 1" can mean: the rule covers every method with an amount argument, so spend(0) raises ValueError; this contradicts R-SPD-2, under which any balance covers 0 and spend(0) returns True / the rule covers load only (or rule 5 takes precedence for spend), so spend(0) returns True by R-SPD-2. Which is meant?
10. **ambiguity** (R-VAL-4): "or more than 50,000" can mean: the rule covers every method with an amount argument, so spend(50001) raises ValueError; this contradicts R-SPD-3, under which a balance of at most 50,000 cents (R-CAP-1) never covers 50,001 and spend(50001) returns False / the rule covers load only (or rule 5 takes precedence for spend), so spend(50001) returns False by R-SPD-3. Which is meant?
11. **ambiguity** (R-LOAD-1): "adds `amount` to the balance" can mean: the balance grows by amount plus any bonus the load earns (R-BON-1) / the balance grows by exactly amount and any bonus is not part of the balance; this contradicts R-BON-1 if 'on the card' means credited to the balance. Which is meant?
12. **ambiguity** (R-CAP-1): "The balance is never more than $500.00" can mean: the cap is absolute and includes bonuses: no call ever leaves the balance above 50,000 cents / only loaded amounts are capped and a bonus may take the balance above 50,000 cents (e.g. load(50000) on a new card leaves 50,500); this contradicts the literal 'never' and is what R-BON-1 forces when R-CAP-2 counts only amount. Which is meant?
13. **ambiguity** (R-CAP-2): "a load that would take it over" can mean: balance + amount > 50,000 (the bonus is not counted); together with R-BON-1 this lets a load such as load(50000) on a new card leave 50,500, contradicting R-CAP-1 / balance + amount + the bonus the load would earn > 50,000 (the bonus is counted), e.g. load(50000) on a new card raises ValueError. Which is meant?
14. **ambiguity** (R-CAP-2): "raise ValueError for a load" can mean: the rejected load has no effect on the balance / the balance after the rejected load is not specified beyond R-CAP-1. Which is meant?
15. **ambiguity** (R-BON-1): "a $5.00 bonus" can mean: a flat 500 cents per qualifying load, whatever its size / 500 cents for every full $100.00 in the load (e.g. 1,000 cents for load(20000)). Which is meant?
16. **ambiguity** (R-BON-1): "on the card" can mean: the bonus is added to the balance, so balance() includes it and spend can use it / the bonus is recorded on the card separately and is not part of the balance returned by balance(). Which is meant?
17. **ambiguity** (R-BON-1): "Every load of $100.00 or more earns a $5.00 bonus" can mean: every qualifying load that succeeds earns the full 500 cents even when that takes the balance over 50,000 cents; this contradicts R-CAP-1 (e.g. load(50000) on a new card would leave 50,500) / a qualifying load whose amount plus bonus would take the balance over 50,000 cents raises ValueError and earns nothing (R-CAP-2 counts the bonus) / the bonus is cut so that the balance stops at 50,000 cents / the bonus is forfeited when it would take the balance over 50,000 cents. Which is meant?
18. **ambiguity** (R-BON-2): "the bonus it earned" can mean: 500 for every successful load of at least 10,000 cents / the bonus actually added to the balance, which is less than 500 when the $500.00 cap cuts it / 500 for every full $100.00 in the load. Which is meant?
19. **ambiguity** (R-SPD-1, R-SPD-2): "covers it" can mean: the balance is at least amount (spending the whole balance is allowed) / the balance is strictly more than amount. Which is meant?
20. **code** (R-SPD-2): the code breaks this requirement here (replayed): a bug, or a reading to change?
   - `spend(0) -> raised ValueError`
21. **ambiguity** (R-SPD-2): "returns True if the balance covers it" can mean: for every amount, including 0: any balance covers 0, so spend(0) returns True; this contradicts R-VAL-3 / only for amounts that pass rule 1 (1 to 50,000); spend(0) raises ValueError by R-VAL-3. Which is meant?
22. **code** (R-SPD-3): the code breaks this requirement here (replayed): a bug, or a reading to change?
   - `spend(50001) -> raised ValueError`
23. **ambiguity** (R-SPD-3, R-SPD-4): "otherwise" can mean: the balance is less than amount / the balance is at most amount. Which is meant?
24. **ambiguity** (R-SPD-3): "otherwise it returns False" can mean: for every amount the balance does not cover, including amounts above 50,000: spend(50001) returns False; this contradicts R-VAL-4 / only for amounts that pass rule 1 (1 to 50,000); spend(50001) raises ValueError by R-VAL-4. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-VAL-3, "Raise ValueError if `amount` is less than 1": both took "the rule covers every method with an amount argument, so spend(0) raises ValueError; this contradicts R-SPD-2, under which any balance covers 0 and spend(0) returns True"
- R-VAL-4, "or more than 50,000": both took "the rule covers every method with an amount argument, so spend(50001) raises ValueError; this contradicts R-SPD-3, under which a balance of at most 50,000 cents (R-CAP-1) never covers 50,001 and spend(50001) returns False"
- R-LOAD-1, "adds `amount` to the balance": both took "the balance grows by amount plus any bonus the load earns (R-BON-1)"
- R-CAP-1, "The balance is never more than $500.00": both took "the cap is absolute and includes bonuses: no call ever leaves the balance above 50,000 cents"
- R-CAP-2, "a load that would take it over": both took "balance + amount + the bonus the load would earn > 50,000 (the bonus is counted), e.g. load(50000) on a new card raises ValueError"
- R-BON-1, "a $5.00 bonus": both took "a flat 500 cents per qualifying load, whatever its size"
- R-BON-1, "on the card": both took "the bonus is added to the balance, so balance() includes it and spend can use it"
- R-BON-1, "Every load of $100.00 or more earns a $5.00 bonus": both took "a qualifying load whose amount plus bonus would take the balance over 50,000 cents raises ValueError and earns nothing (R-CAP-2 counts the bonus)"
- R-BON-2, "the bonus it earned": both took "500 for every successful load of at least 10,000 cents"
- R-SPD-1, "covers it": both took "the balance is at least amount (spending the whole balance is allowed)"
- R-SPD-2, "covers it": both took "the balance is at least amount (spending the whole balance is allowed)"
- R-SPD-3, "otherwise": both took "the balance is less than amount"
- R-SPD-4, "otherwise": both took "the balance is less than amount"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_b, RB-A-OP (R-IF-1): every call meets `op != 0`

## Outside this review
A review judges what calls return and do. The request also asks for these, which were marked non-functional when it was split into requirements. They are not certified, and nothing is said about them except where the report above names one:
- R-IF-1: The code is a Python class named GiftCard with three methods: load(amount), spend(amount) and balance().
