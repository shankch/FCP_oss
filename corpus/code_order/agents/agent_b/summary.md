I wrote `formal/agent_b.yaml`. It has 22 items. `fcp lint` comes back clean, with one info note: the answer assumption depends on outputs (`op`, `phase`), so its receptiveness has to be checked. I read the `fcp explain` rendering back and every item says what I meant.

I also ran a spec-only `fcp check` once to test the model. It reported no tautologies, no unreachable scenarios and no undetermined outputs. It found exactly one conflict, the one I expected (first problem below). The temporary output and cache from that run have been deleted from the workspace.

**How the model works.** Ghost state sums up the earlier calls and answers in the run:
- `held`: reserve answered "ok" and nothing has been released since.
- `paid`: charge answered "ok" and nothing has been refunded since.
- Which steps were called, and which answered "ok".
- `failed`: some step was refused or raised its error.
- `stage`: the furthest step reached so far.
- Counts of refunds, releases and total calls.

Every output is checked against this state.

**The 22 items:**
- **Assumptions (2):**
  - The four arguments stay the same through a run (R-SIG-1).
  - reserve, charge and book only ever answer 0, 1 or 2 (R-API-1).
- **Properties (19):**
  - R-ERR-1: 1
  - R-ARGS-1: 5, one per service method
  - R-STEPS-1: 2 (step order; no return until a step fails or the booking answers "ok")
  - R-ORDER-1: 2
  - R-ONCE-1: 3
  - R-RET-1: 1
  - R-STOP-1: 2
  - R-UNDO-1: 2 (refund count and release count at the return)
  - R-LIMIT-1: 1
- **Scenario (1), R-EX-1:** the exact example run: reserve(3,2) "ok", charge(7,500) "refused", release(3,2), return False, three calls in all.
- **Decisions for R-UNDO-1:** reading 1 for both flagged phrases. The refund and release may come in either order, because the text joins them with "and", not "then". They happen only when there is something to undo.

**Unformalized:** only R-FR-1, R-FR-2 and R-FR-3. They are adapter frame rules, `covered_by` F-END, F-ZERO and F-LIMIT. R-SIG-1 has no property of its own: the stable-arguments assumption carries it, and other properties already rule out outcome 3, so the function always returns a bool.

**Problems in the specification:**
1. **Rule 8 contradicts rules 6 and 7.** If reserve and charge answer "ok" and book is refused or raises, the rules require reserve, charge, book, refund and release. That is five calls, but rule 8 allows at most four. I did not repair it; it is noted in the R-UNDO-1 and R-LIMIT-1 items. `fcp check` confirmed it, with the minimal conflicting set R-LIMIT-1, R-ONCE-1, R-ORDER-1, R-STEPS-1 and R-UNDO-1 on `place_order(7,3,1,1)` with answers ok, ok, refused. A side effect: the R-UNDO-1 question about refund-versus-release order only matters on that conflicting script, because it is the only case that needs both.
2. **Rule 2 states no exception for invalid arguments, but rule 1 forbids any call then.** I limited "take the three steps" to valid arguments, and said so in the note.
3. **Literal readings I took, each noted on its item:**
   - "Return True when" means "if". Returning False after a failure comes from R-STOP-1.
   - "Call nothing else in that case" covers the whole run: exactly three calls. This is stronger than the requirement's paraphrase, which only forbids calls after the booking. It is the only item that rules out, for example, a release before the reserve in a run where every step answers "ok".
   - "Stock we hold" and "paid" stop being true after a release or a refund.
   - "Stop there" also forbids retrying the step that failed.
4. **Interface limitation, not a spec error:** `qty` and `amount` are unsigned, so negative arguments, which rule 1 rejects, cannot occur in traces.

`fcp check` does not copy item notes into `evidence.json`; they exist only in the YAML file.

File: /work/ws_order_agent_b/formal/agent_b.yaml
