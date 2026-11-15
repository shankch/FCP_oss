"""Symbolic Python values and paths, shared by the translation (fcp.prove)
and its strings and lists (fcp.seqs)."""
from __future__ import annotations

from dataclasses import dataclass, field


class Untranslatable(Exception):
    pass


@dataclass
class V:
    """A symbolic Python value: a z3 term with its Python type.

    A string or list whose content depends on the arguments is a `seq`: its
    items are guarded slots (guard, value), in order, and it holds the values
    of the slots whose guard is true.  name is its kind ('str' or 'list'),
    t its length if a term for it is known, and dense says that the slots
    that exist are a prefix of the slots.  One character of such a string is
    a `chr`: t is its code."""
    t: object
    ty: str                      # int | bool | tuple | dict | none | str | ans | type | module | iface | stub
    #                              | chr | seq | undef
    items: tuple = ()            # tuple elements, dict values, a seq's slots
    name: str = ''               # a type's or module's name, a string's text, a stub's method, a seq's kind
    keys: tuple = ()             # dict keys (constants)
    dense: bool = False


@dataclass
class State:
    """One path: its condition, its variables, the calls it made on the
    interface so far, each (op, argument terms, answer term, object number),
    the answers it took, and what it did to the objects and files it sees:
    objects made (numbered from 1), the ones closed, the files that exist,
    each object's path.  The last four are concrete: paths and modes are
    literals in the code this translates."""
    cond: object
    env: dict = field(default_factory=dict)
    events: tuple = ()
    n_ans: int = 0
    made: int = 0
    closed: frozenset = frozenset()
    exists: frozenset = frozenset()
    paths: tuple = ()

    def fork(self, cond) -> 'State':
        return State(cond, dict(self.env), self.events, self.n_ans, self.made, self.closed, self.exists, self.paths)

    def same_world(self, other: 'State') -> bool:
        return (self.n_ans, self.made, self.closed, self.exists, self.paths) == \
            (other.n_ans, other.made, other.closed, other.exists, other.paths)
