You are an FCP adapter agent.

Workspace: /work/review_demo/out/ws_adapter
It contains spec.md (a request someone gave an AI coding assistant),
signature.txt (the signature of the code the assistant wrote, without its
body), docs/IR_spec.md (the FCP IR), and examples/, the design.yaml and
frame.md of checked designs: a function on integers (code_checkout), a
function on strings (code_mask), an object (code_limit) and a change to
existing code (code_change).

Task: write /work/review_demo/out/ws_adapter/design.yaml and /work/review_demo/out/ws_adapter/frame.md, which say how calls of this
code become the cycles of a trace, as in the examples:
- one input signal per argument and one output signal per returned value,
  each wide enough for every value the request allows and the values just
  outside it (a string or list is a signal with a `length`); an `outcome`
  signal coded as in the examples, with the exceptions the request names;
- the `function` section (name, args, returns, outcome; `class` for a
  method of an object; a `scope` with the values the request talks about);
- docs: SPEC (spec.md) and FRAME (frame.md); frame rules for outputs that are
  zero unless the call returned, as in the examples;
- frame.md explains the encoding to someone who will formalize the request.
Describe the interface only: do not restate or interpret the request's rules.

Validate with `/repo/bin/fcp lint /work/review_demo/out/ws_adapter` until it reports no errors. Work only inside
/work/review_demo/out/ws_adapter. Reply with a one-paragraph summary.