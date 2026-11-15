"""Equivalence sweeping (fcp.sweep): agreements between the subterms of a
goal, found on samples and proved by z3 from the leaves up, and the proofs
for code over strings that rest on it (corpus/code_mask)."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_mask')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'experiments'))

z3 = pytest.importorskip('z3')

from fcp import prove as P  # noqa: E402
from fcp import software as SW  # noqa: E402
from fcp import sweep as W  # noqa: E402
from fcp.analyses import Session  # noqa: E402


def same(a, b, *assume) -> bool:
    s = z3.Solver()
    s.add(*assume)
    s.add(a != b)
    return s.check() == z3.unsat


def test_division_as_z3_defines_it():
    for a in range(-7, 8):
        for b in range(-3, 4):
            if b:
                assert W._div(a, b) == z3.simplify(z3.IntVal(a) / z3.IntVal(b)).as_long(), (a, b)
                assert W._mod(a, b) == z3.simplify(z3.IntVal(a) % z3.IntVal(b)).as_long(), (a, b)


def test_a_goal_is_the_conjunction_of_its_parts():
    x, y = z3.Ints('x y')
    p, q = z3.Bools('p q')
    tree = z3.If(x > 3, 1, z3.If(z3.And(p, y < x), 0, z3.If(q, 0, 2)))
    for g, n in [(z3.And(p, z3.And(q, x > 0)), 3),
                 (z3.Not(z3.Implies(z3.And(p, x > 0), q)), 3),
                 (z3.Not(z3.Or(p, z3.Not(q), x == y)), 3),
                 (z3.Not(z3.And(z3.Implies(p, q), True)), 2),          # And(x, True) is x
                 (tree == 0, 2),                                        # not the first end, and one of the others
                 (z3.Not(tree == 1), 1),
                 (0 != tree, 1),
                 (z3.Or(p, q), 1)]:
        parts = W.conjuncts(z3, g)
        assert len(parts) == n, (g, parts)
        assert same(z3.And(*parts), g), g
    assert W.conjuncts(z3, z3.BoolVal(True)) == []


def luhn_two_ways(n: int = 8):
    """The Luhn sum of n digits: doubled by arithmetic, and by a table."""
    xs = [z3.Int(f'd{i}') for i in range(n)]
    table = [0, 2, 4, 6, 8, 1, 3, 5, 7, 9]

    def by_rule(d):
        return z3.If(2 * d > 9, 2 * d - 9, 2 * d)

    def by_table(d):
        out = z3.IntVal(table[9])
        for v in range(8, -1, -1):
            out = z3.If(d == v, table[v], out)
        return out
    a = z3.IntVal(0)
    b = z3.IntVal(0)
    for i, d in enumerate(xs):
        a = a + (by_rule(d) if i % 2 else d)
        b = b + (by_table(d) if i % 2 else d)
    return xs, [z3.And(0 <= d, d <= 9) for d in xs], a % 10 == 0, b % 10 == 0


def test_agreements_are_proved_from_the_leaves_up():
    xs, dom, a, b = luhn_two_ways()
    samples = [[(7 * i + 3 * j) % 10 for j in range(len(xs))] for i in range(40)]
    (na, nb), st = W.sweep(z3, [a, b], xs, dom, samples)
    assert na.eq(nb)                                   # one term: the two sides are the same function
    assert st['merged'] >= len(xs) // 2 and st['unknown'] == 0
    assert same(na, a, *dom)                           # and it is the goal that went in


def test_nothing_is_merged_on_the_samples_alone():
    x = z3.Int('x')
    a, b = x * x + 1, x + 1                            # equal at 0 and 1, the only samples
    (na, nb), st = W.sweep(z3, [a > 5, b > 5], [x], [x >= 0], [[0], [1]])
    assert st['refuted'] >= 1 and st['samples'] > 2    # z3's model is one more sample
    assert not na.eq(nb)
    assert same(na, a > 5, x >= 0) and same(nb, b > 5, x >= 0)


def test_assumptions_decide_what_agrees():
    x, y = z3.Ints('x y')
    a, b = z3.If(x >= 0, x, -x) + y, x + y
    samples = [[i, 3 - i] for i in range(6)]
    (na, nb), _ = W.sweep(z3, [a > 2, b > 2], [x, y], [x >= 0], samples)
    assert na.eq(nb)
    (na, nb), _ = W.sweep(z3, [a > 2, b > 2], [x, y], [], samples)
    assert not na.eq(nb)                               # without x >= 0 the two differ, and stay apart


def test_a_term_the_evaluator_cannot_run_is_left_alone():
    x = z3.Int('x')
    f = z3.Function('f', z3.IntSort(), z3.IntSort())
    roots = [f(x) > 0]
    out, st = W.sweep(z3, roots, [x], [], [[1]])
    assert out[0].eq(roots[0]) and 'skipped' in st


# -- code over strings: card masking -----------------------------------------------------

@pytest.fixture(scope='module')
def mask():
    from prove_demo import implementations
    S = Session(B, sets=['gold'])
    fn = SW.function(S)
    calls = SW.calls_for(S, fn, small=True)
    return S, fn, calls, implementations(B, fn.name, fn.module or '')


def test_the_translation_of_string_code_matches_the_code(mask):
    S, fn, calls, impl = mask
    assert fn.has_seq
    ref = SW.run(fn, impl['ref'], calls)
    tr = P.Translator(impl['ref'], fn.name, seqs=True)
    assert P.check_translation(fn, tr, calls, ref) is None
    # the same terms against what another implementation did: the check sees the difference
    other = SW.run(fn, impl['C7'], calls)
    assert P.check_translation(fn, tr, calls, other) is not None
    with pytest.raises(P.Untranslatable):
        P.check_translation(fn, P.Translator(impl['C9'], fn.name, seqs=True), calls, ref)


def test_path_conditions_are_chains_of_facts(mask):
    """The path that returns is the conjunction of what each step added (one
    fact per character checked), not a disjunction of paths: the proofs of
    what the code returns take these facts as assumptions."""
    from fcp import seqs as Q
    S, fn, calls, impl = mask
    enc = SW._IntSpec(S, ['gold'], fn, 1)
    for name, least in (('ref', 3), ('haiku', 32), ('opus', 32)):     # the models check character by character
        tr = P.Translator(impl[name], fn.name, seqs=True)
        ends = tr.ends(fn, [enc.x[(sig, 1)] for _, sig, _ in fn.args])
        ret = [c for c, kind, _, _, _ in ends if kind == 'return']
        assert len(ret) == 1, name
        facts = Q.since(z3, ret[0], z3.BoolVal(True))
        assert facts is not None and len(facts) >= least, name


def test_string_code_is_proved_and_broken_beyond_the_scope(mask):
    S, fn, calls, impl = mask
    res = SW.run(fn, impl['ref'], calls)
    pr = P.prove(S, 'gold', fn, impl['ref'], calls, res)
    assert pr['status'] == 'ok' and pr['exact']
    got = {r: x['status'] for r, x in pr['requirements'].items()}
    # the Luhn sum as the code computes it and as the reading defines it: equal, piece by piece
    assert got['R-RET-1'] == got['R-ERR-1'] == got['R-MASK-1'] == got['R-LAST4-1'] == got['R-SEP-1'] == 'PROVED'
    assert pr['sweep']['merged'] > 1000 and pr['sweep']['unknown'] == 0
    bad = pr['requirements']['R-QUARTER-1']                   # the last four of twelve digits: more than a quarter
    assert bad['status'] == 'FAILS' and bad['confirmed']
    shown = bad['replay']['ret']
    assert bad['replay']['code'] == [0] and shown


def test_facts_of_the_path_are_assumptions(mask):
    """str.isdigit() is true of more than the ASCII digits, so the Luhn sum
    of C2 is the reading's only where the number is valid: proved with the
    reading's own facts (every character a digit or a separator) assumed."""
    S, fn, calls, impl = mask
    res = SW.run(fn, impl['C2'], calls)
    pr = P.prove(S, 'gold', fn, impl['C2'], calls, res, only={'R-RET-1', 'R-ERR-1'})
    ret, err = pr['requirements']['R-RET-1'], pr['requirements']['R-ERR-1']
    assert ret['status'] == 'PROVED'
    assert ret['sweep'][0]['small'] >= 32 and ret['sweep'][0]['merged'] > 0
    assert err['status'] == 'FAILS' and err['confirmed']
    (number,), = err['calls']
    assert any(c in number for c in '\xb2\xb3\xb9')           # a superscript digit, accepted


def test_the_ends_of_an_if_tree():
    x = z3.Int('x')
    assert P._leaves(z3, z3.If(x > 0, 0, z3.If(x < -3, 2, 0))) == [0, 2]
    assert P._leaves(z3, z3.If(x > 0, 0, x)) is None           # an end that is not a constant: no cases


def test_a_goal_that_says_nothing_of_the_path_is_split_by_outcome():
    """agent_a states the quarter rule of every call, not of the calls that
    return, so its goal has no fact of the path to assume.  It is proved case
    by case, one per outcome of the call, each with that outcome's facts."""
    from prove_demo import implementations
    S = Session(B, sets=['agent_a'])
    fn = SW.function(S)
    calls = SW.calls_for(S, fn, small=True)
    src = implementations(B, fn.name, fn.module or '')['haiku']
    pr = P.prove(S, 'agent_a', fn, src, calls, SW.run(fn, src, calls), only={'R-QUARTER-1'})
    q = pr['requirements']['R-QUARTER-1']
    assert q['status'] == 'PROVED'
    cases = q['sweep'][0]['cases']
    assert [c['outcome'] for c in cases] == [0, 1, 2]           # returned, ValueError, anything else
    assert cases[0]['small'] >= 32 and cases[0]['merged'] > 0


def test_a_failure_found_item_by_item_is_replayed(mask, monkeypatch):
    """With no time for the goal as a whole, the failure is found on the item,
    under the facts of its path, and replayed on the code like any other."""
    S, fn, calls, impl = mask
    monkeypatch.setattr(P, 'WHOLE', 1)
    res = SW.run(fn, impl['C3'], calls)
    pr = P.prove(S, 'gold', fn, impl['C3'], calls, res, only={'R-LAST4-1'})
    bad = pr['requirements']['R-LAST4-1']                     # the last four characters, not digits
    assert bad['status'] == 'FAILS' and bad['confirmed'] and bad['items']
    assert bad['sweep'][0]['small'] >= 32


def test_two_readings_of_a_checksum_are_compared_piece_by_piece():
    """My reading and agent_a's define the Luhn sum differently.  z3 does not
    decide whether they agree on the whole formula; with the items swept it
    does, in seconds, and a difference it finds is confirmed on the monitors."""
    S = Session(B, sets=['gold', 'agent_a'])
    fn = SW.function(S)
    ctx = SW.compare(S, 'gold', 'agent_a', fn, context=True, only={'R-ERR-1', 'R-RET-1', 'R-MASK-1'}, bit_timeout=0)
    assert [ctx[r]['relation'] for r in ('R-ERR-1', 'R-RET-1', 'R-MASK-1')] == ['EQUIVALENT'] * 3
    assert ctx['R-ERR-1']['engine'] == ctx['R-RET-1']['engine'] == 'z3-int+sweep'
    assert ctx['R-MASK-1']['engine'] == 'z3-int'               # decided as before, nothing swept
    plain = SW.compare(S, 'gold', 'agent_a', fn, only={'R-RET-1'}, bit_timeout=0)
    assert plain['R-RET-1']['relation'] == 'A-WEAKER'          # alone, agent_a's says more: half the digits hidden
    assert plain['R-RET-1']['witness_a_not_b']['lines']
