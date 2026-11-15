I wrote `requirements_draft.yaml`, and `fcp anchor` accepted all 9 quotes on the first run ("anchored 9 requirements"). The anchored file is `requirements.yaml`.

**Requirements:**
- **R-FN-1** (non_functional): write a complete implementation of `simplify(x, n)`.
- **R-FN-2** (definition): the function is named `simplify` and takes two parameters, `x` and `n`, in that order.
- **R-OUT-1** (guarantee): when both inputs are valid, the call returns a value and doesn't raise.
- **R-OUT-2** (guarantee): the returned value is "the expression" in simplified form.
- **R-IN-1 / R-IN-2** (assumption): `x` and `n` are each a valid fraction. I split these by argument.
- **R-IN-3 / R-IN-4** (assumption): neither `x` nor `n` has a zero denominator.
- **R-FR-1** (FRAME, guarantee): rule F-ZERO, which says `result` is false unless `outcome` is 0.

There are no scenarios, because the request gives no examples.

**Ambiguities flagged:**
- **The request is underspecified.** Its docstring never says what "the expression" is. The readings I recorded are x·n, x/n, each fraction simplified on its own, or some other expression. It also doesn't say what "simplify" should return: True/False for whether the result is a whole number, a reduced fraction string such as `"1/2"`, or a number or `Fraction`.
- **Contradiction with the adapter.** "Simplify the expression" most naturally means returning a simplified fraction. But frame.md records the returned value as a boolean, and anything else counts as outcome 2. I recorded this on both R-OUT-1 and R-OUT-2. It isn't a spec-versus-spec conflict, because the adapter's types section isn't a frame rule and so has no requirement of its own.
- **What counts as a "valid fraction"?** Readings: positive digit strings in the form `p/q`, a zero numerator allowed, signs, spaces or leading zeros allowed, or a non-string value.
- **"Valid" vs the zero-denominator clause.** Either "valid" already rules out a zero denominator and the clause repeats it, or "valid" only covers the written form.
- **"Zero as denominator".** Either the denominator's value is 0 (so `1/00` is excluded too), or only the literal character `0`.
- **Whole-number results.** Whether a simplified whole number is written as `2` or `2/1`.