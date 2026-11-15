# Request: parse a duration

Write a Python function for our scheduling app:

    def parse_duration(text: str) -> int:

It converts a duration such as `"1h30m"` or `"45s"` into a number of seconds.

1. A duration is one or more parts, each a whole number followed by a unit: `h` for hours, `m` for minutes, `s` for seconds.
2. Each unit appears at most once, in the order h, m, s.
3. Every number is between 1 and 99.
4. Spaces are not allowed.
5. Raise ValueError for anything else, including an empty string.
6. A duration is never longer than one day.

Example: `parse_duration("1h30m")` returns `5400`.
