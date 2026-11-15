# FCP change adapter, version 0.4

This document defines how calls of a changed Python function become a trace
that the FCP engines can check. The function is treated as a chip without
memory, as for any function: its arguments are input signals, its result is
on output signals, and each cycle is one call. A change adds one thing: the
code before the change is called with the same arguments, and its answer is
on three more input signals. A requirement can then say how the new answer
relates to the old one. This document is part of the adapter, not of the
change request.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of the changed `checkout(subtotal, coupon, member, student)`, and, with the
same `subtotal`, `coupon` and `member`, one call of the code before the
change, `checkout(subtotal, coupon, member)`. Calls are independent; the
checker chooses them and their order freely.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `subtotal` | 21 bits | the `subtotal` argument, 0 to 2,097,151 |
| `coupon` | 7 bits | the `coupon` argument, 0 to 127 |
| `member` | 1 bit | the `member` argument |
| `student` | 1 bit | the `student` argument |
| `old_outcome` | 2 bits | how the call of the code before the change ended, coded as `outcome` |
| `old_price` | 21 bits | the price the code before the change returned (0 unless `old_outcome` is 0) |
| `old_ship` | 10 bits | the shipping fee the code before the change returned (0 unless `old_outcome` is 0) |

Negative arguments are not part of the trace.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call of the changed code ended: 0 it returned a pair of integers that fit `price` and `ship`; 1 it raised `ValueError`; 2 it raised any other exception or did not finish; 3 it returned anything else |
| `price` | 21 bits | the first element of the returned pair, when `outcome` is 0 |
| `ship` | 10 bits | the second element of the returned pair, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `price` and `ship` are 0 unless `outcome` is 0.
- F-OLD: `old_price` and `old_ship` are 0 unless `old_outcome` is 0.
