I wrote `formal/agent_a.yaml`. `fcp lint` reports it clean, and the `fcp explain` English output matches what I meant for every item. The main finding is that the spec contradicts itself: read literally, its main statement makes the function always return True, which two of its three examples deny.

**Items: 8**, plus the adapter's frame rule F-ZERO, which is added to every set automatically.
- **1 assumption:** RA-IN-1 says n is between 0 and 65,535. The 16-bit input already guarantees this, so it adds no real constraint; it only records the requirement.
- **4 properties:**
  - RA-FN-1: every call returns a real True or False (`outcome == 0`).
  - RA-FN-2: whenever the call returns, the result is True.
  - RA-EX-1, RA-EX-2, RA-EX-3: candidate(4) and candidate(6) return False, and candidate(8) returns True.
- **3 scenarios:** RA-EX-1-S to RA-EX-3-S say each example call is possible. Since the function is deterministic and keeps no state, I also stated each example as a property so it applies to every such call.
- **11 decisions** cover every phrase flagged as ambiguous. I took the most literal reading each time.

**Left unformalized (3):**
- **R-IF-1** ("complete, not a stub"): this is about the code, not about a trace of calls. The part you can observe is covered by RA-FN-1 and RA-FN-2, since a stub raises or returns None.
- **R-IF-2** (the function name and its one parameter): the property language can't express this. It is fixed by the `function` section of design.yaml.
- **R-FR-1**: this is frame rule F-ZERO, which the adapter already adds to every set. It is marked `covered_by: [F-ZERO]` rather than restated.

**Problems in the specification:**
1. **The main statement contradicts the examples.** "Can be written as the sum of 4 numbers" puts no limit on the numbers. Read that way, every n qualifies (n + 0 + 0 + 0), so the function always returns True. That contradicts candidate(4) == False and candidate(6) == False. The other common readings, non-negative or positive integers, also make 4 = 1+1+1+1 and 6 = 1+1+2+2 qualify. I did not repair this: RA-FN-2 conflicts with RA-EX-1 and RA-EX-2, and FCP's consistency check should report it. Only narrower readings that the text doesn't state fit all three examples, such as "positive even numbers" (n even and n ≥ 8) or "numbers of at least 2". The prompt looks like an abbreviated version of a statement that originally had such a qualifier.
2. **"Distinct numbers" would break the third example.** The smallest sum of four distinct positive integers is 10, so candidate(8) == True would be false.
3. **Python's `==` makes "returns a bool" unclear.** In Python, `0 == False` is true, so the examples are also met by a function that returns 0 or 1. I required the actual values True and False. The looser reading can't be checked exactly anyway, because the trace doesn't record the value when the function returns a non-bool (outcome 2).