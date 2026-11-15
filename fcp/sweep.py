"""Equivalence sweeping for proof goals.

A goal that sets two computations of one quantity side by side (a checksum
as the code computes it and as the requirement defines it) is hard for an
SMT solver as a whole and easy piece by piece: the two sides agree on many
intermediate values, and each agreement follows in a step from the ones
below it.  Sweeping finds those agreements and proves them, from the leaves
up:

  1. every subterm of the goal is evaluated on sample inputs (a generated
     Python function, one line per shared subterm);
  2. subterms of one sort with the same value on every sample are
     candidates: equal to each other, or to a constant;
  3. in dependency order, each candidate is put to z3 under the assumptions
     on the inputs, on terms in which the agreements already proved are
     substituted.  UNSAT merges the subterm into its representative; a model
     is one more sample, which splits the candidates it tells apart; a
     timeout leaves the subterm as it is.

Nothing is merged without a proof, so the goal that comes back is
equivalent to the one that went in under the assumptions, whatever the
samples were: they only decide what is tried.
"""
from __future__ import annotations

import time


class NoSim(Exception):
    """A term the generated evaluator has no line for."""


def order(roots: list) -> list:
    """Every subterm of the roots once, children before parents."""
    seen: set = set()
    out: list = []
    stack = [(r, False) for r in reversed(roots)]
    while stack:
        e, done = stack.pop()
        if done:
            out.append(e)
            continue
        k = e.get_id()
        if k in seen:
            continue
        seen.add(k)
        stack.append((e, True))
        for c in e.children():
            if c.get_id() not in seen:
                stack.append((c, False))
    return out


def variables(z3, term) -> set:
    """The ids of the free variables of a term."""
    return {e.get_id() for e in order([term])
            if z3.is_const(e) and e.decl().kind() == z3.Z3_OP_UNINTERPRETED}


def _is(z3, t, v: int, memo: dict):
    """t == v as a formula of the tests of t, an if-tree over integers."""
    key = t.get_id()
    if key not in memo:
        if z3.is_int_value(t):
            memo[key] = z3.BoolVal(t.as_long() == v)
        elif z3.is_app(t) and t.decl().kind() == z3.Z3_OP_ITE:
            c, a, b = t.arg(0), _is(z3, t.arg(1), v, memo), _is(z3, t.arg(2), v, memo)
            if z3.is_false(a):
                memo[key] = b if z3.is_false(b) else z3.Not(c) if z3.is_true(b) else z3.And(z3.Not(c), b)
            elif z3.is_false(b):
                memo[key] = c if z3.is_true(a) else z3.And(c, a)
            elif z3.is_true(a):
                memo[key] = a if z3.is_true(b) else z3.Or(c, b)
            elif z3.is_true(b):
                memo[key] = z3.Or(z3.Not(c), a)
            else:
                memo[key] = z3.If(c, a, b)
        else:
            memo[key] = t == v
    return memo[key]


def conjuncts(z3, g) -> list:
    """Formulas whose conjunction is g: conjunctions are opened, with the
    negations of disjunctions and implications, and an if-tree compared
    with a constant becomes the formula of its tests."""
    out, stack, memo = [], [g], {}
    while stack:
        e = stack.pop()
        k = e.decl().kind()
        if k == z3.Z3_OP_AND:
            stack.extend(reversed(e.children()))
            continue
        neg = k == z3.Z3_OP_NOT
        c = e.arg(0) if neg else e
        kc = c.decl().kind()
        if kc in (z3.Z3_OP_AND, z3.Z3_OP_OR):                             # And(x), Or(x, False): x
            unit = z3.is_true if kc == z3.Z3_OP_AND else z3.is_false
            rest = [x for x in c.children() if not unit(x)]
            if len(rest) == 1:
                stack.append(z3.Not(rest[0]) if neg else rest[0])
                continue
        if neg and kc == z3.Z3_OP_OR:
            stack.extend(z3.Not(x) for x in reversed(c.children()))
            continue
        if neg and kc == z3.Z3_OP_IMPLIES:
            stack.extend([z3.Not(c.arg(1)), c.arg(0)])
            continue
        if neg and kc == z3.Z3_OP_NOT:
            stack.append(c.arg(0))
            continue
        if kc == z3.Z3_OP_EQ:
            a, b = c.arg(0), c.arg(1)
            if z3.is_int_value(a):
                a, b = b, a
            if z3.is_int_value(b) and z3.is_app(a) and a.decl().kind() == z3.Z3_OP_ITE:
                f = _is(z3, a, b.as_long(), {})
                stack.append(z3.Not(f) if neg else f)
                continue
        if not z3.is_true(e):
            out.append(e)
    return out


def _div(a, b):
    """z3's integer division: the remainder is never negative."""
    if b == 0:
        return 0
    return a // b if b > 0 else -(a // -b)


def _mod(a, b):
    return a % abs(b) if b else 0


def simulator(z3, nodes: list, inputs: list):
    """f(values of the inputs) -> the value of every node, in order."""
    pos = {a.get_id(): j for j, a in enumerate(inputs)}
    idx: dict = {}
    cmp = {z3.Z3_OP_LE: '<=', z3.Z3_OP_LT: '<', z3.Z3_OP_GE: '>=', z3.Z3_OP_GT: '>', z3.Z3_OP_EQ: '==',
           z3.Z3_OP_IFF: '=='}
    fold = {z3.Z3_OP_ADD: ' + ', z3.Z3_OP_SUB: ' - ', z3.Z3_OP_MUL: ' * ', z3.Z3_OP_AND: ' and ',
            z3.Z3_OP_OR: ' or '}
    lines = []
    for i, e in enumerate(nodes):
        key = e.get_id()
        idx[key] = i
        if key in pos:
            rhs = f'x[{pos[key]}]'
        elif z3.is_int_value(e):
            rhs = str(e.as_long())
        elif z3.is_true(e):
            rhs = 'True'
        elif z3.is_false(e):
            rhs = 'False'
        elif not z3.is_app(e) or not e.num_args():
            raise NoSim(str(e)[:60])
        else:
            ch = [f't{idx[c.get_id()]}' for c in e.children()]
            k = e.decl().kind()
            if k == z3.Z3_OP_ITE:
                rhs = f'{ch[1]} if {ch[0]} else {ch[2]}'
            elif k in cmp and len(ch) == 2:
                rhs = f'{ch[0]} {cmp[k]} {ch[1]}'
            elif k == z3.Z3_OP_SUB and len(ch) == 1:
                rhs = f'-{ch[0]}'
            elif k in fold:
                rhs = fold[k].join(ch)
            elif k == z3.Z3_OP_UMINUS:
                rhs = f'-{ch[0]}'
            elif k == z3.Z3_OP_NOT:
                rhs = f'not {ch[0]}'
            elif k == z3.Z3_OP_IMPLIES:
                rhs = f'(not {ch[0]}) or {ch[1]}'
            elif k == z3.Z3_OP_XOR and len(ch) == 2:
                rhs = f'{ch[0]} != {ch[1]}'
            elif k == z3.Z3_OP_DISTINCT:
                rhs = f'len({{{", ".join(ch)}}}) == {len(ch)}'
            elif k == z3.Z3_OP_IDIV:
                rhs = f'_div({ch[0]}, {ch[1]})'
            elif k == z3.Z3_OP_MOD:
                rhs = f'_mod({ch[0]}, {ch[1]})'
            else:
                raise NoSim(e.decl().name())
        lines.append(f'    t{i} = {rhs}')
    src = 'def f(x):\n' + '\n'.join(lines) + f'\n    return [{", ".join(f"t{i}" for i in range(len(nodes)))}]\n'
    env = {'_div': _div, '_mod': _mod}
    exec(compile(src, '<fcp.sweep>', 'exec'), env)
    return env['f']


def sweep(z3, roots: list, inputs: list, assume: list, samples: list, budget: float = 120.0,
          each: int = 500, refine: int = 200, tries: int = 3, trace: bool = False) -> tuple[list, dict]:
    """The roots with every agreement between their subterms that z3 proves
    under `assume` substituted, and what was done.  `inputs` are the free
    variables, `samples` values for them (each satisfying `assume`); `each`
    is the time one candidate gets, in milliseconds, `budget` all of them, in
    seconds; at most `refine` models are taken as new samples, and a subterm
    is put to z3 at most `tries` times."""
    t0 = time.time()
    stats = {'nodes': 0, 'merged': 0, 'constant': 0, 'syntactic': 0, 'refuted': 0, 'unknown': 0, 'checks': 0}
    hard: list = []
    nodes = order(roots)
    stats['nodes'] = len(nodes)
    try:
        f = simulator(z3, nodes, inputs)
        cols = [f(list(s)) for s in samples]
    except (NoSim, RecursionError, ZeroDivisionError, TypeError, IndexError) as e:
        stats['skipped'] = f'{type(e).__name__}: {e}'
        return roots, stats
    base = list(zip(*cols)) if cols else [()] * len(nodes)       # one tuple of values per node
    extra: list = []                                              # the models found on the way, as samples

    def key(i: int):
        return (base[i], tuple(c[i] for c in extra))

    sol = z3.Solver()
    sol.set('timeout', each)
    sol.add(*assume)
    new: list = [None] * len(nodes)
    idx = {e.get_id(): i for i, e in enumerate(nodes)}
    reps: list[int] = []                                          # nodes that stand for themselves
    table: dict = {}

    def differ(a, b) -> str:
        stats['checks'] += 1
        sol.push()
        sol.add(a != b)
        r = sol.check()
        out = 'same' if r == z3.unsat else 'unknown'
        if r == z3.sat:
            out = 'differ'
            if len(extra) < refine:
                md = sol.model()
                xs = []
                for v in inputs:
                    y = md.eval(v, model_completion=True)
                    xs.append(z3.is_true(y) if z3.is_bool(v) else y.as_long())
                extra.append(f(xs))
                table.clear()
                for j in reps:
                    table.setdefault((nodes[j].sort().kind(), key(j)), []).append(j)
        sol.pop()
        return out

    for i, e in enumerate(nodes):
        kids = e.children()
        if not kids:
            new[i] = e
            continue
        ks = [new[idx[c.get_id()]] for c in kids]
        new[i] = e if all(a.eq(b) for a, b in zip(ks, kids)) else e.update(*ks)
        sk = e.sort().kind()
        if sk not in (z3.Z3_BOOL_SORT, z3.Z3_INT_SORT) or time.time() - t0 > budget:
            continue
        done = False
        tried: set = set()
        while len(tried) < tries:
            sig = key(i)
            vals = set(sig[0]) | set(sig[1])
            if len(vals) == 1 and -1 not in tried:                # one value on every sample: a constant?
                tried.add(-1)
                v = next(iter(vals))
                c = z3.BoolVal(bool(v)) if sk == z3.Z3_BOOL_SORT else z3.IntVal(int(v))
                r = differ(new[i], c)
                if r == 'same':
                    new[i] = c
                    stats['constant'] += 1
                    done = True
                    break
                stats['refuted' if r == 'differ' else 'unknown'] += 1
                if r == 'unknown' and trace:
                    hard.append((i, 'constant', str(v)))
                continue                                          # a model may have changed the signature
            j = next((j for j in table.get((sk, sig), []) if j not in tried), None)
            if j is None:
                break
            tried.add(j)
            if new[i].eq(new[j]):
                stats['syntactic'] += 1
                done = True
                break
            r = differ(new[i], new[j])
            if r == 'same':
                new[i] = new[j]
                stats['merged'] += 1
                done = True
                break
            stats['refuted' if r == 'differ' else 'unknown'] += 1
            if r == 'unknown' and trace:
                hard.append((i, j, None))
        if not done:
            reps.append(i)
            table.setdefault((sk, key(i)), []).append(i)
    stats['samples'] = len(samples) + len(extra)
    if trace:
        stats['hard'] = [(i, j, str(nodes[i])[:300], v if j == 'constant' else str(nodes[j])[:300])
                         for i, j, v in hard]
    stats['seconds'] = round(time.time() - t0, 1)
    return [new[idx[r.get_id()]] for r in roots], stats
