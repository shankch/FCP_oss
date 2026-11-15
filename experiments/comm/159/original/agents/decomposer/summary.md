I split the prompt into 21 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`, filling in the line numbers.

**Breakdown (20 from the prompt, 1 from the frame):**
- **Deliverable (R-FN-1, R-FN-2), non-functional:** finish the function, named `eat`, with arguments `(number, need, remaining)` in that order.
- **Argument meanings (R-DEF-1 to R-DEF-3), definitions:** each argument is an integer, and what it counts.
- **Return value (R-RET-1 to R-RET-3):** a guarantee that it returns a list of exactly two integers, plus definitions of the two elements: total eaten (including `number`) and carrots left in stock.
- **How much is eaten (R-EAT-1 to R-EAT-5), guarantees:**
  - If `need <= remaining`: first element is `number+need`, second is `remaining-need`.
  - If `remaining < need`: first element is `number+remaining`, second is `0`.
  - "still hungry" (R-EAT-5), read as something you can check: the first element is less than `number+need`.
- **Input limits (R-IN-1 to R-IN-3), assumptions:** each argument is between 0 and 1000.
- **Examples (R-EX-1 to R-EX-4), scenarios.**
- **Frame rule (R-FR-1, F-ZERO), guarantee:** `eaten` and `left` are 0 unless `outcome` is 0.

**Ambiguities flagged:**
- **`need`:** extra carrots on top of `number`, or the day's total. The total reading would contradict the examples.
- **"need to eat more carrots":** eat exactly `need`, or at least `need`.
- **"total number of eaten carrots":** whether it includes `number`.
- **"carrots left":** left in stock, or still left to eat.
- **"array":** a list, a list or tuple, or any array-like value.
- **"not enough":** `<` or `<=`. Both give the same output.
- **"Constrain":** a precondition with out-of-range behaviour unspecified, an instruction to reject out-of-range values, or a rule that applies to all values. This one matters because design.yaml's scope tests the value 1001.

**Possible contradiction:** if "will still be hungry" means the result must report hunger, that clashes with returning exactly two elements. I recorded it as an ambiguity on both R-EAT-5 and R-RET-1. The four examples agree with the natural reading.

I didn't make requirements from the opening narrative clause (R-DEF-1 already covers it), "Have fun :)" or the section headings.