# FCP interface adapter, version 0.5

This document defines how one run of a Python function that acts through an
interface becomes a trace that the FCP engines can check. The function
receives `api`, a stand-in for the payment service that records every call
and answers it from a script. This document is part of the adapter, not of
the prompt.

## Cycles

A reset starts a run of `charge_order(api, order_id, amount)`. Every later
cycle is one call the function makes on `api`, in order, and then one cycle
for the return. After the return, the trace stays at the return until the
next reset, which starts another run. So `prev(x)` is the value of `x` at the
previous call in the same run, and `once`, `hist` and `since` range over the
current run.

## Inputs

| Signal | Width | Meaning in a cycle |
|---|---|---|
| `order_id` | 20 bits | the `order_id` argument, the same in every cycle of a run |
| `amount` | 21 bits | the `amount` argument, the same in every cycle of a run |
| `answer` | 2 bits | at a call of `api.charge`, what the service answered: 0 `"ok"`, 1 `"declined"`, 2 `"error"`; it means nothing at any other cycle |

## Outputs

| Signal | Width | Meaning in a cycle |
|---|---|---|
| `phase` | 1 bit | 0 at a call on `api`, 1 once the function has returned |
| `op` | 2 bits | at a call: 1 `api.charge`, 2 `api.sleep`; 0 once returned |
| `c_order` | 20 bits | at a call of `api.charge`: its first argument (0 otherwise) |
| `c_amount` | 21 bits | at a call of `api.charge`: its second argument (0 otherwise) |
| `s_seconds` | 8 bits | at a call of `api.sleep`: its argument (0 otherwise) |
| `outcome` | 2 bits | once returned: 0 it returned True or False; 1 it raised `ValueError`; 2 it raised any other exception, made more than 8 calls, or did not finish; 3 it returned anything else. 0 at a call |
| `result` | 1 bit | once returned with outcome 0: the returned value |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-END: once `phase` is 1 it stays 1, with the same `outcome` and `result`.
- F-ZERO: at a call, `outcome` is 0 and `result` is false; once returned, `op` is 0; `result` is false unless `outcome` is 0.
- F-LIMIT: a run makes at most 8 calls: after 8 calls, the next cycle is the return (a run that would go on ends there, with `outcome` 2).
