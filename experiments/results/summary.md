# FCP study: results

## Formalization sets

| Design | Set | Props | Assumptions | Proved on ref | Failed on ref | Injected bugs detected (other variants) | Mutation coverage | Receptive | Conflicts | Lint |
|---|---|---|---|---|---|---|---|---|---|---|
| fifo | gold | 16 | 0 | 16 | 0 | 8/8 (ai: pass) | 56/56 (100%) | True | 0 | 0 |
| fifo | agent_a | 18 | 2 | 18 | 0 | 7/8 (ai: pass) | 55/56 (98%) | True | 0 | 0 |
| fifo | agent_b | 24 | 0 | 21 | 3 | 8/8 (ai: FAIL) | 56/56 (100%) | True | 2 | 0 |
| fifo | literal | 17 | 0 | 15 | 2 | 8/8 (ai: FAIL) | 56/56 (100%) | True | 3 | 0 |
| arbiter | gold | 9 | 1 | 9 | 0 | 7/7 (ai: FAIL) | 40/40 (100%) | True | 0 | 0 |
| arbiter | agent_a | 11 | 2 | 7 | 4 | 7/7 (ai: FAIL) | 40/40 (100%) | True | 3 | 0 |
| arbiter | agent_b | 11 | 2 | 7 | 4 | 7/7 (ai: FAIL) | 40/40 (100%) | True | 2 | 0 |
| bridge | gold | 20 | 2 | 20 | 0 | 8/8 (ai: pass) | 57/57 (100%) | True | 0 | 0 |
| bridge | agent_a | 17 | 2 | 17 | 0 | 8/8 (ai: pass) | 57/57 (100%) | True | 0 | 0 |
| bridge | agent_b | 18 | 2 | 18 | 0 | 8/8 (ai: pass) | 57/57 (100%) | True | 0 | 0 |
| hub | gold | 26 | 5 | 26 | 0 | 5/5 (fixed: pass, ai: FAIL) | 58/58 (100%) | True | 0 | 0 |
| hub | agent_a | 20 | 5 | 18 | 2 | 5/5 (fixed: FAIL, ai: FAIL) | 58/58 (100%) | True | 0 | 0 |
| hub | agent_b | 26 | 5 | 24 | 2 | 5/5 (fixed: FAIL, ai: FAIL) | 58/58 (100%) | True | 0 | 0 |

## Formalization accuracy of the agents (semantic relation to gold, per requirement)

Properties are compared under the gold environment; the agent's assumption set is compared with gold's separately.

| Design | Set | Equivalent | Stronger | Weaker | Incomparable | Missing | Unknown | Equivalent rate | Assumptions vs gold |
|---|---|---|---|---|---|---|---|---|---|
| fifo | agent_a | 4 | 1 | 3 | 8 | 0 | 0 | 25% | STRONGER |
| fifo | agent_b | 11 | 4 | 0 | 1 | 0 | 0 | 69% | EQUIVALENT |
| arbiter | agent_a | 5 | 0 | 1 | 2 | 0 | 0 | 62% | EQUIVALENT |
| arbiter | agent_b | 6 | 0 | 0 | 2 | 0 | 0 | 75% | EQUIVALENT |
| bridge | agent_a | 7 | 1 | 5 | 1 | 1 | 0 | 47% | INCOMPARABLE |
| bridge | agent_b | 4 | 0 | 2 | 9 | 0 | 0 | 27% | WEAKER |
| hub | agent_a | 4 | 2 | 0 | 4 | 0 | 0 | 40% | INCOMPARABLE |
| hub | agent_b | 3 | 1 | 1 | 5 | 0 | 0 | 30% | WEAKER |

## False assurance on real agent formalizations

A *violation* is a (buggy RTL variant, requirement) pair whose gold property fails. False assurance = the flow claims the requirement is assured although it is violated. Naive: all of the set's properties for the requirement proved. FCP: level ASSURED (proved, non-vacuous, receptive environment, equivalent to the independent peer agent set).

| Design | Set | Violations | Naive false assurance | FCP false assurance | Buggy designs declared verified (naive / FCP) |
|---|---|---|---|---|---|
| fifo | agent_a | 53 | 30 (57%) | 0 (0%) | 1 / 0 |
| fifo | agent_b | 56 | 0 (0%) | 0 (0%) | 0 / 0 |
| fifo | literal | 53 | 0 (0%) | 0 (0%) | 0 / 0 |
| arbiter | agent_a | 20 | 3 (15%) | 0 (0%) | 0 / 0 |
| arbiter | agent_b | 20 | 2 (10%) | 0 (0%) | 0 / 0 |
| bridge | agent_a | 28 | 6 (21%) | 0 (0%) | 0 / 0 |
| bridge | agent_b | 31 | 6 (19%) | 0 (0%) | 0 / 0 |
| hub | agent_a | 18 | 4 (22%) | 0 (0%) | 0 / 0 |
| hub | agent_b | 18 | 5 (28%) | 0 (0%) | 0 / 0 |

## Injected formalization faults (one fault per run, into gold)

| Design | Injected | Semantic faults | Flagged by FCP | Hide a real bug (naive) | Hide a real bug (FCP) |
|---|---|---|---|---|---|
| fifo | 34 | 30 | 30 (100%) | 20 | 0 |
| arbiter | 22 | 22 | 22 (100%) | 15 | 0 |
| bridge | 51 | 48 | 48 (100%) | 27 | 0 |
| hub | 65 | 61 | 61 (100%) | 9 | 0 |

| Fault operator | Semantic faults | Flagged | Hide bug (naive) | Hide bug (FCP) | Flagged by |
|---|---|---|---|---|---|
| dropped-conjunct | 17 | 17 | 2 | 0 | peer-disagreement 17, vacuity 2 |
| loose-bound | 11 | 11 | 0 | 0 | peer-disagreement 11, vacuity 1 |
| masking-assumption | 27 | 27 | 20 | 0 | peer-disagreement 27, receptiveness 11, vacuity 27 |
| placeholder-consequent | 50 | 50 | 30 | 0 | peer-disagreement 50, vacuity 50 |
| reset-polarity-trigger | 27 | 27 | 18 | 0 | peer-disagreement 27, vacuity 27 |
| same-cycle | 25 | 25 | 1 | 0 | fails-on-reference 23, peer-disagreement 25, vacuity 4 |
| tight-bound | 4 | 4 | 0 | 0 | fails-on-reference 3, peer-disagreement 4 |

## Disagreement between independent agents as an error detector

| Design | Disagree & wrong | Disagree & both right | Agree & wrong | Agree & right |
|---|---|---|---|---|
| fifo | 17 | 0 | 0 | 0 |
| arbiter | 3 | 0 | 2 | 5 |
| bridge | 15 | 0 | 0 | 0 |
| hub | 10 | 0 | 0 | 0 |

## Assurance yield on the reference design and simulated adjudication

ASSURED: requirements FCP discharges without human input. Adjudication simulates a human who resolves every PROVED-DISPUTED requirement against the intended meaning (gold): the set's formalization is confirmed if it is equivalent to gold, otherwise it must be repaired.

| Design | Set | Formalized reqs | ASSURED | Disputed | Disputed, confirmed by adjudication | Disputed, needs repair | Failed on ref |
|---|---|---|---|---|---|---|---|
| fifo | agent_a | 17 | 0 | 15 | 4 | 11 | 0 |
| fifo | agent_b | 18 | 0 | 13 | 9 | 4 | 2 |
| fifo | literal | 17 | 0 | 12 | 0 | 12 | 2 |
| arbiter | agent_a | 10 | 2 | 1 | 0 | 1 | 4 |
| arbiter | agent_b | 10 | 5 | 1 | 1 | 0 | 4 |
| bridge | agent_a | 14 | 0 | 14 | 7 | 7 | 0 |
| bridge | agent_b | 15 | 0 | 14 | 4 | 10 | 0 |
| hub | agent_a | 10 | 0 | 9 | 4 | 5 | 1 |
| hub | agent_b | 10 | 0 | 9 | 3 | 6 | 1 |

## Review queue and runtime

| Design | Set | Queue on ref | Wall time (s) |
|---|---|---|---|
| fifo | gold | 22 | 43.3 |
| fifo | agent_a | 24 |  |
| fifo | agent_b | 26 |  |
| fifo | literal | 27 |  |
| arbiter | gold | 8 | 27.9 |
| arbiter | agent_a | 13 |  |
| arbiter | agent_b | 12 |  |
| bridge | gold | 19 | 394.6 |
| bridge | agent_a | 17 |  |
| bridge | agent_b | 17 |  |
| hub | gold | 11 | 665.8 |
| hub | agent_a | 12 |  |
| hub | agent_b | 12 |  |

## Totals

- Agent formalizations equivalent to gold: 44/98 (45%)
- False assurance on agent sets: naive 56/244 (23%), FCP 0/244 (0%)
- Injected semantic formalization faults flagged by FCP: 161/161 (100%)
- Injected faults that hide a real RTL bug: naive 71, FCP 0
