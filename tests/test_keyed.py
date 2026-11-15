"""Proofs for objects that hold dictionaries and lists (fcp.keyedproof), on
corpus/code_limit (a rate limiter that keeps, per user, the times of the
calls it allowed)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_limit')
sys.path.insert(0, ROOT)

from fcp import keyedproof as KP  # noqa: E402
from fcp import prove as P  # noqa: E402
from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402

PROVABLE = {'R-ERR-1', 'R-MAX-1', 'R-PEN-1', 'R-RET-1'}


def _short_sequences(S, fn, longest):
    calls, cur = [], []
    for c in SW.calls_for(S, fn, small=True) + [None]:
        if c is None:
            if 0 < len(cur) <= longest:
                calls += [None] + cur
            cur = []
        else:
            cur.append(c)
    return calls


def _texts(G):
    return {KP.text_of(G['facts'], ac) for ac in G['cands']}


def test_a_slot_of_a_list_is_mentioned_only_where_the_list_is_that_long():
    import z3
    n, a, b, t = z3.Ints('n a b t')
    vs = [('len(q)', 'int', 'len', n), ('q[0]', 'int', 'el', a), ('q[1]', 'int', 'el', b), ('t', 'int', 'num', t)]
    texts = _texts(KP.grammar(z3, vs, [0, 60], 2))
    assert {'t >= 0', 'len(q) <= 2', 'len(q) <= 1 -> t >= 60', 'len(q) > 0 -> q[0] + 60 <= t',
            'len(q) > 0 -> t <= q[0] + 60', 'len(q) > 1 -> q[0] <= q[1]', 'len(q) == 2 -> q[1] <= t'} <= texts
    for text in texts:
        guard, _, fact = text.rpartition(' -> ')
        if 'q[1]' in fact:
            assert guard in ('len(q) > 1', 'len(q) == 2'), text
        elif 'q[0]' in fact:
            assert guard in ('len(q) > 0', 'len(q) > 1', 'len(q) == 1', 'len(q) == 2'), text
    only = _texts(KP.grammar(z3, vs, [0, 60], 2, must={'t'}))
    assert only and only < texts and all('t' in x.replace('->', '') for x in only)


def test_the_samples_set_aside_what_another_candidate_implies():
    """Candidates a sampled state refutes are dropped; of two that hold on
    every sample, the weaker waits for the stronger to fail."""
    import z3
    x, y = z3.Ints('x y')
    G = KP.grammar(z3, [('x', 'int', 'num', x), ('y', 'int', 'num', y)], [0, 10], 0)
    g = P.compile_terms(z3, [t for _, t, _ in G['facts']], [x, y])
    kept, aside = KP.sift(g, G, [(0, 20), (0, 30)])
    assert {KP.text_of(G['facts'], ac) for ac in kept} == {'x >= 0', 'x <= 0', 'y >= 10', 'x + 10 <= y'}
    assert {by: [KP.text_of(G['facts'], ac) for ac in acs] for by, acs in aside.items()} == \
        {'x <= 0': ['x <= 10'], 'y >= 10': ['y >= 0'], 'x + 10 <= y': ['x <= y'], 'x <= y': ['x <= y + 10']}
    kept, aside = KP.sift(g, G, [(0, 20), (0, 30)], keep=frozenset({'x <= 10'}))
    assert 'x <= 10' in {KP.text_of(G['facts'], ac) for ac in kept} and 'x <= 0' not in aside
    assert KP.sift(g, G, []) == (G['cands'], {})


def test_the_step_keeps_the_candidates_that_are_proved_from_the_ones_kept():
    """x' = x + 1, y' = y + x, z' = z while x <= 5 and z - 1 after: z >= 0
    is proved while x <= 5 is a candidate, and dropped with it."""
    import z3
    x, y, z, x1, y1, z1 = z3.Ints('x y z x1 y1 z1')
    sol = z3.Solver()
    sol.add(x1 == x + 1, y1 == y + x, z1 == z3.If(x <= 5, z, z - 1))
    pre = [z >= 0, x >= 0, y >= 0, x <= 5]
    lit = {i: z3.Bool(f'inv_{i}') for i in range(len(pre))}
    for i, c in enumerate(pre):
        sol.add(z3.Implies(lit[i], c))
    post = {i: z3.substitute(c, (x, x1), (y, y1), (z, z1)) for i, c in enumerate(pre)}
    core = {}
    alive, undecided = KP.houdini_step(z3, sol, [0, 1, 2, 3], post, lit, batch=2, core=core)
    assert (sorted(alive), undecided) == ([1, 2], 0)
    assert core == {1: frozenset({1}), 2: frozenset({1, 2})}
    more, _ = KP.houdini_step(z3, sol, alive, post, lit, core=core)      # nothing is left to prove
    assert more == alive


def test_a_limiter_is_proved_over_bounded_sequences():
    """Every sequence of up to five calls, for every user: the reference
    keeps four requirements and breaks the fair one where the prompt
    contradicts itself, at a sequence z3 chose, replayed; a planted bug
    (C3: the penalty counts from the first call) is found the same way."""
    S = Session(B, sets=['gold'])
    fn = SW.function(S)
    calls = _short_sequences(S, fn, 5)
    src = os.path.join(B, 'impl', 'ref.py')
    out = P.prove_object(S, 'gold', fn, src, calls, SW.run(fn, src, calls), induct=False)
    assert out['status'] == 'ok' and out['keyed'] and out['k'] == 5 and not out['exact'], out
    reqs = out['requirements']
    assert {r for r, x in reqs.items() if x['status'] == 'PROVED-BOUNDED'} == PROVABLE
    fair = reqs['R-FAIR-1']
    assert fair['status'] == 'FAILS' and fair['confirmed'] and len(fair['calls']) == 5
    user = fair['rigids']['U']
    assert sum(c.startswith(f'allow({user},') for c in fair['calls']) >= 4
    src = os.path.join(B, 'bugs', 'C3.py')
    out = P.prove_object(S, 'gold', fn, src, calls, SW.run(fn, src, calls), only={'R-PEN-1'}, induct=False)
    pen = out['requirements']['R-PEN-1']
    assert pen['status'] == 'FAILS' and pen['confirmed'], out


def test_a_limiter_is_proved_for_every_sequence_by_induction():
    """Sequences of any length: the state after any number of calls is a
    dictionary of lists, abstracted to its value at the reading's user and
    at any other key; the invariant is found among candidates the scope's
    states do not refute.  The fair requirement still fails."""
    S = Session(B, sets=['gold'])
    fn = SW.function(S)
    calls = _short_sequences(S, fn, 5)
    src = os.path.join(B, 'impl', 'ref.py')
    out = P.prove_object(S, 'gold', fn, src, calls, SW.run(fn, src, calls))
    assert out['status'] == 'ok' and out['keyed'] and not out['exact'], out
    ind, reqs = out['induction'], out['requirements']
    assert ind['status'] == 'ok' and (ind['window'], ind['cap'], ind['undecided']) == (1, 3, 0), ind
    assert 0 < ind['invariant'] < ind['candidates']
    assert {r for r, x in reqs.items() if x['status'] == 'PROVED'} == PROVABLE
    assert all(reqs[r]['invariant'] for r in PROVABLE)
    assert any(t.startswith('len(self.allowed[U]) >') for t in reqs['R-MAX-1']['invariant'])
    assert reqs['R-FAIR-1']['status'] == 'FAILS' and reqs['R-FAIR-1']['confirmed']


def test_the_distances_are_the_numbers_the_code_and_the_reading_add_or_subtract():
    """now - t < 60 and now + 10 in the code, also behind a name (WINDOW =
    60, self.COOLDOWN_SECONDS); ncalls + 1 in a reading.  Not 3 (a count),
    1000 (a bound on the user) or the times of a reading's scenarios.
    Where the comparison keeps the distance itself (now - t <= 60 in C1,
    t >= now - 60 and span > 60 in agent A's reading), the next number too."""
    srcs = [os.path.join(B, 'impl', 'ref.py')] + \
        [os.path.join(B, 'agents', f'coder_{m}', 'rate_limiter.py') for m in ('haiku', 'sonnet', 'opus')]
    for s, want in (('gold', [10, 60]), ('agent_b', [1, 10, 60])):
        S = Session(B, sets=[s])
        assert [P._distances(S, s, src) for src in srcs] == [want] * 4
        assert len([c for c in P._consts(S, s, srcs[0]) if c > 0]) > 6
    closed = os.path.join(B, 'bugs', 'C1.py')
    assert P._distances(S, 'agent_b', closed) == [1, 10, 60, 61]
    S = Session(B, sets=['agent_a'])
    assert [P._distances(S, 'agent_a', src) for src in (srcs[0], closed)] == [[10, 11, 60, 61]] * 2
