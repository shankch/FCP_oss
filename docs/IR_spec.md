# FCP Intermediate Representation, version 0.1

The Formal Context Protocol (FCP) IR is the machine-checkable contract between
a natural-language hardware specification and the RTL that claims to
implement it. It is written in YAML and validated against the JSON Schema in
[fcp/schema/fcp-ir.schema.json](../fcp/schema/fcp-ir.schema.json).

A **design bundle** is a directory:

| File | Contents | Typical author |
|---|---|---|
| `spec.md` (any name) | the natural-language specification | spec owner |
| `design.yaml` | interface, parameters, environment, RTL variants, source documents | engineer |
| `requirements.yaml` | atomic requirements, each pinned to a verbatim source quote | decomposition agent, reviewed |
| `formal/<set>.yaml` | one *formalization set*: properties, assumptions, scenarios, don't-cares | formalization agent(s), independently |

Several formalization sets of the same requirements can coexist. FCP compares
them semantically, and disagreement is treated as evidence of either ambiguity
or error.

## 1. design.yaml

```yaml
fcp: "0.1"
design: sync_fifo
docs:
  - {id: SPEC, path: spec.md}
interface:
  clock: clk
  reset: {name: rst_n, active_low: true, synchronous: true}
  params: {DEPTH: 5, WIDTH: 8}          # values used for verification
  signals:
    - {name: push_data, dir: in,  width: WIDTH}
    - {name: count,     dir: out, width: "clog2(DEPTH+1)"}
environment:
  initial_reset: true                    # reset asserted in cycle 0 (default)
  reset_anytime: true                    # reset may be re-asserted later (default)
rtl:
  ref: {top: sync_fifo, files: [rtl/sync_fifo.v], params: {DEPTH: DEPTH, WIDTH: WIDTH}}
```

Widths and parameter values are constant expressions over parameters:
`+ - * << >>`, comparisons, `clog2(x)`, `min`, `max`, `pow2`.

A signal with a `length` is a bounded **sequence** (a string or a list) of
at most `length` slots of `width` bits each:

```yaml
    - {name: number, dir: in, width: 8, length: 32}   # a string of at most 32 characters (codes 0-255)
```

FCP-PL sees it as one value (section 4.3). It is carried by two ports: the
packed slots `number` (slot k in bits [8k+7 : 8k], zero beyond the length)
and the length `number__len`. Monitors read a sequence in canonical form, so
whatever a port carries beyond the length is ignored.

Sequence signals with the same `group` always have the same length: the
fields of a list of records, one signal per field (one direction, one
length). Item k of the list is `price[k]`, `qty[k]`, ... and every analysis
keeps their lengths equal:

```yaml
    - {name: price, dir: in, width: 8, length: 4, group: items}
    - {name: qty, dir: in, width: 3, length: 4, group: items}
```

An optional `frame` lists properties that every behaviour satisfies *by
construction of the interface encoding*, not because of any requirement. The
text adapter ([FCP_fsm.md](FCP_fsm.md)) uses it to say how a text response
is framed as a trace:

```yaml
frame:
  - {id: F-EOS, req: R-FR-1, expr: 'prev(eos) -> eos'}          # end of response is absorbing
  - {id: F-NUL, req: R-FR-2, expr: 'eos -> !(subject || cta)'}   # no labels after the end
  - {id: F-LEN, req: R-FR-3, pattern: bounded_wait, args: {cond: '!eos', max: 14}}
```

Frame items are added to every formalization set. Spec-only analyses assume
them, so free outputs range over well-formed behaviours only. Verification
checks them on every RTL variant like any property. Each item cites a
requirement of the document that defines the encoding.

An optional `cutpoint` marks inputs that are the output of a black-box
component outside the RTL. For an agent ([FCP_agent.md](FCP_agent.md)), the
component is the model: its proposed tool call is a free input of the
scaffold, so every proof holds for every possible model output. `passes`
gives, for each output, the value it takes when the RTL passes the proposal
through unchanged. `fcp.agent` uses it to restate a requirement as a contract
on the component:

```yaml
cutpoint:
  component: the model (LLM) of the agent
  inputs: [p_act, p_ord, p_amt, p_more]
  actions: [say, verify, lookup, confirm, refund, handoff, close]   # for reports
  decode: {p_act: [none, say, verify, lookup, confirm, refund, handoff, close]}
  show: {amt: [confirm, refund], total: [lookup]}   # for reports: when a signal means something
  passes:
    refund: 'p_act == 5 && !done'
    amt: "(p_act == 4 || p_act == 5) && !done ? p_amt : 9'd0"
```

An optional `function` declares that the design is a software function, not
RTL ([FCP_code.md](FCP_code.md)). Each cycle is one call: the arguments drive
input signals, the returned value (or one signal per tuple element) drives
output signals, and an outcome signal says how the call ended: 0 it returned
values that fit their signals, 1 to n the listed exceptions, n + 1 any other
exception or no answer, n + 2 anything else. `fcp.software` runs the function
on a scope of calls and checks the recorded trace with the compiled monitors.
`scope` sets, per argument, a dense range, extra values and a number of random
values; the constants of the readings, the documents and the code are always
added with their neighbours. A string argument (`type: str`) or list argument
(`type: list`) drives a sequence signal; its scope is drawn from the readings
themselves (every comparison in any formula at -1, 0 and +1, every condition
true and false, every length the readings name, each inside every rule's
trigger, solved by z3), followed by every call one edit away, all tiny calls
and random ones over an alphabet: the characters of the readings and the
code, one of each character class, and `alphabet` (for lists, `elements`).
Last come the computed boundaries: every comparison and condition that
mentions an output, solved with the outputs obeying every property of one
reading and under the conditions that make it matter (b of `a && b` where a
holds), so that a rule on a computed value, such as a subtotal of at least
$10, is met by inputs that produce exactly that value.
A design with a `function` section needs no `rtl` section:

```yaml
function:
  name: checkout
  args:
    - {name: subtotal, signal: subtotal, type: int}
    - {name: member, signal: member, type: bool}
  returns: {signals: [price, ship]}           # a tuple; {signal: x} for one value
  outcome: {signal: outcome, raises: [ValueError]}
  scope:
    subtotal: {dense: [0, 2000], random: 400}
```

```yaml
function:
  name: mask_card
  args:
    - {name: number, signal: number, type: str}     # number is a sequence signal (length 32)
  returns: {signal: masked, type: str}
  outcome: {signal: outcome, raises: [ValueError]}
  scope:
    number: {alphabet: '0123456789 -', random: 3000, values: ['4111 1111 1111 1111']}
```

An argument of `type: record` is a dict with one signal per field;
`type: records` is a list of them, one sequence signal per field, the
fields' signals one interface group. The returned value can be a record or a
list of records in the same way. A record is a dict, and a returned dict
must have exactly these keys; a record with its own `class: Item` is an
object of that class of the implementation's module, built with the fields
as keyword arguments (a returned one is read through its attributes). A
returned value of another form is outcome n + 2:

```yaml
function:
  name: order_total
  args:
    - name: items
      type: records                       # a list of dicts; price, qty, gift: one interface group
      fields:
        - {key: price, signal: price}
        - {key: qty, signal: qty}
        - {key: gift, signal: gift, type: bool}
    - {name: member, signal: member, type: bool}
  returns:
    type: record                          # a dict with exactly these keys
    fields:
      - {key: subtotal, signal: subtotal}
      - {key: total, signal: total}
  outcome: {signal: outcome, raises: [ValueError]}
```

With `class`, the function is a method of an object, which keeps state
between calls: a reset creates the object (`init` are the constructor
arguments) and every later cycle calls the method on it, in order, until the
next reset. `prev`, `once`, `hist` and `since` then range over the calls on
one object, and ghost state can model what the object should remember.
`module` names the file the implementation is in. The scope is a set of
call sequences, each on a new object: every sequence of one or two calls over
a few values, random walks (`sequences` of `length` calls, arguments from
`values`, and an argument with `steps`, such as a clock, advanced by one of
its steps at every call), sequences drawn from the readings by bounded model
checking (each condition the readings name, reached after calls that meet
every rule), and every sequence one edit from those:

```yaml
function:
  name: allow
  class: RateLimiter
  module: rate_limiter
  args:
    - {name: user, signal: user, type: int}
    - {name: now, signal: now, type: int}
  returns: {signal: allowed, type: bool}
  outcome: {signal: outcome, raises: [ValueError]}
  scope:
    sequences: 4000
    length: [1, 14]
    user: {values: [0, 1, 2, 1000, 1001]}
    now: {steps: [0, 1, 2, 3, 8, 9, 10, 11, 12, 50, 57, 58, 59, 60, 61, 62]}
```

With `methods` instead of `name`, `args` and `returns`, the object has
several methods. Each call is a call of the method whose `op` the `op` input
signal carries; methods may share an argument signal, and the arguments the
called method does not take are 0 (every engine keeps them so). Each method
has its own results; the other methods' result signals are 0, which a frame
rule should state. The calls are written as the methods: `add(2, 5)`,
`total()`:

```yaml
function:
  class: Cart
  module: cart
  op: {signal: op}                      # 1 add, 2 remove, 3 total
  methods:
    - {name: add, op: 1, args: [{name: sku, signal: sku}, {name: qty, signal: qty}]}
    - {name: remove, op: 2, args: [{name: sku, signal: sku}]}
    - {name: total, op: 3, returns: {signal: total, type: int}}
  outcome: {signal: outcome, raises: [ValueError, KeyError]}   # codes 0 to 4: 3 bits
```

With `baseline`, the design is a **change** to existing code: the code before
the change is run on the same calls (with the arguments it takes), and its
returned values and outcome drive extra *input* signals. A requirement can
then relate the new answer to the old one, for instance that nothing changes
for some customers, and a regression shows as a call on which they differ
where no requirement allows it:

```yaml
  baseline:
    path: impl/old.py                   # the code before the change
    args: [subtotal, coupon, member]    # the arguments it takes
    returns: [old_price, old_ship]      # input signals for its returned values
    outcome: old_outcome                # input signal for how its call ended
```

In the spec-only analyses the old answer is a free input, so readings are
compared for any old code; the conflict search and the code side use the
answers of the actual old code.

An implementation may be a package (a directory) instead of one file: the
function is then looked up in the module `module` names, a dotted name such
as `shop.cart`, with the directory on the import path, so its modules import
one another as a package does. The scope takes the constants and characters
of every module except tests, and mutants are drawn from every module.

With `interface`, the function acts through an object it receives, such as
a payment service (`fcp.effects`). The adapter passes a recording stand-in:
a reset starts a run, every call the function makes on it is one cycle
(`phase` 0, `op` the method, its arguments on the listed output signals, and
the stand-in's answer on the `answer` input, taken from a script), and the
return is the last cycle (`phase` 1, the result and the outcome), which
stays until the next reset. The scope is a set of (arguments, script of
answers) pairs; a run longer than `max_calls` calls ends as "did not finish".
Only methods with `answers` take an entry of the script:

```yaml
function:
  name: charge_order
  args:
    - {name: order_id, signal: order_id, type: int}
    - {name: amount, signal: amount, type: int}
  interface:
    position: 0                           # the parameter that receives it
    methods:
      - {name: charge, op: 1, args: [c_order, c_amount], answers: [ok, declined, error]}
      - {name: sleep, op: 2, args: [s_seconds]}
    signals: {phase: phase, op: op, answer: answer}
    max_calls: 8
  returns: {signal: result, type: bool}
  outcome: {signal: outcome, raises: [ValueError]}
  scope:
    script: {length: 6, random: 300}      # every script of up to 6 answers, and 300 longer ones
```

Code that does not receive the interface, but imports a client library or
calls `time.sleep` itself, declares `position: null`, and each method names
the `patch` the code calls (`module.name`). The sandbox installs the
recording stand-in there before the code is imported, so `from payments
import charge` and `payments.charge(...)` both reach it; a module the
sandbox lacks is created empty. An answer the library delivers as an
exception is listed under `raises`:

```yaml
  interface:
    position: null                        # not passed: the code calls the names below
    methods:
      - {name: charge, op: 1, args: [c_order, c_amount], answers: [ok, declined, error],
         patch: payments.charge, raises: {error: payments.ServiceError}}
      - {name: sleep, op: 2, args: [s_seconds], patch: time.sleep}
```

A method with `handle: true` returns an object (a file from `open`, a socket
from `socket.create_connection`) unless its answer raises; the methods
declared `via` it are called on that object, which a `with` block closes,
and a call on a closed object raises `ValueError`, as on a real file. The
optional `handle` signal carries which object a call made or acted on (1 the
first of the run). An argument is a signal name, or an object that says how
a value that is not an integer becomes one: `enum` (1, 2, ... by position,
0 anything else; tuples compare as lists), `parse: int` (text as the number
its digits spell), `open_mode` (1 read, 2 write, 3 append, 4 create) or
`handle` (an object, or its `fileno()`, as its number); `name` binds keyword
arguments and `default` fills one the call leaves out. `patch` may list
several names, and a name may be a class attribute (`pathlib.Path.exists`).
`files` gives the run its own view of the disk: what `exists` at the start,
changed by methods with `fs` (`open` creates its file in a writing mode,
`remove` deletes, `move` renames), and asked through the `query` names.
Removing or moving a file that is not there raises `FileNotFoundError`
without taking an answer from the script ([corpus/code_save](../corpus/code_save/design.yaml)):

```yaml
  interface:
    position: null
    methods:
      - name: open
        op: 1
        patch: [builtins.open, io.open]
        handle: true                      # returns a file object: f1, f2, ...
        var: f
        fs: open
        args:
          - {name: file, signal: o_path, enum: [balance.txt, balance.txt.tmp]}
          - {name: mode, signal: o_mode, open_mode: true, default: r}
      - {name: write, op: 2, via: open, args: [{name: s, signal: w_value, parse: int}]}
      - {name: close, op: 4, via: open}
      - {name: replace, op: 6, patch: os.replace, fs: move, answers: [ok, fail], raises: {fail: OSError},
         args: [{name: src, signal: r_src, enum: [balance.txt, balance.txt.tmp]},
                {name: dst, signal: r_dst, enum: [balance.txt, balance.txt.tmp]}]}
    signals: {phase: phase, op: op, answer: answer, handle: of}
    files: {exists: [balance.txt], query: [os.path.exists, pathlib.Path.exists]}
```

The contents of a file are not modelled: what the code reads is what the
script answers, and only the methods declared on an object exist on it.

## 2. requirements.yaml

```yaml
requirements:
  - id: R-WR-2
    doc: SPEC
    lines: [42, 43]            # computed by `fcp anchor`, never typed by hand
    quote: "A push while the FIFO is full is ignored: the stored words and count are unchanged by it."
    text: "A push while full has no effect on the stored words or on count."
    kind: guarantee            # guarantee | assumption | dont_care | scenario | definition | non_functional
    depends: [R-ST-4]
    ambiguity:
      - {phrase: "...", readings: ["reading 1", "reading 2"]}
```

The quote must occur verbatim (ignoring whitespace) in the cited lines, which
is checked on load. This makes provenance tamper-evident: an agent cannot cite
text that does not exist.

## 3. Formalization sets

```yaml
fcp: "0.1"
set: agent_a
origin: {kind: agent, role: formalizer, model: "...", run: "..."}
defs:                       # named boolean/numeric expressions (macros)
  wr: "push && !is_full"
ghosts:                     # specification-model state (a reference model)
  - {name: occ, range: [0, DEPTH], init: 0, next: "occ + wr - rd"}
rigids:                     # universally quantified constants
  - {name: i, range: [0, 3]}
assumptions:                # environment obligations (must be justified by a requirement)
  - {id: A-1, req: R-ENV-1, pattern: hold_until, args: {trigger: "req[i] && !gnt[i]", hold: "req[i]", release: "gnt[i]"}}
properties:                 # guarantees the design must satisfy
  - {id: P-1, req: R-ST-1, expr: "full == (count == DEPTH)"}
scenarios:                  # behaviours that must be possible (reachability)
  - {id: S-1, req: R-ST-1, cover: "full"}
dont_cares:                 # outputs intentionally left free
  - {id: D-1, req: R-RD-4, signal: pop_data, when: "occ == 0"}
unformalized:               # every requirement not formalized needs a reason
  - {req: R-PAR-1, reason: "..."}
  - {req: R-USE-2, reason: "...", covered_by: [P-3, P-4]}
decisions:                  # the reading taken for every phrase requirements.yaml flags as ambiguous
  - {req: R-CAP-1, phrase: "a load that would take it over", reading: 2}
```

Every formal item carries `req`, the requirement it formalizes. That link is
the spine of the evidence chain. `decisions` names, for each flagged phrase,
the number of the reading taken in the requirement's `ambiguity` list (from
1); readers that took the same reading are then probed with a variant
reading that takes another (`fcp review`).

A property over `rigids` holds for every combination of their values. A
proof takes the combinations symbolically, whatever their number. A replay
(code run on calls, a recorded run, a counterexample of a comparison) runs
the monitor once per combination, up to 4,096 of them. Code is therefore
not checked against a set whose rigid ranges multiply to more, a comparison
with it cannot confirm a difference it finds, and `fcp lint` warns. Ghost
state can often state a rule for every value of a quantity without a rigid
variable over that quantity.

## 4. FCP-PL expressions

An expression is evaluated **at every clock cycle**. It may mention interface
signals, parameters, `defs`, `ghosts`, `rigids` and `rst_active` (true while
reset is asserted).

### 4.1 Types and operators

| Kind | Values | Produced by |
|---|---|---|
| bool | 1-bit truth value | 1-bit signals, comparisons, logical operators |
| bits(w) | unsigned bit-vector | multi-bit signals, slices, `& \| ^ ~` |
| int | mathematical integer with a static range | literals, parameters, `+ - * %`, ghosts with `range` |
| seq | a string or list: a length and its slots (section 4.3) | sequence signals, string and list literals |

* Arithmetic and comparison are **exact integer** operations. `count - 1` is
  -1 when count is 0. There is no wrap-around and no overflow.
* `! && || -> <->` require **boolean** operands. `x && y` with multi-bit x is
  a type error; write `x != 0`.
* Booleans may be used in arithmetic as 0/1 (`occ + wr - rd`).
* `a % k` takes a constant positive divisor k and is floor modulo, as in
  Python: the result is in 0 .. k-1 even when a is negative.
* Bit-level: `~ & | ^`, `x[i]` (constant or variable index), `x[h:l]`
  (constant slice), `<< >>` (constant shift; `1 << i` is allowed).
* `c ? a : b`, `min(a,b)`, `max(a,b)`, `onehot(x)`, `onehot0(x)`,
  `countones(x)`, `any(x)` (x != 0), `all(x)`, `zext(x, w)`.
* Literals: `5`, `8'hFF`, `4'b1010`, `true`, `false`.
* Precedence, low to high: `-> <->`, `?:`, `||`, `&&`, `|`, `^`, `&`,
  `== !=`, `< <= > >=`, `<< >>`, `+ -`, `*`, unary `! ~ -`, `[ ]`.

### 4.2 Temporal operators (past-time only)

| Operator | Meaning at cycle t |
|---|---|
| `prev(e)`, `prev(e, n)` | value of e at cycle t-1 (t-n) |
| `rose(b)`, `fell(b)` | `b && !prev(b)`, `!b && prev(b)` |
| `stable(e)`, `changed(e)` | `e == prev(e)`, `e != prev(e)` |
| `once(b)` | b held at some cycle since the end of the last reset |
| `hist(b)` | b held at every cycle since the end of the last reset |
| `since(a, b)` | b held at some cycle t' <= t and a held at every cycle in (t', t] |

There are no future operators. Future obligations are expressed with the
patterns below, which compile them to exact past-time monitors. A property
that looks back n cycles is not evaluated in the first n cycles after a
reset. The same rule applies inside `once`, `hist` and `since`: an operand
that looks back n cycles is skipped in the first n cycles after a reset. It
counts as false for `once` and for the second argument of `since`, and as true
for `hist` and for the first argument of `since`. A history operator therefore
never accumulates a value read from a reset cycle. Likewise, a trigger
that looks back n cycles cannot start an obligation in the first n cycles
after a reset; this matters for patterns that keep an obligation alive
across cycles (`next`, `within`, `hold_until`, `bounded_wait`, `inorder`).

### 4.3 Strings and lists

A sequence value has a length and slots, zero at and beyond the length.

| Expression | Meaning |
|---|---|
| `len(s)` | the length of s |
| `s[i]` | the code (string) or value (list) of slot i, counting from 0; 0 when i is outside s |
| `x in s` | some slot below the length of s equals x |
| `s == t`, `s != t` | same length and same slots |
| `"ab"`, `'ab'` | a string literal (escapes `\n \t \\ \" \'` and `\xHH`); a one-character literal where a number is expected is its code, so `s[i] == "*"` and `s[i] - "0"` work |
| `[1, 2, 3]` | a list literal of non-negative constants |
| `all(i < n: b)`, `any(i < n: b)` | b holds for every (some) i in 0 .. n-1 |
| `count(i < n: b)` | how many i in 0 .. n-1 satisfy b |
| `sum(i < n: e)` | the sum of e over i in 0 .. n-1 |
| `isdigit(c)`, `isalpha(c)`, `isalnum(c)`, `islower(c)`, `isupper(c)`, `isspace(c)` | ASCII character classes: `isdigit` holds for `0` to `9` only |
| `lower(c)`, `upper(c)` | ASCII case mapping |

The bound n of a quantifier is any integer expression with a static maximum
of at most 256, usually `len(s)`. The quantified variable is local to the
body and may be used in arithmetic and as an index: `all(i < len(s) - 1:
s[i] <= s[i + 1])` says s is sorted. Quantifiers nest, and `prev`, `stable`
and `changed` apply to whole sequences. Examples:

```yaml
nd:      'count(i < len(number): isdigit(number[i]))'                 # how many digits
same:    'len(masked) == len(number)'
kept:    'all(i < len(number): number[i] == " " -> masked[i] == " ")'
perm:    'len(out) == len(xs) && all(i < len(xs): count(j < len(xs): xs[j] == xs[i]) == count(j < len(out): out[j] == xs[i]))'
```

A quantifier is expanded at compile time into one term per value of its
variable, so a sequence property is still a combinational function of the
cycle and every analysis applies unchanged.

### 4.4 Reset

Properties are evaluated only in cycles where reset is not asserted
(`mode: operational`, the default). Monitor state, ghosts and history
operators are cleared by reset. `mode: always` evaluates in every cycle. It is
used by `after_reset`.

## 5. Patterns

A property, assumption or scenario is either `expr: <bool expression>`
(meaning: holds at every operational cycle) or a pattern with arguments.
Every pattern has a precise semantics, a canonical English rendering (produced
by `fcp explain`), and a *trigger* used to detect vacuity.

| Pattern | Arguments | Meaning |
|---|---|---|
| `invariant` | cond | cond holds at every operational cycle |
| `implies` | trigger, cond | whenever trigger holds, cond holds in the same cycle |
| `next` | trigger, cond | whenever trigger holds at t, cond holds at t+1 (inside cond, `prev(x)` is x at the trigger cycle) |
| `within` | trigger, cond, min, max | whenever trigger holds at t, cond holds at some cycle in [t+min, t+max] |
| `hold_until` | trigger, hold, release | if trigger holds at t, hold holds at every cycle after t up to and including the first cycle where release holds (weak: release may never come) |
| `bounded_wait` | cond, max | cond never holds for more than max consecutive cycles |
| `after_reset` | cond | in every cycle that follows a reset cycle, cond holds (reset values) |
| `inorder` | in_fire, in_data, out_fire, out_data, capacity, [latency], [peek] | every item accepted (in_fire, in_data) is delivered exactly once, unmodified, in order: at each out_fire, out_data (latency 0: same cycle; 1: next cycle) equals the oldest undelivered item. No delivery without an item in flight; at most capacity items in flight. With `peek: c`, whenever c holds and an item is in flight, out_data shows the oldest one |

Obligations are cancelled by reset.

## 6. Semantics of verification

For a formalization set with assumptions A1..Am and a property P, FCP checks

    M_RTL |= (A1 && ... && Am) => P

in the assume-guarantee sense. At every cycle t, if every assumption held at
all cycles <= t (and reset was asserted in cycle 0), then P is not violated at
t. Rigid variables are universally quantified. Proofs are unbounded (IC3/PDR),
cross-checked by BMC, and every counterexample is replayed in an independent
simulator.

What a proof does **not** establish, and how FCP covers each gap:

| Risk | FCP check |
|---|---|
| property never triggers, or constrains nothing | trigger witness on the RTL, unreachability proof, tautology check on the spec model |
| an "environment" assumption actually constrains the design | receptiveness: no reachable state may leave the environment without a legal non-reset input |
| the formalization means something other than the prose | independent formalizations compared by semantic implication; disagreements yield a distinguishing trace for a human |
| a disagreement shows only on behaviours that break other requirements | contextual comparison: the readings are compared again over behaviours that meet every *other* requirement under both readings, and witnesses are minimized to the simplest such behaviour. Suppose a disagreement vanishes in context and every other requirement is proved on the RTL. Then the RTL's behaviours lie inside the context, so proving one reading proves the other (agreement, not intent: see [FCP_fsm.md](FCP_fsm.md) §4) |
| requirements contradict each other | consistency of every trigger situation, every pair of situations and every scenario, with minimal conflicting sets |
| the environment can force a violation that no single situation shows | forcing stimuli: an input sequence on which no output sequence meets the requirements (exists-forall, counterexample-guided), with a minimal conflicting set per stimulus; bounded, and sound for implementations that know the inputs in advance |
| a requirement holds only because a black-box component (the model of an agent) behaves | trust classification: with the cut-point inputs free a requirement is *enforced*; if it fails then but holds once the component keeps that requirement's contract, it is *delegated*; if it fails even then, the RTL *breaks* it |
| a recorded behaviour (an agent run, a simulation dump) breaks a requirement or a contract | runtime verification: the compiled monitor is simulated on the trace, every rigid value is replayed |
| a conflict needs particular values that neither situation candidates nor the forcing search reach (wide arithmetic inputs) | boundary conflicts: pairs of calls built from the constants of the readings and the prompt, each checked for any conforming output pair, with a minimal conflicting set |
| the spec leaves outputs undetermined | determinacy via self-composition: two conforming behaviours with identical history that differ; for a function, also the simplest call on which two values are allowed |
| a function (code, not RTL) breaks a requirement | the code is run on a scope of calls (dense ranges, every constant of the readings, the prompt and the code with its neighbours, random values) in sweeps that make one-step neighbours adjacent; the monitors check the recorded trace; every failure is replayed in a fresh process. Exhaustive within the scope, nothing beyond it |
| implementations of the same prompt make different choices | code splits: calls on which implementations answer differently, grouped by how they split the implementations, with the simplest call of each group |
| properties are too weak to notice RTL changes | mutation analysis: observable mutants that no property kills (for code: one-operator changes of the source, run on the scope) |

## 7. Writing good formalizations (for agents and people)

1. Formalize what the **text** says, not what an implementation would do. Do
   not invent behaviour the text does not state. If the text is ambiguous,
   say so in `note` and pick the most literal reading.
2. Prefer a **specification model** (ghosts driven by inputs) over relations
   between outputs. For example, define the occupancy from push/pop and
   check every output against it.
3. Use assumptions only for obligations the text places on the
   **environment** (inputs). Every assumption needs `req:`. An assumption
   about outputs is almost always a mistake.
4. A requirement that cannot be expressed goes under `unformalized` with a
   reason, or `covered_by` the items that realize it. Never drop one
   silently.
5. Express intentionally unconstrained outputs as `dont_cares`.
