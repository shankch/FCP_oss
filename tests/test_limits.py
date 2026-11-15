"""What the engine does with a reading that is too large, and what an agent's
launcher does with a command that is: found on HumanEval/49 (2^n modulo p),
where one reading's lint took 11 GB and the memory cap stopped the run, and
on HumanEval/46, where the scenario searches of one reading took 12 GB.
Later, on HumanEval/49 again: a constant of 65,537 bits that yosys could not
read, made by min(n, 28) typed with the range of n.  And on HumanEval/26:
definitions that each name the one before three times, which the integer
searches of a review walked and computed again at every use.  And on
HumanEval/144: a rule for every whole number q up to 10^28, of which the
integer encoding listed one instance per value.  And on HumanEval/26 again:
a rule for every value of a list element, over 256 values, which the
bit-level model of a comparison left out, so that a review asked about calls
on which the two readings agree.  And on HumanEval/46 again: a function with
no named exception, whose two-bit outcome signal has a code that names no
ending, on which alone two readings differed."""
import os
import re
import shutil
import signal
import subprocess
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_checkout')
sys.path.insert(0, ROOT)

from fcp.analyses import Session  # noqa: E402
from fcp.lang import BOOL, NUM, WIDE, FcpError, Sym, lookback, parse, vbits, vconst  # noqa: E402
from fcp.monitor import build_monitor  # noqa: E402


@pytest.fixture(scope='module')
def iface():
    return Session(B, sets=['gold']).b.iface


@pytest.fixture
def soon():
    """A test that would not end without the fix fails after a minute."""
    def late(sig, frame):
        raise TimeoutError('still running after 60 s')
    old = signal.signal(signal.SIGALRM, late)
    signal.alarm(60)
    yield
    signal.alarm(0)
    signal.signal(signal.SIGALRM, old)


def prop(cond, **kw):
    return dict({'id': 'P', 'req': 'R-RET-1', 'pattern': 'invariant', 'args': {'cond': cond}}, **kw)


def chain(n):
    """n definitions that each name the one before three times: 3^n paths."""
    defs = {'d0': 'subtotal'}
    for k in range(1, n + 1):
        defs[f'd{k}'] = f'd{k - 1} >= 3 ? d{k - 1} - 3 : d{k - 1}'
    return defs


def test_a_definition_is_measured_once(soon):
    syms = {'d0': Sym('d0', 'def', BOOL, node=parse('prev(x, 2)'))}
    for k in range(1, 201):
        syms[f'd{k}'] = Sym(f'd{k}', 'def', BOOL, node=parse(f'd{k - 1} + d{k - 1} + prev(d{k - 1})'))
    assert lookback(parse('d200'), syms) == 202
    assert lookback(parse('prev(d3) + d200'), syms) == 202
    syms['a'], syms['b'] = Sym('a', 'def', BOOL, node=parse('prev(b)')), Sym('b', 'def', BOOL, node=parse('prev(a)'))
    assert lookback(parse('a'), syms) == 2                 # a definition on the path is not followed again


def test_a_chain_of_definitions_compiles(iface, soon):
    m = build_monitor(iface, {'set': 'x', 'defs': chain(400), 'properties': [prop('d400 <= subtotal')]}, 'mon_x')
    assert 'ok_P' in m.outputs and len(m.text) < 400_000   # one wire per definition, not one per path


def test_a_definition_that_names_itself_is_an_error(iface, soon):
    for defs in ({'a': 'a + 1'}, {'a': 'b + 1', 'b': 'subtotal + a'}):
        with pytest.raises(FcpError, match='names itself'):
            build_monitor(iface, {'set': 'x', 'defs': defs, 'properties': [prop('a >= 0')]}, 'mon_x')


def test_rigid_cases_are_counted_not_listed(iface, soon):
    rigids = [{'name': f'w{k}', 'range': [0, 65534]} for k in range(32)]
    cond = ' && '.join(f'w{k} == subtotal' for k in range(32)) + ' -> price <= subtotal'
    m = build_monitor(iface, {'set': 'x', 'rigids': rigids, 'properties': [prop(cond)]}, 'mon_x')
    it = m.items['P']
    assert not it.det_available and 'about 10^154 rigid cases' in it.note
    with pytest.raises(FcpError, match=r'expands to about 10\^154 cases'):
        build_monitor(iface, {'set': 'x', 'rigids': rigids, 'assumptions': [
            {'id': 'A', 'req': 'R-RET-1', 'pattern': 'invariant', 'args': {'cond': cond}}]}, 'mon_x')
    small = build_monitor(iface, {'set': 'x', 'rigids': [{'name': 'w', 'range': [0, 3]}, {'name': 'v', 'range': [1, 2]}],
                                  'properties': [prop('w + v == subtotal -> price <= subtotal')]}, 'mon_x')
    assert small.items['P'].det_available and small.items['P'].out['okd'] == 'okd_P'


# ----------------------------------------------------------------------------
# the launcher of an agent

def launcher(body: str, **env) -> subprocess.CompletedProcess:
    code = (f'import sys\nsys.path.insert(0, {ROOT!r})\nfrom fcp import cli\n\n\nclass A:\n    cmd = "lint"\n\n\n'
            f'def fn(a):\n{body}\n\n\nsys.exit(cli.limited(fn, A()))\n')
    return subprocess.run([sys.executable, '-c', code], env={**os.environ, **env}, capture_output=True, text=True,
                          timeout=120)


def test_an_agent_command_is_stopped_at_its_memory_limit():
    r = launcher('    return len(bytearray(2 ** 30)) and 0', FCP_AGENT_MEM_GB='0.5')
    assert r.returncode == 3 and 'more than 0.5 GB of memory' in r.stderr and 'Traceback' not in r.stderr
    assert launcher('    return len(bytearray(2 ** 20)) and 0', FCP_AGENT_MEM_GB='0.5').returncode == 0
    assert launcher('    return 1', FCP_AGENT_MEM_GB='0.5').returncode == 1          # the command's own exit code


def test_an_agent_command_is_stopped_at_its_time_limit():
    r = launcher('    while True:\n        pass', FCP_AGENT_CPU_S='1')
    assert r.returncode == 3 and 'after 1 s of processor time' in r.stderr and 'Traceback' not in r.stderr


def test_the_limits_are_for_agents_only(tmp_path):
    """`fcp lint` of a user has no limit, whatever the variables say; with
    FCP_AGENT_WS it has, and says so in one line.

    The limit here is below what the interpreter already holds, so every
    allocation fails.  About one such run in a hundred does not reach the
    line: CPython 3.12 spins in its exception unwinding, and the kernel ends
    the command at the processor limit (see fcp.cli.limited)."""
    fcp = os.path.join(ROOT, 'bin', 'fcp')
    env = {k: v for k, v in os.environ.items() if not k.startswith('FCP_AGENT')}
    tiny = {'FCP_AGENT_MEM_GB': '0.01', 'FCP_AGENT_CPU_S': '5'}
    assert subprocess.run([fcp, 'lint', B], env={**env, **tiny}, capture_output=True, text=True,
                          timeout=300).returncode == 0
    r = subprocess.run([fcp, 'lint', B], env={**env, **tiny, 'FCP_AGENT_WS': B}, capture_output=True, text=True,
                       timeout=300)
    told = r.returncode == 3 and r.stderr.startswith('fcp: lint was stopped: it needs more than 0.01 GB')
    assert told or r.returncode == -signal.SIGKILL, (r.returncode, r.stderr[-300:])


def test_a_comparison_of_readings_stops_at_its_budget(monkeypatch):
    """A review gives one comparison of two readings a time (COMPARE_BUDGET).
    With none left, every direction stays undecided and the search is named
    among those cut short; without a budget the same comparison decides."""
    from fcp import software as SW
    S = Session(B, sets=['gold', 'agent_a'])
    fn = SW.function(S)
    free = SW.compare(S, 'gold', 'agent_a', fn, bit_timeout=0)
    both = [r for r, x in free.items() if x['relation'] not in ('ONLY-A', 'ONLY-B')]
    assert both and all(free[r]['relation'] != 'UNKNOWN' for r in both)
    monkeypatch.setattr(SW, 'BUDGET_HIT', [])
    monkeypatch.setattr(SW, 'COMPARE_BUDGET', 3600)
    timed = SW.compare(S, 'gold', 'agent_a', fn, bit_timeout=0)        # time enough: the same relations
    assert {r: x['relation'] for r, x in timed.items()} == {r: x['relation'] for r, x in free.items()}
    assert SW.BUDGET_HIT == []
    monkeypatch.setattr(SW, 'COMPARE_BUDGET', 0)
    cut = SW.compare(S, 'gold', 'agent_a', fn, bit_timeout=0)
    assert all(cut[r]['relation'] == 'UNKNOWN' for r in both)
    assert SW.BUDGET_HIT == ['the comparison of gold and agent_a']


def test_what_a_plain_comparison_closed_is_not_asked_again_in_context(monkeypatch):
    """Found on a review started from a Claude Code session: six requirements
    whose two readings the plain comparison had shown equal came back
    undecided.  The comparison in context asks more of the solver, ran out
    of time, and its result alone was used.  A call that separates two
    readings in context separates them without context (fewer rules have to
    hold), so a direction without a disagreement there has none in context.
    Given the plain result, the comparison in context does not ask such a
    direction again, lists it under 'carried', and returns the relations of
    a comparison that asks everything.  With no time at all it still knows
    them."""
    from fcp import software as SW
    S = Session(B, sets=['gold', 'agent_a'])
    fn = SW.function(S)
    plain = SW.compare(S, 'gold', 'agent_a', fn, bit_timeout=0)
    full = SW.compare(S, 'gold', 'agent_a', fn, context=True, bit_timeout=0)
    closed = {'EQUIVALENT': list(SW.WITNESSES), 'A-STRONGER': ['witness_a_not_b'], 'A-WEAKER': ['witness_b_not_a']}
    want = {r: closed[x['relation']] for r, x in plain.items() if x['relation'] in closed}
    assert sorted(len(v) for v in want.values()) == [1, 1, 1, 1, 1, 2, 2, 2]     # five stronger, three equal
    asked = []
    split = SW._IntSpec.split

    def counted(self, acc, rej, req, context, timeout=60000):
        asked.append((req, 'witness_a_not_b' if acc == 'gold' else 'witness_b_not_a'))
        return split(self, acc, rej, req, context, timeout)

    monkeypatch.setattr(SW._IntSpec, 'split', counted)
    got = SW.compare(S, 'gold', 'agent_a', fn, context=True, bit_timeout=0, plain=plain)
    assert {r: x['relation'] for r, x in got.items()} == {r: x['relation'] for r, x in full.items()}
    assert {r: x['carried'] for r, x in got.items() if 'carried' in x} == want
    assert sorted(asked) == sorted((r, k) for r, x in full.items() if x['relation'] not in ('ONLY-A', 'ONLY-B')
                                   for k in SW.WITNESSES if k not in want.get(r, []))
    assert len(asked) == 5                                    # of 16: the open direction of the five
    assert all(got[r]['engine'] == plain[r]['engine'] for r, v in want.items() if len(v) == 2)
    # what a review keeps when this comparison fails as a step (review.check): the records that ask nothing
    known = SW.carried_over(plain)
    assert set(known) == {r for r, x in plain.items() if x['relation'] in ('ONLY-A', 'ONLY-B')} | \
        {r for r, v in want.items() if len(v) == 2}
    assert all(got[r] == known[r] for r in known)
    # the other way round nothing follows: without context every direction is asked
    asked.clear()
    again = SW.compare(S, 'gold', 'agent_a', fn, bit_timeout=0, plain=full)
    assert {r: x['relation'] for r, x in again.items()} == {r: x['relation'] for r, x in plain.items()}
    assert len(asked) == 16 and not [r for r, x in again.items() if 'carried' in x]
    # no time at all: what was closed is known, the rest is undecided, and the search is named
    monkeypatch.setattr(SW, 'BUDGET_HIT', [])
    monkeypatch.setattr(SW, 'COMPARE_BUDGET', 0)
    cut = SW.compare(S, 'gold', 'agent_a', fn, context=True, bit_timeout=0, plain=plain)
    assert {r for r, x in cut.items() if x['relation'] == 'EQUIVALENT'} == {r for r, v in want.items() if len(v) == 2}
    assert all(cut[r]['relation'] == 'UNKNOWN' for r, v in want.items() if len(v) == 1)
    assert SW.BUDGET_HIT == ['the comparison of gold and agent_a, in context']       # which of the two it was
    # ... and each undecided record says which of its directions was closed
    assert all(cut[r]['status'] == {'witness_a_not_b': 'none', 'witness_b_not_a': 'unknown'}
               and SW.closed(cut[r]) == ('witness_a_not_b',) for r, v in want.items() if len(v) == 1)
    assert all(cut[r] == known[r] for r in known)               # with no time at all, the same records


def test_an_undecided_record_still_carries_the_direction_it_closed(monkeypatch):
    """A comparison's record says what each direction found ('status').  A
    plain comparison that did not end in one direction of a requirement
    reports UNKNOWN there, and the other direction is closed all the same:
    the comparison in context does not ask that one again.  The same holds
    for a record whose call was not shown, and a record written before the
    status was is read by its relation."""
    from fcp import software as SW
    S = Session(B, sets=['gold', 'agent_a'])
    fn = SW.function(S)
    plain = SW.compare(S, 'gold', 'agent_a', fn, bit_timeout=0)
    full = SW.compare(S, 'gold', 'agent_a', fn, context=True, bit_timeout=0)
    a_b, b_a = SW.WITNESSES
    name = {('none', 'none'): 'EQUIVALENT', ('none', 'witness'): 'A-STRONGER', ('witness', 'none'): 'A-WEAKER',
            ('witness', 'witness'): 'INCOMPARABLE'}
    both = [r for r, x in plain.items() if x['relation'] not in ('ONLY-A', 'ONLY-B')]
    for recs in (plain, full):
        for r in both:
            st = recs[r]['status']
            assert recs[r]['relation'] == name[st[a_b], st[b_a]]
            assert SW.closed(recs[r]) == tuple(k for k in SW.WITNESSES if st[k] == 'none')
        assert all('status' not in x and SW.closed(x) == () for r, x in recs.items() if r not in both)
    # the plain comparison as it is when the second direction of the equal requirements did not end
    equal = [r for r in both if plain[r]['relation'] == 'EQUIVALENT']
    assert len(equal) == 3
    half = {r: {**x, 'relation': 'UNKNOWN', 'status': {a_b: 'none', b_a: 'unknown'}} if r in equal else x
            for r, x in plain.items()}
    asked = []
    split = SW._IntSpec.split

    def counted(self, acc, rej, req, context, timeout=60000):
        asked.append((req, a_b if acc == 'gold' else b_a))
        return split(self, acc, rej, req, context, timeout)

    monkeypatch.setattr(SW._IntSpec, 'split', counted)
    got = SW.compare(S, 'gold', 'agent_a', fn, context=True, bit_timeout=0, plain=half)
    assert {r: x['relation'] for r, x in got.items()} == {r: x['relation'] for r, x in full.items()}
    assert all(got[r]['carried'] == [a_b] and got[r]['status'] == {a_b: 'none', b_a: 'none'} for r in equal)
    assert sorted(k for r, k in asked if r in equal) == [b_a] * 3 and len(asked) == 8      # the 5 of the full carry, and these
    # a record without a status is read by its relation
    assert SW.closed({'relation': 'EQUIVALENT'}) == SW.WITNESSES
    assert SW.closed({'relation': 'A-STRONGER'}) == (a_b,) and SW.closed({'relation': 'A-WEAKER'}) == (b_a,)
    assert all(SW.closed(x) == () for x in ({'relation': 'INCOMPARABLE'}, {'relation': 'UNKNOWN'}, {'relation': 'ONLY-A'},
                                            {'relation': 'NO-CONTEXT', 'status': {a_b: 'none', b_a: 'none'}}, {}, None))
    # a call that is not shown leaves its own direction undecided, and the other as it was found
    rec = {'relation': 'A-STRONGER', 'status': {a_b: 'none', b_a: 'witness'}, b_a: {'lines': ['f(1) -> 2']}}
    kept = SW.unshown({'R-X': rec}, 'the replay did not end')['R-X']
    assert kept['relation'] == 'UNKNOWN' and kept['status'] == {a_b: 'none', b_a: 'unknown'}
    assert SW.closed(kept) == (a_b,) and rec['status'][b_a] == 'witness'


def test_what_the_plain_comparison_alone_says_about_the_one_in_context():
    """A review whose comparison in context did not end keeps what follows
    from the plain one alone (review.check): the record of a requirement
    with both directions closed, which `compare` in context writes without
    asking anything, and the record of a requirement that one reading alone
    states.  Nothing follows for a requirement with a direction that is not
    closed, or with no context to compare in."""
    import copy
    from fcp import software as SW
    a_b, b_a = SW.WITNESSES
    call = {'calls': [[7, 0, 0]], 'lines': ['checkout(7, 0, 0) -> 7, 0']}
    plain = {'R-1': {'relation': 'EQUIVALENT', 'status': {a_b: 'none', b_a: 'none'}, 'k': 2, 'exact': True,
                     'engine': 'z3-int+bit', 'scope_check': {b_a: {'calls': 3, 'separated': False, 'bit': 'none'}}},
             'R-2': {'relation': 'A-STRONGER', 'status': {a_b: 'none', b_a: 'witness'}, 'k': 2, 'exact': True,
                     'engine': 'z3-int', b_a: call},
             'R-3': {'relation': 'UNKNOWN', 'status': {a_b: 'none', b_a: 'unknown'}, 'k': 2, 'exact': True,
                     'engine': 'z3-int'},
             'R-4': {'relation': 'INCOMPARABLE', 'status': {a_b: 'witness', b_a: 'witness'}, 'k': 2, 'exact': True,
                     'engine': 'z3-int', a_b: call, b_a: call},
             'R-5': {'relation': 'ONLY-B', 'k': 2, 'exact': True},
             'R-6': {'relation': 'EQUIVALENT'},                    # written before the status was
             'R-7': {'relation': 'NO-CONTEXT', 'status': {a_b: 'none', b_a: 'none'}},
             '<assumptions>': {'relation': 'EQUIVALENT'}}
    keep = copy.deepcopy(plain)
    known = SW.carried_over(plain)
    assert known == {
        'R-1': {'relation': 'EQUIVALENT', 'status': {a_b: 'none', b_a: 'none'}, 'k': 2, 'exact': True,
                'engine': 'z3-int+bit', 'carried': [a_b, b_a]},
        'R-5': {'relation': 'ONLY-B', 'k': 2, 'exact': True},
        'R-6': {'relation': 'EQUIVALENT', 'status': {a_b: 'none', b_a: 'none'}, 'engine': '', 'carried': [a_b, b_a]}}
    assert plain == keep and known['R-5'] is not plain['R-5']       # plain is left as it is
    assert not SW.shows(known)                                      # no call: nothing to run again
    assert all(SW.closed(x) == SW.WITNESSES for r, x in known.items() if r != 'R-5')
    assert SW.carried_over({}) == {}


def test_a_record_says_what_each_engine_found_in_each_direction(monkeypatch):
    """The status of a record is what the last engine asked in a direction
    found there: the integer encoding, a call of the scope, the bit level.
    A direction that did not end, or whose call the monitors do not confirm,
    is 'unknown' and shows no call, and the other direction stays closed: a
    plain record of this kind, as compare itself writes it, is carried into
    the comparison in context.  Where the monitors ran the call of an
    encoding and refuted it, the encoding and the monitors disagree on that
    requirement: the record says so ('refuted') and closes nothing, so
    nothing of it is carried.  On stubs: no session, no solver, no process."""
    import concurrent.futures
    import types
    from fcp import software as SW
    a_b, b_a = SW.WITNESSES
    reqs = ['R-BIT', 'R-BITCALL', 'R-BITREF', 'R-HALF', 'R-REFUTED', 'R-SCOPE', 'R-UNCONF']
    S = types.SimpleNamespace(b=types.SimpleNamespace(frame_ids=set(), root='/none'), props=lambda s: [
        types.SimpleNamespace(id=f'{s}-{r}', req=r, out={'okd': 'okd'}) for r in reqs])
    call, asked = {'calls': [(1,)], 'outs': [{'y': 2}]}, []
    open_, found = ('unknown', None), ('witness', call)
    ints = {('R-HALF', b_a): open_, ('R-UNCONF', a_b): found, ('R-SCOPE', b_a): open_, ('R-BIT', a_b): open_,
            ('R-BIT', b_a): open_, ('R-BITCALL', a_b): open_, ('R-BITREF', a_b): open_, ('R-REFUTED', a_b): found}
    bits = {('R-BIT', a_b): ('none', None), ('R-BITCALL', a_b): ('witness', call), ('R-BITREF', a_b): ('witness', call)}

    def key(acc):
        return a_b if acc == 'a' else b_a

    class Enc:
        by_sweep = set()

        def __init__(self, *a, **kw):
            pass

        def split(self, acc, rej, req, context, timeout=60000):
            asked.append((req, key(acc)))
            return ints.get((req, key(acc)), ('none', None))

    class Spec:
        sol = types.SimpleNamespace(set=lambda *a: None)

        def __init__(self, *a, **kw):
            pass

    class Pool:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def map(self, f, jobs):
            return [bits.get((j[5], key(j[3])), ('unknown', None)) for j in jobs]

    def on_scope(S, spec, fn, acc, rej, req, context, over=None):
        found = (req, key(acc)) == ('R-SCOPE', b_a)
        return {'calls': 200, 'witness': {'calls': [[7]], 'lines': ['f(7) -> 0']} if found else None}

    def confirm(S, fn, w, acc, rej, req, context, ran=None):
        if req in ('R-REFUTED', 'R-BITREF'):             # both replays ran, and they contradict the encoding
            ran.append(True)
        return req == 'R-BITCALL'                        # R-UNCONF: more values than a replay lists

    def seen(recs):
        return {r: (x['relation'], x['status'][a_b], x['status'][b_a], SW.closed(x),
                    [k for k in SW.WITNESSES if k in x]) for r, x in recs.items()}

    monkeypatch.setattr(SW, 'BUDGET_HIT', [])
    monkeypatch.setattr(SW, 'COMPARE_BUDGET', None)
    monkeypatch.setattr(SW, 'horizon', lambda S, sets: (1, True))
    monkeypatch.setattr(SW, '_IntSpec', Enc)
    monkeypatch.setattr(SW, '_Spec', Spec)
    monkeypatch.setattr(SW, 'scope_separation', on_scope)
    monkeypatch.setattr(SW, '_confirm', confirm)
    monkeypatch.setattr(SW, 'line', lambda fn, c, o: f'f({c[0]}) -> {o["y"]}')
    monkeypatch.setattr(concurrent.futures, 'ProcessPoolExecutor', Pool)
    # without the bit level: a direction did not end, a call was not confirmed or was refuted, a call is of the scope
    plain = SW.compare(S, 'a', 'b', None, bit_timeout=0)
    assert seen(plain) == {'R-BIT': ('UNKNOWN', 'unknown', 'unknown', (), []),
                           'R-BITCALL': ('UNKNOWN', 'unknown', 'none', (b_a,), []),
                           'R-BITREF': ('UNKNOWN', 'unknown', 'none', (b_a,), []),
                           'R-HALF': ('UNKNOWN', 'none', 'unknown', (a_b,), []),
                           'R-REFUTED': ('UNKNOWN', 'unknown', 'none', (), []),
                           'R-SCOPE': ('A-STRONGER', 'none', 'witness', (a_b,), [b_a]),
                           'R-UNCONF': ('UNKNOWN', 'unknown', 'none', (b_a,), [])}
    assert [r for r, x in plain.items() if x.get('refuted')] == ['R-REFUTED']
    assert plain['R-SCOPE'][b_a] == {'calls': [[7]], 'lines': ['f(7) -> 0'], 'from': 'scope'}
    # in context the closed direction of each is carried, also of the undecided ones, and only the rest is asked;
    # of the refuted record nothing is carried and both directions are asked
    asked.clear()
    ctx = SW.compare(S, 'a', 'b', None, context=True, bit_timeout=0, plain=plain)
    assert {r: x.get('carried') for r, x in ctx.items()} == {
        'R-BIT': None, 'R-BITCALL': [b_a], 'R-BITREF': [b_a], 'R-HALF': [a_b], 'R-REFUTED': None, 'R-SCOPE': [a_b],
        'R-UNCONF': [b_a]}
    assert sorted(asked) == [('R-BIT', a_b), ('R-BIT', b_a), ('R-BITCALL', a_b), ('R-BITREF', a_b), ('R-HALF', b_a),
                             ('R-REFUTED', a_b), ('R-REFUTED', b_a), ('R-SCOPE', b_a), ('R-UNCONF', a_b)]
    assert seen(ctx)['R-HALF'] == ('UNKNOWN', 'none', 'unknown', (a_b,), [])
    assert seen(ctx)['R-REFUTED'] == ('UNKNOWN', 'unknown', 'none', (), []) and ctx['R-REFUTED']['refuted'] is True
    # with the bit level: what it finds in a direction is written for that direction
    deep = SW.compare(S, 'a', 'b', None, bit_timeout=300)
    assert seen(deep)['R-BIT'] == ('UNKNOWN', 'none', 'unknown', (a_b,), [])
    assert seen(deep)['R-BITCALL'] == ('A-WEAKER', 'witness', 'none', (b_a,), [a_b])
    assert seen(deep)['R-BITREF'] == ('UNKNOWN', 'unknown', 'none', (), [])        # a call of the bit level, refuted
    assert [r for r, x in deep.items() if x.get('refuted')] == ['R-BITREF', 'R-REFUTED']
    # ... and a call of it that could not be replayed leaves its direction undecided and the other as it was
    monkeypatch.setattr(SW, '_confirm', lambda *a: False)
    last = SW.compare(S, 'a', 'b', None, bit_timeout=300)
    assert seen(last)['R-BITCALL'] == ('UNKNOWN', 'unknown', 'none', (b_a,), []) and 'refuted' not in last['R-BITCALL']


def test_a_review_bounds_its_engine_tasks(monkeypatch):
    """A review starts at most `jobs` engine tasks at a time.  With a
    session's own default (24) the twelve scenario searches of one reading of
    HumanEval/46, 1 GB each, ran together and met the 8 GB cap of the check."""
    from fcp import analyses as AN, review as RV, software as SW
    for name in ('SCOPE_BUDGET', 'CONFLICT_BUDGET', 'COMPARE_BUDGET'):       # check sets them: put back afterwards
        monkeypatch.setattr(SW, name, getattr(SW, name))
    seen = []

    class Stop(Exception):
        pass

    class Spy(AN.Session):
        def __post_init__(self):
            seen.append(self.jobs)
            raise Stop

    monkeypatch.setattr(AN, 'Session', Spy)
    for kw in ({}, {'jobs': 3}):
        with pytest.raises(Stop):
            RV.check(B, None, ['gold', 'agent_a'], **kw)
    assert seen == [RV.JOBS, 3] and RV.JOBS <= 8


@pytest.fixture(scope='module')
def examples(tmp_path_factory):
    """The checkout bundle with a reading of one rule and three examples: one
    that can happen, one the rule forbids, one that is impossible in itself."""
    import shutil
    b = tmp_path_factory.mktemp('examples') / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    (b / 'formal' / 't.yaml').write_text(textwrap.dedent('''
        fcp: "0.1"
        set: t
        origin: {kind: human, role: formalizer, id: t}
        properties:
          - {id: T-P, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal >= 6', cond: 'outcome == 0 && price == subtotal && ship == 0'}}
          - {id: T-Q, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal < 6', cond: 'outcome == 1'}}
        scenarios:
          - {id: S-OK, req: R-EX-1, cover: 'subtotal == 7 && outcome == 0 && price == 7'}
          - {id: S-NO, req: R-EX-1, cover: 'subtotal == 7 && outcome == 0 && price == 3'}
          - {id: S-X, req: R-EX-1, cover: 'subtotal == 7 && subtotal == 8'}
    '''))
    return Session(str(b), sets=['t'])


def test_a_review_searches_the_scenarios_only(examples):
    """A review takes the scenarios from the consistency search and nothing
    else, so it starts no other search: the same verdict for each scenario."""
    from fcp import review as RV
    full = examples.consistency('t', pairs=False)
    only = examples.consistency('t', pairs=False, scenarios_only=True)
    assert (full['situations'], only['situations']) == (6, 3)        # two triggers, three scenarios, progress
    want = {'impossible': ['S-X'], 'forbidden': ['S-NO'], 'blocked': [], 'undecided': []}
    assert RV.scenarios(full) == want and RV.scenarios(only) == want


def test_a_scenario_search_that_did_not_end_settles_nothing(examples):
    """A scenario whose search did not end is no question and no settled
    requirement; one the rules exclude is a question, also when the search
    that says why did not end."""
    from fcp import review as RV
    cons = {'blocked': ['scenario(S-NO)', 'scenario(S-X)', 'trig(T-P)'], 'impossible_scenarios': [],
            'forbidden_scenarios': ['S-NO'], 'undecided': ['scenario(S-OK)', 'progress'], 'conflicts': []}
    sc = RV.scenarios(cons)
    assert sc == {'impossible': [], 'forbidden': ['S-NO'], 'blocked': ['S-X'], 'undecided': ['S-OK']}
    assert RV.scenarios({**cons, 'conflicts': [{'situations': ['scenario(S-X)']}]})['blocked'] == []

    def verdicts(sc):
        out = {'sets': ['t'], 'prompt': {'t': {'conflicts': {'conflicts': []}, 'open': {'open': {}}}},
               'readings': {}, 'scenarios': {'t': sc}}
        settled, queue = RV.verdicts(examples, out)
        return 'R-EX-1' in settled, [q['question'] for q in queue if q['kind'] == 'scenario']

    none = {'impossible': [], 'forbidden': [], 'blocked': [], 'undecided': []}
    assert verdicts(none) == (True, [])
    assert verdicts({**none, 'undecided': ['S-OK']}) == (False, [])
    settled, asked = verdicts({**none, 'blocked': ['S-X']})
    assert not settled and len(asked) == 1 and asked[0].startswith('the behaviour S-X describes can never happen')
    assert 'did not end' in asked[0]
    assert verdicts({'impossible': [], 'forbidden': []}) == (True, [])        # a review written before: as it was


def test_min_and_max_keep_the_narrower_range():
    """min(n, 28) is at most 28.  Typed by the wider of its two operands it
    made 1 << min(n, 28) a value of 65,537 bits on HumanEval/49, whose
    constant yosys could not read."""
    iface = Session(B, sets=['gold']).b.iface
    m = build_monitor(iface, {'set': 'x', 'defs': {'pw': '1 << min(subtotal, 28)'},
                              'properties': [prop('pw >= 1 && max(subtotal, 5) >= 5')]}, 'mon_x')
    assert max(map(len, m.text.split('\n'))) < 400 and 'signed [29:0]' in m.text


def test_a_wide_constant_is_written_in_pieces():
    def bits(text):
        out = ''
        for p in text[1:-1].split(', '):
            run, lit = re.fullmatch(r"\{(\d+)\{1'b([01])\}\}", p), re.fullmatch(r"(\d+)'b([01]+)", p)
            assert run or len(lit.group(2)) == int(lit.group(1)) <= WIDE
            out += run.group(2) * int(run.group(1)) if run else lit.group(2)
        return out

    assert vbits(5, 8) == "8'b00000101" and vbits(1, WIDE).startswith(f"{WIDE}'b0")     # as before
    for w in (WIDE + 1, 5002, 65537):
        for v in (0, 1, 1 << (w - 2), (1 << w) - 1, 0x5a5a << (w - 20), (0xfeed << max(0, w - 4104)) | 0xbeef):
            text = vbits(v, w)
            assert len(bits(text)) == w and int(bits(text), 2) == v
            assert max(map(len, re.findall(r'[01]+', text))) <= WIDE
    wide = NUM(-(1 << 5000), 1 << 5000)
    assert vconst(-1, wide) == '$signed({' + ', '.join(["{4096{1'b1}}", "{906{1'b1}}"]) + '})'


@pytest.fixture(scope='module')
def ranges(tmp_path_factory):
    b = tmp_path_factory.mktemp('ranges') / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    (b / 'formal' / 't.yaml').write_text(textwrap.dedent('''
        fcp: "0.1"
        set: t
        origin: {kind: human, role: formalizer, id: t}
        defs:
          pw: "1 << min(subtotal, 28)"
          far: "1 << min(subtotal, 5000)"
        properties:
          - {id: T-P, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal >= 6', cond: 'outcome == 0'}}
        scenarios:
          - {id: S-A, req: R-EX-1, cover: 'subtotal == 7 && min(subtotal, 28) == 7 && max(subtotal, 28) == 28 && pw == 128'}
          - {id: S-B, req: R-EX-1, cover: 'subtotal == 40 && min(subtotal, 28) == 28 && max(subtotal, 28) == 40 && pw == (1 << 28)'}
          - {id: S-C, req: R-EX-1, cover: 'subtotal == 7 && min(subtotal - 10, 5) == -3 && max(subtotal - 10, 5 - subtotal) == -2'}
          - {id: S-D, req: R-EX-1, cover: 'subtotal == 4100 && far == (1 << 4100)'}
          - {id: X-A, req: R-EX-1, cover: 'subtotal == 40 && min(subtotal, 28) == 40'}
          - {id: X-B, req: R-EX-1, cover: 'subtotal == 7 && max(subtotal, 28) == 7'}
          - {id: X-C, req: R-EX-1, cover: 'subtotal == 4100 && far == (1 << 4099)'}
    '''))
    return Session(str(b), sets=['t'])


def test_min_max_and_wide_constants_mean_what_they_say(ranges):
    """Through yosys and the solver: the narrowed min and max and a constant
    of 5,002 bits written in two pieces have the values the formulas say."""
    from fcp import review as RV
    sc = RV.scenarios(ranges.consistency('t', pairs=False, scenarios_only=True))
    assert sc == {'impossible': ['X-A', 'X-B', 'X-C'], 'forbidden': [], 'blocked': [], 'undecided': []}


# ----------------------------------------------------------------------------
# the integer searches of a review

def test_a_walk_visits_a_definition_once(soon):
    """HumanEval/26: eight definitions that each name the one before three
    times.  The walk for the names a formula uses went into a definition at
    every use: 3^n walks, and forty definitions would not end."""
    from fcp import software as SW
    defs = {n: parse(b) for n, b in chain(40).items()}
    seen = list(SW._walk(parse('d40 <= subtotal'), defs))
    assert len(seen) == 3 + 40 * 8 + 1
    assert {x.val for x in seen if x.op == 'ref'} == set(defs) | {'subtotal'}


def test_a_walk_with_conditions_stops_expanding(soon, monkeypatch):
    """The walk that keeps each node's path condition goes into a definition
    at every use, each under its own conditions, for WALK nodes; after that
    only into a definition it has not been in, and it says that it cut."""
    from fcp import software as SW
    small = {n: parse(b) for n, b in chain(5).items()}
    st = SW._walk_state()
    full = list(SW._walk_ctx(parse('d5 <= subtotal'), small, (), st=st))
    assert len(full) == 1214 and not st['cut']             # 3 + N(5), N(k) = 8 + 3 N(k - 1), N(0) = 1
    assert max(len(ctx) for _, ctx in full) == 5           # one condition per definition on the way down
    monkeypatch.setattr(SW, 'WALK', 2000)
    defs = {n: parse(b) for n, b in chain(40).items()}
    st = SW._walk_state()
    n = sum(1 for _ in SW._walk_ctx(parse('d40 <= subtotal'), defs, (), st=st))
    assert 2000 <= n < 2400 and st['cut'] and st['walked'] == set(defs)


@pytest.fixture(scope='module')
def chained(tmp_path_factory):
    """The checkout bundle with two readings whose price goes through a
    chain of definitions: forty in t, five in u."""
    b = tmp_path_factory.mktemp('chained') / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    for name, n in (('t', 40), ('u', 5)):
        defs = ''.join(f"\n  {k}: '{v}'" for k, v in chain(n).items())
        (b / 'formal' / f'{name}.yaml').write_text(textwrap.dedent(f'''
            fcp: "0.1"
            set: {name}
            origin: {{kind: human, role: formalizer, id: {name}}}
            defs:DEFS
            properties:
              - {{id: T-P, req: R-RET-1, pattern: implies, args: {{trigger: 'subtotal >= 6', cond: 'outcome == 0 && price == d{n} && ship == 0'}}}}
              - {{id: T-Q, req: R-RET-1, pattern: implies, args: {{trigger: 'subtotal < 6', cond: 'outcome == 1'}}}}
        ''').replace('DEFS', defs))
    return Session(str(b), sets=['t', 'u'])


def test_the_integer_encoding_computes_a_definition_once(chained, soon, monkeypatch):
    """The integer encoding computed a definition again at every use: 3^8
    times on HumanEval/26, inside a walk of 3^8 nodes, and the search for
    calls at the boundaries of computed values did not end in 45 minutes.
    The value is the one computed at every use."""
    from fcp import software as SW
    fn = SW.function(chained)
    enc = SW._IntSpec(chained, ['t'], fn, 1)                # forty definitions: 3^40 computations before
    assert ('t', 'T-P', 1) in enc.holds
    a = SW._IntSpec(chained, ['u'], fn, 2)
    monkeypatch.setattr(SW._IntSpec, '_memo', lambda self: {})      # nothing kept: computed at every use
    b = SW._IntSpec(chained, ['u'], fn, 2)
    for f, i in (('d5', 1), ('d5 + d4 <= subtotal', 2), ('prev(d5) == d3', 2)):
        assert a._ex(parse(f), i).eq(b._ex(parse(f), i))
    assert a._depth(parse('prev(d5, 2)')) == b._depth(parse('prev(d5, 2)')) == 2
    assert a._range(parse('d5 + 1'), 1, {}) == b._range(parse('d5 + 1'), 1, {})


def test_the_search_at_computed_boundaries_ends(chained, soon, monkeypatch):
    """With five definitions the walk is complete and nothing is cut short;
    with forty it is cut at WALK nodes, the calls found stand, and the search
    is named among those cut short."""
    from fcp import software as SW
    fn = SW.function(chained)
    monkeypatch.setattr(SW, 'BUDGET_HIT', [])
    monkeypatch.setattr(SW, 'WALK', 3000)
    assert SW.conforming_points(chained, fn, ['u']) and SW.BUDGET_HIT == []
    assert SW.conforming_points(chained, fn, ['t'])
    assert SW.BUDGET_HIT == ['computed boundaries of t']


# ----------------------------------------------------------------------------
# rules over rigid variables in the integer encoding

@pytest.fixture(scope='module')
def rigid(tmp_path_factory):
    """The checkout bundle with readings whose rule holds for every q: over
    1,001 values (n), over 10^12 + 1 (v) and over 10^28 + 1 (x), as "a whole
    number" was written on HumanEval/144, and with two rigids of 101 values
    each in rules of their own (p, r)."""
    b = tmp_path_factory.mktemp('rigid') / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    one = '''
        fcp: "0.1"
        set: NAME
        origin: {kind: human, role: formalizer, id: NAME}
        rigids:
          - {name: q, range: [0, HI]}
        properties:
          - {id: T-P, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal == 7 * q + 7', cond: 'outcome == 0'}}
          - {id: T-Q, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal < 6', cond: 'outcome == 1'}}
    '''
    for name, hi in (('n', 1000), ('v', 10 ** 12), ('x', 10 ** 28)):
        (b / 'formal' / f'{name}.yaml').write_text(textwrap.dedent(one).replace('NAME', name).replace('HI', str(hi)))
    two = '''
        fcp: "0.1"
        set: NAME
        origin: {kind: human, role: formalizer, id: NAME}
        rigids:
          - {name: q, range: [0, 100]}
          - {name: t, range: [0, 100]}
        properties:
          - {id: T-P, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal == 7 * q + 7', cond: 'outcome == 0'}}
          - {id: T-Q, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal == 7 * t + OFF', cond: 'outcome == 1'}}
    '''
    for name, off in (('p', 8), ('r', 9)):
        (b / 'formal' / f'{name}.yaml').write_text(textwrap.dedent(two).replace('NAME', name).replace('OFF', str(off)))
    return Session(str(b), sets=['n', 'v', 'x', 'p', 'r'])


def test_a_rule_over_many_rigid_values_is_not_listed(rigid, soon):
    """The integer encoding lists one instance of a rule per value of its
    rigid variables.  Over 10^12 values the list was a MemoryError and over
    10^28 an OverflowError, which ended a review; it is Unsupported now, as
    every other formula the encoding does not take, and the callers go on
    without the encoding."""
    from fcp import software as SW
    fn = SW.function(rigid)
    enc = SW._IntSpec(rigid, ['n'], fn, 1)                  # 1,001 values: listed, as before
    assert ('n', 'T-P', 1) in enc.holds
    for s, count in (('v', 10 ** 12 + 1), ('x', 10 ** 28 + 1)):
        with pytest.raises(SW.Unsupported, match=f'{s}:T-P: a rule over {count} values of its rigid variables'):
            SW._IntSpec(rigid, [s], fn, 1)
        free = SW._IntSpec(rigid, [s], fn, 1, free_rigids=True)     # one instance at a free constant: as before
        assert (s, 'T-P', 1) in free.holds
    assert SW.conforming_points(rigid, fn, ['x']) == []             # no computed boundaries without the encoding
    rel = SW.compare(rigid, 'n', 'x', fn, bit_timeout=0)['R-RET-1']  # left to the scope and the bit level
    assert rel['relation'] == 'UNKNOWN' and rel['engine'] == '' and set(rel['scope_check']) == {'witness_a_not_b', 'witness_b_not_a'}


def test_a_witness_that_cannot_be_replayed_is_not_confirmed(rigid, soon):
    """Two rigids of 101 values each, in rules of their own: each rule is
    listed, and the monitor would be replayed for 10,201 pairs, more than a
    replay lists.  The witness of the integer encoding is then not confirmed
    (the replay raised ValueError, which ended the comparison)."""
    from fcp import software as SW
    fn = SW.function(rigid)
    enc = SW._IntSpec(rigid, ['p', 'r'], fn, 1)
    st, w = enc.split('p', 'r', 'R-RET-1', False, 20000)
    assert st == 'witness'
    assert SW._confirm(rigid, fn, w, 'p', 'r', 'R-RET-1', False) is False


# ----------------------------------------------------------------------------
# rules over rigid variables on the bit-level model of a comparison

@pytest.fixture(scope='module')
def loose(tmp_path_factory):
    """The checkout bundle with readings that state one rule in two ways: for
    a range of subtotals (u up to 106, u3 up to 5,006), and for every q where
    subtotal == q + 6: over 101 values of q (w), over 102 (w2: one subtotal
    more than u) and over 5,001 (w3: more than a replay lists).  A monitor
    expands a rule over 64 values at most, so the bit-level model has no
    selector for the rule of w, w2 and w3."""
    b = tmp_path_factory.mktemp('loose') / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    one = '''
        fcp: "0.1"
        set: NAME
        origin: {kind: human, role: formalizer, id: NAME}
        RIGIDS
        properties:
          - {id: T-P, req: R-RET-1, pattern: implies, args: {trigger: 'TRIGGER', cond: 'outcome == 0'}}
          - {id: T-Q, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal < 6', cond: 'outcome == 1'}}
    '''
    for name, hi in (('u', 106), ('u3', 5006)):
        (b / 'formal' / f'{name}.yaml').write_text(
            textwrap.dedent(one).replace('NAME', name).replace('RIGIDS\n', '')
            .replace('TRIGGER', f'subtotal >= 6 && subtotal <= {hi}'))
    for name, hi in (('w', 100), ('w2', 101), ('w3', 5000)):
        (b / 'formal' / f'{name}.yaml').write_text(
            textwrap.dedent(one).replace('NAME', name).replace('RIGIDS', f'rigids:\n  - {{name: q, range: [0, {hi}]}}')
            .replace('TRIGGER', 'subtotal == q + 6'))
    return Session(str(b), sets=['u', 'w', 'w2', 'u3', 'w3'])


def test_a_comparison_asks_and_replays_the_rules_it_cannot_assume(loose):
    """Found by reading the review of HumanEval/26 (1a) by hand: one reader
    wrote "for every value v" over 256 values, the bit-level model skipped
    that rule, and the review asked two questions with calls on which the
    readings agree.  Such a rule is now asked, of the reading that rejects,
    for a value at which it fails; where it has to hold, an answer counts
    only if the rule accepts it on replay over every value."""
    from fcp import software as SW
    fn = SW.function(loose)
    assert [SW.left_out(loose, s) for s in ('u', 'w', 'w2')] == [[], ['T-P'], ['T-P']]
    spec = SW._Spec(loose, ['u', 'w', 'w2'], fn, 1)
    assert set(spec.loose) == {('w', 'T-P'), ('w2', 'T-P')} and all(spec.loose.values())
    seven, edge, req = [(7, 0, False)], [(107, 0, False)], 'R-RET-1'
    # u rejects checkout(7, ..) answered with an error, and so does w: the model's answer is replayed, and refuted
    assert spec.split_status(seven, 'w', 'u', req, False) == ('unknown', None) and spec.refuted == 1
    # w2 rejects an error at 107 (q = 101) and u does not: a separating call, where the model said there was none
    st, wit = spec.split_status(edge, 'u', 'w2', req, False)
    assert st == 'witness' and wit['outs'][0]['outcome'] != 0
    assert spec.split_status(seven, 'u', 'w2', req, False) == ('none', None)
    assert spec.split_status(seven, 'u', 'w', req, False) == ('none', None)
    assert spec.split_status(None, 'u', 'w', req, False) == ('none', None)       # over every call
    st, wit = spec.split_status(None, 'u', 'w2', req, False)
    assert st == 'witness' and wit['calls'][0][0] == 107 and SW._confirm(loose, fn, wit, 'u', 'w2', req, False)
    # a scan of the scope gives up after UNCONFIRMED refuted answers: more would cost a replay each
    sc = SW.scope_separation(loose, spec, fn, 'w', 'u', req, False)
    assert sc['witness'] is None and sc['refuted'] == SW.UNCONFIRMED and sc['calls'] < 200
    assert SW.scope_separation(loose, spec, fn, 'u', 'w', req, False) == {'calls': 200, 'witness': None}
    # where the rule has to hold and does, the answer stands: w accepts an error at 200 and u3 does not
    wide = SW._Spec(loose, ['w', 'u3'], fn, 1)
    st, wit = wide.split_status([(200, 0, False)], 'w', 'u3', req, False)
    assert st == 'witness' and wide.refuted == 0 and SW._confirm(loose, fn, wit, 'w', 'u3', req, False)
    spec.loose[('w2', 'T-P')] = None            # as for a rule the model cannot ask at all
    assert spec.split_status(seven, 'u', 'w2', req, False) == ('unknown', None)


def test_a_comparison_names_the_rules_it_cannot_assume(loose, monkeypatch):
    """Over 5,001 values the integer encoding lists nothing and a replay
    lists nothing: a requirement beside such a rule stays UNKNOWN, with no
    call, and the comparison says which rule it could not assume.  The
    review then asks whether the readings mean the same, not which is meant."""
    from fcp import review as RV, software as SW
    fn = SW.function(loose)
    monkeypatch.setattr(SW, 'BUDGET_HIT', [])
    monkeypatch.setattr(SW, 'COMPARE_BUDGET', None)
    rel = SW.compare(loose, 'u3', 'w3', fn, bit_timeout=0)['R-RET-1']
    assert rel['relation'] == 'UNKNOWN' and rel['engine'] == ''
    assert 'witness_a_not_b' not in rel and 'witness_b_not_a' not in rel
    assert rel['scope_check']['witness_a_not_b'] == {'calls': 200, 'separated': False}
    assert rel['scope_check']['witness_b_not_a']['refuted'] == SW.UNCONFIRMED
    assert SW.BUDGET_HIT == ['the comparison of u3 and w3: it cannot assume T-P (rules stated for every value '
                             'of a variable), and requirements they bear on stay undecided']

    def asked(relation, witness):
        out = {'sets': ['u3', 'w3'], 'prompt': {s: {'conflicts': {'conflicts': []}, 'open': {'open': {}}}
                                               for s in ('u3', 'w3')},
               'readings': {'R-RET-1': {'plain': relation, 'context': relation, 'witness': witness}}}
        settled, queue = RV.verdicts(loose, out)
        assert 'R-RET-1' not in settled
        return [(q['kind'], q['question']) for q in queue if q['kind'] in ('readings', 'undecided')]

    assert asked('UNKNOWN', None) == [('undecided', 'the two readings of this requirement were not shown to agree, '
                                       'and no call that separates them was found: do they mean the same?')]
    assert asked('UNKNOWN', ['checkout(107, 0, False) -> raises ValueError']) == \
        [('readings', 'the two readings of this requirement disagree on these calls: which is meant?')]
    assert asked('A-WEAKER', None) == [('readings', 'the two readings of this requirement disagree (no separating '
                                        'call was found within the budget): which is meant?')]


@pytest.fixture(scope='module')
def endings(tmp_path_factory):
    """The checkout bundle with no exception named: a call ends with code 0
    (it returned), 1 (an exception or no answer) or 2 (it returned something
    else), and the two bits of the outcome signal leave code 3, which names
    no ending.  Readings a and b state one rule in two ways that differ on
    code 3 only; c leaves one ending and code 3; x asks for code 3 at one
    subtotal."""
    b = tmp_path_factory.mktemp('endings') / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    design, named = (b / 'design.yaml').read_text(), 'outcome: {signal: outcome, raises: [ValueError]}'
    assert design.count(named) == 1
    (b / 'design.yaml').write_text(design.replace(named, 'outcome: {signal: outcome}'))
    one = '''
        fcp: "0.1"
        set: NAME
        origin: {kind: human, role: formalizer, id: NAME}
        properties:
          - {id: T-P, req: R-RET-1, pattern: implies, args: {trigger: 'TRIGGER', cond: 'COND'}}
          - {id: T-Q, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal < 6', cond: 'outcome == 1'}}
    '''
    for name, trigger, cond in (('a', 'subtotal >= 6', 'outcome == 0 || outcome == 2'),
                                ('b', 'subtotal >= 6', 'outcome != 1'), ('c', 'subtotal >= 6', 'outcome >= 2'),
                                ('x', 'subtotal == 7', 'outcome == 3')):
        (b / 'formal' / f'{name}.yaml').write_text(
            textwrap.dedent(one).replace('NAME', name).replace('TRIGGER', trigger).replace('COND', cond)
            + ("scenarios:\n  - {id: S-7, req: R-EX-1, cover: 'subtotal == 7'}\n" if name == 'x' else ''))
    return Session(str(b), sets=['a', 'b', 'c', 'x'])


def test_a_call_ends_in_a_way_that_has_a_name(endings, monkeypatch):
    """Found by replaying the calls that the stored reviews show: the review
    of HumanEval/46 (1a) asked which of two readings is meant and showed
    fib4(8) "returned something else", a call on which the readings agree.
    They differed on outcome code 3 only, which no call produces: the
    request names no exception, so the codes end at 2, and every search left
    the two-bit signal free.  No search yields such a code now, in either
    model, and no text shows one under the name of another."""
    from fcp import software as SW
    from fcp.harness import ENV_OK
    fn = SW.function(endings)
    assert (fn.other_val, fn.widths[fn.outcome]) == (2, 2)
    assert fn.outcome_name(2) == 'returned something else' and 'names no ending' in fn.outcome_name(3)
    assert f"assume({ENV_OK});" in endings.free_hb(['a']).text()
    spec = SW._Spec(endings, ['a', 'b'], fn, 1)
    assert spec.model.env_ok
    assert spec.split_status(None, 'a', 'b', 'R-RET-1', False) == ('none', None)
    assert spec.split_status(None, 'b', 'a', 'R-RET-1', False) == ('none', None)    # was: a call that ended with code 3
    monkeypatch.setattr(SW, 'BUDGET_HIT', [])
    rel = SW.compare(endings, 'a', 'b', fn, bit_timeout=0)['R-RET-1']
    assert (rel['relation'], rel['engine']) == ('EQUIVALENT', 'z3-int')            # was: A-STRONGER, with that call
    assert 'witness_a_not_b' not in rel and 'witness_b_not_a' not in rel and SW.BUDGET_HIT == []
    # one ending is left where c's rule applies: nothing is open there (was: the same words twice)
    assert fn.outcome not in SW.choices(endings, 'c', fn, [fn.outcome])['open']
    assert SW.choices(endings, 'b', fn, [fn.outcome])['open'][fn.outcome]['shown'] == \
        ['returned', 'returned something else']
    # a signal whose codes all name an ending gets no condition: the harness is the one it was
    assert ENV_OK not in Session(B, sets=['gold']).free_hb(['gold']).text()


def test_rules_that_leave_no_ending_are_a_conflict(endings):
    """A rule that asks for the code that names no ending leaves the call no
    way to end: a conflict of the request with itself, in the search over
    calls and in the search over scenarios.  While code 3 was free, the call
    "ended" with it and both searches found nothing."""
    from fcp import review as RV, software as SW
    fn = SW.function(endings)
    found = SW.conflicts(endings, 'x', fn)['conflicts']
    assert [(c['core'], c['stimulus']) for c in found] == [(['T-P'], ['checkout(7, 0, False)'])]
    assert SW.conflicts(endings, 'b', fn)['conflicts'] == []
    cons = endings.consistency('x', pairs=False, scenarios_only=True)
    assert [(c['mus'], c['situations']) for c in cons['conflicts']] == [(['T-P'], ['scenario(S-7)'])]
    assert RV.scenarios(cons) == {'impossible': [], 'forbidden': [], 'blocked': [], 'undecided': []}
    forced = endings.forcing('x')['conflicts']
    assert forced and forced[0]['core'] == ['T-P']
