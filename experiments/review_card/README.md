# `fcp review` on the gift card, end to end

The request is the gift card prompt ([../../corpus/code_card/spec.md](../../corpus/code_card/spec.md)),
whose study gave the first false assurance in the code studies; the code is
Opus's implementation from that study
([corpus/code_card/agents/coder_opus/gift_card.py](../../corpus/code_card/agents/coder_opus/gift_card.py)).

```bash
bin/fcp review --request experiments/review_card/request.md \
               --code corpus/code_card/agents/coder_opus/gift_card.py \
               --out experiments/review_card/out
```

Every step is an agent here: the adapter, the decomposer (whose
requirements differ from the study's), two formalizers that record which
reading they took for every flagged phrase, and a variant formalizer that
took the other reading of the 13 phrases both had read alike. The report
([out/review.md](out/review.md)) certifies 7 requirements, none broken under
the literal reading, and asks 24 questions; the bonus and the cap are among
them, so the false assurance of the study does not recur.
