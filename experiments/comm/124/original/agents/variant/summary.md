I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` rendering of every item says what I meant it to say. `fcp check` is not available to agents. I also wrote a Python script that mirrors the defs and compares them with a separate reference model, but it needed your approval and did not run. So beyond lint, my only check of the defs is tracing by hand: the five spec examples, the example strings in your readings, and leap and non-leap years (1900, 2000, 2001, 2400, 12000). The script is in the scratchpad as `mirror.py` if you want to run it.

**Items: 30**
- **19 properties.** Every guarantee `R-RET-*`, `R-VAL-1`, `R-EMP-1`, `R-FMT-1…5`, `R-MON-1` and `R-DAY-1…3` gets an item. There are two for `R-FMT-4`: one says the year field must parse as an integer, the other rejects year 0. Each spec example (`R-EX-1…5`) is also a property tying its exact input to its output.
- **11 scenarios.** One for each of the five spec examples, plus one for each example in your readings: `'02-29-2001'` invalid, and `'02-29-2000'`, `'3-11-2000'`, `'03-5-2000'`, `'03-11-20'`, `' 03-11-2000 '` valid.
- **No ghost state.** Every item is a direct relation on `date`, `outcome` and `valid`, written with helper expressions (defs) such as `ok` for "this is a valid date".
- **Consistency, by reasoning:** each rule's trigger rules out `ok`, and together the rule triggers cover every invalid string. So the per-rule items agree with `RV-RET-1`/`RV-RET-2` and with each other.
- **Decisions:** I took reading 2 everywhere you instructed it. For the second `yyyy` phrase in `R-FMT-4` (whether year `0000` is allowed) I also chose reading 2. Your `R-VAL-1` reading excludes year 0000 outright, so reading 1 would contradict it.

**Not formalized (4)**
- `R-IF-1`: it is about the function's name and signature, which the adapter fixes, not about behaviour.
- `R-ARG-1`: every argument is a string by how the interface is encoded, so there is nothing to assume.
- `R-FMT-0`: a definition. It is built into the helper expressions and covered by the month, day and calendar items.
- `R-FR-1`: the frame rule `F-ZERO` in `design.yaml` already covers it.

**Problems in the specification**
- **The instructed readings contradict the requirement texts** for `R-FMT-2/3/4/5` ("exactly two/four decimal digits", "no character before or after"). I formalized the instructed readings and said so in each note. As a result, two of `R-FMT-5`'s cases are rejected only because the field fails to parse, not by an item of its own.
- **Rule 2 as written ignores leap years** and nothing in the prompt requires a real calendar date. Your `R-VAL-1` and `R-DAY-3` readings overlap: both reject Feb 29 in a non-leap year.
- **"parses as an integer" is not fully defined.** My choice:
  - only ASCII whitespace counts, an optional `+` must sit right before the digits, and `_` separators are not accepted;
  - the year has no upper limit and uses the Gregorian leap rule extended backwards.

  Code that uses Python's `int()`/`strip()` also accepts `_`, `\x1c`–`\x1f`, `\x85` and `\xa0`, so it would disagree with this set on those inputs.
- **`R-FMT-4` flags two ambiguities with the same phrase `yyyy`.** A decision can only be told apart by its position in the list.
- **Minor points in the prompt itself:**
  - Rule 1 (not empty) is already implied by rule 4.
  - The example `'04-0-2040'` doesn't say which rule makes it invalid: under a strict two-digit reading it fails on format as well as range.