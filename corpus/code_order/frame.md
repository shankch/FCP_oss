# FCP interface adapter, version 0.6

This document defines how one run of a Python function that calls services
it imports becomes a trace that the FCP engines can check. The function is
run with stand-ins for `inventory`, `payments` and `shipping`: every call it
makes on them is recorded and answered from a script. This document is part
of the adapter, not of the prompt.

## Cycles

A reset starts a run of `place_order(order_id, sku, qty, amount)`. Every
later cycle is one call the function makes on a service, in order, and then
one cycle for the return. After the return, the trace stays at the return
until the next reset, which starts another run. So `prev(x)` is the value of
`x` at the previous call in the same run, and `once`, `hist` and `since`
range over the current run.

## Inputs

| Signal | Width | Meaning in a cycle |
|---|---|---|
| `order_id` | 20 bits | the `order_id` argument, the same in every cycle of a run |
| `sku` | 16 bits | the `sku` argument, the same in every cycle of a run |
| `qty` | 8 bits | the `qty` argument, the same in every cycle of a run |
| `amount` | 21 bits | the `amount` argument, the same in every cycle of a run |
| `answer` | 2 bits | at a call of `inventory.reserve`, `payments.charge` or `shipping.book`, what the service answered: 0 `"ok"`, 1 `"refused"`, 2 it raised its error; it means nothing at any other cycle |

## Outputs

| Signal | Width | Meaning in a cycle |
|---|---|---|
| `phase` | 1 bit | 0 at a call on a service, 1 once the function has returned |
| `op` | 3 bits | at a call: 1 `inventory.reserve`, 2 `payments.charge`, 3 `shipping.book`, 4 `payments.refund`, 5 `inventory.release`; 0 once returned |
| `r_sku`, `r_qty` | 16, 8 bits | at a call of `inventory.reserve`: its arguments (0 otherwise) |
| `c_order`, `c_amount` | 20, 21 bits | at a call of `payments.charge`: its arguments (0 otherwise) |
| `b_order` | 20 bits | at a call of `shipping.book`: its argument (0 otherwise) |
| `f_order`, `f_amount` | 20, 21 bits | at a call of `payments.refund`: its arguments (0 otherwise) |
| `l_sku`, `l_qty` | 16, 8 bits | at a call of `inventory.release`: its arguments (0 otherwise) |
| `outcome` | 2 bits | once returned: 0 it returned True or False; 1 it raised `ValueError`; 2 it raised any other exception, made more than 8 calls, or did not finish; 3 it returned anything else. 0 at a call |
| `result` | 1 bit | once returned with outcome 0: the returned value |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-END: once `phase` is 1 it stays 1, with the same `outcome` and `result`.
- F-ZERO: at a call, `outcome` is 0 and `result` is false; once returned, `op` is 0; `result` is false unless `outcome` is 0.
- F-LIMIT: a run makes at most 8 calls: after 8 calls, the next cycle is the return (a run that would go on ends there, with `outcome` 2).
- F-ANS: `answer` is 0 at every cycle that is not a call of `inventory.reserve`, `payments.charge` or `shipping.book`.
