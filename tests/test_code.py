"""The software adapter (fcp.software) on corpus/code_checkout."""
import os
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_checkout')
sys.path.insert(0, ROOT)
sys.path.insert(0, B)

from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402


@pytest.fixture(scope='module')
def S():
    return Session(B, sets=['gold'])


@pytest.fixture(scope='module')
def fn(S):
    return SW.function(S)


def _write(tmp_path, body: str) -> str:
    p = tmp_path / 'impl.py'
    p.write_text(textwrap.dedent(body))
    return str(p)


def test_outcomes(tmp_path, fn):
    """How a call ended: a pair that fits, ValueError, another exception or no
    answer, anything else."""
    src = _write(tmp_path, '''
        import time
        def checkout(subtotal, coupon, member):
            if subtotal == 1: raise ValueError('x')
            if subtotal == 2: raise TypeError('y')
            if subtotal == 3: return (1.0, 0)
            if subtotal == 4: return (1, 0, 0)
            if subtotal == 5: return [1, 0]
            if subtotal == 6: time.sleep(5)
            if subtotal == 7: return (True, 0)
            return (subtotal, 499)
    ''')
    calls = [(s, 0, 0) for s in range(8)]
    res = SW.run(fn, src, calls, timeout=0.5)
    assert res['code'] == [0, 1, 2, 3, 3, 3, 2, 3]
    assert res['ret']['price'][0] == 0 and res['ret']['ship'][0] == 499
    assert SW.result_text(fn, res, 3).startswith('returned (1.0, 0)')


def test_reference_and_a_planted_bug(S, fn):
    """The reference meets every gold requirement except the one that
    conflicts; the failure is the threshold pair, replayed.  A planted bug
    fails the requirement it was planted against."""
    ref = os.path.join(B, 'impl', 'ref.py')
    calls = SW.calls_for(S, fn, [ref], small=True)
    res = SW.run(fn, ref, calls)
    v = SW.verify(S, 'gold', fn, ref, calls, res, SW.trace(fn, calls, res))
    bad = {i for i, x in v.items() if x['status'] not in ('PASS', 'COVERED')}
    assert bad == {'G-MONO'}
    shown = [c['call'] for c in v['G-MONO']['calls_shown']]
    assert shown[-1].startswith('checkout(5000,') and shown[0].startswith('checkout(4999,')
    assert v['G-MONO']['replay'] == 'confirmed'
    import build
    c1 = build.materialize()['C1']
    calls = SW.calls_for(S, fn, [c1], small=True)
    res = SW.run(fn, c1, calls)
    v = SW.verify(S, 'gold', fn, c1, calls, res, SW.trace(fn, calls, res))
    assert v['G-SHIP']['status'] == 'FAIL'
    assert v['G-SHIP']['calls_shown'][0]['call'].startswith('checkout(5000,')


def test_boundary_conflict(S, fn):
    """Before any code: the free-shipping threshold conflicts with 'adding
    items never lowers the amount charged'."""
    r = SW.conflicts(S, 'gold', fn, limit=1)
    c = r['conflicts'][0]
    assert {'R-SHIP-1', 'R-MONO-1'} <= set(c['reqs'])
    assert [x[0] for x in c['calls']] == [4999, 5000]


def test_open_choice(S, fn):
    """Half a cent is left open by the literal reading."""
    r = SW.choices(S, 'gold', fn, ['price'])['open']['price']
    assert r['call'] == 'checkout(5, 0, True)' and r['values'] == [4, 5]


def test_open_choices_stay_inside_the_contract(tmp_path):
    """No open choice on a call the reading excludes: one that breaks an
    assumption, or that meets a don't-care citing a condition on the caller.
    A freedom the reading declares inside its contract is still a choice of
    the request, and the answer names the don't-care."""
    import shutil
    import yaml
    b = tmp_path / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    rq = yaml.safe_load((b / 'requirements.yaml').read_text())
    for r in rq['requirements']:
        if r['id'] in ('R-IN-1', 'R-IN-2'):
            r['kind'] = 'assumption'                      # conditions on the caller
    (b / 'requirements.yaml').write_text(yaml.safe_dump(rq, sort_keys=False))
    (b / 'formal' / 't.yaml').write_text(textwrap.dedent('''
        fcp: "0.1"
        set: t
        origin: {kind: human, role: formalizer, id: t}
        assumptions:
          - {id: T-A, req: R-IN-1, expr: 'subtotal >= 2'}
        properties:
          - {id: T-P, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal >= 6', cond: 'outcome == 0 && price == subtotal && ship == 0'}}
        dont_cares:
          - {id: T-D1, req: R-IN-2, signal: outcome, when: 'subtotal < 4'}
          - {id: T-D2, req: R-RET-1, signal: price, when: 'subtotal < 6'}
    '''))
    S = Session(str(b), sets=['t'])
    f = SW.function(S)
    r = SW.choices(S, 't', f, ['price', 'ship', 'outcome'])['open']
    assert {x['args'][0] for x in r.values()} == {4}      # not 0 (breaks T-A), not 2 (outside by T-D1)
    assert [r[x]['declared'] for x in ('price', 'ship', 'outcome')] == [['T-D2'], [], []]
    assert r['outcome']['ending'] and not r['price']['ending']
    assert all(x.startswith(('returned', 'raised')) for x in r['outcome']['shown'])
    from fcp import review as RV
    g = RV.given(S, ['t'])
    assert [x['id'] for x in g['contract']] == ['T-A', 'T-D1'] and [x['id'] for x in g['free']] == ['T-D2']
    assert RV.open_question({'price': r['price']}).endswith(
        ' (the reading leaves this free on purpose: T-D2): is any answer acceptable, or which is meant?')
    assert RV.open_question({'outcome': r['outcome']}).startswith('the request lets this call end in two ways, "')
    # one question for the call, with every output it leaves open; the requirement the freedom cites is not settled
    out = {'sets': ['t'], 'prompt': {'t': {'conflicts': {'conflicts': []}, 'open': {'open': r}}}, 'readings': {}}
    settled, queue = RV.verdicts(S, out)
    asked = [q for q in queue if q['kind'] == 'open']
    assert [(q['signal'], q['reqs'], q['calls']) for q in asked] == \
        [('price, ship, outcome', ['R-RET-1'], [r['price']['call']])]
    assert asked[0]['question'].startswith('the request allows `price` to be ') and \
        ' and allows `ship` to be ' in asked[0]['question'] and ' and lets this call end in two ways, ' in asked[0]['question']
    assert 'R-RET-1' not in settled
    # without the freedom it is settled; the reading states no rule for the other requirements,
    # so none of them is (tests/test_partial.py)
    bare = {**out, 'prompt': {'t': {'conflicts': {'conflicts': []}, 'open': {'open': {}}}}}
    assert RV.verdicts(S, bare)[0] == ['R-RET-1']
    assert max(r['price']['values']) <= 9 and max(r['ship']['values']) <= 9      # small answers are shown


def test_mutants():
    ms = SW.mutants('def f(x):\n    return x + 1 if x < 5000 else round(x)\n')
    descs = {m['desc'] for m in ms}
    assert 'line 2: < becomes <=' in descs and 'line 2: round() becomes int()' in descs
    for m in ms:
        compile(m['code'], 'm', 'exec')


def test_an_open_choice_is_confirmed_over_every_rigid_value(tmp_path, monkeypatch):
    """Found on HumanEval/163: a rule stated for every value of a rigid
    variable with a large range is not in the solver of the open-choice
    search, which showed two answers that the rule excludes.  Both answers
    are now replayed on the compiled monitor over every rigid value: a choice
    the rule excludes is dropped and counted, one it allows is kept, and the
    review names the rule its searches leave out."""
    import shutil
    from fcp import review as RV
    b = tmp_path / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    for s, cond in (('one', 'd == 7'), ('two', 'd <= 1')):       # the price is 7; the price is 0 or 1
        (b / 'formal' / f'{s}.yaml').write_text(textwrap.dedent(f'''
            fcp: "0.1"
            set: {s}
            origin: {{kind: human, role: formalizer, id: {s}}}
            rigids:
              - {{name: d, range: [0, 255]}}
            properties:
              - {{id: T-O, req: R-RET-1, pattern: invariant, args: {{cond: 'outcome == 0 && ship == 0 && price <= 255'}}}}
              - {{id: T-D, req: R-RET-1, pattern: implies, args: {{trigger: 'price == d', cond: '{cond}'}}}}
        '''))
    S = Session(str(b), sets=['one', 'two'])
    f = SW.function(S)
    assert SW.left_out(S, 'one') == ['T-D'] and SW.left_out(Session(B, sets=['gold']), 'gold') == []
    one = SW.choices(S, 'one', f, ['price'])
    assert one['open'] == {} and one['left_out'] == ['T-D'] and one['rejected'] == SW.UNCONFIRMED
    two = SW.choices(S, 'two', f, ['price'])
    assert two['open']['price']['values'] == [0, 1] and two['rejected'] == 0
    for k in ('SCOPE_BUDGET', 'CONFLICT_BUDGET', 'COMPARE_BUDGET'):       # check() sets them: put them back
        monkeypatch.setattr(SW, k, getattr(SW, k))
    real = SW.choices                          # the review of this reading, on the price only: a short test
    monkeypatch.setattr(SW, 'conflicts', lambda S, s, fn: {'conflicts': [], 'candidates': 0, 'checked': 0})
    monkeypatch.setattr(SW, 'choices', lambda S, s, fn, signals: real(S, s, fn, ['price']))
    out = RV.check(str(b), None, ['one'], log=lambda *a: None)
    assert out['limits'] == ['the conflicts and open choices of one: these searches leave out T-D (rules stated '
                             f'for every value of a variable); {SW.UNCONFIRMED} calls with two answers that '
                             'break them are not reported']
    assert not [q for q in out['queue'] if q['kind'] == 'open']
    assert 'by a rule they cannot use' in RV.report(Session(str(b), sets=['one']), out)


def test_run_tests(tmp_path):
    impl = _write(tmp_path, 'def double(x):\n    return x * 2 if x != 3 else 7\n')
    t = tmp_path / 'tests'
    t.mkdir()
    (t / 'test_double.py').write_text('from double import double\n'
                                      'def test_two():\n    assert double(2) == 4\n'
                                      'def test_three():\n    assert double(3) == 6\n')
    r = SW.run_tests(str(t / 'test_double.py'), impl, 'double')
    assert (r['passed'], r['failed'], r['ok']) == (1, 1, False)
    assert r['failing'] == ['test_double::test_three']


# ----------------------------------------------------------------------------
# the question of a clash that both readings find
def test_a_clash_both_readings_find_is_one_place(tmp_path):
    """Found on HumanEval/134 with inverted examples: both readings found the
    same clash on the same call, and its question ended "(also with , at 2
    places)".  The two findings were counted as two places, and the list of
    further requirements was printed although it was empty."""
    import shutil
    from fcp import review as RV
    b = tmp_path / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    for s in ('one', 'two'):
        (b / 'formal' / f'{s}.yaml').write_text(textwrap.dedent(f'''
            fcp: "0.1"
            set: {s}
            origin: {{kind: human, role: formalizer, id: {s}}}
            properties:
              - {{id: T-A, req: R-RET-1, pattern: invariant, args: {{cond: 'outcome <= 1'}}}}
              - {{id: T-B, req: R-ERR-1, pattern: invariant, args: {{cond: 'ship <= 255'}}}}
              - {{id: T-C, req: R-MEM-1, pattern: invariant, args: {{cond: 'price <= 65535'}}}}
        '''))
    S = Session(str(b), sets=['one', 'two'])
    base = 'no implementation can meet these requirements on these calls: which one gives way?'

    def asked(*found):                         # (reading, the minimal sets of the clash, the call that shows it)
        out = {'sets': ['one', 'two'], 'readings': {}, 'prompt': {
            s: {'open': {'open': {}}, 'conflicts': {'conflicts': [
                {'reqs': sorted({S.mon(s).items[i].req for mu in muses for i in mu}), 'core': list(muses[0]),
                 'muses': [list(mu) for mu in muses], 'stimulus': [call]}
                for t, muses, call in found if t == s]}} for s in ('one', 'two')}}
        qs = [q for q in RV.verdicts(S, out)[1] if q['kind'] == 'conflict']
        assert all(q['question'].startswith(base) for q in qs)
        return [(q['reqs'], q['calls'], q['question'][len(base):]) for q in qs]

    ab, ac = ('T-A', 'T-B'), ('T-A', 'T-C')
    both = ['R-ERR-1', 'R-RET-1']
    assert asked(('one', [ab], 'f(1)')) == [(both, ['f(1)'], '')]
    assert asked(('one', [ab], 'f(1)'), ('two', [ab], 'f(1)')) == [(both, ['f(1)'], '')]      # found twice, one place
    assert asked(('one', [ab], 'f(22)'), ('two', [ab], 'f(1)')) == [(both, ['f(1)'], ' (at 2 places)')]
    assert asked(('one', [ab, ac], 'f(1)')) == [(['R-RET-1'], ['f(1)'], ' (also with R-ERR-1, R-MEM-1)')]
    assert asked(('one', [ab, ac], 'f(1)'), ('two', [ab, ac], 'f(2)')) == \
        [(['R-RET-1'], ['f(1)'], ' (also with R-ERR-1, R-MEM-1, at 2 places)')]
