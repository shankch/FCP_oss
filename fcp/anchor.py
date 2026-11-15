"""Provenance anchoring: locate a verbatim quote in a source document.

Agents are asked for verbatim quotes, never for line numbers.  The tool
computes the minimal line span containing the quote (whitespace-insensitive)
and rejects quotes that do not occur, so provenance cannot be hallucinated.
"""
from __future__ import annotations

import re
from typing import Optional


def _norm(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def anchor(lines: list[str], quote: str) -> Optional[tuple[int, int]]:
    """Return the minimal 1-based inclusive line span containing quote, or None."""
    q = _norm(quote)
    if not q:
        return None
    n = len(lines)
    best = None
    for lo in range(n):
        acc = ''
        for hi in range(lo, n):
            acc = _norm(acc + ' ' + lines[hi])
            if q in acc:
                if best is None or (hi - lo) < (best[1] - best[0]):
                    best = (lo + 1, hi + 1)
                break
            if len(acc) > len(q) + 400 and hi > lo + 12:
                break
    return best
