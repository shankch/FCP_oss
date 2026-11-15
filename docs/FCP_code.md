# Code as a chip: checking an AI's function against the prompt

[FCP_agent.md](FCP_agent.md) checked an agent whose scaffold was written in a
small Python subset and compiled to Verilog. Ordinary code written by ChatGPT
or Claude Code cannot be compiled to a circuit in general. This document
checks it anyway, by splitting the problem in two:

* **The prompt side stays on the chip engine.** A function's interface
  becomes a chip without memory, and each reading of the prompt compiles to
  monitors over it, as before. Conflicts, open choices and disagreements
  between readings are found before any code exists.
* **The code side runs the code.** The function is called on a large scope of
  inputs, and the same compiled monitors check the recorded calls.

| Chip | Function |
|---|---|
| input pins | the arguments |
| output pins | the returned value (one signal per tuple element), and how the call ended: it returned, it raised a listed exception, it raised anything else or did not finish, or it returned something else |
| one clock cycle | one call |
| a property over consecutive cycles | a requirement that compares two calls, such as "adding items never lowers the amount charged" |
| RTL | the code, which is run rather than compiled |

Everything is in [corpus/code_checkout](../corpus/code_checkout),
[fcp/software.py](../fcp/software.py) and
[experiments/code_demo.py](../experiments/code_demo.py).

## 1. How a function is formalized

**The interface** (`function` in design.yaml, [IR_spec.md](IR_spec.md) §1).
Arguments drive input signals, and the returned value drives output signals.
An `outcome` signal says how the call ended. Each cycle is one call. Calls
are independent, and the checker chooses them and their order freely, so
`prev(x)` is the value of `x` in the previous call, whatever that call was.
The encoding is written down for the formalizers
([frame.md](../corpus/code_checkout/frame.md)), as for agents and text.

**The readings.** Two isolated agents write FCP-PL items over these signals
from the prompt, under the same protocol as the chip study. They never see
code.

**The prompt side, before any code:**
- **Conflicts at the prompt's own boundaries.** The search builds pairs of
  calls from the integer constants of the readings and the prompt: each
  constant and its neighbours, in both orders, with the other arguments at
  their own constants. For each pair the solver asks whether any answer to
  both calls meets every rule; if not, it returns a minimal set of
  conflicting rules. The existing analyses miss such conflicts. The
  trigger-situation candidates are arbitrary values, and the forcing search
  does not converge over 21-bit arithmetic inputs.
- **Open choices.** Determinacy (self-composition, as for chips) finds the
  outputs the prompt leaves open. For each one, the search finds the simplest
  call on which two different answers are both allowed.
- **Readings compared.** A function has no state, and these readings look
  back at most one call, so any disagreement between two readings shows on
  two calls. The comparison is therefore decided on two calls, by z3 over an
  exact integer encoding of FCP-PL. Bit-level PDR timed out on these
  comparisons, because proving two differently written products equal is a
  multiplier-equivalence problem. Every witness of the integer encoding is
  confirmed on the compiled monitors, and every agreement is spot-checked on
  the bit-level model.

**The code side:**
- **Scope.** For every argument the scope has a dense range, every integer
  constant of the readings, the prompt and the code together with its
  neighbours, the ends of the signal's range, and random values over it.
- **Calls.** Every point of the scope is called, in sweeps that put calls
  differing in one argument by one scope step next to each other. On a
  smaller scope the sweeps also run in reverse. A relational rule, such as
  monotonicity, is checked on every such pair.
- **Run.** The function runs in a separate process, with a time limit per
  call and a memory limit.
- **Check.** The compiled monitors of each reading are simulated on the
  recorded trace (Icarus, reading the trace from files). Every failure is
  replayed in a fresh process before it is reported. A rule whose trigger
  never fired in the scope is reported as vacuous.
- **Mutants.** One-operator changes of the code are run on the scope. A
  mutant that changes some answer but no verdict marks behaviour that no rule
  checks, at a line of the code.
- **Code splits.** Where several implementations of the same prompt answer a
  call differently, the calls are grouped by how they split the
  implementations, and the simplest call of each group is shown. A split is
  a decision that the prompt left to whoever wrote the code.

The evidence on code is **exhaustive within the scope** and says nothing
beyond it. It is not a proof.

## 2. The demo: a checkout function

**Prompt** ([spec.md](../corpus/code_checkout/spec.md)). A store asks for
`checkout(subtotal, coupon, member) -> (price, shipping)`, in cents, with
seven rules: range errors, a 10% member discount, a coupon, "discounts stack,
but the total discount is never more than 30%", rounding to the nearest cent,
free shipping from $50, and "adding items to the cart must never lower the
amount charged". One conflict and four ambiguities are planted
([spec_defects.yaml](../corpus/code_checkout/spec_defects.yaml)); no agent saw
that file.

**Readings.** `gold` is mine, read literally. `agent_a` and `agent_b` were
written by two isolated formalizer agents (Opus), in different styles, from
the prompt, the adapter document and the requirements, never from code.

**Code.** Haiku, Sonnet and Opus each received only the prompt, in an empty
directory, with the instruction to write `checkout.py` and pytest tests and
to make the tests pass, as a developer would ask an AI coding tool. All three
runs, with prompts and replies, are recorded under
[agents/](../corpus/code_checkout/agents). Also checked: my reference
implementation ([impl/ref.py](../corpus/code_checkout/impl/ref.py)) and eight
planted bugs, each a one-line patch of it
([bugs/bugs.yaml](../corpus/code_checkout/bugs/bugs.yaml)).

### 2.1 Before any code: the prompt cannot be satisfied

The boundary search finds the planted conflict under all three readings, at
the first place it can occur:

> `checkout(4999, 0, False)` must return `(4999, 499)`: a $54.98 charge.
> `checkout(5000, 0, False)` must return `(5000, 0)`: a $50.00 charge.

Adding one cent to the cart lowers the amount charged, which rule 7 forbids.
Every minimal conflicting set contains the shipping rule and the
monotonicity rule, one rule that fixes the price, and either the rule that
returns a value or the frame rule that zeroes the outputs of a call that
raised. The search checks 5,742 to 15,448 candidate pairs in 17 to 65 s.
The existing trigger-situation check reports all three readings consistent:
its candidates never land on the threshold.

Determinacy finds one output the prompt leaves open, under every reading:
the price at exactly half a cent. The simplest call is
`checkout(5, 0, True)`: a member's 5-cent cart costs 4.5 cents, and both 4
and 5 are a nearest cent.

All three readings agree on every requirement once they are compared in
context, over calls that meet every other requirement under both. They
differ in plain comparison, because agent_a and agent_b state the price and
shipping rules only for calls that returned, while gold also covers calls
that raised. With the return rule in force the difference disappears. Each
comparison is decided on two calls in under a second, and the bit-level
model separates none of 400 calls for any agreement. Both agents named the
conflict and the open rounding in their notes.

### 2.2 The code against every reading

Each model's code passes its own test suite: 134, 196 (plus one test marked
as an expected failure) and 745 tests. Each is called 1,355,700 times, and
every failure below is replayed in a fresh process.

| Code | Breaks, under all three readings | First failing call | Why |
|---|---|---|---|
| Haiku | R-SHIP-1 | `checkout(5000, 0, False) -> (5000, 498)` | it saw the conflict and kept rule 7 by charging shipping on orders of $50 or more |
| Sonnet | R-MONO-1 | `checkout(4999, 0, False) -> (4999, 499)`, then `checkout(5000, 0, False) -> (5000, 0)` | it saw the conflict and kept rule 6, with a test that records rule 7 as an expected failure |
| Opus | R-SHIP-1 | `checkout(4998, 0, False) -> (4998, 2)` | it saw the conflict and kept rule 7 by cutting the fee below $50 |

All three models noticed the conflict and said so in their replies. Each
resolved it differently, and each passes its own tests. Under any reading of
the prompt, each breaks a rule.

**The planted bugs.** FCP flags every bug that breaks a reading, in the
requirement it was planted against, with the first failing call:

| Bug | First failing call |
|---|---|
| C1 a $50.00 cart still pays shipping | `checkout(5000, 0, False) -> (5000, 499)` |
| C2 truncation instead of rounding | `checkout(1, 0, True) -> (0, 499)` |
| C3 cap applied before the member discount | `checkout(60, 21, True) -> (41, 499)` |
| C4 member discount dropped with a coupon | `checkout(10, 1, True) -> (10, 499)` |
| C5 coupons up to 100% accepted | `checkout(0, 51, False) -> (0, 499)` |
| C7 a 1,000,000-cent cart rejected | `checkout(1000000, 0, False) -> raised ValueError` |
| C8 the price returned as a float | `checkout(0, 0, False) -> returned (0.0, 499)` |

C6 replaces exact arithmetic with `round()` on floats, which rounds half a
cent to even. FCP does not flag it under any reading, because every reading
allows either neighbour of half a cent. That is correct for the prompt as
written; whether it is a bug is the open question above.

### 2.3 Where the code splits, and the answer key

Calling the three implementations on the same scope shows four splits:

| Calls | Simplest call | Haiku | Sonnet | Opus |
|---|---|---|---|---|
| 406 | `checkout(5000, 0, True)` | `(4500, 499)` | `(4500, 0)` | `(4500, 499)` |
| 134 | `checkout(5000, 1, False)` | `(4950, 499)` | `(4950, 0)` | `(4950, 50)` |
| 44 | `checkout(5000, 0, False)` | `(5000, 498)` | `(5000, 0)` | `(5000, 0)` |
| 20 | `checkout(4998, 0, False)` | `(4998, 499)` | `(4998, 499)` | `(4998, 2)` |

The first split is a planted ambiguity: is "an order under $50" measured
before or after discounts? Haiku and Opus measure the discounted price;
Sonnet, the reference and all three readings measure the subtotal. The
readings agree, but the decomposer flagged the phrase, and two of three
models chose the other reading. So the question stays in the queue,
answered by this example: "A member's $50.00 cart costs $45.00 after the
discount. Does it ship free?" The other three splits are the models'
different ways out of the conflict.

The review queue for this prompt is therefore three questions:
1. At the free-shipping threshold, which rule gives way, rule 6 or rule 7?
2. Is "an order under $50" the subtotal or the discounted price?
3. At exactly half a cent, round up, round to even, or either?

**What the answers decide.** If rule 7 gives way, FCP certifies Sonnet's code
on all eight remaining requirements and flags Haiku and Opus on rule 6.
If rule 6 gives way, the readings need a new requirement for how the fee
falls off, which nobody wrote, and the three implementations do it in three
different ways.

### 2.4 False assurance

Treat each model's tests as the check, as in "the AI wrote the code and the
tests, and the tests pass". Then all three violated requirements are
certified (3 of 3). FCP certifies none of them. FCP certifies a requirement
only if it passes under both agent readings within the scope, the agent
readings agree on it in context, and it is in no conflict of either reading.
Gold is never used as a peer. Until the conflict is answered, FCP certifies
9 of the 27 requirement-implementation pairs (the range errors, the member
discount and the example). The cost of zero false assurance is again the
queue.

The models' test suites are useful evidence, but each encodes its own
model's decisions. Run against the other implementations, they fail
hundreds of tests (for example 212 of Opus's 745 on Sonnet's code, and 107
of Haiku's 134 on Sonnet's code), mostly at the conflict and the shipping
threshold. They catch most planted bugs, and they flag C6 because each
model chose to round half a cent up. Haiku's suite misses C1, because
Haiku's own code charges shipping on a $50.00 cart.

### 2.5 Behaviour no requirement checks

One-operator mutants of each implementation: 41 to 45 of 44 to 48 mutants
change some answer, and every reading kills all of them but one or two. The
survivors are:
- in all four implementations, the rounding constant (`+ 50` becomes
  `+ 49`), which turns half a cent from up to down: the open question;
- in Opus's code, a change inside its fee taper (`(4998, 2)` becomes
  `(4998, 1)`). Both values break rule 6, so no rule tells them apart.

### 2.6 Beyond the scope: proofs

The scope is exhaustive where it reaches and says nothing elsewhere. For a
pure function on integers and booleans (and on strings and lists, §3.5),
[fcp/prove.py](../fcp/prove.py) goes further. It translates the function's Python source into z3 terms by
symbolic execution, every path with its condition, so that the outcome and
the returned values of one call are terms over the arguments. Joined to the
integer encoding of a reading over k calls (§10), the question "do some k
calls, anywhere in the interface's ranges, break this requirement?" goes to
z3. If none do and the horizon is exact, the requirement is proved for
every call the interface can carry. If some do, the calls are run on the
real code and its trace is checked by the compiled monitors before they are
reported.

The translation is a second implementation of a subset of Python, so it is
checked before it is trusted: on every call of the scope, its outcome and
values must equal what the code answered (1.36 million calls in about a
second, with the terms compiled back to Python). The integer encoding of
the reading is a second implementation of FCP-PL, and it is checked the
same way: on every cycle of that trace, it must say a requirement fails
exactly where the compiled monitor says so. One difference in either, and
nothing is proved. For a change (§5), the old code is translated and
checked too, and its terms are the baseline signals of every call.

The subset covers what the checkout implementations use:
module constants, helper functions that raise (inlined), `isinstance` and
`type()` checks decided by the declared argument types, loops over
`range()` or a literal tuple, comparisons, `and`/`or`, conditional
expressions, `min`, `max`, `abs`, `divmod`, and `//` and `%` by a positive
constant; for code with effects, files and objects it grows as described
below. A value whose Python type depends on the path (`x < 5 and FEE`),
floats, strings in a function whose arguments are numbers (other than
literals and the decimal text of a number), and calls to anything else are
refused, never guessed. A function that takes strings or lists is
translated with sequences as terms (§3.5).

On the checkout study ([prove_demo.py](../experiments/prove_demo.py),
[results](../experiments/results/prove_code_checkout.json)), 30 of the 36
implementation-reading pairs translate. The other 6 are the two planted
variants that call `round()` on a float. Every one of the 260 requirement
verdicts agrees with the scope: the 198 the scope passed are proved, and
the 62 it failed fail the proof too, each at calls z3 chose, replayed and
confirmed on the monitors. Each pair takes 6 to 7 seconds, both checks
included. On the change study
([results](../experiments/results/prove_code_change.json)), 36 of 39 pairs
translate (one planted variant divides as a float), and all 204 verdicts
agree: 139 proved, 65 failing in both. "Nothing changes for non-students"
is proved for all three models' code under every reading, over every call
the interface carries, not just the 3.6 million calls of the scope. Each
pair takes about 25 seconds. In both studies the scope missed nothing. A planted bug at a subtotal it never calls (777,777) passes the
scope and fails the proof ([tests/test_prove.py](../tests/test_prove.py)).
`fcp review` runs the proof on every pure function: a certified requirement
that is also proved under both readings is marked "proved", and calls
outside the scope that break a requirement become a question.

Code with effects (§6) is proved over every run. A call on `api` (or on a
patched name) becomes an event in the translation, and each answering call
takes the next answer of the script as a free variable; an answer the code
receives as an exception forks the path. Paths that made different calls
stay apart, so one run's signals at each cycle are terms over the arguments
and the answers, and a run lasts at most `max_calls` calls and its return.
The integer encoding of the reading gains ghost state (reset, truncated to
the ghost's bits, and an item failing where a ghost it depends on leaves its
range, as in the compiled monitors) and the `next`, `after_reset`, `once`,
`hist` and `since` forms the agents' readings use. Both checks apply run by
run: the path a run's arguments and script select must make the calls the
code made and end as it ended, and the encoding must fail where the
monitors fail. On the payment study
([results](../experiments/results/prove_code_pay.json)) all 39
implementation-reading pairs translate, and all 364 verdicts agree with the
scope: 293 proved for every amount and every script of answers, and 71
failing in both, each at a replayed run. Every model's code is proved on
every requirement but rule 7, which fails at three errors in a row (and, in
the agents' literal readings, after a decline). Each pair takes 1 to 2
seconds.

Files the code opens (§6.3) are translated too. `open` returns an object
numbered in the path, its declared methods are events on it, a `with`
block closes it on every way out, and a call on a closed file raises
`ValueError`. `try`, `except` (by class, as Python matches them),
`else` and `finally` go on from the state where an exception was raised.
Each path also keeps its own view of the disk, which is concrete because
the paths and modes are literals, so `os.path.exists` answers from it and
removing a file that is not there raises `FileNotFoundError` on that path.
On the atomic save, 36 of 39 implementation-reading pairs translate (one
planted variant divides as a float), and all 276 verdicts agree with the
scope: 208 proved for every balance and every answer of `os.replace`, and
68 failing in both ([results](../experiments/results/prove_code_save.json)).
Every model's code breaks only rule 6, at a failed move, under every
reading.

Objects with several methods (§8) are proved over sequences of every
length. The constructor gives the fields; each call runs the method its
`op` selects, and every way that method can end is merged into the fields
after it (at a raise, the fields where it was raised), so a call is one
step from fields to fields and results. The step is checked like the rest,
sequence by sequence from a new object.

A proof for every length is an induction. The state after a call is the
object's fields, the reading's ghosts and the registers its `once`, `hist`
and `since` keep. A reading that looks back w - 1 calls is judged on a
window of w consecutive calls (1 for my reading, 2 and 3 for the agents',
which use `prev` and `next`). Candidate facts about the state come from a
template: each number of the state against each constant of the code and
the reading and against each other number, sums of two numbers, each
boolean, and the same facts under a condition (145 candidates under my
reading). Houdini drops every candidate that fails after one of the first
calls of a new object, or that the others do not carry across one more
call, until the rest is an invariant: true after every call of every
sequence. A requirement is then PROVED if the invariant before a window
implies it at the window's last call, and the first calls, where no full
window exists yet, are checked unrolled from a new object. The window
encoding is itself proved equal to the unrolled one at every call both
cover. Each PROVED verdict reports the facts its proof used. `R-BAL-1` on
the reference, for example, needs `b == self._balance`, `b >= 0` and
`b <= 50000`: the field is the reading's model of the balance, and it
stays within the card's limits. Where no invariant is found the verdict is
PROVED-BOUNDED: no sequence of up to k calls breaks it (k is the scope's
longest sequence), and nothing is claimed beyond.

On the gift card ([results](../experiments/results/prove_code_card.json)),
48 of 52 implementation-reading pairs translate (one planted variant
divides as a float), and all 360 verdicts agree with the scope: 174 fail
in both, and of the 186 that pass, 182 are proved for every sequence of
calls of every length with every amount, and 4 are bounded at 10 calls.
Under my literal reading each model's code fails only the load rule, at a
sequence z3 chose, replayed. Under both agents' readings, which count the
bonus toward the cap as the models do, every requirement is proved: the
shared answer of §8.2, now for every sequence. The variant reading fails
the four requirements that depend on that answer. A pair takes 0.6 to 57
seconds, and the whole study under 7 minutes; unrolled to 10 calls without
induction, a pair under my reading took up to 8 minutes.

The four bounded verdicts are the instructive ones: they are false. All
four are on planted variants whose balance drifts (C3 lets a spend take it
below zero, C6 empties the card at a refused spend, C7 returns the bonus
but never adds it), under my reading, whose model of the balance is a
ghost with a declared range of about a million cents either way. The
model follows what the code reports, at most 50,500 cents a call, so within
10 calls it stays in range and the load rule holds wherever it applies. A
longer sequence takes the model out of its range, and the rule fails on the
compiled monitors:
at call 21 on C3 (21 spends of 50,000 on an empty card), at call 41 on C6
and at call 4,155 on C7
([experiments/card_deep.py](../experiments/card_deep.py),
[results](../experiments/results/prove_code_card_deep.json)). The scope
and the bounded proof both passed them. The induction did not: it found no
invariant because there is none. This is what PROVED-BOUNDED is for. It
says that the proof stopped at k calls, and here the truth changed after
that. The same sequences on the reference fail nothing but the known
conflict. All three variants are still caught: each fails at least two
other requirements on the scope.

Objects whose fields are dictionaries or lists (the rate limiter keeps one
list of times per customer) are proved in §4.5.

### 2.7 A second solver on every proof

A failure is replayed on the real code and on the compiled monitors, so a
wrong answer of the solver cannot produce one. A proof has no such guard.
PROVED means that z3 found some formulas to have no model, and a bug in z3
on one of them would be a false proof that nothing above notices. So each
of those formulas is decided a second time, by cvc5, a solver that shares
no code with z3.

[fcp/confirm.py](../fcp/confirm.py) records every formula z3 answers
*unsat* while a proof runs, in SMT-LIB text as z3 prints it, under the
requirement being settled at that moment. Formulas answered before any
requirement is in hand (the agreements of a sweep, the invariant of an
induction, the check that the one-step encoding of an object is the
unrolled one) stand behind every requirement of the pair. Each text is
then given to cvc5 in a separate process, and a proved requirement gets
one of three words:

- **confirmed**: cvc5 finds every formula behind it unsatisfiable too;
- **refuted**: cvc5 finds a model of one of them. The two solvers
  disagree and neither is believed;
- **unconfirmed**: cvc5 gives no answer on one of them in its time.

(This is not the certification rule of the overview, which compares
readings. Here two solvers are compared on one reading.)

cvc5 picks its procedures by the logic it is told, and no one choice was
best on every formula here: with no logic named it took 26 seconds on a
checkout formula with a product that it decides in half a second as
nonlinear integer arithmetic, and the reverse held for others. So each
formula is given first with no logic named, then in the smallest logic
that holds it, and a nonlinear one under four of cvc5's settings for
products: all of them for three seconds each, then again for ten seconds
each. The first answer of *unsat* or *sat* stands. A formula still open
when the study is over gets one more go, of 45 minutes.

| study | pairs | proved | formulas | in the second go | confirmed | unconfirmed | refuted | cvc5, slowest formula |
|---|---|---|---|---|---|---|---|---|
| checkout (§2.6) | 30 | 198 | 198 | 0 | 198 | 0 | 0 | 7 s |
| card masking (§3.5) | 36 | 161 | 181,745 (24 with `mod` left open) | 35 | 161 | 0 | 0 | 262 s |
| rate limiter (§4.5) | 39 | 65 | 4,134 | 6 | 65 | 0 | 0 | 424 s |
| student pricing (§5.2) | 36 | 139 | 139 | 0 | 139 | 0 | 0 | 0.07 s |
| payment retry (§6.2) | 39 | 293 | 293 | 0 | 293 | 0 | 0 | 0.13 s |
| atomic save (§6.3) | 36 | 208 | 208 | 0 | 208 | 0 | 0 | 0.05 s |
| order (§6.4) | 39 | 278 | 278 | 0 | 278 | 0 | 0 | 0.24 s |
| gift card (§8.2) | 48 | 186 | 1,253 (203 with `mod` left open) | 47 | 186 | 0 | 0 | 1,485 s |
| all | 303 | 1,528 | 188,248 | 88 | 1,528 | 0 | 0 | |

Every proof of the eight studies is confirmed: 1,528 requirements (the
1,517 proved and the 11 proved up to a bound), over 188,248 distinct
formulas, 3.6 GB of text. cvc5 refutes none and leaves none open.

Three studies needed the second go, for 88 formulas, and it settled all of
them. In card masking (35) and the rate limiter (6) they are linear
formulas that only want more than ten seconds on a busy machine:
comparisons a sweep makes between two terms that count characters of the
number, and formulas of 300 to 350 KB with remainders in the limiter. One
of the first and two of the second, timed alone as linear integer
arithmetic, took cvc5 23, 15 and 33 seconds; the slowest of each study had
4 and 7 minutes of cvc5 in all, the attempts before the one that answered
included. The gift card (47) is the hard one, for two kinds of formula.

Before an induction over an object's calls, the engine checks that its
one-step encoding is the unrolled one, call by call up to the bound. A
reading's ghost wraps around at its declared width, as the register in its
compiled monitor does, so the formula for call *n* nests *n* remainders,
and from ten calls on cvc5 gave no answer in two minutes where z3 takes
2 to 56 seconds. So any formula with `mod` is also given with `mod` left
open: every `(mod a b)` becomes `(fcp_mod a b)` for a function `fcp_mod` of which
nothing is said. A formula with no model under every reading of that
function has none under `mod`, which is one of them, so *unsat* on the
looser text is *unsat* on the formula, and cvc5 gives it in a quarter of a
minute to a few minutes: the two encodings take the same remainders of the
same sums. Any other answer on the looser text is ignored. The table
counts the formulas confirmed this way.

The four bounded proofs of §2.6 are the other kind: one formula each, the
object unrolled to ten calls, 420 to 490 KB of text. They rest on the
ghost staying inside its range for ten calls, so with `mod` left open the
formula has models, and only the text as printed counts. z3 decides each
within the half minute its pair takes. cvc5 gave no answer in ten minutes
with no logic named; told that the logic is linear integer arithmetic it
takes 9 to 22 minutes outside the study, and up to 25 inside it. This is
what the length of the second go is set by, and why a long attempt takes
the named logic before none.

What is confirmed is the solver's part and nothing more. The translation
of the code and of the reading into formulas is checked as before, on the
scope's calls (§2.6). The rewriting done before a formula reaches a
solver (`z3.simplify`, the substitutions of a sweep), z3's printer, and
the way the engine puts answers together (induction, Houdini) are still
trusted. cvc5 can also print a proof of each answer, in a format that a
small independent checker (Ethos) reads; `decide(text, proof=True)`
returns it, and nothing here checks it yet.

## 3. Strings and lists: a card-masking function

Most code takes strings and lists, not only integers. This section extends
the adapter to them without changing the split: the prompt side runs on the
chip engines, and the code side runs the code.

### 3.1 How a string becomes a signal

A string or list argument is a **bounded sequence**: a length and at most n
slots of w bits ([IR_spec.md](IR_spec.md) §1, §4.3). For `mask_card(number)`,
`number` has 32 slots of 8 bits, so it covers every string of up to 32
Latin-1 characters. A sequence is carried by two ports, the packed slots and
the length. The monitors read it in canonical form, with every slot at or
beyond the length taken as zero, so nothing a port carries beyond the length
can change a verdict.

FCP-PL gains `len(s)`, `s[i]` (0 outside the sequence), `x in s`, `==` on
whole sequences, string and list literals (a one-character literal is a code
where a number is expected, so `s[i] == "*"` and `s[i] - "0"` work), ASCII
character tests, and four quantifiers over a bound with a static maximum:
`all`, `any`, `count` and `sum`, written `all(i < len(s): ...)`. Rule 2 of the
demo prompt, "replace every digit with `*`, except the last four digits",
reads:

```
all(i < len(number): isdigit(number[i]) && count(j < len(number): j > i && isdigit(number[j])) >= 4
                     -> masked[i] == "*")
```

The compiler expands each quantifier into one term per value of its
variable, so a property over strings is still a combinational function of
one cycle. Every engine therefore applies unchanged: PDR and BMC for the
prompt-side analyses, simulation for traces, and the integer encoding in z3,
which represents a sequence as a length and slots under the same canonical
form. The Luhn check of the demo, a sum over the digits with every second one
from the right doubled, is one such expression.

### 3.2 A scope drawn from the request

For integers, the scope was ranges and the constants of the request with
their neighbours. Strings have too many values for ranges, and the
boundaries that matter are not constants: a card number is valid from 12
digits, whatever its length in characters. So the scope is drawn from the
readings themselves, as constrained random stimulus is in hardware
verification:

- **Atoms.** Every comparison of two integers in any formula, through defs,
  with its two sides differing by -1, 0 and +1 (`count(...) >= 12` gives 11,
  12 and 13 digits); every other condition, holding and failing; and every
  length that the readings and the prompt name.
- **Contexts.** Each atom is solved inside the trigger of every rule and
  with no constraint, so every rule is exercised at every boundary: 12 digits
  inside "the number is valid", which no random string reaches.
- **Solving.** z3 solves each atom in context in the integer encoding, with
  the outputs free, and completes the input at random: slots come from the
  alphabet (the characters of the readings and the code, one of each
  character class including the non-ASCII digit `²`, and a configured set) and
  are fixed at random where the atom allows.
- **Neighbours.** Every such call is followed by calls one edit away (a slot
  deleted, inserted or replaced), which cross the boundaries the atoms sit
  on. A relational rule compares consecutive calls, so it compares calls that
  differ in one place.
- **Tiny and random calls.** All sequences of up to two slots over three
  alphabet characters, and random strings over the alphabet.

### 3.3 Replaying at speed

Unrolled quantifiers make big monitors: about 24,000 lines of Verilog per
reading for 32-character strings. Icarus replays them at about a millisecond
per call. The monitor is now compiled once per reading by Verilator and
replayed on a binary trace file, about 400 times faster
([fcp/vl.py](../fcp/vl.py)). It is the same Verilog module. On every check of
the checkout study and of a 10,000-call string trace, the two simulators
report identical first failures, failure counts and trigger counts. A test
keeps them in agreement ([tests/test_seq.py](../tests/test_seq.py)).
Verilator also reports the failing calls, so a failure is shown at its
simplest failing call rather than its first.

### 3.4 The demo: card masking

**Prompt** ([spec.md](../corpus/code_mask/spec.md)). `mask_card(number)`
takes a card number of 12 to 19 digits, which customers type with spaces or
hyphens, and returns it with most digits replaced by `*`. Rule 1 raises
ValueError for any other character, a wrong number of digits or a failed
Luhn check; rule 2 keeps the last four digits; rule 3 keeps every space and
hyphen in place; rule 4 never shows more than a quarter of the digits. For
12 to 15 digits, four digits are more than a quarter, so rules 2 and 4
conflict on every valid number of those lengths
([spec_defects.yaml](../corpus/code_mask/spec_defects.yaml)).

**Before any code.** The conflict search finds the clash under all three
readings, each time on one call, in 92 to 345 s: under mine,
`mask_card("219011401821")`, twelve digits that pass the Luhn check, must be
answered (rule 1), with its last four digits shown (rule 2) and with at most
three shown (rule 4). Under my reading the trigger-situation check misses it;
under both agents' readings it finds it. The readings agree on every
requirement in context, the two that depend on the Luhn check included.
Each reading computes the check in its own way, and neither the integer
encoding nor the bit-level model alone decided those two comparisons within
30 minutes per direction; the sweep of §3.5, which first proves the
agreements between the two definitions piece by piece and then compares the
requirements, decides them at once. Taken alone, only the return
requirement differs between the readings (my reading's is weaker than each
agent's), and with the other requirements assumed it does not. With every
comparison decided the study takes 5.7 hours, where it took 15.4.

**The code.** Haiku, Sonnet and Opus all noticed the conflict, said so, and
made the same choice: the security rule wins, so a number of 12 to 15
digits shows only its last three. Under every reading each breaks exactly
rule 2, replayed (`mask_card("177111444150")` gives `"*********150"`). The
three implementations answer every call of the scope (131,295 to 133,598
calls, as each scope adds the code's own constants) identically. Their test
suites (38, 146 and 119 tests) fail on each other's code only on input the
prompt does not cover and the scope leaves out (bytes, lists, tuples) and on
one test that reads the module's docstring. FCP flags all 8 planted bugs in
their requirement (the Luhn check from the left, a superscript two taken for
a digit, the last four characters kept instead of the last four digits, 19
digits rejected, hyphens rejected, whitespace stripped first, `X` instead of
`*`, a list returned), and not the refactoring (a regular expression); every
observable mutant is killed. The naive flow certifies the 3 violations; FCP
none, and 9 of 21 pairs overall.

### 3.5 Beyond the scope: proofs for strings

The masking scope has about 131,000 calls; the interface carries every
string of up to 32 characters. The proofs of §2.6 now cover it.

**Strings as terms** ([fcp/seqs.py](../fcp/seqs.py)). In the integer
encoding a string argument is a length and one character code per slot. In
the translation, a string or list whose content depends on the arguments is
a list of guarded slots: pairs of a condition and a value, in order, and
the sequence is the values of the slots whose condition is true. The
argument is 32 slots, slot i under `i < len`. A filter
(`[c for c in number if is_digit(c)]`) strengthens the conditions, a loop
runs its body once per slot under the slot's condition, `append` adds a
slot, and two paths that meet pair the slots each of them added. Nothing
asks how long the sequence is until the code does (`len`, an index, a
slice, the value returned), and then the answer is a sum of conditions.
`str.isdigit()` and the other character tests are Python's own answers on
the 256 codes the interface carries, so the translation knows that
`'²'.isdigit()` is true. The translation is checked as before: on every
call of the scope its outcome and string must equal the code's. Twelve of
the thirteen implementations translate; the refactoring that uses a
regular expression is refused at its `import`.

**Why z3 alone does not answer.** With the outputs replaced by the code's
terms, a requirement is a formula over the 33 integers of the argument.
It holds the Luhn sum twice: as the code computes it (a loop over the
digits from the right, doubling by position) and as the reading defines it
(a sum over the positions, each with the count of the digits to its
right). The two are equal, and z3 does not find that out on the whole
formula. Two readings that define the sum differently pose the same
question, which is why their comparison stayed open in the first run of
this study (§3.4).

**Sweeping** ([fcp/sweep.py](../fcp/sweep.py)). The two sides agree on
many intermediate values: slot i holds a digit, the count of digits right
of slot i, the sum so far. Each agreement follows in one step from the ones
below it. Sweeping, the method hardware tools use to compare two circuits,
finds and proves them from the leaves up. Every subterm of the goals is
evaluated on sample calls (256 from the scope) by a generated Python
function. Subterms with the same value on every sample are candidates:
equal to each other, or to a constant. In dependency order each candidate
goes to z3, on terms in which the agreements already proved are
substituted, with half a second each. UNSAT merges the subterm into its
representative; a model is one more sample, which splits the candidates it
tells apart; a timeout leaves the subterm as it is. Nothing is merged
without a proof, so the goals that come back are equivalent to the ones
that went in. The samples only decide what is tried.

**The facts of the path.** One more step was needed for the models' code.
"When the function returns, at most a quarter of the digits are shown"
fails where the function returns and more than a quarter are shown, and
"the function returns" is a conjunction of what each step of the code
checked: character 0 is a digit or a separator, character 1 is, and so on.
Path conditions are kept as such chains (a branch that rejoins adds one
fact, not a disjunction of paths), each goal is opened into its conjuncts,
and where a goal is still open after the first sweep its small conjuncts
(64 nodes or fewer: the facts) become assumptions under which the large
ones are swept again. Under them the code's digit count and the reading's
are the same term. A reading that states a rule of every call, with no
"when it returns" (agent_a's and agent_b's quarter rule), has no such
facts in its goal; it is proved case by case, one case per outcome of the
call, each with that outcome's facts.

**The readings compared.** The comparison of two readings on the Luhn
requirements is the same kind of question with no code in it: the sum as one
reading defines it against the sum as the other does. A comparison over
strings or lists that z3 leaves open for two seconds is therefore asked
again with the items of both readings swept, on samples drawn from the
constants the readings name (`QUICK`, `_IntSpec.swept` in
[fcp/software.py](../fcp/software.py)). The sweep takes about a second
(5,943 subterms, 1,380 merged into another, 2,631 proved constant, none left
open), after which each direction is decided at once; a difference found
this way is confirmed on the compiled monitors like any other.

**Results.** `experiments/prove_demo.py code_mask` takes the thirteen
implementations under the three readings
([prove_code_mask.json](../experiments/results/prove_code_mask.json); 1,905
seconds run alone, 6 to 97 seconds per pair). Twelve implementations
translate; C9 imports `re` and is refused at the import. The 36 pairs give
240 verdicts, none left open:

| | Verdicts |
|---|---|
| Passed by the scope and proved for every string the interface carries | 161 |
| Failed by the scope and by the proof, z3's string replayed on the code | 75 |
| Passed by the scope of 131,613 calls, failed by the proof | 4 |

29 of the 240 verdicts, on 18 pairs, needed the second stage (the facts of
the path assumed, the rest swept again). The four failures the scope missed are real: each string was
run on the code and on the compiled monitors.

- **C6 strips the number first** (three verdicts, R-ERR-1 under each
  reading). `mask_card('\xa00----8-559785--0--------0  -8-1')` must raise,
  since a no-break space is neither a digit nor a separator; C6 strips it
  and returns `'*----*-******--0--------0  -8-1'`. The other two strings
  begin with a carriage return and with `\x85`. The scope had flagged C6
  on four other requirements and passed it on this one, which is one of the
  two the bug was planted to break.
- **C2 tests digits with `str.isdigit`** (R-RET-1 under agent_a's reading,
  "most of its digits hidden" as fewer than half shown).
  `'¹¹9³¹--9-8¹8--5-8-- --³ -  -  - '` has six digits 0 to 9 and four
  superscripts. C2 accepts it, counts ten digits, and returns
  `'*****--*-**8--5-8-- --³ -  -  - '`, which shows three of the six.

The scope is built once for the proofs, from the readings alone: 131,613
calls, where the study of §3.2 built one per implementation (130,659 to
131,848 calls).

## 4. Objects: a rate limiter

A class with state is the chip engine's home ground: a chip with memory.

### 4.1 How an object becomes a chip

With `class` in the `function` section ([IR_spec.md](IR_spec.md) §1), a
reset creates the object and every later cycle calls the method on it, in
order, until the next reset starts a new object. The object's state stays
inside the code, like the registers of an RTL design that the readings never
name. `prev`, `once`, `hist` and `since` range over the calls on one object,
and a reading can keep a specification model in ghost state: for the demo,
the times of a customer's three most recent allowed attempts and the end of
their penalty, per customer through a rigid variable.

### 4.2 The scope: sequences drawn from the request

The scope is a set of call sequences, each on a new object:

- **Request sequences.** For every condition the readings name (each trigger
  holding and failing, each pair of triggers, and each comparison at -1, 0
  and +1 inside each trigger), bounded model checking on the spec-only model
  finds the shortest sequence of calls after which the condition holds,
  with every rule met before that call. A conforming implementation follows
  the same path, so it reaches the condition too.
- **Short and random sequences.** Every sequence of one or two calls over a
  few values, and random walks: arguments from their pools, and a clock
  advanced by one of its configured steps at every call.
- **Neighbours.** Every sequence one edit away: a call deleted or repeated,
  one argument changed, or the clock of one call moved by one.

A failure is reported with the whole history of its object, the shortest
failing one, and replayed on a new object in a fresh process.

### 4.3 Rules over every customer

A rule about "each customer" is written with a rigid variable, here
`U` in 0 to 1,000. In a proof, a rigid is a free constant, so the rule holds
for every customer. In a trace check, every value is replayed. But an
analysis that *assumes* the rule needs it for every value at once, and 1,001
copies of the monitor are too many: the chip engine then leaves the rule out
of consistency, forcing and determinacy, and would miss the planted conflict.
The comparison of readings already pinned such rules at chosen values
(counterexample-guided). The conflict search for objects does the same:
for each candidate sequence, it assumes the rule at every customer the
sequence names, one monitor instance each. Fewer assumptions than "every
customer" can only hide conflicts, never invent one, so every conflict it
reports is real.

### 4.4 The demo: a login rate limiter

**Prompt** ([spec.md](../corpus/code_limit/spec.md)). `RateLimiter.allow(user, now)`:
at most 3 attempts per customer in any 60 seconds; denied attempts do not
count; "allow an attempt whenever the customer had fewer than 3 allowed
attempts in the last 60 seconds"; and "after a denied attempt, deny that
customer's attempts for the next 10 seconds". Rules 4 and 5 conflict: after
three allowed attempts and a denial, the window frees up while the penalty
still runs. Three ambiguities are planted as well
([spec_defects.yaml](../corpus/code_limit/spec_defects.yaml)): the edges of
the windows, whether a denial during the penalty restarts it, and which call
"the previous call" is.

**Readings.** `gold` keeps a model of each customer in ghost state (the
times of the three most recent allowed attempts and the end of the penalty),
for an arbitrary customer `U` in 0 to 1,000. The two isolated agents did the
same with their own decisions at every edge. Agent B noticed that rule 5 adds
nothing that rules 2 and 4 do not already decide; both noticed that the
literal "previous call" lets time go backwards across a call that raised.

**Before any code.** The sequence conflict search finds the planted conflict
under all three readings, in 9 to 35 seconds, as the shortest sequence that
shows it, for instance under gold:

```
allow(1000, 0); allow(1000, 0); allow(1000, 32); allow(1000, 52) -> denied; allow(1000, 61)
```

At the last call the window holds one allowed attempt, so rule 4 says allow,
and the penalty from 52 says deny. Under agent A's reading it also finds the
second conflict agent A reported, after time goes back. The trigger-situation
check calls every reading consistent. Gold leaves no answer open (the search
for open choices confirms every candidate on the monitors over all 1,001
customers, and rejected one that pinning alone had let through); agent A's
reading leaves one open, after time goes backwards across a call that
raised, where its own notes say its model stops tracking. Readings are
compared by bounded model
checking (8 cycles): in context, gold and agent B differ only on "the
previous call", with a three-call witness, while agent A, who reads both
windows as closed, differs from both on the window and penalty edges.

**The code.** All three models noticed the conflict and let the penalty win,
as did my reference. Their code passes their own tests (48, 43 and 43), and
under gold each breaks exactly rule 4, on the conflict sequence, replayed.
The three implementations answer all 175,528 calls of the scope identically:
three models agreeing is no evidence that the prompt is consistent. Their
test suites still disagree (Sonnet's code fails 8 of Haiku's tests and 12 of
Opus's), on argument types outside the trace's domain, which the tests probe
and the scope does not.

**Planted bugs.** FCP flags 7 of the 8 that break a reading, each with the
shortest failing history; the refactoring is not flagged. It misses C7, a
denial during the penalty that does not restart it: that behaviour differs
from the reference only on a sequence two edits away from every request
sequence, and the models' own tests catch it. The proofs of §4.5 find it,
at six calls. Every observable mutant of the
four implementations changes some verdict under every reading.

**False assurance.** The naive flow certifies all 3 violations; FCP
certifies none, and on this prompt certifies nothing at all: each
model's code fails six of the seven requirements under an agent's reading
(five of those are also in a conflict), and the two agents read the
seventh differently. The
review queue is the conflict, the "previous call", and the window and
penalty edges.

### 4.5 Beyond the scope: proofs for dictionaries and lists

The scope of §4.2 has 175,528 calls, in sequences of at most 15. The
limiter takes any number of calls, for any customers, at any times. The
proofs of §2.6 cover objects whose fields are numbers; the limiter keeps a
dictionary of lists. They now cover that too
([fcp/keyed.py](../fcp/keyed.py), [fcp/keyedproof.py](../fcp/keyedproof.py)).

**Dictionaries and lists as terms.** A dictionary whose keys depend on the
arguments is the list of the writes made to it, oldest first, each with its
key, its value and the condition under which it happened. A read at key k
is decided by the newest write whose key equals k. A list is the guarded
slots of §3.5, a deque is a list that can also lose its first element, an
instance of a helper class is its fields, and a value that is None on some
paths carries a term that says where. Python shares lists, it does not copy
them: after `times = self.allowed[user]`, `times.append(now)` changes what
the dictionary holds. A name that came out of a dictionary therefore has a
home (the dictionary and the key), and a change through the name is also a
write to its home. A change through a name that another name may share is
refused. All thirteen implementations translate. Haiku's limiter keeps a
deque per customer, Sonnet's an object of a helper class per customer,
Opus's a `defaultdict` of deques, and each takes a lock. The translation is
checked as before: on every call of the scope, its outcome and its value
must equal the code's.

**Two models of the code.** The exact model unrolls the calls from the
constructor, with every dictionary as its list of writes. It decides a
requirement over every sequence of a few calls, for every customer and time
the interface carries: a requirement that fails gives a sequence z3 chose,
replayed on the code and on the compiled monitors (FAILS); one that holds
for up to k calls is PROVED-BOUNDED.

The abstract model is one call from any state (two, where the reading looks
back one call): a dictionary is any function of the key, a list is any list
of at most L numbers, and the state also holds the reading's ghosts and
registers, as in §2.6. L is the least of 1, 2, 3, 4, 6 and 8 that no call
exceeds from a state within it; the limiter's lists hold at most three
times. The abstract model is checked against the exact one: started from
the state the exact model has before a call, it must give that call's
outcome, value, verdicts and next state. A conjunction of facts about the
state that holds on a new object, and after every call from a state where
it holds, is an invariant; a requirement it implies holds at every call of
every sequence of any length (PROVED).

**Rules over every customer.** A reading that follows one customer (§4.3:
"for every customer U") is encoded with U as a constant z3 is free to
choose. A proof is then a proof for each customer, a counterexample names
one, and the invariant speaks of `self.allowed[U]`: what the dictionary
holds for the customer the reading follows.

**The invariant.** The candidates come from a grammar over the state:
bounds on each number, the order and the equality of two numbers (fields,
ghosts, elements of a list), their distance where the code or the reading
uses one (60, 61, 10), and each of these under a condition on a list's
length. That is 8,556 to 18,557 candidates per pair. They are first run on
up to 4,000 states the scope reaches, which removes most of the false ones
and proves nothing, and Houdini (§2.6) keeps the ones that are inductive:
147 to 568. Under the gold reading the reference's proof of rule 2 (at most
three allowed attempts in any 60 seconds) uses eight of them:

```
a1 >= a3        a2 >= a3        a3 >= -100        self.last >= last
len(self.allowed[U]) > 0   ->  self.allowed[U][0] >= a3
len(self.allowed[U]) > 2   ->  self.allowed[U][1] == a2
len(self.allowed[U]) > 2   ->  self.allowed[U][2] == a1
len(self.allowed[U]) <= 2  ->  a3 + 60 <= last
```

`a1`, `a2`, `a3` are the reading's own record of the customer's three most
recent allowed attempts, `last` the time of the previous call. The
invariant says how the code's list relates to that record: a full list is
the record, and where the code has dropped a time, the reading's third
attempt is at least a minute old. Nobody wrote it down; it is what the
search found and z3 checked.

**Results.** `experiments/prove_demo.py code_limit` runs the thirteen
implementations (three models, the reference, nine planted variants)
against the three readings: 39 pairs, all translated, 208 verdicts, 28 to
734 seconds per pair (median 86).

| | verdicts |
|---|---|
| Passed by the scope and proved for every sequence of any length | 58 |
| Passed by the scope and proved for every sequence of up to k calls | 7 |
| Failed by the scope and by the proof, z3's sequence replayed on the code | 140 |
| Passed by the scope of 175,528 calls, failed by the proof | 3 |

No verdict is left undecided, and none fails on the scope alone. Under the
gold reading the three models' limiters and the reference get the same
five verdicts: the four rules that can be kept are proved for every
sequence, and rule 4 (the conflict of §4.4) fails at five calls. The
refactoring C9, which keeps its window in a deque, is proved with the same
verdicts as the reference.

The three failures the scope missed, each replayed on the code and on the
monitors:

- **C7, the planted bug the scope study missed** (R-PEN-1, gold). A denial
  during the penalty must start it again; in C7 it does not.
  `allow(1000, 65472)`, `allow(1000, 65473)`, `allow(1000, 65474)` are
  allowed, `allow(1000, 65525)` is denied and starts ten seconds of penalty,
  `allow(1000, 65534)` is denied inside it, and `allow(1000, 65535)` must be
  denied; C7 allows it. In §4.4 this sequence was two edits away from every
  sequence of the scope. With the proofs, all eight planted bugs that break
  a reading are flagged.
- **C3 under agent B's reading of "attempts that were not allowed do not
  count"** (R-COUNT-1): eight calls over three customers, two of which
  raise. C3 already fails R-PEN-1 on the scope.
- **C5 under agent B's reading of rule 2** (R-MAX-1): eight calls in which
  time goes back, which C5 accepts where it must raise. C5 already fails
  three other requirements on the scope.

The seven verdicts proved only up to a bound are on two planted variants,
and all seven pass the scope. C2 appends denied attempts to the customer's
list, so its lists have no bound and there is no abstract state to start
from: four requirements under gold hold for every sequence of up to 15
calls, one under agent B up to 8. C4 keeps one list for all customers, and
the grammar has no invariant for a list that the followed customer shares:
rule 2 holds up to 12 calls under gold and up to 8 under agent B. Unlike
the four bounded verdicts of the gift card (§8.2), none of these seven is
known to fail beyond its bound; both variants are caught on other
requirements.

Agent A reads both windows as closed (§4.4). Under that reading nine of
the thirteen implementations fail every requirement within a few calls, and
nothing is left for the induction.

## 5. Changes: a change request to existing code

Most of what Claude Code does is change code that exists. A change request
has two specifications: the request, and the code before the change, which
defines everything the request does not touch.

### 5.1 The old code as an input

With `baseline` in the `function` section ([IR_spec.md](IR_spec.md) §1),
the code before the change runs on the same calls, with the arguments it
takes, and its answer drives three more *input* signals: `old_price`,
`old_ship` and `old_outcome` in the demo. A requirement can then relate the
new answer to the old one. Rule 3 of the demo, "nothing may change for
customers who are not students", reads:

```
!student -> outcome == old_outcome && price == old_price && ship == old_ship
```

This is a **change contract**. A regression is a call on which the new code
answers differently from the old where no requirement allows it: it fails
this property, at the simplest call, replayed. On the code side and in the
conflict search, the old answers are those of the actual old code. In the
spec-only analyses they are free, so two readings are compared for any old
code, which is stronger than comparing them for this one.

### 5.2 The demo: student pricing

**Change request** ([spec.md](../corpus/code_change/spec.md)), on the
checkout of §2 (the old code is [impl/old.py](../corpus/code_change/impl/old.py)
with its tests): students get 15% off, free shipping "now starts at $75
instead of $50", nothing may change for customers who are not students, and
everything else stays. For a non-student cart from $50.00 to $74.99 the old
code ships free, so rules 2 and 3 cannot both hold
([spec_defects.yaml](../corpus/code_change/spec_defects.yaml)).

**Before any code.** The conflict search finds it under all three readings
at a single call, `checkout(5000, 0, False, False)`, in 29 to 81 s (17,176 to
24,600 candidate pairs, the old code's answers prefetched in one run);
agent_a's reading is the one case where the trigger-situation check also
finds it. Compared in context, the agents differ from my reading on four
requirements, each shown by a call; the witnesses are bounded-model
counterexamples with extreme values, not the simplest calls.

**The code.** All three models applied $75 to students only and kept $50
for everyone else; Haiku called it a conflict, Opus explained that $75 for
everyone would break rule 3, Sonnet just chose. Under every reading each
breaks exactly rule 2, at `checkout(5000, 0, False, False) -> (5000, 0)`,
replayed; the reference makes the same choice. The three implementations
answer all 3.6 million calls of the scope identically, and each model's
tests (22, 29, 45) pass on all three. FCP flags all 8 planted bugs in their
requirement (a student discount that replaces the member discount, an
uncapped student discount, a rounding regression for everyone, a coupon
check skipped for students, shipping measured after discounts, a float price,
a large cart rejected for students, free shipping lost for members), and
not the refactoring; every observable mutant is killed. The naive flow
certifies the 3 violations; FCP none, and 12 of 18 pairs. (One planted
variant, the float price, did not parse in the first run because of a
quoting slip in its patch; it was fixed and its results recomputed.)

## 6. Effects: a payment retry

Code that charges a card, writes a file or calls a service cannot be judged
by its return value alone: what matters is what it did on the way.

### 6.1 The interface as the chip's other side

With `interface` in the `function` section ([IR_spec.md](IR_spec.md) §1),
the function receives a recording stand-in for the service
([fcp/effects.py](../fcp/effects.py)). A reset starts a run; every call the
code makes on the stand-in is one cycle, with the method and its arguments as
outputs and the stand-in's answer as an input, taken from a script; the
return is the last cycle, and stays until the next reset. The code never
really sleeps or charges. A run longer than `max_calls` calls ends as "did
not finish", which a frame rule states, so a rule such as "keep trying until
the charge goes through" can be broken by a run that never ends: without the
bound, a past-time rule could never see it fail.

The scope pairs every script of answers up to a length with every
combination of argument values; only methods with answers take an entry of
the script, so `["error", "error", "error"]` is three failed charges, however
many waits come between them. Before any code, the conflict search asks, for
each short script, whether any conversation meets every rule, with the
stand-in's answer at each cycle tied to the number of charges made before it.

Code that does not receive the service, but imports its client and calls
`time.sleep` itself, is checked the same way: the design says which names it
calls (`patch: payments.charge`, `patch: time.sleep`, and
`raises: {error: payments.ServiceError}` for an answer delivered as an
exception), and the sandbox installs the stand-in under those names before
the code is imported, creating a module it lacks. The reference's behaviour
written that way fails exactly the requirement the reference fails, and
without its waits it fails the waiting rule
([tests/test_effects_patch.py](../tests/test_effects_patch.py)).

Effects also go through objects the code makes itself: a file from `open`,
a socket from `socket.create_connection`. A method declared with `handle`
returns a stand-in object, numbered in the run (`f1`, `f2`), whose declared
methods record their calls on it; a `with` block closes it, and a call on a
closed object raises `ValueError`, as on a real file. Arguments that are not
integers become signals through small encodings: a path or a message by its
position in a list, written text by the number its digits spell, an `open`
mode as read, write, append or create, a file object or its `fileno()` as
its number. The run also keeps its own view of the disk: a file opened for
writing exists, `os.replace` moves it, `os.remove` deletes it, and
`os.path.exists` answers from that view. Removing or moving a file that is
not there raises `FileNotFoundError`, as it would on a disk, so code that
cleans up after the move crashes in the sandbox as it would in production
(§6.3, [tests/test_effects_files.py](../tests/test_effects_files.py), which
also checks a socket client: connections refused and accepted, bytes
answered, the `with` block closing the socket).

### 6.2 The demo: retrying a card payment

**Prompt** ([spec.md](../corpus/code_pay/spec.md)).
`charge_order(api, order_id, amount)` charges through `api.charge`, which
answers `"ok"`, `"declined"` or `"error"`, and waits with `api.sleep`:
retry an error, up to 3 attempts in total, never after a decline, wait 2 and
then 4 seconds, never charge again after an ok, and "keep trying until the
charge goes through, so that no order is lost". The last rule conflicts with
the 3-attempt limit when the service keeps failing
([spec_defects.yaml](../corpus/code_pay/spec_defects.yaml)).

**Before any code.** For the script `["error", "error", "error"]` no
conversation meets the rules: a fourth charge breaks the limit, returning
False breaks rule 7, returning True breaks rule 2, and a run that never
returns is cut off. The search finds it under every reading (67 to 200
seconds over 2,242 to 3,388 scripts). Both agents read rule 7 literally, so
their readings also conflict after a decline, which mine had resolved by
letting the code give up on a declined card. Both also noticed what my
decomposition dropped: the opening sentence ("charges a customer's card ...
retrying when the service fails") is the only text that obliges the function
to charge at all once rule 7 goes. The trigger-situation check calls every
reading consistent.

**The code.** All three models noticed the conflict, kept the 3-attempt
limit, and said that the caller must keep the order when the function returns
False; they also raised a risk no rule mentions, a double charge if an
"error" can mean the charge went through. Under every reading each breaks
exactly rule 7, on three errors, replayed. The three implementations make the
same calls on all 50,000 runs of the scope, and each model's tests pass on
the other two. FCP flags all 8 planted bugs (a retry after a decline, a
fourth attempt, halved waits, True for a decline, dollars for cents, a charge
of 0, a charge after an ok, None after three errors), each at its shortest
conversation; the refactoring is not flagged. Every observable mutant changes
a verdict. The naive flow certifies the 3 violations; FCP certifies none, and
9 of 27 requirement-implementation pairs overall.

### 6.3 Files the code opens: an atomic save

**Prompt** ([spec.md](../corpus/code_save/spec.md)). `save_balance(cents)`
writes the digits to `balance.txt.tmp`, calls `os.fsync` on it, closes it
and moves it over `balance.txt` with `os.replace`, never opening
`balance.txt` itself; it returns True once the balance is there; rule 6 says
"leave no temporary file behind", and rule 7 says that if `os.replace`
fails, keep `balance.txt.tmp` so the balance can be recovered, and return
False. Rules 6 and 7 conflict when the move fails
([spec_defects.yaml](../corpus/code_save/spec_defects.yaml)). Only
`os.replace` answers from the script: if every call on a file could fail,
a conversation could steer a scripted failure onto a harmless call (an
extra write) and the search, which asks for one conversation per script,
would find no conflict.

**Before any code.** For `save_balance(0)` with `os.replace` failing, no
conversation meets my reading: keeping the file breaks rule 6, removing it
breaks rule 7, and moving it again breaks rule 5 or 7, because a retry that
succeeds must return True under one and False under the other. The search
names it in 23 seconds over 217 scripts. Its first answer was an escape that
my reading allowed: remove the temporary file *before* moving it, so that
the failing move leaves nothing behind. "Move that file" means the file that
holds the digits, so the reading now requires it at the move.

**The code against my reading.** My reference keeps the file when the move
fails and so breaks rule 6, on exactly that run. Each of the 8 planted bugs
breaks something more (fsync without flushing Python's buffer, writing
`balance.txt` directly, moving before closing, rejecting 100,000,000,
removing the file in `finally` after the move, writing dollars, True after a
failed move, checking the balance after writing); the refactoring breaks
nothing more. The `finally` bug shows the run's own view of the disk: the
`os.remove` after a successful move raises `FileNotFoundError`.

**The agents' readings.** Both Opus formalizers found the conflict by hand
and named it, along with the retry trap (a second `os.replace` that succeeds
needs True under rule 5 and False under rule 7). The search finds the clash
under their readings too, on the same failing move, in 13 and 36 s; the
trigger-situation check misses it under all three readings. Both took the
reading of rule 4 that needs no flush before `os.fsync`, which the example
supports and my reading does not, and both read the example as an exact
sequence of calls, which no implementation meets because every one flushes.
Their readings differ from mine on six requirements, mostly in corners no
implementation reaches (a write after a close, a second open).

**The code.** Haiku, Sonnet and Opus all noticed the conflict and made the
same choice: rule 7 is the one exception to rule 6, so the temporary file is
kept when `os.replace` fails and removed after any earlier failure. Under
every reading each breaks exactly rule 6, at the failed move, replayed, and
beyond the scope (§2.6) each is proved on every other requirement, for every
balance and both answers of `os.replace`. They part on one point the
readings leave open: Opus first removes a stale temporary file and creates a
new one in exclusive mode (1,179 runs differ; on a fresh disk its `os.remove`
meets `FileNotFoundError` and goes on). Their test suites (18, 37 and 33
tests) fail on each other's code only on what the adapter does not script:
`open`, `write`, `fsync` or `close` failing, an interrupt, a stale temporary
file or link, the exact mode of `open`. FCP flags all 8 planted bugs in
their requirement under my reading and not the refactoring; every
observable mutant is killed. One planted bug shows what the flagged phrase
costs: `os.fsync` without a flush (C1), a real durability bug, fails no test
of any model and no requirement of either agent's reading, because both
took the reading without the flush; only my reading flags it. The naive flow
certifies the 3 violations; FCP none, and 6 of 24 pairs overall
([results](../experiments/results/code_save.json)).

### 6.4 Three services and an undo: placing an order

**Prompt** ([spec.md](../corpus/code_order/spec.md)).
`place_order(order_id, sku, qty, amount)` reserves the stock, charges the
customer and books the delivery through three imported modules, each step
at most once and in that order. When a step is refused or raises its
service's error the function stops, undoes the earlier steps (a refund if
the customer was charged, a release if the stock was reserved, each exactly
once; rule 7) and returns False. Rule 8 says "placing one order makes at
most four calls on them in total". Rules 7 and 8 conflict on one path only
([spec_defects.yaml](../corpus/code_order/spec_defects.yaml)): when the
booking fails, three calls have been made and two more undo them; every
other path takes at most three. The three steps answer from the script
("ok", "refused" or the error); the refund and the release return nothing.
I flagged the undo twice: the order of the refund and the release, and
whether the function may undo a step that was never taken.

**Before any code.** For `place_order(7, 3, 1, 1)` with the answers ok, ok,
refused, no conversation meets my reading. The search names it in 46
seconds over 4,356 scripts; the trigger-situation check finds the reading
consistent. The clash needs six requirements together (the steps, their
order, once each, the return value, the undo and the limit), so no pair of
rules shows it.

**The agents' readings.** Both Opus formalizers found the conflict by
reading and named it; both read the undo as "in either order" and "only for
a step that was taken". The search finds the clash under their readings on
the same call and answers, in 62 and 64 s. The first run found nothing
under agent A's reading, and its comparison put agent A below agent B on
eight requirements, so FCP held all 30 pairs. Both came from one gap in the
adapter (§10): the `answer` input was free at the cycles where no service
answers, so a reading that assumes "the answer is 0, 1 or 2" at every
cycle, as agent A's does, could be escaped there, and with it every later
obligation. The search now fixes the answer to 0 at those cycles, as every
recorded run has it, and the frame of this task states the same as a rule
(F-ANS), so that comparisons range over such runs only. With the rule the
two agents' readings are equivalent in context on every requirement but
the undo, where agent A's also rejects a refund made before any step has
failed and agent B's judges only the return of a failed run.
My reading has no assumptions, so against each agent it looks stronger on
eight requirements, on runs no trace has (an answer of 3, arguments that
change within a run). Compared under the agent's own assumptions
(`experiments/compare_env.py`) it is equivalent in context on seven of
nine; the other two differ in form (a stray release rejected at the call or
at the return).

**The code.** Haiku, Sonnet and Opus all named the contradiction and made
the same choice: the undo is kept and rule 8 yields, with five calls when
the booking fails. Haiku recorded it as an expected failure in its own
tests. The three answer all 46,400 runs of the scope identically, and under
every reading each breaks exactly R-LIMIT-1, as my reference does. Beyond
the scope (§2.6) each is proved on every other requirement, for every
argument and every script of answers, under all three readings; Opus's
code needed the translator to read a helper that is passed the service
call, its error class and `*args` (§10). With my reference and the nine
variants, all 39 pairs translate: 278 requirements are proved, and the 73
that fail on the scope fail the proof too
([results](../experiments/results/prove_code_order.json)). Their suites (31, 53 and 51 tests) pass on each other's code, but
for three of Opus's tests on Haiku's, where a service raises another
service's error, which the prompt does not cover. FCP flags all 8 planted
bugs in their requirement under my reading (a quantity of 100 rejected, an
amount of 0 accepted, a payment error that leaves the function, no release
after a refused charge, no refund after a failed booking, a refund of the
quantity, a second booking after an error, a release of stock never
reserved) and not the refactoring; here the models' suites also catch all
eight, with between 1 and 21 failing tests. Every observable mutant (17, 19
and 18) is killed under every reading.

**False assurance.** The naive flow certifies the 3 violations (R-LIMIT-1
for each model): every suite passes, Haiku's because the failing case is
marked as expected. FCP certifies none of them, and 12 of 30 pairs: the
argument checks, the arguments of each call, the return value and stopping
at a failed step, for each model. The steps, their order and "once each"
pass under every reading but belong to the conflict, the undo is flagged
and read differently by the two agents, and the example is a scenario,
which the comparison of readings does not cover
([results](../experiments/results/code_order.json)).

## 7. Records: invoice lines

Most code that people ask for takes and returns records: a list of order
lines, a dict of settings, a row from a table.

### 7.1 How a record becomes signals

A record is one signal per field, and a list of records one sequence signal
per field, the fields an interface `group` that always has one length
([IR_spec.md](IR_spec.md) §1). Item `i` of the list is `price[i]`,
`qty[i]`, `sale[i]`, so a rule over the items is a quantifier over `i`, as
for any list. The runner builds the dicts (or, with `class`, objects of the
implementation's own record class) and takes the returned dict apart; a dict
with other keys, a tuple or a value out of range is "returned something
else". The harness, the integer encoding and the spec solver keep the fields
of a group at one length, so no witness is a list of records that cannot
exist. Edits on a list of records delete, insert, repeat or swap whole
records, besides changing one field.

### 7.2 Boundaries of computed values

The scope of §3.2 solves every condition with the outputs free, so a rule on
a computed value, such as "a subtotal of $10.00 or more", gives no input at
its boundary: the subtotal is an output. The scope now also solves every
condition and comparison that mentions an output with the outputs obeying
every property of one reading, under the condition that makes it matter
(`subtotal >= 1000` inside `member && subtotal >= 1000` is solved for a
member). The inputs then produce exactly the boundary value: a member's
items whose prices times quantities sum to 1,000 cents. These points come
after all others, so the scope of every earlier study is unchanged and only
grows. The conflict search on sequences now also shrinks each conflict it
finds to the simplest stimulus that still conflicts, one deleted record or
smaller value at a time.

### 7.3 The demo: invoice lines

**Prompt** ([spec.md](../corpus/code_invoice/spec.md)). `invoice(items,
member)` takes a list of `{"price", "qty", "sale"}` dicts and returns
`{"lines", "discount", "total"}`. Members get 10% off every line not on sale,
rounded down to the cent; `discount` is 10% of the summed lines not on sale,
rounded down; `total` is the sum of the lines, and also the full price minus
`discount`. Rounding each line and rounding the order are two different
computations, so the last two rules conflict whenever the lines' lost
fractions add up to a cent or more, which takes two lines or more
([spec_defects.yaml](../corpus/code_invoice/spec_defects.yaml)).

**Before any code.** The conflict search finds the clash under all three
readings, each time on two items, in 21 to 27 s: for a member, items of
3 and 7 cents give lines of 3 and 7 (neither line's tenth reaches a cent),
so rule 5 makes the total 10, while rule 4 gives a discount of 1 and rule 6
a total of 9. A single line never conflicts. Both agents also found it by
hand, read rule 4 literally, and read "rounded down" in rule 3 as the
discount, which the example confirms; their readings agree with each other
and with mine on every requirement in context.

**The code.** Haiku, Sonnet and Opus all noticed the conflict and made the
same choice: round each line, and report as `discount` the sum of the line
discounts. Under every reading each breaks exactly rule 4, on two items,
replayed. The three implementations answer every call of the scope (110,000
to 115,000 calls, as each scope adds the code's own constants) identically;
their test suites (19, 35 and 23 tests) disagree only on malformed input
the prompt does not cover and the scope leaves out (floats, strings, missing
keys, a member that is not a bool). FCP flags all 8 planted bugs in their
requirement (the line rounded instead of its discount, sale lines
discounted, sale items in the order discount, an empty order accepted, the
lines reversed, the first item's sale flag for every line, a zero quantity
accepted beside others, a tuple), and not the refactoring; every observable
mutant is killed. The naive flow certifies the 3 violations; FCP none, and 6
of 24 pairs overall.

## 8. Objects with several methods: gift cards

### 8.1 One chip, several methods

A class with several methods is still one chip with memory. Each cycle calls
one method, chosen by an `op` input, with the arguments that method takes;
methods may share an argument signal, and the arguments the called method
does not take are 0 in the harness, the integer encoding and the spec solver
alike ([IR_spec.md](IR_spec.md) §1, `methods`). Each method has its own
result signals, 0 when another method is called (a frame rule says so), and
calls are written as the methods: `load(49501)`, `balance()`. The scope is
that of §4.2, with the method as one more argument of every call, and object
conflicts are now shrunk like sequence ones: calls dropped and values
lowered within their pools, while a clock keeps its values.

### 8.2 The demo: a gift card

**Prompt** ([spec.md](../corpus/code_card/spec.md)). `GiftCard` with
`load(amount)` (returns the bonus it earned), `spend(amount)` (True if the
balance covers it) and `balance()`: amounts from 1 to 50,000 cents, the
balance never over $500.00 ("raise ValueError for a load that would take it
over"), and a $5.00 bonus for every load of $100.00 or more. Read literally,
a load that takes the balance to between $495.01 and $500.00 is valid, and
its bonus then breaks the cap; read with the bonus counted, there is no
conflict ([spec_defects.yaml](../corpus/code_card/spec_defects.yaml)). I
flagged the phrase as ambiguous on R-CAP-1.

**Before any code.** Under the literal reading (gold) the conflict search
finds `load(49501); balance()` in 1 s: the load must go through, earn 500,
and the balance must then read 50,001, over the cap. Both agents read the
phrase the other way, counting the bonus, so neither of their readings has a
conflict (237 and 127 candidate sequences). The comparison shows it as
disagreements between gold and each agent on R-LOAD-1 and R-CAP-1, at
`load(49501)`; the two agents agree with each other on every requirement in
context.

**The code.** All three models counted the bonus too: a load whose bonus
would pass $500.00 raises ValueError. Only Opus said that the team should
confirm this. The three implementations answer all 64,576 calls of the scope
identically, each model's tests (21, 38 and 42) pass on all three, and under
both agent readings nothing fails. Under gold each breaks exactly R-LOAD-1,
at `load(49501) -> raised ValueError`, replayed. FCP flags all 8 planted bugs
in their requirement (a bonus that needs more than $100.00, a load to exactly
$500.00 rejected, an overdrawn card, a spend of exactly the balance refused,
an amount of 0 accepted, a refused spend that empties the card, a bonus never
put on the card, a balance in dollars), and not the refactoring; every
observable mutant is killed.

**False assurance.** Here FCP certifies all three violations. Two isolated
readers and three models made the same choice on a phrase I had flagged; the
flag holds R-CAP-1 (21 of 24 pairs are certified, not 24), but the
consequence lands on R-LOAD-1, whose text uses the same condition without
the flag. Agreement among independent readers is evidence about the
readers, not about the request, and a flag on one requirement says nothing
about the requirements its answer decides.

**A reading per answer.** A flag is a question whose answer the readers
settle silently; what it decides is not written anywhere. So one more
isolated Opus agent formalized the whole prompt with the flagged phrase
fixed to the reading neither agent had chosen (the decomposer lists both),
and FCP compared that variant with each agent reading in context. They
differ on exactly R-LOAD-1 and R-CAP-1, which are then held as depending on
the question: FCP certifies none of the three violations, and 18 of 24
pairs instead of 21 ([code_card_variant.json](../experiments/results/code_card_variant.json)).
I designed this after seeing the failure. §8.4 measures it on all ten
code tasks, and `fcp review` runs one such reader on the flagged phrases
for which both readers recorded the same listed reading (§9). The variant
agent also found two engine issues: a look-back inside
`once` delays the evaluation of the whole cover that contains it, which can
make a scenario unreachable, and the spec-only check does not test that a
scenario is reachable at all (a cover asking for `bal == 1500 && bal == 1501`
passed).

### 8.3 A package: loyalty points

**Prompt** ([spec.md](../corpus/code_loyal/spec.md)). A package `loyalty`
in three modules: `tiers.py` (basic under 500 points, silver from 500, gold
from 2,000; 1, 2 and 3 points for each dollar), `points.py` (a purchase
earns for each whole dollar at the rate of the account's tier, never more
than 1,000 points) and `account.py`, the class `Account` with
`earn(amount)`, `redeem(points)`, `tier()` and `balance()`. Rule 9 adds
"members keep what they have reached: the tier that `tier` returns never
goes down". After `earn(50000)` the account has 500 points and `tier()`
returns 1; after `redeem(1)` it has 499, so rules 1 and 8 make the next
`tier()` return 0 and rule 9 forbids it
([spec_defects.yaml](../corpus/code_loyal/spec_defects.yaml)). I flagged
"the rate of the account's tier" (before the purchase, or once its points
are added?) on R-POINTS-1 and the cap on R-CAP-1.

**What a package changes.** The design names the class by its module
(`module: loyalty.account`); an implementation is a directory, run with the
package on the path, so the rule in `tiers.py` is checked through the calls
on `Account` that reach it. Mutants are drawn from all three modules in
turn, and the planted bugs sit in each of them (two in `tiers.py`, two in
`points.py`, four in `account.py`).

**Before any code.** The conflict search names
`earn(50000); tier(); redeem(1); tier()` in 1.6 s under my reading (253
candidate sequences), and under both agents' readings in 13 and 78 s, as
R-GET-1 against R-KEEP-1; the trigger-situation check misses it under all
three. Both Opus formalizers had found the conflict by reading, and both
formalized the two sides literally. Agent B's reading is equivalent to mine
on every requirement in context. Agent A's keeps the points in hundredths
in a ghost and computes with `%` and `*`; the bounded comparison leaves five
of its requirements undecided against mine (UNKNOWN), which FCP holds
exactly like a disagreement.

**The code.** No model said that the rules conflict. Haiku, Sonnet and Opus
each store the highest tier the account has reached and return it from
`tier()`: rule 9 wins and rule 1 yields, silently. All three then let the
kept tier set the rate as well (Sonnet and Opus say so; a gold member who
redeems down to 0 points still earns 3 points for each dollar), which no
rule asks for. The three packages answer all 44,079 calls of the scope
identically. Under my reading each breaks R-TIER-1 (`earn(50000) -> 500 |
redeem(50) -> True | tier() -> 1`, 180 calls) and R-POINTS-1 (`earn(50000)
-> 500 | redeem(1) -> True | earn(199) -> 2`, 123 calls), replayed; my
reference follows rule 1 and breaks R-KEEP-1 (43 calls). FCP flags all 8
planted bugs in their requirement under my reading, whichever module they
are in, and not the refactoring. Of the observable mutants (48, 41 and 43)
one survives per model, under every reading: the gold rate of 3 changed to
4. The scope reaches gold only through capped purchases, so the change
shows at one call, where a member who redeemed down from gold earns at the
kept rate, and that call already fails.

**Tests tied to names.** The prompt names the modules and the class, not
the functions inside `tiers.py` and `points.py`, and each model chose its
own (`points_earned`, `points_for_purchase`, `purchase_points`). Each suite
(32, 74 and 72 tests) imports its own names, so it passes on its own package
and does not even load on another model's, on my reference or on a planted
bug: the comparison of suites made for the single-file tasks cannot be made
here. A reading is stated on the interface the prompt gives and runs on all
of them. What can be measured is each suite on the mutants of its own
package (`experiments/own_tests_mutants.py`): Haiku's kills 47 of 48,
Sonnet's 41 of 41 and Opus's 43 of 43 (two because the mutant never
returns), against 47, 40 and 42 for FCP under every reading. Each suite
tests the rate table directly and kills the gold rate of 4 that the scope
misses; Haiku's misses the basic tier numbered -1 instead of 0, because
its tests compare with the package's own constant, while `tier()` returns
-1 and FCP flags it.

**False assurance.** The naive flow certifies all 6 violations (R-TIER-1
and R-POINTS-1 for each model): each suite passes on its own package. FCP
certifies none of them, and 6 of 30 pairs (R-NEW-1 and R-RANGE-1 for each
model). Under the agents' readings the kept tier fails five requirements
(R-TIER-1, R-POINTS-1, R-EARN-1, R-REDEEM-1 and R-GET-1), R-POINTS-1 and
R-CAP-1 are flagged, R-GET-1 and R-KEEP-1 are in the conflict, and the
example is a scenario, which the comparison of readings does not cover
([results](../experiments/results/code_loyal.json)).

### 8.4 A reading per answer, on all ten tasks

§8.2 measured the reading per answer on the task whose failure prompted it.
[experiments/variant_demo.py](../experiments/variant_demo.py) runs it on all
ten code tasks. The measures were fixed before any new reader was compared:
the false certifications before and after; the true certifications that are
held back, and of those how many a comparison shows to differ and how many
stand behind a comparison that did not end; both again for the readers on
each side of an answer; and the cost in agent runs.

**The readers.** The ten tasks flag 20 phrases; each lists two readings, one
lists three. A task gets one more isolated Opus reader per position in those
lists: reader k formalizes the whole prompt with every flagged phrase fixed
to its k-th listed reading (a phrase with fewer readings is left to it),
under the prompt of the stored readers plus those instructions. That is 21
readers: the stored variant of the gift card and 20 new ones. Each is
compared in context with each of the two stored agent readings, by the
comparison of the task's own study. A requirement on which a new reader
differs from one of the two, or on which their comparison does not end, is
held as depending on the question, as in §8.2. What is counted is what the
studies above count. A cell is a requirement of a task under one of its
three model implementations (the requirement-implementation pair of those
studies), it is violated when the implementation breaks the requirement
under the reference reading, and the rule for what is certified is
unchanged.

**A control.** Telling a reader "the other side" needs the side the two
readers took, and the stored readings of six tasks do not say. Those of
loyalty points, the order and the atomic save record which listed reading
they took of every flagged phrase, and §8.2 established it for the gift
card. In these four tasks both readers took the same listed reading of every
flagged phrase, so reader k is on their side for one k and on the other side
for the other. The reader on their side shows what a third reader holds back
merely by being a third reader.

**What the readers cost.** The 20 new readers took 6,831 s of agent time
(159 to 679 s each), 285 turns and $24.67 ($0.65 to $2.24 each);
[variants/runs.jsonl](../experiments/results/variants/runs.jsonl) has one
record per run, and every reader fixed the phrases as told. Comparing a new
reader with the two stored ones took 6 to 72 s for most of them, 237 s for
one reader of the invoice, 430 and 1,592 s for the two of loyalty points and
2,976 and 14,994 s for the two of card masking, whose readings compare
strings. So on these tasks the step costs two formalizer runs per task,
about $2.50 and 11 minutes of agent time, and three where a phrase lists
three readings. The comparisons are engine time, with no agent in them. On
card masking they are the larger cost by far: 5 hours for two readers that
their agents wrote in 9 minutes.

**One reader the engine could not compare at first.** Reader 1 of the rate
limit wrote three rigid variables (a customer and two times) whose values
combine in 4.3 x 10^12 ways. A comparison confirms a counterexample over
rigid values by a replay, a replay runs at most 4,096 combinations, and the
comparison ended in an error. Nothing had told the reader of that limit;
`fcp lint` now warns above it, and a counterexample that cannot be replayed
leaves its direction undecided (§10). With that change the reader is
compared, in 7 and 13 s. It differs from neither stored reader on R-ERR-1
and R-RET-1. On R-MAX-1, R-FAIR-1 and R-PEN-1 one direction stays undecided
against both: whether reader 1 accepts a run that the stored reader rejects.
The engine has a candidate run there and cannot confirm it, because that
takes the replay that cannot run. In the other direction the engine shows a
sequence of calls that the stored reader accepts and reader 1 rejects in
four of the six comparisons, and finds none in the other two (R-MAX-1 and
R-FAIR-1 against the first stored reader): its bounded check runs 8 cycles
and reports a disagreement two cycles after it happens, so it covers the
first 6. The three requirements are held. Reader 2 differs from a
stored reader on these three and on R-ERR-1 and R-RET-1. The rate limit
certifies nothing before the step (§4.4): each model's code breaks six of
its seven requirements under a stored reading, and the two stored readers
read the seventh differently. So this reader cannot change a count below.

**One reader that is expensive to compare.** Reader 2 of card masking takes
a digit to be any character for which Python's `str.isdigit` holds and
allows a separator only between two digits, and its checksum counts inside a
sum. Several directions of its comparison with a stored reading get no
answer from the integer encoding. Each of those goes to a search of 200
calls of the scope and, where that finds nothing, to the bit-level model
with a limit of 30 minutes. The first attempt ended at the 4 GB memory cap
that was enough for every other comparison: one bit-level process held 3.7
GB after 23 minutes. I ran it again alone, from a checkout of the commit
that its record names, under a cap of 16 GB and with two bit-level
processes. The two pairs took 7,482 and 7,512 s, and the memory peaked at
6.2 GB. (Reader 1 of card masking ran under the 4 GB cap with one bit-level
process, 1,128 and 1,848 s. The `settings` field of
[variants/mask.json](../experiments/results/variants/mask.json) is written
by the last run and names two.) On the three requirements that are certified
before the step (R-EX-1, R-MASK-1, R-SEP-1) reader 2 differs from neither
stored reader, so card masking keeps its 9 certificates. It differs from
both on R-RET-1. Two questions did not end, against either stored reader. On
R-ERR-1 the comparison shows a call that reader 2 accepts and the stored
reader rejects, and does not decide whether a call exists the other way
round. On R-QUARTER-1 it decides one direction against the first stored
reader (no call exists that this reader accepts and reader 2 rejects) and
neither direction against the second. Both requirements are held, as the
rule says. R-ERR-1 is flagged and R-QUARTER-1 is in a conflict (§3.4), so
neither is certified before the step and no count changes.

**Results.** The ten tasks have 246 cells, and 33 of them are violated.
"Certified (false)" counts the cells FCP certifies and, of those, the
violated ones.

| Task | Flagged phrases | Readers | Cells | Certified (false) | Held where a new reader differs | Certified (false) | Held where a new reader may reject | Certified (false) |
|---|---|---|---|---|---|---|---|---|
| gift card | 1 | 2 | 24 | 21 (3) | R-CAP-1, R-LOAD-1 | 18 (0) | R-LOAD-1 | 18 (0) |
| price change | 1 | 2 | 18 | 12 (0) | R-SHIP-1 | 12 (0) | R-SHIP-1 | 12 (0) |
| checkout | 3 | 3 | 27 | 9 (0) | R-ROUND-1, R-SHIP-1 | 9 (0) | R-ROUND-1, R-SHIP-1 | 9 (0) |
| invoice | 2 | 2 | 24 | 6 (0) | R-MEM-1 | 6 (0) | R-MEM-1 | 6 (0) |
| rate limit | 4 | 2 | 21 | 0 (0) | R-ERR-1, R-FAIR-1, R-MAX-1, R-PEN-1, R-RET-1 | 0 (0) | R-ERR-1, R-FAIR-1, R-MAX-1, R-PEN-1, R-RET-1 | 0 (0) |
| loyalty points | 2 | 2 | 30 | 6 (0) | R-GET-1, R-POINTS-1, R-REDEEM-1 | 6 (0) | R-GET-1, R-POINTS-1, R-REDEEM-1 | 6 (0) |
| card masking | 2 | 2 | 21 | 9 (0) | R-ERR-1, R-QUARTER-1, R-RET-1 | 9 (0) | R-ERR-1, R-QUARTER-1, R-RET-1 | 9 (0) |
| order | 2 | 2 | 30 | 12 (0) | R-STEPS-1, R-UNDO-1 | 12 (0) | R-STEPS-1, R-UNDO-1 | 12 (0) |
| payment retry | 1 | 2 | 27 | 9 (0) | R-CALL-1, R-DECL-1, R-ERR-1, R-KEEP-1, R-RET-1, R-RETRY-1, R-WAIT-1 | 3 (0) | none | 9 (0) |
| atomic save | 2 | 2 | 24 | 6 (0) | R-CLEAN-1, R-ERR-1, R-KEEP-1, R-RET-1, R-STORE-1, R-SYNC-1, R-TMP-1 | 0 (0) | R-CLEAN-1, R-KEEP-1, R-SYNC-1, R-TMP-1 | 6 (0) |
| **all** | 20 | 21 | 246 | 90 (3) | | 75 (0) | | 87 (0) |

**The designed rule.** Before the step FCP certifies 90 cells, and 3 of them
are false: the gift card's. With every requirement held on which a new
reader differs from a stored one, 75 are certified and none is false. The
step removes the three false certificates and holds back 12 true ones. For
every one of those the comparison shows a run; none stands behind a
comparison that did not end. Most held requirements cost nothing, because
they were not certified before the step: their text is flagged, they are in
a conflict, the two stored readers already read them differently, or a
model's code breaks them under a stored reading. The counts change on five
requirements: R-LOAD-1 in the gift card, which is the failure of §8.2, and
four in two other tasks.

**Where the true certificates go.** All 12 are in the payment retry
(R-CALL-1 and R-ERR-1 under each model) and the atomic save (R-ERR-1 and
R-RET-1). In both tasks a new reader differs from the stored ones on seven
of the eight requirements that both state (the three frame rules aside),
flagged or not, and for most of the seven the cause is not the answer it was
told. In the payment retry the stored readers assume that the service's
answer is one of three *at a charge*; reader 2 assumes it in every cycle. In
the atomic save both new readers assume that the argument does not change
during a run, a fact of the frame that the stored readers do not state. A
reading asks nothing of a run that breaks its assumptions. So on these
requirements the new reader accepts runs that the stored readers reject (an
answer of 3 where no charge is made, an argument that changes in mid-run),
and no call of any code gives such a run. The control says the same: in the
atomic save the reader on the side of the two differs on as many
requirements as the reader on the other side.

**On the runs that meet the new reader's assumptions.** Where a new reader
assumes all that a stored reader assumes and more, `variant_demo.py under
TASK` compares the pair again on the runs that meet the new reader's
assumptions. The command runs on the three tasks whose code calls a service.
In the order the readers assume the same, so nothing is compared again; the
pairs of the payment retry's reader 2 and of the atomic save's two readers
are compared again in 6 to 19 s each. The payment retry's reader 2 then
differs on R-RET-1 alone, and the save's readers on three requirements each
(reader 1 on R-KEEP-1, R-SYNC-1 and R-TMP-1; reader 2 on R-CLEAN-1, R-SYNC-1
and R-TMP-1). None of those is certified before the step. With the
requirements held that differ in these comparisons, the 12 true certificates
stay and the three false ones go.

**A second rule.** The designed rule holds a requirement on any difference.
A certificate, though, says that the code meets a requirement as the two
stored readers state it, and it stays true under any reading that accepts
every run they accept. A new reading can take a certificate away only where
it rejects a run that a stored reading accepts. The second rule holds a
requirement only there: where the comparison shows such a run, or did not
end. It needs no further comparison, because the stored results keep the
direction of every difference. Under it 87 cells are certified, none is
false, and no true certificate is held back; applied to the comparisons of
the paragraph above instead, it holds the same requirements. I wrote this
rule after seeing the results of the first, so these numbers describe the
ten tasks and do not test the rule. It also inherits a limit of every
comparison in context: a run on which two rules of the new reader fail
together lies outside both of their comparisons.

**The rule of `fcp review`.** That limit matters once the rule decides a
certificate. A comparison in context looks only at runs on which every
other rule of both readings holds. The code was checked against the stored
readings, and nothing says that it meets the new reader's other rules: a
run of the code may break one of them and lie outside the comparison.
`fcp review` therefore lets a requirement go only where no run that a
stored reader accepts and the new reader rejects was found in context and
none without context. The comparison without context ranges over every
run, so the new reader's rule then accepts what the stored rule accepts,
whatever the run does on the other requirements. Counted per reader, this
rule holds 39 requirements, where the second rule holds 27 and the designed
rule 48. Each of the 12 it adds is, against at least one stored reader, a
difference in the harmless direction in context (A-STRONGER) and in both
directions without it (INCOMPARABLE): R-CAP-1 for the gift card's reader
1, R-SHIP-1 for the price change's reader 2, R-ROUND-1 for the checkout's
reader 2, R-MAX-1 and R-PEN-1 for the rate limit's reader 2, and in the
atomic save R-CLEAN-1, R-RET-1 and R-STORE-1 for reader 1 and R-KEEP-1,
R-RET-1, R-STORE-1 and R-SYNC-1 for reader 2. The 9 it lets go are
A-STRONGER with and without context: the seven of the payment retry's
reader 2, and R-ERR-1 of the atomic save for both readers. Per task it
holds what the second rule holds and, in addition, R-CAP-1 in the gift
card and R-RET-1 and R-STORE-1 in the atomic save. Under it 84 cells are
certified and none is false. Three true certificates are held back,
R-RET-1 of the atomic save under each model's code; no other requirement
it adds was certified before the step. I wrote this rule after a review of
the engine found the gap (§10), so these numbers too describe the ten
tasks and do not test the rule. One limit stays. A requirement on which
the new reader agrees with the stored ones in context is never held. The
comparison in context covers only runs that meet every other rule of both
readings, so a run of the code that breaks any other rule of the new
reader, or another requirement under a stored reader, is outside what the
step sees, and the new reader may reject it on this requirement.

**Sides.** In four tasks the side of the two stored readers is known (the
control above), so each new reader is on their side or on the other side.

| Task | Reader | Differs on | Certified (false) | May reject on | Certified (false) |
|---|---|---|---|---|---|
| gift card | side of the two | none | 21 (3) | none | 21 (3) |
| gift card | other side | R-CAP-1, R-LOAD-1 | 18 (0) | R-LOAD-1 | 18 (0) |
| loyalty points | side of the two | R-GET-1, R-REDEEM-1 | 6 (0) | R-GET-1, R-REDEEM-1 | 6 (0) |
| loyalty points | other side | R-GET-1, R-POINTS-1, R-REDEEM-1 | 6 (0) | R-GET-1, R-POINTS-1, R-REDEEM-1 | 6 (0) |
| order | side of the two | R-STEPS-1, R-UNDO-1 | 12 (0) | R-STEPS-1, R-UNDO-1 | 12 (0) |
| order | other side | R-UNDO-1 | 12 (0) | R-UNDO-1 | 12 (0) |
| atomic save | side of the two | R-CLEAN-1, R-ERR-1, R-KEEP-1, R-RET-1, R-STORE-1, R-SYNC-1, R-TMP-1 | 0 (0) | R-KEEP-1, R-SYNC-1, R-TMP-1 | 6 (0) |
| atomic save | other side | R-CLEAN-1, R-ERR-1, R-KEEP-1, R-RET-1, R-STORE-1, R-SYNC-1, R-TMP-1 | 0 (0) | R-CLEAN-1, R-TMP-1 | 6 (0) |
| **all 4** | side of the two | | 39 (3) | | 45 (3) |
| **all 4** | other side | | 36 (0) | | 42 (0) |

The reader on the other side removes the three false certificates under both
rules. The reader on the side of the two removes none: it reads the gift
card as they did. Under the designed rule the same-side readers still hold
back 6 true certificates, the atomic save's, as many as the other-side
readers do; under the second rule neither holds back any. Under the rule of
`fcp review` each holds back three, R-RET-1 of the atomic save: 42 cells
are certified with the readers on the side of the two (3 false) and 39
with the readers on the other side (none false). A third reader as such is
therefore no protection, and under the designed rule and the rule of
`fcp review` it is a cost.
What removes the false certificates is the other answer.

**What a third reader does not see.** The reference reading shows where the
two stored readers share a reading that differs from it. (For the three
tasks whose code calls a service the reference is compared with each of the
two on the runs that meet that reader's assumptions,
[compare_env.py](../experiments/compare_env.py): the reference assumes
nothing, so on runs no service produces it differs from every reading that
assumes something.) The two agree with each other and are both shown to
differ from the reference on 13 requirements, 9 of them without a flag. Only
one direction of difference can make a certificate false: each of the two
accepts a run that the reference rejects. That holds on 8 requirements, 5
without a flag.

| Task | Requirement | Flagged | A new reader differs | A new reader may reject | `fcp review` holds it for |
|---|---|---|---|---|---|
| gift card | R-LOAD-1 | no | reader 1 | reader 1 | reader 1 |
| price change | R-SHIP-1 | yes | reader 1, reader 2 | reader 1 | reader 1, reader 2 |
| price change | R-STU-1 | no | none | none | none |
| rate limit | R-ERR-1 | yes | reader 2 | reader 2 | reader 2 |
| rate limit | R-RET-1 | no | reader 2 | reader 2 | reader 2 |
| payment retry | R-ERR-1 | no | reader 2 | none | none |
| atomic save | R-CLEAN-1 | yes | reader 1, reader 2 | reader 2 | reader 1, reader 2 |
| atomic save | R-STORE-1 | no | reader 1, reader 2 | none | reader 1, reader 2 |

A new reader differs from the stored ones on 7 of them and may reject on 5;
the rule of `fcp review` holds 6, those five and R-STORE-1 of the atomic
save. All five lead back to a flagged phrase. R-SHIP-1 of the price change,
R-CLEAN-1 of the atomic save and R-ERR-1 of the rate limit are flagged
themselves. R-LOAD-1 of the gift card and R-RET-1 of the rate limit are not,
and each follows from the answer to a phrase flagged on another requirement:
R-LOAD-1 carries the three false certificates; R-RET-1 ("For a valid call,
allow returns True or False") turns on which calls are valid, and that turns
on "the previous call". The other three turn on no listed answer. The stored
readings of "A student gets a 15% discount" accept a call that ends in
another exception; those of "With an amount outside 1 to 1,000,000 the
function raises ValueError" accept calls of the service before the error;
those of "The balance ends up in balance.txt as its decimal digits" accept a
second `open` during the write. On these three every new reader accepts, in
context, what the stored readers accept. No model's code does any of it, so no certificate
is false there. Had a model's code done it, the second rule would not have
held the requirement, the rule of `fcp review` would have held R-STORE-1
alone, on a difference without context, and the designed rule would have
held two of the three only through the blanket difference described above.
A reading per answer guards a question that was asked. A reading of words
nobody flagged, which two readers share, a third reader under the same
prompt shares too.

**What this shows.** The ten tasks hold three false certificates, all in the
gift card, so what the step removes is measured on that one task; the other
nine show what it costs. It costs two or three formalizer runs per task.
With the designed rule it also costs 12 of the 87 true certificates, for a
reason that has nothing to do with the question asked: a reader that states
one more assumption differs on nearly every requirement. Holding a
requirement only where the new reader may reject a run in context keeps all
87 and still removes the three, on the assumption that the code meets the
new reader's other rules, which nothing checked. `fcp review` drops that
assumption for the requirements on which the new reader differs in
context: once it has the code it holds such a requirement where the new
reader may reject a run in context or without it, which keeps 84 of the 87
and removes the three. The certified cells on requirements that are equal
in context still rest on it. To the questions it asks before any code it applies
the designed rule (§9, §10).

## 9. One command: `fcp review`

Every study above was assembled by hand: I wrote each adapter and
decomposition, and ran the agents. `fcp review` does it from the request and
the code alone ([fcp/review.py](../fcp/review.py)):

```bash
bin/fcp review --request request.md --code answer.py --out review/
bin/fcp review --request request.md --code answer/ --entry shop.cart --out review/   # a package
bin/fcp review --request request.md --signature stub.py --out review/                # before any code
```

1. **Adapter.** An agent sees the request and the code's public signature
   (never its body or its private helpers, whose names can tell how the code
   resolves the request) with the four checked designs as examples, and
   writes design.yaml and frame.md; `fcp lint` must pass.
2. **Requirements.** A decomposer agent writes anchored requirements, flagging
   ambiguities and contradictions.
3. **Readings.** Two isolated formalizer agents, at the same time. Each
   records which listed reading it took for every phrase the decomposer
   flagged. Where both took the same one, a third isolated formalizer reads
   all those phrases the other way (the variant); every requirement on which
   it differs from the two readings in context depends on that shared answer
   and becomes a question (§8.2). Once there is code, a requirement waits
   for that answer only where the variant may reject a run that one of the
   two readings accepts: such a run was found, in context or without it,
   or one of the two searches did not end. Where the variant accepts every
   run they accept, with and without context, the certificate stands
   under it, and the report says so (§8.4, §10). A requirement that the
   review does not certify stays in the question.
4. **The request alone**, then **the code** on the scope, as in the studies.
   Every search has a time: two minutes to draw the scope (`--budget`), five
   for the conflicts of one reading (`--conflict-budget`), five for one
   comparison of two readings (`--compare-budget`). A requirement whose
   comparison is not decided by then is not certified: it becomes a
   question, without a call when none was found, and the report names
   every search that stopped at its time. The comparison in context, on
   which the verdicts rest, is handed what the comparison without context
   closed and does not ask that again (§10). At most eight engine tasks
   run at a time (`--jobs`): one task of a wide reading takes about 1 GB.
   The check is a sequence of named steps: for each reading its
   scenarios, its conflicts and its open choices, then each comparison of
   two readings and the replay of the calls it found (§10), the code on
   the scope, and the proofs under each reading. It runs in a process of
   its own, which the review watches. A
   step that raises an error, that runs longer than fifteen minutes
   (`--step-seconds`), or during which the check and the tools it started
   hold more memory than the check may (`--memory`, in GB; by default the
   least of 8 GB, half of the machine's memory and 85% of the limit of a
   control group around the review) is stopped and recorded with the
   reason, and the check goes on with the next step. A step stopped for
   its memory is first run once more, one engine task at a time. After an
   hour (`--check-seconds`) the step that runs is stopped and the steps
   that are left are not run.
5. **Report** (review.md): the requirements certified (the code meets them
   under both readings, which agree, and they are in no conflict), then the
   questions, each with calls and answers: one per conflict (the same clash
   at other values is one question), one per call the request leaves open,
   disagreements between the readings, and failures of the code. The
   report ends with what the readings take as given: the conditions on the
   caller, outside which a reading says nothing and no open choice is
   reported, and the outputs a reading leaves free on purpose.
   A phrase that the decomposer flagged is a question whatever the
   readers chose, on a requirement of any kind. Only guarantees and
   examples are certified: a definition, an assumption or a don't-care is
   asked about through its flagged phrases, and where the code breaks a
   rule that a reader stated for it. A requirement marked non-functional
   is listed under "Outside this review", so that nobody takes the review
   to cover it (§10).
   A requirement that a reader wrote no rule for is not certified: under
   that reading nothing was checked against it, so it is a question, with
   the reason the reader recorded. A call on which two readings differ is
   shown only after it was run again, from its line as printed, on the
   compiled monitors of both. A call that does not pass is left out: the
   report lists it under "Calls not shown" with the reason, the direction
   it was found for stays undecided, and its requirement is asked about
   without it, unless a certificate stands that does not rest on that
   direction (a comparison with the variant, §10). A question behind which
   no comparison ended is of the kind `undecided`: it shows no call, and
   it says that nothing was shown either way (§10). When a step of the
   check did not end,
   the report begins by naming it with the reason, and no requirement
   that rests on it is certified: none at all after a failed search for
   conflicts or open choices, a failed comparison with the third reader
   in context or a failed run of the code; no example of that reading
   after a failed scenario search. After a failed comparison of the two
   readings in context, the only requirements that rest on it are those
   that both readings state and that the comparison without context did
   not close in both directions, and the report lists them under the
   step; one closed in both directions keeps its agreement (§10). Where
   the comparison without context failed too, and for an object or a
   function with effects, every requirement rests on it. A failed proof changes no verdict, and neither does a failed
   comparison of the two readings outside context. After a failed
   comparison of a reading with the variant outside context, the
   requirements on which the variant differs from that reading wait for
   the shared answers. What the checking process printed about a failed step is
   kept in check_errors.txt. When the check gave no verdicts at all (the
   bundle does not load, or the checking process ended between two
   steps), the report says why, certifies nothing, and asks the phrases
   the decomposer flagged, which need no check.

The agents run headless through the Claude Code CLI (`claude -p`), each in
its own workspace, and every prompt and reply is recorded under
review/agents.

**Before any code.** With `--signature stub.py` in place of `--code`, where
the file holds the def line of the function asked for, the review ends with
the request alone: its conflicts, its open choices, the questions on which
the readings differ and the phrases the decomposer flagged. This is the
review for a request that has not been answered yet.

**What an agent can touch.** A reading must rest on the request alone, and
an agent is a model with a shell, so each one is held by three layers
(`agent_command` and `sandbox` in [fcp/review.py](../fcp/review.py),
`agent_refusal` and `limited` in [fcp/cli.py](../fcp/cli.py)):

1. *Permissions.* An agent has four tools (Read, Write, Edit, Bash), no web
   and no MCP server. Claude Code lets the file tools work inside the
   working directory only. It starts a shell command only when the command
   is the fcp launcher or one it knows to read or to edit files (`cat`,
   `grep`, `ls`, `cp`), on paths inside the working directory; an
   interpreter (`python3`, `awk`), a script, or a command it cannot take
   apart is refused.
2. *The launcher.* Started by an agent, `fcp` lints, explains and anchors
   the files of that agent's workspace and nothing else: no other reader's
   files, no other bundle, no check and no new review. Each of these
   commands has 1 GB of memory and 120 s of processor time
   (`FCP_AGENT_MEM_GB`, `FCP_AGENT_CPU_S`); past either it ends with one
   line that says so and exit code 3. A reading that grows without end
   then costs its agent one command, where it used to cost every agent
   of the run its memory (§10). Linting any bundle of these studies, all
   its readings together, takes at most 2.5 s and 255 MB. The limits hold
   whatever the command is in; the line is written by the stopped command
   itself, and with no memory left at all it is not always written: with
   the limit set below what the interpreter already holds, 823 of 830
   runs of `fcp lint` ended with the line, and seven spun inside CPython
   until the kernel ended them at the processor limit.
3. *A sandbox.* Where bubblewrap starts, the agent's process runs in a file
   system put together from a list: the system directories and the programs
   the agent runs, read-only; a /tmp of its own; its workspace, read-write;
   and of the user's files only what Claude Code needs to log in. In it
   there is no home directory, no checkout of this repository, no other
   agent's workspace and no other process to list. The user's plugins,
   skills and past sessions are not there, and the agent's session records
   go to review/sessions.

`FCP_AGENT_SANDBOX=1` asks for a sandbox or no run at all, `0` switches it
off, and unset takes one where one starts; every agent's record says
whether it ran in one. Two things stay within reach of an agent's process:
the network, since the agent is a model behind an API, and the login of
Claude Code, which is renewed in a directory the sandbox has to leave
writable. What keeps the model from the login is the first layer. The
session records hold every tool call with its outcome, so what an agent did
can be read afterwards (`experiments/comm_demo.py audit` lists the calls
that name anything outside the workspace, and whether they ran).

**First run: a duration parser**
([experiments/review_duration](../experiments/review_duration)). The
request: `parse_duration("1h30m")` returns seconds, with parts of 1 to 99,
units h, m and s at most once and in that order, no spaces, ValueError for
anything else, and "a duration is never longer than one day". Sonnet wrote
the code from the request alone; nobody wrote anything for FCP. The four
agents took 12 minutes, the analyses and the code check 31 (the scope's
request points stopped at their two-minute budget, which the report says).

The report certifies 5 requirements (the result is an int, a repeated unit
raises, the empty string raises, and both examples) and puts 13 questions:

- one failure of the code, replayed: `parse_duration("002h")` raises
  ValueError, while the reading of "a whole number" with leading zeros
  wants 7200;
- twelve ambiguities the decomposer flagged, which stay questions whatever
  the readers chose, among them the request's own contradiction: parts up to
  99 allow "99h", yet "a duration is never longer than one day"; whether that
  sentence is a rule to raise or a promise about the callers; whether the
  units may skip ("1h5s"); whether 90 minutes is allowed after an hour.
  Three of the twelve are flagged on definitions, and the report did not
  ask them until the change of §10: whether "a whole number" may have
  leading zeros (the phrase the failure above turns on) or a sign, and
  whether the unit letters may be capitals.

The conflict search, under both readings, found none in 650 candidates each:
the readings resolve the 99-hour contradiction by raising above one day.
A first draft of the verdicts also certified the requirements the decomposer
had flagged, and asked "which is meant?" where only one reading constrained
a requirement; both are fixed, and `rereport` redraws the verdicts from the
saved results.

**Second run: the gift card, all agents**
([experiments/review_card](../experiments/review_card)). The prompt whose
study gave the false assurance of §8.2, with Opus's code. The decomposer
agent wrote 24 requirements and flagged 20 ambiguities (15 distinct phrases),
the bonus-and-cap one among them; both readers recorded the same reading
for 13 of them, and the variant reader took the
other reading of all 13 (14 minutes). The variant differs from the readers
on six requirements, which are held: the review was made before the rule
of step 3 for a review with code, and its record holds every requirement
that differs (§10). The report certifies 7 requirements
(the result types, a new card's balance, the zero bonus of a small load,
`balance()`, the example), none broken under the literal reading, and asks
24 questions (15 flagged phrases, the dependent requirements, a conflict,
two open choices, three disagreements between the readings, two failures
of the code): whether a load that would pass $500.00
with its bonus raises, whether the bonus is cut, whether `spend(0)` raises or
returns True (a conflict between rules 1 and 5 under both readings), and
whether "covers it" includes the whole balance. The false assurance of the
study does not recur, at the price of a long queue: the prompt is short,
but nearly every phrase in it has two readings.

**From a Claude Code session: `/fcp-review`**
([.claude/skills/fcp-review](../.claude/skills/fcp-review)). A review
belongs where the answer is written, so the repository carries a skill
for Claude Code. Typed in a session, `/fcp-review answer.py` starts a
review of that file, and `/fcp-review DIR` presents a review that is
finished. The skill is a text of instructions for the session, in five
steps:

1. *The request.* The file that is named, or the messages of the
   conversation that asked for the code, word for word and in order,
   without the session's replies and plans: a request that states what
   the code assumed hides what the review is there to find. Where the
   request comes from several messages, the session shows the text and
   asks first. With no code yet, it writes the `def` line asked for and
   the review runs on the request alone (`--signature`).
2. *The start.* `review.sh`, a wrapper of `fcp review`, runs as a
   background command with a limit of three hours and writes to
   `.fcp-review/<date>-<time>/`. The wrapper puts a `.gitignore` into
   `.fcp-review/`, so reviews stay out of commits and no tracked file
   changes. The session may go on with other work and leaves the code
   under review as it is.
3. *No review.* When the command ends without one, the session reports
   the end of the log and does not start the same command again.
4. *The report.* The steps that did not end, the counts, every question
   in the order of the report with its calls as printed, and in a
   sentence each which certified requirements a third reader reads
   another way without their waiting for the shared answers, what the
   report takes as given, leaves outside, did not show, and names as its
   limits.
5. *The answers.* They go under `Decisions` at the end of the request;
   the code changes where an answer goes against it; a new review is
   offered with its cost and starts when the person says so.

Three rules keep the session from standing in for the author. It does
not answer the questions or order them by what it thinks was meant: it
wrote the code, so its view of the request is the thing under review. It
does not change the code before the answers. And it says "certified" as
the report means it. The skill starts only when a person types it
(`disable-model-invocation`), because a review costs four or five agent
runs.

A session in this checkout has the skill. For other projects, link it:

```bash
ln -s /path/to/openfcp/.claude/skills/fcp-review ~/.claude/skills/fcp-review
```

or link it into one project's `.claude/skills/`. The wrapper starts the
launcher of the checkout it is linked from (`FCP_BIN` names another).

Four headless sessions tested it (Claude Code 2.1.299, Opus, each in the
sandbox of an agent):

| session | what it did | time | cost |
|---|---|---|---|
| A: `/fcp-review review` on the finished review of the duration parser | reported the counts, the ten questions with their calls, the limits | 40 s | $0.19 |
| B: `/fcp-review parse_duration.py request.md`, the launcher replaced by a stand-in that writes that review after 45 s | wrote the request word for word, started the wrapper in the background with the right arguments, waited for it, reported as in A, and said that the launcher was a stand-in | 133 s | $0.54 |
| C: as A, the skill reached through a symbolic link in the project's `.claude/skills`, the review redrawn by today's engine | reported 13 questions and what lies outside the review, and noted that the failing call and a question about "a whole number" turn on one phrase | 37 s | $0.20 |
| D: as B with the engine: the launcher hands its command to a relay outside the sandbox, which accepts a review of the test's two files and nothing else | wrote the request word for word, started the wrapper in the background, waited 52 minutes for it, reported 2 certified requirements and 23 questions in the report's order, said of the 8 `undecided` ones that they report a search and not a fact about the request, and named the phrases on which several questions turn | 54 min | $0.46, and $5.52 for the review's five agents |

Session B first tried what an earlier text of the skill asked for, a line
in `.git/info/exclude`. Claude Code refuses a session that edits under
`.git` without approval, so the wrapper now writes the `.gitignore`
itself. What is not tested: a session with a person in it, and the link
under `~/.claude/skills` (C linked inside a project).

Session D reviewed the request and the code of the first run above, with
new agents. Its review took 52 minutes, 18 in the five agents and 34 in
the check, and came back with 2 requirements certified (the two
examples) and 23 questions: twelve on flagged phrases, one on the
answers both readers shared, two on a failure of the code on
`parse_duration("024h")` (leading zeros, as in the first run), and
eight on requirements left `undecided`. For six of the eight the engine
had shown the two readings equal and did not use it; §10 has the fault
and the change. Run again by the changed engine on the same readings,
with no agent, the check takes 26 minutes, certifies 4 requirements
(the examples, the empty string, a repeated unit) and asks 15
questions, none of them `undecided`.

## 10. Engine changes

- **The software adapter** ([fcp/software.py](../fcp/software.py)): the
  `function` section of the IR, the scope, sweeps, the sandboxed runner, the
  monitor check over recorded traces, replay, code mutants, code splits, and
  running a test suite against any implementation.
- **Boundary conflicts**, a spec-level analysis for any design whose
  conflicts need particular values. Sound for the conflicts it finds.
- **Simplest open choice and simplest separating calls**, which turn
  determinacy and comparison witnesses into small examples.
- **Exact comparison for stateless designs.** A bounded horizon makes the
  comparison of readings decidable on k calls. The new integer encoding of
  FCP-PL decides it where the bit-level engines time out. It is a second
  implementation of FCP-PL's semantics, so every witness is confirmed on the
  compiled monitors and every agreement is spot-checked on the bit-level
  model.
- **Linter:** `covered_by` must name existing items (found by agent_a). It
  turned up one slip in the FIFO's literal set, now fixed; no study number
  depends on it.
- **Minimal conflicting sets, deterministically.** z3's unsat core depends on
  the solver's history, so the reported conflict, and with it which
  requirements count as "in a conflict", could change between runs. A
  conflict's minimal set is now found by deletion over the selectors in name
  order, and every minimal set of the stimulus is listed (MARCO); a
  requirement is in a conflict if it belongs to any of them. On the checkout
  prompt this takes the member discount out of the conflict: it was in a
  non-minimal core. FCP now certifies 9 of 27 pairs there instead of 6; no
  other number changed.
- **Replay at speed** ([fcp/vl.py](../fcp/vl.py)): the monitors compiled
  once per reading by Verilator, about 400 times faster than Icarus on the
  string monitors and identical on every check compared (§3.3).
- **The effects scope** took the first four, the last four and four random
  values of an argument with more than twelve, ignoring the values the
  design configures: the payment study never tried amounts of 1,000,000 and
  1,000,001, the boundary of its rule 1. It now takes the configured values
  (else every constant with its neighbours) and the ends of the range. Every
  verdict of the payment study is unchanged under the new scope (13
  implementations, 3 readings).
- **Proofs beyond the scope** ([fcp/prove.py](../fcp/prove.py), §2.6): a
  symbolic executor from a Python subset to z3 terms, checked against the
  code on every call of the scope, joined to the integer encoding of a
  reading, which is checked against the compiled monitors on every cycle of
  the same trace. For code with effects, calls on the interface are events
  and answers free variables, and the encoding gains ghost state and the
  `next`, `after_reset`, `once`, `hist` and `since` forms. For objects, the
  encoding also has a window form (a free start state, then as many
  consecutive calls as the reading looks back), proved equal to the
  unrolled form where both apply, and an induction over the calls with an
  invariant found by Houdini.
- **Strings and lists in the translation, and equivalence sweeping**
  ([fcp/seqs.py](../fcp/seqs.py), [fcp/sweep.py](../fcp/sweep.py), §3.5):
  sequences as guarded slots; path conditions kept as chains of facts; and,
  before a goal goes to z3, the agreements between the code's subterms and
  the reading's found on samples and proved from the leaves up. The goals
  of a string function are conjunctions of the path's facts and a claim
  about the result; the facts are assumptions under which the claim is
  swept again, and a goal with no fact of the path is split by the call's
  outcome.
- **Dictionaries, lists and helper objects in the fields**
  ([fcp/keyed.py](../fcp/keyed.py), [fcp/keyedproof.py](../fcp/keyedproof.py),
  §4.5): a dictionary as its writes, names with a home so that a change
  through a name reaches the dictionary it came from, a window of calls from
  an abstract state checked against the unrolled code, rigid variables as
  free constants, and an invariant grammar over list elements and lengths
  with the distances the code and the reading use. The candidates are run
  on sampled states of the scope before any is put to z3.
- **Records, computed boundaries and shrinking** (§7): groups of sequences
  with one length in every engine, the record shapes in the runner, scope
  points with conforming outputs under their path conditions, and conflicts
  on sequences shrunk to the simplest stimulus.
- **Answers where no service answers** ([fcp/effects.py](../fcp/effects.py),
  §6.4). The conflict search over scripts left the `answer` input free at
  the cycles that are not an answering call. A reading that bounds the
  answer at every cycle could be escaped there, and the search then found
  no conflict under it. The answer is now 0 at those cycles, as the trace
  records it; a task whose readings assume a bound states the same as a
  frame rule, so that comparisons range over such runs only. An argument
  that no rule reads (an order number) can be marked `only` in the scope
  and takes its configured values alone, in the scope and in the search.
- **Conflicts between the state now and what was answered before**
  ([fcp/software.py](../fcp/software.py), §8.3). The candidate sequences of
  the object conflict search now include those after which two properties
  of a reading disagree about one call (both triggers hold, and the outputs
  meet one condition and fail the other). The loyalty conflict under the
  agents' readings is of that kind: a tier computed from the points against
  a tier that never goes down.
- **Packages and services in the test runner.** A suite runs against a
  package as well as a file, with the stub clients of the services the code
  imports beside it. `experiments/own_tests_mutants.py` runs each model's
  suite on the mutants of its own code; `experiments/compare_env.py`
  compares my reading with each agent's under the agent's assumptions.
- **The translator** ([fcp/prove.py](../fcp/prove.py)) reads constants
  assigned several at once (`LO, HI = 1, 100`) and a helper that is passed
  a service call, an error class and `*args`; two paths of a helper that
  made the same calls on the interface are joined when the calls agree term
  for term. All three models' order code needed the first, Opus's the rest.
- **Rigid cases are counted before they are listed**
  ([fcp/monitor.py](../fcp/monitor.py)). A requirement over rigid variables
  is expanded binding by binding when it has at most 64 bindings, and is
  reported as too large otherwise. The bindings were listed first and
  counted afterwards. One agent's reading of HumanEval/49 (`modp`: 2^n
  modulo p, in a language without a power operator) has thirty-two rigid
  variables of sixteen and seventeen bits, about 10^159 bindings; `fcp
  lint` on it took 11 GB within seconds, and the memory cap of the run
  ended the run, 24 reviews into 80. The count is now a product, and the
  reading lints in 0.3 s.
- **A definition is measured once** ([fcp/lang.py](../fcp/lang.py)). How
  many cycles an expression looks back was computed along every path
  through the definitions it names. The other agent's reading of `modp`
  is a chain of 272 definitions, each naming the one before three times:
  3^272 paths, in little memory and without end. The depth is now
  computed once per definition, a chain of that length compiles (0.4 s),
  and a definition that names itself, directly or through others, is
  reported as that instead of as a Python error
  ([tests/test_limits.py](../tests/test_limits.py)).
- **A comparison of two readings has a time**
  ([fcp/software.py](../fcp/software.py), `COMPARE_BUDGET`). Each
  direction of each requirement had limits of its own (a minute of z3, two
  hundred calls with the input fixed, five minutes of bit-level search),
  and nothing bounded their sum. The review of one request over lists
  (HumanEval/163 with its description made incomplete) spent 526 of its
  584 s comparing the two readers with the variant reading. `fcp review`
  now gives one comparison five minutes (`--compare-budget`): a direction
  not reached by then stays undecided, its requirement becomes a question,
  and the report lists the comparison among the searches that stopped at
  their time. The studies run without this budget, as before. The
  comparison of objects and of functions with effects, which runs on the
  bounded model checker, has no budget yet.
- **Open choices stay inside the contract**
  ([fcp/software.py](../fcp/software.py), `_Spec.inside`;
  [fcp/review.py](../fcp/review.py), `given`). An open choice is a call
  on which a reading allows two answers, and the search knew nothing of
  the calls a reading excludes. The first two reviews of requests I did
  not write asked what `generate_integers(0, 0)` returns, with two lists
  of 64 numbers as the answers, where the request says "two positive
  integers", and what `correct_bracketing(" ")` returns, where the
  request says the string is made of brackets. A call is now outside a
  reading's contract when it breaks an assumption, or meets a don't-care
  that cites a requirement of kind assumption (a condition on the
  caller, restated call by call); no open choice is reported on such a
  call, nor after one in an object's history. Any other don't-care is a
  freedom inside the contract, and it is still asked. For a chip, a
  declared don't-care closes the question, because the designer wrote
  it. In a review an agent wrote it, and a request with a part left out
  is read exactly so: both readers of HumanEval/163 with its description
  cut short declare the result free where two even digits lie in the
  range, which is the order the benchmark removed (`[6, 8]` or `[8, 6]`
  on `generate_integers(25, 6)`). The question names the don't-care, a
  requirement so cited is not certified, and the report ends with what
  the readings take as given: every condition on the caller and every
  freedom, with the definitions they name. One call is one question,
  whatever number of outputs it leaves open, and a freedom that both
  readings declare is asked once. The two answers shown are small ones
  (the first pair under a ladder of bounds on length and size, `SMALL`),
  not the solver's first model: 0 or 1 for an element of `fib4` that the
  request does not define, where the first review showed 0 or
  2199023255552.
  The readings of the ten code tasks declare no don't-care, and among
  the seven studies that search for open choices three readings carry an
  assumption (one of the gift card, two of the loyalty account: the call
  names one of the object's methods). Recomputed with the rule on and
  off, the open choices of six of those studies are the recorded ones:
  the same outputs on the same calls, after the same number of calls
  checked. The seventh (the changed function, 72,384 calls) was not
  recomputed; its readings have neither.
- **A review bounds its engine tasks and searches the scenarios only**
  ([fcp/review.py](../fcp/review.py), `JOBS`;
  [fcp/analyses.py](../fcp/analyses.py), `consistency`). The first step
  of a review on a reading asks whether its formal examples can happen
  under its own rules. For that it ran the whole consistency analysis
  (every trigger situation, the scenarios and the progress check, of
  which a review reads the scenarios), up to 24 engine tasks at a time.
  One reader of HumanEval/46 with its recurrence made ambiguous ("+/-"
  between the terms) wrote eight triggers and three scenarios: twelve
  tasks of about 1 GB each, against the 8 GB that the check of one
  benchmark prompt is given, and the check was stopped after ten
  seconds. A review now searches the scenarios only and runs at most
  eight engine tasks at a time (`fcp review --jobs`; four in the
  benchmark run). A scenario search that the engine does not finish
  settles nothing: its requirement is not certified, and the report
  names the search under its limits. Where the rules do exclude a
  scenario and the search that tells an impossible example from a
  forbidden one did not end, the question is still asked and says so.
  On five finished reviews the questions and the certified requirements
  are the same before and after
  ([tests/test_limits.py](../tests/test_limits.py)).
- **An open choice is confirmed over every rigid value**
  ([fcp/software.py](../fcp/software.py), `left_out`, `_conforms`,
  `choices`). A rule stated for every value of a rigid variable is
  expanded value by value when the variable has at most 64 values.
  Above that, the solver behind the conflict and open-choice searches
  of a function leaves the rule out. For conflicts that is safe: a
  clash found with fewer rules still stands, and one that needs the
  rule is missed. For open choices it is not, since fewer rules allow
  more answers. The review of HumanEval/163 as originally worded asked
  whether `generate_integers(1, 1)` returns `[0]` or `[1]`. One reader
  had written "d is in the result exactly when d is an even digit
  between a and b" as two rules over every d from 0 to 255; both were
  left out, and each of the two answers breaks the first. Both answers
  of an open choice are now replayed on the compiled monitor over every
  rigid value before the choice is kept, as the search over objects
  already did. A call whose answers fail is counted, an output is given
  up after eight such calls, and the report lists the rules that the
  two searches leave out under its limits: for such a reading an open
  choice can be missed, never invented. Of the 48 readings of the first
  24 benchmark prompts this one alone states a rule over a wide rigid
  range; of the ten code tasks only the rate limiter's readings do, and
  it is an object, whose answers were already replayed. No result above
  changes ([tests/test_code.py](../tests/test_code.py)).
- **A wide constant is written in pieces, and `min` and `max` keep the
  narrower range** ([fcp/lang.py](../fcp/lang.py), `vbits`, `vconst`,
  `as_num`). One reader of HumanEval/49 as originally worded ("return 2^n
  modulo p") wrote `1 << min(n, 28)`. The result of `min` was given a
  range that covers both arguments, so the shift was by a 16-bit amount
  and its result was 65,537 bits wide. A constant of that width was
  written as one token, which yosys cannot read (the buffer of its
  scanner is fixed), and the check of the request failed after seven
  seconds. The minimum of two values is at most the smaller of their
  upper bounds, and the maximum at least the larger of their lower
  bounds: `min` and `max` now have that range, so the shift above needs
  30 bits. A literal wider than 4,096 bits is written as a concatenation
  of pieces, and a run of equal bits as a replication. Three tests cover
  the ranges, the pieces, and the values a monitor computes with both
  ([tests/test_limits.py](../tests/test_limits.py)).
- **A definition is walked once and computed once per call**
  ([fcp/software.py](../fcp/software.py), `_walk`, `_walk_ctx`,
  `_IntSpec`). The searches behind a function's conflicts, open choices
  and comparisons work on integers, and two of their steps visited a
  definition again at every place it is used: the walks that collect the
  boundaries and conditions of a formula, and the encoding of a formula
  for the solver. One reader of HumanEval/26 as originally worded
  ("remove all elements that occur more than once") wrote eight
  definitions, one per position of the list, each naming the one before
  three times: 3^8 uses of the first. Collecting candidate calls for
  that reading took 1,895 of the 1,985 s of the check, after which the
  conflict search checked none of its 305 candidates and the review said
  so under its limits; the check of one rewrite of the same problem was
  stopped at its 45 minutes inside the comparison of its two readings.
  A walk now enters a definition once. The walk that must keep the
  conditions it passed can meet a definition under different conditions,
  so it enters each definition at least once and stops entering
  definitions again after 100,000 nodes; a search cut this way is named
  under the review's limits. The encoding keeps the term of a definition
  per call, position and bound variables. With the fix the same
  collection takes 96 s and every candidate is checked, and the
  comparison that was stopped ends in 198 s.
  The fix is meant to change time only, and three measurements say how
  far that holds. On 289 of the 290 readings of the pilot and of the
  corpus the new walks visit the same nodes in the same order as the old
  ones (the other is a reading whose old walk would have 1.2e16 nodes).
  The terms the encoding builds are the same, term by term, on 414
  encodings of 209 readings. On one reading of HumanEval/26 the two
  point searches put the same queries to the solver in the same order
  and get the same answers. The calls shown can still differ: of two
  models of one query the solver returns the one its internal numbering
  of terms leads to, and the fix changes which terms exist. Four tests
  ([tests/test_limits.py](../tests/test_limits.py)).
- **A rule over more rigid values than a replay lists is not listed**
  ([fcp/software.py](../fcp/software.py), `_IntSpec._item`, `_confirm`).
  A rule over a rigid variable holds for every value of the variable. The
  integer encoding writes one instance of the rule per value, and a replay
  on the monitor runs once per value, up to 4,096 of them. The encoding
  had no such bound. The readers of HumanEval/144 ("returns True if x * n
  evaluates to a whole number", the fractions given as strings) wrote "a
  whole number" as a rule for every q: if the numerator is q times the
  denominator, the result is True, with q over up to 10^28 values. Listing
  them raised an error that no caller handles (the check of one rewrite
  ended in a `MemoryError` after 130 s). The instances are now counted
  before they are listed, and a rule over more than 4,096 is refused as
  every other formula the encoding does not take: the search for computed
  boundaries goes on without it, and a comparison leaves the requirement
  to the scope and the bit level. A witness on a reading whose rigid
  values are too many to replay (two rigid variables of 101 values, each
  in a rule of its own, are 10,201 replays) is not confirmed, where the
  refusal of the replay ended the comparison before. No rule of the
  corpus has more than 1,024 instances, so no result above changes. Two
  tests ([tests/test_limits.py](../tests/test_limits.py)).
- **The configured values of a string or list are not integers of the
  scope** ([fcp/software.py](../fcp/software.py), `scope`). A design file
  may give an argument values to try: integers, and for a string or list
  whole strings and lists, which the calls of such a function include.
  When a function of a string or list also takes a number, the scope of
  its numbers is computed, and that step put the configured values of
  every argument into one set of integers. The adapter of HumanEval/72
  (`will_it_fly(q, w)`: a list and a number) listed the three example
  lists as values of `q`, and each of the four checks of that problem
  ended within two seconds in a `TypeError`. No bundle of the corpus has a
  string or list beside a number and values for it, so the step had not
  met one. The values of a string or list are now left to the calls that
  use them. One test ([tests/test_seq.py](../tests/test_seq.py)).
- **A clash that both readings find is one place**
  ([fcp/review.py](../fcp/review.py), `verdicts`). Conflicts with the same
  requirements in every minimal set are one question, which closes with the
  further requirements that take part and the number of places. The number
  was the count of findings, so the same clash found by both readings on
  the same call was "2 places", and the list of further requirements was
  printed when it was empty: "(also with , at 2 places)", on twelve
  questions of five reviews of the pilot (§13). The clause now names
  further requirements only when there are some, and counts distinct
  calls. One test ([tests/test_code.py](../tests/test_code.py)).
- **A rule the bit-level comparison cannot assume is asked, and an answer
  that needs it is replayed** ([fcp/software.py](../fcp/software.py),
  `_Spec`, `split_status`, `_held`, `compare`;
  [fcp/review.py](../fcp/review.py), `verdicts`). A rule over a rigid
  variable holds for every value of the variable. A monitor has it in two
  forms: one reads the value from a register, and one is expanded over
  every value, up to 64 of them. A comparison of two readings at the bit
  level assumes and asks the expanded form, and gave a rule over more
  than 64 values no place at all. (The integer encoding, which a
  comparison tries first, lists a rule over every value, up to 4,096 of
  them, and is not affected; the bit level decides what it cannot.) That
  is wrong in both directions. Where
  the rule belongs to the reading that should reject a call, nothing was
  asked, and the answer was "no difference": two readings counted as
  agreeing on a requirement of which nothing had been compared. Where it
  belongs to the reading that should accept the call, the solver chose
  outputs the rule forbids, and the comparison showed a call on which the
  two readings in fact agree. One reader of HumanEval/26 1a ("remove all
  elements that occur K time(s)") stated its two rules for every value of
  an element, 0 to 255, and the review asked two `readings` questions
  under calls of that kind: `candidate([0, 0]) -> [0]` and
  `candidate([0]) -> []`. I found it by reading the review by hand; no
  step of the engine had replayed either call.
  Such a rule is now asked in its register form: the reading rejects a
  call when the rule fails for some value in the variable's range. An
  answer found while such a rule had to hold is replayed on the monitors
  over every value, for every rule of the requirement in the readings
  that have one, and an answer the replay refutes is dropped and the
  direction stays undecided; a scan of the scope stops after eight of
  them. The relation is then UNKNOWN, the report names the rules under
  its limits, and the question says that the two readings were not shown
  to agree and that no separating call was found, where it said that
  they disagree. This is sound and weak: one answer is tried per query,
  so a requirement beside such a rule usually stays undecided (§13).
  The readings of the studies above that are compared this way have no
  rule over more than 64 values (the stored readings with one belong to
  hardware bundles, the agent scaffold and the stateful rate limiter,
  which are compared by other paths), so no result above changes. Two tests
  ([tests/test_limits.py](../tests/test_limits.py)).
- **A call ends in a way that has a name**
  ([fcp/harness.py](../fcp/harness.py), `canonical_outcome`;
  [fcp/smt.py](../fcp/smt.py), `SmtModel.unroll`, `forcing`;
  [fcp/software.py](../fcp/software.py), `_IntSpec`, `Fn.outcome_name`).
  The outcome signal of a function says how a call ended: 0 it returned,
  one code per exception that the request names, then "another exception
  or no answer" and "returned something else". A signal wide enough for
  these codes can have codes left over: with no named exception the codes
  are 0 to 2, the signal has two bits, and 3 names no ending. Every
  search of the solver left the signal free over its whole width. Rules
  compare the signal with numbers, so two readings that agree on every
  ending can differ on a code that names none. In HumanEval/46 1a one
  reader wrote `outcome == 0 || outcome == 2` where the other wrote
  `outcome != 1`, and the review asked which of the two is meant under
  the call `fib4(8) -> returned something else`: a line that printed
  code 3 in the words of code 2. The same freedom hides a conflict: rules
  that leave a call no ending are all met on the code left over, and the
  search for conflicts reports none. The replay of the calls that the
  pilot's reviews show ([experiments/comm_replay.py](../experiments/comm_replay.py),
  §13) found it: it reads a printed line back as the code that its words
  name, and on code 2 the two readings agree.
  The harness now states the codes. Where the outcome signal, or the
  signal that carries the ending of the code before a change, has a code
  left over, a wire `fcp_env_ok` is true while every free copy of the
  signal is at most its last code. A formal run assumes the wire. The
  solver model of a harness is read without its assumptions, so every
  unrolling of the model asserts the wire at every step, and the forcing
  query takes its stimulus from a copy of the model that meets it. The
  integer encoding bounds the outcome by its last code, and a code above
  it prints as "ended with code 3, which names no ending", never in the
  words of another. A design whose codes fill the signal gets no wire and
  its harness text is unchanged. The fourteen stored designs of the
  studies above are all of that kind, so no result above changes; §13
  says which reviews of the pilot it could reach. Two tests
  ([tests/test_limits.py](../tests/test_limits.py)).
- **A review is written whatever a step of its check does**
  ([fcp/review.py](../fcp/review.py), `Steps`, `check`, `supervised`,
  `worker`, `verdicts`, `unchecked`, `checked`). In the pilot of §13 one
  search that failed ended the whole check, and 8 of the 80 requests got
  no review: a translation that did not end in 300 s on three, searches
  that passed 8 GB on five (§13.5, which also has what the eight get
  from the engine described here). The memory and the time of a check
  were held from outside, by the script of the pilot, which could only
  end the check as a whole.
  `check` is now a sequence of named steps: for each reading the search
  for its scenarios, for conflicts and for open choices; each comparison
  of two readings; the run of the code on the scope; the proofs beyond
  the scope. A step that raises is recorded with the reason and returns
  the empty result of its kind, and the next step runs. Each step says
  what rests on it: every verdict (a search for conflicts or open
  choices, a comparison in context, the run of the code), the examples of
  one reading (its scenario search), or no verdict (the comparison
  outside context and the proofs, which add to a report and decide
  nothing in it). The verdicts certify nothing that rests on a failed
  step, and they draw no question from it: a comparison that did not run
  shows no disagreement, and no agreement either. The report begins with
  the failed steps and their reasons. (A failed comparison of the two
  readings in context now names the requirements that rest on it: the
  entry on a failed comparison in context, below.)
  `supervised` runs the check in a process that leads a session of its
  own, and the check writes the result of each step to a file as the step
  ends. Four times a second the review looks at the time of the running
  step, the time of the whole check, and the resident memory of every
  process of that session, which includes the solver and yosys processes
  that sby starts in process groups of their own. Past a limit it kills
  the session, records the running step as failed with the reason, and
  starts a new process, which reads the file and goes on with the next
  step. A step stopped for its memory is first run once more with one
  engine task at a time: most of the memory of a step is that of tasks
  that run side by side. A check that ends outside its steps gives no
  verdicts, and the review says so (§9).
  The watched check gives the review that the check in one process
  gives. On the gift card of §9 with Opus's code and on three requests of
  the pilot (the incomplete rewrites of HumanEval/46, /124 and /138) the
  same bundle was checked both ways, each from a copy without a cache.
  The two results are the same down to every call shown (7 requirements
  certified and 24 questions on the gift card, in 97 s either way) and
  differ only in the run times that the conflict searches record.
  The checking process also ends when the process that watches it is
  gone. `timeout` ended one of these runs, and its check ran on beside
  the next one: a killed process stops nothing, and the session that lets
  the review stop every tool of a check also keeps the check out of reach
  of whoever stops the review. The checking process now looks once a
  second for the process that started it, and when that is gone it kills
  every process of its session and then itself. 28 tests
  ([tests/test_partial.py](../tests/test_partial.py)).
- **A translation that failed is not started again**
  ([fcp/smt.py](../fcp/smt.py), `TranslationFailed`;
  [fcp/software.py](../fcp/software.py), `compare`, `_bit_job`). On
  HumanEval/49 yosys ran out of its 300 s on the monitors of a reading,
  and every search over that reading then waited 300 s for the same
  translation. A model that did not translate is remembered for the life
  of the process and refused at once. A comparison whose bit-level model
  does not translate keeps what the integer encoding decided, leaves the
  rest UNKNOWN, names the reason once under the limits of the review, and
  starts no bit-level process for it.
- **A requirement that a reader left without a rule is a question**
  ([fcp/review.py](../fcp/review.py), `verdicts`, `_unformalized`). A
  reader may leave a requirement without a formal item and record why
  (`unformalized`). The comparison of two readings reports such a
  requirement as stated by one reading only, or not at all, and the
  verdicts took both for agreement: before any code the requirement could
  be listed as settled, and with code it was neither certified nor asked
  about. Now a requirement is certified or settled only if every reading
  holds an item for it, and otherwise the review asks, quoting the
  reason. In the 72 stored reviews of the pilot no requirement was
  settled this way: the 16 requirements that a reading leaves without a
  rule, in 10 reviews, are all phrases the decomposer flagged, which were
  questions already, and each of the 114 settled requirements has an item
  in both readings. The stored reviews are not redrawn; redrawn, those 10
  would carry 16 more questions and the same settled requirements.
- **A call on which two readings differ is run again before it is shown**
  ([fcp/software.py](../fcp/software.py), `read_line`, `separates`,
  `replayed`, `unshown`; [fcp/rv.py](../fcp/rv.py), `NotReplayed`;
  [fcp/review.py](../fcp/review.py), `check`, `report`). A question about
  two readings shows a call on which they differ, and a person who reads
  the review takes the call as a fact. Twice in the pilot of §13 it was
  none: the review showed a call on which the two readings agree
  (HumanEval/26 1a and 46 1a, above), and no step of the engine had run
  the call again. The second was found by a script that replays the
  calls of stored reviews (§13.4). A review now does the same before it
  shows a call.
  After the comparison of the two readings in context, and after each
  comparison in context of a reading with the variant, a step named
  `the replay of the calls of` that comparison takes every call the
  comparison found.
  It reads the call back from its line as printed, `name(args) ->
  result`, and checks each value against the signal that carries it. It
  prints the call again and requires the same line. Then it runs the
  call on the compiled monitors of the two readings, without a solver.
  The call passes when the reading said to accept it breaks none of its
  rules, and the reading said to reject it breaks a rule of the
  requirement in question and no other rule that it had to keep: no frame
  rule, and no rule of another requirement. That is the test a comparison
  in context puts to a witness, applied to what the line says; a rule
  counts for as long as the assumptions of its reading hold.
  A call that does not pass is taken out of the result of the comparison.
  The relation of its requirement becomes UNKNOWN, and the direction the
  call was found for is undecided. In the comparison of the two readings
  the requirement is then neither certified nor settled, and it is asked
  about without the call. In a comparison with the variant the same holds
  before any code; with code the requirement waits for the shared answers
  unless the direction that holds it is closed all the same (the last
  entry of this section).
  The report lists the requirement, the comparison and the reason under
  "Calls not shown", and review.json keeps the call under `dropped`.
  The reasons are these. The line is not read back: it names a value the
  signal cannot carry, or it is no call of the function. The line reads
  back as another call. The call does not separate the two readings. A
  reading has more than 65,536 combinations of free values, the most
  that a replay runs. The ten minutes that the calls of one comparison
  share are used up. A line that ends in words (`raised ValueError`) is
  read as the ending that its words name, with every output at its
  default: the line does not say what the outputs carried, and where
  they decide, the call does not pass and the reason says so.
  The replay is a step of its own, and no verdict rests on it, so that a
  long replay does not take the comparison with it. On the longest call of
  the pilot, a string of 32 characters (HumanEval/80), the replay by the
  script takes 136 seconds and 6.6 GB of memory (the peak of its control
  group). It took 552 seconds before the script used the functions of
  the engine, which simulate a reading once for a call.
  A replay that fails or is stopped takes every call of its comparison
  out, with the reason "the replay did not end", and the review is
  partial (the bullet on steps, above).
  The step covers what a line can carry: a function of plain values
  (integers, booleans, strings, lists of integers), whose line names the
  whole call and every output. The calls of an object, of records, of a
  change and of code with effects are not read back, because a line does
  not carry the state of the object, the nested values, or the answer of
  the code before the change. For these a comparison does what it did
  before: a call that the integer encoding finds is simulated on the
  monitors before it is kept, and the bit-level search runs on the model
  compiled from the monitors. The calls under a conflict or an open
  choice are not read back either. And where a line reads back to the
  very call that the comparison simulated in the same process, the
  simulation is not run a second time: its result is judged again, by
  the reading of the line.
  On three requests of the pilot (the incomplete rewrites of
  HumanEval/46, 124 and 138, each checked from a copy without a cache)
  the check with the step writes the review that the check without it
  wrote: the same requirements settled, the same questions, the same
  calls. The reviews of 46 and 138 show such calls and have two replay
  steps each, in which every call passes; the review of 124 shows none
  and has no such step. The script of §13.4 now calls `read_line` and
  `separates`. Run again on the 59 stored reviews that show such a call,
  it returns what is stored for each of the 119 replays: the same reading
  accepts the call and the same reading rejects it, in context. That
  agreement is weaker than the step: a stored review does not say which
  comparison found a call, or in which direction, so the script confirms
  a call that separates any of the pairs in either direction, where the
  step asks for the pair and the direction of the comparison that found
  it. 39 tests ([tests/test_replay.py](../tests/test_replay.py)).
- **A phrase flagged on a requirement of any kind is asked about**
  ([fcp/review.py](../fcp/review.py), `verdicts`, `unchecked`, `report`).
  The decomposer gives every requirement a kind. A review certifies or
  settles guarantees and examples, and the verdicts looked at no other
  kind. Three things were lost. A phrase flagged on a definition, an
  assumption or a don't-care was in no list of the report, although the
  guarantees are read through it: on HumanEval/80, 1p, the decomposer
  wrote four meanings of "happy" on the definition, and the review did
  not ask which is meant (§13.4). A rule that a reader states for such a
  requirement, and that the code breaks, was no question. And a
  requirement marked non-functional was named nowhere, so the review
  could be taken to cover it.
  The queue now asks about every flagged phrase: those of the guarantees
  and examples first, then those of the other kinds, each in the order
  of the request, so the questions of an earlier review keep their
  numbers. The same phrase with the same meanings on two requirements is
  still one question. A rule stated for a requirement of another kind
  that the code breaks is a `code` question with its call. Such a
  requirement is still never certified or settled, and a reader that
  writes no rule for it is not asked why. The report lists the
  non-functional requirements under "Outside this review".
  One more gap closed with these. A call outside the scope that breaks a
  requirement under one reading (§2.6) was shown only where the code
  passed the requirement on the scope under every reading, and a reading
  with no rule for the requirement passes nothing. The call is now shown
  whenever the scope found no failure of its own.
  The stored reviews of the pilot are not redrawn. Redrawn, 66 of the 72
  would carry 251 more questions, all of the kind `ambiguity`: 142 on
  definitions, 82 on assumptions, 22 on non-functional requirements and
  5 on don't-cares. The 114 settled requirements stay the same, and 67
  reports would list requirements outside the review. On the 19
  originals the ambiguity questions go from 5.9 to 9.5 per request, so
  the full set of questions grows where it was already long (§13.3);
  the hard questions, which carry a result of the engine, do not change.
  The two reviews of §9 are redrawn: the duration parser has 13
  questions where it had 10, and both reports name what lies outside
  them. Three tests ([tests/test_partial.py](../tests/test_partial.py)).
- **A question behind which no comparison ended is of the kind
  `undecided`** ([fcp/review.py](../fcp/review.py), `verdicts`, `check`).
  A comparison of two readings that does not end in its time, or whose
  calls do not pass their replay, leaves the relation of a requirement
  UNKNOWN. The requirement is not certified, and it was asked about
  under the kind `readings`, like a difference that was found. The
  pilot's script had to tell the two apart afterwards (§13.1). The
  review now does: a question about two readings with the relation
  UNKNOWN and no call has the kind `undecided`, with the sentence it
  had ("were not shown to agree, and no call that separates them was
  found").
  The question about the answers both readers shared (§8.2) listed
  every requirement whose comparison with the third reader did not end
  in agreement, the undecided ones among them, and said of all of them
  that they "mean something else" when read the other way. It now says
  that of the requirements a call or a finished comparison shows to
  differ, and names the others as not shown either way. Where none was
  shown to differ, the question has the kind `undecided` and claims no
  difference. Where the first reader's comparison with the third did
  not end, the record of the requirement now carries what the second
  reader's found.
  A bounded comparison (of an object) can also end with no behavior
  that meets the other requirements under both readings at once. The
  question then read that the two readings disagree. It now says that
  there was nothing to compare them on, under the kind `undecided`. No
  stored review has that case.
  No verdict changes: a requirement asked about in either way was not
  certified, and is not now. Redrawn, the 72 reviews of the pilot carry
  17 `undecided` questions in 10 reviews, the same that §13.1 counts:
  12 that were `readings`, and 5 that were `depends` and are reworded.
  9 more `depends` questions keep their kind and their call and are
  reworded, because they list requirements that were not shown to
  differ beside ones that were. One test
  ([tests/test_partial.py](../tests/test_partial.py)); the question left
  when no call passes its replay is in
  [tests/test_replay.py](../tests/test_replay.py).
- **A reading over more rigid values than a replay runs is named by the
  lint, and compared** ([fcp/pipeline.py](../fcp/pipeline.py), `lint`;
  [fcp/analyses.py](../fcp/analyses.py), `_pinned_direction`). A replay
  runs a monitor once per combination of the values of its rigid
  variables, up to 4,096 combinations (the entry above on a rule over
  more rigid values has the same limit for one rule). Nothing said so to
  a reader: not the IR specification, not the prompt, not `fcp lint`.
  The two stored readers of the rate limiter met the limit because each
  tried `fcp code` on an implementation of its own, which the prompt
  does not ask for, and each then restated its windows with ghost
  state. A third reader of that task
  ([experiments/variant_demo.py](../experiments/variant_demo.py), told
  the first listed reading of every flagged phrase) did not try, and
  wrote three rigid variables: a customer and two times, 4.3 x 10^12
  combinations. Its lint was clean. Its comparison with each stored
  reader ended in an error. A comparison confirms the counterexample of
  a direction over a wide rigid range by a replay on the reading the
  counterexample comes from, and that replay was the one place where a
  refusal was not handled; the replays of
  [fcp/software.py](../fcp/software.py) all treat it as "not
  confirmed".
  `fcp lint` now warns when the rigid ranges of a set multiply to more
  than 4,096, and says what follows: code is not checked against the
  set, and a comparison with it cannot confirm a difference it finds.
  [IR_spec.md](IR_spec.md) states the limit. In a comparison, a
  counterexample that cannot be replayed leaves its direction open: the
  requirement comes out UNKNOWN, where the whole pair of readings came
  out as an error, so the reading is still compared on its other
  requirements and the scope is still searched for a call on the open
  ones. A proof is not affected: it takes the combinations symbolically,
  whatever their number. No set of the corpus has more than 4,096
  combinations, so no lint output and no result above changes. One test
  ([tests/test_obj.py](../tests/test_obj.py)).
- **What a comparison closed without context is not asked again in
  context** ([fcp/software.py](../fcp/software.py), `compare`;
  [fcp/review.py](../fcp/review.py), `check`). A review compares its
  two readings twice: each requirement by itself, and then in context,
  with the other requirements assumed under both readings. Its verdicts
  rest on the second comparison, and the two ran apart. The review that
  session D started (§9) certified 2 requirements and put 23 questions,
  8 of them `undecided`. On six of the eight the first comparison had
  shown the two readings equal. The second, whose every query carries
  the other requirements twice, ran out of its five minutes on them,
  and its result alone was used.
  A direction of a comparison asks for a call that one reading accepts
  and the other rejects on the requirement. In context the same call
  must also meet the other requirements under both readings: the
  question without context with rules added, over the same calls. So
  a call that separates two readings in context separates them without
  context, and a direction with no such call without context has none
  in context. `compare` now takes the result without context. Where it
  shows the readings equal, both directions are closed; where it shows
  one reading stronger, one is. A closed direction is not asked again,
  whatever time is left, and the record of the requirement lists it
  under `carried`. The review hands the result of its first comparison
  to the second.
  Two things are not carried (two more now are: the closed direction of
  a requirement left undecided without context, and what the comparisons
  with the third reader close, which ran in context only; the next
  entry). The bounded comparison of objects and of functions with
  effects ([fcp/analyses.py](../fcp/analyses.py)) can end, in context,
  with no behavior at all that meets the other requirements under both
  readings (the entry on the kind `undecided` above), which a carried
  "equal" would hide. And when the second comparison fails as a step,
  the review has no record from it and certifies nothing that rests on
  it (since narrowed to the requirements with a direction that the first
  left open: the entry on a failed comparison in context below).
  Checked on stored readings: on the four tasks of the corpus that are
  compared this way (the checkout, its change request, the invoice,
  card masking), my reading against agent A's and agent A's against
  agent B's come out the same on all 60 requirements with and without
  the first result handed over, none of them undecided, with 89
  directions carried. The 82 stored reviews agree: on 358 requirements
  their first comparison closed a direction and the second ended, and
  the second never found a call in a closed direction. In none of them
  was the second left undecided where the first had closed a
  direction, so no stored review changes, and session D's is the first
  where the two fell apart. Its check, run again by the changed engine
  on the same readings, certifies 4 requirements and asks 15 questions,
  none of them `undecided`. Six requirements are settled by what is
  carried. On the other two, one direction is carried and the open one
  is answered within the half second that the second comparison now
  takes, where it took 349 s and decided nothing; for one of the two,
  the first comparison came out undecided in the review and decided in
  this run, as a search against the clock may. The check takes 26
  minutes where it took 34.
  Two tests ([tests/test_limits.py](../tests/test_limits.py),
  [tests/test_partial.py](../tests/test_partial.py)).
- **A comparison records each direction, and the shared answers hold a
  requirement only where the other reading may reject a run**
  ([fcp/software.py](../fcp/software.py), `closed`, `compare`;
  [fcp/analyses.py](../fcp/analyses.py), `Session.compare`;
  [fcp/review.py](../fcp/review.py), `check`, `waiting`, `released`,
  `verdicts`). The relation of two readings on a requirement folds two
  searches into one word, and UNKNOWN hid what one of them had settled.
  The record of a requirement that both readings state now has a
  `status` for each direction: `none` (no call that the first reading
  accepts and the second rejects, or the reverse), `witness` (such a
  call), `unknown` (the search did not end, or its call did not pass the
  replay). `closed` gives the directions with no disagreement, from the
  status, or from the relation for a record written before this change.
  It gives none for a record with no context to compare in, and none
  for a requirement on which the monitors refuted a call that an
  encoding found (`refuted`): there the encoding and the monitors
  disagreed, and what the encoding closed is not handed on. Two things
  use it.
  The carry of the entry above reads it, so a requirement that the
  comparison without context left undecided with one direction closed
  hands that direction to the comparison in context.
  The "Shared answers" question uses it for the rule of `fcp review` in
  §8.4. A certificate says that the code meets the requirement as the
  two readers state it, and it stands under any reading that accepts
  every run they accept. A direction closed in context says less than
  that: it holds among the runs that meet every other rule of both
  readings, and code that meets the readers' rules may break two rules
  of the variant in one run. A direction closed without context holds
  on every run, whatever the run does on the other requirements. So
  each reader is now compared with the variant twice: without context
  (the step `the comparison of <reader> and variant`, on which nothing
  rests) and in context (`the comparison of <reader> and variant, in
  context`, which takes over what the first closed, as the entry above
  describes, and whose calls are replayed). In a review made before
  this change the first of these names is the comparison in context;
  the record of a failed step keeps what rested on it, so such a review
  reads as it did. Under `depends` the review records, for each reader
  that differs from the variant on it in context (`by`), how its
  comparison in context came out, the
  directions closed in context (`closed`) and without it
  (`closed_alone`), those handed over (`carried`), and what the
  searches covered where that is less than every run (`bound`).
  With code, a requirement goes without the shared answers only where,
  for each of those readers, the direction "a run that this reader
  accepts and the variant rejects" is closed both ways. A reader that
  agrees with the variant in context has no entry and is not asked: a
  certificate needs the code to pass under both readers, so what holds
  of every run that one of them accepts holds of the code, and the
  report speaks of the runs that both readers accept. It waits where
  a call was found in that direction, a search did not end, there was
  no context to compare in, or the comparison without context failed.
  Every requirement that differs waits where the code's run on the
  scope failed or a comparison in context with the variant failed, and
  in a record without `by` or without `closed_alone` (a review made
  before this change, the gift card's of §9 among them). As first
  written, this rule read the comparison in context alone; a review of
  the change found the gap above before any result was drawn with it,
  and the rule was corrected.
  The rule protects a certificate, so it lets go only a requirement
  that the review certifies (`released`): one that the code breaks, or
  that the readers disagree on, stays in the question about the shared
  answers, as before any code. The report names the requirements let go
  under "Shared answers", with the reason and with what the searches
  covered where that is bounded ("runs of 2 calls", "the first 6 cycles
  of a bounded check of 8"). Before any code there is no certificate to
  protect: the question is which requirements the other answer changes,
  and every requirement that differs is listed, as before. Where no
  comparison showed a difference on any requirement of the question
  (undecided searches, or no context to compare in), the question is of
  the kind `undecided` and says that nothing was shown either way. The
  call kept with a requirement is one that a reader accepts and the
  variant rejects, from either reader, where there is one.
  The bounded comparison (objects, effects) now says what it covered.
  Its record carries `engine`, `depth` and `lookahead`: a disagreement
  is reported `lookahead` cycles after it happens, so a direction with
  no call covers the first `depth - lookahead` cycles of a run, and a
  depth that leaves no call to examine is refused. The lookahead is 2
  for every
  reader of the six bounded tasks (card, limit, loyal, order, pay,
  save) except the second new reader of
  the order (6, so 4 of its 10 cycles are covered). In context a
  direction is closed only where a behaviour was shown to meet the
  other rules (the search for one found it, or a direction found a
  call); otherwise the record is UNKNOWN with nothing closed. In a
  direction over a range too large to expand, a counterexample without
  a trace cannot be replayed, is not confirmed and decides nothing;
  elsewhere the engine's verdict stands and the record carries no call.
  A comparison under the assumptions of one reading writes no record of
  the assumptions.
  Three limits stay. A requirement on which the variant agrees with
  both readers in context is never held, whatever the comparison
  without context found, as under the designed rule; a run of the code
  that breaks another rule of the variant, or another requirement under
  a reader (the review then certifies the first and asks about the
  second), is outside this step, and checking the code against the
  variant's rules directly would close it. A requirement that only the variant states is not in `depends`.
  And the comparison is of rules: an example that the variant states is
  never run against the code.
  Checked on stored results. The stored relations of the study of §8.4
  carry no status, so on them `waiting` is the study's `waits`: on each
  of the 21 readers of the ten tasks (the stored variant of the gift
  card and 20 new ones) it holds a requirement that differs in context where the reader may
  reject a run in context, or the comparison without context does not
  close that direction. That is 39 requirements, where the second rule
  of §8.4 holds 27 and the designed rule 48, and it leaves 84 cells
  certified, none false against the reference reading, with three true
  certificates held back (R-RET-1 of the atomic save). With a status, a
  review also lets go a requirement that is undecided only in the other
  direction. The 82 stored reviews, drawn again from their review.json
  by the engine before and after this change, give the same
  certificates, questions and reports.
  A second review, of the corrected rule, found one more gap, older
  than this change: the horizon of a comparison counted how far a rule
  looks back and left out the call that a rule over two consecutive
  calls (`next`) speaks of, so two readings that differ on such a rule
  compared as equivalent on runs of one call. The horizon is now the
  one `window_len` counts. No stored result moves: the tasks whose
  readings use `next` are objects or call services, and the bounded
  check compares them. The line under "Limits of this review" for a
  comparison that was cut short now says when it was the comparison in
  context. The state of a check in progress is kept by step name, so a
  check is finished by the engine that started it.
  Seven new tests, and assertions added to existing ones
  ([tests/test_limits.py](../tests/test_limits.py),
  [tests/test_obj.py](../tests/test_obj.py),
  [tests/test_partial.py](../tests/test_partial.py),
  [tests/test_replay.py](../tests/test_replay.py)).
- **A failed comparison in context keeps what the comparison without
  context closed** ([fcp/software.py](../fcp/software.py),
  `carried_over`; [fcp/review.py](../fcp/review.py), `Steps.run`,
  `check`, `held_back`, `verdicts`, `report`). Every verdict of a review
  rests on the comparison of its two readings in context: when that
  step failed, by an error, by its time or by its memory, the review
  certified nothing, also where the comparison without context had
  ended. For a requirement that the first comparison closed in both
  directions the second asks nothing, and for a requirement that only
  one reading states it compares nothing, so the record it writes for
  either is known before it runs (the entry on the carry above).
  `carried_over` gives these records from the first result. `check`
  hands them to the step as what it returns when it fails, together
  with the other requirements of the first result, the only ones that
  rest on the step. A failed step keeps `rests: all` in its record and
  names them under `reqs`, written when the failure is final: after a
  step stopped for its memory ran once more, and by the next checking
  process for a step that the watching process stopped. The verdicts
  hold back the named requirements, and every requirement after a
  failed step that names none; they draw no question from either. The
  report still begins with "This review is partial" and lists under the
  step the requirements that rest on it. A reader of review.json that
  knows nothing of `reqs` finds `rests: all` and takes the whole review
  as partial, which errs on the safe side. Nothing is kept where the
  first comparison failed too, and nothing for the bounded comparison
  of objects and of functions with effects, which in context can end
  with no behavior that meets the other requirements, also on a
  requirement that is equal without context. The comparisons with the
  third reader are left as they were. So a review certifies what the
  same review certifies when the step ends, less the named
  requirements: for every other requirement the record of the second
  comparison is the same whatever that comparison does.
  A review written before this change has no `reqs` and is drawn again
  as it was. Of the 82 stored reviews, 5 hold a failed comparison of
  the two readings in context; in 3 of them the first comparison failed
  too, and in each of the 5 another step on which every requirement
  rests failed as well, so none of them certifies more when drawn
  again; what a rerun gains is not measured.
  Five new tests, and assertions changed or added in three existing
  ones ([tests/test_limits.py](../tests/test_limits.py),
  [tests/test_partial.py](../tests/test_partial.py)).

## 11. From one function to any Claude Code answer

The same split, the prompt on the chip engine and the code run, now covers:

| Kind of code | Interface | Status |
|---|---|---|
| pure functions on integers and booleans | arguments and result as signals; the code also translated to z3 terms, so requirements can be proved for every call | **built** (§1-2, proofs §2.6) |
| functions on strings and lists | bounded sequences with quantifiers; a scope drawn from the readings; the code also translated, with sequences as terms, and requirements proved for every string the interface carries | **built** (§3, proofs §3.5) |
| stateful code (a class) | a reset creates the object, one method call per cycle; fields that are dictionaries or lists are translated too, and requirements proved over call sequences of every length where an invariant is found | **built** (§4, proofs §4.5) |
| a change to existing code | the old code's answers as inputs: a change contract | **built** (§5) |
| code with effects (a payment service) | the code receives an interface (`api.charge(...)`); every call it makes is an output event, every answer an input the scope scripts; requirements proved over every script of answers | **built** (§6, proofs §2.6) |
| code with effects it does not receive (a client library, `time.sleep`, three imported services) | the same events: the sandbox patches the names the code calls with the stand-in | **built** (§6.1, §6.4) |
| effects through objects the code makes (files from `open`, sockets) | the same events, recorded on stand-in objects; the run keeps its own view of which files exist; files proved over every run | **built** (§6.1, §6.3, proofs §2.6) |
| records (dicts, dataclasses) | one signal per field; a list of records, one sequence per field of one length | **built** (§7) |
| an object with several methods | each call one method, chosen by an `op` input; with number fields, requirements proved over call sequences of every length by induction | **built** (§8, proofs §2.6) |
| a program of several modules | the implementation is a package, entered at the dotted `module` of the design; relative imports work, the scope takes constants from every module but the tests, and mutants are drawn from every module | **built** (§8.3, [tests/test_package.py](../tests/test_package.py)); `fcp review --entry`; checked on its scope, not proved |

Proofs beyond the scope are built for pure functions on integers and
booleans, changes to them, functions on strings and lists (§3.5), code
that calls a service, files the code opens, and objects whose fields are
numbers (§2.6), dictionaries or lists (§4.5), over call sequences of every
length where an invariant is found and up to a number of calls otherwise.

## 12. The model alone on the ten requests

Every study above compares FCP with the tests the code writers wrote for
their own code. One comparison was missing: what the model says about the
request when it is simply asked
([experiments/alone_demo.py](../experiments/alone_demo.py); replies and
grades in [experiments/alone](../experiments/alone), counts in
[alone.json](../experiments/results/alone.json)).

Each of the ten requests went to Opus with no tools and no files, three
times under each of three instructions: the request as it is, which is what
the code writers of the studies got; the instruction of the HumanEvalComm
benchmark (Wu and Fard, 2025) to write the code or to ask clarifying
questions; and its instruction to ask clarifying questions or to answer
that there are none. The same model, again without tools, graded each of
the 90 replies against the planted conflict of spec_defects.yaml: 2 when
the reply says that the rules cannot all be met or asks which of them wins,
1 when it touches the rules without saying so (it follows one of them, or
asks about a consequence), 0 when it does not mention them. The summaries
the 30 code writers of the studies gave with their code, each asked for
"every decision you made where the request was unclear", were graded the
same way.

| Reply | Replies | Names the conflict | Touches the rules | Silent |
|---|---|---|---|---|
| Opus alone, the request as it is | 30 | 27 | 3 | 0 |
| Opus alone, code or questions | 30 | 27 | 3 | 0 |
| Opus alone, questions only | 30 | 27 | 3 | 0 |
| Haiku's summary with its code | 10 | 7 | 3 | 0 |
| Sonnet's summary with its code | 10 | 9 | 1 | 0 |
| Opus's summary with its code | 10 | 9 | 1 | 0 |

**On nine of the ten requests the model alone names the planted conflict in
every reply**, under every instruction, most often in its first sentence
("Rules 6 and 7 conflict as written. A $49.99 cart with no discounts would
cost $49.99 + $4.99 = $54.98. Add one more cent and it ships free for
$50.00, so adding to the cart lowers the charge by $4.98."). The judge
answers with a single digit, so I read replies against it: four of the 81
graded 2, drawn at random, and all fourteen graded 1. The grades stand. On these requests, then, finding the conflict is not what FCP adds
to a current model: a reader who asks Opus is told. What a reader of the
model's reply does not get:

- **The request where nobody was told.** On the loyalty package (§8.3) all
  nine replies and all three code writers take rule 9 as the rule: the tier
  is the highest the account has reached, rule 1 yields, and no reply says
  that the two rules clash. The questions asked there are about consequences
  of that choice (which tier sets the earning rate), not about the choice.
  It is the one request whose conflict has a natural repair, which is why
  it is passed over, and FCP names it with the calls `earn(50000); tier();
  redeem(1); tier()`. The same model did see it when its task was to
  formalize each rule literally (§8.3: both formalizers found it by
  reading); what it says depends on what it is asked.
- **The code under each way out.** Naming a conflict does not resolve it.
  Each model's code takes one way out and passes its own tests, and the
  rule that gave way is broken on calls its suite does not flag (§2.2,
  §2.4): the false assurance of the studies is measured on models that had,
  for the most part, said that the rules conflict.
- **A result that does not rest on attention.** The grades above come from
  a model reading a model. FCP's conflict is derived by an engine from two
  formal readings and comes with the calls on which the rules clash; it is
  found whether or not anyone noticed it, and it can be replayed.

The numbers are for one model at the effort level xhigh on ten short
requests, each with one conflict that I planted so that it is definite;
Haiku's summaries name seven of ten. Only the planted conflict was graded,
not the ambiguous phrases of the same requests, one of which is behind the
false assurance of the gift card (§8.2).

## 13. Requests I did not write: HumanEvalComm

Every code task above is a request I wrote, with one conflict that I
planted. This section runs `fcp review` on requests from an existing
benchmark, before any code is written, and compares the questions it asks
with what the same model asks by itself
([experiments/comm_demo.py](../experiments/comm_demo.py); the reviews and
the replies in [experiments/comm](../experiments/comm), counts in
[comm.json](../experiments/results/comm.json)). It is a pilot: 20 problems,
one model, one run.

### 13.1 Protocol

**The benchmark.** HumanEvalComm (Wu and Fard, 2025) takes the 164 problem
descriptions of HumanEval and rewrites each so that it is ambiguous (1a),
inconsistent (1c: the examples contradict the description) or incomplete
(1p: a part is removed). A model given such a description should ask before
it writes code. The file is fetched at a pinned commit and checked against
a recorded hash ([comm_fetch.py](../experiments/comm_fetch.py)). It is data
only: nothing in it is run, and no agent sees the benchmark's tests or
solutions.

**The screen.** A problem is kept when its values fit the types the
function adapter carries (§3): on the benchmark's own test cases every
argument and result is a boolean, an integer in 0..100,000, an ASCII string
of at most 32 characters or a list of at most 16 such integers; every test
compares with `==`; and the original and the three rewrites each parse as
one Python function. 57 of the 164 problems pass. The other 107 fall to the
first of these reasons that applies: a description that is not one Python
function (7), a value of another type (24), a test that does not compare
with `==` (2), a negative or large integer (31), tests that are not literal
values (29), a float (10), a missing rewrite (1), a long or non-ASCII
string (1), a long list (2). From the 57, 20 are drawn with a fixed seed:
HumanEval/46, 138, 73, 163, 61, 124, 49, 88, 26, 159, 64, 59, 41, 68, 80,
154, 48, 72, 144 and 134. Each has an original description and three
rewrites, so 80 requests; the 20 originals are the controls.

**The review.** Each request is the words "Complete this function:" and the
description with its signature. It goes through `fcp review` with a
signature and no code (§9): an adapter agent, a decomposer, two isolated
formalizers and a variant reader (Opus, effort xhigh), each confined to its
own workspace, then the checks on the request alone: the scenarios of each
reading, its conflicts and open choices, the two readings compared, and the
variant compared with each. Each search has a budget (120 s for a scope,
300 s for a conflict search and for a comparison), and the check of one
request runs in a process of its own inside 8 GB and 45 minutes. Each
request has a work directory outside the repository, under a key that names
neither the problem nor the rewrite, so an agent cannot find a sibling
description by name.

**The model alone.** The same model, without tools, under three
instructions: the benchmark's "generate Python3 code or ask clarifying
questions" (B1); its "ask clarifying questions, or return NO_QUESTIONS"
(B2); and the request exactly as the review gets it, with no invitation to
ask (B0). B1 asks when its reply has no `def`, B2 when its reply is not
NO_QUESTIONS.

**The judge.** The benchmark's own judging prompt, on the same model: given
the original description, the rewrite and the questions asked, it answers 2
for "good questions that recover the modified requirements" and 1 for
"fair questions" that cannot. A rewrite counts as recovered when the grade
is 2. B0 answers with code, so a prompt of the same form grades whether the
prose of its reply names what the rewrite changed (0 to 2). The judge sees
no code and answers with one digit, so I read a sample of its grades
against the questions (§13.4).

**Three levels of question.** A review's questions differ in what stands
behind them, and the judge grades three sets:

- *hard*: a conflict between requirements, a scenario the requirements
  exclude, a call the request leaves open, or a call on which the two
  readings differ. Each states a result of the engine about the request.
  Three of the four show it on a call that the engine found; a scenario
  question shows no call and names an example of the request that the
  rules of a reading exclude;
- *formal*: the hard questions and the `depends` question, which names the
  requirements whose result changes when a phrase both readers read the
  same way is read the other way, with a call. The judge is shown, with
  such a question, the list of those shared answers and their other
  readings;
- *all*: the formal questions and one question per phrase the decomposer
  flagged as ambiguous, which has no call behind it.

A `readings` or `depends` question that shows no call is of another kind.
Its comparison did not end, and it asks whether the readings mean the same
with no fact to show. It is counted apart, as *undecided*, and is part of
the full set only (§13.1 has the correction that put it there). A review
now gives such a question the kind `undecided` itself (§10).


**What changed while the pilot ran.** The benchmark exposed faults in the
engine and in the review, and I fixed them between steps. The numbers below
were produced across these changes, so each is listed with what it touched:

- *Before any check of the pilot run:* the rule for open choices. The
  first two reviews of a trial asked about calls the request itself
  excludes. A call
  that breaks a condition on the caller is now outside the contract and is
  not asked about, one question covers all the open outputs of a call, and
  the two answers shown are small (§9).
- *After the agents of the first six problems:* an agent's reading with 32
  wide free values made the engine list their combinations and took the
  run to its memory cap, on HumanEval/49. Two faults behind it are fixed
  (the monitor counts the combinations before it lists them; the lookback
  of a chain of definitions is computed once per definition), and every
  `fcp` command an agent starts now runs inside 1 GB and 120 s. The 24
  requests of the first six problems were read before this, the other 56
  after. The fixes change time and memory, not what a reading means.
- *After the first checks:* the check of one request (HumanEval/46, 1a)
  ended at its memory cap, and one review (the HumanEval/163 original)
  asked an open choice that a rule over a wide range in fact settles. The
  review now bounds the engine tasks it runs at a time, searches scenarios
  before anything else, names a search that did not end under its limits,
  and replays both answers of an open choice on the monitor before it asks
  (§9). Both requests were checked again; the earlier results are kept
  beside the new ones (`check<n>_review.*`).
- *During the checks of the other 56:* four faults, each fixed, and the
  requests they touched checked again with the earlier results kept
  (`check<n>_review.*`).
  The check of the HumanEval/49 original failed in seven seconds: a
  constant wider than 32 bits was written in a form yosys does not read.
  It is written in pieces now, and `min` and `max` keep the narrower of
  their ranges (§10).
  The check of the HumanEval/26 original spent 1,895 of its 1,985 s
  collecting candidate calls for one reading, after which the conflict
  search of that reading checked none of its 305 candidates; the review
  said so under its limits. The reading has eight definitions that each
  name the one before three times, and two searches of the integer
  encoding walked, and computed, a definition again at every use: 3^8 uses
  of the first. A definition is now walked once and computed once per call,
  and the one walk that must keep the conditions it passed stops expanding
  definitions after 100,000 nodes and is named under the limits when it
  does (§10). The same fault kept the check of HumanEval/26 1a in the
  comparison of its two readings for 39 minutes, and that check was stopped
  at its 45 minutes.
  Two requests whose readings have such chains (HumanEval/26 1p and
  HumanEval/144 1a) were held back before their checks and checked once,
  with the fix.
  The check of HumanEval/144 1c ended after 130 s with a Python
  `MemoryError`. The readers of HumanEval/144 ("True
  if x * n evaluates to a whole number") wrote the whole number as a rule
  for every q: if the numerator is q times the denominator, the result is
  True, with q over up to 10^28 values. The integer encoding lists one
  instance of such a rule per value, and had no bound on how many. A rule
  over more than 4,096 values, the number a replay runs, is now declined
  as other formulas the encoding does not take are, and left to the scope
  and the bit level (§10). The check of the HumanEval/144 original had
  been stopped at its 45 minutes, in the comparison with the variant
  reading; its readings have such a rule over 10^20 values, and whether
  the rule is what made that run long was not established. Checked
  again, it ended in 26 minutes.
  The checks of the four requests of HumanEval/72 (`will_it_fly(q, w)`)
  each failed within two seconds with a Python `TypeError`. The adapter
  had listed the three example lists as values of `q` to try, which the
  bundle format allows. The integer scope, which is computed when a
  function of a string or list also takes a number, took the configured
  values of every argument for integers. No bundle before these four had
  a list beside a number and values for the list. The values of a string
  or list are no longer part of that scope (§10).
  One more change is to wording only. Where both readings found the same
  clash on the same call, the question of that conflict ended "(also with
  , at 2 places)": the two findings were counted as two places, and the
  list of further requirements was printed although it was empty. Five
  reviews of the pilot carried it, on twelve questions (HumanEval/61 1c,
  134 1c, 138 1a, 138 1c and 163 1c). The review of 163 1c was made
  again later, for the last fault of this list, and no longer does; the
  other four, with nine questions, are left as written. The clause now
  names further requirements only when there are some and counts
  distinct calls (§10).
  What the fix can change was measured, since the other checks ran without it.
  On 289 of the 290 readings of the pilot and of the repository's own
  tasks the new walk visits the same
  nodes in the same order (the other is the reading whose walk would have
  1.2e16 nodes); the terms the encoding builds are the same, term by term,
  on 414 encodings of 209 readings (10,399 terms; 44 further encodings
  raise the same error with and without the fix, and 8 are built in a
  minute only with it); and on a reading of the
  HumanEval/26 original the two searches put the same queries to the solver
  in the same order and get the same answers. The calls drawn can still
  differ: of two models of the same query the solver returns the one its
  internal numbering of terms leads to, and the fix changes how many terms
  are alive. So a check repeated with the fix asks the same questions of
  the solver and may show different example calls.
- *After the checks, from what the reviews show:* two more faults. They
  stopped no check. Each put into a review a statement that is not true
  of the readings, and no step of the engine noticed.
  The first I found by reading the review of HumanEval/26 1a by hand. Two
  of its `readings` questions asked which of two readings is meant under
  a call on which the two readings agree. One reader had stated its rules
  for every value of an element, 0 to 255, and the comparison at the bit
  level gave a rule over more than 64 values no place (§10). Six reviews
  of the pilot have such a rule in a reading (HumanEval/26 1a and 1c, the
  49 original, the 144 original and 1c, the 163 original), and the six
  were checked again with the fix. In 26 1a the two questions are gone;
  the review now asks of both requirements whether the two readings mean
  the same, and says that it could not show that they agree. In 144 1c
  two requirements that had "no difference in context" are undecided and
  a `depends` call is gone. In the 144 original the two rule requirements, which the comparison
  had not asked at all, are asked and stay undecided, and the three
  example requirements, certified before, were no longer decided within
  the 300 seconds of the comparison. In the
  49 original and 26 1c the relations between the two readings are
  unchanged and those with the variant reading are not (two are
  undecided in the 49 original; 26 1c shows other calls). The 163
  original is unchanged.
  The second fault was found by a replay that I wrote because of the
  first. Every line `name(args) -> result` that a review shows as a call
  on which two readings differ is read back and run on the compiled
  monitors of the two readings, without a solver
  ([experiments/comm_replay.py](../experiments/comm_replay.py), §13.4).
  On HumanEval/46 1a the replay did not confirm
  `fib4(8) -> returned something else`: the solver had given the call an
  outcome code that names no ending, and the line printed it in the words
  of another code (§10). What the fix can change was measured before the
  rechecks. A search that leaves the code free finds nothing new where
  some code that names an ending makes every comparison of the outcome
  true or false exactly as the unnamed code does. That holds for the
  frame rules and the three readings of 63 of the 80 requests; in 60 of
  them every use of the outcome is a comparison with a number, in one
  more it is compared with a definition that is the constant 0, and two
  compare the outcome of a call with that of the call before. Of the
  other 17, three state the codes in a frame rule of their own, which
  the fix repeats, and three have no review. The remaining 11 and the two
  that compare two calls were checked again with the fix.
  All 13 got a review again. In HumanEval/46 1a the question under
  `fib4(8)` is gone, and the two readings agree on its requirement. In
  144 1p two comparisons that had been cut short ended, and two
  questions that showed no call now show calls. In the 144 original the
  three examples are certified again, and three questions that showed no
  call are gone. Two things differ between this run and the one before
  it, the fix and the load on the machine, and which of them decided
  that for the two HumanEval/144 requests was not measured. In 138 1p
  two requirements whose readings differed when compared alone now agree
  (in context they agreed before, and no question changed). In four
  reviews a question shows another call and asks the same (41 1c, 163
  1c, 80 1c and the 80 original; in the last, one of the two directions
  of the comparison behind the call is now undecided). The other five
  ask what they asked before (61 1p, 154 1a, and the 49, 61 and 72
  originals).
- *A correction to the count, made when the reviews were read.* The pilot's
  script counted every `readings` question as hard and every `depends`
  question as formal. 17 of them, in 10 reviews, show no call: the
  comparison behind them did not end, and the question reports a search
  that was cut short, not a fact about the request. Until the fix above
  such a `readings` question also read "the two readings of this
  requirement disagree (no separating call was found within the budget):
  which is meant?", which says more than was shown. It now reads "the two
  readings of this requirement were not shown to agree, and no call that
  separates them was found: do they mean the same?". Four reviews made
  before that change carry the earlier sentence (the HumanEval/46
  original, 68 1c and 1p, 88 1p) and are left as written. The `depends`
  question that shows no call says in these reviews that the
  requirements "mean something else" when read the other way, which was
  not shown either (five reviews: the HumanEval/61 and 144
  originals, 144 1c, 154 1a and 163 1a); the engine has since changed
  its wording and its kind (§10).
  These questions are now counted apart, as *undecided*. They are part of
  the full set and of neither smaller set, and the judge graded again the
  sets that lost a question. With the correction a hard
  question is counted on 34 of the 53 reviewed rewrites, not 36
  (HumanEval/26 1a and 144 1c ask undecided questions only), and on 3 of
  the 19 reviewed originals, not 5 (the HumanEval/46 and 144 originals).
  A question with a result of the engine behind it is counted on 50
  rewrites, not 52, and on 13 originals, not 16. The grades moved in two
  requests. The formal set of 154 1a is now empty (it had been graded
  fair). That of 163 1a is now the same text as its hard set, and the
  judge graded it fair where it had graded the hard set good (§13.8).

Two sets of requests were read more than once. The eight requests of the
first two problems were first read and checked in a trial without the
sandbox; the pilot uses the later, confined run, and the trial's reviews
are kept for a comparison of two runs (§13.4). The four requests of
HumanEval/49 were read again after the first attempt ended at the memory
cap. No reading was edited by hand, and no request was dropped: the 80 are
the 80 drawn.

### 13.2 The 60 rewrites

A review exists for 53 of the 60 rewrites; §13.5 says why the other
7 have none. On the 53:

| asked or named, and graded good | 1a (17) | 1c (18) | 1p (18) | all (53) |
|---|---|---|---|---|
| FCP, hard questions alone | 7 | 14 | 2 | 23 |
| FCP, formal (hard and `depends`) | 15 | 17 | 15 | 47 |
| FCP, all questions | 17 | 18 | 17 | 52 |
| the model, code or questions (B1) | 8 | 16 | 13 | 37 |
| the model, told to ask (B2) | 15 | 18 | 17 | 50 |
| the model, no invitation, names it (B0) | 13 | 17 | 12 | 42 |

Over all 60 rewrites, with a request that has no review counted as not
recovered, FCP's three rows are 23, 47 and 52 of 60; B1 asks good
questions on 40, B2 on 56, and B0 names the change on 48.

Three things in this table need saying before anything is read from it.

*The judge does not separate.* It graded every set of questions that B1
asked (40 of 40) and that B2 asked (56 of 56) as good, and 52 of the
53 full sets of FCP. What the grade measures in practice is whether
anything was asked that touches the change. So the rows for the model are
the counts of requests it asked about, and the differences between rows
are differences in whether a question was asked at all.

*The model told to ask is hard to beat here.* B2 asks about 56 of the 60
rewrites and about 1 of the 20 originals (§13.3). A rewrite of this
benchmark is a visible defect in a short text: a phrase made vague, an
example changed, a sentence cut. A careful reader sees it, and the model
is one. FCP's full set of questions is level with B2 on the requests it
reviewed (52 against 50 of 53) and ahead of the benchmark's own
instruction, B1 (37), which lets the model answer with code.

*The hard level is the part with a proof behind it, and it is the lowest
row.* A hard question was asked on 34 of the 53 reviewed rewrites
and graded good on 23. On the other 19 the review asked no hard
question; the change was then named, if at all, by a `depends` question
or an ambiguity question, which rest on the decomposer's reading of the
text, as the model's own questions do. Not every hard question shows a
call: on 27 of the 34 at least one does, and on the other 7, all of them
inconsistent rewrites (HumanEval/26, 48, 72, 73, 88, 124 and 154), every
hard question is a scenario question.

FCP was graded good where the model missed on these requests: B1 missed
16 of the 53, and FCP's full set was good on 16 of them; B2
missed 3, FCP good on 3; B0 missed 11, FCP good on 11. On
three requests none of the three instructions asked or named the
change (HumanEval/61 1a, 73 1a and 73 1p), and FCP's formal questions
were graded good on each (§13.4 reads them).
FCP's full set missed one request that all three instructions caught
(HumanEval/124, 1p).

### 13.3 The 20 originals: what the questions cost

The originals are the controls: descriptions that were not changed. The
model asks about almost none of them: B1 about 0 of 20, B2 about 1.
A review exists for 19 of the 20, and it asks something on every one
of them:

| on the 19 reviewed originals | requests asked about | questions, mean (median, max) |
|---|---|---|
| hard | 3 | 0.3 (0, 2) |
| `depends` | 13 | 0.7 (1, 1) |
| ambiguity | 19 | 5.9 (6, 12) |
| undecided (a comparison that did not end) | 3 | 0.3 (0, 3) |

So a review has no "nothing to ask" state at its full level: the
decomposer flags 10.1 phrases per original on average (the table counts
a phrase that is flagged on several requirements once), and one `depends`
question follows whenever the readers shared an answer that matters. As a
detector of a changed request the full set is useless (it asks on every
request), and the `depends` level nearly so. The hard level separates:
a hard question on 34 of 53 rewrites against 3 of 19
originals. The model told to ask separates better on this benchmark: 56 of
60 against 1 of 20. One reason it can is outside this pilot's reach: the
originals are HumanEval's descriptions, which the model has very likely
seen, so a changed description can stand out for a reason that would not
hold for a request nobody has published. FCP's agents are the same model,
so the same holds for them.

The reviews of the pilot ask about the phrases flagged on guarantees and
examples only. With the phrases of every kind of requirement (§10) the 19
originals would carry 9.5 ambiguity questions each (median 9, at most 16),
and the 53 rewrites 11.2 where they carry 7.7.

§13.4 reads the hard questions on the originals by hand.

### 13.4 The questions, read by hand

The judge answers with one digit and is lenient (§13.2), so I read every
hard question of the reviewed requests against what the rewrite changed.

**A hard question lands on the change in 33 of 53 reviewed rewrites**
(1a 9 of 17, 1c 14 of 18, 1p 10 of 18). Some of them:

- HumanEval/88, 1a: "ascending order if the sum is odd or even, or
  descending if the sum is even or odd". Read as written, both orders are
  required at once, and the review reports a conflict on
  `sort_array([1, 0])`. In 1p the sentence is cut after "or sort it", and
  the review asks whether `sort_array([6, 0])` returns `[0, 6]` or
  `[6, 0]`. In 1c two examples are swapped, and the review says of each
  that it can never happen under the rule.
- HumanEval/64, 1a: "returns the number of characters or vowels". The
  review asks whether `candidate("Z")` returns 0 or 1.
- HumanEval/41, 1a: "2*n or n cars are driving left to right". The review
  asks whether `car_race_collision(1)` returns 2 or 4.
- HumanEval/138, 1a: "the sum of exactly 4 positive even numbers" becomes
  "the sum of 4 numbers". The review reports that the example
  `candidate(4) == False` conflicts with the rule as now worded.
- HumanEval/159, 1c: the second number of all four examples is changed.
  The review reports four conflicts, one per example, each with the rule
  for the carrots left.

**The judge calls 10 of these 33 fair, not good**, and it has a
point. In 1p rewrites the removed text is often the whole rule. The review
then shows a call with two allowed results (`candidate(0)`: 0 or 1, for
HumanEval/41 with its last three sentences removed). That locates the gap
exactly, but the answer to it settles one call, not the rule that is
missing; the benchmark's criterion is whether the answer would recover the
requirement. A person asked that question would answer with the rule. The
judge is not asked to assume that.

**No hard question on the change in 20 reviewed rewrites.** In all
but two of them both readers answered the changed phrase the same way,
so the engine was given two readings that agree, and a request on which
every reading agrees has nothing to show on a call. Three kinds:

- *A contradiction the readers settled*
  (HumanEval/41 1c, 46 1c, 64 1c, 72 1a).
  In HumanEval/64, 1c, the examples are changed to 5 and 5. The
  decomposer saw that they contradict the definition of a vowel and wrote
  the contradiction down as an ambiguity with two answers ("the examples
  are wrong", "the examples are authoritative"). Both readers took the
  first, and left the examples out. The same happened with the three
  changed examples of HumanEval/46 and with HumanEval/41, whose function
  is renamed `is_prime` over a text about colliding cars.
- *What is left of the request still points to the original meaning*
  (HumanEval/26 1p, 61 1a and 1p, 72 1p, 73 1a and 1p, 80 1a and 1p, 124 1p, 134 1a, 138 1p, 154 1a and 1p, 159 1a).
  "The minimum number of elements that need to be changed" becomes "the
  number of elements"; "every opening bracket has a corresponding closing
  bracket" becomes "every closing or opening bracket has a corresponding
  closing or opening bracket"; "exactly 4 positive even numbers" is cut
  after "exactly 4" under a function still named `is_equal_to_sum_even`.
  Both readers read the original meaning. So did the model: on three of
  these requests none of the three instructions made it ask or name the
  change.
- *A rule the engine could not use*
  (HumanEval/26 1a, 144 1c).
  One reader of each wrote the rule that carries the change for every
  value of a variable: an element, 0 to 255, and a quotient, up to
  10^12. The conflict search leaves such a rule out and a comparison
  cannot assume it (§10), so the engine did not decide whether the two
  readings agree. The review names the rules under its limits and asks,
  with no call, whether the two readings of the requirement mean the
  same. Before the fix of §13.1 the review of HumanEval/26 1a showed two
  calls here, on which the two readings agree.

The changed phrase is asked about at the ambiguity level in 19 of the 20,
and where the readers' shared answer matters the `depends` question lists
it among the shared answers (about ten per request). That is why the
formal and the full set are graded good on most of them. It is a weak
hit: the question has no call behind it, and the person reading the
review has to find the phrase in a list. The exception is HumanEval/80,
1p, where the sentence that defines a happy string is removed. The
decomposer wrote "the request never defines the property" and four
meanings of "happy" on a requirement of the kind `definition`, and the
queue asked about the ambiguities of guarantees and examples only. The gap
reaches the person through the `depends` question, whose call
`is_happy("dcbabaiagfpgflaq")` separates two rules that fit the six
examples. The queue now asks about the phrases of every kind (§10):
redrawn, this review asks which of the four meanings is meant.

**The one request FCP's full set missed** is HumanEval/124, 1p, where the
list of rules for a valid date is removed. The decomposer noted that the
list is empty and flagged two phrases; the judge graded the two questions
fair, and all three instructions to the model asked what the rules are.
Five more phrases are flagged on the assumption and the definitions, which
the queue of the pilot did not ask about. Redrawn (§10), the review asks
whether "all of the following rules" means an empty list under which every
string is valid, rules that were left out, or the rules of a conventional
date check. The judge has not graded the redrawn reviews.

**Hard questions on originals.** Three of the 19 reviewed originals have
one, six questions in all, and I read each for whether it is a finding.
HumanEval/64: one reader counts lowercase vowels only, the other either
case; the description lists 'a', 'e', 'i', 'o', 'u' and its example
`vowels_count("ACEDY")` is 3. That is a real gap between the rule and the
example, which the example answers; two questions were asked about it.
HumanEval/154 ("True if the second word or any of its rotations is a
substring in the first word"): two `readings` questions, with the calls
`cycpattern_check("", "")` and `cycpattern_check("", " ")`, and beside
them the `depends` question with `cycpattern_check(" ", "")`. All three
ask about an empty second word, which the description does not settle:
also a real gap, and one that no example answers. HumanEval/49 (2^n
modulo p): an `open` question on `modp(0, 0)`, for which the description
names no result, which is true to the letter and pedantic; and a
`readings` question on `modp(1, 2)`, where the two readers differ only
because each wrote the power, which FCP-PL lacks, in another way (§13.5).
That one asks about the readers, not about the request. So four of the
six questions are on real gaps, one is pedantic and one is an artifact of
the language.

Three more originals (HumanEval/46, 61 and 144) carry undecided questions
only: a comparison that did not end, counted apart (§13.1). Before that
correction the one of HumanEval/46 had been counted as a hard question.

**Two runs of the same eight requests.** The requests of the first two
problems were also reviewed in a trial before the pilot run (§13.1). The
number of hard questions differs between the two runs on 4 of the 8: the
readings are written by a model, and a different pair of readings gives
the engine different formulas to compare. The pilot's counts are one draw.

**Every shown call, replayed.** A `readings` question and a `depends`
question show a call on which two readings differ, printed as a line
`name(args) -> result`. After the fault found by hand in HumanEval/26 1a
(§13.1), every such line of every review was read back from its text and
run on the compiled monitors of the two readings, without a solver
([experiments/comm_replay.py](../experiments/comm_replay.py); results in
[replay.json](../experiments/comm/replay.json)). A line is confirmed
when one reading accepts the call, the other rejects it, and a rule of
the requirement in question is among those it breaks.
Of the 72 reviews, 13 show no such line. The other 59 show one under 68
questions (10 `readings`, 58 `depends`). A `depends` question is replayed
once for each requirement it names with a call, which makes 119 replays,
and all 119 are confirmed. Three reviews needed more than the script
gives a request by default (3 GB, 300 seconds, and 4,096 combinations of
a reading's free values). The two HumanEval/80 reviews with such a line,
the original, whose call is a string of 32 characters, and 1c, were
replayed inside 8 GB, in 552 and 581 seconds. One call of the
HumanEval/49 original, `modp(1, 2) -> 0`, is rejected by a reading with
65,536 combinations of free values, and was replayed with the bound
raised to that number. The counts are of the stored reviews, after the
rechecks of §13.1: the line that the replay did not confirm on its first
pass, `fib4(8)` of HumanEval/46 1a, is no longer in a review.
The replay reads what is printed, so it checks the printing as well: a
line that does not print back as itself is reported. It does not cover a
conflict, an open choice, or a question that shows no call.
The reviews of this pilot were written without such a step, and the
script ran after them. A review now runs the replay itself, before it
shows a call (§10).

### 13.5 Where the engine stopped

Every one of the 80 requests got its five agents and two readings that
pass `fcp lint`. 72 got a review. The other 8:

- **HumanEval/49** ("return 2^n modulo p"), three of its four
  requests. FCP-PL has no modular power, and `%` takes a constant divisor.
  The readers built the function from what the language has: `1 << n`
  with n up to 100,000, and the remainder as a table with one row per
  divisor (`p == 1 ? x % 1 : p == 2 ? x % 2 : …`, up to 1,023 rows).
  Translating such a monitor for the solver did not end in 300 s.
  The original first failed on a fault of the engine (a constant wider
  than 32 bits, §13.1). Checked again after the fix it got its review in
  half a minute, because its readers had written the power another way:
  one by induction over calls, the other as a shift of at most 28 places.
- **HumanEval/59** ("the largest prime factor of n"), all four requests.
  The readers wrote "prime" with nested quantifiers (no i below 255 and j
  below 254 with n = (i + 1)(j + 2)…): about 65,000 remainder circuits on
  a 16-bit value. The first step of the check passed 8 GB within 13 to
  77 seconds and the check was stopped.
- **HumanEval/144 1a** (a product of two fractions given as strings, in
  its ambiguous rewrite). The readers stated rules for every value of a
  numerator and of a denominator, over ranges of 10^28 and 2·10^14
  values, and one monitor is 3.6 MB of Verilog. The check passed 8 GB
  after 497 seconds and was stopped.

The screen of §13.1 looks at the types of the values, and both problems
pass it: their arguments and results are small integers. What they need
is arithmetic the language does not have, and a reader who builds it from
shifts, tables and quantifiers writes a formula that is correct and that
the engine cannot translate. Two of twenty screened problems fall there,
and one request of a third.
In the engine of this pilot a review had no partial result for such a
request: one step that failed ended it. The readings and the decomposer's
questions exist and are in the repository, but nothing was checked, so
the tables above count these requests as not reviewed.

**The eight, checked a second time.** The engine now writes a review
whatever a step of its check does (§10). I checked the eight requests
again with it (engine `33a0f99`), from the stored readings and inside
the limits of the pilot: 8 GB and 45 minutes for a check, and inside
the check 6.8 GB and 15 minutes for a step
([experiments/comm_again.py](../experiments/comm_again.py), counts in
[comm_again.json](../experiments/results/comm_again.json), each review
in the `again/` directory of its request). No agent ran and no judge
graded the result. These reviews are counted apart: every table of this
section stays at 72.

| Request | Steps that did not end | What stopped them | Settled | Questions | Check | Most memory (GB) |
|---|---|---|---|---|---|---|
| 49 1a | 3 of 11 | translation 2, memory 1 | 0 | 14: 1 `open`, 1 `depends`, 6 undecided, 6 `ambiguity` | 28 min | 7.2 |
| 49 1c | 4 of 10 | translation 4 | 0 | 10: 2 undecided, 8 `ambiguity` | 37 min | 2.5 |
| 49 1p | 4 of 10 | translation 4 | 0 | 7: 2 undecided, 5 `ambiguity` | 28 min | 2.6 |
| 59 1a | 8 of 10 | memory 7, step time 1 | 0 | 5: 1 undecided, 4 `ambiguity` | 30 min | 7.4 |
| 59 1c | 5 of 10 | memory 1, step time 1, check time 3 | 0 | 3: 1 `scenario`, 2 `ambiguity` | 39 min | 7.1 |
| 59 1p | 7 of 10 | memory 2, step time 1, check time 4 | 0 | 3: 1 `open`, 2 `ambiguity` | 39 min | 7.0 |
| 59 original | 6 of 10 | memory 2, step time 1, check time 3 | 0 | 1: 1 `ambiguity` | 39 min | 7.5 |
| 144 1a | 6 of 10 | step time 1, check time 5 | 0 | 7: 7 `ambiguity` | 39 min | 6.9 |

"Translation" is the translation of the monitors for the solver that did
not end in 300 s. "Memory" is a step that passed 6.8 GB, also when it
was run once more with one engine task at a time. "Step time" is a step
that did not end in 15 minutes. "Check time" is a step that was
stopped, or not started, when the check had used 39 minutes; the other
6 of the 45 are kept for writing the review. The last column is the
most memory that the processes of the check held together during a
step. An undecided question is a comparison of the two readings that
ended neither way (§13.1).

All eight now get a review, and every one is partial. 43 of their 81
steps did not end, and no review settles a requirement. The causes are
those of the pilot: the translation of HumanEval/49 still does not end,
the searches of HumanEval/59 still pass their memory, and in
HumanEval/59 and 144 the steps that ran into their limits used up the
time of the check before its last comparisons started. What has changed
is that the steps that did end are reported.

They do not report much. Of the 50 questions, 35 are the `ambiguity`
questions of the decomposer, which needs no solver, and 11 are
undecided. Four rest on a result of the engine. Read by hand against
what each rewrite changed, two of them are about the change itself: in
59 1c the example that the rules of a reading exclude (the rewrite
changed the example's answer from 29 to 5), and in 59 1p the call
`candidate(6)`, for which the request allows 2 or 3 (the rewrite
dropped "largest"). The `depends` question of 49 1a shows a call,
`candidate(0, 2) -> 1`, and covers the changed phrase among eight
shared answers; its `open` question is about a modulus of 0, which the
review of the original asks as well. Each of the seven rewrites is
asked about its change by an `ambiguity` question. The original of
HumanEval/59 gets one `ambiguity` question.

So a partial review brings these requests to the level of the
decomposer's questions, with a result of the engine about the change on
two of seven rewrites. The arithmetic named above is as far out of the
engine's reach as it was.

27 of the 72 reviews name a limit under which they were made.
In 26 it is a search that did not end under its budget (the collection of candidate calls, a comparison of two readings, a scenario search, a conflict search); in 4 it is rules that a search leaves out because they are stated for every value of a variable.
Such a review certifies nothing that rests on the unfinished search, and
says which search it was.
23 of the 80 requests were checked more than once, and the stored review
is the last one (`status.json` keeps the earlier checks). For 11 the first
check failed, was stopped or was held back on a fault of §13.1; checked
again with the fix, ten got a review and one (HumanEval/144 1a) passed
the memory limit. For the other 12 a fix could change a finished review,
and the review was made again (§13.1).

### 13.6 What the agents touched

Each agent runs confined to its workspace: its own files, the `fcp`
command, and nothing else of the machine or the network (§9). The
transcripts of all 409 agent runs were read by a script
([audit.json](../experiments/comm/audit.json)). 2,074 shell commands ran,
566 were refused by the sandbox or the permission rules, 46 failed.
In the 80 final attempts 92 tool calls named a path outside the
workspace; 91 were refused and 1 ran: a listing of the directory
in which Claude Code keeps that agent's own session memory. No agent read
the benchmark file, a sibling request, or another agent's workspace.

### 13.7 Cost

| per request | FCP review | the model alone |
|---|---|---|
| model calls | 5 agents with tools | 1 call (per instruction) |
| time, agents | 12.8 min mean (6.1 to 48.8) | seconds |
| time, checks | 5.8 min mean, 0.7 median, cap 45 | none |
| notional price | $3.87 | $0.02 |

In all: 17.1 agent hours and a notional $310 for 80 requests, and
12.8 hours of checks summed over the requests, of which two ran at a
time on one 32-core machine.

### 13.8 What this pilot does and does not show

- It is 20 problems of the 57 that pass a screen on types, one model, one
  run. The numbers are counts. Nothing here is a rate.
- The judge is the benchmark's prompt on the same model, and it grades
  nearly everything good. I report where its grades and my reading differ
  (§13.4) and have not replaced it. It is also not stable. In five
  requests two of the judged sets are the same text, graded in separate
  calls, and in two of the five the grades differ, good against fair
  (HumanEval/64 1p and 163 1a). The grades stand as given.
- The model has very likely seen HumanEval. That helps it notice a changed
  description, alone and inside FCP's agents alike, and this pilot cannot
  say by how much.
- 8 requests have no review, and 27 reviews name a limit. Checked a
  second time by the engine that followed the pilot, each of the 8 gets
  a partial review that settles nothing (§13.5); they stay outside
  every count.
  The engine changed while the pilot ran (§13.1): the faults the
  benchmark exposed were fixed as they were found, the reviews a fix
  could reach were made again, and the others stand as first made.
- Two of those faults put a false statement into a review, and no step
  of the engine noticed. One was found by reading a review by hand
  and the other by the replay written because of the first. A review of
  this pilot is therefore checked evidence only as far as §13.4 reports:
  the 119 shown calls on which two readings differ were run again and
  are confirmed; the calls under a conflict or an open choice, and what
  a scenario question says of an example, were not run again.
- No code was written or tested. The benchmark's own measure is whether
  the code written after the questions passes its tests; this pilot stops
  at the questions.

What it does show. On requests I did not write, with defects I did not
plant, a review asks a hard question on 34 of the 53 changed requests it
reviewed and on 3 of the 19 unchanged ones. On 27 of the 34 and on the 3,
such a question shows what it found on a call that a person can check in
a line; on the other 7 it names an example of the request that the rules
of a reading exclude.
It also shows that this is not more than the model does when it is told
to ask: on short, public, single-function requests, B2 asks about nearly
every changed request and about almost no unchanged one, and its
questions are pointed: on four replies I read against the change, each
names what was removed or blurred in its first sentence, and one offers
two candidate rules with inputs on which they differ. What a review adds
on such requests is not the question. It is that the call under a hard
question was found by a solver on readings written apart, where the
model's example is offered unchecked; that a call which separates two
readings was, in this pilot, also run again on their monitors without a
solver (§13.4); and that the review says what it could not settle. Whether that is worth five agents
and minutes of checking per request, against one call, is not shown by
this pilot; the place to look is requests too long for one reading to
hold, and the code written afterwards.

What the engine needs next, from this pilot. None of it was done in the
pilot, and no number of this section is from a later engine; three of
them are done since (§10) and say so.

- A step that fails should be recorded while the review goes on and
  certifies nothing that rests on it. In the pilot one failed step ended
  the review (§13.5). Done since.
- Each tool process needs its own memory limit and each step its own
  deadline, inside the engine. In the pilot a launcher held both from
  outside. Done since, with one memory limit for the checking process
  and all the tools it starts, not one per tool.
- `fcp lint` should refuse what stopped these checks before a check
  starts: a constant wider than the language's integers, a rule that
  names an outcome code no ending has, a formula whose translation passes
  a size.
- A comparison should share its time so that a rule the engine cannot
  decide does not use up the time of the rules it can.
  The 144 original is the case: its comparisons ran out of time in both
  of its last two checks, and the three examples were decided in one
  and not in the other.
- Every call should be replayed on the monitors before a review shows
  it, as the script of §13.4 does afterwards. Done since for the calls
  on which two readings differ, where the function takes and returns
  plain values; the calls under a conflict or an open choice are still
  not read back.
- A question behind which no comparison ended should be worded and
  classed as undecided by the review itself. Done since (§10): such a
  question has the kind `undecided`, and the question about the shared
  answers says "mean something else" only of the requirements that were
  shown to differ.
- A shown call should be one a person can read: the shortest that
  separates, with printable text.

## 14. Limits

- **Scope, not proof.** Each implementation is checked on its scope (from
  50,000 runs to 3.6 million calls). A bug outside the scope is outside the
  evidence, except for code that translates (§2.6, §3.5): pure functions
  on integers, booleans, strings and lists, changes to integer functions,
  code that calls a service, files it opens, and objects whose fields are
  numbers, dictionaries or lists (§4.5), where a requirement can be proved
  for every call, every run, or every sequence of calls the interface
  carries. An object whose lists grow without bound, or whose one list
  serves every key, is proved only up to a number of calls. A string proof is for the
  strings the interface declares (here up to 32 characters of one byte
  each), not for longer ones. Inputs the interface cannot carry (negative numbers,
  floats passed for ints, missing keys) are never tried, by proof or by
  scope; the models' own tests often cover exactly those.
- **Ten prompts.** I wrote them, with planted defects, and checked them
  against three models' code; each answer is one function or class, and
  in one task a package of three modules. Asked without tools, a current
  model names nine of the ten planted conflicts by itself (§12). On 80
  requests of a benchmark I did not write, the model told to ask does so
  on 56 of the 60 changed requests and on 1 of the 20 unchanged ones;
  what a review adds there is a result of the engine under a question,
  most often a call, and a statement of what it could not settle, and 8 of the 80 requests
  got no review; the engine that followed gives each of them a partial
  review that settles nothing (§13).
- **A package is not proved.** The translator reads one module. The loyalty
  package is checked on its scope, and there one mutant per model survives
  (a gold rate of 4 instead of 3) that each model's own tests kill (§8.3).
- **A requirement stated only as a scenario** (an example run) is not part
  of the comparison of readings, so FCP holds it: it reports the agents'
  readings as not agreeing on it.
- **A reading without assumptions** rejects runs that no implementation can
  produce, and so compares as stronger than a reading that assumes them
  away. The frame narrows the runs both range over (§6.4); what is left is
  measured by comparing under the other reading's assumptions. A reader
  that states one more assumption than the others therefore differs from
  them on nearly every requirement: held as designed, that cost 12 true
  certificates in §8.4.
- **Correlated readers.** Agreement between readings is evidence about the
  readings, not about what the author intended. In the gift card both
  readers and all three models took the same side of a flagged phrase, and
  FCP certified three violations. A reading per answer removes them and
  leaves no false certificate on the ten tasks, at two or three more agent
  runs per task (§8.4); under the rule that `fcp review` applies once it
  has the code, it also holds back three of the 87 true certificates. It
  guards a question that was asked. On 8 requirements both stored readers
  accept a run that the reference rejects; a new reader may reject such a
  run on 5 of them, and the other 3 turn on words that nobody flagged
  (`fcp review` holds one of the three, on a difference without
  context).
- **A proof is confirmed, not checked.** A second solver decides again
  every formula behind a proof (§2.7), which guards against a wrong answer
  of z3. The translation of the code and of the reading is validated on
  the scope, not proved, and the rewriting before a formula reaches a
  solver, z3's printer and the engine's induction are trusted. No proof
  object is checked.
- **Bounded witnesses.** Comparisons of objects and changes are decided by
  bounded model checking; their witnesses carry extreme values and are not
  shrunk, unlike conflicts and code failures.
- **The call that shows a conflict is not canonical.** The candidate calls
  come from the solver's models, which depend on what the process solved
  before, and the shrink is greedy: it stops at a call that no single step
  makes simpler. The invoice conflict (§7) was shown on items of 3 and 7
  cents in the study, on 1 × 7 and 1 × 3 cents in a new process, and on
  three items after the other tests had run in the same process; the
  requirements in conflict were the same each time. A study and a review
  each run in a process of their own, where a rerun shows the same call.
- **A look-back inside `once`** delays the evaluation of the whole formula
  that contains it, so `!once(prev(true, 3))` ("fewer than three earlier
  calls") is never true; a counter ghost states it instead.
- **Two semantics.** The integer encoding is a second implementation of
  FCP-PL, checked against the compiled monitors on every witness and on 400
  calls per agreement (and, for a proof, on every cycle of the scope), not
  proved equal to them. The same holds for the translation of code into z3
  terms (§2.6): it agrees with the code everywhere the code was run, and is
  not proved equal to Python.
- **The limits of a check are watched, not enforced by the system.** The
  review adds up the resident memory of the checking process and its
  tools four times a second (§10). Memory that processes share is counted
  once per process, and memory taken and given back between two looks is
  not seen. A hard limit is a control group around the review, and the
  default memory limit stays under one that is there. A step that is
  stopped leaves nothing of what it had found: a search stopped after
  its second conflict reports none, and the review certifies nothing. A
  step that is run again one task at a time costs its time twice.
- **The replay of a shown call reads what a line carries.** It covers
  the calls on which two readings differ, for a function of plain values
  (§10). The calls of objects, records, changes and code with effects,
  and the calls under a conflict or an open choice, are not read back
  from their lines. The replay runs the monitors that the comparison was
  made on, so it checks the search, the integer encoding and the
  printing of a call; a fault in the compiler from FCP-PL to monitors,
  or in the simulator, is one it shares.
- **The sandbox** is a separate process with time and memory limits, not a
  security boundary. Effects are recorded through an interface the code
  receives, names it calls, and the objects those return (files, sockets).
  The contents of files are not modelled: reads return the script's
  answers, and only the methods the design declares exist on a stand-in
  object; a method the code calls beyond them raises `AttributeError`.

## 15. Reproduce

```bash
.venv/bin/python corpus/code_checkout/build.py     # planted bugs from impl/ref.py
.venv/bin/python experiments/code_demo.py          # sections 2.1-2.5, results/code_checkout.json (about 7 minutes)
.venv/bin/python -m pytest tests/test_code.py
.venv/bin/python experiments/code_demo.py code_mask    # section 3, results/code_mask.json
.venv/bin/python experiments/prove_demo.py code_mask   # section 3.5, results/prove_code_mask.json (run alone)
.venv/bin/python -m pytest tests/test_sweep.py
.venv/bin/python experiments/prove_demo.py code_limit  # section 4.5, results/prove_code_limit.json (run alone, about 100 minutes)
.venv/bin/python -m pytest tests/test_keyed.py
.venv/bin/python experiments/effects_demo.py code_order      # section 6.4, results/code_order.json (run alone, about 4 minutes)
.venv/bin/python experiments/compare_env.py code_order       # section 6.4, results/code_order_env.json
.venv/bin/python experiments/prove_demo.py code_order        # section 6.4, results/prove_code_order.json (about 1 minute)
.venv/bin/python experiments/code_demo.py code_loyal         # section 8.3, results/code_loyal.json (run alone, about 32 minutes)
.venv/bin/python experiments/own_tests_mutants.py code_loyal # section 8.3, results/code_loyal_own_tests.json
.venv/bin/python experiments/variant_demo.py plan            # section 8.4: the ten tasks, their flagged phrases, the readers each gets
.venv/bin/python experiments/variant_demo.py agents --jobs 3 # the 20 new readers, confined (114 agent minutes through the Claude Code CLI)
.venv/bin/python experiments/variant_demo.py compare card    # each new reader of a task with the two stored ones (run alone, inside a memory cap; then change,
                                                             # checkout, invoice, limit, loyal, mask, order, pay, save: loyal 34 minutes, the others under 6,
                                                             # and mask about 5 hours, its second reader with FCP_BIT_JOBS=2 under a cap of 16 GB)
.venv/bin/python experiments/compare_env.py code_pay         # the reference against each stored reading on the runs that reading's assumptions admit
                                                             # (results/code_pay_env.json; also code_save)
.venv/bin/python experiments/variant_demo.py under pay       # the pairs in which the new reader assumes more, on the runs that meet its assumptions (also order, save)
.venv/bin/python experiments/variant_demo.py summary         # results/code_variants.json: the numbers of section 8.4
.venv/bin/pip install cvc5                                   # section 2.7: the second solver
.venv/bin/python experiments/confirm_demo.py code_card --workers 8  # section 2.7, results/confirm_code_card.json (run alone, about an hour;
                                                             # code_limit about 100 minutes, code_mask about an hour, the other five under 20 minutes)
.venv/bin/python -m pytest tests/test_confirm.py
.venv/bin/python -m fcp.confirm --tlimit 60000 FILE.smt2     # cvc5's answer on one formula (confirm_demo.py --keep stores them all in corpus/<corpus>/.fcp/confirm/)
.venv/bin/python experiments/alone_demo.py run               # section 12: 90 replies of the model alone, through the Claude Code CLI without tools;
                                                             # then `judge` and `summary`, results/alone.json
.venv/bin/python -m pytest tests/test_review.py              # section 9: what an agent can touch
.venv/bin/python experiments/comm_fetch.py                   # section 13: the benchmark file, at a pinned commit
.venv/bin/python experiments/comm_demo.py prepare            # screen, draw 20 problems, one work directory per request (80)
.venv/bin/python experiments/comm_demo.py agents --jobs 3    # the five agents of each request, confined (about 17 agent hours through the Claude Code CLI)
.venv/bin/python experiments/comm_demo.py check --jobs 2     # each check inside 8 GB and 45 minutes (run alone; 12.8 hours of checks in the pilot, summed over requests and repeats)
.venv/bin/python experiments/comm_demo.py baseline           # the model alone under three instructions; then `judge`, `audit`, `collect`
.venv/bin/python experiments/comm_demo.py summary            # results/comm.json
.venv/bin/python experiments/comm_replay.py                  # every call a review shows under a question about two readings, run again on the monitors (comm/replay.json; about 5 minutes)
.venv/bin/python experiments/comm_replay.py --gb 8 --seconds 900 7b95c329cc30 2ddb62206a79   # the two HumanEval/80 reviews, which need more than 3 GB (6.6 GB at the peak, about 2.5 minutes each)
.venv/bin/python experiments/comm_replay.py --cases 65536 --force 8d539fbca98d               # the HumanEval/49 original: one reading has 65,536 combinations of free values
.venv/bin/python experiments/comm_again.py --jobs 2          # section 13.5: the 8 requests without a review, checked a second time (results/comm_again.json; 4.7 hours of checks, run alone)
.venv/bin/python -m pytest tests/test_limits.py              # sections 10 and 13: wide constants, chains of definitions, rules for every value, outcome codes
.venv/bin/python -m pytest tests/test_partial.py             # sections 9 and 10: a review that is written whatever a step of its check does
.venv/bin/python -m pytest tests/test_replay.py              # sections 9 and 10: a call on which two readings differ is run again before it is shown
```
