"""A second solver on every proof (fcp.confirm): the formulas z3 finds unsatisfiable during a
proof are recorded, by the requirement being settled, and decided again by
cvc5; a verdict is confirmed, refuted or left unconfirmed by its answers."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fcp import confirm as C  # noqa: E402
from fcp import prove as P  # noqa: E402
from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402

pytest.importorskip('cvc5')


def test_only_unsat_answers_are_recorded_under_the_requirement_in_hand():
    import z3
    orig = z3.Solver.check
    x, y = z3.Ints('x y')
    with C.recording() as rec:
        s = z3.Solver()
        s.add(x > 0, x < 0)
        assert s.check() == z3.unsat                 # before any requirement: shared
        C.tag('R-A')
        s = z3.Solver()
        s.add(x > y)
        assert s.check() == z3.sat                   # a model: nothing to confirm
        assert s.check(y > x) == z3.unsat            # the assumption is part of the formula
        assert s.check(y > x) == z3.unsat            # the same formula again: once
        with pytest.raises(RuntimeError):
            with C.recording():
                pass
    assert z3.Solver.check is orig and C._ACTIVE is None
    C.tag('R-B')                                     # outside a recording: nothing happens
    assert rec.answers == {'unsat': 3, 'sat': 1, 'unknown': 0}
    assert len(rec.texts) == 2 and len(rec.by[C.SHARED]) == 1 and len(rec.by['R-A']) == 1
    assert rec.behind('R-A') == rec.by[C.SHARED] + rec.by['R-A'] and rec.behind('R-C') == rec.by[C.SHARED]
    own = rec.texts[rec.by['R-A'][0]]
    assert '(check-sat)' in own and own.count('(assert') == 2
    assert {C.decide(t)['result'] for t in rec.texts.values()} == {'unsat'}


def test_cvc5_reads_what_z3_prints():
    import z3
    x, y, p = z3.Ints('x y p')
    with C.recording() as rec:
        s = z3.Solver()                              # a product: not in the linear logic tried first
        s.add(x >= 0, x <= 2000, p >= 0, p <= 30, y == (x * (100 - p) + 50) / 100, y > x)
        assert s.check() == z3.unsat
        s = z3.Solver()                              # z3 prints a disjunction of nothing as a bare `or`
        s.add(z3.Or(z3.Or(), x > 0), x < 0)
        assert s.check() == z3.unsat
    a, b = (C.decide(t) for t in rec.texts.values())
    assert a['result'] == 'unsat' and a['logic'] in ('ALL', 'QF_NIA') and a['attempts'] >= 1
    assert b['result'] == 'unsat'
    assert C.logic_of(list(rec.texts.values())[1]) == 'QF_LIA'
    assert C.decide('(declare-fun x () Int)\n(assert (> x 0))\n(check-sat)\n')['result'] == 'sat'
    assert C.decide('(assert (> x 0))\n(check-sat)\n')['result'] == 'error'
    got = C.decide(list(rec.texts.values())[1], proof=True)
    assert got['result'] == 'unsat' and got['proof'].lstrip().startswith('(')


def test_mod_left_open_can_only_say_unsat(monkeypatch):
    f = '(declare-fun x () Int)\n(declare-fun |a (mod b|() Int)\n(assert (= (mod x 4) (str.len "(mod ")))\n(check-sat)\n'
    loose = C.abstracted(f)
    assert loose.splitlines()[0] == '(declare-fun fcp_mod (Int Int) Int)'
    assert '(= (fcp_mod x 4) (str.len "(mod "))' in loose and '|a (mod b|' in loose   # names and strings are kept
    assert C.abstracted('(assert (> x 0))') is None and C.abstracted(loose) is None
    # equal arguments give equal values under every reading of the function: decided on the looser text alone
    same = '(declare-fun x () Int)\n(declare-fun y () Int)\n(assert (= x y))\n' \
           '(assert (distinct (mod (+ x 7) 9) (mod (+ y 7) 9)))\n(check-sat)\n'
    asked = []

    def once(answer):
        def fake(text, logic, opts, tlimit, proof):
            asked.append('fcp_mod' in text)
            return {'result': answer if 'fcp_mod' in text else 'unknown', 'logic': logic}
        return fake
    monkeypatch.setattr(C, '_once', once('unsat'))
    got = C.decide(same)
    assert got['result'] == 'unsat' and got['abstraction'] == 'mod' and asked == [False, False, True]
    monkeypatch.setattr(C, '_once', once('sat'))     # a model of the looser formula is none of this one
    got = C.decide(same)
    assert got['result'] == 'unknown' and 'abstraction' not in got
    monkeypatch.undo()
    assert C._once(C.abstracted(same), 'QF_UFLIA', {}, 5000, False)['result'] == 'unsat'
    odd = same.replace('(= x y)', '(= x (+ y 9))')    # true of mod, not of every function
    assert C._once(odd, 'QF_LIA', {}, 5000, False)['result'] == 'unsat'
    assert C._once(C.abstracted(odd), 'QF_UFLIA', {}, 5000, False)['result'] == 'sat'
    assert 'abstraction' not in C.decide(odd)


def test_a_verdict_is_as_good_as_the_formulas_behind_it():
    rec = C.Recorder()
    rec.texts = {d: '' for d in 'abcd'}
    rec.by = {C.SHARED: ['a'], 'R-1': ['b'], 'R-2': ['c'], 'R-3': ['d']}
    pr = {'requirements': {'R-1': {'status': 'PROVED'}, 'R-2': {'status': 'PROVED-BOUNDED'},
                           'R-3': {'status': 'PROVED'}, 'R-4': {'status': 'FAILS'}}}
    ans = {'a': {'result': 'unsat'}, 'b': {'result': 'unsat'}, 'c': {'result': 'unknown'}, 'd': {'result': 'sat'}}
    got = C.confirmations(pr, rec, ans)
    assert {r: c['status'] for r, c in got.items()} == {'R-1': 'confirmed', 'R-2': 'unconfirmed', 'R-3': 'refuted'}
    assert got['R-1'] == {'formulas': 2, 'own': 1, 'status': 'confirmed'} and got['R-3']['open'] == {'d': 'sat'}
    ans['a'] = {'result': 'unknown'}                 # a shared formula left open leaves every verdict open
    assert C.confirmations(pr, rec, ans)['R-1']['status'] == 'unconfirmed'
    rec.by = {}
    assert C.confirmations(pr, rec, ans)['R-1'] == {'formulas': 0, 'own': 0, 'status': 'none'}


def test_the_proofs_of_a_study_are_confirmed():
    """The payment retry (corpus/code_pay): every requirement the reference is proved to meet is
    confirmed by cvc5, each on its own formula; the planted conflict fails and has nothing to confirm.
    A formula with a model, slipped in among those behind a verdict, refutes it."""
    from fcp import effects as FX
    B = os.path.join(ROOT, 'corpus', 'code_pay')
    S = Session(B, sets=['gold'])
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    runs = FX.scope(S, fn, ifc, small=True)
    src = os.path.join(B, 'impl', 'ref.py')
    res = FX.run(fn, ifc, src, runs)
    with C.recording() as rec:
        out = P.prove_effects(S, 'gold', fn, ifc, src, runs, res)
    proved = {r for r, x in out['requirements'].items() if x['status'] == 'PROVED'}
    assert proved and 'R-KEEP-1' not in proved and C.SHARED not in rec.by
    assert set(rec.by) == proved and all(len(ds) == 1 for ds in rec.by.values())
    ck = C.Checker(workers=2)
    try:
        answers = ck.check(rec.texts)
        confs = C.confirmations(out, rec, answers)
        assert set(confs) == proved and {c['status'] for c in confs.values()} == {'confirmed'}
        rec.texts['planted'] = '(declare-fun x () Int)\n(assert (> x 0))\n(check-sat)\n'
        rec.by['R-RET-1'].append('planted')
        confs = C.confirmations(out, rec, ck.check(rec.texts))
    finally:
        ck.close()
    assert confs['R-RET-1']['status'] == 'refuted' and confs['R-RET-1']['open'] == {'planted': 'sat'}
    assert {c['status'] for r, c in confs.items() if r != 'R-RET-1'} == {'confirmed'}


def test_one_more_go_spends_its_time_on_the_looser_text_first(monkeypatch):
    text = '(declare-fun x () Int)\n(assert (= (mod x 4) 5))\n(check-sat)\n'
    asked = []

    def fake(body, logic, opts, tlimit, proof):
        asked.append(('fcp_mod' in body, tlimit, logic))
        return {'result': 'unknown', 'logic': logic, 'why': 'unknown (TIMEOUT)'}

    monkeypatch.setattr(C, '_once', fake)
    ans = C.decide(text, 5000, total=5000)
    assert asked[0][0] and 4900 <= asked[0][1] <= 5000
    assert [(loose, logic) for loose, _, logic in asked[1:]] == [(False, 'QF_NIA'), (False, 'ALL')] or \
        [(loose, logic) for loose, _, logic in asked[1:]] == [(False, 'QF_LIA'), (False, 'ALL')]
    assert all(ms <= 5000 for _, ms, _ in asked)
    assert ans['result'] == 'unknown' and 'mod left open' in ans['why']


def test_again_settles_what_was_left_open():
    text = '(declare-fun x () Int)\n(assert (and (> x 3) (< x 3)))\n(check-sat)\n'
    ck = C.Checker(workers=1, tlimit=1000)
    try:
        ck.known = {'a': {'result': 'unknown', 'why': 'unknown (TIMEOUT)', 'seconds': 2.0},
                    'b': {'result': 'unsat', 'seconds': 0.1}}
        assert ck.again({'a': text, 'b': text}, 4000) == ['a']
    finally:
        ck.close()
    assert ck.known['a']['result'] == 'unsat' and ck.known['a']['again'] == 4000 and ck.known['a']['seconds'] >= 2.0
    assert ck.known['b'] == {'result': 'unsat', 'seconds': 0.1}
