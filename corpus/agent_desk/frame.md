# FCP agent adapter, version 0.1

This document defines how one conversation of a tool-using agent becomes a
trace that the FCP engines can check. The agent is treated as a chip: its
scaffold (the code around the model) is the RTL, and the model sits outside
it. This document is part of the adapter, not of the prompt.

## Turns

Cycle 0 of the trace is reset, before the conversation starts. Every later
cycle is one turn. In a turn the model proposes one tool call, the scaffold
decides what runs, and the tool that ran returns its result, all within that
turn.

## Inputs

| Signal | Meaning in a turn |
|---|---|
| `p_act` | the tool call the model proposes: 0 none (no call, or a malformed one), 1 say, 2 verify, 3 lookup, 4 confirm, 5 refund, 6 handoff, 7 close |
| `p_ord` | the order argument of the proposed call |
| `p_amt` | the amount argument of the proposed call, in whole dollars |
| `p_more` | the proposed message asks whether there is anything else |
| `human` | the customer pressed "Talk to a human" since the previous turn |
| `id_ok` | verify ran in this turn and confirmed the customer's identity |
| `elig` | lookup ran in this turn and the order is eligible for a refund |
| `total` | lookup ran in this turn: the order total, in whole dollars |
| `accepted` | confirm ran in this turn and the customer pressed Yes |

A tool result (`id_ok`, `elig`, `total`, `accepted`) means something only in a turn
in which its tool ran. In any other turn its value is arbitrary.

The `p_` signals are the model's output. They are inputs of the scaffold.

## Outputs

| Signal | Meaning in a turn |
|---|---|
| `say`, `verify`, `lookup`, `confirm`, `refund`, `handoff`, `close` | that tool ran in this turn |
| `ord` | the order of the lookup, confirm or refund that ran |
| `amt` | the amount of the confirm or refund that ran, in whole dollars |
| `more` | the message that was sent asks whether there is anything else |
| `done` | the conversation has ended |

## Abstraction

* Orders are numbered 0 and 1 in the order in which the conversation first mentions them. A conversation concerns at most two orders.
* Amounts are whole dollars from 0 to 511. An amount with cents is rounded up.
* `more` and `p_more` are computed by a rule: the message contains "anything else", ignoring case.
* The customer's free-text messages are not part of the trace. The "Talk to a human" button and the Yes/No button are.

## Frame rules

At most one tool runs in a turn.

The output ord is 0 unless a lookup, confirm or refund ran; amt is 0 unless a confirm or refund ran; more is false unless a message was sent.

The output done is false in the first turn, becomes true in the turn after a handoff or close, and stays true from then on.

No tool runs once done is true.
