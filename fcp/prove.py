"""Proofs beyond the scope for small code.

The software adapter checks code on a scope of calls: exhaustive there, and
silent elsewhere.  For a pure function on integers and booleans, this module
goes further.  It translates the function's Python source into z3 terms by
symbolic execution (every path, with its condition), so that the outcome and
the returned values of one call are terms over the arguments.  Joined to the
integer encoding of a reading over k calls (software._IntSpec), the question
"do some k calls, anywhere in the interface's ranges, break this
requirement?" goes to z3.  If z3 says no and the horizon is exact, the
requirement holds for every call the interface can carry: PROVED, not just
PASS within the scope.  If it says yes, the calls are a counterexample, run
on the real code before they are reported.

The translation is a second implementation of a subset of Python, so it is
checked before it is trusted: its outcome and values on every call of the
scope must equal what the code returned when it ran there.  The integer
encoding of the reading is a second implementation of FCP-PL, so it is
checked the same way: on every cycle of the scope's trace, it must say a
property fails exactly where the compiled monitor says so.  One difference
in either, and nothing is proved.

For a change (a `baseline`), the old code is translated and checked the
same way, and its terms are the baseline signals of every call, so that
"nothing else changes" can be proved too.

The subset: module constants, helper functions (inlined), assignments
(also to tuples), if / elif / else, for over range() with constant bounds,
return, raise, assert, +, -, *, ** by a constant, // and % by a positive
constant, divmod, comparisons (chained, `in` a literal tuple), and / or /
not, conditional expressions, min, max, abs, int, bool, and isinstance /
type() checks, which are decided by the arguments' declared types.  Floats,
strings beyond exception messages, loops with symbolic bounds, try, while,
and calls to anything else are outside it (Untranslatable).
"""
from __future__ import annotations

import ast
import itertools
from typing import Optional

from . import confirm as CONF, keyed as K, seqs as Q, software as SW, sweep as SWP
from .symval import State, Untranslatable, V


# Python types an argument of each declared kind can have, for isinstance/type
TYPE_OF = {'int': {'int', 'Integral', 'Rational', 'Real', 'Complex', 'Number', 'object'},
           'bool': {'bool', 'int', 'Integral', 'Rational', 'Real', 'Complex', 'Number', 'object'}}
EXACT = {'int': 'int', 'bool': 'bool'}
TYPE_NAMES = {'int', 'bool', 'float', 'str', 'list', 'tuple', 'dict', 'set', 'bytes', 'object', 'complex',
              'Integral', 'Rational', 'Real', 'Complex', 'Number'}
PURE_STMT_CALLS = {'print'}
# the builtin exception classes a handler can name, each with its parent
EXC_PARENT = {'FileNotFoundError': 'OSError', 'FileExistsError': 'OSError', 'PermissionError': 'OSError',
              'IsADirectoryError': 'OSError', 'NotADirectoryError': 'OSError', 'TimeoutError': 'OSError',
              'ConnectionError': 'OSError', 'ConnectionRefusedError': 'ConnectionError',
              'ConnectionResetError': 'ConnectionError', 'ConnectionAbortedError': 'ConnectionError',
              'BrokenPipeError': 'ConnectionError', 'KeyError': 'LookupError', 'IndexError': 'LookupError',
              'ZeroDivisionError': 'ArithmeticError', 'OverflowError': 'ArithmeticError',
              'UnicodeError': 'ValueError', 'Exception': 'BaseException'}
EXC_ALIAS = {'IOError': 'OSError', 'EnvironmentError': 'OSError'}


def exc_classes(name: str) -> set:
    """The class an exception name raises, and every class above it (an
    exception the code's service defines derives from Exception)."""
    out = {name}
    while name != 'BaseException':
        name = EXC_PARENT.get(name, 'Exception' if name != 'Exception' else 'BaseException')
        out.add(name)
    return out


def same_events(a: tuple, b: tuple) -> bool:
    """The same calls on the interface, term for term: two paths of a helper
    that made one call each (it answered; it raised and the helper caught
    it) hold two tuples with the same content."""
    if a is b:
        return True
    if len(a) != len(b):
        return False
    same = lambda x, y: x.eq(y) if hasattr(x, 'eq') else x == y     # noqa: E731
    return all(o1 == o2 and h1 == h2 and len(t1) == len(t2) and same(a1, a2)
               and all(same(x, y) for x, y in zip(t1, t2))
               for (o1, t1, a1, h1), (o2, t2, a2, h2) in zip(a, b))


MISSING = object()


class Translator:
    """The function `fname` of a module, as terms (see call and paths).

    With an interface (fcp.effects.Ifc), calls on it are events: each call
    the code makes on `api` (or on a patched name) is recorded with its
    arguments, an answering call takes the next free answer variable ans_j
    (the j-th entry of the script), and an answer delivered as an exception
    forks the path.  Paths whose events differ are kept apart; paths with
    the same events are merged again, so a pure function stays one path."""

    def __init__(self, src: str, fname: str, ifc=None, max_states: int = 4096, seqs: bool = False,
                 keyed: bool = False):
        import z3
        self.z3 = z3
        self.seqs = seqs or keyed              # strings and lists that depend on the arguments (fcp.seqs)
        self.keyed = keyed                     # dictionaries, deques and helper objects in fields (fcp.keyed)
        self.klinks: list = []                 # where the values read or stored in this statement live
        self.kctx = None
        self.in_sub = 0                        # inside and / or / a comprehension: nothing may change there
        self.dom: list = []                    # what the interface says about the arguments
        self.borrowed: list = []               # lists a helper was given, or a loop runs over: not to be appended to
        self.ifc = ifc
        self.max_states = max_states
        self.by_name = {m['name']: m for m in (ifc.methods if ifc else [])}
        self.patched = {p: m for m in (ifc.methods if ifc else []) for p in m.get('patch') or []}
        self.answering = {m['op'] for m in (ifc.methods if ifc else []) if m.get('answers')}
        self.n_ans = 0
        self.widths: dict = {}
        self.cur_class = None
        with open(src) as f:
            tree = ast.parse(f.read())
        self.funcs: dict[str, ast.FunctionDef] = {}
        self.consts: dict[str, V] = {}
        for p, m in self.patched.items():          # builtins.open: the bare name is the stand-in
            if p.startswith('builtins.'):
                self.consts[p.split('.', 1)[1]] = V(None, 'stub', name=m['name'])
        self.classes: dict[str, dict] = {}
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                ms = {f.name: f for f in node.body if isinstance(f, ast.FunctionDef)}
                static = {f.name for f in ms.values()
                          if any(isinstance(d, ast.Name) and d.id == 'staticmethod' for d in f.decorator_list)}
                consts = {}                     # class constants (CAP = 50_000), read through self
                for b in node.body:
                    if isinstance(b, (ast.Assign, ast.AnnAssign)) and b.value is not None:
                        self._const_assign(b, consts)
                self.classes[node.name] = {'methods': ms, 'static': static, 'consts': consts}
            if isinstance(node, ast.FunctionDef):
                self.funcs[node.name] = node
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for a in node.names:
                    full = f'{node.module}.{a.name}' if isinstance(node, ast.ImportFrom) else a.name
                    nm = a.asname or (a.name if isinstance(node, ast.ImportFrom) else a.name.split('.')[0])
                    base = a.name.split('.')[-1]
                    if full in self.patched:
                        self.consts[nm] = V(None, 'stub', name=self.patched[full]['name'])
                    elif base in TYPE_NAMES:
                        self.consts[nm] = V(None, 'type', name=base)
                    else:
                        self.consts[nm] = V(None, 'module', name=full if isinstance(node, ast.ImportFrom)
                                            else a.name.split('.')[0] if not a.asname else a.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                self._const_assign(node, self.consts)
        if fname not in self.funcs and fname not in self.classes:
            raise Untranslatable(f'no function or class {fname}')
        self.fname = fname

    def _const_assign(self, node, into: dict) -> None:
        """Record a constant assignment in `into`: `CAP = 50_000`, or several
        at once, `LO, HI = 1, 100`.  Every value is read before any name is
        bound, as Python does.  A value we cannot use is skipped; a use of
        its name fails later."""
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        pairs = []
        for t in targets:
            if isinstance(t, ast.Name):
                pairs.append((t.id, node.value))
            elif isinstance(t, (ast.Tuple, ast.List)) and isinstance(node.value, (ast.Tuple, ast.List)) \
                    and len(t.elts) == len(node.value.elts) \
                    and not any(isinstance(x, ast.Starred) for x in t.elts + node.value.elts):
                pairs += [(a.id, b) for a, b in zip(t.elts, node.value.elts) if isinstance(a, ast.Name)]
        got = []
        for name, val in pairs:
            try:
                got.append((name, self.expr(val, State(self.z3.BoolVal(True), {}), [])))
            except Untranslatable:
                continue
        into.update(got)

    # -- values ---------------------------------------------------------------

    def truthy(self, v: V):
        z3 = self.z3
        if self.keyed:
            t = K.truthy(self, v)
            if t is not K.NOT_HERE:
                return t
        if v.ty == 'bool':
            return v.t
        if v.ty == 'int':
            return v.t != 0
        if v.ty == 'none':
            return z3.BoolVal(False)
        if v.ty in ('tuple', 'dict'):
            return z3.BoolVal(bool(v.items))
        if v.ty == 'str':
            return z3.BoolVal(bool(v.name))
        if v.ty == 'numstr':
            return z3.BoolVal(True)
        if v.ty in ('chr', 'seq'):
            return Q.truthy(self, v)
        if v.ty == 'ans':
            names = self.ifc.answers
            return z3.Or(*[v.t == i for i, n in enumerate(names) if n]) if any(names) else z3.BoolVal(False)
        if v.ty in ('type', 'module', 'iface', 'stub', 'handle', 'method', 'exc', 'self', 'selfmethod'):
            return z3.BoolVal(True)
        raise Untranslatable(f'the truth of a {v.ty}')

    def as_int(self, v: V):
        if v.ty == 'int':
            return v.t
        if v.ty == 'bool':
            return self.z3.If(v.t, self.z3.IntVal(1), self.z3.IntVal(0))
        raise Untranslatable(f'a {v.ty} where a number is expected')

    def merge(self, c, a: V, b: V) -> V:
        """The value of `a if c else b`, of one Python type."""
        z3 = self.z3
        if a is b:
            return a
        if self.keyed:
            r = K.merge(self, c, a, b)
            if r is not K.NOT_HERE:
                return r
        if self.seqs:
            if 'undef' in (a.ty, b.ty):
                return Q.UNDEF
            if a.ty == 'int' and b.ty == 'int':
                return V(Q.merge_int(self, c, a.t, b.t), 'int')
            text = [x.ty == 'chr' or Q.is_const_str(x) or (x.ty == 'seq' and x.name == 'str') for x in (a, b)]
            if all(text) and not (a.ty == 'str' and b.ty == 'str' and a.name == b.name):
                if all(x.ty == 'chr' or (x.ty == 'str' and len(x.name) == 1) for x in (a, b)):
                    return V(z3.If(c, Q.char(self, a).t, Q.char(self, b).t), 'chr')
                return Q.merge_seq(self, c, Q.as_seq(self, a), Q.as_seq(self, b))
            if Q.is_list(a) and Q.is_list(b):
                return Q.merge_seq(self, c, Q.as_seq(self, a), Q.as_seq(self, b))
        if a.ty != b.ty:
            raise Untranslatable(f'a value that is a {a.ty} on one path and a {b.ty} on another')
        if a.ty in ('int', 'bool', 'ans', 'numstr'):
            return V(z3.If(c, a.t, b.t), a.ty)
        if a.ty == 'tuple':
            if len(a.items) != len(b.items):
                raise Untranslatable('tuples of different lengths on two paths')
            return V(None, 'tuple', tuple(self.merge(c, x, y) for x, y in zip(a.items, b.items)))
        if a.ty == 'none':
            return a
        if a.ty in ('str', 'type', 'module', 'iface', 'stub', 'handle', 'method', 'exc', 'self', 'selfmethod') \
                and a.name == b.name:
            return a
        raise Untranslatable(f'merging two {a.ty} values')

    def static_int(self, v: V) -> int:
        t = self.z3.simplify(self.as_int(v))
        if not self.z3.is_int_value(t):
            raise Untranslatable('a bound or divisor that is not a constant')
        return t.as_long()

    def static_key(self, v: V):
        if v.ty == 'str':
            return v.name
        return self.static_int(v)

    def type_names(self, v: V) -> set:
        if v.ty == 'type':
            return {v.name}
        if v.ty == 'tuple':
            return set().union(*[self.type_names(x) for x in v.items]) if v.items else set()
        raise Untranslatable('isinstance with something other than types')

    # -- expressions ------------------------------------------------------------

    def sub(self, e, st: State, cond, done: list) -> tuple:
        """e evaluated on a branch of st (an operand of and/or, a branch of
        a conditional expression): its value and the branch's condition.  A
        call on the interface there would make the events depend on the
        branch inside one expression, which is not translated."""
        x = State(cond, st.env, st.events, st.n_ans, st.made, st.closed, st.exists, st.paths)
        self.in_sub += 1
        try:
            v = self.expr(e, x, done)
        finally:
            self.in_sub -= 1
        if x.events is not st.events:
            raise Untranslatable('a call on the interface inside and / or / a conditional expression')
        return v, x.cond

    def expr(self, e, st: State, done: list) -> V:
        """The value of e in state st; calls that raise add (cond, 'raise',
        name, events) to done and narrow st.cond to the paths that go on;
        calls on the interface add to st.events."""
        z3 = self.z3
        if isinstance(e, ast.Constant):
            if isinstance(e.value, bool):
                return V(z3.BoolVal(e.value), 'bool')
            if isinstance(e.value, int):
                return V(z3.IntVal(e.value), 'int')
            if e.value is None:
                return V(None, 'none')
            if isinstance(e.value, str):
                return V(None, 'str', name=e.value)
            raise Untranslatable(f'constant {e.value!r}')
        if isinstance(e, ast.JoinedStr):
            parts = e.values
            if len(parts) == 1 and isinstance(parts[0], ast.FormattedValue) and parts[0].conversion == -1 \
                    and parts[0].format_spec is None:
                v = self.expr(parts[0].value, st, done)
                if v.ty == 'int':
                    return V(v.t, 'numstr')    # f"{n}": the decimal text of n
            return V(None, 'str', name='\0f-string')
        if isinstance(e, ast.Name):
            if e.id in st.env:
                if st.env[e.id].ty == 'undef':
                    raise Untranslatable(f'{e.id}: a variable set on some paths only')
                return st.env[e.id]
            if e.id in self.consts:
                return self.consts[e.id]
            if e.id in TYPE_NAMES:
                return V(None, 'type', name=e.id)
            raise Untranslatable(f'name {e.id}')
        if isinstance(e, (ast.Tuple, ast.List)):
            items = tuple(self.expr(x, st, done) for x in e.elts)
            if self.keyed:
                for x in items:
                    K.escape(self, st, x)
            return V(None, 'tuple', items, name='list' if self.seqs and isinstance(e, ast.List) else '')
        if isinstance(e, ast.ListComp) and self.seqs:
            return V(None, 'seq', tuple(Q.comp(self, e, st, done)), 'list')
        if isinstance(e, ast.Dict):
            if self.keyed and not e.keys:
                return K.new_map('dict')
            if any(k is None for k in e.keys):
                raise Untranslatable('** in a dict literal')
            keys = tuple(self.static_key(self.expr(k, st, done)) for k in e.keys)
            return V(None, 'dict', tuple(self.expr(x, st, done) for x in e.values), keys=keys)
        if isinstance(e, ast.Subscript):
            return self.subscript(e, st, done)
        if isinstance(e, ast.Attribute):
            base = self.expr(e.value, st, done)
            if self.keyed:
                r = K.attribute(self, e, base, st, done)
                if r is not K.NOT_HERE:
                    return r
            if base.ty == 'module':
                dotted = f'{base.name}.{e.attr}'
                if dotted in self.patched:
                    return V(None, 'stub', name=self.patched[dotted]['name'])
                return V(None, 'module', name=dotted)
            if base.ty == 'iface' and e.attr in self.by_name:
                return V(None, 'stub', name=e.attr)
            if base.ty == 'self':
                if f'self.{e.attr}' in st.env:
                    return st.env[f'self.{e.attr}']
                cls = self.classes.get(self.cur_class) or {}
                if e.attr in cls.get('consts', {}):
                    return cls['consts'][e.attr]
                return V(None, 'selfmethod', name=e.attr)
            if base.ty == 'handle':
                if e.attr == 'name':
                    path = dict(st.paths).get(int(base.name))
                    return V(None, 'str', name=path) if isinstance(path, str) else V(None, 'none')
                if e.attr == 'closed':
                    return V(z3.BoolVal(int(base.name) in st.closed), 'bool')
                return V(None, 'method', name=f'{base.name}.{e.attr}')
            raise Untranslatable(f'attribute {ast.unparse(e)}')
        if isinstance(e, ast.UnaryOp):
            v = self.expr(e.operand, st, done)
            if isinstance(e.op, ast.Not):
                return V(z3.Not(self.truthy(v)), 'bool')
            if isinstance(e.op, ast.USub):
                return V(-self.as_int(K.number(self, v, st, done) if self.keyed else v), 'int')
            if isinstance(e.op, ast.UAdd):
                return V(self.as_int(v), 'int')
            raise Untranslatable('operator ~')
        if isinstance(e, ast.BinOp):
            a, b = self.expr(e.left, st, done), self.expr(e.right, st, done)
            if self.keyed:
                a, b = K.number(self, a, st, done), K.number(self, b, st, done)
            return self.binop(e.op, a, b)
        if isinstance(e, ast.BoolOp):
            return self.boolop(e, st, done)
        if isinstance(e, ast.Compare):
            return self.compare(e, st, done)
        if isinstance(e, ast.IfExp):
            c = z3.simplify(self.test(e.test, st, done))
            if z3.is_true(c) or z3.is_false(c):
                return self.expr(e.body if z3.is_true(c) else e.orelse, st, done)
            ea, eb = z3.And(st.cond, c), z3.And(st.cond, z3.Not(c))
            a, ca = self.sub(e.body, st, ea, done)
            b, cb = self.sub(e.orelse, st, eb, done)
            both = Q.joined_cond(z3, st.cond, c, ca, cb, ea, eb) if self.seqs else None
            st.cond = z3.Or(ca, cb) if both is None else both
            return self.merge(c, a, b)
        if isinstance(e, ast.Call):
            return self.call_expr(e, st, done)
        raise Untranslatable(f'expression {type(e).__name__}')

    def subscript(self, e: ast.Subscript, st: State, done: list) -> V:
        z3 = self.z3
        base = self.expr(e.value, st, done)
        if self.keyed and K.core(base).ty == 'map':
            return K.subscript(self, e, base, st, done)
        if self.seqs and (base.ty in ('chr', 'seq') or Q.is_const_str(base)
                          or (base.ty == 'tuple' and isinstance(e.slice, ast.Slice))):
            if not isinstance(e.slice, ast.Slice):
                return Q.at(self, base, self.expr(e.slice, st, done), st, done)
            if e.slice.step is not None:
                raise Untranslatable('a slice with a step')
            lo, hi = (self.expr(x, st, done) if x is not None else None for x in (e.slice.lower, e.slice.upper))
            return Q.slice_seq(self, base, lo, hi)
        if base.ty not in ('tuple', 'dict'):
            raise Untranslatable(f'indexing a {base.ty}')
        if isinstance(e.slice, ast.Slice):
            raise Untranslatable('a slice')
        key = self.expr(e.slice, st, done)
        keys = base.keys if base.ty == 'dict' else tuple(range(len(base.items)))
        if base.ty == 'tuple' and key.ty in ('int', 'bool'):
            t = z3.simplify(self.as_int(key))
            if z3.is_int_value(t):
                i = t.as_long()
                if -len(base.items) <= i < len(base.items):
                    return base.items[i]
                self.end(done, st, 'raise', 'IndexError')
                st.cond = z3.BoolVal(False)
                return V(None, 'none')
        try:
            k = self.static_key(key)
            if k in keys:
                return base.items[keys.index(k)]
            self.end(done, st, 'raise', 'KeyError' if base.ty == 'dict' else 'IndexError')
            st.cond = z3.BoolVal(False)
            return V(None, 'none')
        except Untranslatable:
            pass
        if not all(isinstance(k, int) for k in keys) or not base.items:
            raise Untranslatable('a symbolic key into a dict with keys that are not numbers')
        x = self.as_int(key)                   # a symbolic index: one case per key
        hit = z3.Or(*[x == k for k in keys])
        self.end(done, st, 'raise', 'KeyError' if base.ty == 'dict' else 'IndexError', z3.And(st.cond, z3.Not(hit)))
        st.cond = z3.And(st.cond, hit)
        out = base.items[-1]
        for k, v in zip(reversed(keys[:-1]), reversed(base.items[:-1])):
            out = self.merge(x == k, v, out)
        return out

    def binop(self, op, a: V, b: V) -> V:
        z3 = self.z3
        if self.seqs and 'numstr' not in (a.ty, b.ty):
            text = [x.ty in ('chr', 'seq') or Q.is_const_str(x) or Q.is_list(x) for x in (a, b)]
            if isinstance(op, ast.Add) and all(text) and (a.ty != 'str' or b.ty != 'str'):
                return Q.concat(self, a, b)
            if isinstance(op, ast.Mult) and any(text) and any(x.ty in ('int', 'bool') for x in (a, b)):
                return Q.repeat(self, *((a, b) if text[0] else (b, a)))
        if 'numstr' in (a.ty, b.ty) or (a.ty == 'str' and isinstance(op, (ast.Add, ast.Mod))):
            return self.text_op(op, a, b)
        if isinstance(op, ast.Add):
            return V(self.as_int(a) + self.as_int(b), 'int')
        if isinstance(op, ast.Sub):
            return V(self.as_int(a) - self.as_int(b), 'int')
        if isinstance(op, ast.Mult):
            return V(self.as_int(a) * self.as_int(b), 'int')
        if isinstance(op, (ast.FloorDiv, ast.Mod)):
            d = self.static_int(b)
            if d <= 0:
                raise Untranslatable('// or % by a constant that is not positive')
            x = self.as_int(a)
            # z3's integer division is Euclidean, which is Python's floor division for d > 0
            return V(x / d if isinstance(op, ast.FloorDiv) else x % d, 'int')
        if isinstance(op, ast.Pow):
            n = self.static_int(b)
            if n < 0 or n > 8:
                raise Untranslatable('** by a constant outside 0..8')
            x, out = self.as_int(a), z3.IntVal(1)
            for _ in range(n):
                out = out * x
            return V(out, 'int')
        raise Untranslatable(f'operator {type(op).__name__}')

    def text_op(self, op, a: V, b: V) -> V:
        """Text built from a number: '%d' % n, and its decimal text with
        whitespace added (which int() ignores, as the encoding of written
        text does)."""
        if isinstance(op, ast.Mod) and a.ty == 'str' and a.name in ('%d', '%i', '%s') and b.ty == 'int':
            return V(b.t, 'numstr')
        if isinstance(op, ast.Add):
            for x, y in ((a, b), (b, a)):
                if x.ty == 'numstr' and y.ty == 'str' and '\0' not in y.name and not y.name.strip():
                    return x
            if a.ty == 'str' and b.ty == 'str' and '\0' not in a.name + b.name:
                return V(None, 'str', name=a.name + b.name)
        raise Untranslatable('text built from values other than a number and whitespace')

    def test(self, e, st: State, done: list):
        """The truth of a condition.  Of `a and b` only the truth is used
        there, so the operands need not be of one type (`while q and ...`)."""
        if self.keyed and isinstance(e, ast.BoolOp):
            return self.boolop(e, st, done, truth=True).t
        if self.keyed and isinstance(e, ast.UnaryOp) and isinstance(e.op, ast.Not):
            return self.z3.Not(self.test(e.operand, st, done))
        return self.truthy(self.expr(e, st, done))

    def boolop(self, e: ast.BoolOp, st: State, done: list, truth: bool = False) -> V:
        """Python's and / or return one of their operands."""
        z3 = self.z3
        vals, conds, same = [], [], True
        cur = st.cond
        for k, x in enumerate(e.values):
            v, c = self.sub(x, st, cur, done)
            same = same and c.eq(cur)
            vals.append(v)
            t = self.truthy(v)
            conds.append(t)
            cur = z3.And(c, t if isinstance(e.op, ast.And) else z3.Not(t))
        if not (self.seqs and same):               # no operand narrowed the path: nothing to add
            st.cond = z3.And(st.cond, z3.Or(cur, *[z3.Not(c) if isinstance(e.op, ast.And) else c for c in conds]))
        if truth or all(v.ty == 'bool' for v in vals):
            return V(z3.And(*conds) if isinstance(e.op, ast.And) else z3.Or(*conds), 'bool')
        out = vals[-1]
        for v, t in zip(reversed(vals[:-1]), reversed(conds[:-1])):
            out = self.merge(t, out, v) if isinstance(e.op, ast.And) else self.merge(t, v, out)
        return out

    def compare(self, e: ast.Compare, st: State, done: list) -> V:
        z3 = self.z3
        left = e.left
        terms = []

        def is_type_call(x):
            return isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'type' and len(x.args) == 1
        lv = None if is_type_call(left) else self.expr(left, st, done)
        for op, right in zip(e.ops, e.comparators):
            if is_type_call(left):
                if not isinstance(op, (ast.Is, ast.IsNot, ast.Eq, ast.NotEq)):
                    raise Untranslatable('type() compared other than by is or ==')
                rv = self.expr(right, st, done)          # type(x) is int: decided by x's type
                arg = self.expr(left.args[0], st, done)
                same = rv.ty == 'type' and EXACT.get(arg.ty) == rv.name
                terms.append(z3.BoolVal(same if isinstance(op, (ast.Is, ast.Eq)) else not same))
                left, lv = right, rv
                continue
            if is_type_call(right):
                raise Untranslatable('type() on the right of a comparison')
            rv = self.expr(right, st, done)
            if isinstance(op, (ast.In, ast.NotIn)):
                t = K.contains(self, lv, rv, st, done) if self.keyed else None
                if t is None:
                    t = Q.contains(self, lv, rv) if self.seqs else None
                if t is not None:
                    terms.append(t if isinstance(op, ast.In) else z3.Not(t))
                    left, lv = right, rv
                    continue
                if rv.ty == 'dict':
                    rv = V(None, 'tuple', tuple(V(None, 'str', name=k) if isinstance(k, str) else V(z3.IntVal(k), 'int')
                                                for k in rv.keys))
                if rv.ty != 'tuple':
                    raise Untranslatable('`in` something other than a literal')
                t = z3.Or(*[self.eq(lv, x) for x in rv.items]) if rv.items else z3.BoolVal(False)
                terms.append(t if isinstance(op, ast.In) else z3.Not(t))
            elif isinstance(op, (ast.Is, ast.IsNot)):
                if self.keyed and 'opt' in (lv.ty, rv.ty) and 'none' in (lv.ty, rv.ty):
                    t = K.is_none(self, lv if lv.ty == 'opt' else rv)
                    terms.append(t if isinstance(op, ast.Is) else z3.Not(t))
                    left, lv = right, rv
                    continue
                if 'none' not in (lv.ty, rv.ty):
                    raise Untranslatable('`is` between values other than None')
                same = lv.ty == rv.ty
                terms.append(z3.BoolVal(same if isinstance(op, ast.Is) else not same))
            elif isinstance(op, ast.Eq):
                terms.append(self.eq(lv, rv))
            elif isinstance(op, ast.NotEq):
                terms.append(z3.Not(self.eq(lv, rv)))
            else:
                if self.seqs and all(x.ty == 'chr' or (x.ty == 'str' and len(x.name) == 1) for x in (lv, rv)):
                    a, b = Q.char(self, lv).t, Q.char(self, rv).t      # characters compare by their codes
                elif self.keyed:
                    a, b = self.as_int(K.number(self, lv, st, done)), self.as_int(K.number(self, rv, st, done))
                else:
                    a, b = self.as_int(lv), self.as_int(rv)
                terms.append({ast.Lt: a < b, ast.LtE: a <= b, ast.Gt: a > b, ast.GtE: a >= b}[type(op)])
            left, lv = right, rv
        return V(z3.And(*terms) if len(terms) > 1 else terms[0], 'bool')

    def eq(self, a: V, b: V):
        z3 = self.z3
        if self.keyed:
            t = K.eq(self, a, b)
            if t is not K.NOT_HERE:
                return t
        if self.seqs:
            t = Q.eq(self, a, b)
            if t is not None:
                return t
        if a.ty in ('int', 'bool') and b.ty in ('int', 'bool'):
            return a.t == b.t if a.ty == b.ty else self.as_int(a) == self.as_int(b)
        if a.ty == 'none' or b.ty == 'none':
            return z3.BoolVal(a.ty == b.ty)
        if a.ty == 'tuple' and b.ty == 'tuple':
            if len(a.items) != len(b.items):
                return z3.BoolVal(False)
            return z3.And(*[self.eq(x, y) for x, y in zip(a.items, b.items)]) if a.items else z3.BoolVal(True)
        if a.ty == 'str' and b.ty == 'str' and '\0' not in a.name + b.name:
            return z3.BoolVal(a.name == b.name)
        if {a.ty, b.ty} == {'ans', 'str'}:
            x, s = (a, b) if a.ty == 'ans' else (b, a)
            names = self.ifc.answers
            return x.t == names.index(s.name) if s.name in names else z3.BoolVal(False)
        if a.ty == 'ans' and b.ty == 'ans':
            return a.t == b.t
        if {a.ty, b.ty} <= {'ans', 'str', 'int', 'bool', 'tuple'}:
            return z3.BoolVal(False)            # a string never equals a number or a tuple
        raise Untranslatable(f'== between {a.ty} and {b.ty}')

    def call_expr(self, e: ast.Call, st: State, done: list) -> V:
        z3 = self.z3
        if isinstance(e.func, ast.Attribute):
            if self.seqs:
                r = K.method(self, e, st, done) if self.keyed else K.NOT_HERE
                if r is not K.NOT_HERE:
                    return r
                r = Q.method_call(self, e, st, done)
                if r is not Q.NOT_HERE:
                    return r
            f = self.expr(e.func, st, done)
            if self.keyed and f.ty == 'module' and f.name in K.MAKERS:
                return K.make(self, K.MAKERS[f.name], e, st, done)
            if f.ty == 'stub':
                return self.stub_call(self.by_name[f.name], e, st, done)
            if f.ty == 'selfmethod':           # self.helper(...): the class's own method, inlined
                cls = self.classes[self.cur_class]
                if f.name not in cls['methods']:
                    raise Untranslatable(f'self.{f.name}: not a method of the class')
                args = [self.expr(a, st, done) for a in e.args]
                kw = {k.arg: self.expr(k.value, st, done) for k in e.keywords}
                if f.name not in cls['static']:
                    args = [V(None, 'self')] + args
                return self.inline(cls['methods'][f.name], args, kw, st, done)
            if f.ty == 'method':               # a method of an object the code made: f1.write(...)
                n, meth = f.name.split('.', 1)
                maker = next(m for m in self.ifc.methods if m.get('handle'))
                ms = [m for m in self.ifc.methods if m.get('via') and m['name'] == meth]
                if meth == 'fileno' and not e.args:
                    if int(n) in st.closed:
                        self.end(done, st, 'raise', 'ValueError')
                        st.cond = z3.BoolVal(False)
                    return V(z3.IntVal(int(n)), 'int')
                if not ms:
                    raise Untranslatable(f'{maker["name"]}(...).{meth}: not a method the design declares')
                return self.stub_call(ms[0], e, st, done, on=V(None, 'handle', name=n))
            if f.ty == 'module' and self.ifc is not None and f.name in ((self.ifc.files or {}).get('query') or []):
                return self.query(e, st, done)
            raise Untranslatable(f'call of {ast.unparse(e.func)}')
        if not isinstance(e.func, ast.Name):
            raise Untranslatable(f'call of {ast.unparse(e.func)}')
        name = e.func.id
        bound = st.env.get(name, self.consts.get(name))
        if self.keyed:
            r = K.call_name(self, e, bound, st, done)
            if r is not K.NOT_HERE:
                return r
        if bound is not None and bound.ty == 'stub':
            return self.stub_call(self.by_name[bound.name], e, st, done)
        if name in self.funcs and name not in st.env:
            args = self.call_args(e, st, done)
            kw = {k.arg: self.expr(k.value, st, done) for k in e.keywords}
            return self.inline(self.funcs[name], args, kw, st, done)
        if e.keywords:
            raise Untranslatable(f'keyword arguments to {name}')
        if self.seqs and name not in st.env:
            r = Q.call_name(self, e, st, done)
            if r is not Q.NOT_HERE:
                return r
        if name in ('min', 'max'):
            args = [self.expr(a, st, done) for a in e.args]
            if len(args) == 1 and args[0].ty == 'tuple':
                args = list(args[0].items)
            if not args:
                raise Untranslatable(f'{name}() of nothing')
            out = args[0]
            for x in args[1:]:
                # min keeps the first of equal values, as Python does
                c = self.as_int(x) < self.as_int(out) if name == 'min' else self.as_int(x) > self.as_int(out)
                out = self.merge(c, x, out) if x.ty == out.ty else V(z3.If(c, self.as_int(x), self.as_int(out)), 'int')
            return out
        if name in ('sum', 'len') and len(e.args) == 1:
            v = self.expr(e.args[0], st, done)
            if v.ty not in ('tuple', 'dict'):
                raise Untranslatable(f'{name}() of something other than a literal tuple or list')
            items = list(v.items)
            if name == 'len':
                return V(z3.IntVal(len(items)), 'int')
            out = z3.IntVal(0)
            for x in items:
                out = out + self.as_int(x)
            return V(out, 'int')
        if name == 'abs':
            x = self.as_int(self.expr(e.args[0], st, done))
            return V(z3.If(x < 0, -x, x), 'int')
        if name == 'int':
            v = self.expr(e.args[0], st, done)
            if v.ty not in ('int', 'bool') or len(e.args) != 1:
                raise Untranslatable('int() of something other than a number')
            return V(self.as_int(v), 'int')
        if name == 'bool':
            return V(self.truthy(self.expr(e.args[0], st, done)), 'bool')
        if name == 'str' and len(e.args) == 1:
            v = self.expr(e.args[0], st, done)
            if v.ty == 'int':
                return V(v.t, 'numstr')        # the decimal text of a number
            if v.ty in ('str', 'numstr'):
                return v
            raise Untranslatable(f'str() of a {v.ty}')
        if name == 'divmod':
            a, b = (self.expr(x, st, done) for x in e.args)
            return V(None, 'tuple', (self.binop(ast.FloorDiv(), a, b), self.binop(ast.Mod(), a, b)))
        if name == 'isinstance':
            v = self.expr(e.args[0], st, done)
            want = self.type_names(self.expr(e.args[1], st, done))
            have = (Q.py_types(v) if self.seqs else None) or TYPE_OF.get(v.ty) or \
                ({'str', 'object'} if v.ty in ('str', 'ans') else None)
            if have is None:
                raise Untranslatable(f'isinstance of a {v.ty}')
            return V(z3.BoolVal(bool(have & want)), 'bool')
        if name in TYPE_NAMES and name not in ('int', 'bool'):
            raise Untranslatable(f'{name}()')
        raise Untranslatable(f'call of {name}')

    def stub_call(self, m: dict, e: ast.Call, st: State, done: list, on: Optional[V] = None) -> V:
        """A call on the interface: one event, as the sandbox records it.  An
        answering call takes the next answer variable; an answer delivered as
        an exception forks.  A method with `handle` makes an object (f1, ...);
        a method `via` it is called on that object, and raises ValueError once
        the object is closed; `fs` methods change the files the path sees, and
        removing or moving a file that is not there raises FileNotFoundError
        without taking an answer."""
        z3 = self.z3
        args = self.call_args(e, st, done)
        kw = {k.arg: self.expr(k.value, st, done) for k in e.keywords}
        if len(st.events) >= self.ifc.max_calls:   # the runner stops the run here
            self.end(done, st, 'toomany', None)
            st.cond = z3.BoolVal(False)
            return V(None, 'none')
        vals = self.bind_call(m, args, kw)
        terms = [self.encode(x, v) for x, v in zip(m['args'], vals)]
        hn = int(on.name) if on is not None else 0
        err = None
        if on is not None and hn in st.closed and m['name'] != 'close':
            err = 'ValueError'                 # a call on a closed file
        if m.get('fs') in ('remove', 'move') and err is None:
            path = self.static_path(vals[0] if vals else None)
            if path not in st.exists:
                err = 'FileNotFoundError'
        a = z3.IntVal(0)
        if m.get('answers') and err is None:
            a = z3.Int(f'ans_{st.n_ans}')
            st.n_ans += 1
            self.n_ans = max(self.n_ans, st.n_ans)
        if err is not None:
            st.events = st.events + ((m['op'], tuple(terms), a, hn),)
            self.end(done, st, 'raise', err)
            st.cond = z3.BoolVal(False)
            return V(None, 'none')
        if m.get('answers'):                   # answers delivered as exceptions: the path forks, nothing made
            for name, exc in (m.get('raises') or {}).items():
                hit = a == self.ifc.answers.index(name)
                failed = State(z3.And(st.cond, hit), st.env, st.events + ((m['op'], tuple(terms), a, hn),),
                               st.n_ans, st.made, st.closed, st.exists, st.paths)
                self.end(done, failed, 'raise', exc.rsplit('.', 1)[-1])
                st.cond = z3.And(st.cond, z3.Not(hit))
        if m.get('handle'):
            st.made += 1
            hn = st.made
            path = vals[0] if vals else None
            st.paths = st.paths + ((hn, path.name if path is not None and path.ty == 'str' else None),)
        st.events = st.events + ((m['op'], tuple(terms), a, hn),)
        if m.get('fs'):
            self.fs_effect(m, vals, st)
        if on is not None and m['name'] == 'close':
            st.closed = st.closed | {hn}
        if m.get('handle'):
            return V(None, 'handle', name=str(hn))
        if not m.get('answers'):
            return V(None, 'none')
        if m.get('bytes'):
            raise Untranslatable('answers returned as bytes')
        return V(a, 'ans')

    def bind_call(self, m: dict, args: list, kw: dict) -> list:
        """The declared arguments of a call, as the sandbox binds them."""
        z3 = self.z3
        named = {x['name'] for x in m['args'] if x.get('name')}
        rest = [v for k, v in kw.items() if k not in named]
        out = []
        for i, x in enumerate(m['args']):
            if i < len(args):
                v = args[i]
            elif x.get('name') in kw:
                v = kw[x['name']]
            elif not x.get('name') and rest:
                v = rest.pop(0)
            elif 'default' in x:
                d = x['default']
                v = V(None, 'str', name=d) if isinstance(d, str) else V(z3.IntVal(int(d)), 'int')
            else:
                v = None
            out.append(v)
        return out

    def static_path(self, v: Optional[V]):
        if v is None or v.ty != 'str' or '\0' in v.name:
            raise Untranslatable('a file path that is not a literal')
        return v.name

    def fs_effect(self, m: dict, vals: list, st: State):
        if m['fs'] == 'open':
            mode = next((v for x, v in zip(m['args'], vals) if x.get('open_mode')), None)
            mname = mode.name if mode is not None and mode.ty == 'str' else 'r'
            if any(c in mname for c in 'wax'):
                st.exists = st.exists | {self.static_path(vals[0] if vals else None)}
        elif m['fs'] == 'remove':
            st.exists = st.exists - {self.static_path(vals[0])}
        elif m['fs'] == 'move':
            src, dst = self.static_path(vals[0]), self.static_path(vals[1] if len(vals) > 1 else None)
            st.exists = (st.exists - {src}) | {dst}

    def query(self, e: ast.Call, st: State, done: list) -> V:
        """os.path.exists and the other query names: from the path's files."""
        args = [self.expr(a, st, done) for a in e.args]
        return V(self.z3.BoolVal(self.static_path(args[0] if args else None) in st.exists), 'bool')

    def encode(self, x: dict, v: Optional[V]):
        """An argument as the trace carries it (fcp.effects encodings; the
        trace keeps 0 for anything it cannot represent)."""
        z3 = self.z3
        w = self.ifc_width(x['signal'])
        if v is None:
            return z3.IntVal(0)
        if v.ty == 'numstr':
            if x.get('parse') == 'int':
                return z3.If(z3.And(v.t >= 0, v.t < (1 << w)), v.t, z3.IntVal(0))
            if 'enum' in x or x.get('open_mode'):
                raise Untranslatable(f'the text of a number as {x["signal"]}')
            return z3.IntVal(0)
        if v.ty == 'str':
            s = v.name
            if '\0' in s and ('enum' in x or x.get('parse') or x.get('open_mode')):
                raise Untranslatable(f'text the translation does not know, as {x["signal"]}')
            if 'enum' in x:
                return z3.IntVal(1 + x['enum'].index(s) if s in x['enum'] else 0)
            if x.get('open_mode'):
                for c, k in (('x', 4), ('a', 3), ('w', 2), ('r', 1)):
                    if c in s:
                        return z3.IntVal(k)
                return z3.IntVal(0)
            if x.get('parse') == 'int':
                try:
                    n = int(s)
                except ValueError:
                    return z3.IntVal(0)
                return z3.IntVal(n if 0 <= n < (1 << w) else 0)
            return z3.IntVal(0)
        if v.ty == 'handle':
            return z3.IntVal(int(v.name)) if x.get('handle') else z3.IntVal(0)
        if v.ty in ('int', 'bool') and 'enum' not in x and not x.get('open_mode'):
            t = self.as_int(v)
            return z3.If(z3.And(t >= 0, t < (1 << w)), t, z3.IntVal(0))
        if v.ty in ('int', 'bool', 'none', 'tuple'):
            return z3.IntVal(0)
        raise Untranslatable(f'an argument of {x["signal"]} that is a {v.ty}')

    def ifc_width(self, sig: str) -> int:
        return self.widths[sig]

    def end(self, done: list, st: State, kind: str, payload, cond=None):
        """One way out: (cond, kind, payload, events, the state there), the
        state a snapshot so that an except clause can go on from it."""
        snap = State(st.cond if cond is None else cond, dict(st.env), st.events, st.n_ans, st.made, st.closed,
                     st.exists, st.paths)
        done.append((snap.cond, kind, payload, st.events, snap))

    def inline(self, f: ast.FunctionDef, args: list, kw: dict, st: State, done: list) -> V:
        """A helper's value at this call; its raises go to done, with the
        caller's variables (an except clause runs in the caller).  A method
        given self sees the object's fields, and its changes to them carry
        back to the caller."""
        z3 = self.z3
        before = dict(st.env)
        env = self.bind(f, args, kw)
        own = any(a.ty == 'self' for a in env.values())
        if own:
            env.update({k: v for k, v in st.env.items() if k.startswith('self.')})
        if self.keyed:
            K.enter(self, st, env)
        n0 = len(self.borrowed)
        self.borrowed += [a for a in env.values() if Q.is_list(a) or (self.keyed and K.is_mut(a))]
        try:
            outs = self.run(f.body, State(st.cond, env, st.events, st.n_ans, st.made, st.closed, st.exists, st.paths))
        finally:
            del self.borrowed[n0:]
        rets = [(c, v, ev, x) for c, kind, v, ev, x in outs if kind == 'return']
        for c, kind, v, ev, x in outs:
            if kind == 'return':
                continue
            caller = dict(st.env)
            if own:
                caller.update({k: y for k, y in x.env.items() if k.startswith('self.')})
            out = State(c, caller, x.events, x.n_ans, x.made, x.closed, x.exists, x.paths)
            if self.keyed:
                K.back(self, before, out, x)
            done.append((c, kind, v, ev, out))
        if own and rets:                       # the fields after the call, path by path
            fs = {k for _, _, _, x in rets for k in x.env if k.startswith('self.')}
            if any(set(k for k in x.env if k.startswith('self.')) != fs for _, _, _, x in rets):
                raise Untranslatable(f'{f.name}: a method that sets a field on some paths only')
            for k in fs:
                val = rets[-1][3].env[k]
                for c, _, _, x in reversed(rets[:-1]):
                    val = self.merge(c, x.env[k], val)
                st.env[k] = val
        if self.keyed:
            for _, _, _, x in rets:
                K.back(self, before, st, x)
        if not rets:
            st.cond = z3.BoolVal(False)
            return V(None, 'none')
        if any(not same_events(ev, rets[0][2]) or not x.same_world(rets[0][3]) for _, _, ev, x in rets):
            raise Untranslatable(f'{f.name}: a helper whose calls on the interface depend on the path')
        w = rets[0][3]
        st.events, st.n_ans, st.made, st.closed, st.exists, st.paths = \
            w.events, w.n_ans, w.made, w.closed, w.exists, w.paths
        left = [Q.since(z3, c, st.cond) for c, kind, _, _, _ in outs if kind != 'return'] if self.seqs else [None]
        if self.seqs and len(rets) == 1:
            st.cond = rets[0][0]
        elif all(left):                        # every path returned, but those that left with these facts
            for xs in left:
                st.cond = z3.And(st.cond, z3.Not(Q.conj(z3, xs)))
        else:
            st.cond = z3.Or(*[c for c, _, _, _ in rets])
        out = rets[-1][1]
        for c, v, _, _ in reversed(rets[:-1]):
            out = self.merge(c, v, out)
        return out

    def call_args(self, e: ast.Call, st: State, done: list) -> list:
        """The positional arguments of a call; `*xs` is spread where xs is a
        tuple of known length (the *args of a helper)."""
        out = []
        for a in e.args:
            if isinstance(a, ast.Starred):
                v = self.expr(a.value, st, done)
                if v.ty != 'tuple':
                    raise Untranslatable('* on something other than a tuple of known length')
                out += list(v.items)
            else:
                out.append(self.expr(a, st, done))
        return out

    def bind(self, f: ast.FunctionDef, args: list, kw: dict) -> dict:
        a = f.args
        if a.kwarg or a.kwonlyargs or a.posonlyargs:
            raise Untranslatable(f'{f.name}: **kwargs, keyword-only or positional-only parameters')
        names = [x.arg for x in a.args]
        defaults = dict(zip(names[len(names) - len(a.defaults):], a.defaults))
        env = {}
        if a.vararg:                            # *args: the arguments past the named ones, as a tuple
            env[a.vararg.arg] = V(None, 'tuple', tuple(args[len(names):]))
        for i, n in enumerate(names):
            if i < len(args):
                env[n] = args[i]
            elif n in kw:
                env[n] = kw[n]
            elif n in defaults:
                env[n] = self.expr(defaults[n], State(self.z3.BoolVal(True), {}), [])
            else:
                raise Untranslatable(f'{f.name}: missing argument {n}')
        return env

    # -- statements ---------------------------------------------------------------

    def run(self, body: list, st: State) -> list:
        """Every way the block ends: (cond, 'return', V, events),
        (cond, 'raise', name, events) or (cond, 'toomany', None, events),
        with a fall-through returning None."""
        live, done, brk, cont = self.block(body, [st])
        if brk or cont:
            raise Untranslatable('break or continue outside a loop')
        for x in live:
            self.end(done, x, 'return', V(None, 'none'))
        return done

    def merge_states(self, states: list) -> list:
        """States with the same calls on the interface, as one: their
        conditions are disjoint, so a variable is its value under the first
        condition, else under the second."""
        z3 = self.z3
        out: list[State] = []
        for x in states:
            for k, y in enumerate(out):
                if not (y.events is x.events or (not y.events and not x.events)) or set(y.env) != set(x.env) \
                        or not y.same_world(x):
                    continue
                try:
                    env = {n: self.merge(y.cond, y.env[n], x.env[n]) for n in y.env}
                except Untranslatable:
                    continue                    # values that do not merge: the paths stay apart
                out[k] = State(z3.Or(y.cond, x.cond), env, y.events, y.n_ans, y.made, y.closed, y.exists, y.paths)
                break
            else:
                out.append(x)
        return out

    def block(self, body: list, states: list) -> tuple:
        """(live states, done, states that break, states that continue)."""
        done, brk, cont = [], [], []
        live = list(states)
        for s in body:
            if not live:
                break
            nxt = []
            for st in live:
                l, d, b, c = self.stmt(s, st)
                nxt += l
                done += d
                brk += b
                cont += c
            live = self.merge_states(nxt)
            if len(live) > self.max_states:
                raise Untranslatable('too many paths')
        return live, done, brk, cont

    def stmt(self, s, st: State) -> tuple:
        z3 = self.z3
        done: list = []
        if self.keyed:
            r = K.stmt(self, s, st)
            if r is not K.NOT_HERE:
                return r
        if isinstance(s, ast.Expr):
            if isinstance(s.value, ast.Constant):
                return [st], done, [], []        # a docstring
            if isinstance(s.value, ast.Call) and isinstance(s.value.func, ast.Name) and \
                    s.value.func.id in PURE_STMT_CALLS:
                return [st], done, [], []
            st = st.fork(st.cond)
            if self.keyed or not Q.append(self, s, st, done):
                self.expr(s.value, st, done)
            return [st], done, [], []
        if isinstance(s, ast.Pass):
            return [st], done, [], []
        if isinstance(s, (ast.Assign, ast.AnnAssign)):
            if s.value is None:
                return [st], done, [], []
            st = st.fork(st.cond)
            v = self.expr(s.value, st, done)
            for t in (s.targets if isinstance(s, ast.Assign) else [s.target]):
                self.assign(t, v, st)
            return [st], done, [], []
        if isinstance(s, ast.AugAssign):
            st = st.fork(st.cond)
            cur = self.expr(s.target, st, done)
            v = self.binop(s.op, cur, self.expr(s.value, st, done))
            self.assign(s.target, v, st)
            return [st], done, [], []
        if isinstance(s, ast.If):
            st = st.fork(st.cond)
            c = z3.simplify(self.test(s.test, st, done))
            if z3.is_true(c) or z3.is_false(c):    # a constant condition: the other branch is dead code
                l, d, b, cc = self.block(s.body if z3.is_true(c) else s.orelse, [st])
                return l, done + d, b, cc
            ea, eb = z3.And(st.cond, c), z3.And(st.cond, z3.Not(c))
            la, da, ba, ca = self.block(s.body, [st.fork(ea)])
            lb, db, bb, cb = self.block(s.orelse, [st.fork(eb)])
            if self.seqs and len(la) == 1 and len(lb) == 1:     # one state again, split on the test alone
                j = Q.join(self, c, la[0], lb[0], st.cond, ea, eb)
                if j is not None:
                    return [j], done + da + db, ba + bb, ca + cb
            return self.merge_states(la + lb), done + da + db, ba + bb, ca + cb
        if isinstance(s, ast.Return):
            st = st.fork(st.cond)
            v = self.expr(s.value, st, done) if s.value else V(None, 'none')
            self.end(done, st, 'return', v)
            return [], done, [], []
        if isinstance(s, ast.Raise):
            self.end(done, st, 'raise', self.exc_name(s.exc, st))
            return [], done, [], []
        if isinstance(s, ast.Assert):
            st = st.fork(st.cond)
            c = self.test(s.test, st, done)
            self.end(done, st, 'raise', 'AssertionError', z3.And(st.cond, z3.Not(c)))
            st.cond = z3.And(st.cond, c)
            return [st], done, [], []
        if isinstance(s, ast.Break):
            return [], done, [st], []
        if isinstance(s, ast.Continue):
            return [], done, [], [st]
        if isinstance(s, ast.For):
            return self.loop_for(s, st)
        if isinstance(s, ast.While):
            return self.loop_while(s, st)
        if isinstance(s, ast.With):
            return self.with_block(s, st)
        if isinstance(s, ast.Try):
            return self.try_block(s, st)
        raise Untranslatable(f'statement {type(s).__name__}')

    def with_block(self, s: ast.With, st: State) -> tuple:
        """with open(...) as f: the object is closed on every way out of the
        block (the end, return, raise, break), as the sandbox's __exit__ does:
        a recorded close if the design declares one."""
        z3 = self.z3
        if len(s.items) != 1:
            raise Untranslatable('a with statement over several objects')
        done: list = []
        st = st.fork(st.cond)
        v = self.expr(s.items[0].context_expr, st, done)
        if self.keyed and v.ty == 'lock':                # nothing else runs while the lock is held: one caller
            l, d, b, c = self.block(s.body, [st])
            return l, done + d, b, c
        if v.ty != 'handle':
            raise Untranslatable('a with block over something other than an object the code made')
        if s.items[0].optional_vars is not None:
            self.assign(s.items[0].optional_vars, v, st)
        n = int(v.name)
        closer = next((m for m in self.ifc.methods if m.get('via') and m['name'] == 'close'), None)

        def closing(x: State) -> tuple:
            if closer is None or n in x.closed:
                return x, None
            if len(x.events) >= self.ifc.max_calls:
                return x, 'toomany'
            x = x.fork(x.cond)
            x.events = x.events + ((closer['op'], tuple(z3.IntVal(0) for _ in closer['args']), z3.IntVal(0), n),)
            x.closed = x.closed | {n}
            return x, None
        live, d, b, c = self.block(s.body, [st])
        out_live, out_b, out_c = [], [], []
        for group, out in ((live, out_live), (b, out_b), (c, out_c)):
            for x in group:
                y, stop = closing(x)
                if stop:
                    self.end(done, y, 'toomany', None)
                else:
                    out.append(y)
        for cond, kind, payload, events, snap in d:
            y, stop = closing(snap.fork(cond))
            self.end(done, y, 'toomany' if stop else kind, None if stop else payload)
        return self.merge_states(out_live), done, out_b, out_c

    def finally_block(self, s: ast.Try, st: State) -> tuple:
        """try ... finally: the finally block runs on every way out of the
        rest: the end, return, raise, break, continue, and the sandbox
        stopping the run.  If it ends normally, the way out goes on as it
        was; if it returns or raises, that replaces it."""
        inner = ast.Try(body=s.body, handlers=s.handlers, orelse=s.orelse, finalbody=[])
        live, d, b, c = self.try_block(inner, st) if (s.handlers or s.orelse) else self.block(s.body, [st])
        done: list = []

        def after(xs: list) -> tuple:
            l2, d2, b2, c2 = self.block(s.finalbody, xs)
            if b2 or c2:
                raise Untranslatable('break or continue inside finally')
            return l2, d2
        out_live, d2 = after(live)
        done += d2
        out_b, out_c = [], []
        for group, out in ((b, out_b), (c, out_c)):
            for x in group:
                l2, d2 = after([x])
                out += l2
                done += d2
        for cond, kind, payload, events, snap in d:
            l2, d2 = after([snap.fork(cond)])
            done += d2
            for x in l2:                       # finally ended normally: the way out goes on
                self.end(done, x, kind, payload)
        return self.merge_states(out_live), done, out_b, out_c

    def try_block(self, s: ast.Try, st: State) -> tuple:
        """try / except / else: each exception the body raises goes to the
        first handler whose class it is or derives from, which goes on from
        the state where it was raised; the others go on out."""
        if s.finalbody:
            return self.finally_block(s, st)
        live, d, b, c = self.block(s.body, [st.fork(st.cond)])
        done: list = []
        handlers = []
        for h in s.handlers:
            if h.type is None:
                names = None                   # a bare except: everything
            else:
                ts = h.type.elts if isinstance(h.type, ast.Tuple) else [h.type]
                names = set()
                for t in ts:
                    if isinstance(t, ast.Name) and t.id in st.env:
                        held = st.env[t.id]     # a class the function was passed (except service_error:)
                        if held.ty not in ('module', 'type') or not held.name:
                            raise Untranslatable('an except clause naming something other than a class')
                        cls = held.name.rsplit('.', 1)[-1]
                        names.add(EXC_ALIAS.get(cls, cls))
                    elif isinstance(t, ast.Name):
                        names.add(EXC_ALIAS.get(t.id, t.id))
                    elif isinstance(t, ast.Attribute):
                        names.add(t.attr)
                    else:
                        raise Untranslatable('an except clause naming something other than a class')
            handlers.append((h, names))
        caught: dict[int, list] = {}
        for entry in d:
            cond, kind, payload, events, snap = entry
            if kind == 'toomany' and any(nm is None or 'BaseException' in nm for _, nm in handlers):
                raise Untranslatable('an except clause that would catch the sandbox stopping the run')
            if kind != 'raise':
                done.append(entry)
                continue
            k = next((i for i, (h, nm) in enumerate(handlers) if nm is None or nm & exc_classes(payload)), None)
            if k is None:
                done.append(entry)
                continue
            x = snap.fork(cond)
            x.env['\0caught'] = V(None, 'exc', name=payload)
            if handlers[k][0].name:
                x.env[handlers[k][0].name] = V(None, 'exc', name=payload)
            caught.setdefault(k, []).append(x)
        if s.orelse:
            live, d2, b2, c2 = self.block(s.orelse, live)
            done += d2
            b, c = b + b2, c + c2
        for k, xs in caught.items():
            h = handlers[k][0]
            l3, d3, b3, c3 = self.block(h.body, xs)
            for x in l3 + b3 + c3:             # the name an except clause binds is gone after it
                x.env.pop('\0caught', None)
                if h.name:
                    x.env.pop(h.name, None)
            live, done, b, c = live + l3, done + d3, b + b3, c + c3
        return self.merge_states(live), done, b, c

    def loop_for(self, s: ast.For, st: State) -> tuple:
        """for over range() with constant bounds, or over a tuple, list or
        dict constant, unrolled; break and continue end an iteration.  With
        strings and lists (fcp.seqs), also over the slots of one: the body
        runs once per slot under the slot's guard, and joins the path that
        skipped it."""
        z3 = self.z3
        if s.orelse:
            raise Untranslatable('for ... else')
        done: list = []
        st = st.fork(st.cond)
        items = Q.iter_items(self, s.iter, st, done)
        if self.seqs and len(items) > 256:
            raise Untranslatable('a loop of more than 256 steps')
        n0 = len(self.borrowed)
        if isinstance(s.iter, ast.Name) and s.iter.id in st.env and Q.is_list(st.env[s.iter.id]):
            self.borrowed.append(st.env[s.iter.id])
        states, exited = [st], []
        try:
            for g, v in items:
                if not states:
                    break
                entering = []
                for x in states:
                    y = x.fork(Q.both(z3, x.cond, g))
                    self.assign(s.target, v, y)
                    entering.append(y)
                live, d, b, c = self.block(s.body, entering)
                done += d
                exited += b
                if z3.is_true(g):
                    states = self.merge_states(live + c)
                    continue
                after = self.merge_states(live + c)
                j = Q.rejoin(self, g, after[0], states[0], entering[0].cond) \
                    if len(states) == 1 and len(after) == 1 else None
                states = [j] if j is not None else self.merge_states(
                    Q.pad(after + [x.fork(z3.And(x.cond, z3.Not(g))) for x in states]))
        finally:
            del self.borrowed[n0:]
        return self.merge_states(Q.pad(states + exited) if self.seqs else states + exited), done, [], []

    def loop_while(self, s: ast.While, st: State) -> tuple:
        """A while loop unrolled until no path is still in it: every path
        ends within max_calls calls on the interface, or 256 steps."""
        z3 = self.z3
        if s.orelse:
            raise Untranslatable('while ... else')
        bound = self.ifc.max_calls + 2 if self.ifc else 256
        done: list = []
        states, exited = [st.fork(st.cond)], []
        for _ in range(bound):
            if not states:
                break
            entering = []
            for x in states:
                x = x.fork(x.cond)
                c = self.test(s.test, x, done)
                exited.append(x.fork(z3.And(x.cond, z3.Not(c))))
                entering.append(x.fork(z3.And(x.cond, c)))
            live, d, b, cc = self.block(s.body, entering)
            done += d
            exited += b
            states = [x for x in self.merge_states(live + cc) if not z3.is_false(z3.simplify(x.cond))]
        if states:
            raise Untranslatable('a while loop the translation cannot bound')
        exited = [x for x in exited if not z3.is_false(z3.simplify(x.cond))]
        return self.merge_states(exited), done, [], []

    def assign(self, t, v: V, st: State):
        if self.keyed and K.assign(self, t, v, st):
            return
        if isinstance(t, ast.Name):
            st.env[t.id] = v
        elif isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and \
                st.env.get(t.value.id, V(None, 'none')).ty == 'self':
            if v.ty not in ('int', 'bool', 'none'):
                raise Untranslatable(f'self.{t.attr}: a field that is not a number or a boolean')
            st.env[f'self.{t.attr}'] = v
        elif isinstance(t, ast.Tuple):
            if v.ty != 'tuple' or len(v.items) != len(t.elts):
                raise Untranslatable('unpacking something other than a tuple of that length')
            for x, y in zip(t.elts, v.items):
                self.assign(x, y, st)
        else:
            raise Untranslatable(f'assignment to {type(t).__name__}')

    def exc_name(self, e, st: Optional[State] = None) -> str:
        if e is None:                          # a bare raise re-raises what an except clause caught
            if st is not None and '\0caught' in st.env:
                return st.env['\0caught'].name
            raise Untranslatable('raise with nothing to re-raise')
        if isinstance(e, ast.Name) and st is not None and e.id in st.env and st.env[e.id].ty == 'exc':
            return st.env[e.id].name
        if isinstance(e, ast.Call):
            e = e.func
        if isinstance(e, ast.Name):
            return e.id
        if isinstance(e, ast.Attribute):
            return e.attr
        raise Untranslatable('raise of something other than a named exception')

    # -- the function ---------------------------------------------------------------

    def outcome(self, fn: SW.Fn, kind: str, v, cond=None):
        """(code, {ret signal: value}) of one way the function ends, coded
        as the runner codes it (cond: the calls that end this way)."""
        z3 = self.z3
        zero = {r: self.zero(fn, r) for r in fn.rets}
        if kind == 'raise':
            return z3.IntVal(1 + fn.raises.index(v) if v in fn.raises else fn.other_exc), zero
        if kind == 'toomany':
            return z3.IntVal(fn.other_exc), zero
        vs = v.items if fn.tuple_ else (v,)
        ok = z3.BoolVal((not fn.tuple_ or v.ty == 'tuple') and len(vs) == len(fn.rets))
        terms = []
        seqs = {}
        for x, r in zip(vs, fn.rets):
            if r in fn.seqs:                   # a string or a list: its length and slots
                fits, ln, el = Q.ret_seq(self, fn, r, x, cond)
                ok = z3.And(ok, fits)
                seqs[r] = (ln, el)
                terms.append(None)
            elif fn.kinds.get(r, 'int') == 'bool':
                ok = z3.And(ok, z3.BoolVal(x.ty == 'bool'))
                terms.append(z3.If(x.t, z3.IntVal(1), z3.IntVal(0)) if x.ty == 'bool' else z3.IntVal(0))
            elif x.ty != 'int':
                ok = z3.BoolVal(False)
                terms.append(z3.IntVal(0))
            else:
                ok = z3.And(ok, x.t >= 0, x.t < (1 << fn.widths[r]))
                terms.append(x.t)
        terms += [z3.IntVal(0)] * (len(fn.rets) - len(terms))
        out = {}
        for r, t in zip(fn.rets, terms):
            if r in seqs:
                out[r] = SW._ZSeq(z3.If(ok, seqs[r][0], 0), [z3.If(ok, e, 0) for e in seqs[r][1]])
            else:
                out[r] = zero[r] if r in fn.seqs else z3.If(ok, t, z3.IntVal(0))
        return z3.If(ok, z3.IntVal(0), z3.IntVal(fn.other_val)), out

    def zero(self, fn: SW.Fn, r: str):
        """What a result signal carries when the call returned nothing."""
        z3 = self.z3
        return SW._ZSeq(z3.IntVal(0), [z3.IntVal(0)] * fn.seqs[r][1]) if r in fn.seqs else z3.IntVal(0)

    # -- objects --------------------------------------------------------------------

    def fields(self, st: State) -> dict:
        return {k[5:]: v for k, v in st.env.items() if k.startswith('self.')}

    def init_fields(self, fn: SW.Fn) -> dict:
        """The fields a new object starts with: its constructor, run on the
        design's init arguments, must end one way only."""
        z3 = self.z3
        self.widths, self.cur_class = fn.widths, fn.cls
        f = self.classes[fn.cls]['methods'].get('__init__')
        if f is None:
            return {}
        init = [V(z3.IntVal(int(x)), 'int') if not isinstance(x, bool) else V(z3.BoolVal(x), 'bool') for x in fn.init]
        outs = self.run(f.body, State(z3.BoolVal(True), self.bind(f, [V(None, 'self')] + init, {})))
        if len(outs) != 1 or outs[0][1] != 'return':
            raise Untranslatable('a constructor that can end more than one way')
        return self.fields(outs[0][4])

    def method_outcome(self, fn: SW.Fn, m: dict, kind: str, v):
        """(code, {ret signal: value}) of one method call, as the sandbox
        codes it: its own results, the others 0."""
        z3 = self.z3
        zero = {r: z3.IntVal(0) for r in fn.rets}
        if kind == 'raise':
            return z3.IntVal(1 + fn.raises.index(v) if v in fn.raises else fn.other_exc), zero
        if kind == 'toomany':
            return z3.IntVal(fn.other_exc), zero
        if not m['rets']:
            return z3.IntVal(0), zero
        vs = v.items if m['tuple_'] else (v,)
        ok = z3.BoolVal((not m['tuple_'] or v.ty == 'tuple') and len(vs) == len(m['rets']))
        out = dict(zero)
        for x, r in zip(vs, m['rets']):
            if fn.kinds.get(r, 'int') == 'bool':
                ok = z3.And(ok, z3.BoolVal(x.ty == 'bool'))
                out[r] = z3.If(x.t, z3.IntVal(1), z3.IntVal(0)) if x.ty == 'bool' else z3.IntVal(0)
            elif x.ty != 'int':
                ok = z3.BoolVal(False)
            else:
                ok = z3.And(ok, x.t >= 0, x.t < (1 << fn.widths[r]))
                out[r] = x.t
        return z3.If(ok, z3.IntVal(0), z3.IntVal(fn.other_val)), {r: z3.If(ok, t, z3.IntVal(0)) for r, t in out.items()}

    def step(self, fn: SW.Fn, fields: dict, args: list) -> tuple:
        """One call on the object: (fields after it, code, {ret: value}) as
        terms over the fields before it and the call's inputs (fn.args order,
        op first).  Every way the chosen method can end is merged: the
        fields at a raise are the fields where it was raised."""
        z3 = self.z3
        self.widths, self.cur_class = fn.widths, fn.cls
        cls = self.classes[fn.cls]
        vals = [V(a, 'bool' if k == 'bool' else 'int') for a, (_, _, k) in zip(args, fn.args)]
        entries = []
        del self.klinks[:]
        one = {'name': fn.name, 'op': None, 'pos': list(range(len(fn.args))), 'rets': fn.rets, 'tuple_': fn.tuple_}
        for m in fn.methods or [one]:           # a class with one method: every call is a call of it
            f = cls['methods'].get(m['name'])
            if f is None:
                raise Untranslatable(f'{fn.cls}.{m["name"]}: no such method')
            margs = [vals[p] for p in m['pos']]
            env = {f'self.{k}': v for k, v in fields.items()}
            env.update(self.bind(f, margs if m['name'] in cls['static'] else [V(None, 'self')] + margs, {}))
            start = z3.BoolVal(True) if m['op'] is None else vals[0].t == m['op']
            for cond, kind, payload, events, snap in self.run(f.body, State(start, env)):
                for cond, payload in (K.cases(self, cond, kind, payload) if self.keyed else [(cond, payload)]):
                    code, rets = self.method_outcome(fn, m, kind, payload)
                    entries.append((cond, self.fields(snap), code, rets))
        keys = set(fields)
        if any(set(f2) != keys for _, f2, _, _ in entries):
            raise Untranslatable('a method that adds a field the constructor does not set')
        last = entries[-1]
        new, code, rets = dict(last[1]), last[2], dict(last[3])
        for cond, f2, c, r in reversed(entries[:-1]):
            new = {k: self.merge(cond, f2[k], new[k]) for k in keys}
            code = z3.If(cond, c, code)
            rets = {x: z3.If(cond, r[x], rets[x]) for x in fn.rets}
        return new, code, rets

    def ends(self, fn: SW.Fn, args: list) -> list:
        """Every way one call ends: (cond, kind, payload, events)."""
        z3 = self.z3
        self.widths = fn.widths
        f = self.funcs[self.fname]
        vals = [Q.from_arg(self, a, k) if sig in fn.seqs else V(a, 'bool' if k == 'bool' else 'int')
                for a, (_, sig, k) in zip(args, fn.args)]
        if self.seqs:
            self.dom = Q.arg_dom(z3, fn, args)
        if self.ifc is not None and self.ifc.arg is not None:
            vals.insert(self.ifc.arg, V(None, 'iface'))
        return self.run(f.body, State(z3.BoolVal(True), self.bind(f, vals, {})))

    def call(self, fn: SW.Fn, args: list):
        """(outcome, {ret signal: value}) of one call of a pure function as
        terms over args (z3 terms in fn.args order)."""
        z3 = self.z3
        code, rets = z3.IntVal(fn.other_exc), {r: self.zero(fn, r) for r in fn.rets}
        for c, kind, v, ev, _ in reversed(self.ends(fn, args)):
            if ev:
                raise Untranslatable('calls on an interface in a pure function')
            k, rs = self.outcome(fn, kind, v, c)
            code = z3.If(c, k, code)
            rets = {r: Q.ite(z3, c, rs[r], rets[r]) for r in fn.rets}
        return code, rets


def compile_terms(z3, terms: list, args: list):
    """A Python function of the arguments computing the terms, one line per
    shared subterm: evaluating the translation on a scope of a million calls
    by substitution would take minutes."""
    names: dict[int, str] = {}
    lines: list[str] = []
    argn = {a.get_id(): f'x{i}' for i, a in enumerate(args)}
    bins = {z3.Z3_OP_LE: '<=', z3.Z3_OP_LT: '<', z3.Z3_OP_GE: '>=', z3.Z3_OP_GT: '>', z3.Z3_OP_EQ: '==',
            z3.Z3_OP_IDIV: '//', z3.Z3_OP_MOD: '%', z3.Z3_OP_SUB: '-'}

    def leaf(e) -> Optional[str]:
        key = e.get_id()
        if key in argn:
            return argn[key]
        if key in names:
            return names[key]
        if z3.is_int_value(e):
            return str(e.as_long())
        if z3.is_true(e):
            return 'True'
        if z3.is_false(e):
            return 'False'
        return None

    def go(root) -> str:
        todo = [(root, False)]                 # (without recursion: the terms of long sequences are deep)
        while todo:
            e, ready = todo.pop()
            if leaf(e) is not None:
                continue
            if not ready:
                todo.append((e, True))
                todo.extend((c, False) for c in e.children() if leaf(c) is None)
                continue
            k = e.decl().kind()
            ch = [leaf(c) for c in e.children()]
            if k == z3.Z3_OP_ITE:
                out = f'({ch[1]} if {ch[0]} else {ch[2]})'
            elif k in bins and len(ch) == 2:
                out = f'({ch[0]} {bins[k]} {ch[1]})'
            elif k == z3.Z3_OP_SUB:
                out = '(' + ' - '.join(ch) + ')'
            elif k == z3.Z3_OP_ADD:
                out = '(' + ' + '.join(ch) + ')'
            elif k == z3.Z3_OP_MUL:
                out = '(' + ' * '.join(ch) + ')'
            elif k == z3.Z3_OP_UMINUS:
                out = f'(-{ch[0]})'
            elif k == z3.Z3_OP_AND:
                out = '(' + ' and '.join(ch) + ')'
            elif k == z3.Z3_OP_OR:
                out = '(' + ' or '.join(ch) + ')'
            elif k == z3.Z3_OP_NOT:
                out = f'(not {ch[0]})'
            elif k == z3.Z3_OP_DISTINCT and len(ch) == 2:
                out = f'({ch[0]} != {ch[1]})'
            else:
                raise Untranslatable(f'compiling {e.decl().name()}')
            v = f't{len(names)}'
            lines.append(f'    {v} = {out}')
            names[e.get_id()] = v
        return leaf(root)
    outs = [go(t) for t in terms]
    src = f'def f({", ".join(f"x{i}" for i in range(len(args)))}):\n' + '\n'.join(lines) + \
        f'\n    return ({", ".join(outs)},)\n'
    env: dict = {}
    exec(compile(src, '<fcp.prove>', 'exec'), env)
    return env['f']


def check_translation(fn: SW.Fn, tr: Translator, calls: list, res: dict) -> Optional[dict]:
    """The translation's outcome and values on every call of the scope
    against the code's own; the first difference, or None."""
    z3 = tr.z3
    args = [SW._ZSeq(z3.Int(f'a_{n}_len'), [z3.Int(f'a_{n}_{j}') for j in range(fn.seqs[sig][1])]) if sig in fn.seqs
            else z3.Int(f'a_{n}') if k != 'bool' else z3.Bool(f'a_{n}') for n, sig, k in fn.args]
    code, rets = tr.call(fn, args)
    outs = [code] + [t for r in fn.rets for t in Q.flat(rets[r])]
    f = compile_terms(z3, [z3.simplify(t) for t in outs], [t for a in args for t in Q.flat(a)])
    for i, c in enumerate(calls):
        got = f(*[y for x, (_, sig, k) in zip(c, fn.args)
                  for y in ([bool(x)] if k == 'bool' else Q.flat_value(fn, sig, x))])
        vals, at = {}, 1
        for r in fn.rets:                        # a sequence: its length, then its slots
            n = 1 + fn.seqs[r][1] if r in fn.seqs else 1
            vals[r] = [int(v) for v in got[at:at + n]] if r in fn.seqs else int(got[at])
            at += n
        want = res['code'][i]
        wv = {r: Q.flat_value(fn, r, res['ret'][r][i]) if r in fn.seqs else int(res['ret'][r][i]) for r in fn.rets}
        if want == fn.other_exc and got[0] == fn.other_exc:
            continue                             # another exception or a time-out: the same outcome
        if got[0] != want or (want == 0 and vals != wv):
            return {'call': list(c), 'code': want, 'ret': wv, 'translated_code': int(got[0]), 'translated_ret': vals}
    return None


def check_encoding(S, s: str, fn: SW.Fn, enc, calls: list, res: dict) -> Optional[dict]:
    """The reading's integer encoding against its compiled monitors on every
    cycle of the scope's trace: for every property, the calls at which the
    encoding says it fails (on the k calls ending there) must be exactly the
    calls at which the monitor says it fails.  The first difference, or None.
    A proof rests on the encoding, so it is checked where the monitors ran."""
    z3 = enc.z3
    k = enc.k
    cols = SW.trace(fn, calls, res)
    chk = SW.check(S, s, cols, keep=len(calls) + 1)
    frame = S.b.frame_ids
    sigs = fn.signals + fn.base_signals
    xs = [t for i in range(1, k + 1) for n in sigs for t in Q.flat(enc.x[(n, i)])]
    verdict = {**enc.raw_holds, **enc.aholds}
    items = list(dict.fromkeys(sorted(iid for (st, iid, i) in verdict if st == s and iid not in frame)))
    terms = [verdict[(s, iid, i)] for iid in items for i in range(1, k + 1)]
    f = compile_terms(z3, [z3.simplify(t) for t in terms], xs)
    col = []
    for n in sigs:
        if n not in fn.seqs:
            col.append(cols[n])
            continue
        rows = [Q.flat_value(fn, n, fn.decode(n, lambda p, t=t: cols[p][t])) for t in range(len(calls) + 1)]
        col += [list(c) for c in zip(*rows)]     # one column for the length and one per slot
    fails = {iid: set(chk[iid]['fails']) for iid in items}
    n_sig = len(col)
    for t in range(1, len(calls) + 1):     # cycle t is call t (cycle 0 is the reset)
        m = min(t, k)
        window = [c[t - m + j + 1] for j in range(m) for c in col]
        window += [0] * (n_sig * (k - m))
        got = f(*window)
        for j, iid in enumerate(items):
            ok = got[j * k + m - 1]
            if (not ok) != (t in fails[iid]):
                return {'item': iid, 'call': list(calls[t - 1]), 'cycle': t,
                        'encoding': 'fails' if not ok else 'holds',
                        'monitor': 'fails' if t in fails[iid] else 'holds'}
    return None


def baseline(fn: SW.Fn) -> tuple:
    """For a change: the old code as a function of the arguments it takes
    (as software.baseline_values runs it), its translation, and the
    positions of its arguments among the new function's."""
    b = fn.baseline
    names = [a for a, _, _ in fn.args]
    pos = [names.index(a) for a in b['args']]
    old = SW.Fn(b['name'], [fn.args[i] for i in pos], b['returns'], fn.tuple_, b['outcome'], fn.raises, fn.widths,
                {}, fn.seqs, fn.kinds)
    return old, Translator(b['path'], b['name']), pos


def prove(S, s: str, fn: SW.Fn, src: str, calls: list, res: dict, only: Optional[set] = None,
          timeout: int = 120000, check_spec: bool = True) -> dict:
    """Every requirement of reading s on implementation src over all calls
    the interface can carry: PROVED, FAILS (with the calls, confirmed by
    running the code), UNKNOWN (z3 gave up), or the reason nothing was tried
    (untranslatable code, a difference on the scope)."""
    z3 = __import__('z3')
    CONF.tag(None)                               # what z3 answers from here on is shared by the requirements
    if fn.stateful or fn.structured or fn.methods or (fn.has_seq and fn.baseline):
        return {'status': 'unsupported', 'why': 'only pure functions on integers, booleans, strings and lists'}
    old = None
    try:
        tr = Translator(src, fn.name, seqs=fn.has_seq)
        bad = check_translation(fn, tr, calls, res)
        if bad is None and fn.baseline:       # a change: the old code is translated and checked too
            old, old_tr, pos = baseline(fn)
            base = SW.baseline_values(fn, calls)
            b = fn.baseline
            ores = {'code': base[b['outcome']], 'ret': {r: base[r] for r in b['returns']}}
            bad = check_translation(old, old_tr, [tuple(c[i] for i in pos) for c in calls], ores)
            if bad is not None:
                bad = {'baseline': bad}
    except Untranslatable as e:
        return {'status': 'untranslatable', 'why': str(e)}
    if bad is not None:
        return {'status': 'translation differs', 'why': bad}
    k, exact = SW.horizon(S, [s])
    try:
        enc = SW._IntSpec(S, [s], fn, max(1, k))
    except SW.Unsupported as e:
        return {'status': 'unsupported', 'why': str(e)}
    if check_spec:
        bad = check_encoding(S, s, fn, enc, calls, res)
        if bad is not None:
            return {'status': 'encoding differs', 'why': bad}
    sol_base = list(enc.dom)
    codes = {}                                 # the outcome of each call, an if-tree over the code's tests
    defs = []                                  # what the code makes of each output, as a term of the arguments
    for i in range(1, enc.k + 1):
        args = [enc.x[(sig, i)] if kind != 'bool' else enc.x[(sig, i)] != 0 for _, sig, kind in fn.args]
        code, rets = tr.call(fn, args)
        at = len(defs)
        codes[i] = code
        defs.append((enc.x[(fn.outcome, i)], code))
        for r in fn.rets:
            defs += list(zip(Q.flat(enc.x[(r, i)]), Q.flat(rets[r])))
        sol_base += [x == y for x, y in defs[at:]]
        if old is not None:                    # the old code's answer to the same call
            ocode, orets = old_tr.call(old, [args[j] for j in pos])
            sol_base.append(enc.x[(fn.baseline['outcome'], i)] == ocode)
            for r in fn.baseline['returns']:
                sol_base.append(enc.x[(r, i)] == orets[r])
    frame = S.b.frame_ids
    items = {}
    by_req: dict[str, list] = {}
    for (st, iid, i), h in enc.raw_holds.items():  # judged as the scope judges: assumptions do not excuse
        if iid in frame:
            continue
        by_req.setdefault(S.mon(s).items[iid].req, []).append((iid, i, h))

    def settle(hs: list, base: list, goal, ms: int) -> dict:
        sol = z3.Solver()
        sol.set('timeout', ms)
        sol.add(*base)
        sol.add(goal)
        r = sol.check()
        if r == z3.unsat:
            return {'status': 'PROVED' if exact else 'PROVED-BOUNDED', 'k': enc.k}
        if r != z3.sat:
            return {'status': 'UNKNOWN', 'why': sol.reason_unknown(), 'k': enc.k}
        md = sol.model()
        cs = [tuple(enc.value(md, sig, i) for _, sig, _ in fn.args) for i in range(1, enc.k + 1)]
        broken = sorted({iid for iid, i, h in hs if z3.is_false(md.eval(h, model_completion=True))})
        # the calls run on the real code, and the trace on the compiled monitors
        again = SW.run(fn, src, cs)
        chk = SW.check(S, s, SW.trace(fn, cs, again))
        return {'status': 'FAILS', 'calls': [list(c) for c in cs], 'items': broken,
                'replay': {'code': again['code'], 'ret': again['ret']},
                'confirmed': any(chk[iid]['first'] is not None for iid in broken), 'k': enc.k}

    reqs = [(req, hs) for req, hs in sorted(by_req.items()) if only is None or req in only]
    out = {'status': 'ok', 'exact': exact, 'k': enc.k, 'requirements': items}
    if not fn.has_seq:
        for req, hs in reqs:
            CONF.tag(req)
            items[req] = settle(hs, sol_base, z3.Or(*[z3.Not(h) for _, _, h in hs]), timeout)
        return out
    # Code over strings and lists.  With the outputs replaced by the code's terms every goal is a
    # function of the arguments alone, and the agreements between the code's subterms and the
    # reading's are proved from the leaves up (fcp.sweep) before the goals go to z3.
    inputs = [t for i in range(1, enc.k + 1) for _, sig, _ in fn.args for t in Q.flat(enc.x[(sig, i)])]
    ids = {v.get_id() for v in inputs}
    d_in = [c for c in enc.dom if SWP.variables(z3, c) <= ids]
    d_out = [z3.substitute(c, *defs) for c in enc.dom if not SWP.variables(z3, c) <= ids]
    hs2 = {req: [(iid, i, z3.substitute(h, *defs)) for iid, i, h in hs] for req, hs in reqs}
    pool = _samples(fn, enc, calls, res, 4096)
    # Each goal (a requirement's instance failing) as the conjunction it is: what it asserts of the
    # path that returned, fact by fact, and the rest.
    roots, spans = list(d_out), {}
    for req, _ in reqs:
        for n, (_, _, h) in enumerate(hs2[req]):
            cj = SWP.conjuncts(z3, z3.Not(h))
            spans[(req, n)] = (len(roots), len(cj))
            roots += cj
    at = len(roots)
    roots += [codes[i] for i in sorted(codes)]
    new, out['sweep'] = SWP.sweep(z3, roots, inputs, d_in, pool[::max(1, len(pool) // 256)])
    base = d_in + new[:len(d_out)]
    codes = dict(zip(sorted(codes), new[at:]))                    # in the terms the goals are now in
    for req, _ in reqs:
        CONF.tag(req)
        gs = [new[a:a + m] for n in range(len(hs2[req])) for a, m in [spans[(req, n)]]]
        items[req] = settle(hs2[req], base, z3.Or(*[_all(z3, g) for g in gs]), min(timeout, WHOLE))
        if items[req]['status'] != 'UNKNOWN':
            continue
        # Still open: item by item, with the goal's small parts (the facts of the path, one slot
        # each) as assumptions under which its large parts are swept again.
        def part(item, cj: list) -> dict:
            size = [len(SWP.order([c])) for c in cj]
            small = [c for c, z in zip(cj, size) if z <= SMALL]
            large = [c for c, z in zip(cj, size) if z > SMALL]
            if not small and len(large) > 1:                       # no fact of the path: the first part,
                small, large, size = large[:1], large[1:], size[1:]    # which says what the call did
            v, how = None, {'small': len(small), 'large': sorted(z for z in size if z > SMALL)}
            if small and large:
                some = _satisfying(z3, base + small, inputs, pool)
                if some == 'none':                                 # the goal's own parts exclude each other
                    v = {'status': 'PROVED' if exact else 'PROVED-BOUNDED', 'k': enc.k}
                elif some:
                    large, st2 = SWP.sweep(z3, large, inputs, base + small, some[:256], budget=60.0)
                    how.update(st2)
                    v = settle([item], base + small, _all(z3, large), timeout)
            v = v or settle([item], base, _all(z3, cj), timeout)
            v['sweep'] = how
            return v

        parts = []
        for item, cj in zip(hs2[req], gs):
            i = item[1]
            ends = _leaves(z3, codes[i]) if all(len(SWP.order([c])) > SMALL for c in cj) else None
            v = None
            if ends:
                # A goal that says nothing of the path (an invariant): one case per outcome of the
                # call.  The outcome is one of them, so the goal holds on some case or on none.
                cases = []
                for val in ends:
                    cases.append(part(item, SWP.conjuncts(z3, codes[i] == val) + cj))
                    cases[-1]['sweep']['outcome'] = val
                    if cases[-1]['status'] == 'FAILS':
                        break
                v = dict(_worst(cases), sweep={'cases': [c['sweep'] for c in cases]})
            if v is None or v['status'] == 'UNKNOWN':
                v = part(item, cj)
            parts.append(v)
            if v['status'] == 'FAILS':
                break
        items[req] = dict(_worst(parts), sweep=[v['sweep'] for v in parts])
    return out


def _worst(vs: list) -> dict:
    """What several verdicts on parts of one question come to: a failure, else an open part, else proved."""
    return ([v for v in vs if v['status'] == 'FAILS'] or [v for v in vs if v['status'] == 'UNKNOWN'] or vs)[0]


def _leaves(z3, t) -> Optional[list]:
    """The integers an if-tree ends in; None where an end is not a constant."""
    out, stack, seen = set(), [t], set()
    while stack:
        e = stack.pop()
        if e.get_id() in seen:
            continue
        seen.add(e.get_id())
        if z3.is_int_value(e):
            out.add(e.as_long())
        elif z3.is_app(e) and e.decl().kind() == z3.Z3_OP_ITE:
            stack += [e.arg(1), e.arg(2)]
        else:
            return None
    return sorted(out)


SMALL = 64          # a part of a goal this size or smaller is an assumption when the rest is swept again
WHOLE = 10000       # milliseconds a requirement's goal gets as a whole, before it is taken item by item


def _all(z3, xs: list):
    return z3.BoolVal(True) if not xs else xs[0] if len(xs) == 1 else z3.And(*xs)


def _satisfying(z3, hyp: list, inputs: list, pool: list):
    """The samples of the pool on which every formula of hyp holds; if there
    are none, one from z3, or 'none' where z3 shows there is none (an empty
    list: z3 gave up, or hyp cannot be evaluated)."""
    try:
        nodes = SWP.order(hyp)
        f = SWP.simulator(z3, nodes, inputs)
        at = {e.get_id(): i for i, e in enumerate(nodes)}
        want = [at[h.get_id()] for h in hyp]
        out = []
        for x in pool:
            v = f(x)
            if all(v[i] for i in want):
                out.append(x)
    except (SWP.NoSim, RecursionError, ZeroDivisionError, TypeError, IndexError):
        return []
    if out:
        return out
    sol = z3.Solver()
    sol.set('timeout', 10000)
    sol.add(*hyp)
    r = sol.check()
    if r == z3.unsat:
        return 'none'
    if r != z3.sat:
        return []
    md = sol.model()
    return [[z3.is_true(y) if z3.is_bool(v) else y.as_long()
             for v in inputs for y in [md.eval(v, model_completion=True)]]]


def _samples(fn: SW.Fn, enc, calls: list, res: dict, n: int = 256) -> list:
    """Up to n windows of the scope's calls as values of the encoding's
    argument variables, spread evenly over the outcomes the code gave."""
    k = enc.k
    by: dict = {}
    for p in range(len(calls) - k + 1):
        by.setdefault(res['code'][p + k - 1], []).append(p)
    out = []
    for _, ps in sorted(by.items()):
        m = max(1, n // len(by))
        for p in ps[::max(1, len(ps) // m)][:m]:
            out.append([y for c in calls[p:p + k] for x, (_, sig, _) in zip(c, fn.args)
                        for y in Q.flat_value(fn, sig, x)])
    return out


# ----------------------------------------------------------------------------
# code with effects: every run, for every script of answers
# ----------------------------------------------------------------------------

def _ev_sigs(ifc) -> list[str]:
    from . import effects as FX
    return sorted({x for m in ifc.methods for x in FX.arg_sigs(m)})


def effects_signals(fn: SW.Fn, ifc) -> list[tuple[str, int]]:
    """The interface's own signals: phase, op, answer, the calls' arguments."""
    names = [ifc.phase, ifc.op, ifc.answer] + _ev_sigs(ifc) + ([ifc.handle] if ifc.handle else [])
    return [(n, fn.widths[n]) for n in names]


def conversation_terms(tr: Translator, fn: SW.Fn, ifc, ends: list, K: int) -> tuple[dict, dict]:
    """Every signal at cycles 1..K of one run (after its reset) as terms over
    the arguments and the answers, and whether the run still lasts at each
    cycle: a path's events are its first cycles, its return the next one."""
    z3 = tr.z3
    by_op = {m['op']: m for m in ifc.methods}
    names = [n for n, _ in effects_signals(fn, ifc)] + fn.rets + [fn.outcome]
    zero = z3.IntVal(0)
    sig, live = {}, {}
    for c in range(1, K + 1):
        built = []
        for cond, kind, payload, events, _ in ends:
            L = len(events)
            d = {n: zero for n in names}
            if c <= L:
                op, terms, a, hn = events[c - 1]
                m = by_op[op]
                d[ifc.op] = z3.IntVal(op)
                if ifc.handle:
                    d[ifc.handle] = z3.IntVal(min(hn, (1 << fn.widths[ifc.handle]) - 1))
                d[ifc.answer] = a if m.get('answers') else zero
                from . import effects as FX
                for x, t in zip(FX.arg_sigs(m), terms):
                    d[x] = t
            elif c == L + 1:
                code, rets = tr.outcome(fn, kind, payload)
                d[ifc.phase] = z3.IntVal(1)
                d[fn.outcome] = code
                d.update(rets)
            else:
                continue
            built.append((cond, d))
        live[c] = z3.Or(*[b[0] for b in built]) if built else z3.BoolVal(False)
        for n in names:
            if not built:
                sig[(n, c)] = zero
                continue
            t = built[-1][1][n]
            for cond, d in reversed(built[:-1]):
                t = z3.If(cond, d[n], t)
            sig[(n, c)] = t
    return sig, live


def _arg_vars(z3, fn: SW.Fn) -> list:
    return [z3.Int(f'a_{n}') if k != 'bool' else z3.Bool(f'a_{n}') for n, _, k in fn.args]


def check_effects_translation(fn: SW.Fn, ifc, tr: Translator, ends: list, args: list, runs: list,
                              res: list) -> Optional[dict]:
    """On every run of the scope, the path its arguments and script select
    makes the calls the code made, with the same arguments and answers, and
    ends as the code ended.  The first difference, or None."""
    z3 = tr.z3
    M = tr.n_ans
    ans = [z3.Int(f'ans_{j}') for j in range(M)]
    terms, shape = [], []
    for cond, kind, payload, events, _ in ends:
        code, rets = tr.outcome(fn, kind, payload)
        shape.append((len(terms), [(op, len(ts), hn) for op, ts, _, hn in events]))
        terms += [cond, code] + [rets[r] for r in fn.rets]
        for op, ts, a, hn in events:
            terms += list(ts) + [a]
    f = compile_terms(z3, [z3.simplify(t) for t in terms], args + ans)
    kinds = [k for _, _, k in fn.args]
    by_op = {m['op']: m for m in ifc.methods}
    for i, ((a, script), r) in enumerate(zip(runs, res)):
        vals = [bool(x) if k == 'bool' else int(x) for x, k in zip(a, kinds)]
        out = f(*vals, *[script[j] if j < len(script) else 0 for j in range(M)])
        hit = [p for p, (at, _) in enumerate(shape) if out[at]]
        if len(hit) != 1:
            return {'run': i, 'why': f'{len(hit)} paths of the translation take this run'}
        at, evs = shape[hit[0]]
        code, rets = out[at + 1], out[at + 2:at + 2 + len(fn.rets)]
        got = []
        pos = at + 2 + len(fn.rets)
        for op, n, hn in evs:
            got.append([op, [int(x) for x in out[pos:pos + n]], int(out[pos + n]), hn])
            pos += n + 1
        want = []
        for e in r['events']:
            m = by_op[e[0]]
            from . import effects as FX
            ws = [int(v) if isinstance(v, (int, bool)) and v is not None and 0 <= int(v) < (1 << fn.widths[s])
                  else 0 for s, v in zip(FX.arg_sigs(m), e[1])]
            want.append([e[0], ws, e[2] if m.get('answers') else 0, e[4] if len(e) > 4 else 0])
        wret = int(r['ret']) if r['code'] == 0 and r['ret'] is not None else 0
        if got != want or code != r['code'] or (r['code'] == 0 and int(rets[0]) != wret):
            return {'run': i, 'args': list(a), 'script': list(script), 'code': r['code'], 'events': want,
                    'translated_code': int(code), 'translated_events': got}
    return None


def check_effects_encoding(S, s: str, fn: SW.Fn, ifc, enc, runs: list, res: list) -> Optional[dict]:
    """The reading's integer encoding against the compiled monitors on every
    cycle of every run of the scope (each run starts after a reset, as the
    encoding's cycle 1 does).  The first difference, or None."""
    from . import effects as FX
    z3 = enc.z3
    K = enc.k
    cols, where = FX.trace(fn, ifc, runs, res)
    chk = SW.check(S, s, cols, keep=len(where) + 1)
    frame = S.b.frame_ids
    sigs = list(dict.fromkeys(fn.signals + [n for n, _ in effects_signals(fn, ifc)]))
    xs = [enc.x[(n, i)] for i in range(1, K + 1) for n in sigs]
    verdict = {**enc.raw_holds, **enc.aholds}       # properties ungated, and the assumptions themselves
    items = list(dict.fromkeys(iid for (st, iid, i) in verdict if st == s and iid not in frame))
    f = compile_terms(z3, [z3.simplify(verdict[(s, iid, i)]) for iid in items for i in range(1, K + 1)], xs)
    fails = {iid: set(chk[iid]['fails']) for iid in items}
    by_run: dict[int, list[int]] = {}
    for c, w in enumerate(where):
        if w is not None:
            by_run.setdefault(w[0], []).append(c)
    for run, cyc in by_run.items():
        window = [cols[n][c] for c in cyc for n in sigs] + [0] * (len(sigs) * (K - len(cyc)))
        got = f(*window)
        for j, c in enumerate(cyc):
            for t, iid in enumerate(items):
                ok = got[t * K + j]
                if (not ok) != (c in fails[iid]):
                    return {'item': iid, 'run': run, 'call': j + 1, 'encoding': 'fails' if not ok else 'holds',
                            'monitor': 'fails' if c in fails[iid] else 'holds'}
    return None


def prove_effects(S, s: str, fn: SW.Fn, ifc, src: str, runs: list, res: list, only: Optional[set] = None,
                  timeout: int = 300000) -> dict:
    """Every requirement of reading s on code with effects, over every run:
    every argument the interface carries and every script of answers.  A run
    is at most max_calls calls and its return, after a reset, so one run of
    max_calls + 1 cycles decides each requirement: PROVED, or FAILS at a
    run that is replayed on the code and confirmed on the monitors."""
    import z3
    from . import effects as FX
    CONF.tag(None)
    try:
        tr = Translator(src, fn.name, ifc)
        args = _arg_vars(z3, fn)
        ends = tr.ends(fn, args)
        bad = check_effects_translation(fn, ifc, tr, ends, args, runs, res)
    except Untranslatable as e:
        return {'status': 'untranslatable', 'why': str(e)}
    if bad is not None:
        return {'status': 'translation differs', 'why': bad}
    K = ifc.max_calls + 1
    try:
        enc = SW._IntSpec(S, [s], fn, K, extra=tuple(effects_signals(fn, ifc)))
    except SW.Unsupported as e:
        return {'status': 'unsupported', 'why': str(e)}
    bad = check_effects_encoding(S, s, fn, ifc, enc, runs, res)
    if bad is not None:
        return {'status': 'encoding differs', 'why': bad}
    sig, live = conversation_terms(tr, fn, ifc, ends, K)
    ans = [z3.Int(f'ans_{j}') for j in range(tr.n_ans)]
    base = list(enc.dom) + [z3.And(a >= 0, a < len(ifc.answers)) for a in ans]
    for (n, sg, k), a in zip(fn.args, args):
        for c in range(1, K + 1):
            base.append(enc.x[(sg, c)] == (z3.If(a, 1, 0) if k == 'bool' else a))
    for (n, c), t in sig.items():
        base.append(enc.x[(n, c)] == t)
    frame = S.b.frame_ids
    by_req: dict[str, list] = {}
    for (st, iid, c), h in enc.raw_holds.items():   # judged as the scope judges: assumptions do not excuse
        if iid not in frame:
            by_req.setdefault(S.mon(s).items[iid].req, []).append((iid, c, h))
    items = {}
    for req, hs in sorted(by_req.items()):
        if only is not None and req not in only:
            continue
        CONF.tag(req)
        sol = z3.Solver()
        sol.set('timeout', timeout)
        sol.add(*base)
        sol.add(z3.Or(*[z3.And(live[c], z3.Not(h)) for _, c, h in hs]))
        r = sol.check()
        if r == z3.unsat:
            items[req] = {'status': 'PROVED', 'k': K}
        elif r == z3.sat:
            md = sol.model()
            a = tuple(int(bool(md.eval(x, model_completion=True))) if k == 'bool' else
                      md.eval(x, model_completion=True).as_long() for x, (_, _, k) in zip(args, fn.args))
            script = tuple(md.eval(x, model_completion=True).as_long() for x in ans)
            run = [(a, script)]
            again = FX.run(fn, ifc, src, run)
            cols, where = FX.trace(fn, ifc, run, again)
            chk = SW.check(S, s, cols)
            broken = sorted({iid for iid, c, h in hs if z3.is_true(md.eval(live[c], model_completion=True)) and
                             z3.is_false(md.eval(h, model_completion=True))})
            items[req] = {'status': 'FAILS', 'call': FX.call_text(fn, ifc, run, 0), 'items': broken,
                          'conversation': FX.conversation(fn, ifc, run, again, 0),
                          'confirmed': any(chk[iid]['first'] is not None for iid in broken), 'k': K}
        else:
            items[req] = {'status': 'UNKNOWN', 'why': sol.reason_unknown(), 'k': K}
    return {'status': 'ok', 'exact': True, 'k': K, 'requirements': items}


# ----------------------------------------------------------------------------
# objects: every sequence of calls up to a length, every argument
# ----------------------------------------------------------------------------

def _field_vars(z3, fields: dict) -> tuple[list, dict]:
    xs, out = [], {}
    for k, v in sorted(fields.items()):
        x = z3.Bool(f'field_{k}') if v.ty == 'bool' else z3.Int(f'field_{k}')
        xs.append(x)
        out[k] = V(x, v.ty)
    return xs, out


def _concrete(z3, v: V):
    t = z3.simplify(v.t)
    if z3.is_true(t) or z3.is_false(t):
        return z3.is_true(t)
    if z3.is_int_value(t):
        return t.as_long()
    raise Untranslatable('a constructor whose fields are not constants')


def _sequences(calls: list) -> list[list[int]]:
    """Indices of the calls of each object (a None starts a new one)."""
    out, cur = [], None
    for i, c in enumerate(calls):
        if c is None:
            cur = []
            out.append(cur)
        elif cur is not None:
            cur.append(i)
    return [x for x in out if x]


def check_object_translation(fn: SW.Fn, tr: Translator, calls: list, res: dict) -> Optional[dict]:
    """The translated step, from the constructor's fields, on every sequence
    of the scope: the outcome and results of every call as the code gave
    them.  The first difference, or None."""
    z3 = tr.z3
    init = tr.init_fields(fn)
    fxs, fsym = _field_vars(z3, init)
    args = _arg_vars(z3, fn)
    new, code, rets = tr.step(fn, fsym, args)
    order = sorted(init)
    f = compile_terms(z3, [z3.simplify(new[k].t) for k in order] + [z3.simplify(code)] +
                      [z3.simplify(rets[r]) for r in fn.rets], fxs + args)
    start = [_concrete(z3, init[k]) for k in order]
    kinds = [k for _, _, k in fn.args]
    for seq in _sequences(calls):
        cur = list(start)
        for i in seq:
            out = f(*cur, *[bool(x) if k == 'bool' else int(x) for x, k in zip(calls[i], kinds)])
            cur = list(out[:len(order)])
            got, vals = out[len(order)], out[len(order) + 1:]
            want = res['code'][i]
            if want == fn.other_exc and got == fn.other_exc:
                continue
            wv = [int(res['ret'][r][i]) for r in fn.rets]
            if got != want or (want == 0 and [int(v) for v in vals] != wv):
                return {'call': list(calls[i]), 'index': i, 'code': want, 'ret': wv,
                        'translated_code': int(got), 'translated_ret': [int(v) for v in vals]}
    return None


def check_object_encoding(S, s: str, fn: SW.Fn, enc, calls: list, res: dict) -> Optional[dict]:
    """The reading's encoding against the compiled monitors on every call of
    every sequence of the scope, each from its reset.  The first difference,
    or None."""
    z3 = enc.z3
    K = enc.k
    cols = SW.trace(fn, calls, res)
    chk = SW.check(S, s, cols, keep=len(calls) + 1)
    frame = S.b.frame_ids
    sigs = fn.signals
    xs = [enc.x[(n, i)] for i in range(1, K + 1) for n in sigs]
    verdict = {**enc.raw_holds, **enc.aholds}
    items = list(dict.fromkeys(iid for (st, iid, i) in verdict if st == s and iid not in frame))
    f = compile_terms(z3, [z3.simplify(verdict[(s, iid, i)]) for iid in items for i in range(1, K + 1)], xs)
    fails = {iid: set(chk[iid]['fails']) for iid in items}
    for seq in _sequences(calls):
        if len(seq) > K:
            return {'why': f'a sequence of {len(seq)} calls is longer than the encoding ({K})'}
        cyc = [i + 1 for i in seq]                # cycle t is call t - 1 (cycle 0 is the first reset)
        got = f(*([cols[n][c] for c in cyc for n in sigs] + [0] * (len(sigs) * (K - len(cyc)))))
        for j, c in enumerate(cyc):
            for t, iid in enumerate(items):
                ok = got[t * K + j]
                if (not ok) != (c in fails[iid]):
                    return {'item': iid, 'call': j + 1, 'calls': [list(calls[i]) for i in seq[:j + 1]],
                            'encoding': 'fails' if not ok else 'holds',
                            'monitor': 'fails' if c in fails[iid] else 'holds'}
    return None


def _consts(S, s: str, src: str, limit: int = 40) -> list[int]:
    """The numbers the code and the reading mention: the constants an
    invariant is likely to compare the state with."""
    from .lang import const_eval, parse
    out = {0, 1}
    with open(src) as f:
        tree = ast.parse(f.read())
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, int) and not isinstance(n.value, bool):
            out.add(n.value)
    fs = S.b.fsets[s]
    texts = [str(t) for t in (fs.get('defs') or {}).values()]
    for g in fs.get('ghosts') or []:
        texts.append(str(g['next']))
        out.add(const_eval(g.get('init', 0), S.b.iface.params))
        out.update(const_eval(x, S.b.iface.params) for x in g.get('range', ()))
    for it in S.mon(s).items.values():
        texts += [str(v) for k, v in it.args.raw.items() if k in ('trigger', 'cond')]

    def walk(n):
        if n.op == 'num' and isinstance(n.val, int):
            out.add(n.val)
        for a in n.args:
            if hasattr(a, 'op'):
                walk(a)
    for t in texts:
        walk(parse(t))
    return sorted(sorted(out, key=abs)[:limit])


def _reading_texts(S, s: str) -> list:
    fs = S.b.fsets[s]
    texts = [str(t) for t in (fs.get('defs') or {}).values()] + [str(g['next']) for g in fs.get('ghosts') or []]
    for it in S.mon(s).items.values():
        texts += [str(v) for k, v in it.args.raw.items() if k in ('trigger', 'cond')]
    return texts


def _distances(S, s: str, src: str, limit: int = 6) -> list[int]:
    """The numbers the code and the reading add to another number, subtract
    from one, or compare a sum or a difference with (now - t < 60, d + 10):
    the distances an invariant is likely to keep between two numbers of the
    state.  A name bound to a number (WINDOW = 60) counts as the number.
    Where a comparison keeps the distance itself (now - t <= 60, t >= now -
    60), what it leaves out is one further: the next number as well.
    The code's first, at most `limit`."""
    from .lang import parse
    with open(src) as f:
        tree = ast.parse(f.read())
    names: dict = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.Assign, ast.AnnAssign)) and isinstance(n.value, ast.Constant) and type(n.value.value) is int:
            for t in n.targets if isinstance(n, ast.Assign) else [n.target]:
                if isinstance(t, (ast.Name, ast.Attribute)):
                    names.setdefault(t.id if isinstance(t, ast.Name) else t.attr, set()).add(n.value.value)

    def val(e):
        if isinstance(e, ast.Constant) and type(e.value) is int:
            return e.value
        got = names.get(e.id if isinstance(e, ast.Name) else e.attr if isinstance(e, ast.Attribute) else None, ())
        return next(iter(got)) if len(got) == 1 else None

    def arith(e) -> bool:
        return isinstance(e, ast.BinOp) and isinstance(e.op, (ast.Add, ast.Sub))
    code, spec, beyond = [], [], set()

    def closed(op: str, left, right, num, plus, minus) -> None:
        """left op right as D op' c, a difference against a number: with
        <= or > the comparison keeps c, and c + 1 is the first beyond it."""
        for e, flip in ((right, False), (left, True)):
            c = num(e)
            if c is None and plus(e):
                c = next((v for v in map(num, plus(e)) if v is not None), None)
            elif c is None and minus(e) and num(minus(e)[1]) is not None:
                c, flip = num(minus(e)[1]), not flip
            elif c is not None and not (plus(left if flip else right) or minus(left if flip else right)
                                        or plus(right if flip else left) or minus(right if flip else left)):
                c = None
            if c is not None and c > 0 and op in ('<', '<=', '>', '>=') and (op in ('<=', '>')) != flip:
                beyond.add(c + 1)

    ops = {ast.Lt: '<', ast.LtE: '<=', ast.Gt: '>', ast.GtE: '>='}
    for n in ast.walk(tree):
        sides = [n.left, n.right] if arith(n) else [n.left] + n.comparators if isinstance(n, ast.Compare) else []
        if arith(n) or any(arith(e) for e in sides):
            code += [val(e) for e in sides]
        if isinstance(n, ast.Compare):
            for op, a, b in zip(n.ops, sides, sides[1:]):
                closed(ops.get(type(op), ''), a, b, val,
                       lambda e: [e.left, e.right] if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Add) else [],
                       lambda e: [e.left, e.right] if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Sub) else [])
    defs = {k: parse(str(t)) for k, t in (S.b.fsets[s].get('defs') or {}).items()}

    def body(n):                                # a name of the reading stands for its definition
        seen = set()
        while n.op == 'ref' and n.val in defs and n.val not in seen:
            seen.add(n.val)
            n = defs[n.val]
        return n

    def walk(n):
        sums = n.op == 'bin' and n.val in ('+', '-')
        if sums or (n.op == 'bin' and any(a.op == 'bin' and a.val in ('+', '-') for a in n.args)):
            spec.extend(a.val for a in n.args if a.op == 'num' and isinstance(a.val, int))
        if n.op == 'bin' and n.val in ('<', '<=', '>', '>=') and len(n.args) == 2:
            closed(n.val, body(n.args[0]), body(n.args[1]),
                   lambda e: e.val if e.op == 'num' and isinstance(e.val, int) else None,
                   lambda e: list(e.args) if e.op == 'bin' and e.val == '+' else [],
                   lambda e: list(e.args) if e.op == 'bin' and e.val == '-' else [])
        for a in n.args:
            if hasattr(a, 'op'):
                walk(a)
    for t in _reading_texts(S, s):
        walk(parse(t))
    base = list(dict.fromkeys(v for v in sorted(set(code) - {None}) + sorted(spec) if v > 0))
    both = [w for v in base for w in ([v, v + 1] if v + 1 in beyond else [v])]
    return sorted(list(dict.fromkeys(both))[:limit])


def _candidates(z3, ints: dict, bools: dict, small: dict, consts: list, limit: int = 20000) -> list:
    """Candidate conjuncts of an invariant over the state, as (text, term):
    each number against the constants and against each other number, each
    boolean and its negation, sums of two numbers, and the same facts under
    a condition (a boolean, or a ghost with few values at one of them).
    Houdini keeps the ones that hold, so a wrong candidate costs only time."""
    iv, bv = sorted(ints.items()), sorted(bools.items())
    atoms = []
    for n, u in iv:
        for c in consts:
            atoms += [(f'{n} >= {c}', u >= c), (f'{n} <= {c}', u <= c)]
    for (n, u), (m, v) in itertools.combinations(iv, 2):
        atoms += [(f'{n} == {m}', u == v), (f'{n} <= {m}', u <= v), (f'{n} >= {m}', u >= v)]
    lits = []
    for n, q in bv:
        lits += [(n, q), (f'!{n}', z3.Not(q))]
    out = atoms + lits
    for (n, q), (m, r) in itertools.combinations(bv, 2):
        out += [(f'{n} == {m}', q == r), (f'{n} != {m}', q != r)]
    if len(iv) <= 6:
        for n, u in iv:
            rest = [x for x in iv if x[0] != n]
            out += [(f'{n} == {m} + {l}', u == v + x) for (m, v), (l, x) in itertools.combinations(rest, 2)]
    ante = list(lits)
    for n, (u, lo, hi) in sorted(small.items()):
        ante += [(f'{n} == {c}', u == c) for c in range(lo, hi + 1)]
    for an, a in ante:
        out += [(f'{an} -> {cn}', z3.Implies(a, c)) for cn, c in atoms + lits if cn != an]
    return out[:limit]


def _houdini(z3, sol, alive: list, goal: dict, assume: Optional[dict] = None) -> Optional[list]:
    """The candidates of `alive` that survive: while some goal[i] can be
    false (under the assumption literals of the ones still alive), drop the
    ones the model makes false.  None: the solver gave up."""
    alive = list(alive)
    while alive:
        sol.push()
        sol.add(z3.Or(*[z3.Not(goal[i]) for i in alive]))
        r = sol.check(*([assume[i] for i in alive] if assume else []))
        if r == z3.unsat:
            sol.pop()
            return alive
        if r != z3.sat:
            sol.pop()
            return None
        md = sol.model()
        keep = [i for i in alive if z3.is_true(md.eval(goal[i], model_completion=True))]
        sol.pop()
        if len(keep) == len(alive):            # no progress (a model that leaves a goal undecided)
            return None
        alive = keep
    return alive


def induct_object(S, s: str, fn: SW.Fn, src: str, tr: Translator, enc0, fields0: list, code0: list,
                  reqs: list, timeout: int = 120000) -> dict:
    """Requirements of reading s that hold at every call of every sequence
    of any length, by induction on the calls.

    The state is what one call leaves for the next: the object's fields, the
    reading's ghosts and the registers of its once, hist and since.  A window
    of W consecutive calls (W - 1: the furthest an item looks back) starts
    from any state; the code's own step function and the reading's encoding
    relate the calls in it.  An invariant is found by Houdini from candidate
    facts about the state: the ones that hold in the first W states after
    the constructor (in the unrolled encoding enc0) and that, held at the W
    states before the window's last call, hold after it.  A requirement is
    proved for every call from the W-th on if its items hold at the window's
    last call under the invariant; the caller proves the calls before it.

    The window's encoding is not validated against the monitors on its own:
    it is proved equal to the unrolled encoding, which is, at every call of
    enc0 from the W-th on (items, ghosts, registers and fields).

    {'status': 'ok', 'window': W, 'candidates': n, 'invariant': n,
     'proved': {req: [the conjuncts its proof used]}} or {'status': 'none', 'why'}."""
    import z3
    K = enc0.k
    try:
        W = SW.window_len(S, s, fn)
        if W > K:                              # (no call at which the window could be compared with enc0)
            return {'status': 'none', 'why': f'a window of {W} calls, an encoding of {K}'}
        w = SW._IntSpec(S, [s], fn, W, window=True)
    except SW.Unsupported as e:
        return {'status': 'none', 'why': str(e)}
    init = fields0[0]
    if any(v.ty not in ('int', 'bool') for v in init.values()):
        return {'status': 'none', 'why': 'a field that is not a number or a boolean'}
    keys = [k for k in sorted(init) if init[k].ty in ('int', 'bool')]
    fxs, fsym = _field_vars(z3, init)
    F, trans = [fsym], []
    try:
        for p in range(1, W + 1):
            args = [w.x[(sg, p)] if kind != 'bool' else w.x[(sg, p)] != 0 for _, sg, kind in fn.args]
            new, code, rets = tr.step(fn, F[-1], args)
            if any(new[k].ty != init[k].ty for k in init):
                return {'status': 'none', 'why': 'a field whose type changes from call to call'}
            F.append(new)
            trans += [w.x[(fn.outcome, p)] == code] + [w.x[(r, p)] == rets[r] for r in fn.rets]
        n = -1
        while n != len(w.reg):                 # every register, at every call of the window
            n = len(w.reg)
            for r in list(w.reg.values()):
                for p in range(W + 1):
                    w.reg_value(r, p)
    except (Untranslatable, SW.Unsupported) as e:
        return {'status': 'none', 'why': str(e)}
    regs = list(w.reg.values())

    def rname(r):
        from .lang import unparse
        return unparse(r['node']) + (str(r['env']) if r['env'] else '')

    def state(enc, fields, p):
        """(numbers, booleans) of the state after call p, by name."""
        ints = {f'self.{k}': fields[p][k].t for k in keys if init[k].ty == 'int'}
        ints.update({name: enc.g[(s, name, p + 1)] for name in enc.gdecl[s]})
        bools = {f'self.{k}': fields[p][k].t for k in keys if init[k].ty == 'bool'}
        bools.update({rname(r): enc.reg_value(r, p) for r in regs})
        return ints, bools

    ints, bools = state(w, F, 0)               # the canonical state: the variables themselves
    canon = {**ints, **bools}

    def subs(enc, fields, p):
        a, b = state(enc, fields, p)
        return [(canon[n], t) for n, t in {**a, **b}.items()]

    # the window is the unrolled encoding, one call at a time
    sigs = fn.signals + fn.base_signals
    frame = S.b.frame_ids
    its = S.mon(s).items
    sol = z3.Solver()
    sol.set('timeout', timeout)
    sol.add(*enc0.dom)
    for n in range(W, K + 1):
        off = n - W
        sb = [(w.x[(g, p)], enc0.x[(g, off + p)]) for p in range(1, W + 1) for g in sigs] + subs(enc0, fields0, off)
        for r in regs:                         # the free values of the window's registers: the real ones
            sb += [(v, enc0.reg_value(r, off + i)) for i, v in r['at'].items() if 0 < i <= r['depth']]
        pairs = [(h, enc0.raw_holds[(s, iid, n)]) for (_, iid, _), h in w.raw_holds.items()
                 if its[iid].pattern != 'after_reset']
        pairs += [(h, enc0.aholds[(s, iid, n)]) for (_, iid, _), h in w.aholds.items()
                  if its[iid].pattern != 'after_reset']
        a, b = state(w, F, W), state(enc0, fields0, n)
        pairs += [(t, b[0][x]) for x, t in a[0].items()] + [(t, b[1][x]) for x, t in a[1].items()]
        sol.push()
        sol.add(z3.Or(*[z3.substitute(x, *sb) != y for x, y in pairs]))
        r = sol.check()
        sol.pop()
        if r != z3.unsat:
            return {'status': 'none', 'why': f'the one-step encoding is not the unrolled one at call {n}'}

    small = {name: (canon[name], d['lo'], d['hi']) for name, d in w.gdecl[s].items() if d['hi'] - d['lo'] <= 7}
    cands = _candidates(z3, ints, bools, small, _consts(S, s, src))
    alive = list(range(len(cands)))
    # base: the states after 0 .. W - 1 calls on a new object
    for p in range(W):
        sol = z3.Solver()
        sol.set('timeout', timeout)
        sol.add(*enc0.dom)
        for cs in code0[:p]:
            sol.add(*cs)
        sb = subs(enc0, fields0, p)
        alive = _houdini(z3, sol, alive, {i: z3.substitute(cands[i][1], *sb) for i in alive})
        if alive is None:
            return {'status': 'none', 'why': 'the base of the induction was not decided in time'}
    # step: held at the W states before the window's last call, held after it
    sol = z3.Solver()
    sol.set('timeout', timeout)
    sol.add(*w.dom)
    sol.add(*trans)
    at = [subs(w, F, p) for p in range(W + 1)]
    lit = {i: z3.Bool(f'inv_{i}') for i in alive}
    for i in alive:
        sol.add(z3.Implies(lit[i], z3.And(*[z3.substitute(cands[i][1], *at[p]) for p in range(W)])))
    alive = _houdini(z3, sol, alive, {i: z3.substitute(cands[i][1], *at[W]) for i in alive}, lit)
    if alive is None:
        return {'status': 'none', 'why': 'the step of the induction was not decided in time'}
    by_req: dict[str, list] = {}
    for (_, iid, _), h in w.raw_holds.items():
        if iid not in frame:
            by_req.setdefault(its[iid].req, []).append(h)
    back = {str(lit[i]): cands[i][0] for i in alive}
    proved = {}
    for req in reqs:
        sol.push()
        sol.add(z3.Or(*[z3.Not(h) for h in by_req.get(req, [])]))
        if sol.check(*[lit[i] for i in alive]) == z3.unsat:
            # the conjuncts this proof needs: its core, less what it can do without
            core = sorted(sol.unsat_core(), key=lambda x: ('==' in back[str(x)], -len(back[str(x)])))
            for x in list(core):
                rest = [y for y in core if y is not x]
                if sol.check(*rest) == z3.unsat:
                    core = rest
            proved[req] = sorted(back[str(x)] for x in core)
        sol.pop()
    return {'status': 'ok', 'window': W, 'candidates': len(cands), 'invariant': len(alive), 'proved': proved}


def prove_object(S, s: str, fn: SW.Fn, src: str, calls: list, res: dict, only: Optional[set] = None,
                 k: Optional[int] = None, timeout: int = 300000, induct: bool = True) -> dict:
    """Every requirement of reading s on an object with several methods, with
    every argument the interface carries.

    PROVED: at every call of every sequence of calls of any length on a new
    object, by induction (see induct_object) for the calls from the W-th on
    and by unrolling for the W - 1 before it.  Otherwise the requirement is
    checked over every sequence of up to k calls (default: the scope's
    longest): PROVED-BOUNDED, or FAILS at a sequence replayed on the code and
    confirmed on the monitors.  An object that holds dictionaries, lists or
    helper objects, a reading with rigid variables, and an object with one
    method are proved the same way by fcp.keyedproof."""
    import z3
    from . import keyedproof
    CONF.tag(None)
    if not fn.cls or fn.has_seq or fn.structured:
        return {'status': 'unsupported', 'why': 'only objects whose methods take numbers and booleans'}

    def keyed(why: str = '') -> dict:
        """The same question with dictionaries, lists and helper objects in
        the fields, and with the reading's rigid variables as constants."""
        out = keyedproof.prove_keyed(S, s, fn, src, calls, res, only, k, timeout, induct)
        if why and out['status'] in ('unsupported', 'untranslatable') and isinstance(out.get('why'), str):
            out['why'] = f'{why}; with dictionaries and lists in the fields: {out["why"]}'
        return out
    if not fn.methods:
        return keyed()
    try:
        tr = Translator(src, fn.cls)
        bad = check_object_translation(fn, tr, calls, res)
    except Untranslatable as e:
        return keyed(str(e))
    if bad is not None:
        return {'status': 'translation differs', 'why': bad}
    K = k or max(len(x) for x in _sequences(calls))
    try:
        enc = SW._IntSpec(S, [s], fn, K)
    except SW.Unsupported as e:
        if S.b.fsets[s].get('rigids'):
            return keyed(str(e))
        return {'status': 'unsupported', 'why': str(e)}
    bad = check_object_encoding(S, s, fn, enc, calls, res)
    if bad is not None:
        return {'status': 'encoding differs', 'why': bad}
    fields0, code0 = [tr.init_fields(fn)], []
    for i in range(1, K + 1):
        args = [enc.x[(sg, i)] if kind != 'bool' else enc.x[(sg, i)] != 0 for _, sg, kind in fn.args]
        fields, code, rets = tr.step(fn, fields0[-1], args)
        fields0.append(fields)
        code0.append([enc.x[(fn.outcome, i)] == code] + [enc.x[(r, i)] == rets[r] for r in fn.rets])
    frame = S.b.frame_ids
    by_req: dict[str, list] = {}
    for (st, iid, i), h in enc.raw_holds.items():
        if iid not in frame:
            by_req.setdefault(S.mon(s).items[iid].req, []).append((iid, i, h))
    reqs = [r for r in sorted(by_req) if only is None or r in only]
    ind = induct_object(S, s, fn, src, tr, enc, fields0, code0, reqs, min(timeout, 120000)) if induct \
        else {'status': 'none', 'why': 'not asked for'}
    items = {}
    for req in reqs:
        CONF.tag(req)
        hs = by_req[req]
        upto = K
        if req in ind.get('proved', {}):       # the induction starts at call W: the calls before it
            upto = max(1, ind['window'] - 1)
        sol = z3.Solver()
        sol.set('timeout', timeout)
        sol.add(*enc.dom)
        for cs in code0[:upto]:
            sol.add(*cs)
        sol.add(z3.Or(*[z3.Not(h) for _, i, h in hs if i <= upto]))
        r = sol.check()
        if r != z3.unsat and upto < K:         # (a failure there is a failure of the bounded check too)
            upto = K
            sol = z3.Solver()
            sol.set('timeout', timeout)
            sol.add(*enc.dom)
            for cs in code0:
                sol.add(*cs)
            sol.add(z3.Or(*[z3.Not(h) for _, _, h in hs]))
            r = sol.check()
        if r == z3.unsat and upto < K:
            items[req] = {'status': 'PROVED', 'k': K, 'window': ind['window'], 'invariant': ind['proved'][req]}
        elif r == z3.unsat:
            items[req] = {'status': 'PROVED-BOUNDED', 'k': K}
        elif r == z3.sat:
            md = sol.model()
            first = min(i for iid, i, h in hs if z3.is_false(md.eval(h, model_completion=True)))
            seq = [tuple(md.eval(enc.x[(sg, i)], model_completion=True).as_long() for _, sg, _ in fn.args)
                   for i in range(1, first + 1)]
            run = [None] + seq
            again = SW.run(fn, src, run)
            chk = SW.check(S, s, SW.trace(fn, run, again))
            broken = sorted({iid for iid, i, h in hs if i <= first and z3.is_false(md.eval(h, model_completion=True))})
            items[req] = {'status': 'FAILS', 'calls': [SW.call_text(fn, c) for c in seq], 'items': broken,
                          'confirmed': any(chk[iid]['first'] is not None for iid in broken), 'k': K}
        else:
            items[req] = {'status': 'UNKNOWN', 'why': sol.reason_unknown(), 'k': K}
    out = {'status': 'ok', 'exact': bool(items) and all(v['status'] == 'PROVED' for v in items.values()),
           'k': K, 'requirements': items}
    out['induction'] = {k: v for k, v in ind.items() if k != 'proved'}
    return out
