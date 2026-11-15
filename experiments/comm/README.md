# HumanEvalComm pilot: what each review rests on

Written up in [docs/FCP_code.md](../../docs/FCP_code.md) §13; run by
[experiments/comm_demo.py](../comm_demo.py); counts in
[results/comm.json](../results/comm.json).

One directory per request: `<problem number>/<original | 1a | 1c | 1p>/`.

| file | what it is |
|---|---|
| `request.md` | the request as `fcp review` got it: "Complete this function:" and the description with its signature |
| `bundle/` | the adapter's design and frame, the decomposer's requirements, the readings of the two formalizers and of the variant reader |
| `agents/<agent>/` | the prompt, the summary and the run record of each of the five agents |
| `review.json`, `review.md` | the review; absent when the check did not end, and `status.json` says why |
| `check<n>_review.*` | the review of an earlier check of the same request, kept when it was checked again after a fix to the engine |
| `again/` | in the 8 requests whose check did not end in the pilot: the second check, by the engine that writes a review whatever a step of its check does ([experiments/comm_again.py](../comm_again.py), counts in [results/comm_again.json](../results/comm_again.json)). `review.json`, `review.md`, `status.json`, and `check_errors.txt` with what the checking process printed about a step that failed. Counted apart from the 72 reviews of the pilot |
| `baseline.json` | the replies of the same model without tools, under three instructions |
| `judge.json` | the grades of the benchmark's judging prompt |
| `status.json` | what ran, how long it took, and how it ended |

Beside them: [tasks.json](tasks.json), the screen and the 20 problems
drawn; [audit.json](audit.json), every tool call of the agents with its
outcome; and [replay.json](replay.json), every call that a review shows
under a question about two readings, run again on the monitors of those
readings without a solver ([experiments/comm_replay.py](../comm_replay.py)).

A stored bundle holds no copy of its request. To check a request again,
copy its bundle, put `request.md` into the copy as `spec.md`, and run the
check on it; no agent runs, and the review is written to `recheck/`:

```bash
mkdir recheck && cp -r experiments/comm/138/1p/bundle recheck/bundle
cp experiments/comm/138/1p/request.md recheck/bundle/spec.md
.venv/bin/python -c "from fcp import review; review.checked('recheck/bundle', None, ['agent_a', 'agent_b'], 'recheck')"
```

The descriptions are from HumanEvalComm (Jie JW Wu and Fatemeh H. Fard,
ACM TOSEM 2025; https://github.com/jie-jw-wu/human-eval-comm at commit
794a91f3c520e3939b8361e9f4ae927c25756a6e, Apache-2.0), which rewrites the
problem descriptions of HumanEval (OpenAI, MIT license). The benchmark's
tests and solutions are not stored here, and no agent saw them.
