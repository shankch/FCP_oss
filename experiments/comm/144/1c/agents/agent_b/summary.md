I wrote `formal/agent_b.yaml`. `fcp lint` reports it clean, and I read the `fcp explain` output back: every item says what I meant it to. I also wrote a script to check my string-parsing formulas against Python's exact `Fraction`, but running it needed your approval and wasn't run. I checked the key cases by hand instead ("7/10", "05/3", "999999/1").

**Items: 15 formal items, plus 18 decisions (one per flagged phrase)**
- **3 properties.** On any valid call:
  - RB-RES-1: if x·n is a whole number, it returns True.
  - RB-RES-2: if x·n is not a whole number, it returns False.
  - RB-RES-3: it always returns a bool (no exception, no hang, no other type).
- **7 assumptions** (RB-IN-2, -3, -4, -5, mostly one each for x and n). Each argument is digits, one `/`, digits; both numbers are at least 1; leading zeros are allowed.
- **3 scenarios** (RB-EX-1..3), one for each example, read literally.
- **2 don't-cares** (RB-IN-6): `outcome` and `result` are unconstrained when an input is invalid.

**How the model works.** The function keeps nothing between calls, so the reference model has no state carried between calls. Instead, named formulas read the numerator and denominator values out of each string, decide whether it is valid, and build the exact product. Both outputs are checked against that.

The property language has no `%` with a variable divisor. So "whole number" is written with one universally quantified constant `q` from 0 to 999998000001 (the largest possible product): whole means `a·c == q·(b·d)`, and not whole means `q·(b·d) < a·c < (q+1)·(b·d)`.

That range is fine for a solver. But if a checker tries each value of `q` on recorded runs, it would be very slow; I couldn't confirm which way the tool works.

**Requirements left unformalized (5)**
- **R-IF-1:** the function's name and argument order. That's set by the `function` section of `design.yaml`, not by anything in the trace.
- **R-OP-1:** I read "simplify the expression" as a statement of purpose, so it's covered by RB-RES-1/2/3.
- **R-IN-1:** being a string comes from the interface, and "a fraction" is the format already covered by RB-IN-2/3/4.
- **R-FR-1, R-FR-2:** these are the frame rules F-ZERO and F-CODE, which are added to every set automatically; `frame.md` says not to restate them.

**Problems in the specification**
1. **All three examples contradict the stated rule.** 1/5·5/1 = 1 is whole but the example says False; 1/3 and 7/2 are not whole but the examples say True. It looks like True and False were swapped. I took the most literal reading of each sentence: the rule as stated (reading 1) and the examples as written (reading 2). So RB-EX-1 can't happen alongside RB-RES-1, and RB-EX-2/3 can't happen alongside RB-RES-2. I left that visible rather than fixing it. No implementation can satisfy both the rule and the examples.
2. **"Simplify the expression" doesn't match "returns True or False".**
3. **"Do not have zero as denominator" is redundant if "positive" applies to both numbers, or contradicts it if zero numerators are meant to be allowed.** I treated it as a restatement.
4. **"False otherwise" could be read as covering invalid inputs too,** which would contradict "you can assume valid fractions". I limited it to valid calls.
5. **"Evaluates to" leaves floating-point evaluation open.** For example, 1/49·49/1 comes out as 0.9999999999999999 in floats. I used exact arithmetic.