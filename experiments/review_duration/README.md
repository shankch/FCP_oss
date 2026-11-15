# `fcp review` on one AI answer: a duration parser

`request.md` is the request; `code/parse_duration.py` and its tests were
written for it by Claude Sonnet, which saw only the request. Then:

```bash
bin/fcp review --request experiments/review_duration/request.md \
               --code experiments/review_duration/code/parse_duration.py \
               --out experiments/review_duration/out
```

ran the whole protocol with no person in the loop: an adapter agent wrote the
design from the request and the code's signature only, a decomposer agent the
requirements, two isolated formalizer agents the readings (all Opus, headless
through `claude -p`, every prompt and reply under `out/agents`), and FCP the
analyses and the code check. The result is [out/review.md](out/review.md):
the requirements certified, and the questions for the person who wrote the
request. `--resume` reruns the analyses on the saved bundle without the
agents.
