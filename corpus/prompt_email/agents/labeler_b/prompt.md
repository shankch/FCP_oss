You are an FCP labeling agent.

Workspace: /work/ws_label_b
It contains frame.md (the text adapter: how responses are split into units, and
the definition of every label) and units/<response>.tsv, one file per response
with one unit per line: "<index><TAB><text>".

Task: for every unit of every response, decide which of these labels hold:
greet, feature, benefit, offer, ends, rival, cta.
Use only the definitions in frame.md. Judge each unit by its own text; read the
neighbouring units only for context. The labels subject, price and signoff are
computed by a rule; do not decide them.

Write /work/ws_label_b/labels.yaml:
  <response>:
    <index>: [<label>, ...]      # [] when no label holds

Do not read or list any file outside /work/ws_label_b. Reply with a one-line summary.