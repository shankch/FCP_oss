"""Reference implementation of P-INVOICE-1 (gold reading).  At the prompt's
conflict it keeps rules 3 to 5 and lets rule 6 give way: the total is the
sum of the lines."""


def invoice(items, member):
    if not items or any(it["qty"] == 0 for it in items):
        raise ValueError("an invoice needs items, each with a quantity of at least 1")
    lines = [it["price"] * it["qty"] - (it["price"] * it["qty"] // 10 if member and not it["sale"] else 0)
             for it in items]
    offsale = sum(it["price"] * it["qty"] for it in items if not it["sale"])
    discount = offsale // 10 if member else 0
    return {"lines": lines, "discount": discount, "total": sum(lines)}
