I wrote /work/ws_order_agent_a/formal/agent_a.yaml (set agent_a, 29 formal items). `fcp lint` reports no errors, and I read the `fcp explain` output for every item. I ran only lint and explain, no consistency or other analyses, so the conflict described below comes from reading the text, not from an engine result.

**Items**
- **2 assumptions:**
  - OA-A-ARGS (R-SIG-1): the four arguments do not change within a run, as the frame.md Inputs table states.
  - OA-A-ANSWER (R-API-1): a step's answer is ok, refused or error, so `answer <= 2`.
- **26 properties:**
  - R-ARGS-1: 5, one per call kind, checking that each call carries this order's arguments.
  - R-ERR-1: 1.
  - R-STEPS-1: 2. One says charge comes after reserve and book after charge. The other says that with valid arguments the function returns only after a step failed or the booking answered ok.
  - R-ORDER-1: 2.
  - R-ONCE-1: 3.
  - R-RET-1: 4. These cover returning True, no call after the booking answered ok, no other call anywhere in a run where all three steps answered ok, and True only if all three answered ok.
  - R-STOP-1: 2. No step after a failed step, and the return is False with outcome 0.
  - R-UNDO-1: 6. Refund or release by the return when needed, each at most once, and only when there is something to undo.
  - R-LIMIT-1: 1. A call is never the fifth call of the run.
- **1 scenario,** OA-EX-1 for R-EX-1: the prompt's example `place_order(7, 3, 2, 500)`.
- **No ghost state.** Every item relates interface signals directly, using once, since, hist and prev, plus one `next` pattern.
- **Decisions for R-UNDO-1:** reading 1 for both flagged phrases.
  - The refund and the release may come in either order, because the text gives no order.
  - "Only then": no refund or release when there is nothing to undo. The prompt's example supports this, since a refused charge leads to a release and no refund.

**Left unformalized:** R-FR-1, R-FR-2 and R-FR-3. They are frame rules of the interface adapter, and design.yaml already adds them to every set as F-END, F-ZERO and F-LIMIT.

**Problems in the specification**
1. **The rules contradict each other, and the inputs alone force it.** Suppose reserve and charge answer "ok" and book is refused or raises. Rules 2, 4, 6 and 7 then require five calls: reserve, charge, book, refund and release. Rule 8 allows at most four. No implementation can meet every rule on that script. I formalized both sides literally and recorded the conflict in OA-LIMIT-1's note.
2. **Rule 7 does not order the undo calls.** It says nothing about whether the refund or the release comes first, and I took "either order".
3. **"Call nothing else in that case" (rule 5) has two readings.** It can mean nothing in the whole run or only nothing after the booking. I formalized both, as OA-RET-NOTHING and OA-RET-STOP.
4. **"Take no later step" (rule 6) has two readings.** I read it as no reserve, charge or book at all after a failure. That gives the same result as "no later step in the order" once rule 4 (each step at most once) applies.
5. **"Stock we hold" and "paid" (rule 3) are read literally.** Each means the step answered ok and has not been undone since.
6. **Rule 1 says "if", not "only if".** It does not itself forbid ValueError for valid arguments, though the other rules fix the outcome of those runs.
7. **R-RET-1's text goes beyond its quote.** It adds "False otherwise", which the quote of rule 5 does not contain. I formalized it as OA-RET-FALSE and said so in the note.
