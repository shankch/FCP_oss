# A Lean reference for FCP-PL, and the theory machine-checked

Every verdict of FCP rests on two things that were, until now, checked only
by tests and by reading: the compiler that turns an FCP-PL item into a
Verilog monitor ([fcp/monitor.py](../fcp/monitor.py)), and the propositions
of the paper that say what a verdict means. This document describes a second,
independent definition of the language, written in Lean 4, and what it is
used for:

1. **A reference semantics.** What every expression, pattern and item means
   on a trace, as closed forms over the past of the trace, with no
   registers ([lean/FCP/Semantics.lean](../lean/FCP/Semantics.lean),
   [lean/FCP/Items.lean](../lean/FCP/Items.lean)).
2. **An oracle.** The reference is executable. On random traces it is
   compared, output by output and cycle by cycle, with a simulation of the
   compiled monitor of every reading in the corpus.
3. **Theorems.** The register machines the compiler emits compute the
   reference; every item reads the trace only up to its cycle; and
   Propositions 1–4 of the paper, with the corollary on pinned instances,
   hold. Lean checks every proof.

Lean is used where it is the better tool: for statements about every trace
and every reading, which no solver query states. The verdicts themselves
still come from the hardware engines and z3.

## 1. What was built

| File | Lines | Contents |
|---|---|---|
| [lean/FCP/Syntax.lean](../lean/FCP/Syntax.lean) | 135 | Expressions, patterns, ghosts, items, readings |
| [lean/FCP/Semantics.lean](../lean/FCP/Semantics.lean) | 177 | Values, operators, `once`, `hist`, `since`, `prev`, `eval` |
| [lean/FCP/Items.lean](../lean/FCP/Items.lean) | 250 | Patterns, gates, ghosts, the verdict of an item, rigid names |
| [lean/FCP/SExpr.lean](../lean/FCP/SExpr.lean), [lean/Main.lean](../lean/Main.lean) | 305 | The oracle: reads a reading and traces, prints every verdict |
| [lean/FCP/Monitor.lean](../lean/FCP/Monitor.lean) | 596 | The registers of the monitor, and 38 theorems that they compute the reference |
| [lean/FCP/Causal.lean](../lean/FCP/Causal.lean) | 268 | 28 theorems: every item is causal |
| [lean/FCP/Contracts.lean](../lean/FCP/Contracts.lean) | 329 | 18 theorems: Definition 1, conflicts, trust classes, the horizon, proofs |
| [fcp/leanref.py](../fcp/leanref.py) | 698 | Export of a reading to Lean, random traces, simulation, comparison |
| [experiments/lean_oracle.py](../experiments/lean_oracle.py) | 220 | The study below |
| [tests/test_lean.py](../tests/test_lean.py) | 110 | 11 tests, run with the suite when the toolchain is present |

The toolchain is Lean 4.35.0 with no library beyond the core (no Mathlib),
pinned in `lean/lean-toolchain` and unpacked into `.tools/lean`. Nothing
else in FCP depends on it: without the toolchain the Lean tests are skipped.

## 2. The reference semantics

The compiler describes an operator by the register that computes it. The
reference describes it by what it says about the past. For example
(`rst t` says that cycle `t` is a reset):

```lean
/-- No cycle in `[a, b)` is a reset. -/
def quiet (rst : Nat → Bool) (a b : Nat) : Bool :=
  (List.range (b - a)).all fun i => !rst (a + i)

/-- `once(a)`: `a` held at a cycle with no reset between it and now. -/
def onceS (rst : Nat → Bool) (a : Nat → Bool) (t : Nat) : Bool :=
  (List.range (t + 1)).any fun s => a s && quiet rst s t
```

The monitor holds one bit for `once(a)`, cleared by reset and set when `a`
holds. That the bit equals `onceS` at every cycle is a theorem (§5), and a
measurement (§3). The same split is made for every construct: look-back
after a reset (`segGe`), `hist`, `since`, `prev`, the five patterns with an
obligation in the future (`next`, `within`, `hold_until`, `bounded_wait`,
`after_reset`), the gates that silence a verdict in reset and before its
expressions are defined, ghosts with their ranges, and rigid names, for
which an item is checked once per value.

Values are exact integers, as in FCP-PL: a condition is 0 or 1, a
bit-vector its unsigned value, a string or a list a sequence of integers.

## 3. The comparison with the compiled monitors

For a reading, [fcp/leanref.py](../fcp/leanref.py) writes its items as
S-expressions, draws random traces, and asks two parties for every output
of every item at every cycle: the Lean oracle, which evaluates the closed
forms, and Icarus Verilog, which simulates the monitor the compiler emits,
one instance per value of the rigid names. An output is compared at every
cycle until a ghost leaves its declared range, after which the monitor's
ghost register no longer holds the exact value and nothing is compared.

| | |
|---|---|
| Readings | 46: the 44 of the fourteen corpora, and two written for this comparison |
| Items compared | 845 |
| Output streams | 44,520, of which 33,040 take both values |
| Cycles compared | 1,747,852 |
| **Cycles that differ** | **0** |
| Cycles after a ghost left its range (not compared) | 32,948 |
| Items skipped | 41, all of the pattern `inorder` |

The two written readings cover what the corpus does not: every operator,
each pattern with the arguments no corpus item gives it (a window that
opens late, items checked in reset cycles), an active-high reset, a rigid
name with negative values, ghosts that depend on it, a ghost that leaves
its range, and a ghost that depends on a rigid name through another ghost.

`inorder` (a queue of expected values) is the one pattern outside the
reference; its 41 items, in the FIFO, the bridge and the hub, are not
compared.

**The domain.** Every trace above begins with a reset cycle, which is the
standard environment of FCP ("reset is asserted at cycle 0"). The `prev`
registers of the monitor have no reset value, so on a trace that does not
begin with a reset the monitor is undefined until one arrives. This was
measured rather than assumed: on 11,940 streams of traces without the
initial reset, 24,346 outputs of the monitor were undefined (`x`), and of
the 427,450 defined ones none differed from the reference.

## 4. What the comparison found

Before it agreed, the comparison found three defects in the monitor
compiler. None had been seen by the test suite or by the studies, because
no corpus reading exercised them; the two written readings did.

| Defect | Effect | Fix |
|---|---|---|
| A ghost that depends on a rigid name with a negative value was given the instance name `g_acc_k-1` | the monitor was not legal Verilog | the name is `g_acc_km1` ([fcp/monitor.py](../fcp/monitor.py)) |
| The look-back of `prev(a, DEPTH - 1)`, a depth over parameters, was taken as 1 | the item was checked before its expression was defined | the depth is evaluated ([fcp/lang.py](../fcp/lang.py)) |
| A ghost that depends on a rigid name only through another ghost was given one copy for all values | every value of the rigid name shared one register | dependencies are followed through ghosts (`MonitorGen.ghost_deps`) |

No corpus reading has a negative rigid value, a parametric depth, or such
a chain of ghosts: the monitor of each of the 44 corpus readings is the
same text before and after the fixes, so no verdict of the studies changes.

## 5. Is the comparison sensitive?

A comparison that reports no difference is worth what it would have
reported. Two experiments change one side and compare again.

**One change to the monitor.** A sample of single changes to the Verilog of
each reading (an operator, a constant, a negation, a reset), restricted to
lines some compared output reads: of 161,260 possible changes over
the 46 readings, 40 per reading are tried, 1,840 in all, and every one
compiles. The comparison notices **1,436**. Of the other 404, 19 change
only the initial value of a register that the reset in cycle 0 sets, which
no trace can see, and 385 go unnoticed: 273 on a line a verdict reads, 88
on a line only the output of a scenario reads, and 24 on a line read only
through the check that a ghost stays in its range.

The readings fall into two groups. For 43 of them the comparison notices
1,422 of the 1,720 changes tried (83%; from 58% for the gold reading of the
login rate limiter to every change for three readings). What goes
unnoticed there is mostly a boundary the random traces do not land on
(`<` to `<=` is noticed 24 times of 52, a changed constant 403 of 588),
while a dropped negation is noticed 236 times of 242. The three readings
of the card-masking prompt are the exception. Their monitors spell out
every position of a string (about 48,000 possible changes each), they are
compared on 24 traces instead of 60 to stay inside the memory cap, and the
comparison notices only **14 of 120**: a change to the logic of one
position shows only on a trace whose string reaches that position with the
right characters, and random traces rarely do. For these three readings
the agreement of section 3 says little about most of the per-position
logic. The experiment does not separate a change that no trace can show
from one the sampled traces missed, so 385 is an upper bound on what the
comparison would let through, and the comparison remains a test on sampled
traces, not a proof about the compiler.

**One change to the reference.** 23 single changes to a definition in
`lean/` (a look-back met one cycle early, `once` keeping a reset cycle, a
window of `within` that opens one cycle late, a reset that does not set
the ghosts, `%` that truncates, and so on), each rebuilt in a copy. The
comparison notices **23 of 23**. For 18 of them a proof of
`FCP/Monitor.lean` also stops checking; the other five change an operator
on values (`%`, `>>`, `<<`, `isspace`, `upper`), which the theorems take
as given and only the comparison checks.

## 6. The theorems

All proofs are checked by `lake build`; none uses `sorry`, and the only
axioms are the three of Lean's standard logic (`propext`,
`Classical.choice`, `Quot.sound`). There are 84 theorems;
[tests/test_lean.py](../tests/test_lean.py) asks Lean for the axioms of the
30 named below and in `leanref.THEOREMS`.

### 6.1 The registers compute the reference

[lean/FCP/Monitor.lean](../lean/FCP/Monitor.lean) defines each register of
the monitor by its recurrence (what it holds at cycle 0, what it holds at
`t + 1` from what it held at `t`) and proves that it equals the closed form
at every cycle.

| Register of the monitor | Theorem |
|---|---|
| `_seg`, the saturating count of cycles since reset | `segGe_sat` |
| `once`, `hist`, `since` | `eval_once`, `eval_hist`, `eval_since` |
| the delay chain of `prev(a, n)` | `eval_prev` (from cycle `n` on) |
| `next`: the trigger one cycle ago | `nextOpen_eq` |
| `within`: one obligation bit per age | `withinDue_eq` |
| `hold_until`: the open obligation | `holdOpen_eq` |
| `bounded_wait`: the saturating run counter | `waited_eq` |
| `after_reset` | `afterReset_eq` |
| the verdict of every pattern | `Pattern.raw_eq_rawReg` |
| the gates (reset, look-back) | `gate_eq`, `gateTrig_eq` |
| the verdict and the coverage of an item | `Item.ok_eq_okReg`, `Item.cov_eq_covReg` |
| the ghosts, computed in one pass | `ghostRuns_eq` |

### 6.2 Every item is causal

Propositions 1 and 2 are about verdicts that read a trace only up to the
current cycle. [lean/FCP/Causal.lean](../lean/FCP/Causal.lean) proves that
every FCP-PL item is one: if two traces agree up to cycle `t`, every
expression has the same value at `t` (`eval_causal`, by induction on the
expression), the ghosts have the same values (`ghostRun_causal`), and the
item has the same verdict, for every value of its rigid names
(`Item.okAll_causal`, `Item.causal`). So the propositions below apply to
every item a reading can contain.

### 6.3 The propositions of the paper

[lean/FCP/Contracts.lean](../lean/FCP/Contracts.lean) states them over
arbitrary input and output alphabets and arbitrary causal verdicts.

| Paper | Statement | Theorem |
|---|---|---|
| Definition 1 | a system keeps a guarantee on every trace on which the assumptions held so far | `Sat` |
| Proposition 1 | a conflict (an input prefix on which every output breaks a guarantee while the assumptions hold) means no system keeps all the guarantees | `conflict_sound`, `conflict_violates` |
| Corollary | a conflict found among pinned instances of a quantified guarantee is a conflict of the guarantee | `conflict_pinned` |
| Proposition 2 | an enforced rule holds for every model; a delegated rule holds up to the cycle the model first breaks its contract | `enforced_meaning`, `delegated_meaning` |
| Proposition 3 | a trace that separates two readings contains one no longer than the look-back plus one | `horizon`, `horizon_single` |
| Proposition 4 | a proof by unsatisfiable encoding, bounded or by an inductive invariant, is sound when the encoding is exact | `proved_bounded_sound`, `proved_sound`, `invariant_sound` |

Stating Proposition 3 in Lean sharpened it: the bound on the look-back is
needed only for the items the trace breaks, not for the ones it keeps.

## 7. What is not proved

* **The Verilog text.** The recurrences of §6.1 are transcribed by hand
  from the compiler's output; Lean does not read Verilog. The link between
  the two is the comparison of §3 and its sensitivity (§5).
* **`inorder`.** Outside the reference and the theorems.
* **`prev` before its look-back.** `eval_prev` holds from cycle `n` on. That
  the gated verdict does not depend on what the delay chain holds earlier
  is covered by the comparison, not by a theorem.
* **Operators on values.** The theorems are about time: resets, registers,
  obligations. That the monitor's arithmetic and character operators match
  the reference is checked by the comparison alone.
* **Exactness of an encoding.** Proposition 4 assumes that the z3 encoding
  of a function and of its monitors is exact. FCP checks this on the whole
  scope for every proof ([FCP_code.md](FCP_code.md) §4); it is measured,
  not proved.
* **The engines.** Yosys, the model checkers, z3 and Icarus are trusted as
  before.

## 8. Reproduce

```bash
# Lean 4.35.0, unpacked so that .tools/lean/bin/lake exists
curl -L -o lean.tar.zst https://github.com/leanprover/lean4/releases/download/v4.35.0/lean-4.35.0-linux.tar.zst
mkdir -p .tools/lean && tar --zstd -xf lean.tar.zst -C .tools/lean --strip-components=1

(cd lean && PATH=$PWD/../.tools/lean/bin:$PATH lake build)   # checks every proof, builds the oracle
.venv/bin/python -m pytest tests/test_lean.py                # 11 tests, about 15 s
.venv/bin/python experiments/lean_oracle.py                  # proofs, agree, cold, monitor, lean
```

Results: [experiments/results/lean_oracle.json](../experiments/results/lean_oracle.json).
