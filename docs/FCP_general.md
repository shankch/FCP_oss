# FCP beyond hardware: checking any prompt–response pair

The hardware prototype checks `M_RTL ⊨ (A_i ⇒ φ_i)` for requirements taken from a prose spec.
This note generalizes the method to any pair of a prompt `P` (with context documents `C`) and a
response `R` produced by an AI system: code, a SQL query, a schedule, a summary, an email, or an
agent's sequence of tool calls. The goal is unchanged. For every requirement in `P`, report exactly
what has been established about `R`, show the evidence, and never report more than that.

## 1. Three questions instead of two

| Question | Hardware | General |
|---|---|---|
| **Conformance:** does `R` satisfy the reading `(A, φ)`? | model checking | depends on the response type (section 3) |
| **Fidelity:** does `(A, φ)` mean what the prompt says? | N-version readings and witnesses | same |
| **Interpretation:** do the values measured on `R` reflect `R`? | not needed: yosys gives RTL an exact semantics | needed whenever `R` is prose |

The interpretation gap is new. It has the same shape as the fidelity gap: an unreliable translator
sits between text and a formal object. So it gets the same remedy: independent translators, a
semantic comparison, and a concrete witness when they disagree.

## 2. The domain-independent core

* **Requirement:** an atomic obligation anchored to a verbatim span of `P` or `C`, or to a declared
  default. Typical defaults are "the code must run" and "every claim must be supported by the
  attached document". Defaults are explicit entries with ids, so they can be seen and disputed in
  the same way as the hardware decisions `D-1`, `D-2`.
* **Reading:** one reader's formal interpretation of a requirement. It has four parts:
  * **observables `O`:** typed quantities measured on `R`, for example `bullets: list[str]`,
    `out(x): int` or `events: trace`;
  * **assumptions `A`:** constraints on the environment only (inputs, context, other agents), never
    on `R`;
  * **property `φ`:** a predicate over `O` in a decidable checking logic;
  * **pattern:** the template it instantiates (invariant, implication, bounded response, count,
    inclusion, equality with context, ...).
* **Semantics adapter:** maps `R` to the values of `O`. The mapping is either:
  * **exact:** run the code, evaluate the query, parse the structure, replay the trace; or
  * **extracted:** independent extractors read `R`, and their outputs are compared.
* **Engines:** decide `φ` on `O(R)`, or for all inputs when `R` is a program or a system.
* **Ledger:** evidence records, a verdict per requirement, and a review queue of concrete questions.

The bundle of requirements, readings, observables with their source spans in `R`, evidence,
decisions and verdicts travels with the response. A consumer re-runs every exact or proved check
from the bundle instead of trusting the producer, as in proof-carrying code. This is the
"protocol" in Formal Context Protocol: an **evidence-carrying response**.

### Verdicts have two axes

**Evidence strength** (strongest first):

| Level | Meaning |
|---|---|
| PROVED | sound decision procedure, all inputs allowed by `A` (programs, systems) |
| EXACT | deterministic evaluation of `φ` on exactly computed observables (a single instance: a parsed document, a logged trace) |
| EXHAUSTIVE / BOUNDED | every instance of a declared finite domain, or every instance up to a declared size or depth |
| TESTED | sampled instances, with the generator and its coverage recorded |
| EXTRACTED | deterministic `φ` over observables on which independent extractors agree |
| JUDGED | a model or a person judged it; who judged and how it was calibrated are recorded |

**Fidelity status:**
* AGREED: independent readings are equivalent;
* RESOLVED: a disagreement was answered by a person and the answer is recorded as a decision;
* DISPUTED: an open distinguishing example;
* UNCORROBORATED: only one reader formalized it;
* flags: VACUOUS, WEAK, CONFLICTED, ENV-UNSOUND (section 5).

A requirement is **ASSURED** only at PROVED or EXACT strength with AGREED or RESOLVED fidelity and
no flags. A response's verdict is the weakest verdict over its requirements. It is never averaged
into a score, because a score hides which requirement is weak.

## 3. Three kinds of response

| Kind | Examples | Semantics of `R` | Checking logic | Engines | Best evidence |
|---|---|---|---|---|---|
| **Static, exact** | code, SQL, regexes, configs, schedules, math answers, JSON outputs | execution or evaluation | pre/postconditions; relational and arithmetic constraints | SMT, symbolic execution, bounded-exhaustive and property-based testing, verifiers (Dafny, Lean, Verus) | PROVED, or BOUNDED within a declared scope |
| **Reactive** | circuits, agent tool-use trajectories, dialogue policies, protocols | traces | past-time temporal patterns: FCP-PL as it is | model checking for systems; monitors for logged runs | PROVED for systems, EXACT for a given run |
| **Textual** | answers, summaries, emails, reports | extracted typed observables | quantifier-free predicates over the observable schema; entailment against `C` as a judged primitive | deterministic evaluation; SMT over the schema for the analyses; entailment models | EXACT for structure, EXTRACTED for content, JUDGED for support and quality |

Agent trajectories deserve attention. A run of a tool-using agent is a trace of events: tool calls,
messages and results. Requirements on it are exactly FCP-PL patterns:
* "never push to main" is an invariant;
* "run the full suite after the last edit, before committing" uses `since` and `once`;
* "answer each question within two turns" is a bounded wait.

The hardware machinery transfers almost unchanged: events become monitor inputs. The hub's latent
contract violation between two blocks has a direct analogue: a sub-agent's output that breaks the
next agent's input assumptions while the end-to-end task still succeeds.

## 4. Design principles

**P1. Models translate, code judges.** Language models map the prompt to readings and the response
to observable values. Every verdict is computed by deterministic code from those values. A model
never answers "does `R` satisfy `r`?" directly, except for requirements explicitly marked JUDGED,
which are never reported as verified. This matters for two reasons:
* a judge that reads the response can be persuaded by it, and its verdict can be neither replayed
  nor localized;
* separating translation from judgment confines each error to one translation step, where
  redundancy can expose it.

**P2. Isolation.** Each role sees only what it needs:
* readers see `P` and `C`, never `R`;
* extractors see `R` but not the predicates, so they fill a schema without knowing which values
  pass;
* probe generators see readings, not `R`.

A reading written after seeing `R` tends to describe `R`. This is why the hardware formalizers never
saw the RTL. In general settings, the same discipline addresses judges rationalizing the response.

**P3. Keep the checking logic decidable; confine undecidability to translation.** Comparison,
conflict, determinacy and vacuity all need a decision procedure for the checking logic. Observables
are typed and finite or bounded, so these analyses are SMT problems. What cannot be decided ("does
this sentence mean that?") is confined to the translation steps, where it is handled by redundancy
and witnesses. FCP-PL already followed this principle implicitly.

**P4. Ask with examples, not abstractions.** Every fidelity question is a concrete instance on which
two readings differ: an input, a database, a candidate response or a trace. The instance must be
legitimate, meaning it satisfies every other agreed requirement, so the question cannot be dismissed
as moot. This is the general form of the hardware lookahead condition, which requires that a witness
can be extended.

**P5. Every check must show it has teeth.** Each reading must reject two kinds of probe:
* **anti-responses:** empty, trivial, off-topic (the answer to a different prompt), the prompt
  echoed back;
* **targeted mutants of `R`:**
  * code: mutation operators;
  * text: a changed number, a dropped sentence, a swapped entity, a negated claim;
  * traces: reordered or deleted events.

A reading that accepts an anti-response is a tautology on this instance. A requirement whose
readings kill no mutant is non-discriminating.

The kill matrix also gives the dual result: the parts of `R` that no requirement notices.
Unconstrained content (extra claims, extra features, unjustified agent actions) is reported, not
silently passed.

**P6. Assumptions constrain only the environment, and each has provenance.** An assumption may
constrain inputs or context only, must cite a span or a declared default, and is compared as part
of its contract `A ⇒ φ`. Assumptions from different readers are never pooled. In the hardware study,
pooling let one reader's masking assumption leak into the comparison and caused FCP's only false
assurances before the fix.

**P7. Two axes, never one score.** Evidence strength and fidelity status are reported separately
(section 2).

**P8. Disagreement anywhere is a reliability signal.** If two readings differ, the sentence is hard
to read and both readings may be wrong. Section 6 measures what happens when this is ignored.

## 5. The analyses, generalized

| Hardware failure mode | General question | Static, exact | Reactive | Textual |
|---|---|---|---|---|
| Vacuity | Did the situation the requirement talks about occur? | trigger inputs covered by the evidence | trigger reached in the trace or system | the observable is present in `R` |
| Tautology | Does the reading reject anything? | rejects trivial programs (identity, constant, raise) | rejects free outputs | rejects anti-responses |
| Non-receptive assumptions | Do the assumptions constrain only the environment, and keep the cases the prompt names? | the precondition excludes inputs named in `P` | the receptiveness check as it is | an assumption about `C` contradicts `C` or excludes a named case |
| Unfaithful reading | Do independent readings agree? If not, where do they differ? | distinguishing input | distinguishing trace | distinguishing candidate response, built at the observable level and then realized |
| Contradiction | Can all requirements hold at once? | unsat core over the specs | the consistency check as it is | unsat core over observable constraints, then a realization attempt |
| Under-determination | Do the requirements fix what matters? | two compliant programs that differ on some input | the determinacy check as it is | two compliant responses that differ materially |
| Weak properties | Would the checks notice a wrong `R`? | mutation kill matrix | the kill matrix as it is | text-mutation kill matrix |
| Tool unsoundness | Do independent engines and extractors agree? | two engines, replay | PDR against BMC, simulation replay | N extractors; judge calibration on known-good and known-bad variants |

For textual responses, the analyses run on the observable schema, where they are decidable. A
witness found there is an observable vector, for example "6 bullets, revenue present, no Q4
statements". It must then be realized as an actual response and re-extracted to confirm it. When no
sensible response realizes the vector, the witness is dropped. This mirrors the hardware triage
limitation: a clairvoyant witness is not proof against an adaptive environment.

## 6. The acceptance rule is a dial (measured)

When independent readings differ but both hold on `R`, should `R` be accepted? If the intended
meaning is among the readings, both holding implies that `R` is correct. That suggests accepting
without asking anyone. The hardware study's evidence tests this directly
([experiments/decision_rules.py](../experiments/decision_rules.py)):

| Rule | Accept requirement `r` on `R` when | Accepted on the correct RTL without review | False assurance on buggy RTL |
|---|---|---|---|
| naive | the reading is proved | 92/104 | 56/244 (23%) |
| all-readings | every independent reading is proved and clean, even if the readings differ | 77/104 | 10/244 (4%) |
| context | the readings are equivalent on every behaviour that meets the other requirements, and every other requirement is proved under both readings ([FCP_fsm.md](FCP_fsm.md) §4) | 31/104 | 0/244 |
| strict (FCP) | the readings are equivalent, proved and clean | 7/104 | 0/244 |

The 10 false assurances come from five (design, variant, requirement) cases, each counted once for
each agent set:
* arbiter B3 / R-PRI-2;
* bridge B1 / R-RSP-2;
* hub B2 / R-RSP-2;
* hub B3 / R-RSP-1;
* hub AI RTL / R-OV-1.

In every case the two agents read the sentence differently, and both readings accepted exactly the
buggy behavior that the intended reading rejects. The intended meaning was not among the readings.
No rule that looks only at the readings can catch this. Only a question about intent can, and asking
is what the strict rule forces.

Consequences:
* The rule is a dial, set by the cost of a wrong acceptance. Each acceptance records which rule
  produced it.
* Under the strict rule, the price is questions, not risk.
* Questions belong to the requirement, not to the response. An answer is recorded as a decision and
  reused for every later response to the same prompt or template:
  * for a production prompt template, the cost amortizes towards zero;
  * for a one-off prompt, it is the cost of a few clarifying questions, each asked with a concrete
    example.
* The strict rule's 0/244 is an observation, not a guarantee. When readers share the same wrong
  reading (two cases on the arbiter), they agree. Those cases were caught only because the shared
  reading failed on the correct RTL.

## 7. Theory: intent as a hidden predicate

Let `I*` be the acceptance predicate in the author's head; `P` is a lossy encoding of it. Each
reading `φ^j` is a hypothesis about `I*`, and the readers form a committee `H`.

* **A distinguishing instance is a membership query.** For an instance `x` with `φ^a(x) ≠ φ^b(x)`,
  the answer `I*(x)` eliminates at least one hypothesis. This is query-by-committee (Seung, Opper and
  Sompolinsky, 1992), with queries generated by solvers instead of sampled.
* **Soundness.** Assume:
  * (i) every engine is sound for the evidence level it reports;
  * (ii) the observables of `R` are computed correctly;
  * (iii) `I*` belongs to the surviving committee `H'` (the coverage hypothesis).

  Then a strict acceptance implies `I*(R)`, and so does an all-readings acceptance. The two rules
  differ only in how often (iii) fails in practice. Section 6 shows that disagreement is strong
  evidence that (iii) is failing.
* **Bounding the residual risk.** Sample `k` instances from a neighborhood of `R`, such as mutants
  of `R` or perturbed inputs, and ask about intent on each. If all `k` answers agree with the
  accepted reading, then with confidence `1 − δ` the reading's disagreement rate with intent on that
  neighborhood is at most `ln(1/δ)/k`. For example, `k = 30` and `δ = 0.05` give at most 10%. The
  hope that the committee covers intent becomes a measured bound, at a known cost in questions.

## 8. Worked examples

**Code.** "Write `dedupe(xs)` that removes duplicates, keeping the first occurrence of each element."
* **Readings:**
  * A: the output is the subsequence of first occurrences;
  * B: the output equals `list(dict.fromkeys(xs))`.
* **Comparison:** the readings agree on every hashable input of a bounded-exhaustive domain. B
  raises on `[[1], [1]]`, so a hidden assumption becomes visible. Question: "Must `dedupe` accept
  unhashable elements such as lists?"
* **Anti-responses:** `return xs` and `return sorted(set(xs))` are rejected by both readings.
* **Conformance:** symbolic execution or bounded-exhaustive checking within the declared scope gives
  BOUNDED evidence.

**SQL.** "Customers who placed more than 3 orders last month."
* **Readings** differ on two points:
  * `> 3` against `≥ 3`;
  * the previous calendar month against the last 30 days.
* **Distinguishing database:** one customer with exactly 3 orders, and one order placed on the first
  day of the current month (inside the last 30 days, outside the previous calendar month). Two yes/no
  questions settle intent.
* **Conformance:** the query is compared with the agreed reference reading on generated databases
  (BOUNDED), or with an equivalence checker where the SQL fragment allows it.

**Summary.** "Summarize the attached Q3 report in at most 5 bullet points. Include total revenue and
year-on-year growth. Don't speculate about Q4."
* **Observables:**
  * bullets, from an exact parse;
  * revenue stated in the summary and revenue in the report, each from two independent extractors;
  * statements about Q4, extracted;
  * atomic claims, each with its support span in the report.
* **Properties:**
  * `len(bullets) ≤ 5`;
  * `rev_resp == rev_ctx`;
  * `q4_claims == []`;
  * every claim is supported (JUDGED).
* **Fidelity questions,** each asked with a candidate summary:
  * "Does a numbered list count as bullet points?"
  * "Is repeating the report's own sentence 'Q4 guidance is unchanged' speculation?"
* **Teeth:** suppose the report's first five sentences, used as an anti-response, pass every check.
  Then the checks do not capture what a summary is, and the report says so instead of passing `R`
  silently.
* **Evidence:** format EXACT, revenue EXTRACTED, no speculation EXTRACTED, support JUDGED.

**Agent run.** "Fix the failing test. Don't push to main. Run the full test suite before committing."
* **Events:** `edit`, `run_tests(scope, passed)`, `commit`, `push(branch)`.
* **Readings:**
  * `invariant !(push && branch == main)`;
  * `commit -> since(!edit, run_tests && scope == full && passed)`, meaning a full passing run with no
    edit after it.
* **Disagreement:** a second reading, `commit -> once(run_tests && scope == full && passed)`, accepts
  any full run before the commit, even one before the last edit. Distinguishing run:
  `edit, run_tests(full, pass), edit, commit`.
* **Conformance:** a monitor over the logged run gives EXACT evidence. Checking the agent's policy for
  all runs is model checking against an environment model.

## 9. IR sketch

```yaml
fcp: 0.2
domain: text.summary
prompt: {file: prompt.md}
context: [{id: C1, file: q3_report.md}]
defaults:
  - {id: D-SUPPORT, text: "Every claim in the response is supported by the context."}
requirements:
  - {id: R1, quote: "in at most 5 bullet points", kind: format}
  - {id: R2, quote: "Include total revenue", kind: content}
  - {id: R4, quote: "Don't speculate about Q4", kind: prohibition}
  - {id: R5, default: D-SUPPORT, kind: support}
readings:                       # one file per isolated reader; readers never see the response
  agent_a:
    observables:
      bullets:   {type: "list[str]", adapter: markdown.list_items}                 # exact
      rev_resp:  {type: "money?", adapter: extract, ask: "total revenue stated in the response"}
      rev_ctx:   {type: money, adapter: extract, over: C1, ask: "total Q3 revenue"}
      q4_claims: {type: "list[claim]", adapter: extract, ask: "statements about Q4 outcomes"}
      claims:    {type: "list[claim]", adapter: atomic_claims}
    assumptions:
      - {id: A1, source: C1, quote: "Total revenue", text: "C1 states exactly one total revenue figure"}
    properties:
      - {id: P1, req: R1, pred: "len(bullets) <= 5"}
      - {id: P2, req: R2, pred: "rev_resp == rev_ctx"}
      - {id: P4, req: R4, pred: "len(q4_claims) == 0"}
      - {id: P5, req: R5, pred: "all(supported(c, C1) for c in claims)", evidence: judged}
```

## 10. What the current prototype already provides, and what is new

**Reused as it is:**
* requirement IR, provenance anchoring, decisions and schema validation
  ([fcp/ir.py](../fcp/ir.py), [fcp/anchor.py](../fcp/anchor.py));
* the agent protocol: isolated workspaces and recorded runs ([fcp/agents.py](../fcp/agents.py));
* the ledger, verdict levels, review queue and reports ([fcp/pipeline.py](../fcp/pipeline.py),
  [fcp/report.py](../fcp/report.py));
* for the reactive kind: FCP-PL and monitor synthesis. Agent events become monitor inputs, and the
  existing PDR flow decides comparison and consistency over event alphabets.

**New:**
* **domain adapters:** exact parsers, N-version extractors, anti-response generators and mutation
  operators for each response type;
* **a typed observable logic with a z3 encoding** (records, bounded lists, sets, money, dates), for
  comparison, conflict and determinacy at the schema level;
* **an instance realizer:** turns an observable-level witness into an input, a database, a candidate
  response or a trace, and confirms it by re-extraction;
* **the extra evidence levels** EXACT, EXHAUSTIVE, BOUNDED, TESTED, EXTRACTED and JUDGED, plus the
  acceptance dial.

## 11. A study for the generalization

* **Corpus:** five response types (Python functions, SQL, structured outputs, summaries with source
  documents, agent runs), with about ten prompts each. Each prompt comes with:
  * seeded prompt defects (ambiguity, contradiction, under-specification) and their ground truth;
  * seeded response defects (mutants) and real AI responses;
  * gold readings, validated mechanically as in the hardware study.
* **Baselines:**
  * an LLM judge per requirement, which sees the prompt and the response;
  * LLM-written tests or checks, run on the response;
  * single-reader FCP;
  * full FCP at each setting of the dial.
* **Metrics:**
  * false assurance per requirement;
  * defects detected;
  * questions per prompt and human time per question;
  * accuracy of readings and extractions against gold;
  * cost in tokens and CPU.
* **Hypotheses:**
  * H1: LLM-judge false assurance is substantial, and higher when the judge reads the response before
    stating its criteria.
  * H2: full FCP brings false assurance near zero for exact responses, and well below the baselines
    for textual ones, with a bounded number of questions per prompt.
  * H3: the dial's operating points carry over across response types.
  * H4: anti-response and mutant probes catch most weak readings without human input.

## 12. Related work

* **IFEval** (Zhou et al., 2023): instructions verifiable by code, such as word counts and keywords.
  This is a fixed catalog of exact observables, with no fidelity analysis.
* **InFoBench** (Qin et al., 2024): decomposes instructions into yes/no criteria judged by a model.
  It has decomposition, but no formal readings or witnesses.
* **FActScore** (Min et al., 2023) and **SAFE** (Wei et al., 2024): atomic claims of a response,
  checked for support. They correspond to response-side extraction for support checking.
* **TiCoder** (Lahiri et al., 2022; Fakhoury et al., 2024): users approve generated tests to pin down
  intent. This is the closest prior work to distinguishing-example questions, for code.
* **nl2postcond** (Endres et al., 2024): model-written postconditions scored for correctness and,
  using mutants, for discriminative power. These are readings plus the mutation check, for code.
* **Clover** (Sun et al., 2024): a consistency check among docstring, code and Dafny annotations.
* **Semantic entropy** (Farquhar et al., 2024): agreement among independent generations, judged by
  meaning, used to detect confabulation.
* **Query by committee** (Seung, Opper and Sompolinsky, 1992): the learning-theory basis for asking
  where hypotheses disagree.
* **Proof-carrying code** (Necula, 1997): the consumer re-checks the evidence instead of trusting the
  producer.

What is new here:
* one protocol across all response types;
* evidence strength separated from fidelity;
* isolation for both readers and extractors;
* a taxonomy of ways an "assured" verdict can be wrong, each with a mechanical witness;
* measured operating points for the acceptance rule.

## 13. Limitations

* For textual responses, support against the context is still judged by a model. Evidence there is
  capped at JUDGED, and extractors can make correlated errors.
* The coverage hypothesis (iii) is an assumption. Spot checks bound the risk only near `R`, and they
  cost questions.
* Cost scales with the number of readers, extractors and probes. That is acceptable for high-stakes
  outputs but not for casual chat.
* Open-ended quality (tone, helpfulness, creativity) stays JUDGED. FCP's contribution there is to say
  so plainly.
* A textual witness may have no sensible realization, which mirrors the hardware triage limitation.
