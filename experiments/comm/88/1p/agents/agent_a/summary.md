I wrote `formal/agent_a.yaml`. `fcp lint` reports no errors, and I read back `fcp explain`: each item says what I intended.

**Items: 5 properties, no assumptions, no scenarios, no don't-cares.**
- **RA-RET-1:** every call returns a list (outcome 0), including the empty list.
- **RA-RET-2:** when a list is returned, it holds exactly the argument's elements (same length, same count of each value).
- **RA-RET-3:** when a list is returned, it is sorted, either ascending or descending.
- **RA-ORD-1:** if `array[0] + array[last]` is odd, the result is the argument's elements in ascending order, duplicates kept.
- **RA-ORD-2:** if that sum is even, the result is the argument's elements sorted in either direction.

**Requirements left unformalized (7), and why:**
- **R-IF-1, R-IF-2:** these are about the form of the code (a completed function body, the name and parameter). design.yaml already fixes the signature, and no signal carries them.
- **R-IN-1:** I took reading 1: any list counts, including the empty one. The interface only carries unsigned values from 0 to 255, so every trace already meets it and an assumption would constrain nothing.
- **R-RET-4 (argument left unchanged) and R-RET-5 (result is a new object):** no signal shows the argument after the call or which object was returned, so neither can be checked.
- **R-KEY-1:** this is a definition. It is written as the def `key` and covered by RA-ORD-1 and RA-ORD-2.
- **R-FR-1:** the frame item F-EMPTY already implements it and is added to every set, so it is covered by F-EMPTY.

**Readings I took:** reading 1 everywhere except three places. For "or sort it" I took reading 2: sorted, direction unstated. For "you will sort the given array" and "a copy of the given array after sorting" I took reading 2: the argument itself is sorted. That is the most literal wording, but it is my judgement call, and neither choice changes anything a property can check.

**Problems in the specification:**
1. **The prompt is cut off.** It stops at "or sort it" and never states the condition or the direction for the even-sum case. I didn't assume descending. So for an even sum the expected output isn't fully determined: both ascending and descending results pass. The determinacy check will flag this.
2. **The empty list has no defined sum.** It has no first or last value, yet the text still says to return a copy. Under my reading the function must return `[]`, so code that raises `IndexError` on an empty list fails RA-RET-1. In FCP-PL the sum for an empty list works out to 0, which only allows `[]`.
3. **Copy versus in place.** "Return a copy" conflicts with "you will sort the given array". Read literally, the text sorts the argument, which contradicts R-RET-4's own wording that the argument is unchanged. The interface can't show either way.
4. **"First index value, last index value" is unclear.** It could mean the values at those positions or the index numbers themselves. Taking the values before or after sorting also gives different parity, for example `[2,1,4]`: 6 before sorting, 5 after. The one-element case doesn't matter, because one element is sorted in both directions.
5. **Redundancy.** Under the readings I chose, RA-ORD-2 follows from RA-RET-2 and RA-RET-3 together, so it adds nothing on its own.