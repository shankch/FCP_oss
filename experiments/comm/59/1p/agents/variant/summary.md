I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` output reads the way I intended for every item. I also wrote a Python script to check the number-theory definitions against brute force over 0..65535, but running it needed approval and it did not run. I checked those definitions by hand only.

**7 formal items**
- **1 assumption, RV-ENV-2:** any call with n > 1 that is not prime has n = p^k, with p prime and k ≥ 2. Calls whose n has several distinct prime factors are outside the contract, as your reading of "is not a prime" says.
- **5 properties:**
  - **RV-RET-1:** calls in the contract (n > 1, not prime) must not raise an exception and must finish.
  - **RV-RET-2, RV-RET-3, RV-RET-4:** when such a call returns an integer from 0 to 65,535, that value divides n, is prime, and is a prime factor of n (RV-RET-4).
  - **RV-ENV-3-RET:** when n ≤ 1 or n is prime, the call must return an integer from 0 to 65,535 (outcome 0).
- **1 don't-care, RV-ENV-3-VAL:** the returned value is free when n ≤ 1 or n is prime.
- **Decisions recorded:** R-ENV-2 reading 2, R-ENV-3 reading 2, R-RET-1 reading 2, R-RET-4 reading 1. Each item's note says which of your readings affect it.

**Requirements left unformalized (4)**
- **R-IF-1:** this is about the interface (the function's name and argument), not behaviour. The function declaration in `design.yaml` already fixes it.
- **R-DEF-1:** this is a definition. The prime tests in the shared definitions carry it, and it lists the items that use them.
- **R-ENV-1:** your reading of "Assume" means calls with n ≤ 1 must still return an integer. So "n > 1" can't be an environment assumption: it would make RV-ENV-3-RET vacuous for those calls. Instead it is the precondition of RV-RET-1..4 and the trigger of the two RV-ENV-3 items. For the same reason, the words "not a prime" in R-ENV-2 are a precondition, not part of the assumption.
- **R-FR-1:** frame rule F-ZERO is added to every set automatically.

**Problems in the specification**
1. **"The prime factor" assumes there is only one,** but "not a prime" allows n like 6 = 2·3. Your readings settle this (n is a prime power, and any prime factor is accepted). As a result, RV-RET-4 adds nothing beyond RV-RET-2 and RV-RET-3 combined.
2. **The rules are stricter outside the contract than inside it.** Inside, a float such as 3.0 is acceptable (R-RET-1). Outside, for n ≤ 1 or prime n, only an integer is acceptable (R-ENV-3).
3. **The trace encoding can't express either reading exactly.** Outcome 2 covers floats, negative or oversized integers, and non-numbers alike.
   - RV-RET-1 only rules out an exception or no answer. A call in the contract that returns `None` therefore passes, and the value of any outcome-2 return goes unchecked.
   - RV-ENV-3-RET requires outcome 0. So it also rejects something like `-1` for n = 1, which your reading allows, rather than letting `None` through.
4. **FCP-PL's `%` only accepts a constant divisor.** "Divides" and "prime" are therefore written as bounded searches over values up to 255. They are exact only because n and the returned value fit in 16 bits.
5. **Calls with several distinct prime factors are excluded by an assumption.** Under assume-guarantee semantics, once such a call appears in a trace, nothing after it is checked. That doesn't matter if the checker treats each call of this stateless function separately, but I haven't confirmed that it does.