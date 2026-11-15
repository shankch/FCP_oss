"""Effects adapter: a function that acts through an interface it is given.

Code with effects (a payment service, files, a database) is checked through
the interface it acts on.  design.yaml declares the interface: the parameter
that receives it and its methods.  The adapter passes a recording stub, so
every call the code makes is an *output* event and every answer of the stub
an *input*, scripted by the scope.  One run of the function is one
conversation:

* a reset cycle, then one cycle per call the code makes on the interface:
  `phase` 0, `op` the method, its arguments on their signals, and the stub's
  `answer` (an input: for a method that answers, the script's next entry);
* then the return cycle: `phase` 1, the returned value and the outcome, as
  for any function.  `phase` stays 1 until the next reset (frame rule), so a
  rule about the end of a conversation reads `rose(phase)`.

The function's own arguments are inputs held through the conversation.  The
scope is a set of (arguments, script) pairs: every script of the configured
length over the answers, longer random ones, arguments at their boundary
values.  A conversation longer than `max_calls` ends as "did not finish".
The code never really sleeps or charges: the stub only records.  As for any
function, the evidence is exhaustive within the scope, not a proof.
"""
from __future__ import annotations

import itertools
import json
import os
import random
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional

from . import software as SW


@dataclass
class Ifc:
    arg: Optional[int]          # position of the interface parameter; None: the code does not receive it
    methods: list[dict]         # {name, op, args: [{signal, ...}], answers, patch: [names], via, handle, fs}
    phase: str
    op: str
    answer: str
    answers: list[str]          # every answer name; the script holds their indices
    max_calls: int
    handle: Optional[str] = None    # output: which object (1, 2, ...) a call made or acted on
    files: Optional[dict] = None    # {exists: [paths], query: [names]}: what the code sees of the files


def arg_sigs(m: dict) -> list[str]:
    """The signals of a method's arguments, in order."""
    return [a['signal'] for a in m.get('args') or []]


ENCODERS = ('enum', 'parse', 'open_mode', 'handle')


def _method(m: dict) -> dict:
    """A method of design.yaml with its arguments as dicts and its patches
    as a list (an argument may be just its signal; patch may be one name)."""
    m = dict(m)
    m['args'] = [{'signal': a} if isinstance(a, str) else dict(a) for a in m.get('args') or []]
    p = m.get('patch')
    m['patch'] = [p] if isinstance(p, str) else list(p or [])
    return m


def interface(S, fn: SW.Fn) -> Optional[Ifc]:
    d = S.b.raw_design.get('function', {}).get('interface')
    if not d:
        return None
    methods = [_method(m) for m in d['methods']]
    names: list[str] = []
    for m in methods:
        for a in m.get('answers') or []:
            if a not in names:
                names.append(a)
    sig = d['signals']
    pos = d.get('position', 0)
    by_name = {m['name']: m for m in methods}
    for m in methods:
        what = f'interface method {m["name"]}'
        if m.get('via'):
            if not by_name.get(m['via'], {}).get('handle'):
                raise SW.SoftwareError(f'{what}: via {m["via"]!r} is not a method that returns an object (handle: true)')
            if m['patch']:
                raise SW.SoftwareError(f'{what}: a method of an object the code made is reached through it, not patched')
        elif pos is None and not m['patch']:
            raise SW.SoftwareError(f'{what}: the code does not receive the interface '
                                   '(position null), so the method needs `patch`, the name the code calls')
        for p in m['patch']:
            if '.' not in p:
                raise SW.SoftwareError(f'{what}: patch {p!r} is not module.name')
        for a in m.get('raises') or {}:
            if a not in (m.get('answers') or []):
                raise SW.SoftwareError(f'{what}: raises names {a!r}, not one of its answers')
        for a in m['args']:
            if 'signal' not in a or a['signal'] not in fn.widths:
                raise SW.SoftwareError(f'{what}: argument {a} needs a signal of the interface')
            if sum(k in a for k in ENCODERS) > 1:
                raise SW.SoftwareError(f'{what}: argument {a["signal"]} has more than one encoding')
            if a.get('parse') not in (None, 'int'):
                raise SW.SoftwareError(f'{what}: argument {a["signal"]}: parse {a["parse"]!r} is not int')
        if m.get('fs') not in (None, 'open', 'remove', 'move'):
            raise SW.SoftwareError(f'{what}: fs {m["fs"]!r} is not open, remove or move')
    if sig.get('handle') and sig['handle'] not in fn.widths:
        raise SW.SoftwareError(f'interface signals: handle {sig["handle"]!r} is not a signal')
    files = d.get('files')
    if files:
        for q in files.get('query') or []:
            if '.' not in q:
                raise SW.SoftwareError(f'interface files: query {q!r} is not module.name')
    return Ifc(None if pos is None else int(pos), methods, sig['phase'], sig['op'], sig['answer'],
               names, int(d.get('max_calls', 12)), sig.get('handle'), files or None)


RUNNER = r'''
import builtins, functools, importlib, importlib.util, json, os, resource, signal, sys, types

_open = builtins.open                       # the runner's own files, whatever the code patches


def module(name):
    # The module the target lives in; a module the sandbox lacks (the
    # service's client library) is created empty, with its parents.
    try:
        return importlib.import_module(name)
    except ImportError:
        pass
    parts = name.split('.')
    for i in range(1, len(parts) + 1):
        n = '.'.join(parts[:i])
        if n in sys.modules:
            continue
        try:
            importlib.import_module(n)
        except ImportError:
            sys.modules[n] = types.ModuleType(n)
            if i > 1:
                setattr(sys.modules['.'.join(parts[:i - 1])], parts[i - 1], sys.modules[n])
    return sys.modules[name]


def owner(dotted):
    # What holds the last name of a dotted path: a module (created when the
    # sandbox lacks it), or a class in one (pathlib.Path.exists).
    parts = dotted.split('.')
    for i in range(len(parts) - 1, 0, -1):
        try:
            obj = importlib.import_module('.'.join(parts[:i]))
        except ImportError:
            continue
        try:
            for p in parts[i:-1]:
                obj = getattr(obj, p)
            return obj, parts[-1]
        except AttributeError:
            break
    return module('.'.join(parts[:-1])), parts[-1]


def exception(dotted):
    if '.' not in dotted:
        e = getattr(builtins, dotted, None)
        if not (isinstance(e, type) and issubclass(e, BaseException)):
            raise SystemExit('not an exception: %s' % dotted)
        return e
    mname, attr = dotted.rsplit('.', 1)
    m = module(mname)
    if not hasattr(m, attr):                   # a module the sandbox created: its exception too
        setattr(m, attr, type(attr, (Exception,), {'__module__': mname}))
    return getattr(m, attr)


MISSING = object()


class Handle:
    # What the code gets from a method that makes an object (a file from
    # open, a socket): the methods declared on it record; a with block
    # closes it as a real file does.
    def __init__(self, n, var, first):
        self._n, self._var, self._closed = n, var, False
        self.name = None if first is MISSING else first

    @property
    def closed(self):
        return self._closed

    def fileno(self):
        if self._closed:
            raise ValueError('I/O operation on closed file')
        return self._n

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        close = self.__dict__.get('close')
        if close is not None:
            close()
        return False

    def __repr__(self):
        return '<%s%d>' % (self._var, self._n)


def raw(v):
    # paths, bytes and tuples as the strings and lists design.yaml names
    if hasattr(v, '__fspath__'):
        v = os.fspath(v)
    if isinstance(v, bytes):
        try:
            v = v.decode()
        except UnicodeDecodeError:
            pass
    if isinstance(v, tuple):
        v = [raw(x) for x in v]
    return v


def open_mode(v):
    # 1 read, 2 write (truncate), 3 append, 4 create new; 0 anything else
    if not isinstance(v, str):
        return 0
    for c, k in (('x', 4), ('a', 3), ('w', 2), ('r', 1)):
        if c in v:
            return k
    return 0


def encode(a, v):
    # an argument as the integer its signal carries; None: not representable
    if v is MISSING:
        return None
    if isinstance(v, Handle):
        return v._n if a.get('handle') else None
    v = raw(v)
    if 'enum' in a:
        return 1 + a['enum'].index(v) if isinstance(v, (str, list)) and v in a['enum'] else 0
    if a.get('open_mode'):
        return open_mode(v)
    if a.get('parse') == 'int' and isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            return None
    return v if type(v) in (int, bool) else None


def show(a, v, made):
    if v is MISSING:
        return '?'
    if isinstance(v, Handle):
        return '%s%d' % (v._var, v._n)
    if a.get('handle') and type(v) is int and v in made:
        return '%s%d.fileno()' % (made[v]._var, v)
    if type(v) in (int, bool):
        return str(v)
    t = repr(v if isinstance(v, (bytes, tuple)) else raw(v))
    return t if len(t) <= 40 else t[:37] + '...'


def bind(m, a, kw):
    # declared arguments from the call: by position, by name, unnamed ones
    # from leftover keywords in order, else the default
    named = {x['name'] for x in m['args'] if x.get('name')}
    rest = [v for k, v in kw.items() if k not in named]
    vals = []
    for i, x in enumerate(m['args']):
        if i < len(a):
            v = a[i]
        elif x.get('name') in kw:
            v = kw[x['name']]
        elif not x.get('name') and rest:
            v = rest.pop(0)
        else:
            v = x.get('default', MISSING)
        vals.append(v)
    return vals


def main():
    src, fname, calls_path, out_path, spec, timeout = sys.argv[1:7]
    spec, timeout = json.loads(spec), float(timeout)
    try:
        resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
    except (ValueError, OSError):
        pass
    raises, rets = spec['raises'], spec['rets']
    other_exc, other_val = 1 + len(raises), 2 + len(raises)
    files = spec.get('files') or {}

    class Timeout(BaseException):
        pass

    class TooMany(BaseException):
        pass

    cur = {'events': [], 'used': 0, 'script': [], 'made': 0, 'exists': set(), 'objects': {}}
    reached = {}                               # method -> the methods of the objects it makes
    for m in spec['methods']:
        if m.get('via'):
            reached.setdefault(m['via'], []).append(m)

    def missing(m, vals):
        # removing or moving a file that is not there fails as it really would
        if m.get('fs') in ('remove', 'move') and vals and raw(vals[0]) not in cur['exists']:
            return FileNotFoundError(2, 'No such file or directory', raw(vals[0]))
        return None

    def effect(m, vals):
        ex, paths = cur['exists'], [raw(v) for v in vals]
        if m['fs'] == 'open' and paths and isinstance(paths[0], str):
            mode = next((v for x, v in zip(m['args'], vals) if x.get('open_mode')), 'r')
            if open_mode(mode) in (2, 3, 4):
                ex.add(paths[0])
        elif m['fs'] == 'remove' and paths:
            ex.discard(paths[0])
        elif m['fs'] == 'move' and len(paths) >= 2 and isinstance(paths[1], str):
            ex.discard(paths[0])
            ex.add(paths[1])

    def dispatcher(m):
        names = m.get('answers')
        raising = {k: exception(v) for k, v in (m.get('raises') or {}).items()}

        def call(*a, **kw):
            h = None
            if m.get('via'):
                h, a = a[0], a[1:]              # bound to its object below
            events = cur['events']
            if len(events) >= spec['max_calls']:
                raise TooMany()
            vals = bind(m, a, kw)
            err = missing(m, vals)
            if err is None and isinstance(h, Handle) and h._closed and m['name'] != 'close':
                err = ValueError('I/O operation on closed file.')
            ans = 0
            if names and err is None:
                k = cur['used']
                cur['used'] += 1
                ans = cur['script'][k] if k < len(cur['script']) else spec['default']
            name = spec['answers'][ans] if names and err is None else None
            failed = err is not None or name in raising
            made = None
            if m.get('handle') and not failed:
                cur['made'] += 1
                made = Handle(cur['made'], m.get('var', 'f'), vals[0] if vals else MISSING)
                cur['objects'][made._n] = made
                for x in reached.get(m['name'], []):
                    setattr(made, x['name'], functools.partial(calls[x['name']], made))
            hn = made._n if made is not None else (h._n if isinstance(h, Handle) else 0)
            events.append([m['op'], [encode(x, v) for x, v in zip(m['args'], vals)], ans,
                           [show(x, v, cur['objects']) for x, v in zip(m['args'], vals)], hn,
                           None if err is None else type(err).__name__])
            if err is not None:
                raise err
            if name in raising:
                raise raising[name](name)
            if m.get('fs'):
                effect(m, vals)
            if isinstance(h, Handle) and m['name'] == 'close':
                h._closed = True
            if made is not None:
                return made
            if not names:
                return None
            return name.encode() if m.get('bytes') else name
        return call

    calls = {m['name']: dispatcher(m) for m in spec['methods']}

    def exists(p, *a, **kw):
        return raw(p) in cur['exists']

    for m in spec['methods']:                  # effects the code does not receive: patched where it looks
        for p in m.get('patch') or []:
            obj, attr = owner(p)
            setattr(obj, attr, calls[m['name']])
    for q in files.get('query') or []:         # what the code asks about the files: the run's own
        obj, attr = owner(q)
        setattr(obj, attr, exists)
    if os.path.isdir(src):                  # a package: the entry module, by its dotted name
        sys.path.insert(0, os.path.abspath(src))
        mod = importlib.import_module(os.environ['FCP_ENTRY'])
    else:
        sys.path.insert(0, os.path.dirname(os.path.abspath(src)))
        sp = importlib.util.spec_from_file_location('fcp_impl', src)
        mod = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(mod)
    f = getattr(mod, fname)
    with _open(calls_path) as fh:
        runs = json.load(fh)

    def on_alarm(*_):
        raise Timeout()

    signal.signal(signal.SIGALRM, on_alarm)
    out = []
    for args, script in runs:
        cur.update(events=[], used=0, script=script, made=0, exists=set(files.get('exists') or []), objects={})
        stub = types.SimpleNamespace(**calls)  # a new one each run: nothing the code stores on it carries over
        full = list(args)
        if spec['position'] is not None:
            full.insert(spec['position'], stub)
        code, val, what = 0, None, None
        try:
            signal.setitimer(signal.ITIMER_REAL, timeout)
            r = f(*full)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except (Timeout, TooMany) as e:
            signal.setitimer(signal.ITIMER_REAL, 0)
            code, what = other_exc, 'no answer: more than %d calls or %gs' % (spec['max_calls'], timeout)
        except BaseException as e:
            signal.setitimer(signal.ITIMER_REAL, 0)
            name = type(e).__name__
            code = 1 + raises.index(name) if name in raises else other_exc
            if code == other_exc:
                what = ('%s: %s' % (name, e))[:200]
        else:
            kind, w = rets
            ok = (type(r) is bool) if kind == 'bool' else (type(r) is int and 0 <= r < (1 << w))
            if ok:
                val = r
            else:
                code, what = other_val, ('returned %r (%s)' % (r, type(r).__name__))[:200]
        out.append({'events': cur['events'], 'code': code, 'ret': val, 'what': what})
    with _open(out_path, 'w') as fh:
        json.dump(out, fh)

main()
'''


def run(fn: SW.Fn, ifc: Ifc, src: str, runs: list, timeout: float = 2.0, total: float = 1800) -> list[dict]:
    """Run src's function once per (arguments, script), each with a new stub."""
    spec = {'methods': ifc.methods, 'answers': ifc.answers, 'position': ifc.arg, 'max_calls': ifc.max_calls,
            'default': 0, 'raises': fn.raises, 'files': ifc.files,
            'rets': [fn.kinds.get(fn.rets[0], 'int'), fn.widths[fn.rets[0]]]}
    with tempfile.TemporaryDirectory(prefix='fcp_fx_') as d:
        cp, op, rp = os.path.join(d, 'runs.json'), os.path.join(d, 'out.json'), os.path.join(d, 'runner.py')
        with open(cp, 'w') as f:
            json.dump([[list(a), list(s)] for a, s in runs], f)
        with open(rp, 'w') as f:
            f.write(RUNNER)
        p = subprocess.run([SW.PY, '-I', rp, os.path.abspath(src), fn.name, cp, op, json.dumps(spec), str(timeout)],
                           capture_output=True, text=True, timeout=total, cwd=d,
                           env=SW.entry_env(fn))
        if p.returncode != 0 or not os.path.exists(op):
            err = (p.stderr.strip().splitlines() or ['no output'])[-1][:300]
            return [{'events': [], 'code': fn.other_exc, 'ret': None, 'what': err} for _ in runs]
        with open(op) as f:
            return json.load(f)


def scope(S, fn: SW.Fn, ifc: Ifc, seed: int = 1, small: bool = False) -> list[tuple]:
    """(arguments, script) pairs: every script of `length` answers over all
    the answers (shorter for small), random longer ones, each with every
    combination of argument values (constants of the readings and the
    prompt, their neighbours, the ends of the range), sampled above a cap."""
    cfg = fn.scope_cfg
    rng = random.Random(seed)
    n = len(ifc.answers)
    L = cfg.get('script', {}).get('length', 5)
    if small:
        L = min(L, 3)
    scripts = [tuple(t) for k in range(L + 1) for t in itertools.product(range(n), repeat=k)]
    for _ in range(0 if small else cfg.get('script', {}).get('random', 300)):
        scripts.append(tuple(rng.randrange(n) for _ in range(rng.randint(L + 1, ifc.max_calls))))
    vals = SW.scope(S, fn, small=True)
    names = [a for a, _, _ in fn.args]
    consts = SW.constants(S)
    picks = {}
    for a, sig, _ in fn.args:
        top = (1 << fn.widths[sig]) - 1
        if len(vals[a]) <= 12:
            picks[a] = vals[a]
            continue
        if cfg.get(a, {}).get('only') and cfg[a].get('values'):     # an identifier no rule reads
            picks[a] = sorted(set(cfg[a]['values']))
            continue
        # the configured values, else every constant of the readings and the
        # prompt with its neighbours; the ends of the range; a few at random
        cfgv = set(cfg.get(a, {}).get('values', []))
        near = {x for c in consts for x in (c - 1, c, c + 1) if 0 <= x <= top}
        picks[a] = sorted((cfgv or near) | {0, 1, top} | set(rng.sample(vals[a], 4)))
    combos = list(itertools.product(*[picks[a] for a in names]))
    out = [(c, sc) for c in combos for sc in scripts]
    cap = 6000 if small else 50000
    if len(out) > cap:
        out = rng.sample(out, cap)
    return out


def trace(fn: SW.Fn, ifc: Ifc, runs: list, res: list[dict]) -> tuple[dict, list[tuple]]:
    """Columns of the trace and, per cycle, (run index, event index or -1 for
    the return, or None for a reset)."""
    sigs = [sig for _, sig, _ in fn.args]
    ev_sigs = sorted({s for m in ifc.methods for s in arg_sigs(m)})
    hs = [ifc.handle] if ifc.handle else []
    cols: dict[str, list[int]] = {c: [] for c in ['rst_n', ifc.phase, ifc.op, ifc.answer, fn.outcome] +
                                  sigs + ev_sigs + hs + fn.rets}
    where: list = []
    htop = (1 << fn.widths[ifc.handle]) - 1 if ifc.handle else 0

    def cyc(rst, args, ph=0, op=0, ans=0, evargs=None, code=0, ret=0, at=None, hn=0):
        cols['rst_n'].append(rst)
        for h in hs:
            cols[h].append(min(hn, htop))
        for s, v in zip(sigs, args):
            cols[s].append(int(v))
        cols[ifc.phase].append(ph)
        cols[ifc.op].append(op)
        cols[ifc.answer].append(ans)
        for s in ev_sigs:
            cols[s].append((evargs or {}).get(s, 0))
        cols[fn.outcome].append(code)
        for r in fn.rets:
            cols[r].append(ret)
        where.append(at)
    by_op = {m['op']: m for m in ifc.methods}
    for i, ((args, script), r) in enumerate(zip(runs, res)):
        cyc(0, [0] * len(sigs))
        for k, e in enumerate(r['events']):
            op, a, ans = e[:3]
            m = by_op[op]
            ea = {s: (int(v) if isinstance(v, (int, bool)) and v is not None and 0 <= int(v) < (1 << fn.widths[s])
                      else 0) for s, v in zip(arg_sigs(m), a)}
            cyc(1, args, 0, op, ans if m.get('answers') else 0, ea, at=(i, k), hn=e[4] if len(e) > 4 else 0)
        ret = r['ret'] if r['code'] == 0 and r['ret'] is not None else 0
        cyc(1, args, 1, 0, 0, None, r['code'], int(ret), at=(i, -1))
    return cols, where


def conversation(fn: SW.Fn, ifc: Ifc, runs: list, res: list[dict], i: int, upto: Optional[int] = None) -> list[str]:
    """Run i as text: one line per interface call, then the return."""
    args, script = runs[i]
    by_op = {m['op']: m for m in ifc.methods}
    lines = []
    for k, e in enumerate(res[i]['events']):
        if upto is not None and upto != -1 and k > upto:
            break
        lines.append(event_text(ifc, e))
    if upto is None or upto == -1:
        r = res[i]
        lines.append('returns ' + (fn.fmt(fn.rets[0], r['ret']) if r['code'] == 0 else
                                   (r.get('what') or fn.outcome_name(r['code']))))
    return lines


def ifc_name(ifc: Ifc) -> str:
    return 'api'


def method_name(ifc: Ifc, m: dict, hn: int = 0) -> str:
    """How the code calls a method: api.charge, the patched name
    (time.sleep), or on the object it made (f1.write)."""
    if m.get('via'):
        maker = next(x for x in ifc.methods if x['name'] == m['via'])
        return f'{maker.get("var", "f")}{hn}.{m["name"]}'
    if m.get('patch'):
        p = m['patch'][0]
        return p[len('builtins.'):] if p.startswith('builtins.') else p
    return f'{ifc_name(ifc)}.{m["name"]}'


def event_text(ifc: Ifc, e: list) -> str:
    """One recorded call: f1 = open('a.tmp', 'w'), f1.write('120'),
    os.replace(...) -> "fail", os.remove('a.tmp') -> FileNotFoundError."""
    op, a, ans = e[:3]
    m = next(x for x in ifc.methods if x['op'] == op)
    shown = e[3] if len(e) > 3 else ['?' if x is None else str(x) for x in a]
    hn = e[4] if len(e) > 4 else 0
    err = e[5] if len(e) > 5 else None
    text = f'{method_name(ifc, m, hn)}({", ".join(shown)})'
    if m.get('handle') and hn:
        text = f'{m.get("var", "f")}{hn} = {text}'
    if err:
        return f'{text} -> {err}'
    return text + (f' -> "{ifc.answers[ans]}"' if m.get('answers') and not (m.get('handle') and hn) else '')


def _shown_args(ifc: Ifc, args) -> list[str]:
    shown = list(map(str, args))
    if ifc.arg is not None:
        shown.insert(ifc.arg, ifc_name(ifc))
    return shown


def call_text(fn: SW.Fn, ifc: Ifc, runs: list, i: int) -> str:
    args, script = runs[i]
    shown = _shown_args(ifc, args)
    return f'{fn.name}({", ".join(shown)}) with answers ' + \
        '[' + ', '.join(f'"{ifc.answers[x]}"' for x in script) + ']'


def verify(S, s: str, fn: SW.Fn, ifc: Ifc, src: str, runs: list, res: list[dict]) -> dict:
    """Every property of reading s on one implementation: PASS within the
    scope, or FAIL with the shortest failing conversation, replayed."""
    cols, where = trace(fn, ifc, runs, res)
    chk = SW.check(S, s, cols, keep=2000)
    mon = S.mon(s)
    out = {}
    for iid, r in chk.items():
        it = mon.items[iid]
        rec = {'req': it.req, 'role': it.role, 'runs': len(runs), 'count': r['count']}
        if it.role == 'scenario':
            rec['status'] = 'COVERED' if r['cov'] else 'NOT-COVERED'
        elif r['first'] is None:
            rec['status'] = 'PASS' if (r['trig'] is None or r['trig'] > 0) else 'VACUOUS'
            rec['triggered'] = r['trig']
        else:
            cands = [c for c in (r.get('fails') or [r['first']]) if where[c] is not None]
            c = min(cands, key=lambda c: (len(res[where[c][0]]['events']), len(runs[where[c][0]][1]), c))
            i, k = where[c]
            again = run(fn, ifc, src, [runs[i]])[0]
            same = again['events'] == res[i]['events'] and again['code'] == res[i]['code'] and \
                again['ret'] == res[i]['ret']
            rec.update(status='FAIL', triggered=r['trig'], call=call_text(fn, ifc, runs, i),
                       conversation=conversation(fn, ifc, runs, res, i, k),
                       replay='confirmed' if same else 'MISMATCH')
        out[iid] = rec
    return out


# ----------------------------------------------------------------------------
# before any code: scripts of answers on which no conversation meets the rules
# ----------------------------------------------------------------------------

def _script_constraints(spec, fn: SW.Fn, ifc: Ifc, script: tuple, k: int) -> list:
    """The answer at each cycle is the script's entry for the number of
    answering calls made before it (then the default answer), as the stub
    gives it, and 0 at every other cycle, as the trace records it.  (Left
    free there, the answer could break an assumption that bounds it at every
    cycle, and with it every later obligation: a conflict would be missed.)"""
    z3 = spec.z3
    w_op, w_ph, w_ans = fn.widths[ifc.op], fn.widths[ifc.phase], fn.widths[ifc.answer]
    answering = [m['op'] for m in ifc.methods if m.get('answers')]
    out = []
    count = z3.IntVal(0)
    for i in range(1, k + 1):
        op = spec.var('out', ifc.op, w_op, i)
        ph = spec.var('out', ifc.phase, w_ph, i)
        ans = spec.var('in', ifc.answer, w_ans, i)
        is_ans = z3.And(z3.Not(ph) if w_ph == 1 else ph == 0, z3.Or(*[op == o for o in answering]))
        expect = z3.IntVal(0)
        for j in range(len(script) - 1, -1, -1):
            expect = z3.If(count == j, z3.IntVal(script[j]), expect)
        val = z3.If(ans, z3.IntVal(1), z3.IntVal(0)) if w_ans == 1 else z3.BV2Int(ans)   # 1 bit: a Bool
        out.append(val == z3.If(is_ans, expect, z3.IntVal(0)))
        count = count + z3.If(is_ans, 1, 0)
    return out


def conflicts(S, s: str, fn: SW.Fn, ifc: Ifc, limit: int = 4, length: int = 4) -> dict:
    """Before any code: for every script of up to `length` answers and every
    combination of argument values in the small scope, does some
    conversation of at most max_calls calls meet every property?  If none
    does, every minimal conflicting set is listed (as for functions).  Sound,
    like every conflict search: no implementation can answer that script."""
    import time
    t0 = time.time()
    k = ifc.max_calls + 1
    ev = sorted({x for m in ifc.methods for x in arg_sigs(m)}) + ([ifc.handle] if ifc.handle else [])
    spec = SW._Spec(S, s, fn, k, extra_ins=[(ifc.answer, fn.widths[ifc.answer])],
                    extra_outs=[(x, fn.widths[x]) for x in [ifc.phase, ifc.op] + ev])
    z3, sol = spec.z3, spec.sol
    # arguments at the request's own boundaries: each constant of the readings
    # and the prompt with its neighbours, and the ends of the range
    consts = SW.constants(S, sets=[s])
    per = []
    for a, sig, kind in fn.args:
        top = (1 << fn.widths[sig]) - 1
        cfgv = set(fn.scope_cfg.get(a, {}).get('values', []))
        if kind == 'bool' or top == 1:
            per.append([0, 1])
            continue
        if cfgv and fn.scope_cfg[a].get('only'):        # an argument no rule reads: its configured values alone
            per.append(sorted(cfgv))
            continue
        near = sorted({x for c in consts for x in (c - 1, c, c + 1) if 0 <= x <= top})
        vs = {0, 1, top} | (cfgv or set(near[:4] + near[-4:]))      # the configured values, else a few constants
        per.append(sorted(vs))
    combos = list(itertools.product(*per))
    scripts = [tuple(t) for n in range(length + 1) for t in itertools.product(range(len(ifc.answers)), repeat=n)]
    cands = sorted(((c, sc) for c in combos for sc in scripts), key=lambda x: (len(x[1]), x[1], x[0]))
    found: dict[tuple, dict] = {}
    checked = 0

    def unsat(extra, sub):
        return sol.check(*[z3.Bool(x) for x in sub]) == z3.unsat
    for c, sc in cands:
        checked += 1
        extra = spec.fix([c] * k) + _script_constraints(spec, fn, ifc, sc, k)
        sol.push()
        sol.add(*extra)
        try:
            if sol.check(*spec.lits) != z3.unsat:
                continue
            # every minimal conflicting set (MARCO, as _Spec.muses)
            names_ = sorted(spec.sels)
            m = {x: z3.Bool(f'mapfx_{x}') for x in names_}
            mp = z3.Solver()
            muses = []
            while len(muses) < 32 and mp.check() == z3.sat:
                md = mp.model()
                seed = [x for x in names_ if not z3.is_false(md.eval(m[x], model_completion=False))]
                if unsat(extra, seed):
                    keep, i = list(seed), 0
                    while i < len(keep):
                        trial = keep[:i] + keep[i + 1:]
                        if unsat(extra, trial):
                            keep = trial
                        else:
                            i += 1
                    muses.append(sorted(spec.sels[x][1] for x in keep))
                    mp.add(z3.Or(*[z3.Not(m[x]) for x in keep]))
                else:
                    grow = list(seed)
                    for x in names_:
                        if x not in grow and not unsat(extra, grow + [x]):
                            grow.append(x)
                    mp.add(z3.Or(*[m[x] for x in names_ if x not in grow]))
        finally:
            sol.pop()
        key = tuple(tuple(x) for x in sorted(muses))
        if key in found:
            continue
        shown = _shown_args(ifc, c)
        found[key] = {'muses': sorted(muses), 'args': list(c), 'script': list(sc),
                      'stimulus': [f'{fn.name}({", ".join(shown)}) with answers [' +
                                   ', '.join(f'"{ifc.answers[x]}"' for x in sc) + ']'],
                      'reqs': sorted({S.mon(s).items[i].req for mu in muses for i in mu if S.mon(s).items[i].req})}
        if len(found) >= limit:
            break
    return {'conflicts': list(found.values()), 'candidates': len(cands), 'checked': checked,
            'seconds': round(time.time() - t0, 2)}
