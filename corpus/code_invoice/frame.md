# FCP records adapter, version 0.6

This document defines how calls of a Python function that takes and returns
records (dicts) become a trace that the FCP engines can check. The function
is treated as a chip without memory: its arguments are input signals, its
result is on output signals, and each cycle is one call. This document is
part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `invoice(items, member)`. Calls are independent: the function keeps no
state between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Records

A list of records is carried field by field: one sequence signal per field,
all of the same length. Item `i` of `items` is `{"price": price[i], "qty":
qty[i], "sale": sale[i] == 1}`, and `len(price)`, `len(qty)` and `len(sale)`
are always equal: the number of items. In FCP-PL, `len(s)` is the length of a
sequence and `s[i]` its element `i` (counting from 0; 0 at or beyond the
length). The returned dict is carried key by key: `lines` is a sequence
signal, `discount` and `total` are numbers.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `price` | sequence of at most 5 numbers, 0 to 4,095 | the `price` of every item, in order |
| `qty` | sequence of at most 5 numbers, 0 to 15 | the `qty` of every item, in order |
| `sale` | sequence of at most 5 bits | the `sale` flag of every item, in order (1: True) |
| `member` | 1 bit | the `member` argument |

Calls with more than 5 items, prices above 4,095 cents or quantities above 15
are not part of the trace, and neither are negative numbers.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a dict with exactly the keys `lines`, `discount` and `total`, `lines` a list of at most 5 numbers from 0 to 65,535, `discount` from 0 to 65,535 and `total` from 0 to 524,287; 1 it raised `ValueError`; 2 it raised any other exception or did not finish; 3 it returned anything else |
| `lines` | sequence of at most 5 numbers, 0 to 65,535 | `lines` of the returned dict, when `outcome` is 0 |
| `discount` | 16 bits | `discount` of the returned dict, when `outcome` is 0 |
| `total` | 19 bits | `total` of the returned dict, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `lines` is empty and `discount` and `total` are 0 unless `outcome` is 0.
