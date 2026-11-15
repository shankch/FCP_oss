# Text response frame (FCP text adapter, version 0.1)

This document defines how a text response becomes a trace that the FCP
engines can check. It is the "interface protocol" of every prompt bundle that
uses the text adapter. It is part of the adapter, not of the prompt.

## Units

The response is split deterministically into units. Every non-empty line is
one or more units: a line is split into sentences after `.`, `!` or `?`
followed by a space. A line without such punctuation (a subject line, a
greeting such as "Hi Sam,", a sign-off) is one unit.

Unit i of the response is cycle i+1 of the trace. Cycle 0 is reset.

## Labels

Every unit carries the labels below. A label is a 1-bit design output that is
true in a cycle exactly when the unit of that cycle has the property.

| Label | True when the unit ... |
|---|---|
| `subject` | is the subject line of the email (it begins with "Subject:") |
| `greet` | greets the reader by first name, or by a first-name placeholder such as `{first_name}` |
| `feature` | describes a product feature of the headphones (a capability or specification) |
| `benefit` | states what the customer gains, i.e. a benefit to the customer |
| `price` | states the regular price, $249 |
| `offer` | mentions the launch offer (the 20% discount) |
| `ends` | states when the launch offer ends |
| `rival` | mentions a competing product, brand or company |
| `cta` | asks the reader to take an action (buy, order, pre-order, visit, reply, ...) |
| `signoff` | belongs to the closing: the sign-off name, or a closing word such as "Warmly," before it |

Labels are assigned by labelers that see the units and this table, never the
prompt's requirements. A label that a deterministic rule can decide (`subject`,
`price`, `signoff`) is computed by that rule.

## Frame rules

The output eos is false while the response lasts, rises in the cycle after the last unit, and stays true from then on.

While eos is true, every label is false.

A unit that belongs to the closing carries no other label.

A response has at most 14 units.
