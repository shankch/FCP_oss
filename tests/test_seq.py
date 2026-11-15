"""Strings and lists: FCP-PL sequences, their monitors and z3 encoding, and
the software adapter on corpus/code_mask and on a small list function."""
import os
import random
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_mask')
sys.path.insert(0, ROOT)

from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402
from fcp.lang import FcpTypeError, parse, unparse  # noqa: E402


@pytest.fixture(scope='module')
def S():
    return Session(B, sets=['gold'])


@pytest.fixture(scope='module')
def fn(S):
    return SW.function(S)


def test_syntax_round_trip():
    for src in ['all(i < len(s): s[i] != " ")', 'x in "abc"', "s[0] == 'a'", '[1, 2] == xs',
                'count(i < len(s): isdigit(s[i]) && i > 2) <= 4', 'sum(i < 3: xs[i]) % 3 == 0']:
        assert unparse(parse(unparse(parse(src)))) == unparse(parse(src))


# Python semantics of the properties, against the compiled monitor and the
# integer encoding, on random strings.
PROPS = {
    'P1': ('all(i < len(number): number[i] != " ")', lambda s, t: all(c != ' ' for c in s)),
    'P2': ('count(i < len(number): isdigit(number[i])) <= 2', lambda s, t: sum(c.isdigit() for c in s) <= 2),
    'P3': ('masked == number', lambda s, t: s == t),
    'P4': ('"a" in number', lambda s, t: 'a' in s),
    'P5': ('sum(i < len(number): isdigit(number[i]) ? number[i] - "0" : 0) % 3 == 0',
           lambda s, t: sum(int(c) for c in s if c.isdigit()) % 3 == 0),
    'P6': ('len(masked) == len(number) && all(i < len(number): masked[i] == (isdigit(number[i]) ? "*" : number[i]))',
           lambda s, t: t == ''.join('*' if c.isdigit() else c for c in s)),
    'P7': ('lower(number[0]) == "q" || len(number) == 0', lambda s, t: not s or s[0].lower() == 'q'),
    'P8': ('all(i < len(number) - 1: number[i] <= number[i + 1])', lambda s, t: list(s) == sorted(s)),
}


def _traces(n=300, seed=3):
    rng = random.Random(seed)
    al = 'ab1x9 Q*q'
    out = []
    for _ in range(n):
        s = ''.join(rng.choice(al) for _ in range(rng.randint(0, 8)))
        t = s if rng.random() < 0.3 else ''.join('*' if c.isdigit() else c for c in s) \
            if rng.random() < 0.5 else ''.join(rng.choice(al) for _ in range(rng.randint(0, 8)))
        if rng.random() < 0.2:
            s = ''.join(sorted(s))
        out.append((s, t))
    return out


@pytest.fixture(scope='module')
def probe(tmp_path_factory):
    """A copy of code_mask whose gold reading is the invariants above."""
    import shutil
    import yaml
    d = tmp_path_factory.mktemp('probe')
    for f in ('design.yaml', 'requirements.yaml', 'spec.md', 'frame.md'):
        shutil.copy(os.path.join(B, f), d / f)
    (d / 'formal').mkdir()
    fs = {'fcp': '0.1', 'set': 'gold', 'origin': {'kind': 'human', 'role': 'formalizer', 'id': 'gold'},
          'properties': [{'id': k, 'req': 'R-RET-1', 'pattern': 'invariant', 'args': {'cond': v[0]}}
                         for k, v in PROPS.items()]}
    (d / 'formal' / 'gold.yaml').write_text(yaml.safe_dump(fs, sort_keys=False))
    return Session(str(d), sets=['gold'])


def test_monitor_matches_python(probe):
    fn = SW.function(probe)
    tr = _traces()
    calls = [(s,) for s, _ in tr]
    res = {'code': [0] * len(tr), 'ret': {'masked': [t for _, t in tr]}}
    cols = SW.trace(fn, calls, res)
    for engine in ('verilator', 'icarus'):
        if engine == 'icarus':
            os.environ['FCP_ICARUS'] = '1'
        try:
            chk = SW.check(probe, 'gold', cols, keep=len(tr))
        finally:
            os.environ.pop('FCP_ICARUS', None)
        for k, (_, py) in PROPS.items():
            expect = {i + 1 for i, (s, t) in enumerate(tr) if not py(s, t)}
            got = set(chk[k]['fails']) if engine == 'verilator' else None
            assert chk[k]['count'] == len(expect), (engine, k)
            if got is not None:
                assert got == expect, k


def test_integer_encoding_matches_python(probe):
    """The z3 encoding of each property, evaluated on concrete strings."""
    import z3
    fn = SW.function(probe)
    enc = SW._IntSpec(probe, ['gold'], fn, 1, items=False)
    for s, t in _traces(60, seed=5):
        sub = []
        for sig, v in (('number', s), ('masked', t)):
            q = enc.x[(sig, 1)]
            cs = [ord(c) for c in v]
            sub += [(q.ln, z3.IntVal(len(cs)))] + [(e, z3.IntVal(cs[j] if j < len(cs) else 0))
                                                     for j, e in enumerate(q.el)]
        for k, (src, py) in PROPS.items():
            e = z3.simplify(z3.substitute(enc._b(enc._ex(parse(src), 1)), *sub))
            assert z3.is_true(e) == py(s, t), (k, s, t)


def test_type_errors():
    with pytest.raises(FcpTypeError):
        _compile('masked + 1 > 0')
    with pytest.raises(FcpTypeError):
        _compile('all(i < 1000: masked[i] == 1)')
    with pytest.raises(FcpTypeError):
        _compile('"ab" in number')


def _compile(cond):
    from fcp.monitor import build_monitor
    S = Session(B, sets=['gold'])
    fs = {'set': 'x', 'properties': [{'id': 'X', 'req': 'R-RET-1', 'pattern': 'invariant', 'args': {'cond': cond}}]}
    return build_monitor(S.b.iface, fs, 'mon_x')


# ----------------------------------------------------------------------------
# the adapter on code_mask

def test_reference_and_planted_bugs(S, fn):
    import yaml
    calls = SW.calls_for(S, fn, small=True)
    with open(os.path.join(B, 'bugs', 'bugs.yaml')) as f:
        bugs = {b['id']: b for b in yaml.safe_load(f)['bugs']}
    import importlib.util
    spec = importlib.util.spec_from_file_location('mask_build', os.path.join(B, 'build.py'))
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)              # by path: tests/test_code.py has a `build` of its own
    srcs = build.materialize()
    srcs['ref'] = os.path.join(B, 'impl', 'ref.py')
    for v in ('ref', 'C3', 'C7', 'C8', 'C9'):
        res = SW.run(fn, srcs[v], calls)
        out = SW.verify(S, 'gold', fn, srcs[v], calls, res, SW.trace(fn, calls, res))
        failing = {x['req'] for k, x in out.items() if x['status'] == 'FAIL'}
        assert all(x.get('replay', 'confirmed') == 'confirmed' for x in out.values())
        if v == 'ref' or v == 'C9':
            assert failing == {'R-QUARTER-1'}, v               # the prompt's own conflict, nothing else
        else:
            assert set(bugs[v]['violates']) <= failing, v


def test_conflict_before_code(S, fn):
    c = SW.conflicts(S, 'gold', fn, limit=1)
    assert c['conflicts'], c
    reqs = set(c['conflicts'][0]['reqs'])
    assert {'R-LAST4-1', 'R-QUARTER-1', 'R-RET-1'} == reqs
    (num,), = c['conflicts'][0]['calls']
    assert 12 <= sum(ch.isdigit() for ch in num) <= 15


# ----------------------------------------------------------------------------
# a list function, built from scratch

LIST_DESIGN = '''
fcp: '0.1'
design: dedupe
docs:
- {id: SPEC, path: spec.md}
interface:
  clock: clk
  reset: {name: rst_n, active_low: true, synchronous: true}
  signals:
  - {name: clk, dir: in, width: 1}
  - {name: rst_n, dir: in, width: 1}
  - {name: xs, dir: in, width: 4, length: 6}
  - {name: outcome, dir: out, width: 2}
  - {name: ys, dir: out, width: 4, length: 6}
environment: {initial_reset: true, reset_anytime: false, bmc_depth: 2, cover_depth: 2}
function:
  name: dedupe
  args: [{name: xs, signal: xs, type: list}]
  returns: {signal: ys, type: list}
  outcome: {signal: outcome, raises: [ValueError]}
  scope: {xs: {random: 300}}
'''
LIST_REQS = '''
fcp: '0.1'
design: dedupe
origin: {kind: human, id: gold, role: decomposer}
requirements:
- {id: R-1, doc: SPEC, lines: [1], quote: 'Remove duplicates, keeping the first of each, in order.', text: t, kind: guarantee}
'''
LIST_GOLD = '''
fcp: '0.1'
set: gold
origin: {kind: human, role: formalizer, id: gold}
properties:
- {id: G-RET, req: R-1, pattern: invariant, args: {cond: 'outcome == 0'}}
- {id: G-UNIQ, req: R-1, pattern: implies, args: {trigger: 'outcome == 0', cond: 'all(i < len(ys): all(j < i: ys[j] != ys[i]))'}}
- {id: G-SAME, req: R-1, pattern: implies, args: {trigger: 'outcome == 0', cond: 'all(i < len(xs): xs[i] in ys) && all(i < len(ys): ys[i] in xs)'}}
- {id: G-ORDER, req: R-1, pattern: implies, args: {trigger: 'outcome == 0', cond: 'all(i < len(ys) - 1: count(j < len(xs): xs[j] == ys[i] && all(k < j: xs[k] != ys[i + 1])) > 0)'}}
'''


def test_list_function(tmp_path):
    d = tmp_path / 'dedupe'
    (d / 'formal').mkdir(parents=True)
    (d / 'design.yaml').write_text(LIST_DESIGN)
    (d / 'requirements.yaml').write_text(LIST_REQS)
    (d / 'spec.md').write_text('Remove duplicates, keeping the first of each, in order.\n')
    (d / 'formal' / 'gold.yaml').write_text(LIST_GOLD)
    S = Session(str(d), sets=['gold'])
    fn = SW.function(S)
    good = tmp_path / 'good.py'
    good.write_text(textwrap.dedent('''
        def dedupe(xs):
            out = []
            for x in xs:
                if x not in out:
                    out.append(x)
            return out
    '''))
    bad = tmp_path / 'bad.py'
    bad.write_text('def dedupe(xs):\n    return sorted(set(xs))\n')
    tup = tmp_path / 'tup.py'
    tup.write_text('def dedupe(xs):\n    return tuple(dict.fromkeys(xs))\n')
    calls = SW.calls_for(S, fn, small=True)
    assert any(len(c[0]) >= 4 for c in calls)
    verdict = {}
    for name, src in (('good', good), ('bad', bad), ('tup', tup)):
        res = SW.run(fn, str(src), calls)
        out = SW.verify(S, 'gold', fn, str(src), calls, res, SW.trace(fn, calls, res))
        verdict[name] = {k: x['status'] for k, x in out.items()}
    assert set(verdict['good'].values()) == {'PASS'}
    assert verdict['bad']['G-ORDER'] == 'FAIL' and verdict['bad']['G-UNIQ'] == 'PASS'
    assert verdict['tup']['G-RET'] == 'FAIL'              # a tuple is not the list the signature promises


# ----------------------------------------------------------------------------
# a list beside a number, with whole lists as configured values

FITS_DESIGN = '''
fcp: '0.1'
design: fits
docs:
- {id: SPEC, path: spec.md}
interface:
  clock: clk
  reset: {name: rst_n, active_low: true, synchronous: true}
  signals:
  - {name: clk, dir: in, width: 1}
  - {name: rst_n, dir: in, width: 1}
  - {name: xs, dir: in, width: 4, length: 4}
  - {name: cap, dir: in, width: 6}
  - {name: outcome, dir: out, width: 2}
  - {name: ok, dir: out, width: 1}
environment: {initial_reset: true, reset_anytime: false, bmc_depth: 2, cover_depth: 2}
function:
  name: fits
  args: [{name: xs, signal: xs, type: list}, {name: cap, signal: cap, type: int}]
  returns: {signal: ok, type: bool}
  outcome: {signal: outcome, raises: []}
  scope: {xs: {random: 100, values: [[1, 2], [3, 2, 3]]}, cap: {values: [5, 9]}}
'''
FITS_REQS = '''
fcp: '0.1'
design: fits
origin: {kind: human, id: gold, role: decomposer}
requirements:
- {id: R-1, doc: SPEC, lines: [1], quote: 'True if the numbers sum to at most cap.', text: t, kind: guarantee}
'''
FITS_GOLD = '''
fcp: '0.1'
set: gold
origin: {kind: human, role: formalizer, id: gold}
properties:
- {id: G-RET, req: R-1, pattern: invariant, args: {cond: 'outcome == 0'}}
- {id: G-SUM, req: R-1, pattern: invariant, args: {cond: 'ok == (sum(i < len(xs): xs[i]) <= cap)'}}
'''


def test_a_list_beside_a_number_keeps_its_configured_lists(tmp_path):
    """HumanEval/72, will_it_fly(q, w): the example lists were configured
    values of q, and the integer scope of w took them for integers
    (TypeError: unhashable type: 'list') before any search began."""
    d = tmp_path / 'fits'
    (d / 'formal').mkdir(parents=True)
    (d / 'design.yaml').write_text(FITS_DESIGN)
    (d / 'requirements.yaml').write_text(FITS_REQS)
    (d / 'spec.md').write_text('True if the numbers sum to at most cap.\n')
    (d / 'formal' / 'gold.yaml').write_text(FITS_GOLD)
    S = Session(str(d), sets=['gold'])
    fn = SW.function(S)
    vals = SW.scope(S, fn, small=True)
    assert {5, 9} <= set(vals['cap']) and all(type(x) is int for v in vals.values() for x in v)
    calls = SW.calls_for(S, fn, small=True)
    assert {(1, 2), (3, 2, 3)} <= {tuple(c[0]) for c in calls}
    good = tmp_path / 'good.py'
    good.write_text('def fits(xs, cap):\n    return sum(xs) <= cap\n')
    bad = tmp_path / 'bad.py'
    bad.write_text('def fits(xs, cap):\n    return sum(xs) < cap\n')
    verdict = {}
    for name, src in (('good', good), ('bad', bad)):
        res = SW.run(fn, str(src), calls)
        out = SW.verify(S, 'gold', fn, str(src), calls, res, SW.trace(fn, calls, res))
        verdict[name] = {k: x['status'] for k, x in out.items()}
    assert set(verdict['good'].values()) == {'PASS'}
    assert verdict['bad'] == {'G-RET': 'PASS', 'G-SUM': 'FAIL'}
    assert not SW.conflicts(S, 'gold', fn, limit=1)['conflicts']
