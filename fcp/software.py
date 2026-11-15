"""Software adapter: a Python function checked as a chip without memory.

design.yaml `function` maps the arguments of a function to input signals, its
return value (or tuple) to output signals, and the way a call ends to an
outcome signal.  One cycle is one call.  The prompt side needs nothing new:
every reading compiles to monitors over these signals, and the spec-only
analyses (consistency, forcing, determinacy, readings compared in context)
run as for any chip.  The code side is new, because a function written by a
model cannot be compiled to a circuit in general.  It is run instead:

* scope: for every argument, a dense range, every integer constant of the
  readings, the prompt and the code together with its neighbours, the ends
  of the signal range, and random values over it;
* calls: every point of the scope, ordered in sweeps, so that two calls that
  differ in one argument by one scope step are adjacent.  A relational
  requirement such as monotonicity compares consecutive calls;
* run: the function runs in a separate process on all calls;
* check: the compiled monitor of a reading is simulated on the recorded
  trace (Icarus), and every failure is replayed in a fresh process.

The evidence is exhaustive within the scope and says nothing beyond it.
"""
from __future__ import annotations

import array
import ast
import itertools
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional

from . import vl
from .agents import IVERILOG
from .harness import vw
from .kernel import VVP
from .lang import seq_len_port

PY = sys.executable


class SoftwareError(Exception):
    pass


@dataclass
class Fn:
    name: str
    args: list[tuple[str, str, str]]   # (argument, signal, type: int | bool | str | list)
    rets: list[str]                    # output signals: the returned value, or one per tuple element
    tuple_: bool
    outcome: str
    raises: list[str]
    widths: dict[str, int]             # every interface port
    scope_cfg: dict
    seqs: dict[str, tuple[int, int]] = field(default_factory=dict)   # sequence signal -> (slot width, max length)
    kinds: dict[str, str] = field(default_factory=dict)              # argument and return signal -> type
    cls: Optional[str] = None          # a method of an object of this class: calls share its state
    init: list = field(default_factory=list)                         # constructor arguments
    module: str = ''                   # the module (file) the implementation is in; default: name
    baseline: Optional[dict] = None    # a change: the code before it, run on the same calls (see baseline_values)
    # records: per Python parameter {name, kind: value | record | records, pos: positions in a call, keys,
    # bools, cls}; empty when every parameter is one signal.  ret_shape: the same for a returned record.
    shape: list = field(default_factory=list)
    ret_shape: Optional[dict] = None
    groups: dict[str, list[str]] = field(default_factory=dict)       # sequence signal -> its group (one length)
    # an object with several methods: per method {name, op, pos: its arguments' positions in a call,
    # kinds, rets: its result signals, tuple_}; position 0 of every call is the method's op
    methods: list = field(default_factory=list)

    @property
    def base_signals(self) -> list[str]:
        """Input signals that carry the answer of the code before a change."""
        b = self.baseline
        return (list(b['returns']) + [b['outcome']]) if b else []

    @property
    def stateful(self) -> bool:
        return self.cls is not None

    # -- values: what the function sees, and the ports that carry it ----------
    @property
    def signals(self) -> list[str]:
        return [x[1] for x in self.args] + self.rets + [self.outcome]

    @property
    def args_sigs(self) -> list[str]:
        return [x[1] for x in self.args]

    @property
    def has_seq(self) -> bool:
        return any(x in self.seqs for x in self.signals)

    @property
    def structured(self) -> bool:
        """Some parameter or the returned value is a record or a list of them."""
        return bool(self.shape) or self.ret_shape is not None

    def method(self, c) -> Optional[dict]:
        """The method that call c is a call of (objects with several methods)."""
        return next((m for m in self.methods if m['op'] == c[0]), None) if self.methods else None

    def canon(self, c: tuple) -> tuple:
        """Call c in canonical form: the arguments the called method does not
        take are 0 (an unknown op becomes the first method)."""
        if not self.methods:
            return c
        m = self.method(c)
        if m is None:
            m = self.methods[0]
            c = (m['op'],) + tuple(c[1:])
        keep = set(m['pos']) | {0}
        return tuple(x if j in keep else (self.default(self.args[j][1]) if self.args[j][1] in self.seqs else 0)
                     for j, x in enumerate(c))

    def group(self, sig: str) -> list[str]:
        """The sequence signals that always have sig's length (sig alone, or the fields of a list of records)."""
        return self.groups.get(sig, [sig])

    def ports(self, sig: str) -> list[tuple[str, int]]:
        if sig in self.seqs:
            return [(sig, self.widths[sig]), (seq_len_port(sig), self.widths[seq_len_port(sig)])]
        return [(sig, self.widths[sig])]

    def codes(self, v) -> list[int]:
        return [ord(c) for c in v] if isinstance(v, str) else [int(x) for x in v]

    def encode(self, sig: str, v) -> dict[str, int]:
        """Port values for value v of signal sig (slots packed, zero beyond the length)."""
        if sig in self.seqs:
            w = self.seqs[sig][0]
            cs = self.codes(v)
            return {sig: sum(c << (k * w) for k, c in enumerate(cs)), seq_len_port(sig): len(cs)}
        return {sig: int(v)}

    def value_of(self, sig: str, codes: list[int]):
        return ''.join(map(chr, codes)) if self.kinds.get(sig) == 'str' else tuple(codes)

    def decode(self, sig: str, get):
        """The value of sig from its port values (get: port -> int), in canonical form."""
        if sig in self.seqs:
            w, n = self.seqs[sig]
            ln, data = min(get(seq_len_port(sig)), n), get(sig)
            return self.value_of(sig, [(data >> (k * w)) & ((1 << w) - 1) for k in range(ln)])
        return get(sig)

    def default(self, sig: str):
        """The value an output carries when the call did not return one."""
        return ('' if self.kinds.get(sig) == 'str' else ()) if sig in self.seqs else 0

    def fmt(self, sig: str, v) -> str:
        k = self.kinds.get(sig)
        if k == 'bool':
            return str(bool(v))
        if k == 'str':
            return json.dumps(v)
        if k == 'list':
            return '[' + ', '.join(str(x) for x in v) + ']'
        return str(v)

    def shown(self, sig: str, v) -> str:
        """A value of sig as a question shows it: how a call ended, by name."""
        return self.outcome_name(v) if sig == self.outcome else self.fmt(sig, v)

    @property
    def other_exc(self) -> int:
        return 1 + len(self.raises)

    @property
    def other_val(self) -> int:
        return 2 + len(self.raises)

    def outcome_name(self, k: int) -> str:
        if k == 0:
            return 'returned'
        if k <= len(self.raises):
            return f'raised {self.raises[k - 1]}'
        if k == self.other_exc:
            return 'raised another exception or did not finish'
        # a code beyond the last names no ending: no search yields one, and none is shown as another
        return 'returned something else' if k == self.other_val else f'ended with code {k}, which names no ending'


def function(S) -> Fn:
    d = S.b.raw_design.get('function')
    if not d:
        raise SoftwareError(f'{S.b.design}: design.yaml has no function section')
    widths = {s.name: s.width for s in S.b.iface.signals}
    seqs = dict(getattr(S.b.iface, 'seqs', {}) or {})
    if d.get('methods'):
        return _methods_fn(S, d, widths, seqs)
    ifc_groups = dict(getattr(S.b.iface, 'groups', {}) or {})
    groups = {m: list(ms) for ms in ifc_groups.values() for m in ms}

    def record(x: dict, where: str, at: int) -> tuple[list, dict]:
        """The flat (name, signal, type) entries of a record parameter or
        returned record, and its shape."""
        t, fs = x['type'], x.get('fields') or []
        if not fs:
            raise SoftwareError(f'{where}: a {t} needs fields')
        flat = [(f'{x.get("name", "return")}.{f["key"]}', f.get('signal', f['key']),
                 'list' if t == 'records' else f.get('type', 'int')) for f in fs]
        bools = [f.get('type', 'int') == 'bool' for f in fs]
        if t == 'records':
            sigs = [sig for _, sig, _ in flat]
            if any(f.get('type', 'int') not in ('int', 'bool') for f in fs):
                raise SoftwareError(f'{where}: the fields of a list of records are int or bool')
            if any(sig not in groups for sig in sigs) or sorted(groups[sigs[0]]) != sorted(sigs):
                raise SoftwareError(f'{where}: the fields\' signals must be exactly one interface group '
                                    f'(sequence signals with the same `group`)')
            if any(b and seqs[sig][0] != 1 for b, sig in zip(bools, sigs)):
                raise SoftwareError(f'{where}: a bool field needs elements of width 1')
        return flat, {'kind': t, 'keys': [f['key'] for f in fs], 'pos': list(range(at, at + len(fs))),
                      'bools': bools, 'cls': x.get('class')}

    args, shape = [], []
    for a in d['args']:
        if a.get('type') in ('record', 'records'):
            flat, sh = record(a, f'function: argument {a["name"]}', len(args))
            args += flat
            shape.append(dict(sh, name=a['name']))
        else:
            shape.append({'name': a['name'], 'kind': 'value', 'pos': [len(args)]})
            args.append((a['name'], a.get('signal', a['name']), a.get('type', 'int')))
    if all(x['kind'] == 'value' for x in shape):
        shape = []
    r = d['returns']
    ret_shape = None
    if r.get('type') in ('record', 'records'):
        flat, ret_shape = record(r, 'function: returns', 0)
        rets, rtypes = [sig for _, sig, _ in flat], [k for _, _, k in flat]
        del ret_shape['pos']
    else:
        rets = list(r['signals']) if 'signals' in r else [r['signal']]
        rtypes = list(r.get('types') or [r.get('type', 'int')] * len(rets))
    if len(rtypes) != len(rets):
        raise SoftwareError('function: returns.types needs one type per returned signal')
    kinds = {sig: k for _, sig, k in args}
    kinds.update(zip(rets, rtypes))
    for sig in [x[1] for x in args] + rets + [d['outcome']['signal']]:
        if sig not in widths:
            raise SoftwareError(f'function: {sig} is not an interface signal')
    for sig, k in kinds.items():
        if (k in ('str', 'list')) != (sig in seqs):
            raise SoftwareError(f'function: {sig} has type {k}, so it must {"" if k in ("str", "list") else "not "}'
                                f'be a sequence signal (interface `length`)')
    base = None
    if d.get('baseline'):
        bl = d['baseline']
        base = {'path': S.b.path(bl['path']), 'args': list(bl['args']), 'returns': list(bl['returns']),
                'outcome': bl['outcome'], 'name': bl.get('name', d['name'])}
        for sig in base['returns'] + [base['outcome']]:
            if sig not in widths:
                raise SoftwareError(f'function.baseline: {sig} is not an interface signal')
        if not set(base['args']) <= {a for a, _, _ in args}:
            raise SoftwareError('function.baseline: args must be arguments of the function')
        if shape or ret_shape:
            raise SoftwareError('function.baseline: a change to a function of records is not supported yet')
    return _outcome_fits(Fn(d['name'], args, rets, 'signals' in r, d['outcome']['signal'],
                            list(d['outcome'].get('raises') or []), widths, dict(d.get('scope') or {}), seqs, kinds,
                            d.get('class'), list(d.get('init') or []), d.get('module') or d['name'], base, shape,
                            ret_shape, groups))


def _methods_fn(S, d: dict, widths: dict, seqs: dict) -> Fn:
    """An object with several methods: the op signal first, then every
    argument signal once (methods may share one), and every result signal
    once."""
    if not d.get('class'):
        raise SoftwareError('function.methods: a class is needed (the methods of one object)')
    op = d['op']['signal']
    args, kinds, rets, methods = [('op', op, 'int')], {op: 'int'}, [], []
    for m in d['methods']:
        pos, mk = [], []
        for a in m.get('args') or []:
            t = a.get('type', 'int')
            if t in ('record', 'records'):
                raise SoftwareError(f'function.methods: {m["name"]}: records are not supported in methods yet')
            sig = a.get('signal', a['name'])
            if sig not in [x[1] for x in args]:
                args.append((sig, sig, t))
                kinds[sig] = t
            elif kinds[sig] != t:
                raise SoftwareError(f'function.methods: {sig} has two types')
            pos.append([x[1] for x in args].index(sig))
            mk.append(t)
        r = m.get('returns') or {}
        msig = list(r['signals']) if 'signals' in r else ([r['signal']] if 'signal' in r else [])
        mt = list(r.get('types') or [r.get('type', 'int')] * len(msig))
        for sig, t in zip(msig, mt):
            if sig not in rets:
                rets.append(sig)
                kinds[sig] = t
        methods.append({'name': m['name'], 'op': int(m['op']), 'pos': pos, 'kinds': mk, 'rets': msig,
                        'tuple_': 'signals' in r})
    if len({m['op'] for m in methods}) != len(methods) or any(m['op'] < 1 for m in methods):
        raise SoftwareError('function.methods: every method needs its own op, from 1')
    outcome = d['outcome']['signal']
    for sig in [x[1] for x in args] + rets + [outcome]:
        if sig not in widths:
            raise SoftwareError(f'function: {sig} is not an interface signal')
    if max(m['op'] for m in methods) >= 1 << widths[op]:
        raise SoftwareError(f'function.op: {op} is too narrow for the ops')
    for sig, k in kinds.items():
        if (k in ('str', 'list')) != (sig in seqs):
            raise SoftwareError(f'function: {sig} has type {k}, so it must {"" if k in ("str", "list") else "not "}'
                                f'be a sequence signal (interface `length`)')
    fn = Fn(d.get('name') or d['class'], args, rets, False, outcome, list(d['outcome'].get('raises') or []),
            widths, dict(d.get('scope') or {}), seqs, kinds, d['class'], list(d.get('init') or []),
            d.get('module') or d['class'].lower(), None, methods=methods)
    return _outcome_fits(fn)


def _outcome_fits(fn: Fn) -> Fn:
    if fn.other_val >= 1 << fn.widths[fn.outcome]:
        raise SoftwareError(f'function.outcome: {fn.outcome} needs codes 0 to {fn.other_val} (returned, '
                            f'{len(fn.raises)} exceptions, another exception, anything else): widen it')
    return fn


# ----------------------------------------------------------------------------
# scope and calls
# ----------------------------------------------------------------------------

def entry_env(fn: 'Fn') -> dict:
    """The runner's environment: an implementation that is a package is
    entered at the function's module (a dotted name)."""
    return dict(os.environ, FCP_ENTRY=fn.module)


def entry_file(fn: 'Fn', src: str) -> str:
    """The file that holds the function: src itself, or in a package its
    module (`shop.pricing` -> shop/pricing.py or shop/pricing/__init__.py)."""
    if not os.path.isdir(src):
        return src
    base = os.path.join(src, *fn.module.split('.'))
    return base + '.py' if os.path.exists(base + '.py') else os.path.join(base, '__init__.py')


def py_files(src: str) -> list[str]:
    """The source files of an implementation: src, or every module of a
    package except tests (the scope takes its constants from these)."""
    if not os.path.isdir(src):
        return [src]
    out = []
    for dp, dns, fns in os.walk(src):
        dns[:] = sorted(x for x in dns if not x.startswith(('.', '__pycache__', 'test')))
        out += [os.path.join(dp, f) for f in sorted(fns) if f.endswith('.py') and not f.startswith('test')]
    return out


def constants(S, srcs=(), sets: Optional[list[str]] = None) -> set[int]:
    """Integer constants of the readings (all, or those in sets), the
    documents and the code: the boundaries an off-by-one bug sits next to."""
    out: set[int] = set()
    texts = []
    for s, fs in S.b.fsets.items():
        if sets is None or s in sets:
            texts.append(json.dumps(fs))
    for doc in S.b.docs.values():
        with open(S.b.path(doc['path'])) as f:
            texts.append(f.read())
    for t in texts:
        t = re.sub(r'(?<=\d),(?=\d{3})', '', t)          # 1,000,000
        out |= {int(x) for x in re.findall(r'(?<![\w.])\d+(?![\w])', t)}
        out |= {round(float(x) * 100) for x in re.findall(r'\d+\.\d+', t)}   # $4.99 -> 499
    for src in [x for y in srcs for x in py_files(y)]:
        with open(src) as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and type(n.value) in (int, float):
                v = n.value
                out.add(int(v))
                if isinstance(v, float) and abs(v * 100 - round(v * 100)) < 1e-9:
                    out.add(round(v * 100))
    return out


def scope(S, fn: Fn, srcs=(), seed: int = 1, small: bool = False) -> dict[str, list[int]]:
    """Values of every argument.  small: the dense range cut to 200 values
    and only a few random values (for descending sweeps and mutants).  The
    configured values of a string or list are whole strings and lists, which
    seq_calls takes; they are not integers of this scope."""
    consts = constants(S, srcs)
    rng = random.Random(seed)
    vals = {}
    for arg, sig, kind in fn.args:
        top = (1 << fn.widths[sig]) - 1
        if kind == 'bool' or top == 1:
            vals[arg] = [0, 1]
            continue
        cfg = fn.scope_cfg.get(arg, {})
        lo, hi = cfg.get('dense', [0, min(top, 255)])
        if small:
            hi = min(hi, lo + 199)
        given = () if sig in fn.seqs else cfg.get('values', [])
        v = set(range(max(0, lo), min(top, hi) + 1)) | set(given) | {top - 1, top}
        for c in consts:
            v |= {x for x in (c - 1, c, c + 1) if 0 <= x <= top}
        for _ in range(8 if small else cfg.get('random', 64)):
            v.add(rng.randint(0, top))
        vals[arg] = sorted(v)
    return vals


def sweeps(fn: Fn, vals: dict[str, list[int]], descending: bool = False) -> list[tuple]:
    """Every point of the scope once per argument, in runs along that argument
    with the others fixed: consecutive calls differ in one argument by one
    scope step."""
    names = [a for a, _, _ in fn.args]
    calls = []
    for d, name in enumerate(names):
        line = vals[name][::-1] if descending else vals[name]
        for combo in itertools.product(*[vals[n] for n in names if n != name]):
            for x in line:
                calls.append(combo[:d] + (x,) + combo[d:])
    return calls


def calls_for(S, fn: Fn, srcs=(), seed: int = 1, small: bool = False) -> list[tuple]:
    """The call sequence: ascending sweeps over the scope, then ascending and
    descending sweeps over the small scope (or only those when small).  For a
    function of strings or lists, see seq_calls."""
    if fn.stateful:
        return object_calls(S, fn, srcs, seed, small)
    if fn.has_seq:
        return seq_calls(S, fn, srcs, seed, small)
    lite = scope(S, fn, srcs, seed, small=True)
    calls = [] if small else sweeps(fn, scope(S, fn, srcs, seed))
    return calls + sweeps(fn, lite) + sweeps(fn, lite, descending=True)


# ----------------------------------------------------------------------------
# scope of strings and lists: points drawn from the readings
# ----------------------------------------------------------------------------

CLASS_REPS = 'aZ7 .\u00b2'     # a lowercase and an uppercase letter, a digit, a space, a mark, a non-ASCII digit
CMP_OPS = {'<', '<=', '>', '>=', '==', '!='}


def _formulas(S, s: str) -> list:
    """Every formula of reading s, parsed: triggers, conditions, covers."""
    from .lang import parse
    out = []
    for it in S.mon(s).items.values():
        raw = getattr(it.args, 'raw', {}) or {}
        for k, v in raw.items():
            if isinstance(v, str):
                try:
                    out.append(parse(v))
                except Exception:
                    pass
    return out


def _walk(n, defs: dict, seen=None):
    """n and its sub-expressions, through defs.  A definition is walked where
    it is first used and not again: a reading can chain definitions, each
    naming the one before it three times, and eight such definitions walked
    at every use are 3^8 walks.  Every caller takes a set of what is yielded,
    or drops what it has seen before."""
    seen = set() if seen is None else seen
    yield n
    if n.op == 'ref' and n.val in defs and n.val not in seen:
        seen.add(n.val)
        yield from _walk(defs[n.val], defs, seen)
    for a in n.args:
        yield from _walk(a, defs, seen)


WALK = 100000                             # nodes walked with a definition expanded at every use
RIGID_CASES = 4096                        # values of its rigid variables over which the integer encoding lists
#                                           a rule (what rv.check replays): above, Unsupported


def _walk_state() -> dict:
    """What the walks of one reading share: the nodes left before a
    definition is no longer expanded at every use, the definitions walked so
    far, and whether a use was left out."""
    return {'left': WALK, 'walked': set(), 'cut': False}


def _walk_ctx(n, defs: dict, ctx: tuple = (), seen=frozenset(), st: Optional[dict] = None):
    """(node, path condition) for n and its sub-expressions, through defs:
    the conditions, as (formula, holds) pairs, under which the node decides
    the value of n (b of a && b when a holds, x of c ? x : y when c holds).

    A definition is walked at every use, each under its own conditions,
    while nodes are left in st (see _walk_state); after that only if no use
    of it has been walked, and st['cut'] records that a use was left out.
    A chain of 79 definitions that each name the one before three times is
    10^16 nodes."""
    if st is None:
        st = _walk_state()
    st['left'] -= 1
    yield n, ctx
    if n.op == 'ref' and n.val in defs and n.val not in seen:
        if st['left'] > 0 or n.val not in st['walked']:
            st['walked'].add(n.val)
            yield from _walk_ctx(defs[n.val], defs, ctx, seen | {n.val}, st)
        else:
            st['cut'] = True
    if n.op == 'bin' and n.val in ('&&', '||', '->'):
        a, b = n.args
        yield from _walk_ctx(a, defs, ctx, seen, st)
        yield from _walk_ctx(b, defs, ctx + ((a, n.val != '||'),), seen, st)
    elif n.op == 'ite':
        c, x, y = n.args
        yield from _walk_ctx(c, defs, ctx, seen, st)
        yield from _walk_ctx(x, defs, ctx + ((c, True),), seen, st)
        yield from _walk_ctx(y, defs, ctx + ((c, False),), seen, st)
    else:
        for a in n.args:
            yield from _walk_ctx(a, defs, ctx, seen, st)


def alphabet(S, fn: Fn, arg: str, sig: str, srcs=(), sets: Optional[list[str]] = None) -> list[int]:
    """Element values that sequences of argument arg are built from.  A string:
    the characters of the readings' string literals, of short string constants
    in the code, of the configured alphabet, and one character of each class
    (CLASS_REPS).  A list: the integer constants of the readings, the prompt
    and the code with their neighbours, 0, 1 and the largest slot value."""
    from .lang import parse
    w = fn.seqs[sig][0]
    top = (1 << w) - 1
    cfg = fn.scope_cfg.get(arg, {})
    if fn.kinds.get(sig) == 'list':
        vals = {0, 1, top} | set(cfg.get('elements', []))
        for c in constants(S, srcs, sets):
            vals |= {x for x in (c - 1, c, c + 1) if 0 <= x <= top}
        return sorted(vals)
    chars = set(CLASS_REPS) | set(cfg.get('alphabet', ''))
    for name in (sets if sets is not None else list(S.b.fsets)):
        defs = {k: parse(v) for k, v in (S.b.fsets[name].get('defs') or {}).items()}
        for f in _formulas(S, name) + list(defs.values()):
            for x in _walk(f, {}):
                if x.op == 'str':
                    chars |= set(x.val)
    for src in [x for y in srcs for x in py_files(y)]:
        with open(src) as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                continue
        docs = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr)}
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) <= 12 and id(n) not in docs:
                chars |= set(n.value)
    return sorted(c for c in {ord(x) for x in chars} if c <= top)


def _inputs_used(n, defs: dict, inputs: set[str]) -> bool:
    from .lang import refs
    return any(x.op == 'ref' and x.val in inputs for x in _walk(n, defs)) or bool(refs(n) & inputs)


def _drawn(S) -> dict:
    """The points drawn for a session, kept on the session.  (A table of the
    module keyed by id(S) could hand a later session, which got the id of a
    dead one, the points of another bundle.)"""
    try:
        return S._points
    except AttributeError:
        S._points = {}
        return S._points

# Seconds each search may take, or None (no bound: the studies).  `fcp review`
# sets them, so a review answers in minutes; a search cut short says so
# (BUDGET_HIT), and its evidence covers what it reached.
SCOPE_BUDGET: Optional[float] = None      # drawing request points and conforming points, per reading set
CONFLICT_BUDGET: Optional[float] = None   # the conflict search, per reading
COMPARE_BUDGET: Optional[float] = None    # one comparison of two readings; what it leaves open stays UNKNOWN
SMALL = ((1, 1), (2, 9), (4, 99), (8, 999), (16, 99999))    # an open choice's answers: (elements, top number), smallest first
BUDGET_HIT: list[str] = []                # the searches cut short


def _over(t0: float, budget: Optional[float], what: str) -> bool:
    import time
    if budget is not None and time.time() - t0 > budget:
        if what not in BUDGET_HIT:
            BUDGET_HIT.append(what)
        return True
    return False


def _src_key(S, fn: Fn, srcs, sets, seed: int) -> tuple:
    """What the drawn points take from the code: its characters (the
    alphabet), its integer constants and the integer scope.  Implementations
    that agree on these get the same points, so they are drawn once (the
    planted bugs of a corpus share the reference's)."""
    alpha = tuple(tuple(alphabet(S, fn, a, sig, srcs, sets)) for a, sig, _ in fn.args if sig in fn.seqs)
    consts = tuple(sorted(constants(S, srcs, sets)))
    ints = scope(S, fn, srcs, seed, small=True) if any(sig not in fn.seqs for _, sig, _ in fn.args) else {}
    return alpha, consts, tuple(sorted((k, tuple(v)) for k, v in ints.items()))


def request_points(S, fn: Fn, sets: list[str], srcs=(), seed: int = 1, per: int = 2,
                   limit: int = 600) -> list[tuple]:
    key = ('request', tuple(sets), _src_key(S, fn, srcs, sets, seed), seed, per, limit)
    drawn = _drawn(S)
    if key not in drawn:
        drawn[key] = _request_points(S, fn, sets, srcs, seed, per, limit)
    return list(drawn[key])


def _request_points(S, fn: Fn, sets: list[str], srcs=(), seed: int = 1, per: int = 2,
                    limit: int = 600) -> list[tuple]:
    """Calls drawn from the readings themselves, for a function of strings or
    lists.  The atoms: for every comparison of two integers in any formula
    (through defs), its two sides differing by -1, 0 and +1; every other
    condition (a comparison of other values, a quantifier, a character test)
    holding and failing; every sequence argument at every length the readings
    and the prompt name.  Each atom is solved in every context, the trigger of
    every rule and no constraint at all, so that each rule is exercised at
    every boundary.  z3 solves in the integer encoding with outputs free and
    completes at random: slots are drawn from the alphabet and fixed at random
    where possible."""
    import hashlib
    import z3
    from .lang import CHARS, TEMPORAL, parse
    enc = _IntSpec(S, sets, fn, 1, items=False)
    rng = random.Random(seed)
    inputs = {sig for _, sig, _ in fn.args}
    alpha = {sig: alphabet(S, fn, a, sig, srcs, sets) for a, sig, _ in fn.args if sig in fn.seqs}
    ints = scope(S, fn, srcs, seed, small=True) if any(sig not in fn.seqs for _, sig, _ in fn.args) else {}
    atoms, keys = [], set()
    contexts, ckeys = [z3.BoolVal(True)], set()

    def add(e):
        k = hashlib.md5(e.sexpr().encode()).hexdigest()
        if k not in keys:
            keys.add(k)
            atoms.append(e)

    for name in sets:
        enc.defs = enc.all_defs[name]
        for it in S.mon(name).items.values():
            raw = getattr(it.args, 'raw', {}) or {}
            if it.role != 'property' or it.pattern != 'implies' or not isinstance(raw.get('trigger'), str):
                continue
            t = parse(raw['trigger'])
            if not _inputs_used(t, enc.defs, inputs):
                continue
            try:
                e = enc._b(enc._ex(t, 1))
            except (Unsupported, z3.Z3Exception):
                continue
            k = hashlib.md5(e.sexpr().encode()).hexdigest()
            if k not in ckeys:
                ckeys.add(k)
                contexts.append(e)

    consts = constants(S, srcs, sets)
    for a, sig, _ in fn.args:
        if sig in fn.seqs:
            cap = fn.seqs[sig][1]
            for c in sorted({0, 1, 2, cap} | {x for c in consts for x in (c - 1, c, c + 1) if 0 <= x <= cap}):
                add(enc.x[(sig, 1)].ln == c)
    for name in sets:
        enc.defs = enc.all_defs[name]
        for f in _formulas(S, name):
            for n in _walk(f, enc.defs):
                if n.op == 'call' and n.val in TEMPORAL:
                    continue
                cond = (n.op == 'bin' and n.val in CMP_OPS | {'&&', '||', '->', '<->', 'in'}) or \
                    (n.op == 'un' and n.val == '!') or (n.op == 'call' and n.val in CHARS) or \
                    (n.op == 'quant' and n.val in ('all', 'any'))
                if not cond or not _inputs_used(n, enc.defs, inputs):
                    continue
                try:
                    if n.op == 'bin' and n.val in CMP_OPS:
                        x, y = enc._ex(n.args[0], 1), enc._ex(n.args[1], 1)
                        if not isinstance(x, _ZSeq) and not isinstance(y, _ZSeq):
                            x, y = enc._sc(x), enc._sc(y)
                            if not z3.is_bool(x) and not z3.is_bool(y):
                                for d in (-1, 0, 1):
                                    add(x - y == d)
                                continue
                    e = enc._b(enc._ex(n, 1))
                except (Unsupported, z3.Z3Exception):
                    continue                       # uses a quantified variable or an earlier call
                add(e)
                add(z3.Not(e))
    if len(atoms) > limit:
        atoms = rng.sample(atoms, limit)
    sol = z3.Solver()
    sol.set('timeout', 3000)
    sol.add(*enc.dom)
    pts = []
    import time
    t0 = time.time()
    for atom in [z3.And(c, a) for c in contexts for a in atoms]:
        if _over(t0, SCOPE_BUDGET, f'request points of {", ".join(sets)}'):
            break
        for _ in range(per):
            in_alpha, fixes = [], []
            for a, sig, _ in fn.args:
                v = enc.x[(sig, 1)]
                if sig in fn.seqs:
                    in_alpha += [z3.Implies(j < v.ln, z3.Or(*[e == c for c in alpha[sig]])) for j, e in enumerate(v.el)]
                    fixes += [z3.Implies(j < v.ln, e == rng.choice(alpha[sig])) for j, e in enumerate(v.el)]
                else:
                    fixes.append(v == rng.choice(ints[a]))
            rng.shuffle(fixes)
            found = None
            for extra in (in_alpha + fixes[:len(fixes) // 2], in_alpha + fixes[:len(fixes) // 4], in_alpha, []):
                sol.push()
                sol.add(atom, *extra)
                try:
                    if sol.check() == z3.sat:
                        found = sol.model()
                finally:
                    sol.pop()
                if found is not None:
                    break
            if found is None:
                break
            pts.append(tuple(enc.value(found, sig, 1) for _, sig, _ in fn.args))
    return pts


def conforming_points(S, fn: Fn, sets: list[str], srcs=(), seed: int = 1, limit: int = 120) -> list[tuple]:
    key = ('conforming', tuple(sets), _src_key(S, fn, srcs, sets, seed), seed, limit)
    drawn = _drawn(S)
    if key not in drawn:
        drawn[key] = _conforming_points(S, fn, sets, srcs, seed, limit)
    return list(drawn[key])


def _conforming_points(S, fn: Fn, sets: list[str], srcs=(), seed: int = 1, limit: int = 120) -> list[tuple]:
    """Calls at the boundaries of computed values.  request_points leaves
    outputs free, so a rule about a computed value (a subtotal of at least
    $10) gives no input at its boundary.  Here every condition and comparison
    that mentions an output (as in request_points) is solved with the
    outputs obeying every property of one reading, in the integer encoding:
    the inputs then produce the boundary value.  A reading the encoding does
    not support, or that the solver cannot satisfy within its timeout, is
    skipped, and so is an atom it cannot decide."""
    import hashlib
    import z3
    from .lang import CHARS, TEMPORAL, parse
    rng = random.Random(seed)
    outs = set(fn.rets)
    alpha = {sig: alphabet(S, fn, a, sig, srcs, sets) for a, sig, _ in fn.args if sig in fn.seqs}
    ints = scope(S, fn, srcs, seed, small=True) if any(sig not in fn.seqs for _, sig, _ in fn.args) else {}
    pts = []
    for name in sets:
        try:
            enc = _IntSpec(S, [name], fn, 1)
        except (Unsupported, z3.Z3Exception, KeyError):
            continue
        spec = z3.And(*[h for (s_, _, i), h in enc.holds.items() if s_ == name and i == 1])
        atoms, keys = [], set()                    # (atom, its path condition)

        def add(e, pc):
            k = hashlib.md5((e.sexpr() + '|' + pc.sexpr()).encode()).hexdigest()
            if k not in keys:
                keys.add(k)
                atoms.append((e, pc))

        def path(ctx):
            out = []
            for c, pol in ctx:
                try:
                    b = enc._b(enc._ex(c, 1))
                except (Unsupported, z3.Z3Exception):
                    continue                       # a condition on a quantified variable: left out
                out.append(b if pol else z3.Not(b))
            return z3.And(*out) if out else z3.BoolVal(True)
        enc.defs = enc.all_defs[name]
        roots = []
        for it in S.mon(name).items.values():
            raw = getattr(it.args, 'raw', {}) or {}
            fs = {k: v for k, v in raw.items() if isinstance(v, str)}
            for k, v in fs.items():
                try:
                    roots.append((parse(v), ((parse(fs['trigger']), True),)
                                  if k == 'cond' and 'trigger' in fs and it.pattern == 'implies' else ()))
                except Exception:
                    pass
        st = _walk_state()
        for f, ctx0 in roots:
            for n, ctx in _walk_ctx(f, enc.defs, ctx0, st=st):
                if n.op == 'call' and n.val in TEMPORAL:
                    continue
                cond = (n.op == 'bin' and n.val in CMP_OPS | {'&&', '||', '->', '<->', 'in'}) or \
                    (n.op == 'un' and n.val == '!') or (n.op == 'call' and n.val in CHARS) or \
                    (n.op == 'quant' and n.val in ('all', 'any'))
                if not cond or not _inputs_used(n, enc.defs, outs):
                    continue
                try:
                    pc = path(ctx)
                    if n.op == 'bin' and n.val in CMP_OPS:
                        x, y = enc._ex(n.args[0], 1), enc._ex(n.args[1], 1)
                        if not isinstance(x, _ZSeq) and not isinstance(y, _ZSeq):
                            x, y = enc._sc(x), enc._sc(y)
                            if not z3.is_bool(x) and not z3.is_bool(y):
                                for d in (-1, 0, 1):
                                    add(x - y == d, pc)
                                continue
                    e = enc._b(enc._ex(n, 1))
                except (Unsupported, z3.Z3Exception):
                    continue
                add(e, pc)
                add(z3.Not(e), pc)
        if st['cut'] and f'computed boundaries of {name}' not in BUDGET_HIT:
            BUDGET_HIT.append(f'computed boundaries of {name}')     # uses of a definition were left out
        if len(atoms) > limit:
            atoms = rng.sample(atoms, limit)
        sol = z3.Solver()
        sol.set('timeout', 2000)
        sol.add(*enc.dom)
        sol.add(spec)
        if sol.check() != z3.sat:
            continue
        import time
        t0 = time.time()
        for atom, pc in atoms:
            if _over(t0, SCOPE_BUDGET, f'computed boundaries of {name}'):
                break
            in_alpha, fixes = [], []
            for a, sig, _ in fn.args:
                v = enc.x[(sig, 1)]
                if sig in fn.seqs:
                    in_alpha += [z3.Implies(j < v.ln, z3.Or(*[e == c for c in alpha[sig]])) for j, e in enumerate(v.el)]
                    fixes += [z3.Implies(j < v.ln, e == rng.choice(alpha[sig])) for j, e in enumerate(v.el)]
                else:
                    fixes.append(v == rng.choice(ints[a]))
            rng.shuffle(fixes)
            sol.push()
            sol.add(pc)                            # where the atom decides; without it if that is out of reach
            if sol.check() != z3.sat:
                sol.pop()
                sol.push()
            found = None
            for extra in ([], in_alpha + fixes[:len(fixes) // 2], in_alpha + fixes[:len(fixes) // 4], in_alpha):
                sol.push()
                sol.add(atom, *extra)
                try:
                    r = sol.check()
                    if r == z3.sat:
                        found = sol.model()
                finally:
                    sol.pop()
                if r != z3.sat and not extra:
                    break                          # no conforming call reaches it, or the solver cannot tell
                if found is not None and extra:
                    break
            sol.pop()
            if found is not None:
                pts.append(tuple(enc.value(found, sig, 1) for _, sig, _ in fn.args))
    return list(dict.fromkeys(pts))


def _weight(fn: Fn, c: tuple) -> tuple:
    """Simplicity of a call: total sequence length first, then values."""
    flat = []
    size = 0
    for x, (_, sig, _) in zip(c, fn.args):
        if sig in fn.seqs:
            cs = fn.codes(x)
            size += len(cs)
            flat += cs
        else:
            flat.append(int(x))
    return (size, max(flat, default=0), sum(flat), tuple(flat))


def _units(fn: Fn) -> list[list[int]]:
    """The positions of a call that change together: one argument, or the
    fields of a list of records (sequences of one length)."""
    pos = {sig: j for j, (_, sig, _) in enumerate(fn.args)}
    units, seen = [], set()
    for j, (_, sig, _) in enumerate(fn.args):
        if j not in seen:
            u = [pos[g] for g in fn.group(sig) if g in pos] if sig in fn.seqs else [j]
            seen |= set(u)
            units.append(u)
    return units


def _record_edits(fn: Fn, c: tuple, u: list[int], alpha: dict, rng: random.Random) -> list[tuple]:
    """Calls one edit from c in a list of records (positions u, one field
    each): a record deleted, repeated or swapped with the next, or a record
    drawn from the fields' alphabets inserted."""
    sigs = [fn.args[p][1] for p in u]
    cols = [fn.codes(c[p]) for p in u]
    m, n = len(cols[0]), fn.seqs[sigs[0]][1]

    def put(new):
        t = list(c)
        for p, sg, col in zip(u, sigs, new):
            t[p] = fn.value_of(sg, col)
        return tuple(t)
    out = [put([col[:k] + col[k + 1:] for col in cols]) for k in range(m)]
    out += [put([col[:k] + [col[k + 1], col[k]] + col[k + 2:] for col in cols]) for k in range(m - 1)]
    if m < n:
        out += [put([col[:k + 1] + col[k:] for col in cols]) for k in range(m)]
        recs = [tuple(rng.choice(alpha[sg]) for sg in sigs) for _ in range(12)]
        out += [put([col[:k] + [v] + col[k:] for col, v in zip(cols, r)]) for k in range(m + 1) for r in recs]
    return out


def neighbours(fn: Fn, c: tuple, alpha: dict, rng: random.Random, cap: int) -> list[tuple]:
    """Calls one edit from c: one slot of one sequence deleted, inserted or
    replaced (by alphabet elements), or one integer argument moved by one, or
    one boolean flipped; in a list of records, a record deleted, inserted,
    repeated or swapped, or one field of one record replaced.  At most cap of
    them, drawn at random."""
    out = []
    for j, (a, sig, kind) in enumerate(fn.args):
        x = c[j]
        if sig in fn.seqs and len(fn.group(sig)) > 1:
            u = next(u for u in _units(fn) if j in u)
            if j == u[0]:
                out += _record_edits(fn, c, u, alpha, rng)
            cs = fn.codes(x)
            edits = [cs[:k] + [e] + cs[k + 1:] for k in range(len(cs)) for e in alpha[sig] if e != cs[k]]
            vals = [fn.value_of(sig, e) for e in edits]
        elif sig in fn.seqs:
            n = fn.seqs[sig][1]
            cs = fn.codes(x)
            edits = [cs[:k] + cs[k + 1:] for k in range(len(cs))]
            if len(cs) < n:
                edits += [cs[:k] + [e] + cs[k:] for k in range(len(cs) + 1) for e in alpha[sig]]
            edits += [cs[:k] + [e] + cs[k + 1:] for k in range(len(cs)) for e in alpha[sig] if e != cs[k]]
            vals = [fn.value_of(sig, e) for e in edits]
        elif kind == 'bool' or fn.widths[sig] == 1:
            vals = [1 - int(x)]
        else:
            top = (1 << fn.widths[sig]) - 1
            vals = [v for v in (int(x) - 1, int(x) + 1) if 0 <= v <= top]
        out += [c[:j] + (v,) + c[j + 1:] for v in vals]
    return rng.sample(out, cap) if len(out) > cap else out


def tiny(S, fn: Fn, alpha: dict, ints: dict) -> list[tuple]:
    """All calls whose sequences have at most two slots, drawn from three
    alphabet elements of different kinds, with integer arguments at their
    smallest scope values."""
    def picks(sig):
        al = alpha[sig]
        return sorted({al[0], al[len(al) // 2], al[-1]})
    units = _units(fn)
    if all(len(u) == 1 for u in units):
        per = []
        for a, sig, kind in fn.args:
            if sig in fn.seqs:
                vals = [fn.value_of(sig, list(t)) for k in range(3) for t in itertools.product(picks(sig), repeat=k)]
            else:
                vals = ints[a][:2]
            per.append(vals)
        return list(itertools.product(*per))
    per = []
    for u in units:
        sigs = [fn.args[p][1] for p in u]
        if len(u) > 1:                           # a list of records: at most two, of up to nine kinds
            recs = list(itertools.product(*[picks(sg) for sg in sigs]))
            if len(recs) > 9:
                recs = random.Random(0).sample(recs, 9)
            vals = [tuple(fn.value_of(sg, [r[q] for r in rows]) for q, sg in enumerate(sigs))
                    for k in range(3) for rows in itertools.product(recs, repeat=k)]
        elif sigs[0] in fn.seqs:
            vals = [(fn.value_of(sigs[0], list(t)),) for k in range(3) for t in itertools.product(picks(sigs[0]), repeat=k)]
        else:
            vals = [(v,) for v in ints[fn.args[u[0]][0]][:2]]
        per.append(vals)
    out = []
    for combo in itertools.product(*per):
        c = [None] * len(fn.args)
        for u, vs in zip(units, combo):
            for p, v in zip(u, vs):
                c[p] = v
        out.append(tuple(c))
    return out


def seq_calls(S, fn: Fn, srcs=(), seed: int = 1, small: bool = False) -> list[tuple]:
    """The call sequence for a function of strings or lists: request points
    (all readings, see request_points), tiny calls, configured values and
    random calls, each followed by calls one edit away (see neighbours), so
    that a relational requirement compares calls that differ in one place."""
    rng = random.Random(seed)
    alpha = {sig: alphabet(S, fn, a, sig, srcs) for a, sig, _ in fn.args if sig in fn.seqs}
    ints = scope(S, fn, srcs, seed, small=True) if any(sig not in fn.seqs for _, sig, _ in fn.args) else {}
    base = request_points(S, fn, list(S.b.fsets), srcs, seed, per=1 if small else 3)
    base += tiny(S, fn, alpha, ints)
    near = len(base)                      # these get many neighbours, random calls a few
    empty = tuple(fn.default(x[1]) if x[1] in fn.seqs else 0 for x in fn.args)
    for a, sig, _ in fn.args:
        for v in fn.scope_cfg.get(a, {}).get('values', []) if sig in fn.seqs and len(fn.group(sig)) == 1 else []:
            for c in list(base[:4]) or [empty]:
                j = [x[0] for x in fn.args].index(a)
                base.append(c[:j] + (fn.value_of(sig, fn.codes(v)),) + c[j + 1:])
    for p in fn.shape:                     # a list of records: configured values, lists of dicts
        for v in fn.scope_cfg.get(p['name'], {}).get('values', []) if p['kind'] == 'records' else []:
            for c in list(base[:4]) or [empty]:
                t = list(c)
                for k, key, b in zip(p['pos'], p['keys'], p['bools']):
                    t[k] = fn.value_of(fn.args[k][1], [int(bool(r[key])) if b else int(r[key]) for r in v])
                base.append(tuple(t))
    units = _units(fn)
    for _ in range(100 if small else max([fn.scope_cfg.get(a, {}).get('random', 2000) for a, _, _ in fn.args])):
        c = [None] * len(fn.args)
        for u in units:
            a, sig, _ = fn.args[u[0]]
            if sig in fn.seqs:
                m = rng.randint(0, fn.seqs[sig][1])
                for k in u:
                    sg = fn.args[k][1]
                    c[k] = fn.value_of(sg, [rng.choice(alpha[sg]) for _ in range(m)])
            else:
                c[u[0]] = rng.choice(ints[a])
        base.append(tuple(c))
    rich = len(base)                      # points at computed boundaries: many neighbours too
    base += conforming_points(S, fn, list(S.b.fsets), srcs, seed)
    out, seen = [], set()
    for k, c in enumerate(base):
        cap = (6 if small else 40) if k < near or k >= rich else (1 if small else 4)
        for x in [c] + neighbours(fn, c, alpha, rng, cap):
            if x not in seen:
                seen.add(x)
                out.append(x)
    return out


# ----------------------------------------------------------------------------
# scope of an object: sequences of calls, each on a new object
# ----------------------------------------------------------------------------

def history(calls: list, i: int) -> list[int]:
    """The calls on the object that call i is made on, up to i."""
    j = i
    while j > 0 and calls[j - 1] is not None:
        j -= 1
    return list(range(j, i + 1))


def _pools(S, fn: Fn, srcs=()) -> tuple[dict, dict]:
    """Per argument, the values to draw from, or (for an argument with
    `steps`, such as a clock) the increments between consecutive calls."""
    pools, steps = {}, {}
    consts = constants(S, srcs)
    for a, sig, kind in fn.args:
        c = fn.scope_cfg.get(a, {})
        top = (1 << fn.widths[sig]) - 1
        if fn.methods and sig == fn.args[0][1]:
            pools[a] = sorted(m['op'] for m in fn.methods)
        elif 'steps' in c:
            steps[a] = sorted(set(c['steps']))
        elif kind == 'bool' or top == 1:
            pools[a] = [0, 1]
        else:
            vals = set(c.get('values', [])) or ({0, 1} | {x for x in consts if 0 <= x <= top})
            pools[a] = sorted(v for v in vals if 0 <= v <= top)
    return pools, steps


def _walk_seq(fn: Fn, pools: dict, steps: dict, rng: random.Random, n: int, picks=None) -> list[tuple]:
    seq, last = [], {}
    for k in range(n):
        c = []
        for a, sig, kind in fn.args:
            top = (1 << fn.widths[sig]) - 1
            if a in steps:
                st = picks[k][a] if picks else rng.choice(steps[a])
                v = min(top, max(0, (last.get(a, 0) + st) if k else max(0, st)))
                last[a] = v
            else:
                v = picks[k][a] if picks else rng.choice(pools[a])
            c.append(v)
        seq.append(fn.canon(tuple(c)))
    return seq


def _seq_neighbours(fn: Fn, seq: list[tuple], pools: dict, steps: dict, rng: random.Random, cap: int) -> list[list]:
    """Sequences one edit from seq: a call deleted or repeated, one argument of
    one call changed to another value of its pool, or a clock moved by one."""
    out = []
    for j in range(len(seq)):
        out.append(seq[:j] + seq[j + 1:])
        out.append(seq[:j + 1] + seq[j:])
        for x, (a, sig, kind) in enumerate(fn.args):
            top = (1 << fn.widths[sig]) - 1
            vals = [seq[j][x] - 1, seq[j][x] + 1] if a in steps else [v for v in pools[a] if v != seq[j][x]]
            for v in vals:
                if 0 <= v <= top:
                    out.append(seq[:j] + [fn.canon(seq[j][:x] + (v,) + seq[j][x + 1:])] + seq[j + 1:])
    out = [x for x in out if x]
    return rng.sample(out, cap) if len(out) > cap else out


def _cover_atoms(S, s: str, inputs: set) -> list[str]:
    """FCP-PL conditions to cover for reading s: every trigger, holding and
    failing; every pair of triggers; and, inside every trigger and with no
    constraint, every comparison of two integers at -1, 0 and +1 and every
    other condition holding and failing (as in request_points)."""
    from .lang import CHARS, TEMPORAL, parse, unparse
    defs = {n: parse(b) for n, b in (S.b.fsets[s].get('defs') or {}).items()}
    trig, atoms = [], []
    for it in S.mon(s).items.values():
        raw = getattr(it.args, 'raw', {}) or {}
        if it.role == 'property' and it.pattern == 'implies' and isinstance(raw.get('trigger'), str):
            trig.append(unparse(parse(raw['trigger'])))
    for f in _formulas(S, s):
        for n in _walk(f, defs):
            if n.op == 'call' and n.val in TEMPORAL:
                continue
            if n.op == 'quant' or any(x.op == 'quant' for x in _walk(n, {})):
                continue
            if n.op == 'bin' and n.val in ('<', '<=', '>', '>='):
                a, b = unparse(n.args[0]), unparse(n.args[1])
                atoms += [f'({a}) - ({b}) == {d}' for d in (-1, 0, 1)]
            elif (n.op == 'bin' and n.val in CMP_OPS | {'&&', '||'}) or (n.op == 'call' and n.val in CHARS):
                atoms += [unparse(n), f'!({unparse(n)})']
    trig = list(dict.fromkeys(trig))
    out = [t for x in trig for t in (x, f'!({x})')]
    out += [f'({x}) && ({y})' for x, y in itertools.combinations(trig, 2)]
    out += [f'({c}) && ({a})' for c in ['true'] + trig for a in dict.fromkeys(atoms)]
    return list(dict.fromkeys(out))


def _clash_atoms(S, s: str) -> list[str]:
    """Conditions under which two properties of reading s disagree about one
    call: both triggers hold, and the outputs meet the condition of the first
    and fail that of the second.  Only pairs whose conditions read a common
    output are kept.  Where the first condition fixes that output, no answer
    to the call meets both: a rule about the state now against a rule about
    what was answered before, for instance."""
    from .lang import parse, unparse
    defs = {n: parse(b) for n, b in (S.b.fsets[s].get('defs') or {}).items()}
    outs = {x.name for x in S.b.iface.signals if x.dir == 'out'}
    rows = []
    for it in S.mon(s).items.values():
        raw = getattr(it.args, 'raw', {}) or {}
        if it.role == 'property' and it.pattern == 'implies' and isinstance(raw.get('trigger'), str) \
                and isinstance(raw.get('cond'), str):
            t, c = parse(raw['trigger']), parse(raw['cond'])
            rows.append((unparse(t), unparse(c), {n.val for n in _walk(c, defs) if n.op == 'ref'} & outs))
    out = [f'({t1}) && ({t2}) && ({c1}) && !({c2})'
           for (t1, c1, r1), (t2, c2, r2) in itertools.permutations(rows, 2) if r1 & r2]
    return list(dict.fromkeys(out))


def request_sequences(S, fn: Fn, sets: list[str], limit: int = 400, clash: bool = False) -> list[list[tuple]]:
    """Sequences of calls drawn from the readings, for an object: for every
    condition of _cover_atoms, the shortest sequence of calls (bounded model
    checking on the spec-only model, cover_depth cycles) after which the
    condition holds, with every property of the reading met before that
    call.  The outputs on the way are those of a conforming implementation,
    so an implementation that conforms reaches the condition too.  clash:
    the conditions of _clash_atoms as well (the conflict search asks for
    them)."""
    from .lang import FcpError
    from .monitor import build_monitor
    out = []
    inputs = {sig for _, sig, _ in fn.args}
    for s in sets:
        atoms = []
        for a in _cover_atoms(S, s, inputs):
            fs = {'set': 'x', 'defs': S.b.fsets[s].get('defs'), 'ghosts': S.b.fsets[s].get('ghosts'),
                  'rigids': S.b.fsets[s].get('rigids'), 'scenarios': [{'id': 'X', 'req': 'R', 'cover': a}]}
            try:
                build_monitor(S.b.iface, fs, 'mon_probe')
                atoms.append(a)
            except FcpError:
                continue                       # a comparison of non-integers, for instance
        atoms = atoms[:limit]
        if clash:
            more = []
            for a in _clash_atoms(S, s):
                fs = {'set': 'x', 'defs': S.b.fsets[s].get('defs'), 'ghosts': S.b.fsets[s].get('ghosts'),
                      'rigids': S.b.fsets[s].get('rigids'), 'scenarios': [{'id': 'X', 'req': 'R', 'cover': a}]}
                try:
                    build_monitor(S.b.iface, fs, 'mon_probe')
                    more.append(a)
                except FcpError:
                    continue
            atoms = list(dict.fromkeys(atoms + more[:limit]))
        name = f'{s}__cover'
        fs = dict(S.b.fsets[s])
        fs['set'] = name
        fs['scenarios'] = list(fs.get('scenarios') or []) + [
            {'id': f'AT-{k}', 'req': next(iter(S.b.requirements)), 'cover': a} for k, a in enumerate(atoms)]
        S.b.fsets[name] = fs
        try:
            mon = S.mon(name)
            hb = S.free_hb([name])
            hb.no_later_reset()
            for a in S.assumptions(name):
                hb.assumes.append(f"mon_{a.out['aok']}")
            # a property over a large rigid range is met for the monitor's own
            # (free, constant) rigid value, the one the covered condition is about
            okall = ' && '.join(f"mon_{it.out.get('okd') or it.out['ok']}" for it in S.props(name)) or "1'b1"
            hb.regs.append("  reg fcp_hist = 1'b1;")
            hb.body.append(f'  always @(posedge clk) fcp_hist <= fcp_hist && ({hb.rst} || ({okall}));')
            for k in range(len(atoms)):
                hb.covers.append(f"!({hb.rst}) && fcp_hist && mon_{mon.items[f'AT-{k}'].out['cov']}")
            R = S.run([S.task(f'reqseq:{s}', 'cover', hb, [name], engine='cover')])
            res = R[f'reqseq:{s}']
        finally:
            del S.b.fsets[name]
            S._mons.pop(name, None)            # the next call may ask for other conditions
        rst, low = S.b.iface.reset.name, S.b.iface.reset.active_low
        for tr in res.traces or []:
            seq = []
            for st in tr:
                if int(st.get(rst) or 0) == (0 if low else 1):
                    seq = []
                    continue
                get = lambda p: int(st.get(p) or 0)  # noqa: E731
                seq.append(fn.canon(tuple(fn.decode(sig, get) for _, sig, _ in fn.args)))
            if seq:
                out.append(seq)
    return out


def object_calls(S, fn: Fn, srcs=(), seed: int = 1, small: bool = False, extra: Optional[list] = None) -> list:
    """The call sequence for a method of an object: sequences of calls, each
    on a new object (None in the list): every sequence of one or two calls
    over the two first values and the steps 0, 1, 10 and 60 (where
    configured), random walks (`sequences`, of `length` calls) with arguments
    from their pools and clocks advanced by their steps, extra sequences
    (from the request, see request_sequences), and every sequence one edit
    from those."""
    rng = random.Random(seed)
    pools, steps = _pools(S, fn, srcs)
    lo, hi = fn.scope_cfg.get('length', [1, 10])
    if extra is None:
        key = ('objects', tuple(S.b.fsets))
        drawn = _drawn(S)
        if key not in drawn:
            drawn[key] = request_sequences(S, fn, [x for x in S.b.fsets if not x.endswith('__cover')])
        extra = drawn[key]
    base: list[list] = [list(x) for x in extra]
    small_steps = {a: [x for x in v if x in (0, 1, 10, 60)] or v[:2] for a, v in steps.items()}
    alpha = []
    for c in itertools.product(*[(small_steps[a] if a in steps else pools[a] if fn.methods and k == 0 else pools[a][:2])
                                 for k, (a, _, _) in enumerate(fn.args)]):
        alpha.append({a: v for (a, _, _), v in zip(fn.args, c)})
    for n in (1, 2):
        for picks in itertools.product(alpha, repeat=n):
            base.append(_walk_seq(fn, pools, steps, rng, n, list(picks)))
    for _ in range(100 if small else fn.scope_cfg.get('sequences', 2000)):
        base.append(_walk_seq(fn, pools, steps, rng, rng.randint(lo, hi)))
    near = len(extra or [])
    out, seen = [], set()
    for k, sq in enumerate(base):
        cap = (8 if small else 40) if k < near else (1 if small else 3)
        for x in [sq] + _seq_neighbours(fn, sq, pools, steps, rng, cap):
            t = tuple(x)
            if t not in seen:
                seen.add(t)
                out.append(None)
                out.extend(x)
    return out


def seq_candidates(S, fn: Fn, sets: list[str], per: int = 2) -> list[tuple]:
    """Single calls to ask the spec-only model about, simplest first: the
    request points of these readings and the tiny calls."""
    alpha = {sig: alphabet(S, fn, a, sig, (), sets) for a, sig, _ in fn.args if sig in fn.seqs}
    ints = scope(S, fn, (), 1, small=True) if any(sig not in fn.seqs for _, sig, _ in fn.args) else {}
    pts = sorted(set(request_points(S, fn, sets, (), 1, per) + tiny(S, fn, alpha, ints)), key=lambda c: _weight(fn, c))
    seen = set(pts)
    more = [c for c in conforming_points(S, fn, sets) if c not in seen]
    return pts + sorted(more, key=lambda c: _weight(fn, c))


def seq_stimuli(S, fn: Fn, s: str) -> list[list[tuple]]:
    """Conflict candidates for a function of strings or lists: every
    candidate call alone, and, if reading s compares calls, followed by calls
    one edit away."""
    singles = seq_candidates(S, fn, [s])
    stims = [[c] for c in singles]
    if any(relational(it) for it in S.props(s)):
        rng = random.Random(1)
        alpha = {sig: alphabet(S, fn, a, sig, (), [s]) for a, sig, _ in fn.args if sig in fn.seqs}
        stims += [[c, nb] for c in singles for nb in neighbours(fn, c, alpha, rng, 6)]
    return stims


# ----------------------------------------------------------------------------
# conflicts in the prompt, at its own boundaries
# ----------------------------------------------------------------------------

class _Spec:
    """An incremental solver over k calls of the spec-only model of one or
    more readings (outputs free): the inputs and outputs of every call as
    named constants, per property one selector (the property holds at every
    call) and one literal per call (it holds at that call), with
    assume-guarantee semantics over each reading's own assumptions, as in
    triage.  Calls not fixed are free."""

    def __init__(self, S, sets, fn: Fn, k: int, pins: int = 0, extra_ins=(), extra_outs=()):
        import z3
        from . import smt as smtmod
        from .analyses import _rigid_focus
        from .monitor import PATTERNS
        sets = [sets] if isinstance(sets, str) else list(sets)
        self.z3, self.S, self.fn, self.k, self.sets = z3, S, fn, k, sets
        insts = [f'm{j}' for j in range(len(sets))]
        hb = S.free_hb(sets, insts)
        # A property over a rigid range too large to expand has no assumable
        # form.  It is assumed instead at `pins` valuations, one monitor
        # instance each, whose rigid values fix() sets from the calls (the
        # values of the signal its trigger binds the rigid to).  Fewer
        # assumptions than "for every value", so a conflict found is sound.
        self.pinned: dict[int, list[str]] = {}
        self.focus: dict[int, dict] = {}
        for j, st in enumerate(sets):
            free = [it for it in S.props(st) if 'okd' not in it.out]
            foc = _rigid_focus(free, S.b.fsets[st].get('defs'))
            if free and pins and foc and all(set(it.rigids) <= set(foc) for it in free):
                self.pinned[j] = [f'{insts[j]}p{p}' for p in range(pins)]
                self.focus[j] = foc
                for inst in self.pinned[j]:
                    hb.monitor(inst, S.mon(st))
        gen = S.gens(sets)
        gen['harness.v'] = hb.text(formal=False)
        model = smtmod.SmtModel(gen, [], hb.name)
        self.model = model
        self.rst = S.b.iface.reset.name
        # extra_ins / extra_outs: more ports to name, (port, width), free unless a caller constrains them
        self.ins = [p for _, sig, _ in fn.args for p in fn.ports(sig)] + \
            [p for sig in fn.base_signals for p in fn.ports(sig)] + list(extra_ins) + [(self.rst, 1)]
        self.outs = [p for sig in fn.rets + [fn.outcome] for p in fn.ports(sig)] + list(extra_outs)
        base = model.unroll(k)
        self.pin_vars: dict[str, tuple] = {}         # pinned instance + rigid -> (set, rigid, width, pin)
        for j, pinsts in self.pinned.items():
            mon = S.mon(sets[j])
            for pn, inst in enumerate(pinsts):
                for port, w, lo, hi in mon.rigid_ports:
                    rig = port[3:]
                    if rig not in self.focus[j]:
                        continue
                    name = f'{inst}_{port}'
                    base.append(f'(declare-fun pin_{name} () (_ BitVec {w}))')
                    base.append(f'(assert (= pin_{name} {model.sig(name, "s0")}))')
                    self.pin_vars[name] = (j, rig, w, pn)
        for i in range(k + 1):
            for p, sigs in (('in', self.ins), ('out', self.outs)):
                for n, w in sigs:
                    base.append(f'(declare-fun {p}_{n}_{i} () {"Bool" if w == 1 else f"(_ BitVec {w})"})')
                    base.append(f'(assert (= {p}_{n}_{i} {model.sig(n, f"s{i}")}))')
        ins = {n for n, _ in self.ins}

        def lit(v, w):
            return ('true' if v else 'false') if w == 1 else f'(_ bv{v} {w})'
        if fn.methods:                         # one method per call, its arguments only, also when free
            opn, opw = fn.ports(fn.args[0][1])[0]
            for i in range(1, k + 1):
                base.append('(assert (or ' + ' '.join(f'(= in_{opn}_{i} {lit(m["op"], opw)})'
                                                     for m in fn.methods) + '))')
                for m in fn.methods:
                    for j, (_, sg, _) in enumerate(fn.args):
                        if j and j not in m['pos']:
                            for pn, pw in fn.ports(sg):
                                base.append(f'(assert (=> (= in_{opn}_{i} {lit(m["op"], opw)}) '
                                            f'(= in_{pn}_{i} {lit(0, pw)})))')
        for sig in fn.args_sigs + fn.rets:     # the fields of a list of records: one length, also when free
            grp = fn.group(sig)
            if sig in fn.seqs and len(grp) > 1 and grp[0] == sig:
                p = 'in' if seq_len_port(sig) in ins else 'out'
                for g in grp[1:]:
                    for i in range(1, k + 1):
                        base.append(f'(assert (= {p}_{seq_len_port(sig)}_{i} {p}_{seq_len_port(g)}_{i}))')
        self.sels: dict[str, tuple[str, str]] = {}      # selector -> (set, item id)
        self.item_sel: dict[tuple[str, str], str] = {}
        # A property without a selector (see left_out): (set, item id) -> the
        # tag of its okf literals, or None where the model cannot ask it either.
        self.loose: dict[tuple[str, str], Optional[str]] = {}
        self.refuted = 0                # answers found that such a property rejected on replay
        self.undecided = 0              # queries the solver gave up on within its time limit
        for j, (s, inst) in enumerate(zip(sets, insts)):
            aok = [f"{inst}_{a.out['aok']}" for a in S.assumptions(s)]
            for i in range(k + 1):
                cur = '(and ' + ' '.join(model.is_true(a, f's{i}') for a in aok) + ')' if aok else 'true'
                base.append(f'(declare-fun ah{j}_{i} () Bool)')
                base.append(f'(assert (= ah{j}_{i} (and {f"ah{j}_{i - 1}" if i else "true"} {cur})))')
            for it in S.props(s):
                tag = f'{j}_' + re.sub(r'[^A-Za-z0-9_]', '_', it.id)
                if 'okd' in it.out:
                    wires = [f"{inst}_{it.out['okd']}"]
                elif j in self.pinned:
                    wires = [f"{pi}_{it.out['ok']}" for pi in self.pinned[j]]
                else:
                    # No form to assume.  It can still be asked: its ok output
                    # reads the rigid registers of the instance, constants that
                    # are free within their ranges (below), so "ok is false at
                    # call i" says that the rule is broken there for some value.
                    wire = f"{inst}_{it.out['ok']}"
                    asked = not PATTERNS[it.pattern].nondet and model.has(wire)
                    for i in range(k + 1) if asked else ():
                        base.append(f'(declare-fun okf_{tag}_{i} () Bool)')
                        base.append(f'(assert (= okf_{tag}_{i} (=> ah{j}_{i} {model.is_true(wire, f"s{i}")})))')
                    self.loose[(s, it.id)] = tag if asked else None
                    continue
                for i in range(k + 1):
                    now = ' '.join(model.is_true(w, f"s{i}") for w in wires)
                    base.append(f'(declare-fun ok_{tag}_{i} () Bool)')
                    base.append(f'(assert (= ok_{tag}_{i} (=> ah{j}_{i} (and {now}))))')
                base.append(f'(declare-fun sel_{tag} () Bool)')
                base.append(f'(assert (=> sel_{tag} (and ' + ' '.join(f'ok_{tag}_{i}' for i in range(k + 1)) + ')))')
                self.sels[f'sel_{tag}'] = (s, it.id)
                self.item_sel[(s, it.id)] = tag
            if any(x == s for x, _ in self.loose):      # the harness built here does not bound the registers
                for port, pw, lo, hi in S.mon(s).rigid_ports:
                    name = f'{inst}_{port}'
                    if pw > 1 and model.has(name):
                        t, mask = model.sig(name, 's0'), (1 << pw) - 1
                        base.append(f'(assert (and (bvsge {t} {lit(lo & mask, pw)}) (bvsle {t} {lit(hi & mask, pw)})))')
        # Don't-cares, one constant per call.  One that cites a condition on
        # the caller (a requirement of kind assumption) states the contract
        # call by call: a call that meets it is outside the contract, like a
        # call that breaks an assumption.  Any other is a freedom inside it.
        kinds = {r.id: r.kind for r in S.b.requirements.values()}
        self.outside: list[str] = []                         # the don't-cares that bound the contract
        self.frees: dict[str, list[tuple[str, str]]] = {}    # output -> (constant, item id) of its declared freedoms
        for j, (s, inst) in enumerate(zip(sets, insts)):
            for it in S.mon(s).items.values():
                wire = f'{inst}_{it.out.get("dc")}'
                if it.role != 'dontcare' or not model.has(wire):
                    continue
                tag = f'{j}_' + re.sub(r'[^A-Za-z0-9_]', '_', it.id)
                for i in range(k + 1):
                    base.append(f'(declare-fun dc_{tag}_{i} () Bool)')
                    base.append(f'(assert (= dc_{tag}_{i} {model.is_true(wire, f"s{i}")}))')
                if kinds.get(it.req) == 'assumption':
                    self.outside.append(f'dc_{tag}')
                else:
                    self.frees.setdefault(it.note, []).append((f'dc_{tag}', it.id))
        self.sol = model.solver(base)
        self.lits = [z3.Bool(x) for x in self.sels]

    def holds(self, s: str, iid: str, i: int):
        return self.z3.Bool(f'ok_{self.item_sel[(s, iid)]}_{i}')

    def var(self, p: str, n: str, w: int, i: int):
        return self.z3.Bool(f'{p}_{n}_{i}') if w == 1 else self.z3.BitVec(f'{p}_{n}_{i}', w)

    def fix(self, calls) -> list:
        low = self.S.b.iface.reset.active_low
        eqs = [self.var('in', self.rst, 1, 0) == (not low)]
        for i, c in enumerate(calls, 1):
            eqs.append(self.var('in', self.rst, 1, i) == low)
            for (_, sig, _), x in zip(self.fn.args, c):
                for n, v in self.fn.encode(sig, x).items():
                    w = self.fn.widths[n]
                    eqs.append(self.var('in', n, w, i) == (bool(v) if w == 1 else v))
        if self.fn.baseline:                    # the old code's answer to the same calls
            base = baseline_values(self.fn, list(calls))
            for i in range(1, len(calls) + 1):
                for sig in self.fn.base_signals:
                    w = self.fn.widths[sig]
                    v = int(base[sig][i - 1])
                    eqs.append(self.var('in', sig, w, i) == (bool(v) if w == 1 else v))
        eqs += self.pin_values(calls)
        return eqs

    def pin_values(self, calls) -> list:
        """The rigid values of the pinned instances: the distinct values, in
        these calls, of the signal each rigid is bound to, within the rigid's
        range (the first repeated if there are fewer values than pins; the
        lower end of the range if none is in it)."""
        z3, out = self.z3, []
        argpos = {sig: x for x, (_, sig, _) in enumerate(self.fn.args)}
        for name, (j, rig, w, p) in self.pin_vars.items():
            sig = self.focus[j][rig]
            if sig not in argpos:
                continue
            mon = self.S.mon(self.sets[j])
            lo, hi = next((l, h) for q, _, l, h in mon.rigid_ports if q == f'rg_{rig}')
            vals = list(dict.fromkeys(v for v in (int(c[argpos[sig]]) for c in calls) if lo <= v <= hi)) or [lo]
            v = vals[p] if p < len(vals) else vals[0]
            out.append(z3.BitVec(f'pin_{name}', w) == (v & ((1 << w) - 1)))
        return out

    def values(self, m, p: str, sigs: list[str], i: int) -> list:
        """The values of signals sigs at call i of model m, as the function sees them."""
        z3 = self.z3

        def get(n):
            w = self.fn.widths[n]
            v = m.eval(self.var(p, n, w, i), model_completion=True)
            return (1 if z3.is_true(v) else 0) if w == 1 else v.as_long()
        return [self.fn.decode(sig, get) for sig in sigs]

    def core(self, calls) -> Optional[list[str]]:
        """None if some output sequence meets every property on these calls,
        else a minimal set of conflicting properties.  The set is minimized by
        deletion over every property in name order, not from the solver's
        core, so it depends only on the calls."""
        z3, sol = self.z3, self.sol
        sol.push()
        sol.add(*self.fix(calls))
        try:
            if sol.check(*self.lits) != z3.unsat:
                return None
            keep = sorted(self.sels)
            i = 0
            while i < len(keep):
                trial = keep[:i] + keep[i + 1:]
                if sol.check(*[z3.Bool(t) for t in trial]) == z3.unsat:
                    keep = trial
                else:
                    i += 1
            return sorted(self.sels[x][1] for x in keep)
        finally:
            sol.pop()

    def muses(self, calls, cap: int = 64) -> list[list[str]]:
        """Every minimal set of properties that cannot hold together on these
        calls (MARCO: a map solver over the selectors proposes maximal seeds;
        an unsatisfiable seed is shrunk to a minimal set, a satisfiable one
        grown to a maximal one, and each is blocked).  At most cap sets."""
        z3, sol = self.z3, self.sol
        names = sorted(self.sels)
        m = {x: z3.Bool(f'map_{x}') for x in names}
        mp = z3.Solver()
        out = []
        sol.push()
        sol.add(*self.fix(calls))
        try:
            def unsat(sub):
                return sol.check(*[z3.Bool(x) for x in sub]) == z3.unsat
            while len(out) < cap and mp.check() == z3.sat:
                md = mp.model()
                seed = [x for x in names if not z3.is_false(md.eval(m[x], model_completion=False))]
                if unsat(seed):
                    keep, i = list(seed), 0
                    while i < len(keep):
                        trial = keep[:i] + keep[i + 1:]
                        if unsat(trial):
                            keep = trial
                        else:
                            i += 1
                    out.append(sorted(self.sels[x][1] for x in keep))
                    mp.add(z3.Or(*[z3.Not(m[x]) for x in keep]))
                else:
                    grow = list(seed)
                    for x in names:
                        if x not in grow and not unsat(grow + [x]):
                            grow.append(x)
                    mp.add(z3.Or(*[m[x] for x in names if x not in grow]))
        finally:
            sol.pop()
        return sorted(out)

    def separate(self, calls, acc: str, rej: str, req: str, context: bool = True) -> Optional[list[dict]]:
        """Outputs on these calls with which reading acc meets the properties
        of req (in context: every property), reading rej meets every property
        except those of req (in context; otherwise only the frame), and some
        property of req under rej fails at the last call.  None if there is
        none."""
        res = self._split(calls, acc, rej, req, context)
        return res['outs'] if res else None

    def _split(self, calls, acc: str, rej: str, req: str, context: bool) -> Optional[dict]:
        st, w = self.split_status(calls, acc, rej, req, context)
        return w

    def split_status(self, calls, acc: str, rej: str, req: str, context: bool) -> tuple[str, Optional[dict]]:
        """('none' | 'witness' | 'unknown', witness) for _split's question.

        A property without a selector (self.loose) cannot be assumed.  Among
        rej's properties of req it is asked for a value at which it fails,
        and where the model cannot ask it either, the answer is 'unknown'
        instead of 'none'.  Where such a property had to hold, the answers
        found are replayed on the compiled monitors over every value of its
        rigid variables; answers it rejects are no witness, and the result is
        'unknown' (counted in self.refuted): other answers may still exist."""
        z3, sol, S = self.z3, self.sol, self.S
        frame = S.b.frame_ids

        def on(s, iid):
            r = S.mon(s).items[iid].req
            if iid in frame:
                return True
            if s == acc:
                return context or r == req
            return context and r != req
        enabled = [z3.Bool(x) for x, (s, iid) in self.sels.items() if s in (acc, rej) and on(s, iid)]
        last = len(calls) if calls is not None else self.k
        cyc = [last] if calls is not None else range(1, self.k + 1)
        fails = [z3.Not(self.holds(rej, iid, i)) for (s, iid) in self.item_sel for i in cyc
                 if s == rej and S.mon(rej).items[iid].req == req and iid not in frame]
        mine = [tag for (s, iid), tag in self.loose.items()
                if s == rej and S.mon(rej).items[iid].req == req and iid not in frame]
        fails += [z3.Not(z3.Bool(f'okf_{tag}_{i}')) for tag in mine if tag for i in cyc]
        blind = None in mine                    # a property of rej's that cannot be asked: no 'none'
        unheld = list(dict.fromkeys(s for (s, iid) in self.loose if s in (acc, rej) and on(s, iid)))
        if not fails:
            return ('unknown' if blind else 'none'), None
        low = S.b.iface.reset.active_low
        fix = self.fix(calls) if calls is not None else \
            [self.var('in', self.rst, 1, 0) == (not low)] + \
            [self.var('in', self.rst, 1, i) == low for i in range(1, self.k + 1)]
        sol.push()
        sol.add(*fix, z3.Or(*fails))
        try:
            r = sol.check(*enabled)
            if r != z3.sat:                     # unsat without the properties left out is unsat with them
                if r != z3.unsat:
                    self.undecided += 1
                return ('none' if r == z3.unsat and not blind else 'unknown'), None
            m = sol.model()
            n = len(calls) if calls is not None else self.k
            args = [sig for _, sig, _ in self.fn.args]
            outs_s = self.fn.rets + [self.fn.outcome]
            ins = [tuple(self.values(m, 'in', args, i)) for i in range(1, n + 1)]
            outs = [dict(zip(outs_s, self.values(m, 'out', outs_s, i))) for i in range(1, n + 1)]
            w = {'calls': ins, 'outs': outs}
            bs = list(self.fn.base_signals)
            if bs:                              # the old code's answers in this model, for a replay
                w['base'] = [dict(zip(bs, self.values(m, 'in', bs, i))) for i in range(1, n + 1)]
            if unheld:
                rules = [(s, iid) for s in unheld for iid, it in S.mon(s).items.items()
                         if it.role == 'property' and on(s, iid)]
                if not _held(S, self.fn, w, rules):
                    self.refuted += 1
                    return 'unknown', None
            return 'witness', w
        finally:
            sol.pop()

    def _differs(self, sig: str, v, i: int = 1) -> object:
        """Output sig at call i is not v (for a sequence: in canonical form)."""
        z3, fn = self.z3, self.fn
        if sig not in fn.seqs:
            w = fn.widths[sig]
            o = self.var('out', sig, w, i)
            return o != (bool(v) if w == 1 else v)
        w, n = fn.seqs[sig]
        lp = seq_len_port(sig)
        lw = fn.widths[lp]
        raw = self.var('out', lp, lw, i)
        if lw == 1:
            raw = z3.If(raw, z3.BitVecVal(1, 2), z3.BitVecVal(0, 2))
            lw = 2
        ln = z3.If(z3.UGT(raw, z3.BitVecVal(n, lw)), z3.BitVecVal(n, lw), raw)
        cs = fn.codes(v)
        data = self.var('out', sig, fn.widths[sig], i)
        slot = [z3.Extract(k * w + w - 1, k * w, data) if fn.widths[sig] > 1 else data for k in range(len(cs))]
        return z3.Or(ln != z3.BitVecVal(len(cs), lw),
                     *[(x != (c == 1)) if fn.widths[sig] == 1 else (x != z3.BitVecVal(c, w)) for x, c in zip(slot, cs)])

    def inside(self, i: int) -> list:
        """The first i calls are inside the contract of every reading: each
        meets the assumptions, and none meets a don't-care that cites a
        condition on the caller."""
        z3 = self.z3
        return [z3.Bool(f'ah{j}_{i}') for j in range(len(self.sets))] + \
            [z3.Not(z3.Bool(f'{d}_{n}')) for d in self.outside for n in range(1, i + 1)]

    def declared(self, call, sig: str) -> list[str]:
        """The don't-cares (item ids) by which a reading frees output sig on
        purpose on the last of these calls: the freedoms it states itself."""
        z3, sol = self.z3, self.sol
        calls = call if isinstance(call, list) else [call]
        i, ids = len(calls), []
        for d, iid in self.frees.get(sig, []):
            sol.push()
            sol.add(*self.fix(calls), *self.inside(i), z3.Bool(f'{d}_{i}'))
            try:
                if sol.check(*self.lits) == z3.sat:
                    ids.append(iid)
            finally:
                sol.pop()
        return ids

    def two_values(self, call, sig: str, full: bool = False):
        """Two different values of output sig that both meet every property on
        this call, or None.  call may be a list of calls (an object's
        history): then the output of the last one.  full: also the outputs of
        every call in both answers, [(value, [outputs per call]), ...].
        The calls lie inside the contract of the readings (inside): what a
        reading says about a call it excludes is nothing, and that is not a
        choice the request left open.  Where there are two values, the pair
        returned is a small one (SMALL): a question is read by a person."""
        sol = self.sol
        calls = call if isinstance(call, list) else [call]
        i = len(calls)
        sol.push()
        sol.add(*self.fix(calls), *self.inside(i))
        try:
            found = self._two(sig, i, [])
            if found is None:
                return None
            for n, top in SMALL:
                bound = self._small(sig, i, n, top)
                if not bound:                  # nothing to bound: a truth value, or how the call ended
                    break
                less = self._two(sig, i, bound)
                if less is not None:
                    found = less
                    break
            return found if full else tuple(sorted(v for v, _ in found))
        finally:
            sol.pop()

    def _two(self, sig: str, i: int, bound: list):
        """[(value, [outputs per call]), ...]: two answers that differ in
        output sig at call i and meet bound, under what the solver holds; None
        if there are not two."""
        z3, sol = self.z3, self.sol
        outs_s = self.fn.rets + [self.fn.outcome]
        sol.push()
        sol.add(*bound)
        try:
            found = []
            for _ in range(2):
                if sol.check(*self.lits) != z3.sat:
                    return None
                m = sol.model()
                v = self.values(m, 'out', [sig], i)[0]
                found.append((v, [dict(zip(outs_s, self.values(m, 'out', outs_s, j))) for j in range(1, i + 1)]))
                sol.add(self._differs(sig, v, i))
            return found
        finally:
            sol.pop()

    def _small(self, sig: str, i: int, n: int, top: int) -> list:
        """Output sig at call i is small: a sequence of at most n elements,
        and a number (each element of a list) at most top.  Nothing for a
        truth value, for how the call ended, or where the bound excludes no
        value."""
        z3, fn = self.z3, self.fn
        if sig == fn.outcome or fn.kinds.get(sig) == 'bool':
            return []

        def low(x, w):
            return [z3.ULE(x, z3.BitVecVal(top, w))] if w > 1 and top < (1 << w) - 1 else []
        if sig not in fn.seqs:
            w = fn.widths[sig]
            return low(self.var('out', sig, w, i), w)
        w, cap = fn.seqs[sig]
        lp = seq_len_port(sig)
        lw = fn.widths[lp]
        raw = self.var('out', lp, lw, i)
        n = min(n, cap)
        if lw == 1:
            out = [z3.Not(raw)] if n == 0 else []
        else:
            out = [z3.ULE(raw, z3.BitVecVal(n, lw))] if n < (1 << lw) - 1 else []
        if fn.kinds.get(sig) != 'str' and fn.widths[sig] > 1:
            data = self.var('out', sig, fn.widths[sig], i)
            for k in range(n):
                out += low(z3.Extract(k * w + w - 1, k * w, data), w)
        return out


class Unsupported(Exception):
    pass


class _ZSeq:
    """A sequence in the integer encoding: its length and its slots (zero at
    and beyond the length).  lit: the elements, for a literal."""

    def __init__(self, ln, el, lit=None):
        self.ln, self.el, self.lit = ln, list(el), lit

    @property
    def cap(self) -> int:
        return len(self.el)


class _IntSpec:
    """Readings encoded directly in z3 integer arithmetic over k calls, from
    FCP-PL's exact integer semantics: signals are integers in their ranges,
    a string or list is a length and its slots, prev() refers to the previous
    call, and an item that looks back d calls holds by definition in the
    first d calls after reset.  Products that two readings write differently
    become the same polynomial here, while the bit-level model of the
    monitors turns them into a multiplier-equivalence problem.  Quantifiers
    are unrolled as in the compiler, and an item over rigid variables is the
    conjunction of its instances over their whole ranges (outside items, as in
    request points, a rigid is a free constant); over more than RIGID_CASES
    values it is Unsupported, not listed.  Only implies and invariant
    items are supported.  Every witness is confirmed on the compiled monitors
    before it is reported."""

    def __init__(self, S, sets: list[str], fn: Fn, k: int, items: bool = True, extra: tuple = (),
                 window: bool = False, free_rigids: bool = False):
        """window: the k calls are any k consecutive calls, not the first k
        after a reset.  The ghosts before the first of them and the registers
        of once, hist and since are then free variables (the state the window
        starts from), and the items are stated at the last call only.

        free_rigids: a rigid variable is one free constant in its range, in
        the items and in the ghosts, instead of an item being the conjunction
        of its instances.  An item is then false for some calls exactly if
        one of its instances is, so a proof (no calls and no rigid value make
        it false) is the same proof, and ghosts that follow one rigid value
        (the state of one customer) can be encoded at all."""
        import z3
        from .lang import parse
        self.z3, self.S, self.fn, self.k, self.sets = z3, S, fn, k, list(sets)
        self.parse = parse
        self.window, self.reg = window, {}
        self.free = free_rigids
        self.x, self.dom = {}, []
        # ghost state per reading: value at each call, the exact next value,
        # and whether the update stays in the ghost's range (as the monitor)
        self.g, self.gwf, self.gdecl = {}, {}, {}
        for n, w in extra:                     # more signals (an interface's calls and answers)
            for i in range(1, k + 1):
                if (n, i) not in self.x:
                    v = z3.Int(f'{n}_{i}')
                    self.dom.append(z3.And(v >= 0, v <= (1 << w) - 1))
                    self.x[(n, i)] = v
        # how a call ended is one of the codes that name an ending, also in a wider signal
        # (HarnessBuilder.canonical_outcome)
        ends = {fn.outcome} | ({fn.baseline['outcome']} if fn.baseline else set())
        for n in fn.signals + fn.base_signals:
            for i in range(1, k + 1):
                if n in fn.seqs:
                    w, cap = fn.seqs[n]
                    ln = z3.Int(f'{n}_{i}_len')
                    el = [z3.Int(f'{n}_{i}_{j}') for j in range(cap)]
                    self.dom += [ln >= 0, ln <= cap] + [z3.And(e >= 0, e <= (1 << w) - 1) for e in el] + \
                        [z3.Implies(ln <= j, e == 0) for j, e in enumerate(el)]
                    self.x[(n, i)] = _ZSeq(ln, el)
                else:
                    v = z3.Int(f'{n}_{i}')
                    self.dom.append(z3.And(v >= 0, v <= (fn.other_val if n in ends else (1 << fn.widths[n]) - 1)))
                    self.x[(n, i)] = v
        for n in fn.signals:                   # the fields of a list of records: one length
            for g in fn.group(n)[1:] if fn.group(n)[0] == n else []:
                self.dom += [self.x[(n, i)].ln == self.x[(g, i)].ln for i in range(1, k + 1) if (g, i) in self.x]
        for i in range(1, k + 1) if fn.methods else []:    # one method per call, its arguments only
            opv = self.x[(fn.args[0][1], i)]
            self.dom.append(z3.Or(*[opv == m['op'] for m in fn.methods]))
            for m in fn.methods:
                for j, (_, sg, _) in enumerate(fn.args):
                    if j and j not in m['pos']:
                        v = self.x[(sg, i)]
                        self.dom.append(z3.Implies(opv == m['op'], v.ln == 0 if isinstance(v, _ZSeq) else v == 0))
        self.holds: dict[tuple[str, str, int], object] = {}
        self.raw_holds: dict[tuple[str, str, int], object] = {}   # without the assumptions
        self._swept, self.sweep_stats, self.by_sweep = None, None, set()
        self.aholds: dict[tuple[str, str, int], object] = {}      # the assumptions' own verdicts
        self.defs: dict = {}
        self.all_defs = {s: {n: parse(b) for n, b in (S.b.fsets[s].get('defs') or {}).items()} for s in self.sets}
        from .lang import const_eval
        self.rigids = {s: {r['name']: tuple(const_eval(x, S.b.iface.params) for x in r['range'])
                           for r in (S.b.fsets[s].get('rigids') or [])} for s in self.sets}
        self.rig = {}
        for rs in self.rigids.values():
            for name, (lo, hi) in rs.items():
                if name not in self.rig:
                    self.rig[name] = z3.Int(f'rigid_{name}')
                    self.dom.append(z3.And(self.rig[name] >= lo, self.rig[name] <= hi))
        self.cur = None
        self._dv: dict = {}                    # per definitions in use: what was computed for them (_memo)
        if not items:
            return
        for s in self.sets:
            self.defs = self.all_defs[s]
            self.cur = s
            self._ghosts(s)
            its = [it for it in S.mon(s).items.values() if it.role in ('property', 'assumption')]
            for it in its:
                if it.pattern not in ('implies', 'invariant', 'next', 'after_reset'):
                    raise Unsupported(f'{s}:{it.id}: pattern {it.pattern}')
            ah = z3.BoolVal(True)
            assum = [it for it in its if it.role == 'assumption']
            for i in ([k] if window else range(1, k + 1)):
                for it in assum:
                    a = z3.And(self._item(it, i), self._wf(it, i))
                    self.aholds[(s, it.id, i)] = a
                    ah = z3.And(ah, a)
                for it in its:
                    if it.role == 'property':
                        v = z3.And(self._item(it, i), self._wf(it, i))
                        self.raw_holds[(s, it.id, i)] = v       # the monitor's own verdict, ungated
                        self.holds[(s, it.id, i)] = z3.Implies(ah, v)

    def _ghosts(self, s: str):
        """Ghost values of reading s at calls 1..k: init after the reset,
        then each call's next value truncated to the ghost's bits, as the
        compiled register; gwf says whether an update stays in the range
        (an item that depends on the ghost fails where it does not)."""
        z3 = self.z3
        from .lang import const_eval, signed_bits
        decl = {}
        for g in self.S.b.fsets[s].get('ghosts') or []:
            if 'range' in g:                   # a signed register of signed_bits(lo, hi), as compiled
                lo, hi = (const_eval(x, self.S.b.iface.params) for x in g['range'])
                nb, ranged = signed_bits(lo, hi), True
            else:
                nb = const_eval(g['width'], self.S.b.iface.params)
                lo, hi, ranged = 0, (1 << nb) - 1, False
            node = self.parse(g['next'])
            if not self.free and any(x.op == 'ref' and x.val in self.rigids.get(s, {})
                                     for x in _walk(node, self.defs)):
                raise Unsupported(f'ghost {g["name"]}: a ghost over rigid variables')
            decl[g['name']] = {'lo': lo, 'hi': hi, 'nb': nb, 'ranged': ranged, 'node': node,
                               'init': const_eval(g.get('init', 0), self.S.b.iface.params)}
        self.gdecl[s] = decl
        for name, d in decl.items():
            if self.window:                    # any value the register can hold
                v, half = z3.Int(f'ghost_{s}_{name}'), 1 << (d['nb'] - 1)
                self.dom.append(z3.And(v >= -half, v <= half - 1) if d['ranged'] else
                                z3.And(v >= 0, v <= (1 << d['nb']) - 1))
                self.g[(s, name, 1)] = v
            else:
                self.g[(s, name, 1)] = z3.IntVal(d['init'])
        for i in range(1, self.k + 1):
            nxt = {name: self._i(self._ex(d['node'], i)) for name, d in decl.items()}
            for name, d in decl.items():
                v = nxt[name]
                self.gwf[(s, name, i)] = z3.And(v >= d['lo'], v <= d['hi']) if d['ranged'] else z3.BoolVal(True)
                half = 1 << (d['nb'] - 1)          # truncated to the register: signed for a range, else unsigned
                self.g[(s, name, i + 1)] = (v + half) % (1 << d['nb']) - half if d['ranged'] else v % (1 << d['nb'])

    def _memo(self) -> dict:
        """What has been computed for the definitions in use (self.defs), by
        (what, reading, name, call, bindings).  A definition has one value at
        a call under given bindings, and a reading can chain definitions that
        each name the one before three times: computed at every use, eight
        of them are 3^8 computations.  A computation that raises is not
        kept."""
        m = self._dv.get(id(self.defs))
        if m is None or m[0] is not self.defs:
            m = self._dv[id(self.defs)] = (self.defs, {})      # holds the dict, so its id is not reused
        return m[1]

    def _depth(self, n) -> int:
        """How many earlier calls an expression looks at (prev, rose, ...)."""
        if n.op == 'ref' and n.val in self.defs:
            memo, key = self._memo(), ('depth', n.val)
            if key not in memo:
                memo[key] = self._depth(self.defs[n.val])
            return memo[key]
        if n.op == 'call' and n.val == 'prev':
            d = n.args[1].val if len(n.args) == 2 and n.args[1].op == 'num' else 1
            return d + self._depth(n.args[0])
        if n.op == 'call' and n.val in ('rose', 'fell', 'stable', 'changed'):
            return 1 + self._depth(n.args[0])
        if n.op == 'call' and n.val in ('once', 'hist', 'since'):
            return 0                           # defined from the reset on, by its own defaults
        return max([self._depth(a) for a in n.args], default=0)

    def _wf(self, it, i):
        """The range checks of the ghosts an item depends on, at call i."""
        z3 = self.z3
        decl = self.gdecl.get(self.cur) or {}
        if not decl:
            return z3.BoolVal(True)
        keys = ('trigger', 'cond') if it.pattern == 'implies' else ('cond',)
        names = {x.val for k in keys for x in _walk(self.parse(it.args.raw[k]), self.defs)
                 if x.op == 'ref' and x.val in decl}
        todo = list(names)
        while todo:
            g = todo.pop()
            for x in _walk(decl[g]['node'], self.defs):
                if x.op == 'ref' and x.val in decl and x.val not in names:
                    names.add(x.val)
                    todo.append(x.val)
        return z3.And(*[self.gwf[(self.cur, g, i)] for g in sorted(names)]) if names else z3.BoolVal(True)

    def _item(self, it, i):
        """An item's verdict at call i, gated as the monitor gates it: true in
        the first `depth` calls after the reset.  next: the trigger, armed
        once its own look-back is defined, latched for the following call;
        after_reset: the condition at the first call after the reset."""
        z3 = self.z3
        if i <= it.depth:
            return z3.BoolVal(True)
        raw = it.args.raw
        keys = ('trigger', 'cond') if it.pattern in ('implies', 'next') else ('cond',)
        nodes = [self.parse(raw[k]) for k in keys]
        if it.pattern == 'next' and not (i >= 2 and i - 1 > it.tdepth):
            return z3.BoolVal(True)            # no trigger was latched for this call
        if it.pattern == 'after_reset' and (i != 1 or self.window):
            return z3.BoolVal(True)            # (in a window, no call is the first after the reset)
        at = [i - 1, i] if it.pattern == 'next' else [i] * len(nodes)
        rs = self.rigids.get(self.cur, {})
        used = sorted({x.val for n in nodes for x in _walk(n, self.defs) if x.op == 'ref' and x.val in rs})
        if self.free:
            if used and it.role == 'assumption':
                raise Unsupported(f'{self.cur}:{it.id}: an assumption over rigid variables')
            used = []                          # one instance, at the free constants
        count = 1
        for r in used:
            count *= rs[r][1] - rs[r][0] + 1
        if count > RIGID_CASES:                # counted, not listed: 10^28 values have no list
            raise Unsupported(f'{self.cur}:{it.id}: a rule over {count} values of its rigid variables')
        out = []
        for vals in itertools.product(*[range(rs[r][0], rs[r][1] + 1) for r in used]):
            env = dict(zip(used, vals))
            ex = [self._b(self._ex(n, j, env)) for n, j in zip(nodes, at)]
            out.append(z3.Implies(ex[0], ex[1]) if len(ex) == 2 else ex[0])
        return z3.And(*out) if len(out) > 1 else out[0]

    def _b(self, e):
        e = self._sc(e)
        return e if self.z3.is_bool(e) else e != 0

    def _i(self, e):
        e = self._sc(e)
        return self.z3.If(e, 1, 0) if self.z3.is_bool(e) else e

    def _sc(self, e):
        """A one-character literal where a number is expected is its code."""
        if isinstance(e, _ZSeq):
            if e.lit is not None and len(e.lit) == 1:
                return self.z3.IntVal(e.lit[0])
            raise Unsupported('a sequence where a number is expected')
        return e

    def _lit(self, codes):
        z3 = self.z3
        codes = list(codes)
        return _ZSeq(z3.IntVal(len(codes)), [z3.IntVal(c) for c in codes] or [z3.IntVal(0)], lit=codes)

    def _elem(self, q: '_ZSeq', j: int):
        return q.el[j] if 0 <= j < q.cap else self.z3.IntVal(0)

    def _seq_eq(self, a: '_ZSeq', b: '_ZSeq'):
        z3 = self.z3
        return z3.And(a.ln == b.ln, *[self._elem(a, j) == self._elem(b, j) for j in range(min(a.cap, b.cap))])

    def _range(self, n, i, env) -> tuple[int, int]:
        """Static bounds of an integer expression (a quantifier's bound)."""
        if n.op == 'num':
            return n.val, n.val
        if n.op == 'ref':
            if n.val in env:
                return env[n.val], env[n.val]
            if n.val in self.defs:
                memo, key = self._memo(), ('range', self.cur, n.val, i, tuple(sorted(env.items())))
                if key not in memo:
                    memo[key] = self._range(self.defs[n.val], i, env)
                return memo[key]
            if n.val in self.fn.widths and n.val not in self.fn.seqs:
                return 0, (1 << self.fn.widths[n.val]) - 1
            if n.val in (self.gdecl.get(self.cur) or {}):
                d = self.gdecl[self.cur][n.val]
                return d['lo'], d['hi']
        if n.op == 'call' and n.val == 'len':
            return 0, self._ex(n.args[0], i, env).cap
        if n.op == 'bin' and n.val in ('+', '-', '*'):
            (a, b), (c, d) = self._range(n.args[0], i, env), self._range(n.args[1], i, env)
            if n.val == '+':
                return a + c, b + d
            if n.val == '-':
                return a - d, b - c
            ps = [a * c, a * d, b * c, b * d]
            return min(ps), max(ps)
        if n.op == 'call' and n.val in ('min', 'max'):
            rs = [self._range(x, i, env) for x in n.args]
            f = min if n.val == 'min' else max
            return f(r[0] for r in rs), f(r[1] for r in rs)
        if n.op == 'ite':
            (a, b), (c, d) = self._range(n.args[1], i, env), self._range(n.args[2], i, env)
            return min(a, c), max(b, d)
        raise Unsupported(f'no static bound for {n.op} {n.val}')

    def _ex(self, n, i, env=None):
        z3 = self.z3
        env = env or {}
        if n.op == 'num':
            return z3.IntVal(n.val)
        if n.op == 'str':
            return self._lit([ord(c) for c in n.val])
        if n.op == 'list':
            vals = [z3.simplify(self._i(self._ex(a, i, env))) for a in n.args]
            if not all(z3.is_int_value(v) for v in vals):
                raise Unsupported('list literal of non-constants')
            return self._lit([v.as_long() for v in vals])
        if n.op == 'ref':
            if n.val in env:
                return z3.IntVal(env[n.val])
            if n.val in self.defs:
                memo, key = self._memo(), ('ex', self.cur, n.val, i, tuple(sorted(env.items())))
                if key not in memo:
                    memo[key] = self._ex(self.defs[n.val], i, env)
                return memo[key]
            if (n.val, i) in self.x:
                return self.x[(n.val, i)]
            if (self.cur, n.val, i) in self.g:
                return self.g[(self.cur, n.val, i)]
            if n.val == 'rst_active':
                return z3.BoolVal(False)       # every modelled call is outside reset
            if n.val in self.rig:
                return self.rig[n.val]
            raise Unsupported(f'name {n.val}')
        if n.op == 'quant':
            var, bnd, body = n.args
            bound = self._i(self._ex(bnd, i, env))
            lo, top = self._range(bnd, i, env)
            terms = []
            for j in range(max(0, top)):
                g = z3.BoolVal(True) if j < lo else (j < bound)
                x = self._ex(body, i, {**env, var.val: j})
                terms.append((g, self._b(x) if n.val != 'sum' else self._i(x)))
            if n.val == 'all':
                return z3.And(*[z3.Implies(g, x) for g, x in terms]) if terms else z3.BoolVal(True)
            if n.val == 'any':
                return z3.Or(*[z3.And(g, x) for g, x in terms]) if terms else z3.BoolVal(False)
            if n.val == 'count':
                return z3.Sum(*[z3.If(z3.And(g, x), 1, 0) for g, x in terms]) if terms else z3.IntVal(0)
            return z3.Sum(*[z3.If(g, x, 0) for g, x in terms]) if terms else z3.IntVal(0)
        if n.op == 'un':
            a = self._ex(n.args[0], i, env)
            if n.val == '!':
                return z3.Not(self._b(a))
            if n.val == '-':
                return -self._i(a)
            raise Unsupported(f'operator {n.val}')
        if n.op == 'bin':
            a, b = self._ex(n.args[0], i, env), self._ex(n.args[1], i, env)
            o = n.val
            if o == 'in':
                if not isinstance(b, _ZSeq):
                    raise Unsupported('in on a non-sequence')
                x = self._i(a)
                if b.lit is not None:
                    return z3.Or(*[x == c for c in sorted(set(b.lit))]) if b.lit else z3.BoolVal(False)
                return z3.Or(*[z3.And(j < b.ln, x == e) for j, e in enumerate(b.el)])
            if o in ('==', '!=') and isinstance(a, _ZSeq) and isinstance(b, _ZSeq):
                eq = self._seq_eq(a, b)
                return eq if o == '==' else z3.Not(eq)
            if o in ('&&', '||', '->', '<->'):
                a, b = self._b(a), self._b(b)
                return {'&&': z3.And, '||': z3.Or, '->': z3.Implies, '<->': lambda x, y: x == y}[o](a, b)
            a, b = self._sc(a), self._sc(b)
            if o in ('==', '!='):
                if z3.is_bool(a) and z3.is_bool(b):
                    return (a == b) if o == '==' else (a != b)
                a, b = self._i(a), self._i(b)
                return (a == b) if o == '==' else (a != b)
            a, b = self._i(a), self._i(b)
            if o in ('<', '<=', '>', '>='):
                return {'<': a < b, '<=': a <= b, '>': a > b, '>=': a >= b}[o]
            if o in ('+', '-', '*'):
                return {'+': a + b, '-': a - b, '*': a * b}[o]
            if o == '%' and z3.is_int_value(z3.simplify(b)) and z3.simplify(b).as_long() > 0:
                return a % b                     # Euclidean, as floor modulo for a positive divisor
            raise Unsupported(f'operator {o}')
        if n.op == 'ite':
            c = self._b(self._ex(n.args[0], i, env))
            a, b = self._ex(n.args[1], i, env), self._ex(n.args[2], i, env)
            if isinstance(a, _ZSeq) and isinstance(b, _ZSeq):
                cap = max(a.cap, b.cap)
                return _ZSeq(z3.If(c, a.ln, b.ln), [z3.If(c, self._elem(a, j), self._elem(b, j)) for j in range(cap)])
            a, b = self._sc(a), self._sc(b)
            if z3.is_bool(a) and z3.is_bool(b):
                return z3.If(c, a, b)
            return z3.If(c, self._i(a), self._i(b))
        if n.op == 'idx':
            base = self._ex(n.args[0], i, env)
            if not isinstance(base, _ZSeq):
                raise Unsupported('bit-select')
            ix = z3.simplify(self._i(self._ex(n.args[1], i, env)))
            if z3.is_int_value(ix):
                return self._elem(base, ix.as_long())
            out = z3.IntVal(0)
            for j in range(base.cap - 1, -1, -1):
                out = z3.If(ix == j, base.el[j], out)
            return out
        if n.op == 'call':
            from .lang import CHARS
            if n.val == 'len':
                q = self._ex(n.args[0], i, env)
                if not isinstance(q, _ZSeq):
                    raise Unsupported('len of a non-sequence')
                return q.ln
            if n.val in CHARS:
                c = self._i(self._ex(n.args[0], i, env))
                return z3.Or(*[z3.And(c >= lo, c <= hi) for lo, hi in CHARS[n.val]])
            if n.val in ('lower', 'upper'):
                c = self._i(self._ex(n.args[0], i, env))
                lo, hi, d = (65, 90, 32) if n.val == 'lower' else (97, 122, -32)
                return z3.If(z3.And(c >= lo, c <= hi), c + d, c)
            if n.val in ('min', 'max'):
                vals = [self._i(self._ex(a, i, env)) for a in n.args]
                out = vals[0]
                for v in vals[1:]:
                    out = z3.If(v < out, v, out) if n.val == 'min' else z3.If(v > out, v, out)
                return out
            if n.val == 'prev':
                back = n.args[1].val if len(n.args) == 2 else 1
                if i - back < 1:
                    raise Unsupported('prev before the first call')
                return self._ex(n.args[0], i - back, env)
            if n.val in ('once', 'hist', 'since') and self.window:
                return self._reg(n, i, env)
            if n.val in ('once', 'hist', 'since'):
                # registers cleared by the reset: over the calls since it, each
                # counting only where its argument's look-back is defined
                def at(x, j, default):
                    return self._b(self._ex(x, j, env)) if self._depth(x) <= j - 1 else z3.BoolVal(default)
                if n.val == 'once':
                    return z3.Or(*[at(n.args[0], j, False) for j in range(1, i + 1)])
                if n.val == 'hist':
                    return z3.And(*[at(n.args[0], j, True) for j in range(1, i + 1)])
                out = z3.BoolVal(False)
                for j in range(1, i + 1):
                    out = z3.Or(at(n.args[1], j, False), z3.And(at(n.args[0], j, True), out))
                return out
            if n.val in ('stable', 'changed', 'rose', 'fell'):
                if i < 2:
                    raise Unsupported(f'{n.val} at the first call')
                now, before = self._ex(n.args[0], i, env), self._ex(n.args[0], i - 1, env)
                if n.val in ('stable', 'changed'):
                    if isinstance(now, _ZSeq):
                        eq = self._seq_eq(now, before)
                        return eq if n.val == 'stable' else z3.Not(eq)
                    if not (z3.is_bool(now) and z3.is_bool(before)):
                        now, before = self._i(now), self._i(before)
                    return (now == before) if n.val == 'stable' else (now != before)
                now, before = self._b(now), self._b(before)
                return z3.And(z3.Not(before), now) if n.val == 'rose' else z3.And(before, z3.Not(now))
            if n.val == 'zext':
                return self._ex(n.args[0], i, env)
        raise Unsupported(f'{n.op} {n.val}')

    def _reg(self, n, i: int, env=None):
        """Window mode: the register of a once, hist or since after call i of
        the window.  Before the window (i == 0) it is a free boolean, part of
        the state the window starts from; where the window does not reach
        back far enough for its argument, it is any value."""
        from .lang import unparse
        z3 = self.z3
        env = env or {}
        key = (self.cur, unparse(n), tuple(sorted(env.items())))
        r = self.reg.get(key)
        if r is None:
            ix = len(self.reg)
            r = self.reg[key] = {'node': n, 'env': dict(env), 'set': self.cur, 'ix': ix,
                                 'at': {0: z3.Bool(f'reg_{ix}')},
                                 'depth': max(self._depth(a) for a in n.args)}
        if i not in r['at']:
            if i <= r['depth']:
                r['at'][i] = z3.Bool(f'reg_{r["ix"]}_any{i}')
            else:
                before = self._reg(n, i - 1, env)
                a = [self._b(self._ex(x, i, env)) for x in n.args]
                r['at'][i] = z3.Or(before, a[0]) if n.val == 'once' else \
                    z3.And(before, a[0]) if n.val == 'hist' else z3.Or(a[1], z3.And(a[0], before))
        return r['at'][i]

    def reg_value(self, r: dict, i: int):
        """The register r (a record of some encoding's reg) after call i, in
        its own reading: in a window as _reg, else counted from the reset
        (after call 0 it holds what the reset left in it)."""
        cur, defs = self.cur, self.defs
        self.cur, self.defs = r['set'], self.all_defs[r['set']]
        try:
            return self._reg(r['node'], i, r['env']) if self.window else self._b(self._ex(r['node'], i, r['env']))
        finally:
            self.cur, self.defs = cur, defs

    def value(self, m, n: str, i: int):
        """The value of signal n at call i in model m, as the function sees it."""
        v = self.x[(n, i)]
        if isinstance(v, _ZSeq):
            ln = m.eval(v.ln, model_completion=True).as_long()
            return self.fn.value_of(n, [m.eval(e, model_completion=True).as_long() for e in v.el[:ln]])
        return m.eval(v, model_completion=True).as_long()

    def _signal_vars(self) -> list:
        """The variables of the signals of the k calls, in a fixed order."""
        out = []
        for i in range(1, self.k + 1):
            for n in self.fn.signals + self.fn.base_signals:
                v = self.x[(n, i)]
                out += [v.ln] + v.el if isinstance(v, _ZSeq) else [v]
        return out

    def _sweep_samples(self, consts: list, n: int = 256, seed: int = 1) -> list:
        """Values for every signal of k calls, in the order of _signal_vars,
        drawn from the constants the readings name and the ranges between
        them: each sample has a palette of up to three of these, so that some
        strings are all of one kind (digits, say) and some mix kinds.  What
        the function gives back is in part its argument, slot by slot.  The
        samples only decide which agreements are tried (fcp.sweep), so they
        need not be calls of the scope or behaviour any reading accepts."""
        fn, rng = self.fn, random.Random(seed)
        args = {sg for _, sg, _ in fn.args}

        def atoms(hi: int) -> list:
            cs = sorted({c for c in consts if c <= hi} | {0, hi})
            return [(c, c) for c in cs] + [(x, y) for x, y in zip(cs, cs[1:]) if y - x > 1]

        def draw(palette: list) -> int:
            lo, hi = rng.choice(palette)
            return rng.randint(lo, hi)
        rows = []
        for _ in range(n):
            row = []
            for _ in range(self.k):
                lens: dict = {}
                src: list = []
                for sig in fn.signals + fn.base_signals:
                    if sig in fn.seqs:
                        w, cap = fn.seqs[sig]
                        at = atoms((1 << w) - 1)
                        palette = rng.sample(at, min(len(at), rng.randint(1, 3)))
                        lead = fn.group(sig)[0]
                        if lead not in lens:
                            lens[lead] = rng.randint(0, cap) if sig in args or not src else \
                                min(cap, rng.choice([len(src), len(src), rng.randint(0, cap)]))
                        el = [draw(palette) for _ in range(lens[lead])]
                        if sig in args:
                            src = src or el
                        else:                                     # an answer: the argument, in part
                            el = [src[j] if j < len(src) and src[j] < (1 << w) and rng.random() < 0.5 else e
                                  for j, e in enumerate(el)]
                        row += [len(el)] + el + [0] * (cap - len(el))
                    else:
                        row.append(draw(atoms((1 << fn.widths[sig]) - 1)))
            rows.append(row)
        return rows

    def swept(self) -> dict:
        """self.holds with every agreement between their subterms that z3
        proves under the domain substituted (fcp.sweep), so each is equivalent
        to the item it stands for on every value of the signals.  Two readings
        that define one quantity in two ways (a checksum over the digits of a
        string) agree piece by piece, which z3 does not find out on the whole
        formula.  For a function over strings or lists whose items speak of
        signals only (no ghost, no rigid variable); {} otherwise."""
        if self._swept is None:
            self._swept = {}
            z3, fn = self.z3, self.fn
            if fn.has_seq and not self.window and self.holds:
                from . import sweep as SWP
                keys = list(self.holds)
                terms = [self.holds[q] for q in keys]
                inputs = self._signal_vars()
                ids = {v.get_id() for v in inputs}
                if all(SWP.variables(z3, t) <= ids for t in terms):
                    top = max(1 << w for w in list(fn.widths.values()) + [w for w, _ in fn.seqs.values()])
                    consts = sorted({e.as_long() for e in SWP.order(terms) if z3.is_int_value(e)
                                     and 0 <= e.as_long() < top})
                    new, self.sweep_stats = SWP.sweep(z3, terms, inputs, list(self.dom), self._sweep_samples(consts))
                    if 'skipped' not in self.sweep_stats:
                        self._swept = dict(zip(keys, new))
        return self._swept

    def split(self, acc: str, rej: str, req: str, context: bool, timeout: int = 60000) -> tuple[str, Optional[dict]]:
        """('none' | 'witness' | 'unknown', witness): as _Spec._split with every
        call free.  A question over strings or lists that z3 leaves open for
        QUICK milliseconds is asked again on the swept items (swept)."""
        z3, S = self.z3, self.S
        frame = S.b.frame_ids

        def on(s, iid):
            r = S.mon(s).items[iid].req
            if iid in frame:
                return True
            return (context or r == req) if s == acc else (context and r != req)

        def ask(holds: dict, ms: int):
            sol = z3.Solver()
            sol.set('timeout', ms)
            sol.add(*self.dom)
            sol.add(*[h for (s, iid, i), h in holds.items() if s in (acc, rej) and on(s, iid)])
            sol.add(z3.Or(*[z3.Not(h) for (s, iid, i), h in holds.items()
                            if s == rej and S.mon(rej).items[iid].req == req and iid not in frame]))
            return sol.check(), sol
        seq = self.fn.has_seq and not self.window
        r, sol = ask(self.holds, min(timeout, QUICK) if seq else timeout)
        if seq and r not in (z3.sat, z3.unsat):
            r, sol = ask(self.swept() or self.holds, timeout)
            if self._swept and r in (z3.sat, z3.unsat):
                self.by_sweep.add((acc, rej, req))
        if r == z3.unsat:
            return 'none', None
        if r != z3.sat:
            return 'unknown', None
        m = sol.model()
        calls = [tuple(self.value(m, x[1], i) for x in self.fn.args) for i in range(1, self.k + 1)]
        outs = [{n: self.value(m, n, i) for n in self.fn.rets + [self.fn.outcome]} for i in range(1, self.k + 1)]
        base = [{n: self.value(m, n, i) for n in self.fn.base_signals} for i in range(1, self.k + 1)]
        return 'witness', {'calls': calls, 'outs': outs, 'base': base}


def _trace(S, fn: Fn, w: dict) -> list[dict]:
    """The calls and answers of witness w as a trace for the compiled monitors (cycle 0 is the reset)."""
    rst, low = S.b.iface.reset.name, S.b.iface.reset.active_low
    tr = [{rst: 0 if low else 1}]
    for k, (c, o) in enumerate(zip(w['calls'], w['outs'])):
        st = {rst: 1 if low else 0}
        for sig, v in o.items():
            st.update(fn.encode(sig, v))
        for (_, sig, _), x in zip(fn.args, c):
            st.update(fn.encode(sig, x))
        for sig, v in (w.get('base') or [{}] * len(w['calls']))[k].items():
            st.update(fn.encode(sig, v))
        tr.append(st)
    return tr


def _held(S, fn: Fn, w: dict, rules: list[tuple[str, str]]) -> bool:
    """The properties (set, item id) hold on the calls and answers of w,
    replayed on the compiled monitors over every value of their rigid
    variables, for as long as the assumptions of their reading hold (as in
    _Spec).  False also where the values are too many to replay."""
    from . import rv
    tr = _trace(S, fn, w)
    for s in dict.fromkeys(s for s, _ in rules):
        try:
            r = rv.check(S, s, tr)
        except ValueError:
            return False
        items = S.mon(s).items
        broke = [c for i, c in r.items() if c is not None and items[i].role == 'assumption']
        upto = min(broke) if broke else len(tr)
        if any(r[i] is not None and r[i] < upto for x, i in rules if x == s):
            return False
    return True


def _confirm(S, fn: Fn, w: dict, acc: str, rej: str, req: str, context: bool, ran: Optional[list] = None) -> bool:
    """A witness of the integer encoding, simulated on the compiled monitors:
    rej's items of req fail, and every item that had to hold holds.  ran,
    when given, receives an entry once both replays have run, which tells a
    witness that the monitors refuted from one that could not be replayed."""
    tr = _trace(S, fn, w)
    frame = S.b.frame_ids
    try:
        ra, rr = _replay(S, acc, tr), _replay(S, rej, tr)
    except ValueError:                         # more rigid values than a replay lists: not confirmed
        return False
    if ran is not None:                        # both replays ran: False from here on is a refutation
        ran.append(True)
    must_a = [i for i in ra if i in frame or context or S.mon(acc).items[i].req == req]
    must_r = [i for i in rr if i in frame or (context and S.mon(rej).items[i].req != req)]
    fails = [i for i in rr if S.mon(rej).items[i].req == req and i not in frame]
    return (all(ra[i] is None for i in must_a if S.mon(acc).items[i].role == 'property') and
            all(rr[i] is None for i in must_r if S.mon(rej).items[i].role == 'property') and
            any(rr[i] is not None for i in fails))


def spot_check(S, spec: '_Spec', fn: Fn, acc: str, rej: str, req: str, n: int = 200, seed: int = 1) -> int:
    """Second engine for a comparison decided by the integer encoding: the
    bit-level model of the compiled monitors looks for a behaviour separating
    the readings on n single calls (the simplest ones and random ones of the
    small scope).  Returns how many calls it separates, which must be 0 when
    the readings were found equivalent."""
    if fn.has_seq:
        pts = seq_candidates(S, fn, [acc, rej])
    else:
        vals = scope(S, fn, small=True)
        names = [a for a, _, _ in fn.args]
        pts = sorted(itertools.product(*[vals[x] for x in names]), key=_simple)
    rng = random.Random(seed)
    sample = pts[:n // 2] + rng.sample(pts, min(len(pts), n - n // 2))
    prefetch(fn, sample)
    return sum(spec.separate([c], acc, rej, req) is not None for c in sample)


def window_len(S, s: str, fn: Fn) -> int:
    """How many consecutive calls a one-step check of reading s has to see:
    one more than the furthest that an item, or the argument of a once, hist
    or since, looks back."""
    e = _IntSpec(S, [s], fn, 1, items=False)
    e.defs, e.cur = e.all_defs[s], s
    back, nodes = 0, []
    for it in S.mon(s).items.values():
        if it.role not in ('property', 'assumption'):
            continue
        back = max(back, it.depth, it.tdepth + 1 if it.pattern == 'next' else 0)
        nodes += [e.parse(v) for k, v in it.args.raw.items() if k in ('trigger', 'cond')]
    nodes += [e.parse(g['next']) for g in S.b.fsets[s].get('ghosts') or []]
    for n in nodes:
        for x in _walk(n, e.defs):
            if x.op == 'call' and x.val in ('once', 'hist', 'since'):
                back = max(back, max(e._depth(a) for a in x.args))
            back = max(back, e._depth(x))
    return back + 1


def horizon(S, sets: list[str]) -> tuple[int, bool]:
    """(k, exact): k is one more than the largest number of earlier calls any
    item of these readings looks at; a rule over two consecutive calls
    (next) looks at the call of its trigger, one call before the furthest
    that the trigger looks back, as `window_len` counts it.  exact: no ghost
    state, no unbounded history operator and only same-cycle patterns, so
    every violation of an item shows on k consecutive calls ending at the
    violation."""
    d, exact = 0, True
    for s in sets:
        fs = S.b.fsets[s]
        text = json.dumps(fs.get('defs') or {})
        exact = exact and not fs.get('ghosts')
        for it in S.mon(s).items.values():
            if it.role not in ('property', 'assumption'):
                continue
            d = max(d, it.depth, it.tdepth + 1 if it.pattern == 'next' else 0)
            exact = exact and it.pattern in ('implies', 'invariant')
            text += it.formula
        exact = exact and not re.search(r'\b(once|hist|since)\s*\(', text)
    return d + 1, exact


def scope_separation(S, spec: '_Spec', fn: Fn, acc: str, rej: str, req: str, context: bool,
                     n: int = 200, seed: int = 1, over=None) -> dict:
    """Evidence for a comparison the solver could not decide: the bit-level
    model is asked, call by call with the input fixed, for outputs on which acc
    meets req and rej does not (the simplest candidate calls first, then
    random calls of the small scope).  Fixing the input makes each query
    easy.  over: asked before every call, and the search ends when it says
    so.  It also ends after UNCONFIRMED calls whose answers a property that
    the model cannot assume rejected on replay ('refuted' then counts them):
    more calls would cost a replay each and decide nothing.  Returns
    {'calls': checked, 'witness': lines of the first separating call or
    None}, with 'undecided' where the solver gave up on some calls."""
    if fn.has_seq:
        pts = seq_candidates(S, fn, [acc, rej])
        rng = random.Random(seed)
        more = [c for c in calls_for(S, fn, small=True) if c not in set(pts)]
        pts = pts[:n // 2] + rng.sample(more, min(len(more), n - min(len(pts), n // 2)))
    else:
        vals = scope(S, fn, small=True)
        names = [x for x, _, _ in fn.args]
        allp = sorted(itertools.product(*[vals[x] for x in names]), key=_simple)
        rng = random.Random(seed)
        pts = allp[:n // 2] + rng.sample(allp, min(len(allp), n - n // 2))
    prefetch(fn, pts)
    r0, u0 = spec.refuted, spec.undecided

    def done(calls: int, witness) -> dict:
        res = {'calls': calls, 'witness': witness}
        if spec.refuted > r0:
            res['refuted'] = spec.refuted - r0
        if spec.undecided > u0:
            res['undecided'] = spec.undecided - u0
        return res
    for k, c in enumerate(pts, 1):
        if over is not None and over():
            return done(k - 1, None)
        outs = spec.separate([c], acc, rej, req, context)
        if outs:
            return done(k, {'calls': [list(c)], 'lines': [line(fn, c, outs[0])]})
        if spec.refuted - r0 >= UNCONFIRMED:
            return done(k, None)
    return done(len(pts), None)


def _bit_job(job: tuple) -> tuple:
    """One direction of a comparison decided on the bit-level model of the
    compiled monitors, in a process of its own (z3 is not thread-safe and the
    model takes gigabytes)."""
    root, sets, k, acc, rej, req, context, timeout = job
    from . import smt as smtmod
    from .analyses import Session
    S = Session(root, sets=sets)
    fn = function(S)
    try:
        spec = _Spec(S, sets, fn, k)
    except smtmod.TranslationFailed as e:     # it translated in the process that asks: not here, beside the others
        return 'untranslated', str(e)
    spec.sol.set('timeout', int(timeout * 1000))
    st, w = spec.split_status(None, acc, rej, req, context)
    return st, w


QUICK = 2000                # milliseconds a question over strings or lists gets before its items are swept
BIT_TIMEOUT = 1800          # seconds per direction left open by the integer encoding
BIT_JOBS = int(os.environ.get("FCP_BIT_JOBS", 6))   # bit-level processes at once (about 2.8 GB each)
BIT_LEAST = 20              # seconds: with less than this left for a direction, no bit-level process starts


def compare(S, a: str, b: str, fn: Fn, context: bool = False, only: Optional[set] = None,
            spec: Optional['_Spec'] = None, bit_timeout: Optional[float] = None,
            plain: Optional[dict] = None) -> dict:
    """Readings a and b compared requirement by requirement on the spec-only
    model of a function, by z3 over k calls (see horizon).  When the bound
    is exact, the relation is decided: no disagreement of any length exists
    if none exists on k calls.  context: a disagreement must also meet every
    other requirement under both readings.  A direction the integer encoding
    cannot decide is first checked call by call on the scope
    (scope_separation), where a separating call is a witness, and then
    decided on the bit-level model of the monitors, in parallel processes,
    within bit_timeout seconds (BIT_TIMEOUT; 0 skips it).  What neither
    decides stays UNKNOWN, and so does every direction not reached within
    COMPARE_BUDGET seconds, which BUDGET_HIT then names.  Where the bit-level
    model of the two readings does not translate (smt.TranslationFailed),
    what the integer encoding left open stays UNKNOWN too, and BUDGET_HIT
    says why.  The bit-level model cannot assume a property over more rigid
    values than the monitor expands (left_out): a call it finds where such a
    property had to hold counts only if the property accepts it on replay
    over every value, and where a requirement stays UNKNOWN beside such
    properties, BUDGET_HIT names them.  plain: what this comparison returned
    without context.  A direction's question in context is its question
    without context with constraints added (the other requirements, under
    both readings), so a direction with no disagreement without context has
    none in context.  It is not asked again, whatever time is left, and the
    record lists it under 'carried'; a record with both directions carried
    names the engine that decided them there.  A plain record that is
    UNKNOWN because one direction did not end still closes the other
    (closed).  Same result format as Session.compare: each record of a
    requirement that both readings state has 'status', what was found in
    each direction ('none', 'witness' or 'unknown')."""
    import time
    from . import smt as smtmod
    t0, what = time.time(), f'the comparison of {a} and {b}' + (', in context' if context else '')

    def carried(r: str) -> tuple:
        """The directions of r that the comparison without context closed."""
        return closed((plain or {}).get(r)) if context else ()

    def over() -> bool:
        return _over(t0, COMPARE_BUDGET, what)

    def left(most: float) -> float:
        return most if COMPARE_BUDGET is None else min(most, max(0.0, COMPARE_BUDGET - (time.time() - t0)))

    def untold(e):
        msg = f'{what}: {e}; what the integer encoding left open stays undecided'
        if msg not in BUDGET_HIT:
            BUDGET_HIT.append(msg)

    k, exact = horizon(S, [a, b])
    frame = S.b.frame_ids
    ra = {it.req for it in S.props(a) if it.req and it.id not in frame}
    rb = {it.req for it in S.props(b) if it.req and it.id not in frame}
    try:
        enc = _IntSpec(S, [a, b], fn, k)
    except Unsupported:
        enc = None
    out, pending, open_jobs = {}, {}, []
    refuted: set = set()                     # requirements with a call of an encoding that the monitors refuted
    untranslated = False                     # the bit-level model of the two readings did not translate
    for r in sorted(ra | rb):
        if only is not None and r not in only:
            continue
        if r not in ra or r not in rb:
            out[r] = {'relation': 'ONLY-B' if r not in ra else 'ONLY-A', 'k': k, 'exact': exact}
            continue
        res, scoped = {}, {}
        for key, acc, rej in (('witness_a_not_b', a, b), ('witness_b_not_a', b, a)):
            if key in carried(r):                    # no disagreement without context: none in context
                res[key] = ('none', None)
                continue
            if over():                               # out of time: undecided, and BUDGET_HIT says so
                res[key] = ('unknown', None)
                continue
            st, w = enc.split(acc, rej, r, context, max(1000, int(left(60) * 1000))) if enc else ('unknown', None)
            ran: list = []
            if st == 'witness' and not _confirm(S, fn, w, acc, rej, r, context, ran):
                st, w = 'unknown', None              # the encodings disagree: report nothing as decided
                if ran:                              # replayed and refuted, not merely too many values to replay
                    refuted.add(r)
            if st == 'unknown' and not untranslated and not over():
                if spec is None:
                    try:
                        spec = _Spec(S, [a, b], fn, max(1, k))
                    except smtmod.TranslationFailed as e:
                        untranslated = True
                        untold(e)
                        res[key] = (st, w)
                        continue
                if COMPARE_BUDGET is not None:       # a query gets a minute at most, and no more than is left
                    spec.sol.set('timeout', int(max(1.0, left(60)) * 1000))
                sc = scope_separation(S, spec, fn, acc, rej, r, context, over=over)
                if COMPARE_BUDGET is not None:
                    spec.sol.set('timeout', NO_TIMEOUT)
                scoped[key] = {'calls': sc['calls'], 'separated': sc['witness'] is not None}
                scoped[key].update({x: sc[x] for x in ('refuted', 'undecided') if x in sc})
                if sc['witness']:
                    st, w = 'witness', None
                    res[key] = (st, w)
                    scoped[key]['lines'] = sc['witness']['lines']
                    scoped[key]['calls_'] = sc['witness']['calls']
                    continue
                open_jobs.append((r, key, acc, rej))
            res[key] = (st, w)
        pending[r] = (res, scoped)
    bt = BIT_TIMEOUT if bit_timeout is None else bit_timeout
    given = bt
    if open_jobs and bt and COMPARE_BUDGET is not None:    # the time that is left, shared among the jobs
        share = left(bt * len(open_jobs)) * min(BIT_JOBS, len(open_jobs)) / len(open_jobs)
        bt = min(bt, share) if share >= BIT_LEAST else 0
        if not bt and what not in BUDGET_HIT:
            BUDGET_HIT.append(what)
    bit: dict[tuple, tuple] = {}
    if open_jobs and bt:
        import multiprocessing
        from concurrent.futures import ProcessPoolExecutor
        jobs = [(S.b.root, [a, b], max(1, k), acc, rej, r, context, bt) for r, key, acc, rej in open_jobs]
        with ProcessPoolExecutor(max_workers=min(BIT_JOBS, len(jobs)),
                                 mp_context=multiprocessing.get_context('spawn')) as ex:
            for (r, key, acc, rej), (st, w) in zip(open_jobs, ex.map(_bit_job, jobs)):
                if st == 'untranslated':
                    untold(w)
                    st, w = 'unknown', None
                ran = []
                if st == 'witness' and not _confirm(S, fn, w, acc, rej, r, context, ran):
                    st, w = 'unknown', None
                    if ran:
                        refuted.add(r)
                bit[(r, key)] = (st, w)
                if st == 'unknown' and bt < given and what not in BUDGET_HIT:
                    BUDGET_HIT.append(what)
    cannot = False                           # a requirement stays undecided beside a property left out
    for r, (res, scoped) in pending.items():
        for (rr, key), sw in bit.items():
            if rr == r:
                res[key] = sw
                scoped.setdefault(key, {})['bit'] = sw[0]
        sts = (res['witness_a_not_b'][0], res['witness_b_not_a'][0])
        enc_used = enc
        if 'unknown' in sts:
            rel = 'UNKNOWN'
            cannot = cannot or any(context or S.mon(s).items[i].req == r for s in (a, b) for i in left_out(S, s))
        else:
            rel = {('none', 'none'): 'EQUIVALENT', ('none', 'witness'): 'A-STRONGER',
                   ('witness', 'none'): 'A-WEAKER', ('witness', 'witness'): 'INCOMPARABLE'}[sts]
        rec = {'relation': rel, 'status': dict(zip(WITNESSES, sts)), 'k': k, 'exact': exact,
               'engine': ('z3-int' if enc_used else '') + ('+bit' if any(v.get('bit') for v in scoped.values()) else '')
               + ('+sweep' if enc and {(a, b, r), (b, a, r)} & enc.by_sweep else '')}
        if r in refuted:                             # what an encoding closed on r is not handed on (closed)
            rec['refuted'] = True
        if carried(r):
            rec['carried'] = list(carried(r))
            if len(rec['carried']) == 2:             # nothing was asked here
                rec['engine'] = plain[r].get('engine', '')
        for key, (st, w) in res.items():
            if w:
                rec[key] = {'calls': [list(c) for c in w['calls']],
                            'lines': [line(fn, c, o) for c, o in zip(w['calls'], w['outs'])]}
            elif key in scoped and scoped[key].get('lines'):
                rec[key] = {'calls': scoped[key].pop('calls_'), 'lines': scoped[key]['lines'], 'from': 'scope'}
        if scoped:
            rec['scope_check'] = scoped
        out[r] = rec
    if cannot:
        msg = f'{what}: it cannot assume ' + ', '.join(dict.fromkeys(left_out(S, a) + left_out(S, b))) + \
            ' (rules stated for every value of a variable), and requirements they bear on stay undecided'
        if msg not in BUDGET_HIT:
            BUDGET_HIT.append(msg)
    return out


UNCONFIRMED = 8                            # calls with unconfirmed answers after which a search gives up (choices, scope_separation)
NO_TIMEOUT = 4294967295                    # z3's value for a solver without a time limit


def left_out(S, s: str) -> list[str]:
    """The properties of reading s that _Spec cannot assume unless they are
    pinned: those over more rigid values than the monitor expands.  The
    searches for conflicts and open choices leave them out and confirm what
    they find by replay; a comparison asks them of the reading that rejects
    and replays what it finds against them (_Spec.split_status)."""
    return [it.id for it in S.props(s) if 'okd' not in it.out]


def _conforms(S, s: str, fn: Fn, calls, outs) -> bool:
    """These answers (the outputs of every call) meet every property of
    reading s on the compiled monitor, over every rigid value.  False also
    where the rigid values are too many to replay: not confirmed."""
    from . import rv
    rst, low = S.b.iface.reset.name, S.b.iface.reset.active_low
    base = baseline_values(fn, list(calls)) if fn.baseline else {}
    tr = [{rst: 0 if low else 1}]
    for j, (c, o) in enumerate(zip(calls, outs)):
        st = {rst: 1 if low else 0}
        for sig, v in o.items():
            st.update(fn.encode(sig, v))
        for (_, sig, _), x in zip(fn.args, c):
            st.update(fn.encode(sig, x))
        for sig in (fn.base_signals if fn.baseline else []):
            st[sig] = int(base[sig][j])
        tr.append(st)
    try:
        r = rv.check(S, s, tr)
    except ValueError:
        return False
    return all(r[i] is None for i, it in S.mon(s).items.items() if it.role == 'property' and i in r)


def choices(S, s: str, fn: Fn, signals: list[str]) -> dict:
    """For every output in signals (the ones determinacy found open), the
    simplest single call on which reading s allows two different values:
    the question the prompt leaves to whoever writes the code.  Only calls
    inside the reading's contract (_Spec.inside).  'declared' names the
    don't-cares by which the reading frees the output there on purpose:
    still a choice of the request, which the reader took to be meant.

    The solver leaves out the properties over a large rigid range
    ('left_out'), and fewer rules can only add allowed answers.  With such
    properties, both answers are therefore confirmed on the compiled monitor
    over every rigid value before the choice is kept; 'rejected' counts the
    calls whose answers were not, and after UNCONFIRMED of them an output is
    given up: an open choice of such a reading can be missed, never invented."""
    # a sequence's length port stands for the sequence
    signals = list(dict.fromkeys(next((q for q in fn.seqs if seq_len_port(q) == x), x) for x in signals))
    signals = [x for x in signals if x in fn.rets + [fn.outcome]]
    if fn.stateful:
        return object_choices(S, s, fn, signals)
    spec = _Spec(S, s, fn, 1)
    if fn.has_seq:
        cands = seq_candidates(S, fn, [s], per=1)
    else:
        vals = scope(S, fn, small=True)
        names = [a for a, _, _ in fn.args]
        cands = sorted(itertools.product(*[vals[n] for n in names]), key=lambda c: (max(c), sum(c), c))
    found, checked = {}, 0
    loose = left_out(S, s)
    missed = {x: 0 for x in signals}           # per output, the calls whose answers were not confirmed
    prefetch(fn, cands)
    for c in cands:
        todo = [x for x in signals if x not in found and missed[x] < UNCONFIRMED]
        if not todo:
            break
        checked += 1
        for sig in todo:
            w = spec.two_values(c, sig, full=True)
            if not w:
                continue
            if loose and not all(_conforms(S, s, fn, [c], outs) for _, outs in w):
                missed[sig] += 1
                continue
            v = tuple(sorted(x for x, _ in w))
            found[sig] = {'call': call_text(fn, c), 'args': list(c), 'values': list(v),
                          'shown': [fn.shown(sig, x) for x in v], 'ending': sig == fn.outcome,
                          'declared': spec.declared(c, sig)}
    out = {'open': found, 'checked': checked}
    if loose:
        out.update(left_out=loose, rejected=sum(missed.values()))
    return out


def _smaller(fn: Fn, c: tuple, alpha: dict, ints: dict) -> list[tuple]:
    """Calls simpler than c by one step: a record (or a slot of a sequence)
    deleted, or one element or integer replaced by a smaller value of its
    alphabet or scope."""
    out = []
    for u in _units(fn):
        sigs = [fn.args[p][1] for p in u]
        if sigs[0] in fn.seqs:
            cols = [fn.codes(c[p]) for p in u]
            for k in range(len(cols[0])):            # delete item k of every field
                t = list(c)
                for p, sg, col in zip(u, sigs, cols):
                    t[p] = fn.value_of(sg, col[:k] + col[k + 1:])
                out.append(tuple(t))
            for p, sg, col in zip(u, sigs, cols):
                for k, x in enumerate(col):
                    for v in [v for v in alpha[sg] if v < x]:
                        t = list(c)
                        t[p] = fn.value_of(sg, col[:k] + [v] + col[k + 1:])
                        out.append(tuple(t))
        else:
            p = u[0]
            for v in [v for v in ints.get(fn.args[p][0], [0, 1]) if v < int(c[p])]:
                out.append(fn.canon(c[:p] + (v,) + c[p + 1:]))
    return out


def shrink(spec: '_Spec', fn: Fn, stim: list, alpha: dict, ints: dict, budget: int = 600,
           drop: bool = False) -> list:
    """A simpler stimulus that still conflicts: each call replaced, while
    one exists, by the simplest call one step smaller (see _smaller) on
    which the stimulus still conflicts; with drop (a sequence of calls on an
    object), calls are also deleted."""
    best, tries, improved = list(stim), 0, True
    while improved and tries < budget:
        improved = False
        for j in range(len(best)) if drop and len(best) > 1 else []:
            tries += 1
            trial = best[:j] + best[j + 1:]
            if spec.core(trial) is not None:
                best, improved = trial, True
                break
        if improved:
            continue
        for j in range(len(best)):
            w = _weight(fn, best[j])
            for c in sorted(set(_smaller(fn, best[j], alpha, ints)), key=lambda x: _weight(fn, x)):
                if _weight(fn, c) >= w:
                    continue
                tries += 1
                trial = best[:j] + [c] + best[j + 1:]
                if spec.core(trial) is not None:
                    best, improved = trial, True
                    break
                if tries >= budget:
                    break
    return best


def conflicts(S, s: str, fn: Fn, limit: int = 4) -> dict:
    """Boundary conflicts of reading s, before any code exists: pairs of calls
    built from the integer constants of the readings and the prompt (each
    constant and its neighbours, in both orders, with the other arguments at
    their own constants), on which no output pair meets every property.

    A conflict found is sound: it is an unrealizability witness, since no
    implementation can answer both calls.  Finding none says only that no
    candidate pair is a conflict.  For each stimulus every minimal
    conflicting set is listed; a requirement is in conflict if it belongs to
    one of them, whichever the solver would have reported.  The search complements the trigger-situation
    and forcing analyses, whose candidates are arbitrary or whose search does
    not converge over wide arithmetic inputs."""
    import time
    t0 = time.time()
    if fn.stateful:
        return object_conflicts(S, s, fn, limit)
    spec = _Spec(S, s, fn, 2)
    order = seq_stimuli(S, fn, s) if fn.has_seq else [list(p) for p in boundary_pairs(S, fn, [s])]
    if fn.baseline:                             # the old code's answers, all in one run
        baseline_values(fn, [c for cand in order for c in cand])
    found: dict[tuple, dict] = {}
    checked = 0
    alpha = ints = None
    for cand in order:
        if _over(t0, CONFLICT_BUDGET, f'conflict search of {s}'):
            break
        checked += 1
        cr = spec.core(cand)
        if cr is None:
            continue
        stim = cand
        for single in ([[c] for c in cand] if len(cand) > 1 else []):    # one call already conflicting?
            if spec.core(single) is not None:
                stim, cr = single, spec.core(single)
                break
        if any(cr in f['muses'] for f in found.values()):
            continue                            # a minimal set already listed: the same conflict elsewhere
        if fn.has_seq:                          # the simplest stimulus with this conflict
            if alpha is None:
                alpha = {sig: alphabet(S, fn, a, sig, (), [s]) for a, sig, _ in fn.args if sig in fn.seqs}
                ints = scope(S, fn, (), 1, small=True) if any(sig not in fn.seqs for _, sig, _ in fn.args) else {}
            stim = shrink(spec, fn, stim, alpha, ints)
            cr = spec.core(stim)
        ms = spec.muses(stim)
        key = tuple(tuple(x) for x in ms)
        if key in found:
            continue
        found[key] = {'core': cr, 'muses': ms,
                      'calls': [[list(x) if isinstance(x, tuple) else x for x in c] for c in stim],
                      'stimulus': [call_text(fn, c) for c in stim],
                      'reqs': sorted({S.mon(s).items[i].req for mu in ms for i in mu if S.mon(s).items[i].req})}
        if len(found) >= limit:
            break
    return {'conflicts': list(found.values()), 'candidates': len(order), 'checked': checked,
            'seconds': round(time.time() - t0, 2)}


def object_choices(S, s: str, fn: Fn, signals: list[str], pins: int = 3) -> dict:
    """choices() for an object: the shortest request sequence after which
    reading s allows two different answers to the last call."""
    seqs = sorted({tuple(x) for x in request_sequences(S, fn, [s])},
                  key=lambda t: (len(t), tuple(_weight(fn, c) for c in t)))
    found, checked = {}, 0
    if not seqs or not signals:
        return {'open': found, 'checked': checked}
    # Pinned rules are fewer assumptions, which can only add allowed answers:
    # every open choice is therefore confirmed on the compiled monitors, over
    # every rigid value, for both answers.
    spec = _Spec(S, s, fn, max(len(t) for t in seqs), pins=pins)
    rejected = 0
    for t in seqs:
        todo = [x for x in signals if x not in found]
        if not todo:
            break
        checked += 1
        for sig in todo:
            w = spec.two_values(list(t), sig, full=True)
            if not w:
                continue
            if not all(_conforms(S, s, fn, t, outs) for _, outs in w):
                rejected += 1
                continue
            v = tuple(sorted(x for x, _ in w))
            found[sig] = {'call': '; '.join(call_text(fn, c) for c in t), 'args': [list(c) for c in t],
                          'values': list(v), 'shown': [fn.shown(sig, x) for x in v], 'sequence': True,
                          'ending': sig == fn.outcome, 'declared': spec.declared(list(t), sig)}
    return {'open': found, 'checked': checked, 'rejected': rejected}


def object_separation(S, fn: Fn, a: str, b: str, req: str, context: bool, n: int = 150, pins: int = 3) -> dict:
    """Evidence for an object comparison the proof engine left open: request
    sequences of both readings (and their neighbours), shortest first, are
    asked one by one on the bit-level model, with rules over a large rigid
    range pinned at the values each sequence names, for outputs on which one
    reading meets req and the other does not.  A witness found is replayed on
    the compiled monitors over every rigid value before it is kept."""
    rng = random.Random(1)
    pools, steps = _pools(S, fn)
    seqs = request_sequences(S, fn, [a, b])
    cands = sorted({tuple(x) for sq in seqs for x in [sq] + _seq_neighbours(fn, sq, pools, steps, rng, 4)},
                   key=lambda t: (len(t), tuple(_weight(fn, c) for c in t)))[:n]
    out = {'calls': len(cands)}
    if not cands:
        return out
    spec = _Spec(S, [a, b], fn, max(len(t) for t in cands), pins=pins)
    for key, acc, rej in (('a_not_b', a, b), ('b_not_a', b, a)):
        for t in cands:
            st, w = spec.split_status(list(t), acc, rej, req, context)
            if st == 'witness' and _confirm(S, fn, w, acc, rej, req, context):
                out[key] = {'calls': [list(c) for c in w['calls']],
                            'lines': [line(fn, c, o) for c, o in zip(w['calls'], w['outs'])], 'sequence': True}
                break
    return out


def object_conflicts(S, s: str, fn: Fn, limit: int = 4, pins: int = 3) -> dict:
    """conflicts() for an object: the candidates are sequences of calls on a
    new object, the request sequences of reading s (with those after which
    two of its properties disagree about a call) and every sequence one edit
    from them, shortest first.  A property over a large rigid range is
    assumed at the values its trigger binds the rigid to in the sequence
    (pins).  Each conflict is shown as its shortest conflicting prefix."""
    import time
    t0 = time.time()
    rng = random.Random(1)
    pools, steps = _pools(S, fn)
    seqs = request_sequences(S, fn, [s], clash=True)
    cands = {tuple(x) for sq in seqs for x in [sq] + _seq_neighbours(fn, sq, pools, steps, rng, 8)}
    order = sorted(cands, key=lambda t: (len(t), tuple(_weight(fn, c) for c in t)))
    if not order:
        return {'conflicts': [], 'candidates': 0, 'checked': 0, 'seconds': round(time.time() - t0, 2)}
    spec = _Spec(S, s, fn, max(len(t) for t in order), pins=pins)
    found: dict[tuple, dict] = {}
    checked = 0
    for cand in order:
        if _over(t0, CONFLICT_BUDGET, f'conflict search of {s}'):
            break
        checked += 1
        cand = list(cand)
        if spec.core(cand) is None:
            continue
        stim = next(cand[:n] for n in range(1, len(cand) + 1) if spec.core(cand[:n]) is not None)
        cr = spec.core(stim)
        if any(cr in f['muses'] for f in found.values()):
            continue
        # the simplest stimulus with this conflict: calls dropped, values lowered within their pools
        # (an argument with steps, a clock, keeps its values)
        stim = shrink(spec, fn, stim, {}, dict(pools, **{a: [] for a in steps}), drop=True)
        ms = spec.muses(stim)
        key = tuple(tuple(x) for x in ms)
        if key in found:
            continue
        found[key] = {'core': ms[0] if ms else [], 'muses': ms, 'calls': [list(c) for c in stim],
                      'stimulus': [call_text(fn, c) for c in stim],
                      'reqs': sorted({S.mon(s).items[i].req for mu in ms for i in mu if S.mon(s).items[i].req})}
        if len(found) >= limit:
            break
    return {'conflicts': list(found.values()), 'candidates': len(order), 'checked': checked,
            'seconds': round(time.time() - t0, 2)}


def _simple(p) -> tuple:
    flat = tuple(x for c in p for x in c) if isinstance(p[0], tuple) else p
    return (max(flat), sum(flat), flat)


def boundary_pairs(S, fn: Fn, sets: Optional[list[str]] = None) -> list[tuple[tuple, tuple]]:
    """Pairs of calls at the boundaries of the readings and the prompt:
    consecutive boundary values of one argument (each constant and its
    neighbours, in both orders) with the other arguments at their constants.
    Simplest first."""
    consts = constants(S, sets=sets)
    vals, others = {}, {}
    for arg, sig, kind in fn.args:
        top = (1 << fn.widths[sig]) - 1
        if kind == 'bool' or top == 1:
            vals[arg] = others[arg] = [0, 1]
            continue
        vals[arg] = sorted({0, top} | {x for c in consts for x in (c - 1, c, c + 1) if 0 <= x <= top})
        others[arg] = sorted({0, 1, top} | {c for c in consts if 0 <= c <= top})
    names = [a for a, _, _ in fn.args]
    cands = set()
    for d, name in enumerate(names):
        line = vals[name]
        pairs = list(zip(line, line[1:]))
        pairs += [(b, a) for a, b in pairs]
        for combo in itertools.product(*[others[n] for n in names if n != name]):
            for x1, x2 in pairs:
                cands.add((combo[:d] + (x1,) + combo[d:], combo[:d] + (x2,) + combo[d:]))
    return sorted(cands, key=_simple)


def line(fn: Fn, c: tuple, outs: dict) -> str:
    """'checkout(5, 0, True) -> (4, 0)' from a call and its output values."""
    k = int(outs.get(fn.outcome, 0))
    if k == 0:
        return f'{call_text(fn, c)} -> {ret_text(fn, [outs.get(s, fn.default(s)) for s in fn.rets], c)}'
    return f'{call_text(fn, c)} -> {fn.outcome_name(k)}'


def separating(S, spec: '_Spec', fn: Fn, acc: str, rej: str, req: str, limit: int = 2000) -> Optional[dict]:
    """The simplest calls on which reading acc accepts a behaviour that reading
    rej rejects for requirement req, while both readings agree on everything
    else: single calls of the small scope first, then boundary pairs."""
    if fn.has_seq:
        singles, pairs = seq_candidates(S, fn, [acc, rej])[:limit], []
    else:
        vals = scope(S, fn, small=True)
        names = [a for a, _, _ in fn.args]
        singles = sorted(itertools.product(*[vals[n] for n in names]), key=_simple)[:limit]
        pairs = [list(p) for p in boundary_pairs(S, fn)[:limit]]
    prefetch(fn, singles)
    prefetch(fn, pairs)
    r0 = spec.refuted
    for calls in [[c] for c in singles] + pairs:
        outs = spec.separate(calls, acc, rej, req)
        if outs:
            return {'calls': [list(c) for c in calls], 'lines': [line(fn, c, o) for c, o in zip(calls, outs)]}
        if spec.refuted - r0 >= UNCONFIRMED:       # a property the model cannot assume keeps rejecting the answers
            break
    return None


# ----------------------------------------------------------------------------
# the calls a comparison shows, run again
# ----------------------------------------------------------------------------

REPLAY_SECONDS = 600                           # for the calls of one comparison, replayed one after the other
REPLAY_CASES = 65536                           # values of a reading's rigid variables that one replay runs through
WITNESSES = ('witness_a_not_b', 'witness_b_not_a')


def closed(rec) -> tuple:
    """The directions in which a comparison's record of a requirement found
    no disagreement: 'witness_a_not_b' where no run exists that the first
    reading accepts and the second rejects, 'witness_b_not_a' the other way
    round.  Read from the record's status per direction, so that a record
    that is UNKNOWN because one direction did not end, or because its call
    was not shown, still closes the other; a record without one (written
    before the status was) is read by its relation.  A record with no
    context to compare in (NO-CONTEXT) closes nothing, and neither does a
    requirement that only one reading states.  A record on which the
    monitors refuted a call that an encoding found ('refuted') closes
    nothing: the encoding and the monitors disagreed on that requirement."""
    if not isinstance(rec, dict) or rec.get('relation') == 'NO-CONTEXT' or rec.get('refuted'):
        return ()
    st = rec.get('status')
    if isinstance(st, dict):
        return tuple(k for k in WITNESSES if st.get(k) == 'none')
    return {'EQUIVALENT': WITNESSES, 'A-STRONGER': WITNESSES[:1], 'A-WEAKER': WITNESSES[1:]}.get(rec.get('relation'), ())


def carried_over(plain: dict) -> dict:
    """The records that `compare` in context, handed `plain` (what it
    returned without context), writes without asking anything.  For a
    requirement with no disagreement in either direction without context:
    EQUIVALENT with both directions under 'carried' (context only adds
    constraints: see compare).  For a requirement that only one reading
    states: the record it has without context.  Every other requirement is
    left out: what the comparison in context finds on it is not known
    before it ran.  For a review whose comparison in context did not end
    (review.check).  Not for the bounded comparison (Session.compare), which
    in context answers NO-CONTEXT where no behavior meets the other
    requirements, also on a requirement that is equal without context."""
    out = {}
    for r, x in plain.items():
        if r == '<assumptions>' or not isinstance(x, dict):
            continue
        if x.get('relation') in ('ONLY-A', 'ONLY-B'):
            out[r] = dict(x)
        elif len(closed(x)) == 2:
            out[r] = {'relation': 'EQUIVALENT', 'status': dict.fromkeys(WITNESSES, 'none'),
                      **{k: x[k] for k in ('k', 'exact') if k in x},
                      'engine': x.get('engine', ''), 'carried': list(WITNESSES)}
    return out


def printable(fn: Fn) -> bool:
    """A line printed by `line` names the whole call and every output: a
    function of plain values.  Not an object (the calls of a sequence share
    its state), not records or nested values, and not a change (the line
    does not carry what the baseline answered)."""
    return not (fn.stateful or fn.methods or fn.structured or fn.base_signals)


def shows(recs: dict) -> bool:
    """A record of a comparison shows a call."""
    return any(isinstance(x, dict) and isinstance(x.get(k), dict) and x[k].get('lines')
               for x in recs.values() for k in WITNESSES)


def _value(fn: Fn, sig: str, x):
    """x as the value of signal sig, in the form the engine holds it.
    ValueError where the signal cannot carry it."""
    k = fn.kinds.get(sig)
    if sig in fn.seqs:
        w, n = fn.seqs[sig]
        ok = (isinstance(x, str) if k == 'str' else isinstance(x, list) and all(type(e) is int for e in x)) \
            and len(x) <= n and all(0 <= c < (1 << w) for c in fn.codes(x))
        v = tuple(x) if ok and k != 'str' else x
    elif k == 'bool':
        ok, v = isinstance(x, bool), x
    else:
        ok, v = type(x) is int and 0 <= x < (1 << fn.widths[sig]), x
    if not ok:
        raise ValueError(f'{x!r} is no value of {sig}')
    return v


def read_line(fn: Fn, text: str) -> tuple[tuple, dict, bool]:
    """The call and the outputs that a line printed by `line` names, for a
    printable function: (call, outs, valued).  An ending in words (an
    exception, no answer, a value that does not fit) is read as the code the
    words name, with every output at its default, and valued is False: the
    line does not say what the outputs carried.  ValueError where the text is
    no such line; a code that names no ending is none."""
    head, sep = fn.name + '(', ') -> '
    if not text.startswith(head):
        raise ValueError(f'no call of {fn.name}')
    at, args = text.find(sep, len(head) - 1), None
    while at >= 0:                             # the first split whose left side reads as the arguments
        inner = text[len(head):at]
        try:
            args = ast.literal_eval(f'({inner},)') if inner.strip() else ()
        except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
            args = None
        if isinstance(args, tuple) and len(args) == len(fn.args):
            break
        at, args = text.find(sep, at + 1), None
    if args is None:
        raise ValueError(f'no call of {fn.name} with {len(fn.args)} arguments')
    call = tuple(_value(fn, sig, x) for (_, sig, _), x in zip(fn.args, args))
    right = text[at + len(sep):]
    outs = {s: fn.default(s) for s in fn.rets}
    for k in range(1, fn.other_val + 1):
        if right == fn.outcome_name(k):
            outs[fn.outcome] = k
            return call, outs, False
    try:
        v = ast.literal_eval(right)
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        raise ValueError(f'{right[:60]!r} is no result of a call') from None
    vals = list(v) if fn.tuple_ and isinstance(v, tuple) else [v]
    if len(vals) != len(fn.rets):
        raise ValueError(f'{len(vals)} results where the function returns {len(fn.rets)}')
    for s, x in zip(fn.rets, vals):
        outs[s] = _value(fn, s, x)
    outs[fn.outcome] = 0
    return call, outs, True


def _replay(S, s: str, tr: list[dict], cases: int = 4096, timeout: Optional[float] = None) -> dict:
    """rv.check of trace tr on the monitors of reading s, kept with the
    session: a call that a search confirmed is not simulated again when its
    printed line reads back to the same trace."""
    from . import rv
    memo, mon = S.__dict__.setdefault('_replayed', {}), S.mon(s)
    key = (s, json.dumps(tr, sort_keys=True))
    if key not in memo or memo[key][0] is not mon:
        if len(memo) >= 256:
            memo.clear()
        memo[key] = (mon, rv.check(S, s, tr, max_cases=cases, timeout=timeout))
    return memo[key][1]


def separates(S, fn: Fn, w: dict, acc: str, rej: str, req: str, context: bool,
              cases: int = REPLAY_CASES, timeout: Optional[float] = None) -> bool:
    """The calls and outputs of w, run on the compiled monitors without a
    solver, separate the two readings on requirement req as a comparison
    reads a witness (_Spec.split_status): reading acc accepts them (its rules
    of req and the frame; in context every rule), and reading rej rejects
    them by a rule of req while every other rule it had to keep holds (the
    frame; in context the rules of the other requirements).  A rule counts
    for as long as the assumptions of its reading hold.  rv.NotReplayed
    where a reading has more rigid values than `cases`, or the simulations
    pass `timeout` seconds."""
    import time
    t0 = time.time()
    tr = _trace(S, fn, w)
    frame = S.b.frame_ids

    def failing(s):
        left = None if timeout is None else max(0.05, timeout - (time.time() - t0))
        r = _replay(S, s, tr, cases, left)
        items = S.mon(s).items
        broke = [c for i, c in r.items() if c is not None and items[i].role == 'assumption']
        upto = min(broke) if broke else len(tr)
        return {i for i, c in r.items() if items[i].role == 'property' and c is not None and c < upto}, items
    fa, ia = failing(acc)
    fr, ir = failing(rej)
    on_a = [i for i in ia if ia[i].role == 'property' and (i in frame or context or ia[i].req == req)]
    on_r = [i for i in ir if ir[i].role == 'property' and (i in frame or (context and ir[i].req != req))]
    asked = [i for i in ir if ir[i].role == 'property' and ir[i].req == req and i not in frame]
    return not any(i in fa for i in on_a) and not any(i in fr for i in on_r) and any(i in fr for i in asked)


def _why_not(S, fn: Fn, lines: list, acc: str, rej: str, req: str, context: bool, cases: int,
             left: float) -> Optional[str]:
    """None where the calls of these printed lines separate the two readings
    on replay; else why they are not shown."""
    from . import rv
    try:
        read = [read_line(fn, x) for x in lines]
    except ValueError as e:
        return f'the call is not read back ({e})'
    if [line(fn, c, o) for c, o, _ in read] != list(lines):
        return 'the call reads back as another call'
    if left <= 0:
        return 'the call was not replayed (the time for the replays of this comparison was used up)'
    w = {'calls': [c for c, _, _ in read], 'outs': [o for _, o, _ in read]}
    try:
        if separates(S, fn, w, acc, rej, req, context, cases, left):
            return None
    except rv.NotReplayed as e:
        return f'the call was not replayed ({e})'
    return 'the call does not separate the two readings when it is run on their monitors' + \
        ('' if all(v for _, _, v in read) else ' (its line names an ending, not the values that went with it)')


def _drop(rec: dict, key: str, why: str):
    """Witness `key` of a comparison's record is no longer shown: it is kept
    under 'dropped' with the reason, and the requirement is undecided, in
    that direction (what the other direction found stands in 'status')."""
    rec.setdefault('dropped', {})[key] = {'lines': list(rec[key]['lines']), 'why': why}
    del rec[key]
    rec['relation'] = 'UNKNOWN'
    if isinstance(rec.get('status'), dict):
        rec['status'][key] = 'unknown'


def replayed(S, a: str, b: str, fn: Fn, recs: dict, context: bool = False, seconds: Optional[float] = None,
             cases: int = REPLAY_CASES) -> dict:
    """The records of compare(S, a, b, fn, context) with every call they show
    run again from its printed line: the line is read back (read_line), must
    print as it was shown, and its calls must separate the two readings on
    the compiled monitors (separates).  A witness that passes is marked
    'replayed'.  One that does not is taken out of its record and kept there
    under 'dropped' with the reason, and its requirement becomes UNKNOWN: a
    call that was not replayed is not shown.  seconds: for all the calls
    together (REPLAY_SECONDS); a call reached after that is dropped as not
    replayed.  For a printable function.  recs is left as it is."""
    import copy
    import time
    t0, most = time.time(), REPLAY_SECONDS if seconds is None else seconds
    out = copy.deepcopy(recs)
    for r, rec in out.items():
        if not isinstance(rec, dict) or r == '<assumptions>':
            continue
        for key, acc, rej in ((WITNESSES[0], a, b), (WITNESSES[1], b, a)):
            w = rec.get(key)
            if not isinstance(w, dict) or not w.get('lines'):
                continue
            why = _why_not(S, fn, w['lines'], acc, rej, r, context, cases, most - (time.time() - t0))
            if why is None:
                w['replayed'] = True
            else:
                _drop(rec, key, why)
    return out


def unshown(recs: dict, why: str) -> dict:
    """The records of a comparison without the calls they show, each kept
    under 'dropped' with the reason `why`: what stands where the replay of
    the calls did not end.  recs is left as it is."""
    import copy
    out = copy.deepcopy(recs)
    for r, rec in out.items():
        if not isinstance(rec, dict) or r == '<assumptions>':
            continue
        for key in WITNESSES:
            if isinstance(rec.get(key), dict) and rec[key].get('lines'):
                _drop(rec, key, why)
    return out


# ----------------------------------------------------------------------------
# running the function
# ----------------------------------------------------------------------------

RUNNER = r'''
import array, importlib.util, json, os, resource, signal, sys

def main():
    src, fname, calls_path, out_path, kinds, widths, raises, timeout = sys.argv[1:9]
    kinds = kinds.split(',')
    widths = [int(w) for w in widths.split(',')]
    raises = [r for r in raises.split(',') if r]
    timeout = float(timeout)
    tuple_ = sys.argv[9] == '1'
    try:
        resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
    except (ValueError, OSError):
        pass
    if os.path.isdir(src):                  # a package: the entry module, by its dotted name
        sys.path.insert(0, os.path.abspath(src))
        mod = importlib.import_module(os.environ['FCP_ENTRY'])
    else:
        sys.path.insert(0, os.path.dirname(os.path.abspath(src)))
        spec = importlib.util.spec_from_file_location('fcp_impl', src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    f = getattr(mod, fname)
    a = array.array('q')
    with open(calls_path, 'rb') as fh:
        a.frombytes(fh.read())
    nargs = len(kinds)
    n = len(a) // nargs
    nret = len(widths)
    other_exc, other_val = 1 + len(raises), 2 + len(raises)
    out = array.array('q')
    examples = {}

    class Timeout(BaseException):
        pass

    def on_alarm(*_):
        raise Timeout()

    signal.signal(signal.SIGALRM, on_alarm)
    for i in range(n):
        args = [bool(a[i * nargs + j]) if kinds[j] == 'bool' else int(a[i * nargs + j]) for j in range(nargs)]
        code, vals, what = 0, [0] * nret, None
        try:
            signal.setitimer(signal.ITIMER_REAL, timeout)
            r = f(*args)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except Timeout:
            code, what = other_exc, 'did not finish within %gs' % timeout
        except BaseException as e:
            signal.setitimer(signal.ITIMER_REAL, 0)
            name = type(e).__name__
            if name in raises:
                code = 1 + raises.index(name)
            else:
                code, what = other_exc, ('%s: %s' % (name, e))[:200]
        else:
            vs = r if tuple_ else (r,)
            if (not tuple_ or (type(r) is tuple and len(r) == nret)) and all(
                    type(v) is int and 0 <= v < (1 << w) for v, w in zip(vs, widths)):
                vals = list(vs)
            else:
                code, what = other_val, ('returned %r (%s)' % (r, type(r).__name__))[:200]
        out.append(code)
        out.extend(vals)
        if what is not None:
            ex = examples.setdefault(str(code), [])
            if len(ex) < 5:
                ex.append({'call': i, 'args': args, 'what': what})
    with open(out_path, 'wb') as fh:
        out.tofile(fh)
    with open(out_path + '.json', 'w') as fh:
        json.dump(examples, fh)

main()
'''


RUNNER_JSON = r'''
import importlib.util, json, os, resource, signal, sys

def fits(v, spec):
    kind, w, n = spec
    if kind == 'int':
        return type(v) is int and 0 <= v < (1 << w)
    if kind == 'bool':
        return type(v) is bool
    if kind == 'str':
        return type(v) is str and len(v) <= n and all(ord(c) < (1 << w) for c in v)
    return type(v) is list and len(v) <= n and all(type(x) is int and 0 <= x < (1 << w) for x in v)

def main():
    src, fname, calls_path, out_path, kinds, rets, raises, timeout, tuple_, cls, init, shape, rshape, methods = \
        sys.argv[1:15]
    kinds, rets, init, shape, rshape, methods = (json.loads(x) for x in (kinds, rets, init, shape, rshape, methods))
    by_op = {m['op']: m for m in methods}
    raises = [r for r in raises.split(',') if r]
    timeout, tuple_ = float(timeout), tuple_ == '1'
    try:
        resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
    except (ValueError, OSError):
        pass
    if os.path.isdir(src):                  # a package: the entry module, by its dotted name
        sys.path.insert(0, os.path.abspath(src))
        mod = importlib.import_module(os.environ['FCP_ENTRY'])
    else:
        sys.path.insert(0, os.path.dirname(os.path.abspath(src)))
        spec = importlib.util.spec_from_file_location('fcp_impl', src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    f = None if cls else getattr(mod, fname)
    with open(calls_path) as fh:
        calls = json.load(fh)
    other_exc, other_val = 1 + len(raises), 2 + len(raises)
    out, examples = [], {}

    class Timeout(BaseException):
        pass

    def on_alarm(*_):
        raise Timeout()

    def make(p, d):
        return getattr(mod, p['cls'])(**d) if p.get('cls') else d

    def build(flat):
        """The Python arguments: a record from its fields' values, a list of
        records from the fields' lists (one length)."""
        out = []
        for p in shape:
            vs = [flat[k] for k in p['pos']]
            if p['kind'] == 'value':
                out.append(vs[0])
            elif p['kind'] == 'record':
                out.append(make(p, dict(zip(p['keys'], vs))))
            else:
                out.append([make(p, {key: (bool(col[j]) if b else col[j])
                                     for key, col, b in zip(p['keys'], vs, p['bools'])})
                            for j in range(len(vs[0]))])
        return out

    def fields_of(x):
        if rshape.get('cls'):
            if type(x).__name__ != rshape['cls'] or not all(hasattr(x, k) for k in rshape['keys']):
                return None
            return [getattr(x, k) for k in rshape['keys']]
        if type(x) is not dict or set(x) != set(rshape['keys']):
            return None
        return [x[k] for k in rshape['keys']]

    def split(r):
        """The returned value as one value per output signal, or None when it
        does not have the declared form."""
        if rshape is None:
            if tuple_ and not (type(r) is tuple and len(r) == len(rets)):
                return None
            return list(r if tuple_ else (r,))
        if rshape['kind'] == 'record':
            return fields_of(r)
        if type(r) is not list:
            return None
        rows = [fields_of(x) for x in r]
        if any(x is None for x in rows):
            return None
        out = []
        for j, b in enumerate(rshape['bools']):
            col = [row[j] for row in rows]
            if b:
                if not all(type(v) is bool for v in col):
                    return None
                col = [int(v) for v in col]
            out.append(col)
        return out

    signal.signal(signal.SIGALRM, on_alarm)
    for i, raw in enumerate(calls):
        if raw is None:                      # reset: a new object
            code, vals, what = -1, None, None
            try:
                signal.setitimer(signal.ITIMER_REAL, timeout)
                obj = getattr(mod, cls)(*init)
                f = obj if methods else getattr(obj, fname)
                signal.setitimer(signal.ITIMER_REAL, 0)
            except BaseException as e:
                signal.setitimer(signal.ITIMER_REAL, 0)
                f, what = None, ('constructor: %s: %s' % (type(e).__name__, e))[:200]
            out.append([code, vals])
            if what is not None:
                ex = examples.setdefault(str(other_exc), [])
                if len(ex) < 5:
                    ex.append({'call': i, 'args': None, 'what': what})
            continue
        args = [bool(x) if k == 'bool' else (list(x) if k == 'list' else x) for x, k in zip(raw, kinds)]
        code, vals, what = 0, None, None
        if shape:
            try:
                args = build(args)
            except BaseException as e:           # a record class that does not take these fields
                code, what = other_exc, ('building the arguments: %s: %s' % (type(e).__name__, e))[:200]
                out.append([code, vals])
                ex = examples.setdefault(str(code), [])
                if len(ex) < 5:
                    ex.append({'call': i, 'args': raw, 'what': what})
                continue
        try:
            if f is None:
                raise RuntimeError('no object: the constructor failed')
            m = by_op.get(raw[0]) if methods else None
            if methods and m is None:
                raise RuntimeError('no method has op %r' % (raw[0],))
            signal.setitimer(signal.ITIMER_REAL, timeout)
            r = getattr(f, m['name'])(*[args[k] for k in m['pos']]) if m else f(*args)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except Timeout:
            code, what = other_exc, 'did not finish within %gs' % timeout
        except BaseException as e:
            signal.setitimer(signal.ITIMER_REAL, 0)
            name = type(e).__name__
            if name in raises:
                code = 1 + raises.index(name)
            else:
                code, what = other_exc, ('%s: %s' % (name, e))[:200]
        else:
            if m is not None:                    # its own results; the other results are empty
                vals = [('' if sp[0] == 'str' else [] if sp[0] == 'list' else 0) for sp in rets]
                if m['ret_idx']:
                    vs = r if m['tuple_'] else (r,)
                    if (m['tuple_'] and not (type(r) is tuple and len(r) == len(m['ret_idx']))) or not all(
                            fits(v, rets[j]) for v, j in zip(vs, m['ret_idx'])):
                        code, vals, what = other_val, None, ('returned %r (%s)' % (r, type(r).__name__))[:200]
                    else:
                        for v, j in zip(vs, m['ret_idx']):
                            vals[j] = v
                out.append([code, vals])
                if what is not None:
                    ex = examples.setdefault(str(code), [])
                    if len(ex) < 5:
                        ex.append({'call': i, 'args': raw, 'what': what})
                continue
            vs = split(r)
            if vs is not None and all(fits(v, sp) for v, sp in zip(vs, rets)):
                vals = list(vs)
            else:
                code, what = other_val, ('returned %r (%s)' % (r, type(r).__name__))[:200]
        out.append([code, vals])
        if what is not None:
            ex = examples.setdefault(str(code), [])
            if len(ex) < 5:
                ex.append({'call': i, 'args': raw, 'what': what})
    with open(out_path, 'w') as fh:
        json.dump({'out': out, 'examples': examples}, fh)

main()
'''


def _run_json(fn: Fn, src: str, calls: list[tuple], timeout: float, total: float) -> dict:
    """run() for a function with string or list arguments or results, or a
    method of an object (a None in calls creates a new object; its entry has
    outcome -1)."""
    jsonable = [None if c is None else [list(x) if isinstance(x, tuple) else x for x in c] for c in calls]
    rets = [[fn.kinds.get(r, 'int'), fn.seqs[r][0] if r in fn.seqs else fn.widths[r], fn.seqs.get(r, (0, 0))[1]]
            for r in fn.rets]
    with tempfile.TemporaryDirectory(prefix='fcp_sw_') as d:
        cp, op, rp = os.path.join(d, 'calls.json'), os.path.join(d, 'out.json'), os.path.join(d, 'runner.py')
        with open(cp, 'w') as f:
            json.dump(jsonable, f)
        with open(rp, 'w') as f:
            f.write(RUNNER_JSON)
        argv = [PY, '-I', rp, os.path.abspath(src), fn.name, cp, op, json.dumps([k for _, _, k in fn.args]),
                json.dumps(rets), ','.join(fn.raises), str(timeout), '1' if fn.tuple_ else '0', fn.cls or '',
                json.dumps(fn.init), json.dumps(fn.shape), json.dumps(fn.ret_shape),
                json.dumps([dict(m, ret_idx=[fn.rets.index(x) for x in m['rets']]) for m in fn.methods])]
        p = subprocess.run(argv, capture_output=True, text=True, timeout=total, cwd=d, env=entry_env(fn))
        if p.returncode != 0 or not os.path.exists(op):
            err = (p.stderr.strip().splitlines() or ['no output'])[-1][:300]
            return {'code': [-1 if c is None else fn.other_exc for c in calls],
                    'ret': {r: [fn.default(r)] * len(calls) for r in fn.rets},
                    'examples': {str(fn.other_exc): [{'call': 0, 'args': jsonable[0] if calls else [], 'what': err}]},
                    'load_error': err}
        with open(op) as f:
            o = json.load(f)
    code = [c for c, _ in o['out']]
    ret = {}
    for j, r in enumerate(fn.rets):
        col = []
        for c, vals in o['out']:
            v = vals[j] if c == 0 else fn.default(r)
            col.append(tuple(v) if isinstance(v, list) else v)
        ret[r] = col
    return {'code': code, 'ret': ret, 'examples': o['examples'], 'load_error': None}


def run(fn: Fn, src: str, calls: list[tuple], timeout: float = 1.0, total: float = 1800) -> dict:
    """Run src's function on every call in a fresh process.  Returns
    {'code': [outcome per call], 'ret': {signal: [value per call]},
    'examples': {outcome: [{call, args, what}]}, 'load_error': str or None}."""
    if fn.has_seq or fn.stateful or fn.structured:
        return _run_json(fn, src, calls, timeout, total)
    nret = len(fn.rets)
    with tempfile.TemporaryDirectory(prefix='fcp_sw_') as d:
        a = array.array('q', [int(x) for c in calls for x in c])
        cp, op, rp = os.path.join(d, 'calls.bin'), os.path.join(d, 'out.bin'), os.path.join(d, 'runner.py')
        with open(cp, 'wb') as f:
            a.tofile(f)
        with open(rp, 'w') as f:
            f.write(RUNNER)
        argv = [PY, '-I', rp, os.path.abspath(src), fn.name, cp, op, ','.join(k for _, _, k in fn.args),
                ','.join(str(fn.widths[s]) for s in fn.rets), ','.join(fn.raises), str(timeout),
                '1' if fn.tuple_ else '0']
        p = subprocess.run(argv, capture_output=True, text=True, timeout=total, cwd=d, env=entry_env(fn))
        if p.returncode != 0 or not os.path.exists(op):
            # the module does not even load: every call ends without an answer
            err = (p.stderr.strip().splitlines() or ['no output'])[-1][:300]
            return {'code': [fn.other_exc] * len(calls), 'ret': {s: [0] * len(calls) for s in fn.rets},
                    'examples': {str(fn.other_exc): [{'call': 0, 'args': list(calls[0]) if calls else [],
                                                      'what': err}]}, 'load_error': err}
        o = array.array('q')
        with open(op, 'rb') as f:
            o.frombytes(f.read())
        with open(op + '.json') as f:
            examples = json.load(f)
    step = 1 + nret
    return {'code': list(o[0::step]), 'ret': {s: list(o[1 + j::step]) for j, s in enumerate(fn.rets)},
            'examples': examples, 'load_error': None}


_BASE: dict[tuple, tuple] = {}


def prefetch(fn: Fn, calls) -> None:
    """For a change: the old code's answers to all these calls, in one run,
    before a loop asks the solver about them one by one."""
    if fn.baseline:
        flat = [c for x in calls for c in (x if isinstance(x, list) else [x])]
        baseline_values(fn, [c for c in flat if c is not None])


def baseline_values(fn: Fn, calls: list) -> dict[str, list[int]]:
    """For a change: the code before it, run on the same calls (with the
    arguments it takes), as columns of its signals: returned values and
    outcome.  Cached per call; the calls not yet cached run in one process."""
    b = fn.baseline
    names = [a for a, _, _ in fn.args]
    pos = [names.index(a) for a in b['args']]
    sub = [None if c is None else tuple(c[i] for i in pos) for c in calls]
    todo = list(dict.fromkeys(x for x in sub if x is not None and (b['path'], x) not in _BASE))
    if todo:
        old = Fn(b['name'], [fn.args[i] for i in pos], b['returns'], fn.tuple_, b['outcome'], fn.raises, fn.widths,
                 {}, fn.seqs, fn.kinds)
        r = run(old, b['path'], todo)
        for j, x in enumerate(todo):
            _BASE[(b['path'], x)] = tuple(r['ret'][s][j] for s in b['returns']) + (max(0, r['code'][j]),)
    cols: dict[str, list] = {s: [] for s in fn.base_signals}
    for x in sub:
        vals = _BASE[(b['path'], x)] if x is not None else (0,) * len(fn.base_signals)
        for s, v in zip(fn.base_signals, vals):
            cols[s].append(v)
    return cols


def _shape_text(fn: Fn, p: dict, vals: list, sigs: list[str]) -> str:
    """A parameter or returned value of shape p from its signals' values: a
    value, a record as a dict literal (or Cls(key=value, ...)), or a list of
    records."""
    def rec(items):
        if p.get('cls'):
            return f'{p["cls"]}(' + ', '.join(f'{k}={v}' for k, v in zip(p['keys'], items)) + ')'
        return '{' + ', '.join(f'{json.dumps(k)}: {v}' for k, v in zip(p['keys'], items)) + '}'
    if p['kind'] == 'value':
        return fn.fmt(sigs[0], vals[0])
    if p['kind'] == 'record':
        return rec([fn.fmt(sg, v) for sg, v in zip(sigs, vals)])
    cols = [fn.codes(v) for v in vals]
    return '[' + ', '.join(rec([str(bool(col[j])) if b else str(col[j]) for col, b in zip(cols, p['bools'])])
                           for j in range(len(cols[0]) if cols else 0)) + ']'


def call_text(fn: Fn, c: tuple) -> str:
    m = fn.method(c)
    if m is not None:
        return f'{m["name"]}(' + ', '.join(fn.fmt(fn.args[p][1], c[p]) for p in m['pos']) + ')'
    if fn.shape:
        args = ', '.join(_shape_text(fn, p, [c[k] for k in p['pos']], [fn.args[k][1] for k in p['pos']])
                         for p in fn.shape)
    else:
        args = ', '.join(fn.fmt(sig, x) for x, (_, sig, _) in zip(c, fn.args))
    return f'{fn.name}({args})'


def ret_text(fn: Fn, vals: list, c=None) -> str:
    """The returned value from its signals' values (in fn.rets order); for
    an object with several methods, the results of the method call c calls."""
    m = fn.method(c) if c is not None else None
    if m is not None:
        vs = [fn.fmt(sg, vals[fn.rets.index(sg)]) for sg in m['rets']]
        return '(' + ', '.join(vs) + ')' if m['tuple_'] else (vs[0] if vs else 'None')
    if fn.ret_shape is not None:
        return _shape_text(fn, fn.ret_shape, vals, fn.rets)
    vs = [fn.fmt(sg, v) for sg, v in zip(fn.rets, vals)]
    return f'({", ".join(vs)})' if fn.tuple_ else vs[0]


def result_text(fn: Fn, res: dict, i: int, c=None) -> str:
    k = res['code'][i]
    if k == 0:
        return ret_text(fn, [res['ret'][s][i] for s in fn.rets], c)
    for ex in res['examples'].get(str(k), []):
        if ex['call'] == i:
            return ex['what']
    return fn.outcome_name(k)


def trace(fn: Fn, calls: list[tuple], res: dict) -> dict[str, list[int]]:
    """Columns of the trace (one per port), cycle 0 reset, then one cycle per
    call; a None in calls (a new object) is a reset cycle."""
    cols = {'rst_n': [0] + [0 if c is None else 1 for c in calls], fn.outcome: [0] + [max(0, k) for k in res['code']]}

    def put(sig, vals):
        if sig not in fn.seqs:
            cols[sig] = [0] + [int(v) for v in vals]
            return
        enc = [fn.encode(sig, fn.default(sig))] + [fn.encode(sig, v) for v in vals]
        for port, _ in fn.ports(sig):
            cols[port] = [e[port] for e in enc]
    for j, (_, sig, _) in enumerate(fn.args):
        put(sig, [fn.default(sig) if c is None else c[j] for c in calls])
    for s in fn.rets:
        put(s, res['ret'][s])
    if fn.baseline:
        for s, col in baseline_values(fn, calls).items():
            put(s, col)
    return cols


def cycle(cols: dict, k: int) -> dict:
    return {n: v[k] for n, v in cols.items()}


# ----------------------------------------------------------------------------
# checking a recorded trace with the compiled monitor
# ----------------------------------------------------------------------------

def _probes(mon) -> list[tuple[str, str, str]]:
    """(item id, kind, monitor output): ok of every property (plus its trigger),
    aok of every assumption, cov of every scenario."""
    out = []
    for it in mon.items.values():
        if it.role == 'property':
            out.append((it.id, 'ok', it.out['ok'] if mon.rigid_ports else (it.out.get('okd') or it.out['ok'])))
            if 'tr' in it.out:
                out.append((it.id, 'tr', it.out['tr']))
        elif it.role == 'assumption':
            out.append((it.id, 'aok', it.out['aok']))
        elif it.role == 'scenario' and 'cov' in it.out:
            out.append((it.id, 'cov', it.out['cov']))
    return out


def check(S, s: str, cols: dict[str, list[int]], max_cases: int = 4096, keep: int = 0) -> dict:
    """Simulate the monitor of reading s on the trace.  Returns, per item,
    {'first': first failing cycle or None, 'count': failing cycles,
    'trig': cycles in which the trigger held, 'cov': cycles in which a
    scenario held, 'fails': up to keep failing cycles}.  Rigid variables are
    replayed over their whole range.  The monitor runs compiled by Verilator
    (fcp.vl) when it is installed, else in Icarus (FCP_ICARUS=1 forces it)."""
    mon = S.mon(s)
    probes = _probes(mon)
    n = len(cols['rst_n'])
    rig = mon.rigid_ports
    cases = 1
    for _, _, lo, hi in rig:
        cases *= hi - lo + 1
    if cases > max_cases:
        raise SoftwareError(f'{s}: {cases} rigid cases exceed max_cases={max_cases}')
    if vl.available() and not os.environ.get('FCP_ICARUS'):
        out: dict[str, dict] = {}
        for (iid, kind, _), (first, count, fails) in zip(probes, vl.replay(mon, probes, cols, keep)):
            rec = out.setdefault(iid, {'first': None, 'count': 0, 'trig': None, 'cov': None, 'fails': []})
            if kind in ('ok', 'aok'):
                rec.update(first=None if first < 0 else first, count=count, fails=fails)
            else:
                rec['trig' if kind == 'tr' else 'cov'] = count
        return out
    tb = ['`timescale 1ns/1ps', 'module fcp_sw;', "  reg clk = 1'b0;", '  integer k, n;', '  reg [8*1024:1] fn;']
    conns = ['.clk(clk)']
    for name, w in mon.ports_in:
        tb.append(f'  reg {vw(w)}{name};')
        tb.append(f'  reg {vw(w)}m_{name} [0:{n - 1}];')
        conns.append(f'.{name}({name})')
    for port, w, lo, hi in rig:
        tb.append(f'  reg signed [{w - 1}:0] rg_{port};')
        tb.append(f'  integer i_{port};')
        conns.append(f'.{port}(rg_{port})')
    for port, w in mon.nondet_ports:
        conns.append(f".{port}({w}'d0)")
    for o in mon.outputs:
        tb.append(f'  wire {o};')
        conns.append(f'.{o}({o})')
    tb.append(f'  {mon.module} m (' + ', '.join(conns) + ');')
    for j, _ in enumerate(probes):
        tb.append(f'  integer first_{j}, count_{j};')
        if rig:
            tb.append(f'  reg seen_{j} [0:{n - 1}];')
    tb += ['  task replay;', '    begin', '      for (k = 0; k < n; k = k + 1) begin']
    tb.append('        ' + ' '.join(f'{name} = m_{name}[k];' for name, _ in mon.ports_in) + ' #1;')
    for j, (_, kind, wire) in enumerate(probes):
        # with rigid replays, a cycle counts once (seen_j); without, every replay is the only one
        once = f' && !seen_{j}[k]' if rig else ''
        mark = f' seen_{j}[k] = 1\'b1;' if rig else ''
        if kind in ('ok', 'aok'):
            tb.append(f'        if ({wire} !== 1\'b1{once}) begin if (first_{j} < 0 || k < first_{j}) first_{j} = k; '
                      f'count_{j} = count_{j} + 1;{mark} end')
        else:
            tb.append(f'        if ({wire} === 1\'b1{once}) begin count_{j} = count_{j} + 1;{mark} end')
    tb += ["        #4 clk = 1'b1; #5 clk = 1'b0;", '      end', '    end', '  endtask', '  initial begin']
    tb.append('    if (!$value$plusargs("n=%d", n)) n = 0;')
    for name, _ in mon.ports_in:
        tb.append(f'    if ($value$plusargs("f_{name}=%s", fn)) $readmemh(fn, m_{name});')
    for j, _ in enumerate(probes):
        tb.append(f'    first_{j} = -1; count_{j} = 0;')
        if rig:
            tb.append(f'    for (k = 0; k < n; k = k + 1) seen_{j}[k] = 1\'b0;')
    ind = '    '
    for port, w, lo, hi in rig:
        tb.append(f'{ind}for (i_{port} = {lo}; i_{port} <= {hi}; i_{port} = i_{port} + 1) begin')
        ind += '  '
        tb.append(f'{ind}rg_{port} = i_{port};')
    tb.append(f'{ind}replay;')
    for _ in rig:
        ind = ind[:-2]
        tb.append(f'{ind}end')
    for j, _ in enumerate(probes):
        tb.append(f'    $display("P {j} %0d %0d", first_{j}, count_{j});')
    tb += ['    $finish;', '  end', 'endmodule']
    with tempfile.TemporaryDirectory(prefix='fcp_swc_') as d:
        with open(os.path.join(d, 'mon.v'), 'w') as f:
            f.write(mon.text)
        with open(os.path.join(d, 'tb.v'), 'w') as f:
            f.write('\n'.join(tb) + '\n')
        plus = [f'+n={n}']
        for name, _ in mon.ports_in:
            p = os.path.join(d, f'{name}.hex')
            col = cols.get(name)
            with open(p, 'w') as f:
                f.write(''.join(f'{v:x}\n' for v in col) if col is not None else '0\n' * n)
            plus.append(f'+f_{name}={p}')
        subprocess.run([IVERILOG, '-g2005', '-o', os.path.join(d, 'sim'), os.path.join(d, 'mon.v'),
                        os.path.join(d, 'tb.v')], check=True, capture_output=True, text=True)
        res = subprocess.run([VVP, '-n', os.path.join(d, 'sim')] + plus, check=True, capture_output=True, text=True)
    out: dict[str, dict] = {}
    for line in res.stdout.splitlines():
        if not line.startswith('P '):
            continue
        _, j, first, count = line.split()
        iid, kind, _ = probes[int(j)]
        rec = out.setdefault(iid, {'first': None, 'count': 0, 'trig': None, 'cov': None, 'fails': []})
        if kind in ('ok', 'aok'):
            rec['first'] = None if int(first) < 0 else int(first)
            rec['count'] = int(count)
        else:
            rec['trig' if kind == 'tr' else 'cov'] = int(count)
    return out


# ----------------------------------------------------------------------------
# verdicts on one implementation
# ----------------------------------------------------------------------------

def relational(it) -> bool:
    """Does the item compare a call with earlier calls?"""
    text = json.dumps(it.source) + it.formula + json.dumps(getattr(it.args, 'raw', {}))
    return bool(re.search(r'\b(prev|rose|fell|stable|changed|once|hist|since)\s*\(', text))


def render(S, fn: Fn, tr: list[dict], upto: Optional[int] = None) -> list[str]:
    """A trace (of the spec-only model or of a run) as calls, one per cycle
    outside reset: 'checkout(5000, 0, False) -> (5000, 0)'."""
    rst, low = S.b.iface.reset.name, S.b.iface.reset.active_low
    out = []
    for k, st in enumerate(tr):
        if upto is not None and k > upto:
            break
        if int(st.get(rst) or 0) == (0 if low else 1):
            continue
        get = lambda p: int(st.get(p) or 0)  # noqa: E731
        c = tuple(fn.decode(sig, get) for _, sig, _ in fn.args)
        code = int(st.get(fn.outcome) or 0)
        res = ret_text(fn, [fn.decode(s, get) for s in fn.rets], c) if code == 0 else fn.outcome_name(code)
        out.append(f'{call_text(fn, c)} -> {res}')
    return out


def replay(fn: Fn, src: str, calls: list[tuple], res: dict, idx: list[int]) -> bool:
    """Run the calls at idx again in a fresh process (for an object, on a new
    object, in order): the same outcomes?"""
    lead = [None] if fn.stateful else []
    again = run(fn, src, lead + [calls[i] for i in idx])
    o = len(lead)
    return all(again['code'][j + o] == res['code'][i] and
               all(again['ret'][s][j + o] == res['ret'][s][i] for s in fn.rets) for j, i in enumerate(idx))


def verify(S, s: str, fn: Fn, src: str, calls: list[tuple], res: dict, cols: dict) -> dict:
    """Every property of reading s on one implementation: PASS within the
    scope, or FAIL with the first failing call (and the call before it, for a
    relational property), replayed."""
    chk = check(S, s, cols, keep=2000 if (fn.has_seq or fn.stateful) else 0)
    mon = S.mon(s)
    out = {}
    for iid, r in chk.items():
        it = mon.items[iid]
        rec = {'req': it.req, 'role': it.role, 'calls': len(calls), 'count': r['count']}
        if it.role == 'scenario':
            rec['status'] = 'COVERED' if r['cov'] else 'NOT-COVERED'
        elif r['first'] is None:
            rec['status'] = 'PASS' if (r['trig'] is None or r['trig'] > 0) else 'VACUOUS'
            rec['triggered'] = r['trig']
        else:
            k = r['first']                      # cycle; call index k - 1
            rel = relational(it)
            if fn.stateful:                     # the shortest, simplest history that ends in a failure
                k = min((c for c in (r.get('fails') or [k]) if c >= 1 and calls[c - 1] is not None),
                        key=lambda c: (len(history(calls, c - 1)),
                                       tuple(_weight(fn, calls[i]) for i in history(calls, c - 1))), default=k)
                idx = history(calls, k - 1)
            else:
                if r.get('fails'):              # the simplest failing call (the first for integer functions)
                    k = min((c for c in r['fails'] if c >= 1 and (c >= 2 or not rel)),
                            key=lambda c: tuple(_weight(fn, calls[i]) for i in ([c - 2, c - 1] if rel else [c - 1])),
                            default=k)
                idx = [k - 2, k - 1] if rel and k >= 2 else [k - 1]
            rec.update(status='FAIL', triggered=r['trig'],
                       calls_shown=[{'call': call_text(fn, calls[i]), 'got': result_text(fn, res, i, calls[i])} for i in idx],
                       cycles=[i + 1 for i in idx],
                       replay='confirmed' if replay(fn, src, calls, res, idx) else 'MISMATCH')
        out[iid] = rec
    return out


def disagreements(fn: Fn, calls: list[tuple], results: dict[str, dict]) -> list[dict]:
    """Where implementations of the same prompt answer the same call
    differently (N-version code).  Calls are grouped by how they split the
    implementations into groups that agree; for each split, the number of
    distinct calls and the simplest one with every implementation's answer.
    A split is a decision the prompt left to whoever wrote the code."""
    names = list(results)
    if fn.stateful:
        return _object_disagreements(fn, calls, results)
    groups: dict[tuple, dict] = {}
    seen = set()
    simple = (lambda c: _weight(fn, c)) if fn.has_seq else _simple  # noqa: E731
    for i, c in enumerate(calls):
        if c in seen:
            continue
        seen.add(c)
        outs = {n: (results[n]['code'][i],) + tuple(results[n]['ret'][s][i] for s in fn.rets) for n in names}
        if len(set(outs.values())) == 1:
            continue
        part: dict[tuple, list[str]] = {}
        for n in names:
            part.setdefault(outs[n], []).append(n)
        key = tuple(sorted(tuple(g) for g in part.values()))
        g = groups.setdefault(key, {'count': 0, 'best': i})
        g['count'] += 1
        if simple(c) < simple(calls[g['best']]):
            g['best'] = i
    out = []
    for key, g in sorted(groups.items(), key=lambda kv: -kv[1]['count']):
        i = g['best']
        out.append({'groups': [list(x) for x in key], 'count': g['count'], 'call': call_text(fn, calls[i]),
                    'args': list(calls[i]), 'answers': {n: result_text(fn, results[n], i, calls[i]) for n in names}})
    return out


def _object_disagreements(fn: Fn, calls: list, results: dict[str, dict]) -> list[dict]:
    """disagreements() for an object: per sequence, the first call on which
    the implementations answer differently, grouped by how that call splits
    them; for each split, the number of distinct histories and the shortest
    one, with every implementation's answers along it."""
    names = list(results)
    groups: dict[tuple, dict] = {}
    seen = set()
    i = 0
    while i < len(calls):
        if calls[i] is None:
            i += 1
            continue
        h = history(calls, i)
        outs = {n: (results[n]['code'][i],) + tuple(results[n]['ret'][s][i] for s in fn.rets) for n in names}
        if len(set(outs.values())) > 1:
            key_h = tuple(calls[j] for j in h)
            if key_h not in seen:
                seen.add(key_h)
                part: dict[tuple, list[str]] = {}
                for n in names:
                    part.setdefault(outs[n], []).append(n)
                key = tuple(sorted(tuple(g) for g in part.values()))
                g = groups.setdefault(key, {'count': 0, 'best': h})
                g['count'] += 1
                w = lambda hh: (len(hh), tuple(_weight(fn, calls[j]) for j in hh))  # noqa: E731
                if w(h) < w(g['best']):
                    g['best'] = h
            while i < len(calls) and calls[i] is not None:      # the rest of this sequence
                i += 1
            continue
        i += 1
    out = []
    for key, g in sorted(groups.items(), key=lambda kv: -kv[1]['count']):
        h = g['best']
        out.append({'groups': [list(x) for x in key], 'count': g['count'],
                    'call': '; '.join(call_text(fn, calls[j]) for j in h),
                    'args': [list(calls[j]) for j in h], 'sequence': True,
                    'answers': {n: '; '.join(result_text(fn, results[n], j, calls[j]) for j in h) for n in names}})
    return out


def outcome_summary(fn: Fn, res: dict) -> dict:
    """How often each outcome occurred, with examples of the unexpected ones."""
    counts: dict[str, int] = {}
    for k in res['code']:
        if k < 0:
            continue                         # a new object, not a call
        counts[fn.outcome_name(k)] = counts.get(fn.outcome_name(k), 0) + 1
    return {'counts': counts, 'examples': res['examples'], 'load_error': res.get('load_error')}


# ----------------------------------------------------------------------------
# mutants of the code: behaviour that no requirement notices
# ----------------------------------------------------------------------------

_CMP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
_BIN = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Div, ast.Div: ast.FloorDiv,
        ast.Mod: ast.FloorDiv}
_SYM = {ast.Lt: '<', ast.LtE: '<=', ast.Gt: '>', ast.GtE: '>=', ast.Eq: '==', ast.NotEq: '!=', ast.Add: '+',
        ast.Sub: '-', ast.Mult: '*', ast.FloorDiv: '//', ast.Div: '/', ast.Mod: '%', ast.And: 'and', ast.Or: 'or'}


def _sites(tree) -> list[tuple[int, str, str, int]]:
    """(node index in walk order, operator kind, description, line)."""
    out = []
    for i, n in enumerate(ast.walk(tree)):
        line = getattr(n, 'lineno', 0)
        if isinstance(n, ast.Compare):
            for j, op in enumerate(n.ops):
                if type(op) in _CMP:
                    out.append((i, f'cmp{j}', f'{_SYM[type(op)]} becomes {_SYM[_CMP[type(op)]]}', line))
        elif isinstance(n, ast.BinOp) and type(n.op) in _BIN:
            out.append((i, 'bin', f'{_SYM[type(n.op)]} becomes {_SYM[_BIN[type(n.op)]]}', line))
        elif isinstance(n, ast.BoolOp):
            out.append((i, 'bool', f'{_SYM[type(n.op)]} becomes {"or" if isinstance(n.op, ast.And) else "and"}', line))
        elif isinstance(n, ast.Constant) and type(n.value) is int and not isinstance(n.value, bool):
            out.append((i, 'inc', f'{n.value} becomes {n.value + 1}', line))
            out.append((i, 'dec', f'{n.value} becomes {n.value - 1}', line))
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            out.append((i, 'not', '"not" removed', line))
        elif isinstance(n, ast.IfExp):
            out.append((i, 'ifexp', 'the two branches of a conditional expression swapped', line))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ('round', 'min', 'max'):
            alt = {'round': 'int', 'min': 'max', 'max': 'min'}[n.func.id]
            out.append((i, 'call', f'{n.func.id}() becomes {alt}()', line))
    return out


def _apply(tree, idx: int, kind: str):
    for i, n in enumerate(ast.walk(tree)):
        if i != idx:
            continue
        if kind.startswith('cmp'):
            j = int(kind[3:])
            n.ops[j] = _CMP[type(n.ops[j])]()
        elif kind == 'bin':
            n.op = _BIN[type(n.op)]()
        elif kind == 'bool':
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        elif kind in ('inc', 'dec'):
            n.value += 1 if kind == 'inc' else -1
        elif kind == 'not':
            return n                            # replaced by its operand below
        elif kind == 'ifexp':
            n.body, n.orelse = n.orelse, n.body
        elif kind == 'call':
            n.func.id = {'round': 'int', 'min': 'max', 'max': 'min'}[n.func.id]
        return None
    raise KeyError(idx)


class _Unnot(ast.NodeTransformer):
    def __init__(self, target):
        self.target = target

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        return node.operand if node is self.target else node


def mutants(src_text: str, limit: int = 80) -> list[dict]:
    """First-order mutants of the source, one operator change each."""
    sites = _sites(ast.parse(src_text))
    if len(sites) > limit:
        step = len(sites) / limit
        sites = [sites[int(i * step)] for i in range(limit)]
    out = []
    for idx, kind, desc, line in sites:
        tree = ast.parse(src_text)
        target = _apply(tree, idx, kind)
        if target is not None:
            tree = _Unnot(target).visit(tree)
        try:
            code = ast.unparse(ast.fix_missing_locations(tree))
        except Exception:
            continue
        out.append({'id': f'M{len(out) + 1}', 'line': line, 'desc': f'line {line}: {desc}', 'code': code})
    return out


def mutation(S, sets: list[str], fn: Fn, src: str, calls: list[tuple], limit: int = 80, jobs: int = 16) -> dict:
    """Mutants of the implementation on the calls: a mutant is observable if
    some call ends differently, and killed by a reading if some property of
    that reading changes its verdict (first failing call or number of
    failing calls).  Observable survivors are behaviour that no requirement
    of the reading constrains."""
    base = run(fn, src, calls)
    bcols = trace(fn, calls, base)
    bchk = {s: check(S, s, bcols) for s in sets}
    if os.path.isdir(src):                      # a package: mutants of every module, taken in turn
        per = []
        for path in py_files(src):
            with open(path) as f:
                rel = os.path.relpath(path, src)
                per.append([dict(mu, id=f'{rel}:{mu["id"]}', desc=f'{rel}: {mu["desc"]}', file=rel)
                            for mu in mutants(f.read(), limit)])
        muts = [m for row in itertools.zip_longest(*per) for m in row if m is not None][:limit]
    else:
        with open(src) as f:
            muts = mutants(f.read(), limit)

    def one(mu):
        with tempfile.TemporaryDirectory(prefix='fcp_mut_') as d:
            if os.path.isdir(src):              # the mutant module among the package's others
                import shutil
                p = os.path.join(d, 'pkg')
                shutil.copytree(src, p, ignore=shutil.ignore_patterns('__pycache__'))
                with open(os.path.join(p, mu['file']), 'w') as f:
                    f.write(mu['code'])
            else:
                p = os.path.join(d, os.path.basename(src))
                with open(p, 'w') as f:
                    f.write(mu['code'])
            r = run(fn, p, calls)
        diffs = (i for i in range(len(calls)) if r['code'][i] != base['code'][i]
                 or any(r['ret'][s][i] != base['ret'][s][i] for s in fn.rets))
        if fn.has_seq:                          # the simplest call that shows the change
            diff = min(diffs, key=lambda i: _weight(fn, calls[i]), default=None)
        else:
            diff = next(diffs, None)
        rec = {k: mu[k] for k in ('id', 'line', 'desc')}
        rec['observable'] = diff is not None
        if diff is None:
            return rec
        hist = history(calls, diff) if fn.stateful else [diff]
        rec['example'] = {'call': '; '.join(call_text(fn, calls[j]) for j in hist),
                          'original': '; '.join(result_text(fn, base, j, calls[j]) for j in hist),
                          'mutant': '; '.join(result_text(fn, r, j, calls[j]) for j in hist)}
        cols = trace(fn, calls, r)
        rec['killed_by'] = {}
        for s in sets:
            c = check(S, s, cols)
            rec['killed_by'][s] = sorted(i for i, x in c.items() if S.mon(s).items[i].role == 'property' and
                                         (x['first'], x['count']) != (bchk[s][i]['first'], bchk[s][i]['count']))
        return rec

    with ThreadPoolExecutor(max_workers=jobs) as ex:
        recs = list(ex.map(one, muts))
    obs = [r for r in recs if r['observable']]
    return {'mutants': len(recs), 'observable': len(obs), 'calls': len(calls),
            'killed': {s: sum(1 for r in obs if r['killed_by'][s]) for s in sets},
            'survivors': {s: [r for r in obs if not r['killed_by'][s]] for s in sets},
            'all': recs}


# ----------------------------------------------------------------------------
# the naive baseline: the tests the model wrote for its own code
# ----------------------------------------------------------------------------

def run_tests(tests: str, impl: str, module: str, timeout: float = 300, support: Optional[str] = None) -> dict:
    """Run a pytest file against an implementation saved as <module>.py (a
    package: its directory, with its modules).  `support` is a directory of
    files the tests need beside the code, such as stub clients of the
    services it imports.  Returns counts, the ids of the failing tests and
    pytest's summary line."""
    import xml.etree.ElementTree as ET
    with tempfile.TemporaryDirectory(prefix='fcp_tests_') as d:
        if support and os.path.isdir(support):
            for f in sorted(os.listdir(support)):
                if os.path.isfile(os.path.join(support, f)):
                    shutil.copy(os.path.join(support, f), os.path.join(d, f))
        if os.path.isdir(impl):
            top = module.split('.')[0]
            shutil.copytree(os.path.join(impl, top), os.path.join(d, top),
                            ignore=shutil.ignore_patterns('__pycache__'))
        else:
            shutil.copy(impl, os.path.join(d, f'{module}.py'))
        shutil.copy(tests, os.path.join(d, os.path.basename(tests)))
        xml = os.path.join(d, 'junit.xml')
        p = subprocess.run([PY, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', f'--junitxml={xml}', d],
                           capture_output=True, text=True, timeout=timeout, cwd=d)
        failing = []
        if os.path.exists(xml):
            for tc in ET.parse(xml).getroot().iter('testcase'):
                if tc.find('failure') is not None or tc.find('error') is not None:
                    failing.append(f"{tc.get('classname')}::{tc.get('name')}")
    last = (p.stdout.strip().splitlines() or [''])[-1]
    num = lambda w: int(m.group(1)) if (m := re.search(rf'(\d+) {w}', last)) else 0  # noqa: E731
    return {'passed': num('passed'), 'failed': num('failed') + num('error'), 'ok': p.returncode == 0,
            'failing': sorted(failing), 'summary': last}
