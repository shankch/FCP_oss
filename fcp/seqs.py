"""Strings and lists in the translation (fcp.prove).

A string or list whose content depends on the arguments is a list of
guarded slots: (guard, value) pairs in order, and the sequence is the values
of the slots whose guard is true.  An argument of at most n characters is n
slots, slot i with guard i < len.  Filtering strengthens guards, a loop runs
its body once per slot under the slot's guard, an append adds a slot, and
two paths that meet pair the slots each of them added.  Nothing here asks
how long the sequence is until the code does (len, an index, a slice, the
returned value), and then the answer is a sum of guards.

The functions take the translator (fcp.prove.Translator) as `tr`.
"""
from __future__ import annotations

import ast

from .symval import State, Untranslatable, V

NOT_HERE = object()                      # this module does not translate the call: the caller goes on


def _int_ok(c: str) -> bool:
    try:
        int(c)
        return True
    except ValueError:
        return False


# Python's own answers for the codes a string of the interface can hold
PREDS = {name: [c for c in range(256) if getattr(chr(c), name)()]
         for name in ('isdigit', 'isalpha', 'isalnum', 'isspace', 'isupper', 'islower', 'isdecimal', 'isnumeric',
                      'isascii')}
INT_OK = [c for c in range(256) if _int_ok(chr(c))]
assert INT_OK == list(range(48, 58)) and all(int(chr(c)) == c - 48 for c in INT_OK)
SPACE = PREDS['isspace']
STR_LIKE = ('str', 'chr', 'seq')
UNDEF = V(None, 'undef')


def in_codes(z3, t, codes):
    """t is one of the codes, as a disjunction of ranges."""
    runs, codes = [], sorted(set(codes))
    for c in codes:
        if runs and runs[-1][1] == c - 1:
            runs[-1][1] = c
        else:
            runs.append([c, c])
    parts = [t == lo if lo == hi else z3.And(t >= lo, t <= hi) for lo, hi in runs]
    return z3.BoolVal(False) if not parts else parts[0] if len(parts) == 1 else z3.Or(*parts)


def both(z3, a, b):
    return b if z3.is_true(a) else a if z3.is_true(b) else z3.And(a, b)


def since(z3, cond, start):
    """What cond adds to start, if cond is start narrowed step by step
    (And(And(start, x), y): [x, y]), else None.  Path conditions are kept in
    this shape, a chain of facts, wherever two paths join: a disjunction of
    the two would hide the facts they share from the solver."""
    out = []
    while not cond.eq(start):
        if not (z3.is_app(cond) and cond.decl().kind() == z3.Z3_OP_AND and cond.num_args() == 2):
            return None
        out.append(cond.arg(1))
        cond = cond.arg(0)
    return out[::-1]


def conj(z3, xs: list):
    return xs[0] if len(xs) == 1 else z3.And(*xs)


def joined_cond(z3, base, c, ca, cb, ea, eb):
    """The condition where two branches of base meet again (entered on c as
    ea and on its negation as eb, left as ca and cb): base, with what each
    branch added where it ran; None if a branch's condition is no chain."""
    xa, xb = since(z3, ca, ea), since(z3, cb, eb)
    if xa is None or xb is None:
        return None
    cond = base
    if xa:
        cond = z3.And(cond, z3.Or(z3.Not(c), conj(z3, xa)))
    if xb:
        cond = z3.And(cond, z3.Or(c, conj(z3, xb)))
    return cond


def is_const_str(v: V) -> bool:
    return v.ty == 'str' and '\0' not in v.name


def is_list(v: V) -> bool:
    return (v.ty == 'seq' and v.name == 'list') or (v.ty == 'tuple' and v.name == 'list')


def char(tr, v: V) -> V:
    """v as one character, if it is one."""
    if v.ty == 'chr':
        return v
    if is_const_str(v) and len(v.name) == 1:
        return V(tr.z3.IntVal(ord(v.name)), 'chr')
    raise Untranslatable(f'a {v.ty} where one character is expected')


def as_seq(tr, v: V) -> V:
    z3 = tr.z3
    T = z3.BoolVal(True)
    if v.ty == 'seq':
        return v
    if is_const_str(v):
        return V(z3.IntVal(len(v.name)), 'seq', tuple((T, V(z3.IntVal(ord(c)), 'chr')) for c in v.name), 'str',
                 dense=True)
    if v.ty == 'chr':
        return V(z3.IntVal(1), 'seq', ((T, v),), 'str', dense=True)
    if v.ty == 'tuple':
        return V(z3.IntVal(len(v.items)), 'seq', tuple((T, x) for x in v.items), 'list', dense=True)
    raise Untranslatable(f'a {v.ty} where a string or a list is expected')


def from_arg(tr, zs, kind: str) -> V:
    """An argument of the interface (software._ZSeq) as slots."""
    z3 = tr.z3
    return V(zs.ln, 'seq', tuple((zs.ln > j, V(e, 'chr' if kind == 'str' else 'int')) for j, e in enumerate(zs.el)),
             'str' if kind == 'str' else 'list', dense=True)


def arg_dom(z3, fn, args: list) -> list:
    """What the interface says about the arguments (z3 terms or _ZSeq in fn.args order)."""
    out = []
    for a, (_, sig, kind) in zip(args, fn.args):
        if sig in fn.seqs:
            w, cap = fn.seqs[sig]
            out += [a.ln >= 0, a.ln <= cap] + [z3.And(e >= 0, e <= (1 << w) - 1) for e in a.el] + \
                [z3.Implies(a.ln <= j, e == 0) for j, e in enumerate(a.el)]
        elif kind != 'bool':
            out.append(z3.And(a >= 0, a <= (1 << fn.widths[sig]) - 1))
    return out


def ones(z3, guards: list):
    """How many of the guards are true."""
    n = sum(1 for g in guards if z3.is_true(g))
    rest = [z3.If(g, 1, 0) for g in guards if not z3.is_true(g) and not z3.is_false(g)]
    if not rest:
        return z3.IntVal(n)
    out = rest[0]
    for x in rest[1:]:
        out = out + x
    return out + n if n else out


def length(tr, v: V):
    v = as_seq(tr, v)
    return v.t if v.t is not None else ones(tr.z3, [g for g, _ in v.items])


def positions(tr, v: V) -> list:
    """The position of each slot among the slots that exist."""
    z3 = tr.z3
    if v.dense:
        return [z3.IntVal(j) for j in range(len(v.items))]
    out, cur = [], z3.IntVal(0)
    for g, _ in v.items:
        out.append(cur)
        cur = z3.simplify(cur + 1) if z3.is_true(g) else cur if z3.is_false(g) else cur + z3.If(g, 1, 0)
    return out


def dead(tr, cond) -> bool:
    """No call takes this path (asked of z3, briefly; unknown is no)."""
    z3 = tr.z3
    c = z3.simplify(cond)
    if z3.is_false(c):
        return True
    if z3.is_true(c):
        return False
    sol = z3.Solver()
    sol.set('timeout', 2000)
    sol.add(*tr.dom)
    sol.add(c)
    return sol.check() == z3.unsat


# -- iteration ------------------------------------------------------------------

def iter_items(tr, e, st: State, done: list) -> list:
    """The slots a for loop or a comprehension runs over: (guard, value)."""
    z3 = tr.z3
    T = z3.BoolVal(True)
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Name) and e.func.id not in st.env \
            and e.func.id not in tr.funcs and not e.keywords:
        name = e.func.id
        if name == 'range':
            b = [tr.static_int(tr.expr(x, st, done)) for x in e.args]
            if len(range(*b)) > 256:
                raise Untranslatable('a loop of more than 256 steps')
            return [(T, V(z3.IntVal(i), 'int')) for i in range(*b)]
        if tr.seqs and name == 'enumerate' and len(e.args) in (1, 2):
            inner = iter_items(tr, e.args[0], st, done)
            cur = z3.IntVal(tr.static_int(tr.expr(e.args[1], st, done)) if len(e.args) == 2 else 0)
            out = []
            for g, v in inner:
                out.append((g, V(None, 'tuple', (V(cur, 'int'), v))))
                cur = z3.simplify(cur + 1) if z3.is_true(g) else cur + z3.If(g, 1, 0)
            return out
        if tr.seqs and name == 'reversed' and len(e.args) == 1:
            return list(reversed(iter_items(tr, e.args[0], st, done)))
    v = tr.expr(e, st, done)
    if v.ty == 'dict':
        return [(T, V(None, 'str', name=k) if isinstance(k, str) else V(z3.IntVal(k), 'int')) for k in v.keys]
    if v.ty == 'tuple':
        return [(T, x) for x in v.items]
    if tr.seqs and v.ty in STR_LIKE:
        return list(as_seq(tr, v).items)
    raise Untranslatable('a for loop other than over range() or a constant tuple')


def comp(tr, e, st: State, done: list, lazy: bool = False) -> list:
    """The slots of a comprehension or generator expression.  lazy: its
    consumer may stop early (all, any), so no element may raise."""
    z3 = tr.z3
    if len(e.generators) != 1 or e.generators[0].is_async:
        raise Untranslatable('a comprehension with more than one for')
    gen = e.generators[0]
    out = []
    for g, v in iter_items(tr, gen.iter, st, done):
        x = State(both(z3, st.cond, g), dict(st.env), st.events, st.n_ans, st.made, st.closed, st.exists, st.paths)
        n0 = len(done)
        guard = g
        tr.in_sub += 1                          # nothing is changed in place inside a comprehension
        try:
            tr.assign(gen.target, v, x)
            for test in gen.ifs:
                t = tr.truthy(tr.expr(test, x, done))
                guard = both(z3, guard, t)
                x.cond = z3.And(x.cond, t)
            val = tr.expr(e.elt, x, done)
        finally:
            tr.in_sub -= 1
        if x.events is not st.events:
            raise Untranslatable('a call on the interface inside a comprehension')
        if len(done) > n0:
            if lazy:
                raise Untranslatable('all() or any() over elements that may raise')
            for d in done[n0:]:                 # the comprehension goes on where no element raised
                st.cond = z3.And(st.cond, z3.Not(d[0]))
        out.append((guard, val))
    return out


# -- paths that meet ----------------------------------------------------------------

def merge_seq(tr, c, a: V, b: V) -> V:
    """`a if c else b` for two sequences: the slots they share stay, the
    slots each path added are paired in order."""
    z3 = tr.z3
    if a.name != b.name:
        raise Untranslatable('a value that is a string on one path and a list on another')
    n = 0
    while n < min(len(a.items), len(b.items)) and a.items[n] is b.items[n]:
        n += 1
    xa, xb = a.items[n:], b.items[n:]
    out = list(a.items[:n])
    for k in range(max(len(xa), len(xb))):
        if k < len(xa) and k < len(xb):
            (ga, va), (gb, vb) = xa[k], xb[k]
            try:
                v = tr.merge(c, va, vb)
            except Untranslatable:
                out += [(both(z3, c, ga), va), (both(z3, z3.Not(c), gb), vb)]
                continue
            out.append((ga if ga.eq(gb) else z3.If(c, ga, gb), v))
        elif k < len(xa):
            out.append((both(z3, c, xa[k][0]), xa[k][1]))
        else:
            out.append((both(z3, z3.Not(c), xb[k][0]), xb[k][1]))
    t = a.t if a.t is not None and b.t is not None and a.t.eq(b.t) else None
    return V(t, 'seq', tuple(out), a.name, dense=False)


def join(tr, c, a: State, b: State, base=None, ca=None, cb=None):
    """The state `a if c else b`, or None if the two paths did different
    things on the interface.  A variable only one of them set is unusable
    afterwards.  base: the condition both started from (ca, cb: the
    conditions they entered with), kept as it is if neither narrowed it."""
    z3 = tr.z3
    if not (a.events is b.events or (not a.events and not b.events)) or not a.same_world(b):
        return None
    env = {}
    for n in dict.fromkeys(list(a.env) + list(b.env)):
        x, y = a.env.get(n), b.env.get(n)
        if x is None or y is None:
            env[n] = UNDEF
            continue
        try:
            env[n] = tr.merge(c, x, y)
        except Untranslatable:
            return None
    cond = joined_cond(z3, base, c, a.cond, b.cond, ca, cb) if base is not None else None
    if cond is None:
        cond = z3.Or(a.cond, b.cond)
    return State(cond, env, a.events, a.n_ans, a.made, a.closed, a.exists, a.paths)


def delta(z3, a, b):
    """d with a == b + d, if a is written as b plus something."""
    if z3.is_app(a) and a.decl().kind() == z3.Z3_OP_ADD:
        ch = a.children()
        for k, x in enumerate(ch):
            if x.eq(b):
                rest = ch[:k] + ch[k + 1:]
                out = rest[0]
                for y in rest[1:]:
                    out = out + y
                return out
    return None


def merge_int(tr, c, a, b):
    """If(c, a, b) for two numbers; a counter one path adds to is the
    counter plus what that path adds."""
    z3 = tr.z3
    d = delta(z3, a, b)
    if d is not None:
        return b + z3.If(c, d, 0)
    d = delta(z3, b, a)
    if d is not None:
        return a + z3.If(c, 0, d)
    return z3.If(c, a, b)


# -- the returned value -----------------------------------------------------------------

def dense_form(tr, v: V, cap: int, cond=None) -> tuple:
    """(length, [value at position p for p < cap]) of a sequence, zero
    beyond the length; the values are numbers (codes or list elements)."""
    z3 = tr.z3
    v = as_seq(tr, v)
    gs = [g for g, _ in v.items]
    vals = [x.t for _, x in v.items]
    ln = length(tr, v)
    mono = v.dense
    if not mono and gs:
        gaps = [z3.And(gs[j + 1], z3.Not(gs[j])) for j in range(len(gs) - 1)]
        mono = not gaps or dead(tr, z3.And(cond if cond is not None else z3.BoolVal(True), z3.Or(*gaps)))
    if mono:
        el = [z3.If(gs[p], vals[p], 0) if p < len(gs) else z3.IntVal(0) for p in range(cap)]
        return ln, el
    pos = positions(tr, v)
    el = []
    for p in range(cap):
        parts = [z3.If(z3.And(gs[j], pos[j] == p), vals[j], 0) for j in range(p, len(gs))]
        el.append(z3.Sum(*parts) if len(parts) > 1 else parts[0] if parts else z3.IntVal(0))
    return ln, el


# -- lists that grow ------------------------------------------------------------------

def holds(v: V, x: V) -> bool:
    """x is v or is somewhere inside it."""
    return v is x or any(holds(y[1] if isinstance(y, tuple) else y, x) for y in v.items)


def append(tr, s, st: State, done: list) -> bool:
    """`name.append(x)` as a statement, on a list the function built and no
    other name refers to: the name is bound to the list with one more slot.
    False: not such a statement."""
    c = s.value
    if not (tr.seqs and isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == 'append'
            and isinstance(c.func.value, ast.Name) and c.func.value.id in st.env):
        return False
    name = c.func.value.id
    cur = st.env[name]
    if not is_list(cur):
        return False
    if len(c.args) != 1 or c.keywords:
        raise Untranslatable('append() with other than one argument')
    if any(cur is b for b in tr.borrowed) or any(holds(v, cur) for n, v in st.env.items() if n != name):
        raise Untranslatable('append() to a list that has another name')
    z3 = tr.z3
    v = tr.expr(c.args[0], st, done)
    base = as_seq(tr, cur)
    full = base.dense and all(z3.is_true(g) for g, _ in base.items)
    st.env[name] = V(z3.simplify(base.t + 1) if base.t is not None else None, 'seq',
                     base.items + ((z3.BoolVal(True), v),), 'list', dense=full)
    return True


def rejoin(tr, g, live: State, prev: State, entered):
    """After a loop body that ran under the slot's guard g: the state
    `live if g else prev` (entered: the condition the body started with), or
    None if the two do not join."""
    z3 = tr.z3
    out = join(tr, g, live, prev)
    if out is not None:
        xs = since(z3, live.cond, entered)
        if xs is None:
            out.cond = z3.Or(live.cond, z3.And(prev.cond, z3.Not(g)))
        else:                                  # what the body added holds where the slot exists
            out.cond = z3.And(prev.cond, z3.Or(z3.Not(g), conj(z3, xs))) if xs else prev.cond
    return out


# -- calls ------------------------------------------------------------------------------

NAMES = ('len', 'sum', 'all', 'any', 'ord', 'int', 'str', 'list', 'set', 'frozenset')
ALL_CHARS = ('isdigit', 'isalpha', 'isalnum', 'isspace', 'isdecimal', 'isnumeric')   # true of a string: of every
METHODS = set(PREDS) | {'join', 'strip', 'lstrip', 'rstrip', 'replace', 'count'}     # character, and it has one


def arg_val(tr, a, st: State, done: list, lazy: bool = False) -> V:
    """An argument that may be a generator expression or reversed(...)."""
    if isinstance(a, ast.GeneratorExp):
        return V(None, 'seq', tuple(comp(tr, a, st, done, lazy)), 'list')
    if isinstance(a, ast.Call) and isinstance(a.func, ast.Name) and a.func.id == 'reversed' \
            and 'reversed' not in st.env and len(a.args) == 1 and not a.keywords:
        v = as_seq(tr, arg_val(tr, a.args[0], st, done, lazy))
        return V(v.t, 'seq', tuple(reversed(v.items)), 'list')
    return tr.expr(a, st, done)


def call_name(tr, e, st: State, done: list):
    """A builtin on a string or a list; NOT_HERE for another call."""
    z3 = tr.z3
    name = e.func.id
    if name not in NAMES or len(e.args) != 1:
        return NOT_HERE
    v = arg_val(tr, e.args[0], st, done, lazy=name in ('all', 'any'))
    if name in ('set', 'frozenset'):
        if not is_const_str(v):
            raise Untranslatable(f'{name}() of something other than a constant string')
        return V(None, 'tuple', tuple(V(None, 'str', name=c) for c in dict.fromkeys(v.name)), name='set')
    if name == 'str':
        if v.ty == 'int':
            return V(v.t, 'numstr')
        if v.ty in ('str', 'numstr', 'chr') or (v.ty == 'seq' and v.name == 'str'):
            return v
        raise Untranslatable(f'str() of a {v.ty}')
    if name == 'int':
        if v.ty in ('int', 'bool'):
            return V(tr.as_int(v), 'int')
        c = char(tr, v)                        # int('7'): the digit, or ValueError
        ok = in_codes(z3, c.t, INT_OK)
        bad = z3.And(st.cond, z3.Not(ok))
        if not dead(tr, bad):
            tr.end(done, st, 'raise', 'ValueError', bad)
            st.cond = z3.And(st.cond, ok)
        return V(c.t - 48, 'int')
    if name == 'ord':
        return V(char(tr, v).t, 'int')
    if v.ty == 'dict':
        if name != 'len':
            raise Untranslatable(f'{name}() of a dict')
        return V(z3.IntVal(len(v.items)), 'int')
    s = as_seq(tr, v)
    if name == 'len':
        return V(length(tr, s), 'int')
    if name == 'list':
        return V(s.t, 'seq', s.items, 'list', dense=s.dense)
    if name == 'sum':
        if s.name != 'list' or any(x.ty not in ('int', 'bool') for _, x in s.items):
            raise Untranslatable('sum() of values that are not numbers')
        out = None
        for g, x in s.items:
            t = tr.as_int(x) if z3.is_true(g) else z3.If(g, tr.as_int(x), 0)
            out = t if out is None else out + t
        return V(z3.IntVal(0) if out is None else out, 'int')
    ts = [(g, tr.truthy(x)) for g, x in s.items]
    if name == 'all':
        return V(z3.And(*[z3.Or(z3.Not(g), t) for g, t in ts]) if ts else z3.BoolVal(True), 'bool')
    return V(z3.Or(*[both(z3, g, t) for g, t in ts]) if ts else z3.BoolVal(False), 'bool')


def joined(tr, v: V) -> V:
    """''.join(v): the characters of v's elements, in order."""
    z3 = tr.z3
    s = as_seq(tr, v)
    out, one = [], True
    for g, x in s.items:
        if x.ty == 'chr' or (is_const_str(x) and len(x.name) == 1):
            out.append((g, char(tr, x)))
        elif is_const_str(x) or (x.ty == 'seq' and x.name == 'str'):
            one = False
            out += [(both(z3, g, h), c) for h, c in as_seq(tr, x).items]
        else:
            raise Untranslatable(f'join() of a {x.ty}')
    return V(s.t if one else None, 'seq', tuple(out), 'str', dense=one and s.dense)


def strip(tr, s: V, codes: list, left: bool, right: bool) -> V:
    z3 = tr.z3
    ws = [z3.Or(z3.Not(g), in_codes(z3, c.t, codes)) for g, c in s.items]    # absent, or a character to strip
    n = len(ws)
    lead, trail = [None] * n, [None] * n
    cur = z3.BoolVal(True)
    for j in range(n):
        cur = lead[j] = both(z3, cur, ws[j])
    cur = z3.BoolVal(True)
    for j in reversed(range(n)):
        cur = trail[j] = both(z3, cur, ws[j])
    out = []
    for j, (g, c) in enumerate(s.items):
        keep = [g] + ([z3.Not(lead[j])] if left else []) + ([z3.Not(trail[j])] if right else [])
        out.append((z3.And(*keep), c))
    return V(None, 'seq', tuple(out), 'str')


def method_call(tr, e, st: State, done: list):
    """A method of a string; NOT_HERE if the call is on something else."""
    z3 = tr.z3
    attr = e.func.attr
    if attr not in METHODS or e.keywords:
        return NOT_HERE
    x = State(st.cond, dict(st.env), st.events, st.n_ans, st.made, st.closed, st.exists, st.paths)
    d: list = []
    try:
        base = tr.expr(e.func.value, x, d)
    except Untranslatable:
        return NOT_HERE
    if not (is_const_str(base) or base.ty == 'chr' or (base.ty == 'seq' and base.name == 'str')):
        return NOT_HERE
    st.cond, st.env, st.events, st.n_ans, st.made, st.closed, st.exists, st.paths = \
        x.cond, x.env, x.events, x.n_ans, x.made, x.closed, x.exists, x.paths
    done += d
    args = [arg_val(tr, a, st, done) for a in e.args]
    if attr == 'join':
        if base.ty != 'str' or base.name or len(args) != 1:
            raise Untranslatable('join() with a separator')
        return joined(tr, args[0])
    consts = all(is_const_str(a) for a in args)
    if is_const_str(base) and consts:           # all constants: Python's own answer
        r = getattr(base.name, attr)(*[a.name for a in args])
        return V(None, 'str', name=r) if isinstance(r, str) else \
            V(z3.BoolVal(r), 'bool') if isinstance(r, bool) else V(z3.IntVal(r), 'int')
    s = as_seq(tr, base)
    if attr in PREDS:
        if args:
            raise Untranslatable(f'{attr}() with arguments')
        if base.ty == 'chr':
            return V(in_codes(z3, base.t, PREDS[attr]), 'bool')
        if attr not in ALL_CHARS:
            raise Untranslatable(f'{attr}() of a string of several characters')
        if not s.items:
            return V(z3.BoolVal(False), 'bool')
        return V(z3.And(z3.Or(*[g for g, _ in s.items]),
                        *[z3.Or(z3.Not(g), in_codes(z3, c.t, PREDS[attr])) for g, c in s.items]), 'bool')
    if attr in ('strip', 'lstrip', 'rstrip'):
        if len(args) > 1 or not consts:
            raise Untranslatable(f'{attr}() of characters that are not constants')
        return strip(tr, s, [ord(c) for c in args[0].name] if args else SPACE, attr != 'rstrip', attr != 'lstrip')
    if attr == 'replace':
        if len(args) != 2 or not consts or len(args[0].name) != 1 or len(args[1].name) > 1:
            raise Untranslatable('replace() other than of one character by at most one')
        a = ord(args[0].name)
        if args[1].name:
            b = ord(args[1].name)
            return V(s.t, 'seq', tuple((g, V(z3.If(c.t == a, b, c.t), 'chr')) for g, c in s.items), 'str',
                     dense=s.dense)
        return V(None, 'seq', tuple((z3.And(g, c.t != a), c) for g, c in s.items), 'str')
    if len(args) != 1:                           # count
        raise Untranslatable('count() with other than one argument')
    a = char(tr, args[0])
    return V(ones(z3, [z3.And(g, c.t == a.t) for g, c in s.items]), 'int')


# -- operators ----------------------------------------------------------------------------

def truthy(tr, v: V):
    z3 = tr.z3
    if v.ty == 'chr':
        return z3.BoolVal(True)
    gs = [g for g, _ in v.items]
    return z3.Or(*gs) if gs else z3.BoolVal(False)


def contains(tr, lv: V, rv: V):
    """`lv in rv` for a character in a string or a set of characters, or a
    value in a list; None if it is neither."""
    z3 = tr.z3
    if is_const_str(lv) and is_const_str(rv):
        return z3.BoolVal(lv.name in rv.name)
    if lv.ty == 'chr' or (is_const_str(lv) and len(lv.name) == 1 and rv.ty in ('seq', 'chr')):
        c = char(tr, lv)
        if is_const_str(rv):
            return in_codes(z3, c.t, [ord(x) for x in rv.name])
        if rv.ty == 'dict':
            return in_codes(z3, c.t, [ord(k) for k in rv.keys if isinstance(k, str) and len(k) == 1])
        if rv.ty == 'tuple':
            if all(is_const_str(x) for x in rv.items):
                return in_codes(z3, c.t, [ord(x.name) for x in rv.items if len(x.name) == 1])
            return z3.Or(*[tr.eq(c, x) for x in rv.items]) if rv.items else z3.BoolVal(False)
        if rv.ty in ('seq', 'chr'):
            ts = [both(z3, g, tr.eq(c, x)) for g, x in as_seq(tr, rv).items]
            return z3.Or(*ts) if ts else z3.BoolVal(False)
        return None
    if rv.ty == 'seq' and rv.name == 'list':
        ts = [both(z3, g, tr.eq(lv, x)) for g, x in rv.items]
        return z3.Or(*ts) if ts else z3.BoolVal(False)
    if rv.ty == 'seq' or lv.ty == 'seq':
        raise Untranslatable('`in` for a string of several characters')
    return None


def eq(tr, a: V, b: V):
    """a == b where one of them is a character, a string or a list of the
    translation; None if neither is."""
    z3 = tr.z3
    if a.ty not in ('chr', 'seq') and b.ty not in ('chr', 'seq'):
        return None
    if 'chr' in (a.ty, b.ty):
        c, o = (a, b) if a.ty == 'chr' else (b, a)
        if o.ty == 'chr':
            return c.t == o.t
        if is_const_str(o):
            return c.t == ord(o.name) if len(o.name) == 1 else z3.BoolVal(False)
    for x in (a, b):
        if x.ty in ('int', 'bool', 'none', 'dict', 'numstr'):
            return z3.BoolVal(False)
        if x.ty not in STR_LIKE and x.ty != 'tuple':
            raise Untranslatable(f'== between {a.ty} and {b.ty}')
        if x.ty == 'str' and not is_const_str(x):
            raise Untranslatable('== with text the translation does not know')
    if (a.ty == 'tuple' and not is_list(a)) or (b.ty == 'tuple' and not is_list(b)):
        return z3.BoolVal(False)                # a tuple is not a list or a string
    sa, sb = as_seq(tr, a), as_seq(tr, b)
    if sa.name != sb.name:
        return z3.BoolVal(False)
    if any(x.ty not in ('chr', 'int') for _, x in sa.items + sb.items):
        raise Untranslatable('== between lists of values that are not numbers')
    n = max(len(sa.items), len(sb.items))
    la, ea = dense_form(tr, sa, n)
    lb, eb = dense_form(tr, sb, n)
    return z3.And(la == lb, *[x == y for x, y in zip(ea, eb)])


def at(tr, base: V, key: V, st: State, done: list) -> V:
    """base[key]: the slot at that position among the slots that exist."""
    z3 = tr.z3
    s = as_seq(tr, base)
    if key.ty not in ('int', 'bool'):
        raise Untranslatable('an index that is not a number')
    k = z3.simplify(tr.as_int(key))
    const = z3.is_int_value(k)
    if not s.items:
        ok, val = z3.BoolVal(False), V(None, 'none')
    elif const and k.as_long() >= 0 and s.dense:
        i = k.as_long()
        ok, val = s.items[i] if i < len(s.items) else (z3.BoolVal(False), V(None, 'none'))
    else:
        L, pos = length(tr, s), positions(tr, s)
        p = k if const and k.as_long() >= 0 else L + k.as_long() if const else z3.If(k < 0, L + k, k)
        hit = [both(z3, g, pos[j] == p) for j, (g, _) in enumerate(s.items)]
        ok, val = z3.Or(*hit), s.items[-1][1]
        for h, (_, v) in zip(reversed(hit[:-1]), reversed(s.items[:-1])):
            val = tr.merge(h, v, val)
    bad = z3.And(st.cond, z3.Not(ok))
    if z3.is_false(z3.simplify(ok)) or not dead(tr, bad):
        tr.end(done, st, 'raise', 'IndexError', bad)
        st.cond = z3.And(st.cond, ok)
    return val


def slice_seq(tr, base: V, lo, hi) -> V:
    """base[lo:hi] (a bound is a V or None): the slots at those positions."""
    z3 = tr.z3
    s = as_seq(tr, base)
    L, pos = length(tr, s), positions(tr, s)

    def bound(b):
        if b is None or b.ty == 'none':
            return None
        t = z3.simplify(tr.as_int(b))
        if z3.is_int_value(t):                  # a bound before the start is the start, as every position is >= 0
            return t if t.as_long() >= 0 else L + t.as_long()
        return z3.If(t < 0, L + t, t)
    a, b = bound(lo), bound(hi)
    if a is not None and z3.is_int_value(a) and a.as_long() == 0:
        a = None
    out = []
    for j, (g, v) in enumerate(s.items):
        keep = [g] + ([pos[j] >= a] if a is not None else []) + ([pos[j] < b] if b is not None else [])
        out.append((z3.And(*keep) if len(keep) > 1 else g, v))
    t = s.t if a is None and b is None else None
    return V(t, 'seq', tuple(out), s.name, dense=s.dense and a is None)


def concat(tr, a: V, b: V) -> V:
    z3 = tr.z3
    sa, sb = as_seq(tr, a), as_seq(tr, b)
    if sa.name != sb.name:
        raise Untranslatable('+ between a string and a list')
    full = sa.dense and all(z3.is_true(g) for g, _ in sa.items)
    return V(sa.t + sb.t if sa.t is not None and sb.t is not None else None, 'seq', sa.items + sb.items, sa.name,
             dense=full and sb.dense)


def repeat(tr, a: V, n: V) -> V:
    """a * n for a constant n."""
    z3 = tr.z3
    s = as_seq(tr, a)
    k = max(0, tr.static_int(n))
    if k * len(s.items) > 256:
        raise Untranslatable('a string or list of more than 256 slots')
    full = s.dense and all(z3.is_true(g) for g, _ in s.items)
    return V(z3.simplify(s.t * k) if s.t is not None else None, 'seq', s.items * k, s.name, dense=full)


def py_types(v: V):
    """The Python types of a value of this module, for isinstance; None for another value."""
    if v.ty == 'chr' or (v.ty == 'seq' and v.name == 'str'):
        return {'str', 'object'}
    if is_list(v):
        return {'list', 'object'}
    if v.ty == 'tuple' and v.name == 'set':
        return {'frozenset', 'set', 'object'}
    return None


# -- the interface ----------------------------------------------------------------------------

def ret_seq(tr, fn, r: str, x: V, cond) -> tuple:
    """A returned string or list as the interface carries it: (it is one
    and it fits, its length, its slots), judged as the runner judges."""
    z3 = tr.z3
    w, cap = fn.seqs[r]
    kind = fn.kinds.get(r)
    no = (z3.BoolVal(False), z3.IntVal(0), [z3.IntVal(0)] * cap)
    if x.ty in ('numstr', 'ans') or (x.ty == 'str' and not is_const_str(x)):
        raise Untranslatable('returned text the translation does not know')
    if kind == 'str' and not (x.ty in ('str', 'chr') or (x.ty == 'seq' and x.name == 'str')):
        return no
    if kind != 'str' and not is_list(x):
        return no
    s = as_seq(tr, x)
    if any(v.ty != ('chr' if kind == 'str' else 'int') for _, v in s.items):
        raise Untranslatable('a returned list of values that are not numbers')
    ln, el = dense_form(tr, s, cap, cond)
    fits = [ln <= cap]
    for g, v in s.items:
        t = z3.simplify(v.t)
        if not (z3.is_int_value(t) and 0 <= t.as_long() < (1 << w)):
            fits.append(z3.Or(z3.Not(g), z3.And(t >= 0, t < (1 << w))))
    return z3.And(*fits) if len(fits) > 1 else fits[0], ln, el


def ite(z3, c, a, b):
    """If(c, a, b) for two values of the interface (terms or sequences)."""
    if hasattr(a, 'el'):
        return type(a)(z3.If(c, a.ln, b.ln), [z3.If(c, x, y) for x, y in zip(a.el, b.el)])
    return z3.If(c, a, b)


def flat(x) -> list:
    """The terms of a value of the interface."""
    return [x.ln] + list(x.el) if hasattr(x, 'el') else [x]


def flat_value(fn, sig: str, v) -> list:
    """A Python value of signal sig as numbers, in the order of flat()."""
    if sig not in fn.seqs:
        return [int(v)]
    codes = fn.codes(v)
    return [len(codes)] + codes + [0] * (fn.seqs[sig][1] - len(codes))


def pad(states: list) -> list:
    """The states with the same variables: one that some of them lack is
    unusable in those (so that paths that meet are one state again)."""
    names = dict.fromkeys(n for x in states for n in x.env)
    for x in states:
        for n in names:
            x.env.setdefault(n, UNDEF)
    return states
