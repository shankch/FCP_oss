"""Proofs for objects whose fields hold dictionaries, lists, deques and
helper objects (the translation: fcp.keyed).

Two models of the code are used.  The exact one unrolls the calls from the
constructor: a dictionary is the list of the writes made so far, so the
terms are the code's own answers for every sequence of up to K calls, and
they are checked against what the code did on every sequence of the scope.
A requirement that holds on it holds for every sequence of up to K calls
(PROVED-BOUNDED); one that does not gives a sequence, replayed on the code
and confirmed on the monitors (FAILS).

The abstract one is a window of calls from any state: a dictionary is any
function of the key, a list any list of at most L numbers.  A conjunction
of facts about that state which holds on a new object and after every call
from a state where it holds is an invariant, found by Houdini among
candidates (grammar); a requirement it implies at the window's last call
holds at every call of every sequence of any length (PROVED).  The window
is checked against the exact model on the calls both cover.

A reading that follows one key (a rigid variable: "an arbitrary customer")
is encoded with the rigid as a free constant (software._IntSpec,
free_rigids): a proof for the free constant is a proof for each of its
values.
"""
from __future__ import annotations

import itertools
from typing import Optional

from . import confirm as CONF, keyed as K, seqs as Q, software as SW
from .symval import Untranslatable, V


LOG = None                                # a function of one string, told what the induction is doing


def note(msg: str):
    if LOG is not None:
        LOG(msg)


def call_args(fn: SW.Fn, enc, i: int) -> list:
    return [enc.x[(sg, i)] if kind != 'bool' else enc.x[(sg, i)] != 0 for _, sg, kind in fn.args]


def unroll(tr, fn: SW.Fn, enc, n: int) -> tuple:
    """The first n calls on a new object: (fields after 0 .. n calls,
    [the constraints tying call i's outcome and results to the code],
    [call i's outcome and results as terms])."""
    z3 = tr.z3
    tr.dom = [c for i in range(1, n + 1) for c in Q.arg_dom(z3, fn, [enc.x[(sg, i)] for _, sg, _ in fn.args])]
    fields, code, terms = [tr.init_fields(fn)], [], []
    for i in range(1, n + 1):
        new, c, rets = tr.step(fn, fields[-1], call_args(fn, enc, i))
        fields.append(new)
        code.append([enc.x[(fn.outcome, i)] == c] + [enc.x[(r, i)] == rets[r] for r in fn.rets])
        terms.append([c] + [rets[r] for r in fn.rets])
    return fields, code, terms


def check_translation(P, fn: SW.Fn, enc, terms: list, calls: list, res: dict) -> Optional[dict]:
    """The unrolled model against the code on every sequence of the scope:
    the outcome and results of every call.  The first difference, or None."""
    z3 = enc.z3
    n = len(terms)
    xs = [enc.x[(sg, i)] for i in range(1, n + 1) for _, sg, _ in fn.args]
    f = P.compile_terms(z3, [z3.simplify(t) for ts in terms for t in ts], xs)
    w, na = 1 + len(fn.rets), len(fn.args)
    for seq in P._sequences(calls):
        if len(seq) > n:
            return {'why': f'a sequence of {len(seq)} calls is longer than the model ({n})'}
        flat = [int(v) for i in seq for v in calls[i]] + [0] * (na * (n - len(seq)))
        out = f(*flat)
        for j, i in enumerate(seq):
            got, vals = int(out[w * j]), [int(v) for v in out[w * j + 1: w * j + w]]
            want, wv = res['code'][i], [int(res['ret'][r][i]) for r in fn.rets]
            if want == fn.other_exc and got == fn.other_exc:
                continue
            if got != want or (want == 0 and vals != wv):
                return {'calls': [list(calls[x]) for x in seq[:j + 1]], 'index': i, 'code': want, 'ret': wv,
                        'translated_code': got, 'translated_ret': vals}
    return None


def rigid_values(enc, s: str, row: list) -> list:
    """Valuations of the reading's rigid variables to try on one sequence:
    the numbers in its calls and their neighbours, and the ends of the range."""
    out = []
    for name, (lo, hi) in sorted(enc.rigids.get(s, {}).items()):
        vals = {lo, hi} | {v + d for v in row for d in (-1, 0, 1) if lo <= v + d <= hi}
        out.append(sorted(vals))
    return list(itertools.islice(itertools.product(*out), 256))


def check_encoding(P, S, s: str, fn: SW.Fn, enc, calls: list, res: dict) -> Optional[dict]:
    """The reading's encoding against the compiled monitors on every call of
    every sequence of the scope.  The monitors are replayed over every value
    of a rigid variable and report a call at which some value fails; the
    encoding is evaluated at the values rigid_values picks.  The first
    difference, or None."""
    z3 = enc.z3
    n = enc.k
    cols = SW.trace(fn, calls, res)
    chk = SW.check(S, s, cols, keep=len(calls) + 1)
    frame = S.b.frame_ids
    sigs = fn.signals
    rig = [enc.rig[r] for r in sorted(enc.rigids.get(s, {}))]
    xs = [enc.x[(g, i)] for i in range(1, n + 1) for g in sigs] + rig
    verdict = {**enc.raw_holds, **enc.aholds}
    items = list(dict.fromkeys(iid for (st, iid, i) in verdict if st == s and iid not in frame))
    f = P.compile_terms(z3, [z3.simplify(verdict[(s, iid, i)]) for iid in items for i in range(1, n + 1)], xs)
    fails = {iid: set(chk[iid]['fails']) for iid in items}
    for seq in P._sequences(calls):
        if len(seq) > n:
            return {'why': f'a sequence of {len(seq)} calls is longer than the encoding ({n})'}
        cyc = [i + 1 for i in seq]                # cycle t is call t - 1 (cycle 0 is the first reset)
        row = [cols[g][c] for c in cyc for g in sigs]
        base = row + [0] * (len(sigs) * (n - len(cyc)))
        got = [f(*(base + list(rv))) for rv in rigid_values(enc, s, row)]
        for j, c in enumerate(cyc):
            for t, iid in enumerate(items):
                ok = all(g[t * n + j] for g in got)
                if (not ok) != (c in fails[iid]):
                    return {'item': iid, 'call': j + 1, 'calls': [list(calls[i]) for i in seq[:j + 1]],
                            'encoding': 'fails' if not ok else 'holds',
                            'monitor': 'fails' if c in fails[iid] else 'holds'}
    return None


def bounded(z3, enc, code0, hs, n, timeout):
    """The requirement call by call: at call i with the code of calls 1..i
    and the requirement at the calls before it, which is proved by then.
    (result, the call it was reached at, the solver)."""
    import time
    sol = z3.Solver()
    sol.add(*enc.dom)
    end = time.time() + timeout / 1000
    for i in range(1, n + 1):
        sol.add(*code0[i - 1])
        here = [h for _, j, h in hs if j == i]
        if not here:
            continue
        left = end - time.time()
        if left <= 0:
            return z3.unknown, i, sol
        sol.set('timeout', max(1, int(left * 1000)))
        sol.push()
        sol.add(z3.Or(*[z3.Not(h) for h in here]))
        r = sol.check()
        if r != z3.unsat:
            return r, i, sol
        sol.pop()
        sol.add(*here)
    return z3.unsat, n, sol


def whole(z3, enc, code0, hs, upto, timeout):
    """The requirement at the calls 1 .. upto, as one question: (result, the solver)."""
    sol = z3.Solver()
    sol.set('timeout', timeout)
    sol.add(*enc.dom)
    for cs in code0[:upto]:
        sol.add(*cs)
    sol.add(z3.Or(*[z3.Not(h) for _, i, h in hs if i <= upto]))
    return sol.check(), sol


def prove_keyed(S, s: str, fn: SW.Fn, src: str, calls: list, res: dict, only: Optional[set] = None,
                k: Optional[int] = None, timeout: int = 120000, induct: bool = True) -> dict:
    """Each requirement of reading s on an object with dictionaries, lists
    or helper objects in its fields, or of a reading with rigid variables.

    First, every sequence of a few calls (8, or k if less) on every value
    of the arguments: FAILS at a sequence z3 chose, the shortest of them,
    replayed on the code and confirmed on the monitors.  Then the
    requirements that did not fail, by induction (induct_keyed): PROVED, at
    every call of every sequence of calls of any length on a new object
    (the induction for the calls from the W-th on, the few calls for the
    W - 1 before it).  A requirement the induction does not prove is checked
    over every sequence of up to k calls (default: the scope's longest):
    PROVED-BOUNDED (each length as one question; if one is not answered in
    time, call by call, for the calls answered) or FAILS.  The same dict as
    prove.prove_object returns."""
    import z3
    from . import prove as P
    CONF.tag(None)
    n = k or max(len(x) for x in P._sequences(calls))
    try:
        enc = SW._IntSpec(S, [s], fn, n, free_rigids=True)
    except SW.Unsupported as e:
        return {'status': 'unsupported', 'why': str(e)}
    try:
        tr = P.Translator(src, fn.cls, keyed=True)
        fields0, code0, terms = unroll(tr, fn, enc, n)
        bad = check_translation(P, fn, enc, terms, calls, res)
    except Untranslatable as e:
        return {'status': 'untranslatable', 'why': str(e)}
    if bad is not None:
        return {'status': 'translation differs', 'why': bad}
    bad = check_encoding(P, S, s, fn, enc, calls, res)
    if bad is not None:
        return {'status': 'encoding differs', 'why': bad}
    frame = S.b.frame_ids
    by_req: dict[str, list] = {}
    for (st, iid, i), h in enc.raw_holds.items():
        if iid not in frame:
            by_req.setdefault(S.mon(s).items[iid].req, []).append((iid, i, h))
    reqs = [r for r in sorted(by_req) if only is None or r in only]
    note(f'the translation and the encoding agree with the code and the monitors on {len(calls)} calls')
    top, found = min(n, 8), {}
    for req in reqs:                           # failures first: over a few calls, the shortest sequence
        CONF.tag(req)
        hs = by_req[req]
        r, sol = whole(z3, enc, code0, hs, top, timeout)
        covered = top if r == z3.unsat else 0
        for upto in ([d for d in (1, 2, 3, 4, 5, 6) if d < top] if r != z3.unsat else []):
            r1, sol1 = whole(z3, enc, code0, hs, upto, timeout)
            if r1 != z3.unsat:
                r, sol = r1, sol1
                break
            covered = upto
        note(f'{req}: {r} over {top if r == z3.unsat else covered + 1} calls')
        found[req] = (r, sol, covered)
    CONF.tag(None)                             # the induction is shared by the requirements
    left = [req for req in reqs if found[req][0] == z3.unsat]
    if not induct:
        ind = {'status': 'none', 'why': 'not asked for'}
    elif not left:
        ind = {'status': 'none', 'why': 'every requirement fails or is undecided over a few calls'}
    else:
        ind = induct_keyed(S, s, fn, src, tr, enc, fields0, code0, left, calls, res, min(timeout, 120000))
    items = {}
    for req in reqs:
        CONF.tag(req)
        hs = by_req[req]
        r, sol, covered = found[req]
        depth = n
        # the induction starts at call W: the calls before it are among the few
        early = r == z3.unsat and req in ind.get('proved', {}) and covered >= min(n, ind['window'] - 1)
        if r == z3.unsat and not early:
            for upto in sorted({min(n, 12), n} - set(range(covered + 1))):
                r, sol = whole(z3, enc, code0, hs, upto, timeout)
                note(f'{req}: {r} over {upto} calls')
                if r != z3.unsat:
                    break
                covered = upto
        if r == z3.unknown and covered:        # the lengths answered stand
            depth = covered + 1
        elif r == z3.unknown:
            r, depth, sol = bounded(z3, enc, code0, hs, n, timeout)
        if r == z3.unsat and early:
            items[req] = {'status': 'PROVED', 'k': n, 'window': ind['window'], 'invariant': ind['proved'][req]}
        elif r == z3.unsat:
            items[req] = {'status': 'PROVED-BOUNDED', 'k': n}
        elif r == z3.unknown and depth > 1:
            items[req] = {'status': 'PROVED-BOUNDED', 'k': depth - 1, 'why': f'no answer beyond {depth - 1} calls'}
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
                          'confirmed': any(chk[iid]['first'] is not None for iid in broken), 'k': n,
                          'rigids': {r: md.eval(v, model_completion=True).as_long() for r, v in enc.rig.items()}}
        else:
            items[req] = {'status': 'UNKNOWN', 'why': sol.reason_unknown(), 'k': n}
    out = {'status': 'ok', 'exact': bool(items) and all(v['status'] == 'PROVED' for v in items.values()),
           'k': n, 'requirements': items, 'keyed': True}
    out['induction'] = {k: v for k, v in ind.items() if k != 'proved'}
    return out


# -- the shape of the state ------------------------------------------------------------------
#
# A shape says what a field holds at every call: ('int',), ('bool',), ('lock',),
# ('none',), ('opt', shape), ('list', is a deque), ('rec', class, names, shapes),
# ('map', kind, shape of a value or None if nothing was ever stored).

def shape(v: V) -> tuple:
    if v.ty in ('int', 'bool', 'lock', 'none'):
        return (v.ty,)
    if v.ty == 'opt':
        return ('opt', shape(v.items[0]))
    if Q.is_list(v):
        xs = [x[1] if isinstance(x, tuple) else x for x in v.items]
        if any(x.ty != 'int' for x in xs):
            raise Untranslatable('a list of something other than numbers in the state')
        return ('list', K.is_deque(v))
    if v.ty == 'rec':
        return ('rec', v.name, v.keys, tuple(shape(x) for x in v.items))
    if v.ty == 'map':
        sh = None
        for _, x, _, _ in v.items:
            sh = shape(x) if sh is None else join(sh, shape(x))
        return ('map', v.name, sh)
    raise Untranslatable(f'a {v.ty} in the state')


def join(a: tuple, b: tuple) -> tuple:
    """The shape of a value that has shape a at one call and b at another."""
    if a == b:
        return a
    if a[0] == 'none':
        return b if b[0] == 'opt' else ('opt', b)
    if b[0] == 'none':
        return join(b, a)
    if a[0] == 'opt' or b[0] == 'opt':
        return ('opt', join(a[1] if a[0] == 'opt' else a, b[1] if b[0] == 'opt' else b))
    if a[0] == b[0] == 'rec' and a[1:3] == b[1:3]:
        return a[:3] + (tuple(join(x, y) for x, y in zip(a[3], b[3])),)
    if a[0] == b[0] == 'map' and a[1] == b[1]:
        return ('map', a[1], a[2] if b[2] is None else b[2] if a[2] is None else join(a[2], b[2]))
    raise Untranslatable(f'a field that is a {a[0]} at one call and a {b[0]} at another')


def has_map(sh: Optional[tuple]) -> bool:
    return sh is not None and (sh[0] == 'map' or (sh[0] == 'opt' and has_map(sh[1]))
                               or (sh[0] == 'rec' and any(has_map(x) for x in sh[3])))


def shapes(fields: list) -> dict:
    """The shape of each field, over the states of the unrolled model."""
    out = {}
    for fs in fields:
        for name, v in fs.items():
            out[name] = join(out[name], shape(v)) if name in out else shape(v)
    for name, sh in out.items():
        if (sh[0] == 'map' and has_map(sh[2])) or (sh[0] != 'map' and has_map(sh)):
            raise Untranslatable(f'{name}: a dictionary inside another value')
    return out


KEY = '*'                                 # the label of any key, in the names of a state's numbers


class Abstract:
    """Any state of a shape: a number or boolean is a free constant, a
    dictionary is a function of the key (z3 uninterpreted functions: whether
    the key is there, and each number of the value it has), a list is its
    length and its first L numbers.  facts collects what the shape says of
    them (the length of a list is 0 .. L), key by key as keys are looked up.
    The constants and functions are named as flat() names the numbers of a
    state (st.<name>, the functions with KEY for the key)."""

    def __init__(self, tr, L: int, facts: list):
        self.tr, self.z3, self.L, self.facts, self.funs = tr, tr.z3, L, facts, {}

    def fun(self, name: str, args: tuple, boolean: bool = False):
        z3 = self.z3
        sort = z3.BoolSort() if boolean else z3.IntSort()
        if not args:
            return z3.Const(f'st.{name}', sort)
        if name not in self.funs:
            self.funs[name] = z3.Function(f'st.{name}', *([z3.IntSort()] * len(args) + [sort]))
        return self.funs[name](*args)

    def build(self, sh: tuple, name: str, args: tuple = ()) -> V:
        z3 = self.z3
        if sh[0] == 'int':
            return V(self.fun(name, args), 'int')
        if sh[0] == 'bool':
            return V(self.fun(name, args, True), 'bool')
        if sh[0] == 'lock':
            return V(None, 'lock')
        if sh[0] == 'none':
            return K.none()
        if sh[0] == 'opt':
            return K.opt(self.tr, self.fun(f'{name} is None', args, True), self.build(sh[1], name, args))
        if sh[0] == 'list':
            ln = self.fun(f'len({name})', args)
            self.facts.append(z3.And(ln >= 0, ln <= self.L))
            slots = tuple((ln > j, V(self.fun(f'{name}[{j}]', args), 'int')) for j in range(self.L))
            return V(ln, 'seq', slots, 'list', keys=K.DEQUE if sh[1] else (), dense=True)
        if sh[0] == 'rec':
            return V(None, 'rec', tuple(self.build(x, f'{name}.{key}', args) for key, x in zip(sh[2], sh[3])),
                     sh[1], keys=sh[2])
        if sh[2] is None:                      # (a dictionary nothing is ever stored in)
            return K.new_map(sh[1])
        return K.new_map(sh[1], K.Rest(lambda k: (self.fun(f'{KEY} in {name}', (k,), True),
                                                  self.build(sh[2], f'{name}[{KEY}]', (k,)))))


def flat(tr, sh: tuple, v: Optional[V], name: str, L: int, out: list, pres=None, label=None):
    """A value of a shape as named numbers and booleans, appended to out as
    (name, 'int' | 'bool', role, key label, term).  Where the value is not
    there (pres is false: a key the dictionary does not have, the inside of
    a None) they are 0 and false, so that two states that are the same to
    the code have the same numbers."""
    z3 = tr.z3

    def put(n, sort, role, t):
        if pres is not None:
            t = z3.And(pres, t) if sort == 'bool' else z3.If(pres, t, 0)
        out.append((n, sort, role, label, t))

    def no(what):
        raise Untranslatable(f'{name}: {what}, not the {sh[0]} it is in the unrolled model')
    if sh[0] in ('int', 'bool'):
        if v is not None and v.ty != sh[0]:
            no(f'a {v.ty}')
        zero = z3.BoolVal(False) if sh[0] == 'bool' else z3.IntVal(0)
        put(name, sh[0], 'flag' if sh[0] == 'bool' else 'num', zero if v is None else v.t)
    elif sh[0] == 'opt':
        n, x = (z3.BoolVal(False), None) if v is None else K.split(tr, v)
        put(f'{name} is None', 'bool', 'flag', n)
        flat(tr, sh[1], x, name, L, out, z3.Not(n) if pres is None else z3.And(pres, z3.Not(n)), label)
    elif sh[0] == 'list':
        if v is None:
            ln, el = z3.IntVal(0), [z3.IntVal(0)] * L
        else:
            if not Q.is_list(v) or K.is_deque(v) != sh[1]:
                no(f'a {v.ty}')
            if any((x[1] if isinstance(x, tuple) else x).ty != 'int' for x in v.items):
                no('a list of something other than numbers')
            ln, el = Q.dense_form(tr, v, L)
        put(f'len({name})', 'int', 'len', ln)
        for j in range(L):
            put(f'{name}[{j}]', 'int', 'el', el[j])
    elif sh[0] == 'rec':
        if v is not None and (v.ty != 'rec' or v.name != sh[1] or v.keys != sh[2]):
            no(f'a {v.name or v.ty}')
        for key, x in zip(sh[2], sh[3]):
            flat(tr, x, None if v is None else K.field(v, key), f'{name}.{key}', L, out, pres, label)
    elif v is not None and v.ty != sh[0]:      # a lock, or None
        no(f'a {v.ty}')


def project(tr, shs: dict, fields: dict, keys: dict, L: int) -> list:
    """A state as named numbers and booleans: each field, and each
    dictionary at each of the keys ({label: term})."""
    out = []
    for name in sorted(shs):
        sh, v = shs[name], fields[name]
        if sh[0] != 'map':
            flat(tr, sh, v, f'self.{name}', L, out)
            continue
        if v.ty != 'map' or v.name != sh[1]:
            raise Untranslatable(f'self.{name}: a {v.ty}, not the dictionary it is in the unrolled model')
        if sh[2] is None:
            if v.items or v.t is not None:
                raise Untranslatable(f'self.{name}: stored into, and empty in the unrolled model')
            continue
        for label, k in keys.items():
            pres, val = K.lookup(tr, v, k)
            out.append((f'{label} in self.{name}', 'bool', 'flag', label, pres))
            flat(tr, sh[2], val, f'self.{name}[{label}]', L, out, pres, label)
    return out


# -- candidate invariants ----------------------------------------------------------------------

def grammar(z3, vs: list, consts: list, L: int, must: Optional[set] = None, offs: Optional[list] = None) -> dict:
    """Candidate conjuncts of an invariant over the numbers and booleans vs
    ((name, sort, role, constant)): each number against the constants and
    against each other number, also at a distance (offs: the ones the code
    and the reading mention, by default the first positive constants:
    x + 60 <= y, x <= y + 60); each boolean and its negation; and the
    same facts under a condition: a boolean, or the length of a list
    (len == c, len <= c, len > c).  A slot of a list is mentioned only
    under a condition that says the list is that long (len > 2 ->
    x[2] <= y): past its length a slot holds nothing the code can read.
    must: only the ones that mention one of these names.

    {'facts': [(text, term, the names in it)],
     'cands': [(a, c)]: fact a implies fact c (a None: fact c alone),
     'neg': {a: the fact that says fact a is false, where there is one},
     'stronger': {c: the facts next above fact c (each implies it)},
     'weaker': {a: the facts next below fact a (it implies each)},
     'near': the facts x <= y + d, tried only where the rest is not enough}.
    Houdini keeps the candidates that hold."""
    lens = [(n, c) for n, sort, role, c in vs if role == 'len']
    nums = [(n, c) for n, sort, role, c in vs if sort == 'int' and role != 'len']
    bools = [(n, c) for n, sort, role, c in vs if sort == 'bool']
    offs = [c for c in consts if c > 0][:6] if offs is None else offs
    slot = {n: (f'len({n[:n.rindex("[")]})', int(n[n.rindex('[') + 1:-1])) for n, sort, role, c in vs if role == 'el'}
    facts, at = [], {}
    neg, stronger, weaker, guard, far = {}, {}, {}, {}, set()

    def sound(a, c) -> bool:
        return all(guard.get(a, ('', 0))[0] == ln and guard[a][1] > j
                   for ln, j in (slot[n] for n in facts[c][2] if n in slot))

    def fact(text, term, names) -> int:
        if text not in at:
            at[text] = len(facts)
            facts.append((text, term, frozenset(names)))
        return at[text]

    def chain(xs):
        """Facts from the weakest to the strongest."""
        for lo, hi in zip(xs, xs[1:]):
            stronger.setdefault(lo, []).append(hi)
        return xs

    def pair(n, u, m, v):
        eq, le, ge = fact(f'{n} == {m}', u == v, {n, m}), fact(f'{n} <= {m}', u <= v, {n, m}), \
            fact(f'{n} >= {m}', u >= v, {n, m})
        stronger.setdefault(le, []).append(eq)
        stronger.setdefault(ge, []).append(eq)
        return eq, le, ge
    atoms, lits, eqs, ante = [], [], [], []
    for n, u in lens:
        atoms += chain([fact(f'{n} <= {c}', u <= c, {n}) for c in range(L, -1, -1)])
    for (n, u), (m, v) in itertools.combinations(lens, 2):
        atoms += pair(n, u, m, v)
    for n, u in nums:
        atoms += chain([fact(f'{n} >= {c}', u >= c, {n}) for c in consts])
        atoms += chain([fact(f'{n} <= {c}', u <= c, {n}) for c in consts[::-1]])
    for (n, u), (m, v) in itertools.combinations(nums, 2):
        eq, le, ge = pair(n, u, m, v)
        atoms += [eq, le, ge]
        for (a, x), (b, y), mid in (((n, u), (m, v), le), ((m, v), (n, u), ge)):
            near = [fact(f'{a} <= {b} + {d}', x <= y + d, {n, m}) for d in offs[::-1]]
            far.update(near)
            atoms += near + chain(near + [mid] + [fact(f'{a} + {d} <= {b}', x + d <= y, {n, m}) for d in offs])[len(near) + 1:]
    for n, q in bools:
        yes, no = fact(n, q, {n}), fact(f'!({n})', z3.Not(q), {n})
        lits += [yes, no]
        neg[yes], neg[no] = no, yes
    for (n, q), (m, r) in itertools.combinations(bools, 2):
        eqs += [fact(f'({n}) == ({m})', q == r, {n, m}), fact(f'({n}) != ({m})', q != r, {n, m})]
    ante += lits
    for n, u in lens:
        le = {c: fact(f'{n} <= {c}', u <= c, {n}) for c in range(L)}
        gt = {c: fact(f'{n} > {c}', u > c, {n}) for c in range(L)}
        for c in range(L + 1):
            eq = fact(f'{n} == {c}', u == c, {n})
            ante.append(eq)
            guard[eq] = (n, c)                 # (the list is at least this long)
            weaker[eq] = [x for x in (le.get(c), gt.get(c - 1)) if x is not None]
        for c in range(L):
            ante += [le[c], gt[c]]
            guard[gt[c]] = (n, c + 1)
            neg[gt[c]] = le[c]
            weaker[le[c]] = [le[c + 1]] if c + 1 in le else []
            weaker[gt[c]] = [gt[c - 1]] if c - 1 in gt else []
    cands = [(None, c) for c in atoms + lits + eqs if sound(None, c)]
    cands += [(a, c) for a in ante for c in atoms + lits if not facts[c][2] <= facts[a][2] and sound(a, c)]
    if must is not None:
        cands = [(a, c) for a, c in cands if (facts[c][2] | (facts[a][2] if a is not None else set())) & must]
    return {'facts': facts, 'cands': cands, 'neg': neg, 'stronger': stronger, 'weaker': weaker, 'near': far}


def text_of(facts: list, ac: tuple) -> str:
    a, c = ac
    return facts[c][0] if a is None else f'{facts[a][0]} -> {facts[c][0]}'


def candidate(z3, facts: list, ac: tuple) -> tuple:
    """A candidate of the grammar as (text, term, the names in it)."""
    a, c = ac
    if a is None:
        return facts[c]
    return text_of(facts, ac), z3.Implies(facts[a][1], facts[c][1]), facts[a][2] | facts[c][2]


def grammars(parts: list) -> dict:
    """Several grammars as one."""
    out = {'facts': [], 'cands': [], 'neg': {}, 'stronger': {}, 'weaker': {}, 'near': set()}
    for g in parts:
        o = len(out['facts'])
        out['facts'] += g['facts']
        out['near'] |= {c + o for c in g['near']}
        out['cands'] += [(None if a is None else a + o, c + o) for a, c in g['cands']]
        out['neg'].update({a + o: c + o for a, c in g['neg'].items()})
        for k in ('stronger', 'weaker'):
            out[k].update({a + o: [c + o for c in cs] for a, cs in g[k].items()})
    return out


def samples(P, m, enc0, fields0: list, calls: list, res: dict, depth: int = 8, most: int = 4000) -> list:
    """States the object is in on the scope's sequences, each as the values
    of the names of m.meta: the states after each of the first `depth`
    calls of a sequence, with the reading's rigid variables and the key of
    the dictionaries (the `*` of the names) at values the sequence uses:
    first the ones that are a key of some dictionary at some call, and one
    that never is.  They are computed by the unrolled model, which is the
    code on the scope (check_translation, check_encoding)."""
    import random
    z3, fn, s = m.z3, m.fn, m.s
    D = min(enc0.k, depth)
    key = z3.Int('a_key')
    sigs = fn.signals
    rnames = sorted(enc0.rigids.get(s, {}))
    rng = [enc0.rigids[s][r] for r in rnames]
    xs = [enc0.x[(g, i)] for i in range(1, D + 1) for g in sigs] + [enc0.rig[r] for r in rnames] + [key]
    nm = len(m.meta)
    f = P.compile_terms(z3, [z3.simplify(x[4]) for p in range(D + 1) for x in m.state(enc0, fields0, p, key)], xs)
    sorts = [sort for _, sort, _, _ in m.meta]
    present = [j for j, (n, _, _, label) in enumerate(m.meta) if label == KEY and n.startswith(f'{KEY} in ')]
    cols = SW.trace(fn, calls, res)
    seqs = P._sequences(calls)
    out = set()
    for seq in seqs[::max(1, len(seqs) // 200)]:
        cyc = [i + 1 for i in seq[:D]]            # cycle t is call t - 1 (cycle 0 is the first reset)
        row = [int(cols[g][c]) for c in cyc for g in sigs]
        base = row + [0] * (len(sigs) * (D - len(cyc)))
        vals = sorted(set(row))

        def run(rv, kv):
            got = f(*(base + list(rv) + [kv]))
            return [got[p * nm:(p + 1) * nm] for p in range(len(cyc) + 1)]
        keys = [v for v in vals if any(st[j] for st in run([lo for lo, _ in rng], v) for j in present)][:3]
        keys.append(max(vals, default=0) + 1)
        picks = [list(dict.fromkeys(v for v in keys + [lo, hi] + vals if lo <= v <= hi))[:4] for lo, hi in rng]
        for rv in itertools.islice(itertools.product(*picks), 8):
            for kv in keys:
                for st in run(rv, kv):
                    out.add(tuple(bool(v) if sort == 'bool' else int(v) for v, sort in zip(st, sorts)))
    states = sorted(out)
    return random.Random(0).sample(states, most) if len(states) > most else states


def sift(g, G: dict, states: list, keep: frozenset = frozenset()) -> tuple:
    """The candidates of grammar G no sampled state refutes, less the ones
    another candidate stands for on the samples: a -> c is set aside while
    a candidate that implies it holds in every sampled state (c alone, a
    stronger fact than c under a, or c under a weaker fact than a), or
    while a holds in none and the fact that says so is a candidate.  (the
    ones kept, {the text of the candidate that stands for them: the ones
    set aside}): the ones set aside are brought back if that candidate
    turns out not to be invariant.  g: the facts' values in a state; keep:
    texts never set aside."""
    facts, neg = G['facts'], G['neg']
    if not states:
        return list(G['cands']), {}
    rows = [g(*st) for st in states]
    full = (1 << len(states)) - 1
    mask = [int(''.join('1' if v else '0' for v in col), 2) for col in zip(*rows)]
    ok = [(a, c) for a, c in G['cands'] if not (full if a is None else mask[a]) & ~mask[c]]
    valid = {text_of(facts, ac) for ac in ok}
    kept, aside = [], {}
    for a, c in ok:
        above = [(a, x) for x in G['stronger'].get(c, ())]
        if a is not None and mask[a] == 0:     # a is never seen: the fact that says so stands for a -> c
            by = text_of(facts, (None, neg[a])) if a in neg else None
            if by in valid:
                aside.setdefault(by, []).append((a, c))
            continue
        if a is not None:
            above += [(x, c) for x in G['weaker'].get(a, ())] + [(None, c)]
        by = next((t for t in (text_of(facts, x) for x in above) if t in valid), None)
        if by is None or text_of(facts, (a, c)) in keep:
            kept.append((a, c))
        else:
            aside.setdefault(by, []).append((a, c))
    return kept, aside


def houdini_step(z3, sol, alive: list, post: dict, lit: dict, batch: int = 40, deadline=None,
                 falsified=None, core: Optional[dict] = None, quick: int = 3000, slow: int = 20000,
                 name=None) -> tuple:
    """Houdini for the step of the induction, a batch of goals at a time:
    the candidates of `alive` that hold after the call when all of them are
    assumed before it.  A batch that can fail drops every candidate its
    model makes false (falsified(model, the candidates left), or the model's
    value of each goal); one the solver gives up on (after `quick`
    milliseconds) is halved, and a single candidate it gives up on (after
    `slow`) is dropped (counted: the invariant is then
    weaker than it could be, and still an invariant).  A batch that is
    proved keeps the candidates its proof assumed (the unsat core) and is
    proved again only if one of them is dropped: at the end every candidate
    left has a proof from candidates that are left.  core: the proofs so
    far, kept from one run to the next (more candidates: the same proofs).
    (them or None if the time ran out, the number dropped undecided)."""
    import time
    live = dict.fromkeys(alive)
    of = {str(x): i for i, x in lit.items()}
    core = {} if core is None else core        # a proved candidate: the candidates its proof assumed
    undecided, rounds = 0, 0
    todo = [alive[i:i + batch] for i in range(0, len(alive), batch)][::-1]
    while todo:
        b = [i for i in todo.pop() if i in live and i not in core]
        if not b:
            continue
        if deadline is not None and time.time() > deadline:
            return None, undecided
        rounds += 1
        sol.push()
        sol.add(z3.Or(*[z3.Not(post[i]) for i in b]))
        sol.set('timeout', quick if len(b) > 1 else slow)
        t0 = time.time()
        r = sol.check(*[lit[i] for i in live])
        if time.time() - t0 > 1:
            note(f'    query {rounds}: {r} in {time.time() - t0:.1f}s, {len(b)} goals, {len(live)} assumed'
                 + (': ' + ' | '.join(name(i) for i in b[:6]) if name else ''))
        dead, used = [], None
        if r == z3.sat:
            md = sol.model()
            if falsified is not None:
                dead = [i for i in falsified(md) if i in live]
            if not dead:
                dead = [i for i in (b if falsified is not None else live)
                        if z3.is_false(md.eval(post[i], model_completion=True))]
        elif r == z3.unsat:
            used = frozenset(of[str(x)] for x in sol.unsat_core())
        sol.pop()
        if used is not None:
            core.update((i, used) for i in b)
            continue
        if not dead:
            if len(b) > 1:
                todo += [b[len(b) // 2:], b[:len(b) // 2]]
                continue
            dead = b
            undecided += 1
        gone = set(dead)
        for i in dead:
            del live[i]
            core.pop(i, None)
        stale = [i for i, c in core.items() if c & gone]
        for i in stale:
            del core[i]
        todo = [stale[i:i + batch] for i in range(0, len(stale), batch)] + todo + [b]   # (the stale ones last)
        if rounds % 25 == 0:
            note(f'    step: {len(live)} alive, {len(core)} proved, {undecided} undecided')
    note(f'    step: {len(live)} alive after {rounds} queries, {undecided} undecided')
    return list(live), undecided


def houdini(z3, sol, alive: list, goal: dict, assume: Optional[dict] = None, soft: bool = False) -> Optional[list]:
    """The candidates of `alive` that survive: while some goal[i] can be
    false (under the assumption literals of the ones still alive), drop the
    ones the model makes false.  None: the solver gave up (soft: what is
    left by then, which is then a filter and not a proof)."""
    alive = list(alive)
    while alive:
        sol.push()
        sol.add(z3.Or(*[z3.Not(goal[i]) for i in alive]))
        r = sol.check(*([assume[i] for i in alive] if assume else []))
        note(f'    houdini: {len(alive)} alive, {r}')
        if r != z3.sat:
            sol.pop()
            return alive if r == z3.unsat or soft else None
        md = sol.model()
        keep = [i for i in alive if z3.is_true(md.eval(goal[i], model_completion=True))]
        sol.pop()
        if len(keep) == len(alive):            # no progress (a model that leaves a goal undecided)
            return alive if soft else None
        alive = keep
    return alive


# -- the window: W calls from any state --------------------------------------------------------

CAPS = (1, 2, 3, 4, 6, 8)                 # the lengths tried as the bound of the state's lists


def has_list(sh: Optional[tuple]) -> bool:
    return sh is not None and (sh[0] == 'list' or (sh[0] == 'opt' and has_list(sh[1]))
                               or (sh[0] == 'map' and has_list(sh[2]))
                               or (sh[0] == 'rec' and any(has_list(x) for x in sh[3])))


class Window:
    """W consecutive calls from any state of the shape whose lists hold at
    most L numbers: the reading's one-step encoding (its ghosts and registers
    free before the first call, its rigid variables free constants) and the
    code's own step, over the abstract state."""

    def __init__(self, S, s: str, fn: SW.Fn, tr, shs: dict, W: int, L: int):
        self.z3 = z3 = tr.z3
        self.S, self.s, self.fn, self.tr, self.shs, self.W, self.L = S, s, fn, tr, shs, W, L
        self.w = w = SW._IntSpec(S, [s], fn, W, window=True, free_rigids=True)
        self.facts = list(w.dom)
        self.nd = len(self.facts)              # (what follows them: the facts of the shape)
        tr.dom = self.facts
        self.ab = Abstract(tr, L, self.facts)
        self.F = [{name: self.ab.build(sh, f'self.{name}') for name, sh in sorted(shs.items())}]
        self.trans = []
        for p in range(1, W + 1):
            new, code, rets = tr.step(fn, self.F[-1], call_args(fn, w, p))
            self.F.append(new)
            self.trans += [w.x[(fn.outcome, p)] == code] + [w.x[(r, p)] == rets[r] for r in fn.rets]
        n = -1
        while n != len(w.reg):                 # every register, at every call of the window
            n = len(w.reg)
            for r in list(w.reg.values()):
                for p in range(W + 1):
                    w.reg_value(r, p)
        self.regs = list(w.reg.values())
        self.kappa = z3.Int('any_key')
        self.meta = [x[:4] for x in self.state(w, self.F, 0)]
        self.canon = {n: (z3.Bool if sort == 'bool' else z3.Int)(f'c.{n}') for n, sort, _, _ in self.meta}

    def state(self, enc, fields: list, p: int, key=None) -> list:
        """The state after call p as (name, sort, role, key label, term):
        the fields, the dictionaries at each rigid variable and at one more
        key (any key, unless one is given), the ghosts and the registers."""
        from .lang import unparse
        self.tr.dom = self.facts if enc is self.w else list(enc.dom)
        keys = dict(self.w.rig)
        keys[KEY] = self.kappa if key is None else key
        out = project(self.tr, self.shs, fields[p], keys, self.L)
        out += [(g, 'int', 'ghost', None, enc.g[(self.s, g, p + 1)]) for g in enc.gdecl[self.s]]
        out += [(unparse(r['node']) + (str(r['env']) if r['env'] else ''), 'bool', 'reg', None, enc.reg_value(r, p))
                for r in self.regs]
        return out

    def subs(self, enc, fields: list, p: int, key=None) -> list:
        return [(self.canon[x[0]], x[4]) for x in self.state(enc, fields, p, key)]

    def instances(self) -> list:
        """The keys the window looks up: what is assumed of every key before
        a call is used of these."""
        seen = {}
        for v in self.F[0].values():
            if v.ty == 'map' and v.t is not None:
                for k, _ in list(v.t.seen.values()):
                    seen[k.get_id()] = k
        for k in list(self.w.rig.values()) + [self.kappa]:
            seen[k.get_id()] = k
        return list(seen.values())

    def open(self, timeout: int):
        """A solver holding the window, to which candidates are admitted."""
        z3, W = self.z3, self.W
        T = self.instances()
        self.at = {(p, None): self.subs(self.w, self.F, p) for p in range(W + 1)}
        for p in range(W):
            for j, t in enumerate(T):
                self.at[(p, j)] = self.subs(self.w, self.F, p, t)
        self.nT = len(T)
        self.sol = z3.Solver()
        self.sol.set('timeout', timeout)
        self.sol.add(*self.facts)              # (complete by now: every key has been looked up)
        self.sol.add(*self.trans)
        self.lit, self.post = {}, {}

    def admit(self, cands: list, idxs: list):
        """Candidates into the solver: each under its literal in the W
        states before the window's last call (one about any key: at every
        key the window looks up), and its goal: itself after that call (at
        any key)."""
        z3, W = self.z3, self.W
        uni = {n for n, _, _, label in self.meta if label == KEY}
        for i in idxs:
            _, term, names = cands[i]
            where = [(p, j) for p in range(W) for j in range(self.nT)] if names & uni else [(p, None) for p in range(W)]
            self.lit[i] = z3.Bool(f'inv_{i}')
            self.sol.add(z3.Implies(self.lit[i], z3.And(*[z3.substitute(term, *self.at[x]) for x in where])))
            self.post[i] = z3.substitute(term, *self.at[(W, None)])

    def step(self, cands: list, alive: list, timeout: int, deadline=None) -> tuple:
        """The candidates that, held before the window's last call, hold
        after it: (them or None, the number dropped undecided)."""
        self.open(timeout)
        self.admit(cands, alive)
        return houdini_step(self.z3, self.sol, alive, self.post, self.lit, deadline=deadline)

    def caps(self) -> list:
        return [(f'{n} <= {self.L}', self.canon[n] <= self.L, {n})
                for n, _, role, label in self.meta if role == 'len' and label in (KEY, None)]

    def capped(self, timeout: int) -> bool:
        """A call leaves no list longer than L."""
        cands = self.caps()
        if not cands:
            return True
        alive = self.step(cands, list(range(len(cands))), timeout)[0]
        return alive is not None and len(alive) == len(cands)

    def agrees(self, enc0, fields0: list, code0: list, upto: int, timeout: int) -> Optional[str]:
        """The window is the unrolled model, one call at a time: with the
        state before call n of the unrolled model put for the abstract state
        (each function of the key: what the unrolled dictionary has at that
        key), the window's outcome and results, the state it leaves (at the
        rigid variables and at any key), the items' verdicts, the ghosts and
        the registers are the unrolled model's at call n; for the states
        whose lists hold at most L numbers.  None, or what differs."""
        z3, w, W, fn, s = self.z3, self.w, self.W, self.fn, self.s
        sigs = fn.signals + fn.base_signals
        its = self.S.mon(s).items
        var, key = z3.Var(0, z3.IntSort()), z3.Int('a_key')
        after = self.state(w, self.F, W)
        shape = self.facts[self.nd:]
        for n in range(W, upto + 1):
            off = n - W
            ex = {x[0]: x[4] for x in self.state(enc0, fields0, off, key)}
            sb = [(w.x[(g, p)], enc0.x[(g, off + p)]) for p in range(1, W + 1) for g in sigs]
            sb += [(self.ab.fun(name, (), sort == 'bool'), ex[name]) for name, sort, role, label in self.meta
                   if label is None and role not in ('ghost', 'reg')]
            sb += [(w.g[(s, g, 1)], enc0.g[(s, g, off + 1)]) for g in w.gdecl[s]]
            for r in self.regs:                # the free values of the window's registers: the real ones
                sb += [(v, enc0.reg_value(r, off + i)) for i, v in r['at'].items() if 0 < i <= r['depth']]
                sb.append((w.reg_value(r, 0), enc0.reg_value(r, off)))
            fsb = [(f, z3.substitute(ex[name], (key, var))) for name, f in self.ab.funs.items()]

            def exact(t):
                t = z3.substitute(t, *sb)
                return z3.substitute_funs(t, *fsb) if fsb else t
            want = {x[0]: x[4] for x in self.state(enc0, fields0, n)}
            pairs = [(exact(x[4]), want[x[0]]) for x in after]
            for hs, hs0 in ((w.raw_holds, enc0.raw_holds), (w.aholds, enc0.aholds)):
                pairs += [(exact(h), hs0[(s, iid, n)]) for (_, iid, _), h in hs.items()
                          if its[iid].pattern != 'after_reset']
            sol = z3.Solver()
            sol.set('timeout', timeout)
            sol.add(*enc0.dom)
            for cs in code0[:n]:
                sol.add(*cs)
            sol.add(*[exact(f) for f in shape])
            sol.add(z3.Or(z3.Not(z3.And(*[exact(c) for c in self.trans])), *[a != b for a, b in pairs]))
            r = sol.check()
            if r != z3.unsat:
                return f'the one-step model is not the unrolled one at call {n}' + \
                    ('' if r == z3.sat else ' (not decided in time)')
        return None


def induct_keyed(S, s: str, fn: SW.Fn, src: str, tr, enc0, fields0: list, code0: list, reqs: list,
                 calls: Optional[list] = None, res: Optional[dict] = None, timeout: int = 120000,
                 depth: int = 3, budget: int = 900) -> dict:
    """Requirements of reading s that hold at every call of every sequence
    of any length, by induction on the calls, for an object whose state
    holds dictionaries and lists.

    The state is abstract (Abstract): a dictionary is any function of the
    key, a list any list of at most L numbers, L the least of CAPS that no
    call exceeds.  The window is checked against the unrolled model at the
    calls W .. W + depth (Window.agrees).  The invariant is found by Houdini
    from candidates of two kinds: about the fields, the ghosts and the
    dictionaries at the reading's rigid variables; and about the
    dictionaries at any key, which are assumed before a call at every key
    the call looks up and proved after it at a key nothing is known of.
    With the scope's calls and their results, the candidates are first
    sifted on the states the object is in on the scope (samples, sift): a
    filter, which proves nothing.  The ones left must hold in the states
    after 0 .. W - 1 calls (the base of the induction) and survive the step
    (houdini_step), within `budget` seconds.  The facts x <= y + d are
    added only if a requirement is not proved without them: the invariant
    so far and its proofs are kept.

    {'status': 'ok', 'window', 'cap', 'candidates', 'sampled', 'invariant',
     'undecided', 'proved': {req: [the conjuncts its proof used]}} or
    {'status': 'none', 'why'}."""
    import time
    import z3
    from . import prove as P
    Kn = enc0.k
    try:
        W = SW.window_len(S, s, fn)
        if W > Kn:
            return {'status': 'none', 'why': f'a window of {W} calls, an encoding of {Kn}'}
        shs = shapes(fields0)
        m, why = None, 'no bound on the lists of the state'
        for L in CAPS if any(has_list(x) for x in shs.values()) else (0,):
            try:
                x = Window(S, s, fn, tr, shs, W, L)
            except Untranslatable as e:
                why = str(e)
                continue
            if x.capped(timeout):
                m = x
                break
        if m is None:
            return {'status': 'none', 'why': why}
        note(f'window of {W}, lists of at most {m.L}')
        bad = m.agrees(enc0, fields0, code0, min(Kn, W + depth), timeout)
        note(f'the window agrees with the unrolled model: {bad is None}')
        if bad is not None:
            return {'status': 'none', 'why': bad}
        consts = P._consts(S, s, src)
        anyk = {n for n, _, _, label in m.meta if label == KEY}
        fixed = [(n, sort, role, m.canon[n]) for n, sort, role, label in m.meta if label != KEY]
        uni = [(n, sort, role, m.canon[n]) for n, sort, role, label in m.meta
               if label == KEY or (label is None and role not in ('ghost', 'reg'))]
        offs = sorted({1, *P._distances(S, s, src)})       # (x + 1 <= y: x < y)
        G = grammars([grammar(z3, fixed, consts, m.L, offs=offs), grammar(z3, uni, consts, m.L, must=anyk, offs=offs)])
        facts = G['facts']
        g = P.compile_terms(z3, [t for _, t, _ in facts], [m.canon[n] for n, _, _, _ in m.meta])
        states = samples(P, m, enc0, fields0, calls, res) if calls is not None else []
        frame, its = S.b.frame_ids, S.mon(s).items
        by_req: dict[str, list] = {}
        for (_, iid, _), h in m.w.raw_holds.items():
            if iid not in frame:
                by_req.setdefault(its[iid].req, []).append(h)
        cands, pairs, alive = [], [], []       # admitted: (text, term, names), (a, c) in the grammar; the ones held
        core, proved, undecided, total = {}, {}, 0, 0
        m.open(min(timeout, 20000))
        deadline = time.time() + budget

        def base(idxs):
            """The ones that hold in the states after 0 .. W - 1 calls."""
            for p in range(W):
                sol = z3.Solver()
                sol.set('timeout', timeout)
                sol.add(*enc0.dom)
                for cs in code0[:p]:
                    sol.add(*cs)
                sb = m.subs(enc0, fields0, p)
                idxs = houdini(z3, sol, idxs, {i: z3.substitute(cands[i][1], *sb) for i in idxs})
                if not idxs:
                    break
            return idxs

        def admit(acs) -> bool:
            """More candidates: the ones that hold at the base, into the solver."""
            new = list(range(len(cands), len(cands) + len(acs)))
            cands.extend(candidate(z3, facts, ac) for ac in acs)
            pairs.extend(acs)
            new = base(new)
            if new is not None:
                m.admit(cands, new)
                alive.extend(new)
            return new is not None

        def falsified(md):
            """The candidates false in the model's state after the call."""
            st = [md.eval(t, model_completion=True) for _, t in m.at[(W, None)]]
            if not all(z3.is_int_value(x) or z3.is_true(x) or z3.is_false(x) for x in st):
                return []
            v = g(*[x.as_long() if z3.is_int_value(x) else z3.is_true(x) for x in st])
            return [i for i, (a, c) in enumerate(pairs) if (a is None or v[a]) and not v[c]]
        for wide in (False, True):             # first without the facts x <= y + d, then with them
            part = G if wide else dict(G, cands=[ac for ac in G['cands'] if ac[1] not in G['near']])
            total = len(part['cands'])
            kept, aside = sift(g, part, states, frozenset(c[0] for c in m.caps()))
            seen = {c[0] for c in cands}
            kept = [ac for ac in kept if text_of(facts, ac) not in seen]
            aside = {by: [ac for ac in acs if text_of(facts, ac) not in seen] for by, acs in aside.items()}
            note(f'{total} candidates, {len(states)} sampled states: {len(kept)} to try, '
                 f'{sum(map(len, aside.values()))} set aside')
            if not admit(kept):
                return {'status': 'none', 'why': 'the base of the induction was not decided in time'}
            fresh = True
            while True:
                held = {cands[i][0] for i in alive}
                seen = {c[0] for c in cands}
                back = [ac for t in list(aside) if t in seen and t not in held for ac in aside.pop(t)]
                if back:                       # what a candidate that is not invariant stood for
                    if not admit(back):
                        return {'status': 'none', 'why': 'the base of the induction was not decided in time'}
                    fresh = True
                    continue
                if not fresh:
                    break
                left, und = houdini_step(z3, m.sol, alive, m.post, m.lit, deadline=deadline, falsified=falsified,
                                         core=core, name=lambda i: cands[i][0])
                if left is None:
                    return {'status': 'none', 'why': 'the step of the induction was not decided in time'}
                alive[:] = left
                undecided += und
                fresh = False
            note(f'an invariant of {len(alive)} conjuncts')
            if any(c[0] not in held for c in m.caps()):
                return {'status': 'none', 'why': f'lists of at most {m.L} numbers: not an invariant'}
            sol, lit = m.sol, m.lit
            sol.set('timeout', timeout)
            back = {str(lit[i]): cands[i][0] for i in alive}
            for req in reqs:
                if req in proved:
                    continue
                sol.push()
                sol.add(z3.Or(*[z3.Not(h) for h in by_req.get(req, [])]))
                r = sol.check(*[lit[i] for i in alive])
                if r == z3.sat and LOG is not None:       # a state the invariant allows, where the call breaks it
                    md = sol.model()
                    show = [f'{x[0]} = {md.eval(t, model_completion=True)}' for x, (_, t) in zip(m.meta, m.at[(W - 1, None)])]
                    args = [str(md.eval(m.w.x[(sg, W)], model_completion=True)) for _, sg, _ in fn.args]
                    note(f'    {req} is not implied: {fn.name}({", ".join(args)}) from ' + ', '.join(show))
                if r == z3.unsat:
                    # the conjuncts this proof needs: its core, less what it can do without
                    used = sorted(sol.unsat_core(), key=lambda x: ('==' in back[str(x)], -len(back[str(x)])))
                    for x in list(used):
                        rest = [y for y in used if y is not x]
                        if sol.check(*rest) == z3.unsat:
                            used = rest
                    proved[req] = sorted(back[str(x)] for x in used)
                sol.pop()
            if all(r in proved for r in reqs):
                break
    except (Untranslatable, SW.Unsupported) as e:
        return {'status': 'none', 'why': str(e)}
    return {'status': 'ok', 'window': W, 'cap': m.L, 'candidates': total, 'sampled': len(states),
            'invariant': len(alive), 'undecided': undecided, 'proved': proved}
