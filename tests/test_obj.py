"""Objects: a method of a class checked as a chip with memory, on
corpus/code_limit (a rate limiter)."""
import os
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_limit')
sys.path.insert(0, ROOT)

from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402


@pytest.fixture(scope='module')
def S():
    return Session(B, sets=['gold'])


@pytest.fixture(scope='module')
def fn(S):
    return SW.function(S)


@pytest.fixture(scope='module')
def calls(S, fn):
    return SW.calls_for(S, fn, small=True)


def test_new_object_per_sequence(tmp_path, fn):
    """A None in the calls is a new object: state does not leak between sequences."""
    src = tmp_path / 'impl.py'
    src.write_text(textwrap.dedent('''
        class RateLimiter:
            def __init__(self):
                self.n = 0
            def allow(self, user, now):
                self.n += 1
                if user == 7:
                    raise KeyError('x')
                return self.n <= 2
    '''))
    calls = [None, (0, 0), (0, 1), (0, 2), None, (0, 3), (7, 4), (0, 5)]
    res = SW.run(fn, str(src), calls)
    assert res['code'] == [-1, 0, 0, 0, -1, 0, 2, 0]
    assert res['ret']['allowed'] == [False, True, True, False, False, True, False, False]
    cols = SW.trace(fn, calls, res)
    assert cols['rst_n'] == [0, 0, 1, 1, 1, 0, 1, 1, 1]
    assert SW.history(calls, 7) == [5, 6, 7]


def test_reference_and_planted_bugs(S, fn, calls):
    import importlib.util
    spec = importlib.util.spec_from_file_location('limit_build', os.path.join(B, 'build.py'))
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    srcs = build.materialize()
    srcs['ref'] = os.path.join(B, 'impl', 'ref.py')
    want = {'ref': {'R-FAIR-1'}, 'C3': {'R-PEN-1'}, 'C6': {'R-RET-1'}, 'C8': {'R-RET-1'}, 'C9': {'R-FAIR-1'}}
    for v, reqs in want.items():
        res = SW.run(fn, srcs[v], calls)
        out = SW.verify(S, 'gold', fn, srcs[v], calls, res, SW.trace(fn, calls, res))
        failing = {x['req'] for x in out.values() if x['status'] == 'FAIL'}
        assert reqs <= failing, (v, failing)
        if v in ('ref', 'C9'):
            assert failing == {'R-FAIR-1'}, v               # the prompt's own conflict, nothing else
        for x in out.values():
            if x['status'] == 'FAIL':
                assert x['replay'] == 'confirmed'
                assert len(x['calls_shown']) >= 1


def test_conflict_before_code(S, fn):
    c = SW.conflicts(S, 'gold', fn, limit=1)
    assert c['conflicts'], c
    reqs = set(c['conflicts'][0]['reqs'])
    assert {'R-FAIR-1', 'R-PEN-1'} <= reqs
    assert len(c['conflicts'][0]['calls']) >= 5           # three allowed, one denied, one more


def test_pins_follow_defs_and_stay_in_range():
    """agent_b binds its customer through a def (by_u: user == u): the conflict
    search must still pin it, and never at a value outside the rigid's range."""
    S2 = Session(B, sets=['agent_b'])
    fn2 = SW.function(S2)
    c = SW.conflicts(S2, 'agent_b', fn2)
    reqs = [set(x['reqs']) for x in c['conflicts']]
    assert any({'R-FAIR-1', 'R-PEN-1'} <= r for r in reqs), c['conflicts']
    for x in c['conflicts']:
        assert all(0 <= call[0] <= 1000 for call in x['calls']) or 'R-FAIR-1' not in x['reqs'], x


def test_reading_over_more_rigid_values_than_a_replay_runs(tmp_path):
    """A reading whose rigid ranges multiply to more combinations than a replay
    runs (a reader of this task wrote three rigid variables, 4.3e12
    combinations): lint says so, and a comparison leaves open the direction
    whose counterexample it cannot replay over every combination.  The lint
    said nothing before, and the refusal of the replay ended the comparison."""
    import shutil
    from fcp import pipeline, rv
    d = tmp_path / 'limit'
    shutil.copytree(B, d, ignore=shutil.ignore_patterns('agents', 'variants', '__pycache__'))
    text = (d / 'formal' / 'agent_a.yaml').read_text()
    rigid = '  - {name: c, range: [0, 1000]}'
    assert 'set: agent_a' in text and rigid in text
    (d / 'formal' / 'agent_a.yaml').unlink()                # the same reading, with a second rigid that no rule names
    (d / 'formal' / 'wide.yaml').write_text(
        text.replace('set: agent_a', 'set: wide').replace(rigid, rigid + '\n  - {name: z, range: [0, 9]}', 1))
    S2 = Session(str(d), sets=['agent_b', 'wide'])
    assert not [x for x in pipeline.lint(S2, 'agent_b') if x['kind'] == 'rigid-cases']
    warn = [x for x in pipeline.lint(S2, 'wide') if x['kind'] == 'rigid-cases']
    assert len(warn) == 1 and warn[0]['severity'] == 'warning' and '10,010 combinations' in warn[0]['msg'], warn
    with pytest.raises(rv.NotReplayed):
        rv.check(S2, 'wide', [])
    S2.cmp_engine = 'bmc'
    rel = S2.compare('agent_b', 'wide', only={'R-FAIR-1'})['R-FAIR-1']
    assert rel['relation'] == 'UNKNOWN', rel
    # the record says which direction that was: agent_b accepts a run that wide rejects, the other way is open
    assert rel['status'] == {'witness_a_not_b': 'witness', 'witness_b_not_a': 'unknown'}
    from fcp import software as SW
    assert SW.closed(rel) == ()


def stubbed(S2, found: dict, asked: list):
    """Replace the searches of S2 by their results: a task is named
    <tag>:<req>:<a=>b | b=>a | sat>[:p<n>], and found gives the status per kind."""
    from fcp.engine import Result

    def run(tasks):
        asked.extend(t.name for t in tasks)
        return {t.name: Result(t.name, '', found[t.name.split(':')[2]], t.mode, S2.cmp_engine, 0.0, '', trace=[])
                for t in tasks}
    S2.run = run


def test_a_bounded_comparison_records_what_each_direction_found():
    """Session.compare (the engine of a review of objects and effects) writes
    the status of each direction from what its searches returned, and closed()
    reads it.  The searches are replaced by their results, so every relation
    is reached without a solver.  In context a direction that found nothing
    is closed only where a behaviour was shown to meet the other
    requirements.  A counterexample without a trace, of a direction that is
    replayed over its rigid values, is not a call.  A bound that leaves no
    cycle for a call is refused."""
    S2 = Session(B, sets=['agent_a', 'agent_b'])
    S2.cmp_engine = 'bmc'
    la = max(S2.lookahead('agent_a'), S2.lookahead('agent_b'))
    found, asked = {}, []
    stubbed(S2, found, asked)
    a_b, b_a = SW.WITNESSES

    def rel(ab, ba, sat=None, req='R-RET-1'):
        found.update({'a=>b': ab, 'b=>a': ba, 'sat': sat})
        return S2.compare('agent_a', 'agent_b', context=sat is not None, only={req})[req]

    for ab, ba, sat, relation, status in (
            ('PASS', 'PASS', None, 'EQUIVALENT', ('none', 'none')),
            ('PASS', 'FAIL', None, 'A-STRONGER', ('none', 'witness')),
            ('FAIL', 'PASS', 'FAIL', 'A-WEAKER', ('witness', 'none')),
            ('FAIL', 'FAIL', 'FAIL', 'INCOMPARABLE', ('witness', 'witness')),
            ('PASS', 'TIMEOUT', 'FAIL', 'UNKNOWN', ('none', 'unknown')),
            ('PASS', 'FAIL', 'TIMEOUT', 'A-STRONGER', ('none', 'witness')),     # the call found meets the rest
            ('PASS', 'PASS', 'TIMEOUT', 'UNKNOWN', ('unknown', 'unknown')),     # nothing was shown to meet the rest
            ('PASS', 'PASS', 'PASS', 'NO-CONTEXT', ('none', 'none'))):          # nothing meets the rest: nothing closed
        x = rel(ab, ba, sat)
        assert (x['relation'], x['status']) == (relation, dict(zip(SW.WITNESSES, status))), (ab, ba, sat, x)
        assert SW.closed(x) == (() if relation == 'NO-CONTEXT' else
                                tuple(k for k, s in zip(SW.WITNESSES, status) if s == 'none'))
        assert (x['engine'], x['depth'], x['lookahead']) == ('bmc', S2.bmc_depth, la)
    # a direction whose rule ranges over rigid values is replayed before its call is kept: nothing to replay here
    x = rel('FAIL', 'PASS', req='R-FAIR-1')
    assert x['relation'] == 'UNKNOWN' and x['status'] == {a_b: 'unknown', b_a: 'none'} and a_b not in x
    assert SW.closed(x) == (b_a,)
    # cycle 0 is the reset and a disagreement is reported la cycles after it happens
    S2.bmc_depth = la + 1
    with pytest.raises(ValueError, match='examines no call'):
        rel('PASS', 'PASS')
    S2.bmc_depth = la + 2
    assert rel('PASS', 'PASS')['depth'] == la + 2


def test_a_comparison_under_the_assumptions_of_one_set_writes_no_record_of_the_assumptions():
    """With env both sets run under the assumptions of one set, and no search
    compares the assumptions of the two: the comparison writes no
    '<assumptions>' record (it used to write EQUIVALENT, from no search)."""
    H = Session(os.path.join(ROOT, 'corpus', 'arbiter'), sets=['agent_a', 'agent_b'])
    assert H.assumptions('agent_a') and H.assumptions('agent_b')
    asked: list = []
    stubbed(H, {'a=>b': 'PASS', 'b=>a': 'PASS', 'sat': 'FAIL'}, asked)
    assert H.compare('agent_a', 'agent_b')['<assumptions>']['relation'] == 'EQUIVALENT'
    assert sorted(n for n in asked if ':<assumptions>:' in n) == ['cmp:<assumptions>:a=>b', 'cmp:<assumptions>:b=>a']
    del asked[:]
    assert '<assumptions>' not in H.compare('agent_a', 'agent_b', env='agent_a')
    assert asked and not [n for n in asked if ':<assumptions>:' in n]
