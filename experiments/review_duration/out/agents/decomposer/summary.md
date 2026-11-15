I split the request into 17 requirements and anchored them. `fcp anchor` accepted every quote on the first run, so no fixes were needed, and it wrote `requirements.yaml` with the line numbers filled in.

**The requirements**
- **Deliverable and interface (3):** it must be a Python function (`R-NF-1`); the name and parameter are `parse_duration(text: str)` (`R-IF-1`); and whenever it returns, the result is an `int` (`R-IF-2`).
- **Conversion (1):** `R-CONV-1` says every valid duration converts to 3600·h + 60·m + s seconds.
- **Format (6 plus `R-NUM-1`):** rule 1 became three definitions: one or more parts, each a whole number followed by a unit, and the units are h/m/s. Rules 2–4 became separate requirements, each saying `ValueError` is raised: a unit used twice (`R-FMT-4`), units out of order (`R-FMT-5`), a number outside 1–99 (`R-NUM-1`), and spaces (`R-FMT-6`).
- **Errors (2):** `ValueError` for anything else (`R-ERR-1`), and specifically for the empty string (`R-ERR-2`).
- **Upper bound (1):** `R-MAX-1`, never longer than one day.
- **Examples (2):** `"1h30m"` → 5400 and `"45s"` → 45, both as scenarios.
- **Frame rule (1):** `R-FR-1`, which `seconds` is 0 unless `outcome` is 0. `design.yaml` already refers to it by that ID.

**The contradiction**
Rules 1–4 allow up to 99 hours (`"99h99m99s"` is 362,439 seconds), but rule 6 says no duration is longer than one day (86,400 seconds). So `"25h"` can't both convert to 90,000 and be rejected. I recorded this on `R-NUM-1`, `R-MAX-1` and `R-CONV-1`.

Rule 6 also comes after "Raise ValueError for anything else", so it's unclear whether that rule covers it. I gave `R-MAX-1` three readings:
- it's a validity rule, so longer inputs raise `ValueError`;
- it's an assumption about callers, so longer inputs are left unspecified;
- it only caps the result, so the function could clamp to 86,400.

The draft uses the first reading, and `R-ERR-1` notes the same scope question.

**Other ambiguities I flagged**
- **"between 1 and 99":** whether it includes 1 and 99 or not.
- **"Every number":** one range for every unit, or minutes and seconds below 60 as on a clock (is `"1h90m"` valid?).
- **"whole number":** whether leading zeros are allowed (`"01h"`, `"001h"`), and whether a sign is (`"+1h"`, which Python `int()` accepts).
- **Uppercase units:** whether `"1H30M"` is valid.
- **"in the order h, m, s":** whether a unit can be skipped, as in `"1h5s"`.
- **"Spaces":** whether this means only the space character or all whitespace, and whether surrounding whitespace could be trimmed instead of rejected.

I added `depends` links (allowed by the format, though not in your template) so the format rules that raise errors point to `R-ERR-1`, and `R-CONV-1` points to the format rules.

Files are in `ws_decomposer`:
- `requirements_draft.yaml`
- `requirements.yaml`