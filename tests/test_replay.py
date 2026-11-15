"""Every call that a review shows under a question about two readings is run
again before it is shown.  Found on the HumanEvalComm pilot: a script that
read every shown line back and ran it on the compiled monitors
(experiments/comm_replay.py) found a call that no reading rejected (`fib4(8)`
on HumanEval/46, 1a), after the review had been written.  The engine now does
what the script did, as a step of the check: the line is read back
(software.read_line), must print as it was shown, and its calls must separate
the two readings on their monitors (software.separates).  A call that does
not pass is not shown: the requirement is undecided, and the review names the
call it dropped."""
import copy
import os
import shutil
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_checkout')
sys.path.insert(0, ROOT)

from fcp import review as RV  # noqa: E402
from fcp import rv  # noqa: E402
from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402

# from a subtotal of 6 on, the price is PRICE and shipping is free; below 6 the call raises
READING = '''
    fcp: "0.1"
    set: NAME
    origin: {kind: human, role: formalizer, id: NAME}
    properties:
      - {id: T-P, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal >= 6', cond: 'outcome == 0 && price == PRICE && ship == 0'}}
      - {id: T-Q, req: R-ERR-1, pattern: implies, args: {trigger: 'subtotal < 6', cond: 'outcome == 1'}}
'''
# the rule of v, stated for every q of ten values
RIGID = '''
    fcp: "0.1"
    set: w
    origin: {kind: human, role: formalizer, id: w}
    rigids:
      - {name: q, range: [0, 9]}
    properties:
      - {id: T-P, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal == q + 6', cond: 'outcome == 0 && price == subtotal - 1 && ship == 0'}}
      - {id: T-Q, req: R-ERR-1, pattern: implies, args: {trigger: 'subtotal < 6', cond: 'outcome == 1'}}
'''
U_NOT_V = 'checkout(6, 0, False) -> (6, 0)'            # u accepts it, v rejects it
V_NOT_U = 'checkout(6, 0, False) -> (5, 0)'
NEITHER = 'checkout(6, 0, False) -> (7, 0)'            # both reject it
STEP = 'the comparison of u and v, in context'


def bundle(tmp, **prices) -> str:
    """The checkout bundle with one small reading per name: the price it states from 6 on."""
    b = tmp / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    for s, p in prices.items():
        (b / 'formal' / f'{s}.yaml').write_text(textwrap.dedent(READING).replace('NAME', s).replace('PRICE', p))
    return str(b)


@pytest.fixture(scope='module')
def two(tmp_path_factory):
    """Readings u (the price is the subtotal), v (one less) and w (as v, by a rule over ten values)."""
    b = bundle(tmp_path_factory.mktemp('two'), u='subtotal', v='subtotal - 1')
    with open(os.path.join(b, 'formal', 'w.yaml'), 'w') as f:
        f.write(textwrap.dedent(RIGID))
    S = Session(b, sets=['u', 'v', 'w'])
    return S, SW.function(S)


def both(a=U_NOT_V, b=V_NOT_U) -> dict:
    """What a comparison of u and v returns, with these two lines."""
    return {'R-ERR-1': {'relation': 'EQUIVALENT'},
            'R-RET-1': {'relation': 'INCOMPARABLE', 'witness_a_not_b': {'lines': [a]},
                        'witness_b_not_a': {'lines': [b]}}}


# ---------------------------------------------------------------- a printed line, read back
def test_a_printed_line_reads_back_to_its_call(two):
    S, fn = two
    for c, o, valued in [((6, 0, False), {'price': 6, 'ship': 0, 'outcome': 0}, True),
                         ((2097151, 127, True), {'price': 2097151, 'ship': 1023, 'outcome': 0}, True),
                         ((5, 0, True), {'price': 0, 'ship': 0, 'outcome': 1}, False),
                         ((5, 0, True), {'price': 0, 'ship': 0, 'outcome': 2}, False),
                         ((0, 0, False), {'price': 0, 'ship': 0, 'outcome': 3}, False)]:
        text = SW.line(fn, c, o)
        assert SW.read_line(fn, text) == (c, o, valued), text
    assert SW.line(fn, (5, 0, True), {'outcome': 1}) == 'checkout(5, 0, True) -> raised ValueError'
    assert SW.read_line(fn, U_NOT_V) == ((6, 0, False), {'price': 6, 'ship': 0, 'outcome': 0}, True)


def test_a_line_with_strings_reads_back_to_its_call():
    S = Session(os.path.join(ROOT, 'corpus', 'code_mask'))
    fn = SW.function(S)
    assert SW.printable(fn) and fn.seqs['number'] == (8, 32)
    for number, masked in [('4111 1111', '**** 1111'), ('', ''), ('a"b\\c', "'"), ('x) -> "y', ') -> '),
                           ('caf\xe9', '\xff'), ('1' * 32, '*' * 32)]:
        text = SW.line(fn, (number,), {'masked': masked, 'outcome': 0})
        assert SW.read_line(fn, text) == ((number,), {'masked': masked, 'outcome': 0}, True), text
    assert SW.read_line(fn, 'mask_card(") -> ") -> raised ValueError') == ((') -> ',), {'masked': '', 'outcome': 1}, False)
    for text in ['mask_card("€") -> ""',                  # a character that no slot of 8 bits carries
                 f'mask_card("{"1" * 33}") -> ""',             # longer than the signal
                 'mask_card([52, 49]) -> ""', 'mask_card("4") -> 4', 'mask_card("4") -> None',
                 "mask_card('4') -> " + '"4" -> "4"', 'mask_card("4) -> "4"']:
        with pytest.raises(ValueError):
            SW.read_line(fn, text)


@pytest.mark.parametrize('text', [
    '', 'checkout', 'checkout(6, 0, False)', 'check(6, 0, False) -> (6, 0)', ' checkout(6, 0, False) -> (6, 0)',
    'checkout(6, 0) -> (6, 0)', 'checkout(6, 0, False, 1) -> (6, 0)', 'checkout() -> (6, 0)',
    'checkout(6, 0, 0) -> (6, 0)',                             # 0 is no bool
    'checkout(True, 0, False) -> (6, 0)',                      # and True is no number
    'checkout(2097152, 0, False) -> (6, 0)',                   # beyond the 21 bits of the subtotal
    'checkout(-1, 0, False) -> (6, 0)', 'checkout(6.0, 0, False) -> (6, 0)', 'checkout(None, 0, False) -> (6, 0)',
    'checkout(6, 0, False) -> (6, 1024)',                      # beyond the 10 bits of the shipping
    'checkout(6, 0, False) -> six', 'checkout(6, 0, False) -> (6, 0, 1)', 'checkout(6, 0, False) -> 6',
    'checkout(6, 0, False) -> [6, 0]', 'checkout(6, 0, False) -> ', 'checkout(6, 0, False) -> (6, 0',
    'checkout(6, 0, False) -> raised KeyError', 'checkout(6, 0, False) -> returned',
    'checkout(6, 0, False) -> ended with code 9, which names no ending',
    'checkout(6, 0, __import__("os")) -> (6, 0)', 'checkout(6, 0, False) -> (6, 0) -> (6, 0)'])
def test_a_line_that_names_no_call_is_not_read(two, text):
    with pytest.raises(ValueError):
        SW.read_line(two[1], text)


def test_only_a_function_of_plain_values_prints_its_whole_call():
    """An object's calls share its state, and the line of a change does not
    carry what the code before it answered: such calls are not replayed
    from their lines."""
    for name, plain in [('code_checkout', True), ('code_mask', True), ('code_limit', False), ('code_invoice', False),
                        ('code_change', False)]:
        S = Session(os.path.join(ROOT, 'corpus', name))
        assert SW.printable(SW.function(S)) is plain, name
    assert SW.shows(both()) and not SW.shows({'R-RET-1': {'relation': 'EQUIVALENT'}, '<assumptions>': []})
    assert not SW.shows({'R-RET-1': {'relation': 'UNKNOWN', 'witness_a_not_b': None, 'dropped': {}}})


# ---------------------------------------------------------------- the calls of a comparison, run again
def test_the_calls_that_a_comparison_finds_pass_the_replay(two):
    S, fn = two
    recs = SW.compare(S, 'u', 'v', fn, context=True)
    assert recs['R-RET-1']['relation'] == 'INCOMPARABLE' and recs['R-ERR-1']['relation'] == 'EQUIVALENT'
    assert recs['R-RET-1']['witness_a_not_b']['lines'] == [U_NOT_V]
    assert recs['R-RET-1']['witness_b_not_a']['lines'] == [V_NOT_U]
    before = copy.deepcopy(recs)
    S.__dict__.pop('_replayed', None)          # what the comparison simulated is forgotten: every call is simulated here
    got = SW.replayed(S, 'u', 'v', fn, recs, context=True)
    assert recs == before                      # the records of the comparison are left as they are
    assert got['R-RET-1']['witness_a_not_b'] == {**before['R-RET-1']['witness_a_not_b'], 'replayed': True}
    assert got['R-RET-1']['witness_b_not_a'] == {**before['R-RET-1']['witness_b_not_a'], 'replayed': True}
    assert got['R-RET-1']['relation'] == 'INCOMPARABLE' and 'dropped' not in got['R-RET-1']
    assert got['R-ERR-1'] == before['R-ERR-1']
    assert len(S.__dict__['_replayed']) == 4   # two lines on two monitors, and no line simulated twice
    assert SW.replayed(S, 'u', 'v', fn, recs, context=False) == got      # plain: the rules of the requirement alone


def test_separates_reads_a_call_as_the_comparison_reads_a_witness(two):
    S, fn = two

    def sep(text, acc, rej, req='R-RET-1', context=True):
        c, o, _ = SW.read_line(fn, text)
        return SW.separates(S, fn, {'calls': [c], 'outs': [o]}, acc, rej, req, context)
    assert sep(U_NOT_V, 'u', 'v') and not sep(U_NOT_V, 'v', 'u')
    assert sep(V_NOT_U, 'v', 'u') and not sep(V_NOT_U, 'u', 'v')
    assert not sep(NEITHER, 'u', 'v') and not sep(NEITHER, 'v', 'u')    # the accepting reading rejects it too
    assert not sep(U_NOT_V, 'u', 'v', req='R-ERR-1')                    # rejected, but not by a rule of that requirement
    # in context every rule of the accepting reading counts; alone, the rules of the requirement do
    broken = 'checkout(5, 0, False) -> (5, 0)'                          # below 6 a call raises, in both readings
    assert not sep(broken, 'u', 'v') and not sep(broken, 'u', 'v', context=False)
    assert sep('checkout(6, 0, False) -> raised ValueError', 'u', 'v', context=False) is False


def test_a_call_that_does_not_pass_is_dropped_with_the_reason(two):
    S, fn = two
    recs = both(a=NEITHER)
    before = copy.deepcopy(recs)
    got = SW.replayed(S, 'u', 'v', fn, recs, context=True)
    assert recs == before
    assert got['R-RET-1'] == {
        'relation': 'UNKNOWN', 'witness_b_not_a': {'lines': [V_NOT_U], 'replayed': True},
        'dropped': {'witness_a_not_b': {'lines': [NEITHER], 'why': 'the call does not separate the two readings '
                                                                   'when it is run on their monitors'}}}
    assert got['R-ERR-1'] == {'relation': 'EQUIVALENT'}

    def why(text, **kw):
        got = SW.replayed(S, 'u', 'v', fn, both(a=text), context=True, **kw)['R-RET-1']
        assert got['relation'] == 'UNKNOWN' and 'witness_a_not_b' not in got
        assert got['dropped']['witness_a_not_b']['lines'] == [text]
        return got['dropped']['witness_a_not_b']['why']
    assert why(V_NOT_U) == 'the call does not separate the two readings when it is run on their monitors'
    assert why('checkout(6, 0, False) -> raised ValueError') == \
        'the call does not separate the two readings when it is run on their monitors ' \
        '(its line names an ending, not the values that went with it)'
    assert why('checkout(6,0,False) -> (6, 0)') == 'the call reads back as another call'
    assert why('checkout(06, 0, False) -> (6, 0)').startswith('the call is not read back (no call of checkout with 3')
    assert why('checkout(6, 0, False) -> six') == "the call is not read back ('six' is no result of a call)"
    assert why('checkout(6, 0, 0) -> (6, 0)') == 'the call is not read back (0 is no value of member)'
    assert why(U_NOT_V, seconds=0) == \
        'the call was not replayed (the time for the replays of this comparison was used up)'
    # every direction of every requirement is replayed on its own
    got = SW.replayed(S, 'u', 'v', fn, both(a=NEITHER, b=NEITHER), context=True)['R-RET-1']
    assert got['relation'] == 'UNKNOWN' and sorted(got['dropped']) == ['witness_a_not_b', 'witness_b_not_a']
    assert not SW.shows({'R-RET-1': got})


def test_a_rule_over_more_values_than_a_replay_runs_is_not_replayed(two):
    """A reading's rule stated for every value of a variable is run for every
    value.  Beyond the cases a replay runs through, the call is not shown as
    replayed, and not as failed either."""
    S, fn = two
    recs = {'R-RET-1': {'relation': 'A-WEAKER', 'witness_a_not_b': {'lines': [U_NOT_V]}}}
    assert SW.replayed(S, 'u', 'w', fn, recs, context=True)['R-RET-1']['witness_a_not_b']['replayed'] is True
    S.__dict__.pop('_replayed', None)
    got = SW.replayed(S, 'u', 'w', fn, recs, context=True, cases=9)['R-RET-1']
    assert got == {'relation': 'UNKNOWN', 'dropped': {'witness_a_not_b': {
        'lines': [U_NOT_V], 'why': 'the call was not replayed (w: 10 rigid cases exceed max_cases=9)'}}}
    c, o, _ = SW.read_line(fn, U_NOT_V)
    with pytest.raises(rv.NotReplayed):
        SW.separates(S, fn, {'calls': [c], 'outs': [o]}, 'u', 'w', 'R-RET-1', True, cases=9)
    assert SW.separates(S, fn, {'calls': [c], 'outs': [o]}, 'u', 'w', 'R-RET-1', True, cases=10)


def test_a_simulation_past_its_time_is_not_a_result(two):
    S, fn = two
    c, o, _ = SW.read_line(fn, U_NOT_V)
    tr = SW._trace(S, fn, {'calls': [c], 'outs': [o]})
    with pytest.raises(rv.NotReplayed, match='u: the replay did not end in 0.001 s'):
        rv.check(S, 'u', tr, timeout=0.001)
    assert issubclass(rv.NotReplayed, ValueError)          # what the callers of rv.check caught before
    held = {'F-ZERO': None, 'T-P': None, 'T-Q': None}      # the frame rule of the bundle and the two of the reading
    assert rv.check(S, 'u', tr, timeout=60) == rv.check(S, 'u', tr) == held


def test_the_calls_of_a_comparison_whose_replay_did_not_end_are_not_shown():
    recs = both()
    recs['<assumptions>'] = {'relation': 'EQUIVALENT'}
    before = copy.deepcopy(recs)
    got = SW.unshown(recs, 'the replay did not end')
    assert recs == before and got['R-ERR-1'] == before['R-ERR-1'] and got['<assumptions>'] == before['<assumptions>']
    assert got['R-RET-1'] == {'relation': 'UNKNOWN', 'dropped': {
        'witness_a_not_b': {'lines': [U_NOT_V], 'why': 'the replay did not end'},
        'witness_b_not_a': {'lines': [V_NOT_U], 'why': 'the replay did not end'}}}


# ---------------------------------------------------------------- in a review
def quiet(*a):
    pass


@pytest.fixture
def pair(tmp_path, monkeypatch):
    """A bundle with readings u and v, and searches that answer at once: no
    conflict, no open choice, every scenario possible.  The comparisons and
    the replays are the engine's."""
    for k in ('SCOPE_BUDGET', 'CONFLICT_BUDGET', 'COMPARE_BUDGET'):       # check() sets them: put them back
        monkeypatch.setattr(SW, k, getattr(SW, k))
    monkeypatch.setattr(Session, 'consistency', lambda self, s, **kw: {})
    monkeypatch.setattr(SW, 'conflicts', lambda S, s, fn: {'conflicts': [], 'candidates': 0, 'checked': 0})
    monkeypatch.setattr(SW, 'choices', lambda S, s, fn, signals: {'open': {}, 'checked': 0})
    return bundle(tmp_path, u='subtotal', v='subtotal - 1')


def asked(out, kind):
    return [(q['reqs'], q.get('relation'), q['calls']) for q in out['queue'] if q['kind'] == kind]


def test_a_review_replays_the_calls_it_shows(pair):
    out = RV.check(pair, None, ['u', 'v'], log=quiet)
    assert [s['step'] for s in out['steps']][-3:] == ['the comparison of u and v', STEP,
                                                     f'the replay of the calls of {STEP}']
    assert out['failed'] == [] and 'dropped' not in out
    assert out['readings']['R-RET-1'] == {'plain': 'INCOMPARABLE', 'context': 'INCOMPARABLE', 'witness': [U_NOT_V]}
    assert asked(out, 'readings') == [(['R-RET-1'], 'INCOMPARABLE', [U_NOT_V])]
    assert 'R-ERR-1' in out['certified'] and 'R-RET-1' not in out['certified']
    text = RV.report(Session(pair, sets=['u', 'v']), out)
    assert f'   - `{U_NOT_V}`' in text and 'Calls not shown' not in text and 'This review is partial' not in text
    # readings that agree show no call, and nothing is replayed
    same = RV.check(pair, None, ['u', 'u'], log=quiet)
    assert not [s for s in same['steps'] if s['step'].startswith('the replay')] and asked(same, 'readings') == []


def test_a_review_does_not_show_a_call_that_fails_its_replay(pair, monkeypatch):
    full = RV.check(pair, None, ['u', 'v'], log=quiet)
    real = SW.compare

    def compare(lines):
        def f(S, a, b, fn, context=False, **kw):
            recs = real(S, a, b, fn, context=context, **kw)
            if context:
                for k, x in zip(SW.WITNESSES, lines):
                    recs['R-RET-1'][k]['lines'] = [x]
            return recs
        monkeypatch.setattr(SW, 'compare', f)
        return RV.check(pair, None, ['u', 'v'], log=quiet)

    why = 'the call does not separate the two readings when it is run on their monitors'
    out = compare([NEITHER, V_NOT_U])                  # one direction's call is false: the other's is shown
    assert out['failed'] == []
    assert out['dropped'] == [{'step': STEP, 'req': 'R-RET-1', 'lines': [NEITHER], 'why': why}]
    assert out['readings']['R-RET-1'] == {'plain': 'INCOMPARABLE', 'context': 'UNKNOWN', 'witness': [V_NOT_U]}
    assert asked(out, 'readings') == [(['R-RET-1'], 'UNKNOWN', [V_NOT_U])]
    assert out['certified'] == full['certified']
    text = RV.report(Session(pair, sets=['u', 'v']), out)
    assert '\n## Calls not shown\n' in text and f'\n- R-RET-1 ({STEP}): {why}\n' in text
    assert NEITHER not in text and f'   - `{V_NOT_U}`' in text and 'This review is partial' not in text

    out = compare([NEITHER, NEITHER])                  # both are: an undecided question is left, without a call
    assert [d['lines'] for d in out['dropped']] == [[NEITHER], [NEITHER]]
    assert out['readings']['R-RET-1'] == {'plain': 'INCOMPARABLE', 'context': 'UNKNOWN', 'witness': None}
    assert asked(out, 'undecided') == [(['R-RET-1'], 'UNKNOWN', [])] and asked(out, 'readings') == []
    assert out['certified'] == full['certified']
    assert NEITHER not in RV.report(Session(pair, sets=['u', 'v']), out)


def test_a_replay_that_does_not_end_leaves_a_partial_review_without_the_calls(pair, monkeypatch):
    full = RV.check(pair, None, ['u', 'v'], log=quiet)

    def boom(*a, **kw):
        raise MemoryError()

    monkeypatch.setattr(SW, 'replayed', boom)
    out = RV.check(pair, None, ['u', 'v'], log=quiet)
    step = f'the replay of the calls of {STEP}'
    assert out['failed'] == [{'step': step, 'why': 'MemoryError', 'rests': 'none', 'reading': None}]
    assert out['dropped'] == [{'step': STEP, 'req': 'R-RET-1', 'lines': [x], 'why': 'the replay did not end'}
                              for x in (U_NOT_V, V_NOT_U)]
    assert out['readings']['R-RET-1'] == {'plain': 'INCOMPARABLE', 'context': 'UNKNOWN', 'witness': None}
    assert asked(out, 'undecided') == [(['R-RET-1'], 'UNKNOWN', [])] and asked(out, 'readings') == []
    assert out['certified'] == full['certified']       # no verdict rests on the replay: the question does
    text = RV.report(Session(pair, sets=['u', 'v']), out)
    assert '## This review is partial' in text and f'- {step}: MemoryError' in text
    assert '## Calls not shown' in text and U_NOT_V not in text and V_NOT_U not in text


def test_the_calls_under_a_shared_answer_are_replayed_per_reader(pair, monkeypatch):
    """Both readers state u and a third reader, of the other reading of what
    they shared, states v.  Where the call found for the first reader does
    not pass, the one found for the second is shown."""
    shutil.copy(os.path.join(pair, 'formal', 'u.yaml'), os.path.join(pair, 'formal', 'u2.yaml'))
    with open(os.path.join(pair, 'formal', 'u2.yaml')) as f:
        text = f.read().replace('set: u', 'set: u2').replace('id: u}', 'id: u2}')
    with open(os.path.join(pair, 'formal', 'u2.yaml'), 'w') as f:
        f.write(text)
    with open(os.path.join(pair, 'formal', 'v.yaml')) as f:
        text = f.read().replace('set: v', 'set: variant').replace('id: v}', 'id: variant}')
    with open(os.path.join(pair, 'formal', 'variant.yaml'), 'w') as f:
        f.write(text)
    with open(os.path.join(pair, 'formal', 'variant_answers.json'), 'w') as f:
        f.write('[]')
    out = RV.check(pair, None, ['u', 'u2'], log=quiet)
    steps = [s['step'] for s in out['steps']]
    assert steps[-6:] == [f'the {what}comparison of {s} and variant{how}' for s in ('u', 'u2') for what, how in
                          (('', ''), ('', ', in context'), ('replay of the calls of the ', ', in context'))]
    assert not [s for s in steps if s.startswith('the replay') and 'variant' not in s]     # u and u2 agree: no call
    # per reader: no direction without a call, in context or without it
    differs = {'relation': 'INCOMPARABLE', 'closed': [], 'closed_alone': []}
    assert out['depends'] == {'R-RET-1': {'relation': 'INCOMPARABLE', 'peers': ['u', 'u2'], 'witness': [U_NOT_V],
                                          'by': {'u': differs, 'u2': differs}}}
    assert asked(out, 'depends') == [(['R-RET-1'], None, [U_NOT_V])] and 'dropped' not in out
    real = SW.compare

    def compare(S, a, b, fn, context=False, **kw):
        recs = real(S, a, b, fn, context=context, **kw)
        if (a, b) == ('u', 'variant'):
            recs['R-RET-1']['witness_a_not_b']['lines'] = [NEITHER]
            recs['R-RET-1']['witness_b_not_a']['lines'] = [NEITHER]
        return recs
    monkeypatch.setattr(SW, 'compare', compare)
    out = RV.check(pair, None, ['u', 'u2'], log=quiet)
    # the first reader's comparison is undecided without its calls: the entry carries what the second one found
    undecided = {'relation': 'UNKNOWN', 'closed': [], 'closed_alone': []}
    assert out['depends'] == {'R-RET-1': {'relation': 'INCOMPARABLE', 'peers': ['u', 'u2'], 'witness': [U_NOT_V],
                                          'by': {'u': undecided, 'u2': differs}}}
    assert [(d['step'], d['lines']) for d in out['dropped']] == \
        [('the comparison of u and variant, in context', [NEITHER])] * 2
    assert asked(out, 'depends') == [(['R-RET-1'], None, [U_NOT_V])]

    def compare(S, a, b, fn, context=False, **kw):     # no call of either reader passes: nothing was shown
        recs = real(S, a, b, fn, context=context, **kw)
        if b == 'variant':
            recs['R-RET-1']['witness_a_not_b']['lines'] = [NEITHER]
            recs['R-RET-1']['witness_b_not_a']['lines'] = [NEITHER]
        return recs
    monkeypatch.setattr(SW, 'compare', compare)
    out = RV.check(pair, None, ['u', 'u2'], log=quiet)
    assert out['depends'] == {'R-RET-1': {'relation': 'UNKNOWN', 'peers': ['u', 'u2'], 'witness': None,
                                          'by': {'u': undecided, 'u2': undecided}}}
    assert asked(out, 'depends') == [] and asked(out, 'undecided') == [(['R-RET-1'], None, [])]
    said = next(q['question'] for q in out['queue'] if q['kind'] == 'undecided')
    assert 'was not shown either way' in said and 'mean something else:' not in said
    assert 'R-RET-1' not in out['certified']

    def compare(S, a, b, fn, context=False, **kw):     # the first reader shows a run that the variant alone accepts
        recs = real(S, a, b, fn, context=context, **kw)
        if (a, b) == ('u', 'variant'):
            x = recs['R-RET-1']
            x.pop('witness_a_not_b', None)
            x['relation'], x['status'] = 'A-STRONGER', {**x['status'], 'witness_a_not_b': 'none'}
        return recs
    monkeypatch.setattr(SW, 'compare', compare)
    out = RV.check(pair, None, ['u', 'u2'], log=quiet)
    # the call kept is one that a reader accepts and the variant rejects (what makes a requirement wait once
    # there is code), also where it is the second reader's
    first = out['depends']['R-RET-1']['by']['u']
    assert (first['relation'], first['closed'], first['closed_alone']) == ('A-STRONGER', ['witness_a_not_b'],
                                                                           ['witness_a_not_b'])
    assert out['depends']['R-RET-1']['by']['u2'] == differs and 'dropped' not in out
    assert out['depends']['R-RET-1']['witness'] == [U_NOT_V] and asked(out, 'depends') == [(['R-RET-1'], None, [U_NOT_V])]


def test_with_code_the_shared_answers_hold_what_the_other_reading_may_reject(pair, monkeypatch):
    """Both readers state that the price is the subtotal, and the third
    reader, of the other reading of what they shared, that it is at most the
    subtotal: it accepts every run the readers accept, and more.  Before any
    code the requirement waits for the answers (its meaning is open).  With
    code that the readers' rule accepts it is certified: no run of that code
    is rejected under the other answer.  That stands when the call the other
    reading alone accepts is not shown, since the direction that holds a
    requirement back is the other one.  It does not stand on the comparison
    in context alone: a third reader that also states the readers' other rule
    under this requirement accepts their runs only among the runs that meet
    that rule, and the requirement waits.  So it does when the comparison
    without context did not end, when the comparison in context of one
    reader or the run of the code did not end, and when the third reader's
    rule rejects a run of the readers."""
    import json
    form = os.path.join(pair, 'formal')
    with open(os.path.join(form, 'u.yaml')) as f:
        u = f.read()
    with open(os.path.join(form, 'v.yaml')) as f:
        v = f.read()
    with open(os.path.join(form, 'u2.yaml'), 'w') as f:
        f.write(u.replace('set: u', 'set: u2').replace('id: u}', 'id: u2}'))
    assert 'price == subtotal &&' in u

    def third(text, s):
        with open(os.path.join(form, 'variant.yaml'), 'w') as f:
            f.write(text.replace(f'set: {s}', 'set: variant').replace(f'id: {s}}}', 'id: variant}'))

    def sees(out):
        return RV.report(Session(pair, sets=['u', 'u2']), out)

    wider = u.replace('price == subtotal &&', 'price <= subtotal &&')
    third(wider, 'u')
    with open(os.path.join(form, 'variant_answers.json'), 'w') as f:
        json.dump([{'req': 'R-STACK-1', 'phrase': 'Discounts stack', 'taken': 1}], f)
    passed = {'T-P': {'req': 'R-RET-1', 'status': 'PASS'}, 'T-Q': {'req': 'R-ERR-1', 'status': 'PASS'}}
    monkeypatch.setattr(SW, 'calls_for', lambda S, fn, codes: [])              # the code: every rule passes on the scope
    monkeypatch.setattr(SW, 'run', lambda fn, code, calls: [])
    monkeypatch.setattr(SW, 'trace', lambda fn, calls, res: {})
    monkeypatch.setattr(SW, 'outcome_summary', lambda fn, res: {'counts': {}})
    monkeypatch.setattr(SW, 'verify', lambda S, s, fn, code, calls, res, cols: json.loads(json.dumps(passed)))
    monkeypatch.setattr('fcp.prove.prove', lambda S, s, fn, code, calls, res: {'status': 'ok', 'requirements': {}})
    code = os.path.join(B, 'impl', 'ref.py')
    a_b = 'witness_a_not_b'
    more = {'relation': 'A-STRONGER', 'closed': [a_b], 'closed_alone': [a_b], 'carried': [a_b]}
    wait = ('the other reading accepts every run that both readers accept, whatever the run does on the other '
            'requirements')

    before = RV.check(pair, None, ['u', 'u2'], log=quiet)
    d = before['depends']['R-RET-1']
    assert list(before['depends']) == ['R-RET-1'] and d['by'] == {'u': more, 'u2': more}
    assert d['relation'] == 'A-STRONGER'
    call, = d['witness']                                # a run the other reading accepts and the readers reject
    assert SW.read_line(SW.function(Session(pair, sets=['u'])), call)[1]['price'] < 6
    assert asked(before, 'depends') == [(['R-RET-1'], None, [call])] and 'R-RET-1' not in before['certified']
    assert wait not in sees(before)

    out = RV.check(pair, code, ['u', 'u2'], log=quiet)
    assert out['depends'] == before['depends'] and out['failed'] == []
    assert asked(out, 'depends') == asked(out, 'undecided') == [] and out['certified'] == ['R-RET-1', 'R-ERR-1']
    text = sees(out)
    assert '## Shared answers' in text and f'On R-RET-1 {wait}: what is certified of this requirement stands under ' \
        'either answer, and it does not wait for these answers.' in text
    real = SW.compare

    def compare(S, a, b, fn, context=False, **kw):     # the call of the other reading does not pass its replay
        recs = real(S, a, b, fn, context=context, **kw)
        if b == 'variant':
            recs['R-RET-1']['witness_b_not_a']['lines'] = [NEITHER]
        return recs
    monkeypatch.setattr(SW, 'compare', compare)
    out = RV.check(pair, code, ['u', 'u2'], log=quiet)
    half = {**more, 'relation': 'UNKNOWN'}
    assert out['depends'] == {'R-RET-1': {'relation': 'UNKNOWN', 'peers': ['u', 'u2'], 'witness': None,
                                          'by': {'u': half, 'u2': half}}}
    assert len(out['dropped']) == 2 and asked(out, 'depends') == asked(out, 'undecided') == []
    assert 'R-RET-1' in out['certified']
    again = RV.check(pair, None, ['u', 'u2'], log=quiet)                   # before code it is asked, as undecided
    assert asked(again, 'undecided') == [(['R-RET-1'], None, [])] and 'R-RET-1' not in again['certified']

    def compare(S, a, b, fn, context=False, **kw):     # the comparisons without context do not end
        if b == 'variant' and not context:
            raise RuntimeError('stopped')
        return real(S, a, b, fn, context=context, **kw)
    monkeypatch.setattr(SW, 'compare', compare)
    out = RV.check(pair, code, ['u', 'u2'], log=quiet)
    assert [(f['step'], f['rests']) for f in out['failed']] == [(f'the comparison of {s} and variant', 'none')
                                                                for s in ('u', 'u2')]
    shut = {'relation': 'A-STRONGER', 'closed': [a_b], 'closed_alone': []}     # in context only, and nothing handed on
    assert out['depends']['R-RET-1']['by'] == {'u': shut, 'u2': shut}
    assert asked(out, 'depends') == [(['R-RET-1'], None, [call])] and out['certified'] == ['R-ERR-1']
    assert wait not in sees(out)

    def compare(S, a, b, fn, context=False, **kw):     # the comparison in context of one reader does not end
        if (a, b, context) == ('u2', 'variant', True):
            raise RuntimeError('stopped')
        return real(S, a, b, fn, context=context, **kw)
    monkeypatch.setattr(SW, 'compare', compare)
    out = RV.check(pair, code, ['u', 'u2'], log=quiet)
    assert [f['step'] for f in out['failed']] == ['the comparison of u2 and variant, in context']
    assert out['depends']['R-RET-1']['by'] == {'u': more} and RV.waiting(out) == (['R-RET-1'], [])
    assert asked(out, 'depends') == [(['R-RET-1'], None, [call])] and out['certified'] == []
    assert wait not in sees(out)
    monkeypatch.setattr(SW, 'compare', real)

    def boom(*a, **kw):
        raise RuntimeError('stopped')
    with monkeypatch.context() as m:                   # the run of the code does not end: nothing is shown about it
        m.setattr(SW, 'verify', boom)
        out = RV.check(pair, code, ['u', 'u2'], log=quiet)
    assert 'the code on the scope' in [f['step'] for f in out['failed']] and out['depends'] == before['depends']
    assert RV.waiting(out) == (['R-RET-1'], []) and asked(out, 'depends') == [(['R-RET-1'], None, [call])]
    assert out['certified'] == [] and wait not in sees(out)

    # the readers' other rule, stated under this requirement too: among the runs that meet that rule (the
    # context) the other reading accepts every run of the readers, and without it a run that does not raise
    # below 6 is one the readers accept on this requirement and the other reading rejects
    raises = "{id: T-R, req: R-RET-1, pattern: implies, args: {trigger: 'subtotal < 6', cond: 'outcome == 1'}}"
    third(f'{wider}  - {raises}\n', 'u')
    out = RV.check(pair, code, ['u', 'u2'], log=quiet)
    only = {'relation': 'A-STRONGER', 'closed': [a_b], 'closed_alone': []}
    assert out['failed'] == [] and out['depends']['R-RET-1']['by'] == {'u': only, 'u2': only}
    assert asked(out, 'depends') == [(['R-RET-1'], None, out['depends']['R-RET-1']['witness'])]
    assert out['certified'] == ['R-ERR-1'] and wait not in sees(out)

    third(v, 'v')                                      # one less than the subtotal: it rejects what the readers accept
    out = RV.check(pair, code, ['u', 'u2'], log=quiet)
    assert out['depends']['R-RET-1']['by'] == {s: {'relation': 'INCOMPARABLE', 'closed': [], 'closed_alone': []}
                                               for s in ('u', 'u2')}
    assert asked(out, 'depends') == [(['R-RET-1'], None, [U_NOT_V])] and 'R-RET-1' not in out['certified']
    assert wait not in sees(out)


# from a subtotal of 6 on, the call that follows returns a price of at least LEAST
FOLLOWS = '''
    fcp: "0.1"
    set: NAME
    origin: {kind: human, role: formalizer, id: NAME}
    properties:
      - {id: T-P, req: R-RET-1, pattern: next, args: {trigger: 'subtotal >= 6', cond: 'outcome == 0 && price >= LEAST'}}
      - {id: T-Q, req: R-ERR-1, pattern: implies, args: {trigger: 'subtotal >= 6', cond: 'price != 0'}}
'''


def test_a_rule_over_two_calls_is_compared_on_runs_of_two_calls(pair):
    """A rule of pattern next speaks of the call after its trigger, so it
    cannot fail on a run of one call.  Found by a review of the rule for the
    shared answers: the horizon of a comparison counted how far an item
    looks back and not the call of the trigger, two readings whose rules
    over two calls differ compared as EQUIVALENT on runs of one call, and
    with a third reader the requirement would not have been asked about.
    The horizon is the one `window_len` counts, and the record says that the
    search was within runs of two calls."""
    for name, least in (('n1', '1'), ('n9', '9')):
        with open(os.path.join(pair, 'formal', f'{name}.yaml'), 'w') as f:
            f.write(textwrap.dedent(FOLLOWS).replace('NAME', name).replace('LEAST', least))
    S = Session(pair, sets=['n1', 'n9'])
    fn = SW.function(S)
    assert SW.horizon(S, ['n1', 'n9']) == (2, False) and SW.window_len(S, 'n1', fn) == 2
    for context in (False, True):
        x = SW.compare(S, 'n1', 'n9', fn, context=context, bit_timeout=0)['R-RET-1']
        assert x['relation'] == 'A-WEAKER' and x['status'] == {'witness_a_not_b': 'witness', 'witness_b_not_a': 'none'}
        assert (x['k'], x['exact']) == (2, False) and 'refuted' not in x
        assert len(x['witness_a_not_b']['lines']) == 2             # the trigger, and the call the rule speaks of
        assert RV._bound(x) == 'runs of 2 calls' and SW.closed(x) == ('witness_b_not_a',)
