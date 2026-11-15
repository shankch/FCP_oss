"""Objects that hold dictionaries, lists and records, in the translation
(fcp.prove with keyed=True, on top of fcp.seqs).

A dictionary whose keys depend on the arguments is a `map`: the writes made
to it, oldest first, each (key, value, condition, present), over a rest that
says what it holds at every other key: nothing (the object as its
constructor made it) or, for a proof by induction, an arbitrary value of
the map's shape.  A read at key k runs through the writes: the newest one
whose key equals k and whose condition holds decides.

A value that is None on some paths is an `opt`: a term that says where, and
the value elsewhere.  An instance of a helper class is a `rec`: its fields.
A deque is a list that can also lose its first element.

Python's lists and objects are shared, not copied: after `x = d[k]`,
`x.append(1)` changes what d holds.  A name that came out of a map, or
whose value went into one, therefore has a home (the map and the key it
stands for), and a change through the name is also a write to its home.  A
name bound to a value the statement itself made has a home of its own.  A
change through a name with no home, or to a value that another name may
also refer to, is not translated.

The functions take the translator (fcp.prove.Translator) as `tr`.
"""
from __future__ import annotations

import ast
from typing import Optional

from . import seqs as Q
from .symval import State, Untranslatable, V

NOT_HERE = Q.NOT_HERE
HOME = '\0home:'                         # env key of a name's home
DEQUE = ('deque',)                       # V.keys of a list that is a deque
NUMBERS = {'Integral', 'Rational', 'Real', 'Complex', 'Number'}
MAKERS = {'collections.deque': 'deque', 'collections.defaultdict': 'defaultdict',
          'threading.Lock': 'lock', 'threading.RLock': 'lock'}
SPECIAL = {'__bool__', '__len__', '__eq__', '__ne__', '__getattr__', '__getattribute__', '__setattr__', '__hash__'}


def none() -> V:
    return V(None, 'none')


def is_mut(v: V) -> bool:
    """A value a later statement could change in place."""
    return Q.is_list(v) or v.ty in ('rec', 'map') or (v.ty == 'opt' and is_mut(v.items[0]))


def is_deque(v: V) -> bool:
    return v.ty == 'seq' and v.name == 'list' and v.keys == DEQUE


# -- values that may be None ------------------------------------------------------------

def split(tr, v: V) -> tuple:
    """(where v is None, v where it is not: None if it is None everywhere)."""
    z3 = tr.z3
    if v.ty == 'none':
        return z3.BoolVal(True), None
    if v.ty == 'opt':
        return v.t, v.items[0]
    return z3.BoolVal(False), v


def opt(tr, isnone, inner: Optional[V]) -> V:
    z3 = tr.z3
    n = z3.simplify(isnone)
    if inner is None or z3.is_true(n):
        return none()
    if z3.is_false(n):
        return inner
    return V(n, 'opt', (inner,))


def gone(tr, cond) -> bool:
    """No call takes this path: seen in the term, or asked of z3 briefly."""
    return tr.z3.is_false(tr.z3.simplify(cond)) or Q.dead(tr, cond)


def unopt(tr, v: V, st: State, done: list, exc: str = 'TypeError') -> Optional[V]:
    """v where it is not None.  Where it is, the code raises exc (an
    operation None does not have), and the path goes on elsewhere.  None:
    it is None on every path, and nothing goes on."""
    z3 = tr.z3
    if v.ty not in ('opt', 'none'):
        return v
    n, inner = split(tr, v)
    if inner is None:
        if not z3.is_false(z3.simplify(st.cond)):
            tr.end(done, st, 'raise', exc)
        st.cond = z3.BoolVal(False)
        return None
    bad = z3.And(st.cond, n)
    if not gone(tr, bad):
        tr.end(done, st, 'raise', exc, bad)
        st.cond = z3.And(st.cond, z3.Not(n))
    return inner


# -- dictionaries ---------------------------------------------------------------------------

class Rest:
    """What a map holds at the keys no write names: at(k) is (present,
    value), the same terms each time it is asked about the same key."""

    def __init__(self, at):
        self._at, self.seen = at, {}

    def at(self, k):
        i = k.get_id()
        if i not in self.seen:
            self.seen[i] = (k, self._at(k))
        return self.seen[i][1]


def new_map(kind: str = 'dict', rest=None) -> V:
    return V(rest, 'map', (), kind)


def key_term(tr, k: V):
    if k.ty != 'int':
        raise Untranslatable(f'a dictionary key that is a {k.ty}')
    return k.t


def lookup(tr, m: V, k) -> tuple:
    """(where m has key k, its value there: None if it has the key nowhere)."""
    z3 = tr.z3
    present, val = (z3.BoolVal(False), None) if m.t is None else m.t.at(k)
    for ek, ev, ec, ep in m.items:
        hit = z3.simplify(z3.And(ec, ek == k))
        if z3.is_false(hit):
            continue
        if z3.is_true(hit):
            present, val = ep, ev
        else:
            present = z3.If(hit, ep, present)
            val = ev if val is None else tr.merge(hit, ev, val)
    return z3.simplify(present), val


def store(tr, m: V, k, v: V, cond=None) -> V:
    """m after m[k] = v (where cond holds, if one is given)."""
    z3 = tr.z3
    T = z3.BoolVal(True)
    if cond is None or z3.is_true(cond):
        return V(m.t, 'map', tuple(e for e in m.items if not e[0].eq(k)) + ((k, v, T, T),), m.name)
    if z3.is_false(cond):
        return m
    return V(m.t, 'map', m.items + ((k, v, cond, T),), m.name)


def merge_map(tr, c, a: V, b: V) -> V:
    """`a if c else b` for two states of one dictionary: the writes they
    share stay; a write both made to the same key is one write of the merged
    value; the others are writes on their own path."""
    z3 = tr.z3
    if a.name != b.name or a.t is not b.t:
        raise Untranslatable('two different dictionaries on two paths')
    n = 0
    while n < min(len(a.items), len(b.items)) and a.items[n] is b.items[n]:
        n += 1
    xa, xb = a.items[n:], b.items[n:]
    out = list(a.items[:n])
    for j in range(max(len(xa), len(xb))):
        if j < len(xa) and j < len(xb):
            (ka, va, ca, pa), (kb, vb, cb, pb) = xa[j], xb[j]
            if ka.eq(kb) and ca.eq(cb) and pa.eq(pb):
                try:
                    out.append((ka, tr.merge(c, va, vb), ca, pa))
                    continue
                except Untranslatable:
                    pass
        if j < len(xa):
            k, v, e, p = xa[j]
            out.append((k, v, Q.both(z3, e, c), p))
        if j < len(xb):
            k, v, e, p = xb[j]
            out.append((k, v, Q.both(z3, e, z3.Not(c)), p))
    return V(a.t, 'map', tuple(out), a.name)


def factory(tr, kind: str) -> V:
    """What a defaultdict of this kind puts at a key it does not have."""
    z3 = tr.z3
    f = kind.split(':', 1)[1] if ':' in kind else ''
    if f == 'deque':
        return V(z3.IntVal(0), 'seq', (), 'list', keys=DEQUE, dense=True)
    if f == 'list':
        return V(None, 'tuple', (), name='list')
    if f == 'int':
        return V(z3.IntVal(0), 'int')
    raise Untranslatable(f'a defaultdict of {f or "nothing"}')


# -- two paths that meet ----------------------------------------------------------------------

def same_home(a: V, b: V) -> bool:
    if a.name != b.name or (a.t is None) != (b.t is None) or len(a.keys) != len(b.keys):
        return False
    return (a.t is None or a.t.eq(b.t)) and all(x.eq(y) for x, y in zip(a.keys, b.keys))


def merge(tr, c, a: V, b: V):
    """`a if c else b` where one of them is a value of this module;
    NOT_HERE if neither is."""
    z3 = tr.z3
    tys = (a.ty, b.ty)
    if 'undef' in tys:
        return Q.UNDEF
    if 'home' in tys:
        if a.ty == b.ty and same_home(a, b):
            return a
        raise Untranslatable('a name that stands for two different stored values on two paths')
    if 'opt' in tys or ('none' in tys and a.ty != b.ty):
        (na, xa), (nb, xb) = split(tr, a), split(tr, b)
        inner = xa if xb is None else xb if xa is None else tr.merge(c, xa, xb)
        return opt(tr, z3.If(c, na, nb), inner)
    if a.ty == 'map' and b.ty == 'map':
        return merge_map(tr, c, a, b)
    if a.ty == 'rec' and b.ty == 'rec':
        if a.name != b.name or a.keys != b.keys:
            raise Untranslatable('objects of two classes on two paths')
        return V(None, 'rec', tuple(tr.merge(c, x, y) for x, y in zip(a.items, b.items)), a.name, keys=a.keys)
    if a.ty == 'lock' and b.ty == 'lock':
        return a
    if Q.is_list(a) and Q.is_list(b) and (is_deque(a) or is_deque(b)):
        if not (is_deque(a) and is_deque(b)):
            raise Untranslatable('a value that is a deque on one path and a list on another')
        out = Q.merge_seq(tr, c, a, b)
        return V(out.t, 'seq', out.items, 'list', keys=DEQUE, dense=out.dense)
    return NOT_HERE


def truthy(tr, v: V):
    """The truth of a value of this module; NOT_HERE for another."""
    z3 = tr.z3
    if v.ty == 'opt':
        return z3.And(z3.Not(v.t), tr.truthy(v.items[0]))
    if v.ty == 'map':
        if v.t is None and not v.items:
            return z3.BoolVal(False)
        raise Untranslatable('the truth of a dictionary')
    if v.ty == 'rec':
        if SPECIAL & set(tr.classes[v.name]['methods']):
            raise Untranslatable(f'{v.name}: a class that defines its own truth or equality')
        return z3.BoolVal(True)
    if v.ty == 'lock':
        return z3.BoolVal(True)
    return NOT_HERE


def eq(tr, a: V, b: V):
    """a == b where one of them is a value of this module; NOT_HERE otherwise."""
    z3 = tr.z3
    if 'opt' in (a.ty, b.ty):
        (na, xa), (nb, xb) = split(tr, a), split(tr, b)
        inner = tr.eq(xa, xb) if xa is not None and xb is not None else z3.BoolVal(False)
        return z3.Or(z3.And(na, nb), z3.And(z3.Not(na), z3.Not(nb), inner))
    for x in (a, b):
        if x.ty in ('map', 'rec', 'lock') or is_deque(x):
            raise Untranslatable(f'== with a {"deque" if is_deque(x) else x.ty}')
    return NOT_HERE


def is_none(tr, v: V):
    """`v is None` as a term."""
    return split(tr, v)[0]


# -- names and where their values live ----------------------------------------------------------
#
# The home of a name is the env entry HOME + name: a V of type 'home' whose
# name is the place ('' for a value only this name refers to, 'self.F' for
# a field), t the key in the field's dictionary (None: the field itself) and
# keys[0] the condition under which the name's value is the stored one.
# FROZEN in a path's env: a value was bound in a way the translation does not
# follow (it may have two names), so nothing is changed in place afterwards.

FROZEN = '\0frozen'


def frozen(st: State) -> bool:
    return FROZEN in st.env


def freeze(st: State):
    st.env[FROZEN] = V(None, 'none')


def names(st: State) -> list:
    return [n for n in st.env if not n.startswith('\0') and not n.startswith('self.')]


def home_of(st: State, name: str) -> Optional[V]:
    h = st.env.get(HOME + name)
    return h if h is not None and h.ty == 'home' else None


def set_home(tr, st: State, name: str, place: str, k=None, cond=None):
    st.env[HOME + name] = V(k, 'home', name=place, keys=(tr.z3.BoolVal(True) if cond is None else cond,))


def core(v: V) -> V:
    return v.items[0] if v.ty == 'opt' else v


def holders(st: State, v: V) -> list:
    """The env entries whose value is v or holds it."""
    v = core(v)
    return [n for n, x in st.env.items() if not n.startswith('\0') and Q.holds(x, v)]


def nested(v: V) -> bool:
    """A list with an element that can itself be changed in place."""
    return Q.is_list(v) and any(is_mut(x) for _, x in Q_items(v))


def Q_items(v: V) -> list:
    return list(v.items) if v.ty == 'seq' else [(None, x) for x in v.items]


def escape(tr, st: State, v: V):
    """v goes into a value the code is building.  If a name or a field
    also holds it, it has two owners from here on."""
    if is_mut(v) and holders(st, v):
        freeze(st)


def touched(tr, st: State, place: str, keep: Optional[str] = None, entries: bool = True):
    """Something stored in `place` changed in place.  Every other name that
    stands for a value stored there may show the old state: it is unusable
    from here on.  entries False: only the names that stand for all of
    `place` (a key was added, and what the other keys hold is as it was)."""
    for n in names(st):
        h = st.env.get(HOME + n)
        if h is None or n == keep:
            continue
        if h.ty != 'home' or (h.name == place and (entries or h.t is None)):
            st.env[n] = Q.UNDEF
            st.env.pop(HOME + n, None)


def link(tr, place: str, k, cond, v: V, kind: str):
    """This statement read v from place[k] (kind 'read'), or stored it there."""
    if is_mut(v):
        tr.klinks.append((place, k, cond, v, kind))


def unlink(tr, place: str):
    tr.klinks[:] = [x for x in tr.klinks if x[0] != place]


FRESH_CALLS = {'list', 'sorted', 'dict'}


def is_fresh(tr, e, st: State) -> bool:
    """The expression makes a new value each time it runs."""
    if isinstance(e, (ast.List, ast.ListComp, ast.BinOp)) or (isinstance(e, ast.Dict) and not e.keys):
        return True
    if isinstance(e, ast.Subscript) and isinstance(e.slice, ast.Slice):
        return True
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Name):
        n = e.func.id
        b = st.env.get(n, tr.consts.get(n))
        if b is not None and b.ty == 'module' and b.name in MAKERS:
            return True
        return n not in st.env and (n in FRESH_CALLS or n in tr.classes)
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute):
        try:
            f = tr.expr(e.func, State(st.cond, dict(st.env)), [])
        except Untranslatable:
            return False
        return f.ty == 'module' and f.name in MAKERS
    return False


def bind_name(tr, name: str, v: V, st: State):
    """name = v.  A value that can change in place needs a home: where
    this statement stored it, a home of its own if the statement made it,
    or where this statement read it; otherwise the path is frozen."""
    st.env.pop(HOME + name, None)
    st.env[name] = v
    if not is_mut(v):
        return
    fresh, n0 = (tr.kctx[0], tr.kctx[1]) if tr.kctx is not None else (False, len(tr.klinks))
    links = tr.klinks[n0:]
    for place, k, cond, x, kind in reversed(links):
        if kind == 'store' and x is v:
            set_home(tr, st, name, place, k)
            return
    if fresh and not nested(v) and not [n for n in holders(st, v) if n != name]:
        set_home(tr, st, name, '')
        return
    for place, k, cond, x, kind in reversed(links):
        if kind == 'read' and x is v:
            set_home(tr, st, name, place, k, cond)
            return
    freeze(st)


def adopt(tr, st: State, place: str, k, v: V) -> Optional[str]:
    """v is stored at place[k] (k None: it is the field).  A name that made
    it stands for the stored value from here on: that name is returned."""
    unlink(tr, place)
    if not is_mut(v):
        return None
    name = None
    hs = holders(st, v)
    if hs:
        name = hs[0]
        h = home_of(st, name)
        if len(hs) != 1 or name.startswith('self.') or st.env[name] is not v or h is None or h.name != '':
            raise Untranslatable('a list, a dictionary or an object stored in two places')
        set_home(tr, st, name, place, k)
    link(tr, place, k, tr.z3.BoolVal(True), v, 'store')
    return name


def may_change(tr, st: State):
    if frozen(st):
        raise Untranslatable('a change in place after a value was bound in a way the translation does not follow')
    if tr.in_sub:
        raise Untranslatable('a change in place inside and / or, a conditional expression or a comprehension')


# -- the places a statement changes ------------------------------------------------------------

def self_field(st: State, e) -> Optional[str]:
    """'self.F' if e is a field of the object."""
    if isinstance(e, ast.Attribute) and isinstance(e.value, ast.Name) and \
            st.env.get(e.value.id, none()).ty == 'self' and f'self.{e.attr}' in st.env:
        return f'self.{e.attr}'
    return None


def resolve(tr, e, st: State, done: list):
    """Where the value of e lives: ('name', n), ('field', 'self.F'),
    ('key', parent, key) or ('attr', parent, a), from a name or a field that
    holds something a statement can change.  None: nowhere this module follows."""
    if isinstance(e, ast.Name):
        v = st.env.get(e.id)
        return ('name', e.id) if v is not None and is_mut(v) else None
    f = self_field(st, e)
    if f is not None:
        return ('field', f) if is_mut(st.env[f]) else None
    if isinstance(e, ast.Attribute):
        p = resolve(tr, e.value, st, done)
        return None if p is None else ('attr', p, e.attr)
    if isinstance(e, ast.Subscript) and not isinstance(e.slice, ast.Slice):
        p = resolve(tr, e.value, st, done)
        return None if p is None else ('key', p, tr.expr(e.slice, st, done))
    return None


def root(ref) -> tuple:
    while ref[0] in ('key', 'attr'):
        ref = ref[1]
    return ref


def can_change(tr, ref, st: State):
    """A change in place through ref is one this module follows."""
    may_change(tr, st)
    r = root(ref)
    if r[0] == 'field':
        return
    n = r[1]
    v, h = st.env[n], home_of(st, n)
    if h is None:
        raise Untranslatable(f'{n}: a change to a value that may have another name')
    if any(core(v) is core(b) for b in tr.borrowed):
        raise Untranslatable(f'{n}: a change to a value the caller passed in')
    if [m for m in holders(st, v) if m != n and m != h.name]:
        raise Untranslatable(f'{n}: a change to a value that has another name')


def over(tr, st: State, done: list, exc: str):
    """Every call on this path raises exc here."""
    if not tr.z3.is_false(tr.z3.simplify(st.cond)):
        tr.end(done, st, 'raise', exc)
    st.cond = tr.z3.BoolVal(False)


def map_get(tr, m: V, key: V, st: State, done: list) -> V:
    """What m[key] reads.  A dict raises KeyError where it has no such key;
    a defaultdict has its default there (which the caller stores)."""
    z3 = tr.z3
    present, val = lookup(tr, m, key_term(tr, key))
    if m.name.startswith('defaultdict'):
        if z3.is_true(present):
            return val
        new = factory(tr, m.name)
        return new if val is None else tr.merge(present, val, new)
    if val is None:
        over(tr, st, done, 'KeyError')
        return none()
    bad = z3.And(st.cond, z3.Not(present))
    if not gone(tr, bad):
        tr.end(done, st, 'raise', 'KeyError', bad)
        st.cond = z3.And(st.cond, present)
    return val


def field(p: V, a: str) -> V:
    if p.ty != 'rec' or a not in p.keys:
        raise Untranslatable(f'attribute {a} of a {p.name or p.ty}')
    return p.items[p.keys.index(a)]


def with_field(p: V, a: str, v: V) -> V:
    field(p, a)
    return V(None, 'rec', tuple(v if k == a else x for k, x in zip(p.keys, p.items)), p.name, keys=p.keys)


def put_root(tr, ref, v: V, st: State, entries: bool = True):
    """The name or the field at the root of a ref now holds v, and so does
    what the name stands for."""
    if ref[0] == 'field':
        st.env[ref[1]] = v
        unlink(tr, ref[1])
        touched(tr, st, ref[1], entries=entries)
        return
    n = ref[1]
    st.env[n] = v
    h = home_of(st, n)
    if h is None or not h.name:
        return
    if h.t is None:
        st.env[h.name] = v
    else:
        m = st.env[h.name]
        if m.ty != 'map':
            raise Untranslatable(f'{h.name}: a dictionary that is None on some paths')
        st.env[h.name] = store(tr, m, h.t, v, h.keys[0])
    unlink(tr, h.name)
    touched(tr, st, h.name, keep=n)


def update(tr, ref, f, st: State, done: list, entries: bool = True):
    """The value at ref becomes f(the value there)."""
    kind = ref[0]
    if kind in ('name', 'field'):
        put_root(tr, ref, f(st.env[ref[1]]), st, entries)
        return

    def inner(p: V) -> V:
        q = unopt(tr, p, st, done, 'AttributeError' if kind == 'attr' else 'TypeError')
        if q is None:
            return p
        if kind == 'attr':
            return with_field(q, ref[2], f(field(q, ref[2])))
        if q.ty != 'map':
            raise Untranslatable(f'a change inside a {q.ty}, by position')
        return store(tr, q, key_term(tr, ref[2]), f(map_get(tr, q, ref[2], st, done)))
    update(tr, ref[1], inner, st, done, entries)


def read(tr, ref, st: State, done: list) -> V:
    """The value at ref, with nothing changed (a defaultdict's default is
    not stored: for a read that is about to be followed by a write)."""
    kind = ref[0]
    if kind in ('name', 'field'):
        return st.env[ref[1]]
    q = unopt(tr, read(tr, ref[1], st, done), st, done, 'AttributeError' if kind == 'attr' else 'TypeError')
    if q is None:
        return none()
    if kind == 'attr':
        return field(q, ref[2])
    if q.ty != 'map':
        raise Untranslatable(f'a {q.ty} read by position, on the way to a change')
    return map_get(tr, q, ref[2], st, done)


# -- lists and deques that change in place ------------------------------------------------------

def appended(tr, cur: V, v: V) -> V:
    z3 = tr.z3
    base = Q.as_seq(tr, cur)
    full = base.dense and all(z3.is_true(g) for g, _ in base.items)
    return V(z3.simplify(base.t + 1) if base.t is not None else None, 'seq',
             base.items + ((z3.BoolVal(True), v),), 'list', keys=DEQUE if is_deque(cur) else (), dense=full)


def popleft(tr, cur: V, st: State, done: list) -> tuple:
    """(the deque without its first element, that element).  The slots stay
    where they are: a slot goes on existing if one before it existed."""
    z3 = tr.z3
    before, firsts, new = z3.BoolVal(False), [], []
    for g, v in cur.items:
        if not z3.is_false(g):
            firsts.append((z3.simplify(z3.And(g, z3.Not(before))), v))
        new.append((z3.simplify(z3.And(g, before)), v))
        before = z3.simplify(z3.Or(before, g))
    if not firsts:
        over(tr, st, done, 'IndexError')
        return cur, none()
    bad = z3.And(st.cond, z3.Not(before))
    if not gone(tr, bad):
        tr.end(done, st, 'raise', 'IndexError', bad)
        st.cond = z3.And(st.cond, before)
    val = firsts[-1][1]
    for h, v in reversed(firsts[:-1]):
        val = tr.merge(h, v, val)
    return V(None, 'seq', tuple(new), 'list', keys=DEQUE), val


CHANGES = {'append', 'popleft', 'pop', 'clear', 'extend', 'insert', 'remove', 'appendleft', 'extendleft', 'sort',
           'reverse', 'rotate', 'update', 'popitem'}
DICT_ONLY = {'get', 'setdefault', 'items', 'keys', 'values', 'pop', 'popitem', 'update', 'clear', 'copy'}


def change_call(tr, e, ref, st: State, done: list) -> V:
    """x.append(v) or x.popleft(), where x is the value at ref."""
    attr = e.func.attr
    if attr not in ('append', 'popleft'):
        raise Untranslatable(f'{attr}() on a list, a deque or a dictionary the object keeps')
    if e.keywords or len(e.args) != (1 if attr == 'append' else 0):
        raise Untranslatable(f'{attr}() with these arguments')
    can_change(tr, ref, st)
    if ref[0] in ('name', 'field') and unopt(tr, st.env[ref[1]], st, done, 'AttributeError') is None:
        return none()
    v = tr.expr(e.args[0], st, done) if e.args else None
    if v is not None:
        escape(tr, st, v)
    out = []

    def f(cur: V) -> V:
        c = unopt(tr, cur, st, done, 'AttributeError')
        if c is None:
            return cur
        if attr == 'append':
            if not Q.is_list(c):
                raise Untranslatable(f'append() on a {c.ty}')
            return appended(tr, c, v)
        if not is_deque(c):
            raise Untranslatable(f'popleft() on a {c.ty}')
        new, val = popleft(tr, c, st, done)
        out.append(val)
        return new
    update(tr, ref, f, st, done)
    return out[0] if out else none()


# -- dictionaries: reads, get and setdefault ---------------------------------------------------

MAP_CALLS = {'get', 'setdefault', 'items', 'keys', 'values', 'copy'}


def inserted(tr, st: State, place: Optional[str], m: V, k, out: V):
    """A read put `out` at key k of the dictionary in `place`."""
    may_change(tr, st)
    if place is None:
        raise Untranslatable('a default put into a dictionary that is not a field of the object')
    st.env[place] = store(tr, m, k, out)
    unlink(tr, place)
    link(tr, place, k, tr.z3.BoolVal(True), out, 'store')
    touched(tr, st, place, entries=False)


def subscript(tr, e, base: V, st: State, done: list) -> V:
    """base[key], where base is a dictionary of this module."""
    z3 = tr.z3
    m = unopt(tr, base, st, done, 'TypeError')
    if m is None:
        return none()
    if isinstance(e.slice, ast.Slice):
        raise Untranslatable('a slice of a dictionary')
    place = self_field(st, e.value)
    key = tr.expr(e.slice, st, done)
    k = key_term(tr, key)
    present = lookup(tr, m, k)[0]
    out = map_get(tr, m, key, st, done)
    if m.name.startswith('defaultdict') and not z3.is_true(present):
        inserted(tr, st, place, m, k, out)
    elif place is not None:
        link(tr, place, k, z3.BoolVal(True), out, 'read')
    return out


def method(tr, e, st: State, done: list):
    """x.append(v), x.popleft(), d.get(k[, default]) and d.setdefault(k,
    default) on the values of this module; NOT_HERE for another call."""
    z3 = tr.z3
    attr = e.func.attr
    if attr in CHANGES:
        ref = resolve(tr, e.func.value, st, done)
        if ref is not None:
            return change_call(tr, e, ref, st, done)
    if attr not in MAP_CALLS:
        return NOT_HERE
    x, d = st.fork(st.cond), []
    try:
        base = tr.expr(e.func.value, x, d)
    except Untranslatable:
        return NOT_HERE
    if core(base).ty != 'map':
        return NOT_HERE
    st.cond, st.env, st.events, st.n_ans, st.made, st.closed, st.exists, st.paths = \
        x.cond, x.env, x.events, x.n_ans, x.made, x.closed, x.exists, x.paths
    done += d
    m = unopt(tr, base, st, done, 'AttributeError')
    if m is None:
        return none()
    if attr not in ('get', 'setdefault') or e.keywords or not 1 <= len(e.args) <= 2:
        raise Untranslatable(f'{attr}() on a dictionary whose keys depend on the arguments')
    place = self_field(st, e.func.value)
    k = key_term(tr, tr.expr(e.args[0], st, done))
    dflt = tr.expr(e.args[1], st, done) if len(e.args) == 2 else none()
    held = is_mut(dflt) and bool(holders(st, dflt))
    present, val = lookup(tr, m, k)
    if z3.is_true(present):
        out = val
    else:
        out = dflt if val is None else tr.merge(present, val, dflt)
    if attr == 'setdefault' and not z3.is_true(present):
        if held:
            raise Untranslatable('setdefault() with a default that has another name')
        inserted(tr, st, place, m, k, out)
    elif place is not None and not held:
        link(tr, place, k, present if attr == 'get' and len(e.args) == 2 else z3.BoolVal(True), out, 'read')
    return out


def attribute(tr, e, base: V, st: State, done: list):
    """base.attr for a field of the object, a field of a helper object, or
    a type of the numbers module; NOT_HERE for another."""
    if base.ty == 'module' and base.name == 'numbers' and e.attr in NUMBERS:
        return V(None, 'type', name=e.attr)
    if base.ty == 'self':
        f = f'self.{e.attr}'
        if f not in st.env:
            return NOT_HERE
        link(tr, f, None, tr.z3.BoolVal(True), st.env[f], 'read')
        return st.env[f]
    if base.ty in ('rec', 'opt', 'none'):
        p = unopt(tr, base, st, done, 'AttributeError')
        return none() if p is None else field(p, e.attr)
    return NOT_HERE


# -- values the code makes ----------------------------------------------------------------------

def make(tr, kind: str, e, st: State, done: list) -> V:
    """deque(), deque(a list), defaultdict(deque | list | int), Lock()."""
    if kind == 'lock':
        if e.args or e.keywords:
            raise Untranslatable('a lock made with arguments')
        return V(None, 'lock')
    if kind == 'deque':
        if e.keywords or len(e.args) > 1:
            raise Untranslatable('a deque with a maximum length')
        if not e.args:
            return factory(tr, 'defaultdict:deque')
        src = tr.expr(e.args[0], st, done)
        if not Q.is_list(src):
            raise Untranslatable(f'deque() of a {src.ty}')
        s = Q.as_seq(tr, src)
        return V(s.t, 'seq', s.items, 'list', keys=DEQUE, dense=s.dense)
    if e.keywords or len(e.args) != 1:
        raise Untranslatable('defaultdict() with other than one argument')
    f = tr.expr(e.args[0], st, done)
    of = 'deque' if f.ty == 'module' and MAKERS.get(f.name) == 'deque' else \
        f.name if f.ty == 'type' and f.name in ('list', 'int') else None
    if of is None:
        raise Untranslatable('a defaultdict of something other than deque, list or int')
    return new_map(f'defaultdict:{of}')


def instantiate(tr, name: str, e, st: State, done: list) -> V:
    """An object of a helper class: the fields its constructor sets."""
    cls = tr.classes[name]
    if SPECIAL & set(cls['methods']):
        raise Untranslatable(f'{name}: a class that defines its own truth, equality or attributes')
    if e.keywords:
        raise Untranslatable(f'{name}(): keyword arguments')
    args = [tr.expr(a, st, done) for a in e.args]
    for a in args:
        escape(tr, st, a)
    init = cls['methods'].get('__init__')
    if init is None:
        if args:
            raise Untranslatable(f'{name}(): arguments, and no constructor')
        return V(None, 'rec', (), name)
    env = tr.bind(init, [V(None, 'self')] + args, {})
    saved, n0 = (tr.cur_class, tr.kctx, tr.in_sub), len(tr.klinks)
    tr.cur_class, tr.kctx, tr.in_sub = name, None, 0
    try:
        outs = tr.run(init.body, State(st.cond, env))
    finally:
        tr.cur_class, tr.kctx, tr.in_sub = saved
        del tr.klinks[n0:]
    if len(outs) != 1 or outs[0][1] != 'return' or outs[0][3]:
        raise Untranslatable(f'{name}(): a constructor that can raise, or that calls the interface')
    if frozen(outs[0][4]):
        freeze(st)
    fs = tr.fields(outs[0][4])
    return V(None, 'rec', tuple(fs.values()), name, keys=tuple(fs))


def call_name(tr, e, bound: Optional[V], st: State, done: list):
    """name(...) for a maker (deque, defaultdict, Lock), dict() and the
    helper classes of the module; NOT_HERE for another name."""
    name = e.func.id
    if bound is not None:
        if bound.ty == 'module' and bound.name in MAKERS:
            return make(tr, MAKERS[bound.name], e, st, done)
        return NOT_HERE
    if name == 'dict' and not e.args and not e.keywords:
        return new_map('dict')
    if name in tr.classes:
        return instantiate(tr, name, e, st, done)
    return NOT_HERE


# -- statements ---------------------------------------------------------------------------------

def storable(v: V) -> bool:
    return v.ty in ('int', 'bool', 'none', 'lock') or is_mut(v) or (v.ty == 'opt' and storable(v.items[0]))


def assign(tr, t, v: V, st: State) -> bool:
    """name = v, or self.field = v.  False: another target."""
    if isinstance(t, ast.Name):
        bind_name(tr, t.id, v, st)
        return True
    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and \
            st.env.get(t.value.id, none()).ty == 'self':
        if not storable(v):
            raise Untranslatable(f'self.{t.attr}: a field that holds a {v.ty}')
        place = f'self.{t.attr}'
        keep = adopt(tr, st, place, None, v)
        st.env[place] = v
        touched(tr, st, place, keep=keep)
        return True
    return False


def target(tr, t, v: V, st: State, done: list):
    """t = v, for one target of an assignment statement."""
    if isinstance(t, ast.Tuple):
        saved, tr.kctx = tr.kctx, None
        try:
            tr.assign(t, v, st)
        finally:
            tr.kctx = saved
        return
    if assign(tr, t, v, st):
        return
    if not isinstance(t, (ast.Subscript, ast.Attribute)):
        tr.assign(t, v, st)                    # not a target the translation has
        return
    ref = resolve(tr, t.value, st, done)
    if ref is None:
        raise Untranslatable(f'an assignment to {ast.unparse(t)}')
    can_change(tr, ref, st)
    if isinstance(t, ast.Attribute):
        escape(tr, st, v)

        def f(p: V) -> V:
            q = unopt(tr, p, st, done, 'AttributeError')
            return p if q is None else with_field(q, t.attr, v)
        update(tr, ref, f, st, done)
        return
    if isinstance(t.slice, ast.Slice):
        raise Untranslatable('an assignment to a slice')
    k = key_term(tr, tr.expr(t.slice, st, done))
    if ref[0] == 'field':
        m = unopt(tr, st.env[ref[1]], st, done, 'TypeError')
        if m is None:
            return
        if m.ty != 'map':
            raise Untranslatable(f'an assignment into a {m.ty}, by position')
        keep = adopt(tr, st, ref[1], k, v)
        st.env[ref[1]] = store(tr, m, k, v)
        touched(tr, st, ref[1], keep=keep)
        return
    escape(tr, st, v)

    def g(p: V) -> V:
        q = unopt(tr, p, st, done, 'TypeError')
        if q is None:
            return p
        if q.ty != 'map':
            raise Untranslatable(f'an assignment into a {q.ty}, by position')
        return store(tr, q, k, v)
    update(tr, ref, g, st, done)


def stmt(tr, s, st: State):
    """The statements this module translates itself, each as the translator
    returns them (states that go on, ends, breaks, continues); NOT_HERE for
    the others.  The links a statement logs are gone when it ends."""
    done: list = []
    n0 = len(tr.klinks)
    try:
        if isinstance(s, (ast.Import, ast.ImportFrom)):
            st = st.fork(st.cond)
            for a in s.names:
                full = f'{s.module}.{a.name}' if isinstance(s, ast.ImportFrom) else a.name
                if full in tr.patched or a.name == '*':
                    raise Untranslatable(f'import of {full} inside a function')
                nm = a.asname or (a.name if isinstance(s, ast.ImportFrom) else a.name.split('.')[0])
                st.env.pop(HOME + nm, None)
                st.env[nm] = V(None, 'module', name=full if isinstance(s, ast.ImportFrom) or a.asname
                               else a.name.split('.')[0])
            return [st], done, [], []
        if isinstance(s, (ast.Assign, ast.AnnAssign)):
            if s.value is None:
                return [st], done, [], []
            st = st.fork(st.cond)
            tr.kctx = (is_fresh(tr, s.value, st), n0)
            try:
                v = tr.expr(s.value, st, done)
                for t in (s.targets if isinstance(s, ast.Assign) else [s.target]):
                    target(tr, t, v, st, done)
            finally:
                tr.kctx = None
            return [st], done, [], []
        if isinstance(s, ast.AugAssign):
            st = st.fork(st.cond)
            if isinstance(s.target, ast.Name):
                if is_mut(st.env.get(s.target.id, none())):
                    raise Untranslatable(f'{ast.unparse(s)}: a list changed with an operator')
                return NOT_HERE
            ref = resolve(tr, s.target, st, done)
            if ref is None or ref[0] == 'field':
                if ref is not None:
                    raise Untranslatable(f'{ast.unparse(s)}: a list or a dictionary changed with an operator')
                return NOT_HERE
            can_change(tr, ref, st)
            rhs = []

            def f(cur: V) -> V:
                if is_mut(cur):
                    raise Untranslatable(f'{ast.unparse(s)}: a list changed with an operator')
                if not rhs:
                    rhs.append(tr.expr(s.value, st, done))
                return tr.binop(s.op, cur, rhs[0])
            update(tr, ref, f, st, done)
            return [st], done, [], []
        return NOT_HERE
    finally:
        del tr.klinks[n0:]


# -- comparisons and calls ----------------------------------------------------------------------

def contains(tr, lv: V, rv: V, st: State, done: list):
    """`lv in rv` for a dictionary of this module; None for another value."""
    if core(rv).ty != 'map':
        return None
    m = unopt(tr, rv, st, done)
    return tr.z3.BoolVal(False) if m is None else lookup(tr, m, key_term(tr, lv))[0]


def number(tr, v: V, st: State, done: list) -> V:
    """v as an operand of arithmetic or of an ordering: where it is None
    the code raises TypeError."""
    if v.ty not in ('opt', 'none'):
        return v
    x = unopt(tr, v, st, done)
    return V(tr.z3.IntVal(0), 'int') if x is None else x


def enter(tr, st: State, env: dict):
    """A helper starts with the caller's doubts."""
    if frozen(st):
        env[FROZEN] = st.env[FROZEN]


def back(tr, before: dict, st: State, callee: State):
    """st is the caller after a helper ended in state callee, the fields
    the helper changed already written.  The caller's names that stood for
    what those fields held no longer do."""
    for k, v in before.items():
        if k.startswith('self.') and st.env.get(k) is not v:
            unlink(tr, k)
            touched(tr, st, k)
    if frozen(callee):
        freeze(st)


def cases(tr, cond, kind, payload) -> list:
    """The ends of a call that returns None or a value, as two ends."""
    if kind != 'return' or payload is None or getattr(payload, 'ty', '') != 'opt':
        return [(cond, payload)]
    z3 = tr.z3
    n = payload.t
    return [(z3.And(cond, n), none()), (z3.And(cond, z3.Not(n)), payload.items[0])]
