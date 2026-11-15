# Prompts as finite-state machines: checking any prompt–response pair with the chip engine

[FCP_general.md](FCP_general.md) proposed generalizing FCP from RTL to any
prompt–response pair with domain adapters. This document takes a stronger
position. Every prompt is treated as a finite-state machine and every
response as a trace of that machine, so a prompt can be verified exactly like
chip logic, with the same engines.

The claim was tested on a real prompt. The unchanged FCP pipeline (yosys,
ABC-PDR, boolector, z3) checked three readings of the prompt and three
responses from three models. The engine needed only three small changes:

* a design-level *frame*;
* a *contextual* mode for comparing readings;
* a compiler fix that an agent found.

Everything is in [corpus/prompt_email/](../corpus/prompt_email/) and
[experiments/prompt_demo.py](../experiments/prompt_demo.py).

## 1. The assumption, made precise

The assumption "every prompt is an FSM" is true for free. A response has a
bounded length over a finite vocabulary, so any set of acceptable responses is
finite and therefore regular. The free version is useless, though: at the
token level the automaton is the answer key.

The useful version is a factorization:

```
response --segment--> units u1..un --label--> σ1..σn ∈ 2^AP --monitor A--> verdict
             (the clock)                (the outputs)              (the prompt)
```

* **Units:** a response is split into units (sentences, lines, tool calls,
  turns). Each unit is one clock cycle.
* **Labels:** each unit gets a few labels, which are atomic propositions about
  that unit, such as "states the price" or "asks the reader to act".
* **Prompt:** the prompt becomes a small automaton over the labels. It holds
  the finite control (order, counts, conditions, prohibitions). The
  semantics lives in the labels.

The *factorization hypothesis* is the substantive assumption: the author's
intent depends on the response only through its label trace.

| Chip | Prompt |
|---|---|
| clock cycle | one unit of the response |
| reset | start of the response |
| output port | a label (1 bit, or a small integer) |
| input port | environment events: user turns, tool results (none for one-shot text) |
| RTL | the response replayed as a chip ([fcp/text.py](../fcp/text.py)); for agents, the scaffold that generates it |
| SVA / FCP-PL property | an instruction of the prompt |
| interface protocol | the *frame*: units, end of response, label compatibility ([frame.md](../corpus/prompt_email/frame.md)) |
| sensor and ADC | the labeler |

The last row is the honest summary. This is a mixed-signal design. The
digital part (the automaton) is decided exactly. The analog front end (the
labels) is not, so a verdict is exact *relative to its labels* and the labels
carry the residual risk.

Exact rules decide the labels that can be decided exactly (`subject`,
`price`, `signoff`). Two isolated labelers decide the others. The labelers
never see the prompt's requirements.

## 2. What the chip engine does with a prompt

These analyses already existed and are unchanged:

* **Before any response exists.** Is the prompt satisfiable at all, and if not,
  which minimal set of instructions conflicts? Does any instruction constrain
  nothing? Where do two independent readings of the prompt differ, and what is
  the simplest response that tells them apart?
* **For each response.** An exact verdict per instruction, with the unit at
  which it fails; anti-responses (the empty response); mutation, i.e. which
  label changes no instruction notices.

These are the changes this work needed:

* **Frame** ([fcp/ir.py](../fcp/ir.py), [fcp/analyses.py](../fcp/analyses.py)).
  The frame lists rules that every behaviour satisfies by construction of the
  encoding: `eos` is absorbing, no labels after the end, at most 14 units, and
  a closing unit carries no other label. Spec-only analyses assume it, and
  verification checks it on every response chip. Without it the free model
  quantifies over traces that no text can produce.
* **Contextual comparison with witness economy**
  ([fcp/analyses.py](../fcp/analyses.py), `compare(context=True,
  economy=...)`).
  * Two readings of one instruction are compared only over responses that
    satisfy every *other* instruction under both readings.
  * The witness is then minimized to the response with the fewest labels set.
  * The result is a question about a realistic response, not about a trace
    that breaks every other instruction (Section 3.2).
* **History-operator fix** ([fcp/lang.py](../fcp/lang.py)).
  * Formalizer agent_a reported that a `prev` nested inside `once`, `hist` or
    `since` could accumulate a value read in the reset cycle.
  * Confirmed: `!once(feature && prev(once(feature)))` failed on a response
    with one feature unit, while the equivalent
    `feature -> !prev(once(feature))` proved.
  * The operand is now skipped in the cycles where it would read past a reset.
  * All 16 existing corpus monitors are byte-identical after the fix, so no
    earlier result changes.

## 3. The demo: an email prompt

| Input | Source |
|---|---|
| Prompt | [spec.md](../corpus/prompt_email/spec.md): a launch email with 10 checkable instructions, one planted conflict and several ambiguities |
| Readings | `gold` (mine, literal); `agent_a`, `agent_b` (isolated formalizer agents, same prompt template as the RTL study) |
| Responses | Opus, Sonnet and Haiku, each given only the prompt ([responses/](../corpus/prompt_email/responses/)) |
| Labels | rules for `subject`, `price`, `signoff`; labeler A (Sonnet) and labeler B (Haiku), isolated from the prompt; the adjudicator (me), written before reading A and B |
| Baseline | an LLM-as-judge (Opus) with the prompt, the responses and a per-instruction checklist |

Runtime: 50 s for the whole pipeline (3 readings × 10 response chips), plus
285 s for the contextual comparisons with minimized witnesses.

### 3.1 The prompt is unsatisfiable under its literal reading, and this is found before any response

Without any response, consistency analysis proved that no email satisfies the
gold reading, in 12 s. It returned this minimal conflicting set:

* "Start with a subject line."
* "Then greet the reader by their first name."
* "Describe exactly three features"
* "Give each feature its own sentence,"
* "and follow it with a sentence about the benefit"
* "Keep the body under 7 sentences."

Read literally, a greeting plus three feature sentences plus three benefit
sentences is 7 body sentences, and "under 7" allows at most 6.

The first run of the analysis did not find the conflict, and why matters.
The solver had built a "conforming" email that hid benefits inside closing
units ("greet benefit signoff"), so they did not count as body sentences. The
free model allowed label combinations that no real text has. Two fixes
followed:

* a frame rule: closing units carry no other label;
* a positional definition of the body in my reading.

In other words, the prompt-level analysis tests the label semantics as well as
the prompt. It finds loopholes in the encoding the way a model checker finds
under-constrained inputs.

### 3.2 Three readings and the questions they produce

The readings disagree on exactly the planted ambiguities:

* "the body" (does the greeting count?);
* "its own sentence";
* "followed by the sign-off".

| Requirement | Plain comparison | In context, minimized witness | Question for the author |
|---|---|---|---|
| R-LEN-1 "under 7 sentences" | agents vs gold: INCOMPARABLE | agents weaker than gold. The witness is subject, greeting, F, B, F, B, F, B+price+CTA, sign-off | "Is this email under 7 sentences?" The witness has exactly the structure that all three models wrote, so any of the three emails is the question |
| R-FEAT-2 "its own sentence" | agent_a weaker than gold | agent_a weaker: it accepts a feature in the subject line, with its benefit in the greeting line | "May a feature appear in the subject line?" |
| R-GREET-1 "Then greet" | agent_a vs both others: INCOMPARABLE | vs gold: EQUIVALENT. vs agent_b: agent_a stronger; it rejects a greeting unit that also starts with "Subject:" | none against gold; against agent_b, only about a malformed subject line |
| R-END-1 "End with a call to action" | agents stronger than gold, on the empty email; agent_a weaker than agent_b | vs gold: NO-CONTEXT. agent_a vs agent_b: agent_a weaker; it accepts a second sign-off in the middle of the email | none against gold until R-LEN-1 is answered, because under gold no email meets the rest of the prompt. Between the agents: "May 'The Aurora Team' appear before the end?" |

Three findings come out of this table:

* **Comparing in isolation produces irrelevant disputes.** Two of the four
  plain disputes come from traces that break other instructions. One of them
  vanishes in context, and the other survives only through a malformed
  subject line.
* **The questions have an order.** The conflict question (R-LEN-1) has to be
  answered first, because under gold the R-END-1 dispute has no context to be
  asked in.
* **The comparison also exposed a weakness in my own reading.** Gold's R-END-1
  accepts the empty email: its end-of-response trigger never fires when the
  response ends at once. Both agents' readings reject it. The other
  requirements reject the empty email anyway, but as a reading of the
  instruction gold is too weak.

### 3.3 Responses as chips

The table gives the requirements each response fails, using the adjudicator's
labels.

| Response | gold (greeting counts) | agent_a (greeting excluded) | agent_b (greeting excluded, benefit may share the feature sentence) |
|---|---|---|---|
| empty (anti-response) | 4 requirements | 5 | 5 |
| Opus | R-LEN-1 | none | none |
| Sonnet | R-LEN-1 | none | none |
| Haiku | R-LEN-1, R-FEAT-2 (unit 4: "Adaptive noise cancelling adjusts …, so the noise fades …") | R-FEAT-2 (same unit) | none |

Every failure names the unit at which it occurs. Every verdict follows from
two choices: a reading of the prompt and a set of labels. FCP surfaces both.

### 3.4 Labels are the trust boundary

| Comparison | Label decisions that differ (27 units × 7 labelled properties = 189) |
|---|---|
| labeler A vs labeler B | 1 |
| labeler A vs adjudicator | 2 |
| labeler B vs adjudicator | 3 |

The two labelers differ on only one decision. But they *share* two decisions
the adjudicator disagrees with:

* "Say hello to the Aurora X2, our new wireless headphones": both labelers
  call the subject line a feature;
* "for a soft, comfortable fit": both call it a benefit.

The first one changes verdicts. With the labelers' labels, Sonnet's email has
four features, so it fails three more requirements under gold and two or
three more under the agent readings.

So agreement between independent labelers is not correctness: their errors
are correlated, as the RTL study found for formalizers. Two remedies follow,
and each is a mechanical step, not a judgment:

* anchor labels to the prompt's own facts ("states one of the listed product
  facts"), which removes this particular dispute;
* send a sample of agreed labels to the adjudicator.

### 3.5 The LLM-as-judge baseline

The judge marked **33 of 33** checks PASS and answered that the prompt is
satisfiable. Its comments show how:

* "6 body sentences (greeting not counted)";
* "one feature each in sentences 1, 3, 5".

It chose agent_b's readings silently. It did not say that the instruction is
ambiguous, that under the other reading every email fails, or that the prompt
then cannot be satisfied at all. Its reading is defensible, and perhaps even
the intended one. The point is that the judge returns one confident answer
where FCP returns a question, the evidence for it, and the consequence of
each answer.

## 4. Contextual comparison on the RTL study

The study's open problem was yield. The strict rule accepted 7 of 104
requirements on the reference RTL. Disputes were dominated by readings that
differ only on behaviours a conforming design never shows.

The contextual comparison targets exactly that. It is sound per requirement
under one condition: accept a disputed requirement on an RTL variant only when
(a) both readings are equivalent in context, and (b) every other requirement
of both readings is proved on that variant. The variant's behaviours then lie
inside the context, so the peer's reading holds as well.
[experiments/context_rule.py](../experiments/context_rule.py) measures yield
and false assurance as [decision_rules.py](../experiments/decision_rules.py)
does, and checks the argument on every gained acceptance.

The full study evidence was used: 4 designs, 2 agent readings each, 104
formalized requirements on the reference RTL, and 244 violated requirements
on buggy variants.

| Acceptance rule | Accepted on reference RTL | False assurance on buggy RTL |
|---|---|---|
| naive: the reading is proved | 92/104 | 56/244 |
| all readings proved, even if they differ ([decision_rules.py](../experiments/decision_rules.py)) | 77/104 | 10/244 |
| equivalent in a *minimal* sufficient context, and that context proved | 64/104 | 5/244 |
| **equivalent in the full context, and every other requirement proved under both readings** | **31/104** | **0/244** |
| strict: equivalent, as in the study | 7/104 | 0/244 |

* **Full context.** Comparing readings in context raises yield 4.4-fold, from
  7 to 31, with zero false assurance. All of the gain is on the bridge, the
  one design whose reference RTL proves every requirement under both
  readings. On the FIFO, arbiter and hub, a single failing requirement blocks
  the rule.
  * Most disputes vanish in context: 13 of 17 on the FIFO, 3 of 3 on the
    arbiter, 12 of 14 on the bridge and 6 of 10 on the hub.
  * The argument held empirically: whenever the rule accepted a requirement,
    the peer's reading was proved too, with 0 exceptions.
* **Minimal context.** A minimal sufficient context has 1 to 6 requirements.
  Requiring only that context to be proved unlocks the other designs and gives
  64 of 104, but it admits 5 false assurances:
  * arbiter B3/R-PRI-2 (both agents) and hub ai/R-OV-1 (both agents). These
    are four of the five cases where all readings were proved but wrong.
  * arbiter B3/R-G-3 for agent_a, which is new.

  In every case the peer's reading was also proved, so the argument held. Both
  agents were simply wrong together. Every one of these designs fails another
  requirement, which the full-context condition forbids.

The lesson is the one the dial already taught. Agreement between readings,
exact or contextual, is evidence about the readings, not about intent. The
safe use of contextual equivalence is on designs that pass everything under
both readings. Elsewhere, disputes still need a question.

## 5. What else the FSM view gives

These items are designed but not built, except the last, which is now built
and measured in [FCP_agent.md](FCP_agent.md).

* **Generation-time enforcement.** A monitor plus co-reachability ("can this
  prefix still be completed into an accepted response?") is a shield. If a
  unit leads to a dead state, regenerate that unit. The finite control is then
  correct by construction, and only the labels remain at risk. At the token
  level this is grammar-constrained decoding; at the unit level it is
  shielding (Alshiekh et al., 2018).
* **Learning intent with queries.** Each reading is a hypothesis about the
  author's automaton.
  * A distinguishing response is a membership query in Angluin's L*.
  * Agreement of independent readings plus spot checks approximates an
    equivalence query.
  * The PAC bound from FCP_general.md (ln(1/δ)/k) applies.
  * For large label alphabets, symbolic automata learning (Argyros and
    D'Antoni, 2018) is the relevant theory.
* **Testing the label alphabet (CEGAR).** Suppose two responses have the same
  label trace but get different human verdicts. That pair is a mechanical
  witness that the labels are too coarse, and it says where to refine them,
  for example a feature *count* instead of a feature bit. agent_a noticed the
  bit's limit by itself: two features in one sentence count as one.
* **Agents as chips.**
  * An agent's scaffold (states, retries, permissions) is RTL; each LLM call is
    a cut point with free outputs; tools are the environment, with
    assumptions.
  * A policy in the system prompt ("no refund above $500 without escalation")
    is then proved for *every* LLM output.
  * A counterexample is the exact LLM output that breaks the policy. That is
    where a runtime guard belongs, and the guard becomes a checked assumption
    in an assume-guarantee contract ([fcp/compose.py](../fcp/compose.py)).
  * Built: [FCP_agent.md](FCP_agent.md) (scaffold compiled from Python,
    enforced / delegated / broken classification, forcing stimuli, 18 real
    model runs).

## 6. Where the assumption breaks

* **Labels.** A verdict is only as strong as its weakest label: rule-exact,
  labeler-agreed, or adjudicated. The FSM does not remove this gap; it isolates
  it to single, small questions such as "does unit 0 state a feature?".
* **Content relations.** "Every claim is supported by the source" or "the
  answer is correct" become one oracle label. The automaton adds nothing, and
  the requirement stays judged.
* **Holistic qualities.** Tone, persuasiveness and style are a one-state
  machine over a global label, and stay judged (R-TONE-1 here).
* **Non-regular structure.** Unbounded counting or nesting does not occur,
  because responses are bounded and FCP-PL counters are exact integers. The
  cost is size, which is what symbolic engines are built for.
* **Segmentation.** Segmentation is itself an interpretation. agent_a noted
  that a subject line containing ". " would split into two units.

## 7. Reproduce

```bash
.venv/bin/python experiments/prompt_demo.py        # chips from labels, full pipeline, results/prompt_email*.json
.venv/bin/python experiments/context_rule.py       # contextual comparison on the RTL study
bin/fcp explain corpus/prompt_email --set agent_a  # any reading, in English
```

Agent prompts, models and output hashes are recorded under
[corpus/prompt_email/agents/](../corpus/prompt_email/agents/).
