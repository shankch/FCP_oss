# The Formal Context Protocol: closing the false-assurance loop for AI-generated RTL

*Research prototype report. OpenFCP, November 2026.*

## Abstract

Large language models can produce substantial RTL and, just as quickly,
assertions that "verify" it. When the same kind of system writes the design
and the checks, a passing proof certifies very little. We separate the two
questions every verification claim depends on. **Conformance** asks whether
the RTL satisfies the formal property under its assumptions, and is decidable
for finite-state designs. **Fidelity** asks whether that property and those
assumptions mean what the prose requirement means. Fidelity is not decidable,
but it can be *refuted* by concrete witnesses and *corroborated* by
independent agreement.

The Formal Context Protocol (FCP) is an IR plus a set of analyses that turn
each recognized way a proof can yield false assurance into a mechanical check
with a concrete witness. The failure modes are: vacuity, assumptions that
constrain the design, unfaithful formalization, contradictory or
under-determined specifications, properties too weak to notice RTL changes,
and tool unsoundness. Every requirement keeps an auditable chain from its
verbatim source quote to content-addressed proof artifacts, and receives a
verdict whose level states exactly what has been established. What the
machine cannot settle becomes a short, prioritized queue of human decisions,
each backed by a waveform. We evaluate a prototype on four designs (FIFO,
round-robin arbiter, APB bridge, and a two-block hub) with seeded
specification defects, 28 injected RTL defects, AI-generated RTL, two
independent AI formalizations per design, and a controlled fault-injection
study of formalizations. Results are in Section 7.

## 1. Problem

A specification `S` (prose) describes intended behaviour. An implementation
`M` (RTL), possibly AI-generated, claims to realize it. A verification flow
produces, for each requirement `r_i` extracted from `S`, a formal property
`phi_i` and assumptions `A_i`, and checks `M |= (A_i => phi_i)`. The flow's
output is an *assurance claim*: "requirement `r_i` holds".

The claim is false in two different ways:

1. **Conformance failure.** The check is wrong: an engine bug, a modelling
   bug (X-semantics, reset), or a bounded result presented as a proof.
2. **Fidelity failure.** The check is right but irrelevant: `phi_i` or `A_i`
   does not capture `r_i`.

Simulation-based flows face the same problem in weaker form. Formal flows
remove the "selected behaviours" limitation but sharpen the fidelity problem:
an unfaithful property is proved *for all behaviours*, so the false assurance
is total.

## 2. First principles

**Traces and properties.** An interface `Sigma = (I, O)` of input and output
bit-vectors. A trace is `pi : N -> Val(I u O)`. A design `M` denotes a set of
traces `[[M]]`. A safety property is a set of traces closed under limits;
equivalently, it is recognized by a deterministic monitor with a per-cycle
verdict `ok_t`, where `pi |= phi` iff `ok_t(pi) = 1` for all `t`.

**Assume-guarantee satisfaction.**
`M |= (A => phi)` iff for every `pi in [[M]]` and every `t`, if `A` held at
all cycles `<= t` then `phi` is not violated at `t`. This is what model
checkers with `assume` statements decide.

**Where false assurance comes from.** Fix a requirement `r`, its
formalization `(A, phi)` and a proof of `M |= (A => phi)`. The proof is
*worthless as evidence for r* in exactly the following situations, each of
which is a property of artefacts we hold, and hence checkable:

| # | Situation | Mechanical witness |
|---|---|---|
| V | `phi` never "fires" on `M` under `A` (vacuous antecedent), or `phi` holds on *every* behaviour allowed by `A` (tautology) | unreachability proof of the trigger; proof of `phi` on the spec-only model with free outputs |
| E | `A` excludes behaviours of `M` itself rather than of its environment | a reachable state in which no non-reset input satisfies `A` (non-receptiveness) |
| F | `(A, phi)` differs from the meaning of `r` | a trace accepted by one independent formalization and rejected by another |
| C | the requirements contradict each other, so `r` cannot be met as written | a stimulus on which no output sequence satisfies the guarantees while the assumptions hold |
| U | `S` does not determine some output, so "proved" leaves behaviour open | two conforming behaviours with identical history that differ in an output |
| W | the proved properties are too weak to notice a behavioural change of `M` | an observable mutant of `M` that no property kills |
| T | the engine or model is wrong | engine disagreement (PDR vs BMC); simulator replay mismatch |

Fidelity (row F) is the only one that is not decidable from artefacts, because
`r` is prose. FCP's position is that undecidable does not mean unaddressable.
Fidelity can be **refuted** by showing a human a concrete behaviour on which
two readings differ, and **corroborated** by agreement of independent
formalizations (N-version formalization). A human judgment on a 6-cycle
waveform ("is this allowed by R-SIM-1?") is far cheaper and more reliable than
reviewing temporal formulas.

**Design consequences.**

1. *Small trusted base.* The AI is untrusted. Its outputs are restricted to
   a small language with precise semantics (FCP-PL) that is compiled by a
   deterministic compiler into monitors. The trusted base is that compiler,
   yosys, and the engines, and the engines cross-check each other.
2. *Context isolation.* A formalizer that sees the RTL can formalize what the
   RTL does rather than what the spec says. FCP formalizers see only the spec,
   the interface and the requirements.
3. *Black-box properties.* Requirements are formalized over interface signals
   and *specification-model* (ghost) state driven by the interface, never
   over internal RTL signals. The same properties then apply to any
   implementation and can be analysed without one.
4. *Witness-carrying verdicts.* Every non-trivial verdict carries a trace,
   such as a counterexample, trigger witness, distinguishing trace, blocking
   state, conflict stimulus or surviving mutant, so humans review behaviours
   rather than formulas.

## 3. The FCP intermediate representation

The IR (see [IR_spec.md](IR_spec.md)) has three layers, all YAML validated by
a versioned JSON Schema:

* **Design manifest**: interface (signals, widths as parameter expressions),
  parameters, reset, environment defaults, RTL variants, and source
  documents.
* **Requirements**: atomic requirements, each with a verbatim quote, a kind
  (guarantee / assumption / don't-care / scenario / definition /
  non-functional), dependencies and recorded ambiguities. Line spans are
  *computed* from quotes (`fcp anchor`), and quotes are re-verified on every
  load, so provenance cannot be hallucinated.
* **Formalization sets**: properties, assumptions, scenarios (behaviours that
  must be possible), don't-cares (intentional under-specification) and an
  explicit list of unformalized requirements with reasons. A set may define
  ghost state (a reference model), rigid variables (universally quantified
  constants) and named definitions. Several independent sets of the same
  requirements coexist.

Every analysis result is stored in an evidence ledger keyed by content hashes
of the spec, requirements, formal sets and RTL, together with tool versions
and the cache key of every proof task.

### 3.1 FCP-PL

FCP-PL is a past-time temporal expression language with three kinds of
values: booleans, unsigned bit-vectors, and integers with statically computed
ranges. Its semantic choices remove common sources of formalization error.

* **Exact arithmetic.** `count - 1` is -1 at count 0. Every numeric
  sub-expression is compiled to a two's-complement wire wide enough for its
  interval, and comparisons are mathematical.
* **No implicit truthiness.** Logical operators require 1-bit operands.
* **Past-time only.** `prev, rose, fell, stable, changed, once, hist, since`.
  Future obligations exist only inside *patterns* (`next`, `within`,
  `hold_until`, `bounded_wait`, `after_reset`, `inorder`) whose monitors are
  exact: they flag a violation on the minimal bad prefix.
* **Reset semantics.** Properties are evaluated only outside reset; history
  operators, ghosts and obligations are cleared by reset; `prev` reaching
  before the current reset segment disables evaluation instead of reading
  arbitrary state.

**Assert form vs assume form.** Some properties are best checked with
universally quantified nondeterminism. For example, `inorder` tracks one
arbitrarily chosen item (Wolper's data-independence argument), which keeps
proofs small. Such monitors are sound in *assertion* position only: in
*assumption* position the solver would simply choose not to track. FCP
therefore compiles every property twice. The `ok` form may be
nondeterministic. The `okd` form is deterministic: rigid variables are
expanded into conjunctions and `inorder` becomes an explicit queue model.
Every analysis that *assumes* a property uses `okd`.

## 4. Analyses

All analyses are generated harnesses around the same compiled monitor, run by
SymbiYosys (ABC PDR for unbounded proofs, boolector BMC for bounded checks
and witnesses) or by z3 directly on the yosys SMT2 model.

**4.1 Verification.** For each property, PDR (unbounded) and BMC (bounded)
are run independently. A PDR pass with a BMC failure is reported as an
*engine disagreement*, never as a proof. Every counterexample is replayed in
Icarus Verilog from the witness (inputs and initial state) and compared cycle
by cycle with the solver's trace. A replay can be confirmed, confirmed with
X (the failure depends on undefined state, e.g. an out-of-range memory read),
or a mismatch.

**4.2 Vacuity.** For each property with a trigger (antecedent), a cover proves
the trigger reachable on the RTL under the assumptions and yields a positive
example. If no witness is found, PDR proves unreachability and the proof is
classified VACUOUS. Independently, each property is checked on the
*spec-only model* (interface outputs free): if it holds there under the
assumptions, it constrains nothing and is a tautology.

**4.3 Receptiveness of assumptions.** Assumptions mention outputs (valid/ready
rules, "no push when full"). An assumption is legitimate only if it restricts
the environment: in every reachable state the environment must have at least
one legal, non-reset input. A state with none is a *blocking state*. In it,
`assume` prunes the design's own behaviour, so any bug past that point is
masked. Finding one is an exists-forall query (a reachable state such that
for all inputs the assumptions fail). We solve it by counterexample-guided
refinement over candidate input vectors with z3 on the yosys SMT2 model.

**4.4 Consistency.** A natural but wrong definition of conflict is "a trigger
situation that cannot occur once all requirements are assumed". This flags
situations the spec legitimately steers outputs away from. Our definition: a
**conflict** is a stimulus (an input sequence) on which *no output sequence*
satisfies the guarantees while the assumptions hold. Under assume-guarantee
semantics this is an unrealizability witness, because an open-loop
environment playing that stimulus defeats every implementation. Candidate
stimuli come from every requirement's trigger situation, every pair of
situations and every scenario, each extended by a lookahead (4.6). z3 decides
each candidate and returns a minimized unsat core: the minimal conflicting
requirements. Scenarios (behaviours the spec says must be possible,
including permissions such as "the bridge *may* accept...") that become
unreachable under the guarantees are reported separately. The check is
sound for conflicts but incomplete against an *adaptive* environment, since
a fixed stimulus lets the solver choose outputs clairvoyantly.

**4.5 Determinacy.** Self-composition: two copies of the interface outputs
share the inputs, both copies are constrained by all guarantees and
assumptions, and we search for a cycle where the output histories have been
identical but one output differs, outside declared don't-cares. A witness is
a concrete under-specification: the spec permits two behaviours after the
same history. This is a 2-safety (hyper)property, proved unboundedly by PDR
when it holds.

**4.6 Doomed prefixes and lookahead.** Monitors flag violations on minimal
bad prefixes, but a prefix with no violation *yet* may already be doomed.
For example, a wrong address in the setup phase is detected only at transfer
completion. Every analysis that interprets a satisfying prefix as evidence
(determinacy, comparison, consistency) therefore requires the prefix to be
extendable by `L = 1 + w` cycles, where `w` is the longest obligation window
in the set. Without this, the prototype reported spurious
under-specifications.

**4.7 Comparing formalizations (N-version formalization).** For two
independent sets and each requirement, FCP proves or refutes `P_a => P_b` and
`P_b => P_a`. It assumes the deterministic form of one, asserts the other on
the spec-only model with the union of both sets' assumptions, and requires
the counterexample to be extendable. The result is EQUIVALENT, STRONGER,
WEAKER or INCOMPARABLE, with a distinguishing trace for each failed direction.
This is also how formalization accuracy against a gold standard is measured
automatically.

**4.8 Triage.** For a counterexample, FCP asks whether any spec-conforming
output sequence exists on the same inputs. If one does, the RTL deviated, and
MaxSAT finds the conforming behaviour closest to the RTL's, which localizes
the bug to a (cycle, signal, expected, actual) diff. If none exists even
under assume-guarantee semantics, the requirements conflict on that stimulus
and an unsat core names them. Otherwise the stimulus violates the assumptions
for every conforming behaviour.

**4.9 Mutation assurance coverage.** yosys `mutate` samples netlist mutations
tied to RTL source lines. A miter decides observability under the
assumptions, comparing outputs outside reset and modulo don't-cares, and
equivalent mutants are excluded. Every property is then checked on every
observable mutant. Coverage is the fraction killed. Survivors are concrete,
line-located behaviour that no requirement constrains, and the kill matrix
links requirements to the RTL lines they constrain.

**4.10 Compositional contracts.** A sub-block with its own FCP contract is
replaced inside the parent by a generated stub. In *obligation* mode the stub
wraps the real block and asserts the block's assumptions on its boundary, so
the parent must honour the child's contract. In *abstraction* mode the stub's
outputs are free but constrained by the child's guarantees, so parent
properties are proved against the contract. Obligations are what make the
abstraction sound.

## 5. Verdicts and the review queue

Each requirement receives a level:

| Level | Meaning |
|---|---|
| ASSURED | unbounded proof; trigger witnessed; not a tautology; environment receptive; an independent formalization is semantically equivalent |
| PROVED-UNVALIDATED | proved, but no independent formalization corroborates the reading |
| PROVED-DISPUTED | proved, but an independent formalization differs (distinguishing trace attached) |
| PROVED-CONFLICTED / -VACUOUS / -ENV-UNSOUND | proved, but the proof is undermined by a conflict, vacuity or a blocking assumption |
| FAILED | counterexample, replayed and triaged |
| BOUNDED / UNKNOWN | engine-limited |
| UNFORMALIZED / COVERED-* / MISSING | not formalized with a reason, realized indirectly, or silently dropped |

Everything that is not mechanically discharged becomes an item in a review
queue. Each item has a severity, a subject, and the decision a human must make,
for example "adjudicate this distinguishing trace" or "these requirements
cannot all hold on this stimulus: amend the spec".

## 6. Agents

Agents are untrusted producers of IR, with fixed roles:

* **Decomposer**: spec to requirements with verbatim quotes. Spans are
  computed and checked by the tool.
* **Formalizers (N >= 2)**: requirements to formalization sets. Each runs in
  an isolated workspace without RTL and without the other formalizer's
  output, using different style hints for diversity. They may run the
  linter and the English renderer on their own output.
* **RTL generator**: spec to RTL, never seeing formalizations. Its RTL is
  what FCP validates.
* **Adversaries** are implemented mechanically in this prototype: the
  analyses of Section 4 challenge every formalization, triage every failed
  proof, minimize counterexamples (MaxSAT diff, unsat cores), and identify
  uncovered behaviour (surviving mutants, undetermined outputs).

Every agent run is recorded (prompt, prompt hash, model, outputs and their
hashes), so the study is replayable without the agents.

## 7. Evaluation

### 7.1 Corpus and setup

| Design | Spec lines | Ref RTL lines | Requirements (gold) | Gold properties / assumptions | Injected RTL defects | Spec defects |
|---|---|---|---|---|---|---|
| SFIFO-01 synchronous FIFO, DEPTH=5 | 86 | 53 | 21 | 16 / 0 | 8 | 4 planted, 1 found by an agent |
| RRA-4 round-robin arbiter | 53 | 44 | 12 | 9 / 1 | 7 | 4 planted |
| BRG-1 command-to-APB bridge | 84 | 61 | 21 | 20 / 2 | 8 | 3 planted |
| HUB-2 two-port APB hub (selector + BRG-1) | 45 | 124 | 13 | 26 / 5 | 5 | 2 planted, 2 found during the study |

The specifications are written like real IP documents. They contain
deliberate contradictions (FIFO: simultaneous push/pop at the boundaries,
`>=` vs `>` thresholds; arbiter: "granted in the same cycle" vs "registered",
"requester 3 always wins" vs fairness), ambiguities (rotation semantics,
read-data timing), a permission that another sentence forbids (bridge), an
incompleteness (bridge/hub write-response data), and a *vacuity trap* (a FIFO
usage rule that must not become an assumption). The 28 RTL defects are
realistic single edits: off-by-one flags, pointer wrap, missing reset,
priority, handshake, capture and routing errors.

The **gold** formalizations were written by the author, are proved on the
reference RTL, kill every observable mutant, and detect every injected
defect. They resolve the spec conflicts through recorded decisions.

**Agents.** For each design, four Claude Sonnet sub-agents ran in isolated
workspaces: one decomposer, two independent formalizers (different style
hints; no RTL, no gold, no access to each other), and one RTL generator
(spec and interface only). All 16 runs are recorded in `corpus/*/agents/`.
The formalizers worked from the gold requirement list, so that formalization
quality could be measured per requirement independently of decomposition
quality.

Tools: yosys 0.70, SymbiYosys with ABC PDR (unbounded) and boolector BMC
(depth 20), z3 5.3, Icarus Verilog 14. The machine has 32 cores. About 39,700
content-addressed proof tasks were run, about 38,400 engine CPU-seconds in
total. PDR's median per obligation is 0.82 s, the 95th percentile 2.3 s and
the maximum 15 s. A complete study run of a design, including mutation and
fault injection, takes 6 to 26 minutes of wall time, and an incremental
re-run takes under 8 minutes.

### 7.2 Decomposition

| Design | Gold reqs | Agent reqs | Recall of gold (quote overlap) | Kind agreement | Agent reqs with ambiguity flags | Spec defects flagged |
|---|---|---|---|---|---|---|
| FIFO | 21 | 53 | 100% | 20/21 | 39 (74%) | 5/5 |
| arbiter | 12 | 22 | 100% | 12/12 | 21 (95%) | 4/4 |
| bridge | 21 | 49 | 100% | 20/21 | 36 (73%) | 3/3 |
| hub | 13 | 31 | 100% | 13/13 | 27 (87%) | 4/4 |

Every quote was verbatim; the anchoring step rejected none. The decomposers
named every planted contradiction explicitly in prose, and found three real
defects that had not been planted:
- a parameter default that violates its own legal range for DEPTH=2;
- a permission in HUB-2 that allows two acceptances in one cycle;
- that the hub's 12-cycle bound "looks infeasible".

However, they attached ambiguity flags to 73–95% of all requirements. LLM
flags have high recall and low precision: on their own they cannot focus a
reviewer. The mechanical analyses supply the precision.

### 7.3 Formalization accuracy

Each agent property set was compared with gold by semantic implication under
the gold environment. The agent's assumptions were compared with gold's
separately.

| Design | Agent | Equivalent | Stronger | Weaker | Incomparable | Missing | Assumptions vs gold |
|---|---|---|---|---|---|---|---|
| FIFO | A | 4 | 1 | 3 | 8 | 0 | stronger (adopted the usage rule) |
| FIFO | B | 11 | 4 | 0 | 1 | 0 | equivalent |
| arbiter | A | 5 | 0 | 1 | 2 | 0 | equivalent |
| arbiter | B | 6 | 0 | 0 | 2 | 0 | equivalent |
| bridge | A | 7 | 1 | 5 | 1 | 1 | incomparable (pready window) |
| bridge | B | 4 | 0 | 2 | 9 | 0 | weaker |
| hub | A | 4 | 2 | 0 | 4 | 0 | incomparable |
| hub | B | 3 | 1 | 1 | 5 | 0 | weaker |

Only **45% (44/98)** of agent formalizations are semantically equivalent to
the intended meaning, although every set was well-formed, lint-clean, and
read back correctly through `fcp explain`. This is the core empirical case for
FCP: well-formed, plausible, and self-checked AI formalizations are wrong
about half of the time. The differences are seldom absurd. They are readings
of timing windows ("within 4 cycles of the start"), conditions, modalities,
and conflicts that the agent resolved differently.

### 7.4 Defect detection

Gold detects 28/28 injected RTL defects. Every counterexample was replayed in
Icarus Verilog and confirmed. Two are *confirmed-with-X*: the failure depends
on reading uninitialised or out-of-range state, which the simulator shows as
X. The agent sets detect 55/56. The miss is FIFO agent A, whose usage-rule
assumption excludes the behaviour that bug B3 corrupts.

**AI-generated RTL.** The four RTL generators produced designs that pass
their own extensive self-written testbenches (up to hundreds of thousands
of cycles, each catching all 12 to 24 of its own self-inserted mutations). FCP's verdicts against the gold contract:

| Design | Verdict | Detail |
|---|---|---|
| FIFO | **ASSURED** | all 16 properties proved, 57/57 observable mutants killed |
| bridge | **ASSURED** | all 20 proved, 56/56 mutants killed |
| arbiter | **FAILED R-RST-1** | `gnt` is not masked while `rst_n` is low. The generator chose this deliberately ("gating would make it non-registered"). Replay confirmed; triage reports an RTL deviation at cycle 0, `gnt: RTL 1, spec 0` |
| hub | **FAILED R-OV-1** | it accepts a new command in the response-handshake cycle, using a BRG-1 "may" that the hub's one-transaction rule forbids. Triage reports an RTL deviation, `c0_ready/c1_ready: RTL 1, spec 0` at cycle 4 |

### 7.5 False assurance

We count a *violation* for each (buggy variant, requirement) pair where the
gold property fails, 244 in total over the eight agent sets. A flow gives
*false assurance* if it claims the requirement holds:
- **Naive:** the set's properties for the requirement are proved. This is
  the "LLM writes assertions, prover says PASS" workflow.
- **FCP:** the requirement reaches level ASSURED. That requires a proof, a
  witnessed trigger, a receptive environment, and **contract equivalence**
  with the other agent's independent formalization. Gold is never used as a
  peer.

| Design | Agent | Violations | Naive false assurance | FCP false assurance |
|---|---|---|---|---|
| FIFO | A | 53 | **30 (57%)** | 0 |
| FIFO | B | 56 | 0 | 0 |
| arbiter | A | 20 | 3 (15%) | 0 |
| arbiter | B | 20 | 2 (10%) | 0 |
| bridge | A | 28 | 6 (21%) | 0 |
| bridge | B | 31 | 6 (19%) | 0 |
| hub | A | 18 | 4 (22%) | 0 |
| hub | B | 18 | 5 (28%) | 0 |
| **total** | | **244** | **56 (23%)** | **0 (0%)** |

FIFO agent A is the instructive case. It adopted the usage rule "the producer
shall not push while full" as an environment assumption, while noting in
plain English that this made two tolerance properties untriggerable. That
assumption is receptive: the environment can always choose not to push. So
the receptiveness check correctly does not object. The flaw was caught twice.
Vacuity analysis proved FA-WR-2 and FA-RD-3 vacuous (and tautological), and
contract comparison showed every one of agent A's contracts to be *weaker*
than agent B's.

An earlier version of the comparison pooled both sets' assumptions. Under it,
agent A's assumption leaked into the agreement check, and FCP still gave 4
false assurances (8%) on this set. **Comparing contracts `A_x => P_x` rather
than properties under pooled assumptions is necessary for soundness.** This
is a methodological result of the study.

### 7.6 Injected formalization faults

Each gold property was mutated by one fault operator at a time, a mechanical
model of typical formalization mistakes. A masking-assumption variant was
also run for every property with a trigger:

| Operator | Semantic faults | Flagged by FCP | Would hide a real RTL bug (naive) | ... (FCP) | Flagged by |
|---|---|---|---|---|---|
| placeholder consequent (`... \|\| true`) | 50 | 50 | 30 | 0 | vacuity/tautology, peer |
| reset-polarity error in trigger | 27 | 27 | 18 | 0 | vacuity, peer |
| masking assumption (`assume !trigger`) | 27 | 27 | 20 | 0 | vacuity, peer, receptiveness (11) |
| dropped conjunct | 17 | 17 | 2 | 0 | peer, vacuity |
| same-cycle instead of next-cycle | 25 | 25 | 1 | 0 | fails on reference, peer |
| bound one cycle too loose | 11 | 11 | 0 | 0 | peer |
| bound one cycle too tight | 4 | 4 | 0 | 0 | fails on reference, peer |
| **total** | **161** | **161 (100%)** | **71** | **0** | |

Of 172 injected mutations, 11 were semantically equivalent to the original
and were excluded automatically by the implication check. Without FCP, 71 of
the 161 faults would have certified a buggy design.

### 7.7 Independent disagreement as an error signal

Across all requirements formalized by both agents, a contract disagreement
between them was always a real error (45 of 45: precision 1.0), and 9
agreements were correct. There were only 2 agreements in error, both from the
arbiter, where both agents chose the literal "shift the priority by one
position" reading of an ambiguous sentence while gold, the reference RTL and
the AI RTL use true round robin. These two did not produce false assurance:
the agents' properties fail on the intent-conforming RTL, and the
decomposer's ambiguity flag puts the requirement in the review queue. They do
show the fundamental limit of N-version formalization: correlated
misreadings of ambiguous text. Witness-carrying review of flagged ambiguities
is the remaining defence.

### 7.8 Specification analysis

* **Conflicts.**
  - FIFO: the literal set yields exactly the two planted contradictions as
    minimal cores, `{R-SIM-1, R-ST-4}` and `{R-ST-3, R-TM-2, R-ST-4}`, and
    shows the *consequence* of the second: the scenario "the FIFO becomes
    full" is unreachable, because count would have to pass through AF_LEVEL.
    Agent B, which kept the corner cases literal, produced the same cores.
  - Arbiter: both agents' sets yield the planted cores `{R-G-2, R-OV-1}`,
    `{R-G-1, R-OV-1, R-PRI-3}` and `{R-G-3, R-PRI-3}`.
  - Bridge: the "may accept" permission, which both agents formalized as a
    scenario, is *unreachable* under the agents' own guarantees. Agent B
    predicted this.
  - The earlier, naive conflict definition reported dozens of "conflicts" in
    the consistent bridge gold set. The assume-guarantee feasibility criterion
    reports none.
* **Unrealizable requirement found by FCP.** HUB-2 required every pending
  command to be accepted within 12 cycles. The reference RTL failed it. A
  sweep found the tight bound to be exactly 17, and hand analysis confirmed
  that round robin plus the specified environment latencies force 17
  cycles. This defect was *not* planted. Every hub agent later reached the
  same conclusion independently: both formalizers, the decomposer, and the
  RTL generator, which gave a throughput argument. The fixed-stimulus triage
  could not *prove* unrealizability, because a clairvoyant implementation
  meets the bound on any single stimulus. This is a documented limitation.
* **Determinacy.**
  - It reproduced the planted gap: bridge `rsp_rdata` on write responses is
    undetermined, and nothing else is.
  - On the first hub gold set it also found that I had omitted "a response is
    raised only after its transfer completes". FCP corrected the reference
    itself.
  - The doomed-prefix lookahead (Section 4.6) was needed: without it the
    bridge gold set showed spurious under-specification of `paddr`.

### 7.9 Compositional reasoning (HUB-2)

The reference hub passes **all** end-to-end properties. Its bridge-contract
obligation, the bridge's own assumption "a pending command is held stable
until accepted", **fails**: when a second port arrives, the selector switches
ports while the bridge is busy. This is a latent integration bug. It is
harmless with this bridge, which samples only when idle, and would break any
pipelined replacement. A first repair, holding the selection, honoured the
bridge contract but **violated round robin**, which the monolithic proofs
caught. The correct repair presents a command to the bridge only when it is
ready. It passes all monolithic proofs, both obligations, and all 22 parent
properties against the bridge *contract* in place of its implementation
(3.1 s): a sound assume-guarantee proof.

### 7.10 Cost: assurance yield and human review

FCP's zero false assurance has a price, and we report it. With two
independent Sonnet-class formalizers, contract-level agreement was rare.
Their readings of timing windows and environment obligations differed, so few
requirements were ASSURED automatically: 2 and 5 of 10 for the arbiter, 0
elsewhere. Most proved requirements were PROVED-DISPUTED, and each one goes
to a human with a distinguishing trace. In a simulated adjudication, where
each dispute is resolved by checking the formalization against the intended
meaning, 0–9 per set are confirmed and the rest need repair. The review
queue on the reference designs holds 8–27 decisions per set. A naive flow
asks for no decisions and is wrong about 23% of the violated requirements it
certifies. A manual review of the same formal sets would mean judging 9–26
temporal formulas per design with no witness of where they go wrong.

## 8. Threats to validity

* **Gold authorship.** Gold formalizations were written by the same model
  family as the agents (as the expert author). They are validated
  mechanically: they are proved on reference RTL, kill every observable
  mutant, detect every injected defect, and are consistent and determined.
  Their *fidelity* to the prose is still a judgement, recorded as decisions.
  FCP found one gap in a gold set.
* **Scale.** The designs are small; the largest monitor has a few hundred
  state bits. PDR scaled comfortably: every verification obligation in the study received a definitive verdict (no bounded or unknown results). Large
  subsystems will need the compositional route of Section 7.9 more
  systematically.
* **One parameterization per design** (FIFO DEPTH=5 was chosen non-power-of-two
  deliberately).
* **Isolation by instruction.** Agents were told not to read outside their
  workspace. One reported listing sibling directory names once. Production
  use needs sandboxed workspaces.
* **Review effort is a proxy:** counts of decisions, not measured human time.
* **Bounded lookahead and clairvoyant triage** are sound for what they report
  but incomplete: conflicts that need an adaptive environment are missed.

## 9. Related work

* **Vacuity:** Beer et al. 1997; Kupferman and Vardi 2003.
* **Assume-guarantee:** McMillan's circular reasoning for safety; contract
  theories.
* **Realizability:** Pnueli and Rosner.
* **Self-composition and hyperproperties:** Barthe et al.; Clarkson and
  Schneider.
* **Mutation-based coverage for formal:** mcy; commercial property-coverage
  tools.
* **N-version programming:** Avizienis.
* **LLM-generated assertions and specifications:** nl2spec; LLM-to-SVA
  generators.

FCP's contribution is not any single analysis. It is the protocol: a
provenance-carrying IR, a semantics designed to avoid the common
formalization errors, the observation that each false-assurance mode has a
mechanical witness, the soundness refinements the study forced (assume vs
assert forms, feasibility-based conflicts, extendable witnesses,
contract-based agreement), and verdicts that say exactly what has been
established.

## 10. Conclusion

When AI writes both the RTL and the checks, "all properties proved" is not
evidence. Across four designs, 55% of the AI formalizations meant something
other than the specification. Taking proofs at face value certified 23% of
the violated requirements and 71 of 161 injected faults. FCP certified none,
and routed every uncertain claim to a reviewer together with the concrete
behaviour at stake. Its analyses also found what neither the spec author nor
the reference designs had caught:
- an unrealizable latency bound;
- a latent contract violation between two blocks;
- a missing requirement in the reference formalization itself.

The remaining problem is honest and well defined: agreement between
independent formalizers is the bottleneck of assurance yield, and
disagreements are cheap to adjudicate exactly because FCP turns them into
waveforms.
