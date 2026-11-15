"""Formalization fault operators: mechanical models of typical mistakes an AI
(or a person) makes when turning prose into properties.  Each operator takes
one property of a formalization set and returns a mutated copy, or None if it
does not apply."""
from __future__ import annotations

import copy

from fcp.lang import Node, parse, unparse


def _conj(n: Node) -> list[Node]:
    if n.op == 'bin' and n.val == '&&':
        return _conj(n.args[0]) + _conj(n.args[1])
    return [n]


def _and(parts: list[Node]) -> str:
    return ' && '.join(f'({unparse(p)})' if p.op in ('bin', 'ite') and p.val not in ('&&',) else unparse(p)
                       for p in parts)


def trigger_reset_polarity(p: dict) -> dict | None:
    """Antecedent written with the wrong reset polarity: never true outside reset (vacuous)."""
    if p.get('pattern') in ('implies', 'next', 'within', 'hold_until'):
        q = copy.deepcopy(p)
        q['args']['trigger'] = f'({q["args"]["trigger"]}) && rst_active'
        return q
    return None


def drop_conjunct(p: dict) -> dict | None:
    """A conjunct of the consequent is forgotten (too weak)."""
    key = 'cond' if p.get('pattern') in ('implies', 'next', 'invariant', 'after_reset', 'within') else None
    src = p.get('expr') if 'expr' in p else (p['args'].get(key) if key else None)
    if src is None:
        return None
    parts = _conj(parse(str(src)))
    if len(parts) < 2:
        return None
    q = copy.deepcopy(p)
    new = _and(parts[:-1])
    if 'expr' in q:
        q['expr'] = new
    else:
        q['args'][key] = new
    return q


def placeholder(p: dict) -> dict | None:
    """Consequent replaced by a placeholder that always holds (tautology)."""
    q = copy.deepcopy(p)
    if 'expr' in q:
        q['expr'] = f'({q["expr"]}) || true'
        return q
    if q.get('pattern') in ('implies', 'next', 'invariant', 'after_reset'):
        q['args']['cond'] = f'({q["args"]["cond"]}) || true'
        return q
    return None


def loosen_bound(p: dict) -> dict | None:
    """Response window or wait bound one cycle too generous (too weak)."""
    q = copy.deepcopy(p)
    if q.get('pattern') == 'within':
        q['args']['max'] = f'({q["args"]["max"]}) + 1'
        return q
    if q.get('pattern') == 'bounded_wait':
        q['args']['max'] = f'({q["args"]["max"]}) + 1'
        return q
    if q.get('pattern') == 'inorder':
        q['args']['capacity'] = f'({q["args"]["capacity"]}) + 1'
        return q
    return None


def tighten_bound(p: dict) -> dict | None:
    """Window one cycle too strict (too strong: false alarm)."""
    q = copy.deepcopy(p)
    if q.get('pattern') in ('within', 'bounded_wait'):
        q['args']['max'] = f'({q["args"]["max"]}) - 1'
        return q
    return None


def same_cycle(p: dict) -> dict | None:
    """Next-cycle obligation checked in the same cycle (timing error)."""
    if p.get('pattern') == 'next':
        q = copy.deepcopy(p)
        q['pattern'] = 'implies'
        return q
    return None


OPERATORS = {
    'reset-polarity-trigger': trigger_reset_polarity,
    'dropped-conjunct': drop_conjunct,
    'placeholder-consequent': placeholder,
    'loose-bound': loosen_bound,
    'tight-bound': tighten_bound,
    'same-cycle': same_cycle,
}


def masking_assumption(fs: dict, p: dict) -> dict | None:
    """An 'environment assumption' that excludes the property's trigger
    situation (the classic way an AI makes a failing proof pass)."""
    trig = None
    if p.get('pattern') in ('implies', 'next', 'within', 'hold_until'):
        trig = p['args']['trigger']
    if trig is None:
        return None
    return {'id': p['id'] + '-MASK', 'req': p['req'], 'expr': f'!({trig})',
            'note': 'injected masking assumption'}
