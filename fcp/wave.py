"""Compact text waveforms for counterexamples, witnesses and diffs."""
from __future__ import annotations

from typing import Optional


def wave(trace: list[dict], signals: list[str], mark: Optional[int] = None,
         expect: Optional[dict] = None, labels: Optional[dict] = None, max_steps: int = 40) -> str:
    """Render a trace as a table: one row per signal, one column per cycle.

    expect maps (step, signal) -> value the specification requires; such cells
    are shown as actual>expected."""
    if not trace:
        return '(empty trace)'
    steps = trace[-max_steps:]
    off = len(trace) - len(steps)
    cells = {}
    for i, st in enumerate(steps):
        for sname in signals:
            v = st.get(sname)
            txt = '.' if v is None else str(v)
            if expect and (i + off, sname) in expect:
                txt = f'{txt}>{expect[(i + off, sname)]}'
            cells[(i, sname)] = txt
    width = max([len(c) for c in cells.values()] + [len(str(off + len(steps) - 1))]) + 1
    names = [(labels or {}).get(s, s) for s in signals]
    nw = max(len(n) for n in names + ['cycle'])
    head = 'cycle'.ljust(nw) + ' |' + ''.join(
        (('!' if mark is not None and i + off == mark else '') + str(i + off)).rjust(width) for i in range(len(steps)))
    rows = [head, '-' * len(head)]
    for sname, n in zip(signals, names):
        rows.append(n.ljust(nw) + ' |' + ''.join(cells[(i, sname)].rjust(width) for i in range(len(steps))))
    return '\n'.join(rows)
