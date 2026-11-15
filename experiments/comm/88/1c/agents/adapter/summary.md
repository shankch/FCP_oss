I wrote `design.yaml`, `frame.md` and `requirements.yaml` for `sort_array(array)`, and `fcp lint` now reports `lint: clean`.

Each call of `sort_array` is one cycle of the trace, with no memory between calls. The argument becomes the input signal `array`, a list of at most 8 numbers from 0 to 255. Each sample array in the request has at most 7 numbers from 0 to 6, so these limits cover them plus values just outside. The returned list becomes the output signal `result`, with the same limits. `outcome` is 2 bits:
- **0:** it returned a list that fits.
- **1:** it raised an exception or did not finish.
- **2:** it returned anything else.

`raises` is `[]` because the request names no exception.

The `function` section declares `array` and `result` as type `list`. Its `scope` uses the numbers 0–6 as elements, 3000 random lists, and the request's four sample arrays as values. There is one frame rule, F-EMPTY (`outcome != 0 -> len(result) == 0`). It cites R-FR-1, a definition that quotes `frame.md` line 50; `fcp anchor` filled in that line number from `draft.yaml`, which is still in the workspace. `frame.md` explains the calls, how lists are written in FCP-PL, the inputs and outputs, and that negative numbers, longer lists and larger values are not part of the trace. It also notes that no signal shows the list after the call, so the trace can't tell whether the function changed its argument.

I set the design name to `review` to match the existing `requirements.yaml`. Lint only checks the files: it accepted the list-of-lists `values` in the scope, but I haven't run anything that uses that scope.