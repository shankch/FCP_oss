"""A review that is written whatever a step of its check does.  Found on
HumanEval/49, /59 and /144: a translation by yosys that did not end in 300 s
(three requests) and searches that passed 8 GB (five).  Each ended the whole
check, so eight of eighty requests got no review at all.  Now
the check is a sequence of named steps (fcp.review.Steps): one that raises is
recorded with the reason and the check goes on; `supervised` runs the check in
a process of its own and stops the step that passes its memory or its time;
the verdicts certify nothing that rests on a step that failed, and the report
names it."""
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
import types

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_checkout')
sys.path.insert(0, ROOT)

from fcp import review as RV  # noqa: E402
from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402


def fake(jobs=4):
    """What Steps needs of a session: the number of engine tasks at a time."""
    return types.SimpleNamespace(runner=types.SimpleNamespace(jobs=jobs))


def boom():
    raise ValueError('boom')


# ---------------------------------------------------------------- the steps of a check
def test_a_step_that_raises_is_recorded_and_the_next_one_runs(monkeypatch, capsys):
    monkeypatch.setattr(SW, 'BUDGET_HIT', [])
    lines = []
    st = RV.Steps(None, lines.append, fake())

    def short():
        SW.BUDGET_HIT.append('the search of x')
        return {'n': 1}

    assert st.run('one', short, {}) == {'n': 1}
    assert st.run('two', boom, {'n': 0}) == {'n': 0}                 # the empty result of the step
    assert st.run('three', lambda: (1, 2), None, rests='none') == (1, 2)
    assert st.failed('two') and not st.failed('one') and not st.failed('four')
    assert st.run('four', lambda: 1, None, needs='two') is None     # not run: it needs a step that failed
    assert st.run('five', lambda: 1, None, needs='one') == 1
    done, failed = st.summary()
    assert [(x['step'], x.get('failed')) for x in done] == [
        ('one', None), ('two', 'ValueError: boom'), ('three', None), ('four', 'not run: two did not end'),
        ('five', None)]
    assert failed == [{'step': 'two', 'why': 'ValueError: boom', 'rests': 'all', 'reading': None},
                      {'step': 'four', 'why': 'not run: two did not end', 'rests': 'all', 'reading': None}]
    assert st.d['steps']['one']['cut'] == ['the search of x'] and st.d['steps']['two']['cut'] == []
    assert lines == ['  one', '  two', '  two: failed (ValueError: boom)', '  three', '  five']
    assert 'ValueError: boom' in capsys.readouterr().err             # the trace goes to the error stream


def test_a_check_started_again_runs_only_the_steps_its_file_does_not_hold(tmp_path, monkeypatch):
    monkeypatch.setattr(SW, 'BUDGET_HIT', [])
    path, ran = str(tmp_path / 'state.json'), []

    def step(name, result):
        def f():
            ran.append(name)
            return result
        return f

    st = RV.Steps(path, lambda *a: None, fake())
    assert st.run('one', step('one', {'calls': (1, 2)}), {}) == {'calls': [1, 2]}       # as a later process reads it
    assert st.run('two', boom, {}, rests='scenarios', reading='t') == {}
    with open(path) as f:
        d = json.load(f)
    assert 'running' not in d and d['steps']['two']['failed'] == 'ValueError: boom'
    again = RV.Steps(path, lambda *a: None, fake())
    assert again.run('one', step('one', {'calls': (3, 4)}), {}) == {'calls': [1, 2]}
    assert again.run('two', step('two', {}), {'empty': 1}, rests='scenarios', reading='t') == {'empty': 1}
    assert again.run('three', step('three', 3), None) == 3
    assert ran == ['one', 'three']
    assert again.summary()[1] == [{'step': 'two', 'why': 'ValueError: boom', 'rests': 'scenarios', 'reading': 't'}]


def test_a_stopped_check_runs_no_further_step_and_a_step_run_again_runs_alone(tmp_path, monkeypatch):
    monkeypatch.setattr(SW, 'BIT_JOBS', 6)
    path, S, seen = str(tmp_path / 'state.json'), fake(4), []
    RV._write_json(path, {'steps': {'one': {'again': 'passed the memory limit of 1.0 GB'},
                                    'two': {'failed': 'did not end in 9 s', 'seconds': 9.0}}})
    lines = []
    st = RV.Steps(path, lines.append, S)
    assert st.run('one', lambda: seen.append((S.runner.jobs, SW.BIT_JOBS)) or 'ok', None) == 'ok'
    assert seen == [(1, 1)] and (S.runner.jobs, SW.BIT_JOBS) == (4, 6) and lines == ['  one, one task at a time']
    assert st.run('two', lambda: 'ok', 'empty', rests='none') == 'empty'      # stopped by the process that watches
    assert st.d['steps']['two']['rests'] == 'none'
    st.d['stop'] = 'the check reached its time limit of 5 s'
    assert st.run('three', lambda: 'ok', 'empty') == 'empty'
    assert st.summary()[1][-1]['why'] == 'not run: the check reached its time limit of 5 s'


def test_a_failed_step_names_the_requirements_that_rest_on_it(tmp_path, monkeypatch):
    """A step on which the verdicts rest can be given the only requirements
    that rest on it (reqs): its record names them when it fails, and only
    then.  A step fails in four ways: it raises; the process that watches
    stops it and records it, without what rests on it; it is stopped for its
    memory, recorded with 'again', run once more and fails then; or the
    check was stopped before it.  In each the requirements are written when
    `run` first sees the failure, together with what rests on the step.  A
    check started again on the file writes nothing more, and a failed step
    that is given none is recorded as it was."""
    step, path, saves = 'the comparison of one and two, in context', str(tmp_path / 'state.json'), []
    write = RV._write_json
    monkeypatch.setattr(RV, '_write_json', lambda p, d: (saves.append(p), write(p, d))[1])
    st = RV.Steps(None, quiet, fake())
    assert st.run('one', lambda: 1, None, reqs=['R-X']) == 1           # a step that ended names none
    assert st.run('two', boom, {}) == {}                               # a failed step that is given none
    assert st.run('three', boom, {'R-RET-1': 1}, reqs=['R-EX-1']) == {'R-RET-1': 1}
    assert st.run('four', boom, {}, reqs=[]) == {}                     # no requirement rests on it
    assert 'reqs' not in st.d['steps']['one']
    assert st.summary()[1] == [
        {'step': 'two', 'why': 'ValueError: boom', 'rests': 'all', 'reading': None},
        {'step': 'three', 'why': 'ValueError: boom', 'rests': 'all', 'reading': None, 'reqs': ['R-EX-1']},
        {'step': 'four', 'why': 'ValueError: boom', 'rests': 'all', 'reading': None, 'reqs': []}]
    # stopped by the process that watches, which records neither what rests on the step nor the requirements
    RV._write_json(path, {'steps': {step: {'failed': 'did not end in 3 s', 'seconds': 3.0}}})
    st = RV.Steps(path, quiet, fake())
    assert st.run(step, boom, {}, reqs=['R-EX-1']) == {}               # not run again
    with open(path) as f:
        assert json.load(f)['steps'][step] == {'failed': 'did not end in 3 s', 'seconds': 3.0, 'rests': 'all',
                                               'reading': None, 'reqs': ['R-EX-1']}
    n = len(saves)
    again = RV.Steps(path, quiet, fake())      # the next process, on the file: nothing is written
    assert again.run(step, boom, {}, reqs=['R-EX-1']) == {} and len(saves) == n
    assert again.summary()[1] == [{'step': step, 'why': 'did not end in 3 s', 'rests': 'all', 'reading': None,
                                   'reqs': ['R-EX-1']}]
    # stopped for its memory: run once more, alone, and the failure of that run names the requirements
    RV._write_json(path, {'steps': {step: {'again': 'passed the memory limit of 1.0 GB'}}})
    st = RV.Steps(path, quiet, fake())
    assert st.run(step, boom, {}, reqs=[]) == {}
    assert st.summary()[1] == [{'step': step, 'why': 'ValueError: boom', 'rests': 'all', 'reading': None, 'reqs': []}]
    # ... and a step that ends when it runs alone did not fail
    RV._write_json(path, {'steps': {step: {'again': 'passed the memory limit of 1.0 GB'}}})
    st = RV.Steps(path, quiet, fake())
    assert st.run(step, lambda: {'r': 1}, {}, reqs=['R-EX-1']) == {'r': 1}
    assert 'reqs' not in st.d['steps'][step] and st.summary()[1] == []
    # a stopped check: the step is not run, which is a failure like the others
    RV._write_json(path, {'steps': {}, 'stop': 'the check reached its time limit of 5 s'})
    st = RV.Steps(path, quiet, fake())
    assert st.run(step, lambda: 1, {}, reqs=['R-EX-1']) == {}
    assert st.summary()[1] == [{'step': step, 'why': 'not run: the check reached its time limit of 5 s',
                                'rests': 'all', 'reading': None, 'reqs': ['R-EX-1']}]
    # a record that already says what rests on it (a file of an engine before this change) is left as it is
    RV._write_json(path, {'steps': {step: {'failed': 'ValueError: boom', 'rests': 'all', 'reading': None}}})
    st = RV.Steps(path, quiet, fake())
    assert st.run(step, boom, {}, reqs=['R-EX-1']) == {}
    assert st.summary()[1] == [{'step': step, 'why': 'ValueError: boom', 'rests': 'all', 'reading': None}]


# ---------------------------------------------------------------- a check that is watched
WORKER = '''
import json, os, subprocess, sys, time, types
sys.path.insert(0, sys.argv[1])
from fcp import review as RV
HOLD = 'import sys, time; x = b"1" * int(sys.argv[1]); print("held", flush=True); time.sleep(60)'


def play(bundle, code, sets, log, scope_budget, conflict_budget, compare_budget, jobs, state):
    """A check whose steps are written in its bundle argument."""
    script = json.loads(bundle)
    S = types.SimpleNamespace(runner=types.SimpleNamespace(jobs=jobs))
    st = RV.Steps(state, log, S)
    if script.get('before') == 'die':
        os._exit(7)
    if script.get('before') == 'raise':
        raise KeyError('no such reading')
    if script.get('before') == 'sleep':
        time.sleep(120)

    def act(what, arg):
        if what == 'sleep':
            time.sleep(arg)
        elif what in ('eat', 'hog'):       # eat: arg MB for every task at a time; hog: arg MB whatever runs
            n = int(arg * (S.runner.jobs if what == 'eat' else 1)) << 20
            p = subprocess.Popen([sys.executable, '-c', HOLD, str(n)], stdout=subprocess.PIPE,
                                 preexec_fn=os.setpgrp)        # in a process group of its own, as sby starts its tools
            with open(script['pids'], 'a') as f:
                f.write(f'{p.pid}\\n')
            p.stdout.readline()
            time.sleep(1.5)
            p.kill()
            p.wait()
        elif what == 'keep':                # a tool that runs as long as the step, arg seconds
            p = subprocess.Popen([sys.executable, '-c', HOLD, '1'], stdout=subprocess.PIPE, preexec_fn=os.setpgrp)
            p.stdout.readline()
            with open(script['pids'], 'a') as f:
                f.write(f'{os.getpid()}\\n{p.pid}\\n')
            time.sleep(arg)
        elif what == 'raise':
            raise ValueError('boom')
        elif what == 'die':
            os._exit(7)
        return {'did': what, 'jobs': S.runner.jobs}

    out = {'ran': {}}
    for name, what, arg in script['steps']:
        out['ran'][name] = st.run(name, lambda: act(what, arg), None)
    out['steps'], out['failed'] = st.summary()
    return out


RV.check = play
sys.exit(RV.worker(sys.argv[2]))
'''


def watched(tmp_path, steps, before=None, **kw):
    """A check of these steps (name, what it does, how much) under `supervised`."""
    (tmp_path / 'worker.py').write_text(WORKER)
    script = {'steps': steps, 'pids': str(tmp_path / 'pids'), 'before': before}
    lines = []
    res = RV.supervised(json.dumps(script), None, ['x'], log=lines.append, state=str(tmp_path / 'state.json'),
                        worker=[sys.executable, str(tmp_path / 'worker.py'), ROOT], **kw)
    return res, lines


def alive(pid: int) -> bool:
    try:
        with open(f'/proc/{pid}/stat') as f:
            return f.read().rsplit(')', 1)[1].split()[0] != 'Z'
    except OSError:
        return False


def why(res, step):
    return next(x['why'] for x in res['failed'] if x['step'] == step)


def test_a_watched_check_runs_in_a_process_of_its_own(tmp_path):
    res, lines = watched(tmp_path, [['one', 'ok', 0], ['two', 'raise', 0], ['three', 'ok', 0]], jobs=3)
    assert res['ran'] == {'one': {'did': 'ok', 'jobs': 3}, 'two': None, 'three': {'did': 'ok', 'jobs': 3}}
    assert res['failed'] == [{'step': 'two', 'why': 'ValueError: boom', 'rests': 'all', 'reading': None}]
    assert lines == ['  one', '  two', '  two: failed (ValueError: boom)', '  three']
    assert 'ValueError: boom' in (tmp_path / 'state.json.err').read_text()      # the trace of the step that failed
    with open(tmp_path / 'state.json') as f:
        d = json.load(f)
    assert 'running' not in d and list(d['steps']) == ['one', 'two', 'three'] and d['args']['jobs'] == 3


def test_a_step_that_runs_too_long_is_stopped_and_the_check_goes_on(tmp_path):
    t = time.time()
    res, lines = watched(tmp_path, [['one', 'ok', 0], ['two', 'sleep', 120], ['three', 'ok', 0]], step_seconds=2)
    assert time.time() - t < 30
    assert res['failed'] == [{'step': 'two', 'why': 'did not end in 2 s', 'rests': 'all', 'reading': None}]
    assert res['ran']['two'] is None and res['ran']['three'] == {'did': 'ok', 'jobs': RV.JOBS}
    assert '  two: failed (did not end in 2 s)' in lines and lines[-1] == '  three'


def test_a_step_that_holds_too_much_is_run_again_alone(tmp_path):
    """The memory is that of every process of the check, also of a tool in a
    process group of its own; a step stopped for it runs once more with one
    engine task at a time, and what it started is killed with it."""
    res, lines = watched(tmp_path, [['one', 'ok', 0], ['big', 'eat', 100], ['three', 'ok', 0]], memory=0.3, jobs=4)
    assert res['failed'] == [] and res['ran']['big'] == {'did': 'eat', 'jobs': 1}
    assert res['ran']['three'] == {'did': 'ok', 'jobs': 4}
    assert '  big: passed the memory limit of 0.3 GB; once more, one task at a time' in lines
    assert '  big, one task at a time' in lines
    pids = [int(x) for x in (tmp_path / 'pids').read_text().split()]
    assert len(pids) == 2 and not any(alive(p) for p in pids)
    peak = next(s['peak_gb'] for s in res['steps'] if s['step'] == 'big')
    assert 0.3 < peak < 0.6


def test_a_step_that_holds_too_much_alone_fails(tmp_path):
    res, lines = watched(tmp_path, [['big', 'hog', 400], ['two', 'ok', 0]], memory=0.3)
    assert why(res, 'big') == 'passed the memory limit of 0.3 GB, also with one task at a time'
    assert res['ran'] == {'big': None, 'two': {'did': 'ok', 'jobs': RV.JOBS}}
    pids = [int(x) for x in (tmp_path / 'pids').read_text().split()]
    assert len(pids) == 2 and not any(alive(p) for p in pids)
    res, _ = watched(tmp_path, [['big', 'hog', 400]], memory=0)                # no limit
    assert res['failed'] == []


def test_a_check_that_reaches_its_time_limit_ends_with_what_it_has(tmp_path):
    steps = [['one', 'ok', 0], ['two', 'sleep', 120], ['three', 'ok', 0], ['four', 'ok', 0]]
    res, lines = watched(tmp_path, steps, check_seconds=2)
    limit = 'the check reached its time limit of 2 s'
    assert [(x['step'], x['why']) for x in res['failed']] == [
        ('two', 'was stopped: ' + limit), ('three', 'not run: ' + limit), ('four', 'not run: ' + limit)]
    assert res['ran'] == {'one': {'did': 'ok', 'jobs': RV.JOBS}, 'two': None, 'three': None, 'four': None}


def test_a_checking_process_that_ends_in_a_step_fails_that_step_only(tmp_path):
    res, lines = watched(tmp_path, [['one', 'ok', 0], ['two', 'die', 0], ['three', 'ok', 0]])
    assert [(x['step'], x['why']) for x in res['failed']] == [
        ('two', 'the checking process ended with exit code 7')]
    assert res['ran']['three'] == {'did': 'ok', 'jobs': RV.JOBS}


def test_a_check_that_ends_outside_its_steps_gives_no_verdicts(tmp_path):
    res, _ = watched(tmp_path, [['one', 'ok', 0]], before='die')
    assert res['unchecked'] == 'outside its steps, the checking process ended with exit code 7'
    assert res['certified'] == [] and res['queue'] == [] and res['code'] is None
    res, _ = watched(tmp_path, [['one', 'ok', 0]], before='raise')
    assert res['unchecked'] == "KeyError: 'no such reading'"
    assert 'KeyError' in (tmp_path / 'state.json.err').read_text()
    t = time.time()
    res, _ = watched(tmp_path, [['one', 'ok', 0]], before='sleep', step_seconds=1)   # stopped before its first step
    assert res['unchecked'] == 'outside its steps, the checking process did not end in 1 s' and time.time() - t < 30


def test_an_interrupted_check_leaves_no_process(tmp_path, monkeypatch):
    seen = []

    def interrupt(proc, *a):
        seen.append(proc.pid)
        time.sleep(0.5)
        raise KeyboardInterrupt

    monkeypatch.setattr(RV, '_watch', interrupt)
    with pytest.raises(KeyboardInterrupt):
        watched(tmp_path, [['big', 'hog', 50], ['two', 'sleep', 120]])
    pids = seen + [int(x) for x in (tmp_path / 'pids').read_text().split()]
    assert len(pids) == 2 and not any(alive(p) for p in pids)


DRIVER = '''
import sys
sys.path.insert(0, sys.argv[1])
from fcp import review as RV
RV.supervised(sys.argv[2], None, ['x'], log=lambda *a: None, state=sys.argv[3],
              worker=[sys.executable, sys.argv[4], sys.argv[1]])
'''


def test_a_check_whose_watcher_is_killed_ends_itself(tmp_path):
    """Found when `timeout` ended a review: the checking process, in a session
    of its own, ran on beside the next one.  A process that is killed stops
    nothing itself, so the checking process looks for the one that watches
    it, and ends with all it started when that one is gone."""
    (tmp_path / 'worker.py').write_text(WORKER)
    (tmp_path / 'driver.py').write_text(DRIVER)
    script = {'steps': [['one', 'ok', 0], ['two', 'keep', 120]], 'pids': str(tmp_path / 'pids'), 'before': None}
    driver = subprocess.Popen([sys.executable, str(tmp_path / 'driver.py'), ROOT, json.dumps(script),
                               str(tmp_path / 'state.json'), str(tmp_path / 'worker.py')])
    pids = []
    try:
        t = time.time()
        while len(pids) < 2 and time.time() - t < 60:
            time.sleep(0.1)
            if (tmp_path / 'pids').exists():
                pids = [int(x) for x in (tmp_path / 'pids').read_text().split()]
        assert len(pids) == 2 and all(alive(p) for p in pids) and driver.poll() is None
        assert os.getsid(pids[0]) == pids[0] != os.getsid(driver.pid)        # the check leads a session of its own
        assert os.getpgid(pids[1]) == pids[1]                                # and its tool a group of its own
        driver.kill()                                                        # no handler runs, nothing is cleaned up
        driver.wait()
        t = time.time()
        while any(alive(p) for p in pids) and time.time() - t < 20:
            time.sleep(0.1)
        assert not any(alive(p) for p in pids)
    finally:
        driver.kill()
        driver.wait()
        for p in pids:
            try:
                os.kill(p, 9)
            except OSError:
                pass


def test_the_memory_a_check_may_hold(monkeypatch):
    monkeypatch.delenv('FCP_MEMORY_GB', raising=False)
    assert RV.memory_budget(2) == 2 * 2 ** 30 and RV.memory_budget(0.5) == 2 ** 29
    assert RV.memory_budget(0) is None                                        # no limit
    with open('/proc/meminfo') as f:
        ram = next(int(x.split()[1]) for x in f if x.startswith('MemTotal:')) * 1024
    assert 0 < RV.memory_budget() <= min(8 * 2 ** 30, ram // 2)
    monkeypatch.setenv('FCP_MEMORY_GB', '3')
    assert RV.memory_budget() == 3 * 2 ** 30 and RV.memory_budget(1) == 2 ** 30
    monkeypatch.setenv('FCP_MEMORY_GB', '0')
    assert RV.memory_budget() is None


def test_the_processes_of_a_session_are_found_and_stopped():
    hold = 'import sys, time; x = b"1" * (64 << 20); print("held", flush=True); time.sleep(60)'
    lead = ('import os, subprocess, sys, time; '
            'p = subprocess.Popen([sys.executable, "-c", sys.argv[1]], preexec_fn=os.setpgrp); '
            'print(p.pid, flush=True); time.sleep(60)')
    p = subprocess.Popen([sys.executable, '-c', lead, hold], stdout=subprocess.PIPE, text=True,
                         start_new_session=True)
    try:
        child = int(p.stdout.readline())
        assert p.stdout.readline().strip() == 'held'
        found = dict(RV._session(p.pid))
        assert set(found) == {p.pid, child} and found[child] > 64 << 20
        assert os.getpid() not in found
        RV._stop_session(p.pid)
        assert RV._session(p.pid) == [] and not alive(child)
    finally:
        p.kill()
        p.wait()


# ---------------------------------------------------------------- a check with a step that fails
READING = '''
    fcp: "0.1"
    set: {s}
    origin: {{kind: human, role: formalizer, id: {s}}}
    properties:
      - {{id: T-P, req: R-RET-1, pattern: implies, args: {{trigger: 'subtotal >= 6', cond: 'outcome == 0 && price == subtotal && ship == 0'}}}}
      - {{id: T-Q, req: R-RET-1, pattern: implies, args: {{trigger: 'subtotal < 6', cond: 'outcome == 1'}}}}
    scenarios:
      - {{id: S-OK, req: R-EX-1, cover: 'subtotal == 7 && outcome == 0 && price == 7'}}
'''
NONE = {'conflicts': [], 'candidates': 0, 'checked': 0}
SAME = {'R-RET-1': {'relation': 'EQUIVALENT'},
        'R-EX-1': {'relation': 'INCOMPARABLE', 'witness_a_not_b': {'lines': ['checkout(7, 0, 0) -> 7, 0']}}}


def copy(tmp_path, *sets):
    """The checkout bundle with the same small reading under each of these names."""
    b = tmp_path / 'b'
    shutil.copytree(B, b, ignore=shutil.ignore_patterns('agents', 'bugs', 'impl', '__pycache__', '.fcp*'))
    for s in sets:
        (b / 'formal' / f'{s}.yaml').write_text(textwrap.dedent(READING.format(s=s)))
    return str(b)


@pytest.fixture
def small(tmp_path, monkeypatch):
    """That bundle with readings `one` and `two`, and searches that answer at
    once: no conflict, no open choice, every scenario possible; the readings
    agree on R-RET-1 and differ on R-EX-1."""
    for k in ('SCOPE_BUDGET', 'CONFLICT_BUDGET', 'COMPARE_BUDGET'):       # check() sets them: put them back
        monkeypatch.setattr(SW, k, getattr(SW, k))
    monkeypatch.setattr(Session, 'consistency', lambda self, s, **kw: {})
    monkeypatch.setattr(SW, 'conflicts', lambda S, s, fn: dict(NONE))
    monkeypatch.setattr(SW, 'choices', lambda S, s, fn, signals: {'open': {}, 'checked': 0})
    monkeypatch.setattr(SW, 'compare', lambda S, a, b, fn, **kw: json.loads(json.dumps(SAME)))
    # the call of SAME is made up, and a made-up call does not pass a replay: it is not replayed here
    # (tests/test_replay.py has the replay, and what a review says when a call does not pass)
    monkeypatch.setattr(SW, 'shows', lambda recs: False)
    return copy(tmp_path, 'one', 'two')


def quiet(*a):
    pass


def test_a_search_that_fails_leaves_a_partial_review(small, monkeypatch):
    """Found on HumanEval/49, 59 and 144: one search that failed ended the
    check, and the request got no review.  The step is now listed with the
    reason, the other steps run, and nothing is settled that rests on it."""
    full = RV.check(small, None, ['one'], log=quiet)
    assert full['failed'] == [] and {'R-RET-1', 'R-EX-1'} <= set(full['certified'])
    assert [s['step'] for s in full['steps']] == ['the scenarios of one', 'the conflicts of one',
                                                 'the open choices of one']
    assert 'This review is partial' not in RV.report(Session(small, sets=['one']), full)

    def boom(S, s, fn):
        raise ValueError('boom')

    monkeypatch.setattr(SW, 'conflicts', boom)
    lines = []
    out = RV.check(small, None, ['one'], log=lines.append)
    assert out['failed'] == [{'step': 'the conflicts of one', 'why': 'ValueError: boom', 'rests': 'all',
                              'reading': None}]
    assert out['prompt']['one']['conflicts'] == NONE
    assert out['certified'] == [] and out['queue'] == full['queue']        # the questions of the other steps stand
    assert lines == ['  the scenarios of one', '  the conflicts of one',
                     '  the conflicts of one: failed (ValueError: boom)', '  the open choices of one']
    text = RV.report(Session(small, sets=['one']), out)
    assert '## This review is partial\n1 of the 3 steps of the check did not end. What the other steps found ' \
        'stands; no requirement is settled that rests on one of these:\n- the conflicts of one: ValueError: boom\n' \
        in text
    assert 'Settled: 0 requirements.' in text and '## Settled' not in text


def test_a_scenario_search_that_fails_unsettles_the_scenarios_of_its_reading(small, monkeypatch):
    full = RV.check(small, None, ['one'], log=quiet)

    def boom(self, s, **kw):
        raise RuntimeError('the solver\n  ended')

    monkeypatch.setattr(Session, 'consistency', boom)
    out = RV.check(small, None, ['one'], log=quiet)
    assert out['failed'] == [{'step': 'the scenarios of one', 'why': 'RuntimeError: the solver ended',
                              'rests': 'scenarios', 'reading': 'one'}]
    assert out['scenarios']['one'] == {'impossible': [], 'forbidden': [], 'blocked': [], 'undecided': []}
    assert out['certified'] == [r for r in full['certified'] if r != 'R-EX-1']     # the example is not settled
    assert out['queue'] == full['queue']                                         # and no question says it is wrong


def test_a_comparison_that_fails_shows_no_disagreement_and_no_agreement(small, monkeypatch):
    full = RV.check(small, None, ['one', 'two'], log=quiet)
    asked = [q for q in full['queue'] if q['kind'] == 'readings']
    assert [(q['reqs'], q['relation'], q['calls']) for q in asked] == \
        [(['R-EX-1'], 'INCOMPARABLE', ['checkout(7, 0, 0) -> 7, 0'])]
    assert 'R-RET-1' in full['certified'] and 'R-EX-1' not in full['certified']

    def fails(which):
        def compare(S, a, b, fn, context=False, **kw):
            if context == which:
                raise ValueError('boom')
            return json.loads(json.dumps(SAME))
        monkeypatch.setattr(SW, 'compare', compare)
        return RV.check(small, None, ['one', 'two'], log=quiet)

    out = fails(True)                          # in context: what the verdicts are drawn from
    assert out['failed'] == [{'step': 'the comparison of one and two, in context', 'why': 'ValueError: boom',
                              'rests': 'all', 'reading': None, 'reqs': ['R-EX-1']}]
    # what the plain one closed in both directions is kept (the next tests); R-EX-1 rests on the failed step
    assert out['readings'] == {'R-RET-1': {'plain': 'EQUIVALENT', 'context': 'EQUIVALENT', 'witness': None,
                                           'carried': list(SW.WITNESSES)},
                               'R-EX-1': {'plain': 'INCOMPARABLE', 'context': None, 'witness': None}}
    assert out['certified'] == full['certified'] and not [q for q in out['queue'] if q['kind'] == 'readings']
    assert [q for q in out['queue'] if q['kind'] != 'readings'] == [q for q in full['queue'] if q['kind'] != 'readings']
    out = fails(False)                         # the plain one: no verdict rests on it
    assert out['failed'] == [{'step': 'the comparison of one and two', 'why': 'ValueError: boom',
                              'rests': 'none', 'reading': None}]
    assert out['readings']['R-EX-1'] == {'plain': None, 'context': 'INCOMPARABLE',
                                        'witness': ['checkout(7, 0, 0) -> 7, 0']}
    assert out['certified'] == full['certified'] and out['queue'] == full['queue']


def test_a_failed_comparison_in_context_keeps_what_the_plain_one_closed(small, monkeypatch):
    """The verdicts of a review rest on the comparison of its two readings
    in context.  When that step failed, the review certified nothing, also
    where the comparison without context had ended.  For a requirement that
    one closed in both directions the comparison in context has nothing to
    ask (SW.compare), so its record is known without it (SW.carried_over),
    and so is the record of a requirement that one reading alone states.
    These keep what a review whose comparison ended says of them.  The
    failed step names the other requirements, which alone rest on it: none
    of them is settled or certified, and no question is asked about them."""
    a_b, b_a = SW.WITNESSES
    step = 'the comparison of one and two, in context'
    same = {'relation': 'EQUIVALENT', 'status': {a_b: 'none', b_a: 'none'}, 'k': 1, 'exact': True, 'engine': 'z3-int'}
    found = {'R-RET-1': same,
             'R-EX-1': {**same, 'relation': 'A-STRONGER', 'status': {a_b: 'none', b_a: 'witness'},
                        b_a: {'calls': [[7, 0, 0]], 'lines': ['checkout(7, 0, 0) -> 7, 0']}},
             'R-ERR-1': {**same, 'relation': 'UNKNOWN', 'status': {a_b: 'none', b_a: 'unknown'}},
             'R-IN-1': {'relation': 'ONLY-A', 'k': 1, 'exact': True}}
    fail = []

    def compare(S, a, b, fn, context=False, plain=None, **kw):
        if not context:
            return json.loads(json.dumps(found))
        if fail:
            raise ValueError('boom')
        # in context the two readings are equal on every requirement that both state
        return {r: dict(x) if x['relation'] == 'ONLY-A' else {**same, 'carried': list(SW.closed(plain[r]))}
                for r, x in found.items()}

    monkeypatch.setattr(SW, 'compare', compare)
    full = RV.check(small, None, ['one', 'two'], log=quiet)
    assert full['failed'] == [] and {'R-RET-1', 'R-EX-1'} <= set(full['certified'])
    fail.append(1)
    out = RV.check(small, None, ['one', 'two'], log=quiet)
    assert out['failed'] == [{'step': step, 'why': 'ValueError: boom', 'rests': 'all', 'reading': None,
                              'reqs': ['R-ERR-1', 'R-EX-1']}]
    assert out['readings'] == {
        'R-RET-1': {'plain': 'EQUIVALENT', 'context': 'EQUIVALENT', 'witness': None, 'carried': [a_b, b_a]},
        'R-EX-1': {'plain': 'A-STRONGER', 'context': None, 'witness': None},
        'R-ERR-1': {'plain': 'UNKNOWN', 'context': None, 'witness': None},
        'R-IN-1': {'plain': 'ONLY-A', 'context': 'ONLY-A', 'witness': None}}
    # what does not rest on the step reads as in the review whose comparison ended, and the rest has no relation
    assert all(out['readings'][r] == full['readings'][r] for r in ('R-RET-1', 'R-IN-1'))
    assert sorted(r for r, x in out['readings'].items() if x['context'] is None) == out['failed'][0]['reqs']
    assert out['certified'] == [r for r in full['certified'] if r != 'R-EX-1'] and 'R-RET-1' in out['certified']
    assert out['queue'] == full['queue'] and not [q for q in out['queue'] if q['kind'] in ('readings', 'undecided')]
    assert [s['step'] for s in out['steps']] == [s['step'] for s in full['steps']]      # and no step is added
    text = RV.report(Session(small, sets=['one', 'two']), out)
    assert f'## This review is partial\n1 of the {len(out["steps"])} steps of the check did not end. What the ' \
        'other steps found stands; no requirement is settled that rests on one of these:\n' \
        f'- {step}: ValueError: boom\n' \
        '  - Only R-ERR-1, R-EX-1 rest on it: whether the two readings agree on them in context was not shown. ' \
        'On every other requirement that both readings state, the comparison without context found no run that ' \
        'one reading accepts and the other rejects, and in context there is none either.\n\n' in text
    assert '- R-RET-1: ' in text.split('## Settled')[1].split('## Questions')[0]
    # with code the same: what the code meets under both readings is certified, except what rests on the step
    coded(monkeypatch, {'one': PASSED, 'two': PASSED}, {})
    code = os.path.join(B, 'impl', 'ref.py')
    out = RV.check(small, code, ['one', 'two'], log=quiet)
    fail.clear()
    full = RV.check(small, code, ['one', 'two'], log=quiet)
    assert {'R-RET-1', 'R-EX-1'} <= set(full['certified'])
    assert out['failed'][0]['reqs'] == ['R-ERR-1', 'R-EX-1'] and len(out['failed']) == 1
    assert out['certified'] == [r for r in full['certified'] if r != 'R-EX-1'] and out['queue'] == full['queue']
    text = RV.report(Session(small, sets=['one', 'two']), out)
    assert '  - Only R-ERR-1, R-EX-1 rest on it: whether the two readings agree on them in context was not shown. ' \
        in text
    assert 'no requirement is certified that rests on one of these:' in text


def test_a_failed_comparison_in_context_keeps_nothing_where_nothing_is_known(small, monkeypatch):
    """Two cases in which every requirement rests on the failed comparison
    in context, as before.  The comparison without context failed too: there
    is nothing to keep.  And the comparison is the bounded one, of an object
    or of a function with effects (Session.compare): in context it can end
    with no behavior at all that meets the other requirements (NO-CONTEXT),
    also on a requirement that is equal without context, so nothing is known
    of a requirement before it ran."""
    step = 'the comparison of one and two, in context'
    entry = {'step': step, 'why': 'ValueError: boom', 'rests': 'all', 'reading': None}

    def partial(out):
        text = RV.report(Session(small, sets=['one', 'two']), out)
        return out['certified'] == [] and 'rests on it: ' not in text and 'rest on it: ' not in text and \
            f'- {step}: ValueError: boom\n' in text

    def both(S, a, b, fn, **kw):
        raise ValueError('boom')

    monkeypatch.setattr(SW, 'compare', both)
    out = RV.check(small, None, ['one', 'two'], log=quiet)
    assert out['failed'] == [{**entry, 'step': 'the comparison of one and two', 'rests': 'none'}, entry]
    assert out['readings'] == {} and partial(out)

    def bounded(self, a, b, context=False, **kw):
        if context:
            raise ValueError('boom')
        return json.loads(json.dumps(SAME))

    monkeypatch.setattr('fcp.effects.interface', lambda S, fn: {'methods': []})       # a function with effects
    monkeypatch.setattr('fcp.effects.conflicts', lambda S, s, fn, ifc: dict(NONE))
    monkeypatch.setattr(Session, 'compare', bounded)
    out = RV.check(small, None, ['one', 'two'], log=quiet)
    assert out['failed'] == [entry]
    assert out['readings'] == {'R-RET-1': {'plain': 'EQUIVALENT', 'context': None, 'witness': None},
                               'R-EX-1': {'plain': 'INCOMPARABLE', 'context': None, 'witness': None}}
    assert partial(out)


def test_only_the_requirements_a_failed_step_names_rest_on_it(small):
    """The verdicts and the report, from the file of a review.  A failed
    step that names requirements holds back those, and no question is asked
    about them; one that names none holds back every requirement, as in
    every review written before a step could name any."""
    S = Session(small, sets=['one', 'two'])
    step = 'the comparison of one and two, in context'
    carry = 'the comparison without context found no run that one reading accepts and the other rejects, and in ' \
        'context there is none either.\n'
    known = {'R-RET-1': {'plain': 'EQUIVALENT', 'context': 'EQUIVALENT', 'witness': None,
                         'carried': list(SW.WITNESSES)},
             'R-EX-1': {'plain': 'A-STRONGER', 'context': None, 'witness': None}}

    def drawn(failed, readings=known, **more):
        out = {'sets': ['one', 'two'], 'readings': readings, 'failed': failed, 'steps': [{}] * 8, 'code': None,
               'prompt': {s: {'conflicts': {'conflicts': []}, 'open': {'open': {}}} for s in ('one', 'two')}, **more}
        out['certified'], out['queue'] = RV.verdicts(S, out)
        assert not [q for q in out['queue'] if q['kind'] in ('readings', 'undecided')]
        return [r for r in out['certified'] if r in known], RV.report(S, out)

    def entry(**more):
        return {'step': step, 'why': 'did not end in 3 s', 'rests': 'all', 'reading': None, **more}

    settled, text = drawn([])
    assert settled == ['R-RET-1', 'R-EX-1']                                    # no relation in context: agreeing
    settled, text = drawn([entry()])                                           # a review written before
    assert settled == [] and f'- {step}: did not end in 3 s\n\n' in text and 'rests on it: ' not in text
    settled, text = drawn([entry(reqs=['R-EX-1'])])
    assert settled == ['R-RET-1']
    assert f'- {step}: did not end in 3 s\n  - Only R-EX-1 rests on it: whether the two readings agree on it in ' \
        'context was not shown. On every other requirement that both readings state, ' + carry in text
    settled, text = drawn([entry(reqs=[])], {'R-RET-1': known['R-RET-1']})
    assert settled == ['R-RET-1', 'R-EX-1']
    assert f'- {step}: did not end in 3 s\n  - No requirement rests on it: on every requirement that both ' \
        'readings state, ' + carry in text
    # beside a failed step that names none, nothing is settled
    other = {'step': 'the conflicts of two', 'why': 'ValueError: boom', 'rests': 'all', 'reading': None}
    settled, text = drawn([entry(reqs=['R-EX-1']), other])
    assert settled == [] and '  - Only R-EX-1 rests on it: ' in text
    assert RV.held_back([]) == (False, []) and RV.held_back([entry()]) == (True, [])
    assert RV.held_back([entry(reqs=['R-EX-1'])]) == (False, ['R-EX-1'])
    assert RV.held_back([entry(reqs=[]), {'step': 'an old one', 'why': 'x'}]) == (True, [])     # no 'rests': all
    assert RV.held_back([entry(reqs='R-EX-1')]) == (True, [])                  # what is not a list names none
    assert RV.held_back([{**entry(reqs=['R-EX-1']), 'rests': 'none'}]) == (False, [])
    # a failed step on which no verdict rests, or the examples of one reading: as before
    assert drawn([entry(reqs=['R-EX-1']), {**other, 'rests': 'none'}])[0] == ['R-RET-1']
    assert drawn([entry(reqs=[]), {**other, 'rests': 'scenarios', 'reading': 'one'}],
                 {'R-RET-1': known['R-RET-1']})[0] == ['R-RET-1']                # R-EX-1 is an example
    # a check that gave no verdicts and whose file holds such a step: the report says no more than it did
    un = {'sets': ['one', 'two'], 'readings': {}, 'failed': [entry(reqs=['R-EX-1'])], 'steps': [{}] * 8,
          'code': None, 'unchecked': 'outside its steps, the checking process ended with exit code 7',
          'certified': [], 'queue': [], 'prompt': {}}
    text = RV.report(S, un)
    assert 'rests on it: ' not in text and f'- {step}: did not end in 3 s\n' in text


def test_the_comparison_in_context_is_given_what_the_plain_one_found(small, monkeypatch):
    """The verdicts of a review rest on the comparison of its two readings in
    context.  That comparison is given the result of the plain one, which
    runs first, so that a direction closed there is not asked again
    (SW.compare; tests/test_limits.py).  A requirement it did not have to ask
    about says so in the review's file.  Where the plain comparison failed,
    the one in context is given nothing and asks everything."""
    seen = []

    def compare(S, a, b, fn, context=False, plain=None, **kw):
        seen.append((context, plain))
        if not context and len(seen) > 2:
            raise ValueError('boom')
        recs = json.loads(json.dumps(SAME))
        if context and plain:
            recs['R-RET-1']['carried'] = list(SW.WITNESSES)
        return recs

    monkeypatch.setattr(SW, 'compare', compare)
    out = RV.check(small, None, ['one', 'two'], log=quiet)
    assert seen == [(False, None), (True, SAME)]
    assert out['readings'] == {'R-RET-1': {'plain': 'EQUIVALENT', 'context': 'EQUIVALENT', 'witness': None,
                                           'carried': list(SW.WITNESSES)},
                               'R-EX-1': {'plain': 'INCOMPARABLE', 'context': 'INCOMPARABLE',
                                          'witness': ['checkout(7, 0, 0) -> 7, 0']}}
    assert 'R-RET-1' in out['certified'] and 'R-EX-1' not in out['certified']
    again = RV.check(small, None, ['one', 'two'], log=quiet)
    assert seen[2:] == [(False, None), (True, {})]
    assert again['readings']['R-RET-1'] == {'plain': None, 'context': 'EQUIVALENT', 'witness': None}
    assert again['certified'] == out['certified'] and again['queue'] == out['queue']


def test_code_that_could_not_be_run_on_the_scope_is_not_certified(small, monkeypatch):
    code = os.path.join(B, 'impl', 'ref.py')

    def boom(S, fn, codes):
        raise ValueError('boom')

    monkeypatch.setattr(SW, 'calls_for', boom)
    out = RV.check(small, code, ['one'], log=quiet)
    assert [(x['step'], x['why'], x['rests']) for x in out['failed']] == [
        ('the code on the scope', 'ValueError: boom', 'all'),
        ('the proofs beyond the scope under one', 'not run: the code on the scope did not end', 'none')]
    assert out['code'] == {'calls': 0, 'verify': {'one': {}}} and out['proofs'] == {}
    assert out['certified'] == [] and not [q for q in out['queue'] if q['kind'] == 'code']
    text = RV.report(Session(small, sets=['one']), out)
    assert '2 of the 5 steps of the check did not end.' in text and 'no requirement is certified that rests' in text


def test_a_proof_that_fails_leaves_what_the_scope_showed(small, monkeypatch):
    from fcp import prove as P
    code = os.path.join(B, 'impl', 'ref.py')
    passed = {'T-P': {'req': 'R-RET-1', 'status': 'PASS'}, 'T-Q': {'req': 'R-RET-1', 'status': 'PASS'},
              'S-OK': {'req': 'R-EX-1', 'status': 'COVERED'}}
    monkeypatch.setattr(SW, 'calls_for', lambda S, fn, codes: [])
    monkeypatch.setattr(SW, 'run', lambda fn, code, calls: [])
    monkeypatch.setattr(SW, 'trace', lambda fn, calls, res: {})
    monkeypatch.setattr(SW, 'outcome_summary', lambda fn, res: {'counts': {}})
    monkeypatch.setattr(SW, 'verify', lambda S, s, fn, code, calls, res, cols: dict(passed))

    def boom(S, s, fn, code, calls, res):
        raise ValueError('boom')

    monkeypatch.setattr(P, 'prove', boom)
    out = RV.check(small, code, ['one'], log=quiet)
    assert out['failed'] == [{'step': 'the proofs beyond the scope under one', 'why': 'ValueError: boom',
                              'rests': 'none', 'reading': None}]
    assert set(out['certified']) == {'R-RET-1', 'R-EX-1'} and out['proofs'] == {}
    text = RV.report(Session(small, sets=['one']), out)
    assert 'Certified: 2 requirements.' in text and '1 of the 5 steps of the check did not end.' in text


# ---------------------------------------------------------------- a review that is written whatever the check does
def test_a_check_without_verdicts_still_asks_what_was_flagged(tmp_path):
    res = RV.unchecked(B, ['gold'], 'it did not start')
    assert res['unchecked'] == 'it did not start' and res['certified'] == [] and res['code'] is None
    assert {q['kind'] for q in res['queue']} == {'ambiguity'}
    assert sorted(r for q in res['queue'] for r in q['reqs']) == ['R-ROUND-1', 'R-SHIP-1', 'R-STACK-1']
    text = RV.report(Session(B, sets=['gold']), res)
    assert 'The check gave no verdicts: it did not start. Nothing is settled; the questions below are' in text
    assert f'Settled: 0 requirements. Questions: {len(res["queue"])}.' in text
    coded = RV.unchecked(B, ['gold'], 'it did not start', coded=True)
    assert coded['code'] == {'calls': 0, 'verify': {'gold': {}}}
    assert 'Nothing is certified' in RV.report(Session(B, sets=['gold']), coded)
    res = RV.unchecked(str(tmp_path / 'none'), ['gold'], 'the bundle does not load')      # nothing to ask from
    assert res['queue'] == [] and 'The check gave no verdicts: the bundle does not load.' in RV.report(None, res)


STUBBED = '''
import os, sys, time
sys.path.insert(0, sys.argv[1])
from fcp import review, software as SW
from fcp.analyses import Session
mode = os.environ.get('FCP_TEST_MODE')
if mode == 'die':
    os._exit(7)
Session.consistency = lambda self, s, **kw: {}
SW.conflicts = lambda S, s, fn: {'conflicts': [], 'candidates': 0, 'checked': 0}
SW.choices = lambda S, s, fn, signals: {'open': {}, 'checked': 0}


def compare(S, a, b, fn, context=False, **kw):
    if context and mode == 'raise':
        raise ValueError('boom')
    if context and mode == 'sleep':
        time.sleep(120)
    return {'R-RET-1': {'relation': 'EQUIVALENT'}}


SW.compare = compare
sys.exit(review.worker(sys.argv[2]))
'''


def test_a_review_is_written_whatever_its_check_does(tmp_path, monkeypatch):
    """`review` on a directory that holds the bundle and both readings, its
    check in a process whose searches answer at once, fail, or do not end."""
    out = tmp_path / 'out'
    out.mkdir()
    shutil.move(copy(tmp_path, 'agent_a', 'agent_b'), out / 'bundle')
    monkeypatch.setattr(RV, 'WORKER', STUBBED)

    def review(mode, **kw):
        monkeypatch.setenv('FCP_TEST_MODE', mode)
        res = RV.review('', None, str(out), log=quiet, resume=True, variants=False, signature='-', **kw)
        with open(out / 'review.json') as f:
            assert json.load(f) == json.loads(json.dumps(res, default=str))
        assert not (out / 'check_state.json').exists() and not (out / 'check_state.json.err').exists()
        return res, (out / 'review.md').read_text()

    def again(res, text):                      # the verdicts drawn again from the stored review: the same review
        new = RV.rereport(str(out))
        return new == json.loads(json.dumps(res, default=str)) and (out / 'review.md').read_text() == text

    res, text = review('ok')
    assert res['failed'] == [] and 'unchecked' not in res and 'trace' not in res
    assert len(res['steps']) == 8 and 'R-RET-1' in res['certified']
    assert 'This review is partial' not in text and not (out / 'check_errors.txt').exists()
    assert again(res, text)
    ok = res['certified']
    res, text = review('raise')
    assert [x['step'] for x in res['failed']] == ['the comparison of agent_a and agent_b, in context']
    # the comparison without context closed R-RET-1 in both directions: no requirement rests on the failed step
    assert res['failed'][0]['reqs'] == [] and res['certified'] == ok and res['trace'] == 'check_errors.txt'
    assert '  - No requirement rests on it: ' in text
    assert again(res, text)
    assert 'ValueError: boom' in (out / 'check_errors.txt').read_text()
    assert 'What the checking process printed about it is in check_errors.txt.' in text
    res, text = review('sleep', step_seconds=3)
    assert [(x['step'], x['why']) for x in res['failed']] == [
        ('the comparison of agent_a and agent_b, in context', 'did not end in 3 s')]
    assert 'trace' not in res and not (out / 'check_errors.txt').exists()      # nothing printed; the older trace is gone
    assert res['failed'][0]['reqs'] == [] and res['certified'] == ok           # named by the check that went on
    res, text = review('die')
    assert res['unchecked'] == 'outside its steps, the checking process ended with exit code 7'
    assert res['certified'] == [] and res['queue'] and all(q['kind'] == 'ambiguity' for q in res['queue'])
    assert 'The check gave no verdicts: outside its steps, the checking process ended with exit code 7. ' \
        'Nothing is settled' in text
    assert again(res, text)                    # no verdicts to draw again: left as it is
    (out / 'bundle' / 'formal' / 'agent_b.yaml').write_text('set: agent_b\nproperties: [unclosed')
    res, text = review('ok')                   # a reading that does not load: said, and no question to ask
    assert res['unchecked'] and res['queue'] == [] and res['trace'] == 'check_errors.txt'
    assert 'The check gave no verdicts: ' + res['unchecked'] in text
    assert again(res, text)                    # also where the bundle does not load


def test_the_limits_of_a_check_are_options_of_the_command(monkeypatch, capsys):
    from fcp import cli
    seen = []
    results = [{'certified': ['R-1'], 'queue': [{}], 'failed': [{'step': 'x'}], 'steps': [{}, {}, {}]},
               {'certified': [], 'queue': [], 'unchecked': 'it did not start', 'failed': [], 'steps': []},
               {'certified': ['R-1', 'R-2'], 'queue': [], 'failed': [], 'steps': [{}]}]

    def review(request, code, out, **kw):
        seen.append(kw)
        return results[len(seen) - 1]

    monkeypatch.setattr(RV, 'review', review)
    monkeypatch.delenv('FCP_AGENT_WS', raising=False)
    assert cli.main(['review', '--request', 'r.md', '--signature', 's.py', '--out', 'o']) == 0
    assert [seen[-1][k] for k in ('memory', 'step_seconds', 'check_seconds')] == [None, 900, 3600]
    assert (RV.STEP_SECONDS, RV.CHECK_SECONDS) == (900, 3600)
    assert capsys.readouterr().out == \
        'partial: 1 of 3 steps of the check did not end; settled 1 requirements; 1 questions -> o/review.md\n'
    assert cli.main(['review', '--request', 'r.md', '--code', 'c.py', '--out', 'o', '--memory', '2.5',
                     '--step-seconds', '60', '--check-seconds', '600']) == 0
    assert [seen[-1][k] for k in ('memory', 'step_seconds', 'check_seconds')] == [2.5, 60, 600]
    assert capsys.readouterr().out == \
        'the check gave no verdicts; certified 0 requirements; 0 questions -> o/review.md\n'
    assert cli.main(['review', '--request', 'r.md', '--code', 'c.py', '--out', 'o', '--memory', '0']) == 0
    assert seen[-1]['memory'] == 0                                            # no limit
    assert capsys.readouterr().out == 'certified 2 requirements; 0 questions -> o/review.md\n'


# ---------------------------------------------------------------- a model that does not translate
def test_a_model_that_does_not_translate_is_not_tried_twice(monkeypatch):
    """Found on HumanEval/49: yosys ran out of its 300 s on the monitors of a
    reading, and every search over that reading waited for it again."""
    from fcp import smt
    calls = []

    def slow(script, d):
        calls.append(script)
        raise subprocess.TimeoutExpired('yosys', 300)

    monkeypatch.setattr(smt, 'run_yosys', slow)
    monkeypatch.setattr(smt, '_FAILED', {})
    for _ in range(2):
        with pytest.raises(smt.TranslationFailed) as e:
            smt.SmtModel({'m.v': 'module m(input clk); endmodule\n'}, [], 'm')
        assert str(e.value) == 'the translation of the monitors for the solver (yosys) did not end in 300 s'
    assert len(calls) == 1
    assert RV.why_failed(e.value) == str(e.value)          # said as it is, without the name of the exception

    def broken(script, d):
        raise RuntimeError("yosys failed\nERROR: Module `x' not found!\n\n")

    monkeypatch.setattr(smt, 'run_yosys', broken)
    with pytest.raises(smt.TranslationFailed) as e:
        smt.SmtModel({'n.v': 'module n; endmodule\n'}, [], 'n')
    assert str(e.value) == "the translation of the monitors for the solver (yosys) failed: ERROR: Module `x' not found!"


def test_a_comparison_whose_bit_level_model_does_not_translate_stays_undecided(tmp_path, monkeypatch):
    """What the integer encoding decides stands; the rest is UNKNOWN, the
    limits say why once, and no bit-level process starts for a model that
    did not translate in this one."""
    import concurrent.futures
    from fcp import smt
    b = copy(tmp_path, 'one', 'two')
    S = Session(b, sets=['one', 'two'])
    fn = SW.function(S)
    why = 'the translation of the monitors for the solver (yosys) did not end in 300 s'
    said = f'the comparison of one and two, in context: {why}; what the integer encoding left open stays undecided'
    tried = []

    def no_integers(*a, **kw):
        raise SW.Unsupported('not here')

    def no_bits(*a, **kw):
        tried.append(a)
        raise smt.TranslationFailed(why)

    def no_pool(*a, **kw):
        raise AssertionError('a bit-level process was started')

    monkeypatch.setattr(SW, 'BUDGET_HIT', [])
    monkeypatch.setattr(SW, '_IntSpec', no_integers)
    monkeypatch.setattr(SW, '_Spec', no_bits)
    monkeypatch.setattr(concurrent.futures, 'ProcessPoolExecutor', no_pool)
    out = SW.compare(S, 'one', 'two', fn, context=True, bit_timeout=300)
    assert 'R-RET-1' in out and {x['relation'] for x in out.values()} == {'UNKNOWN'}
    assert SW.BUDGET_HIT == [said] and len(tried) == 1
    job = (b, ['one', 'two'], 1, 'one', 'two', 'R-RET-1', True, 5)
    assert SW._bit_job(job) == ('untranslated', why)       # in a process of its own: told, not raised

    class Spec:                                # the model translates here, and not in the processes beside it
        sol = types.SimpleNamespace(set=lambda *a: None)

    class Pool:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def map(self, f, jobs):
            return [('untranslated', why) for _ in jobs]

    monkeypatch.setattr(SW, '_Spec', lambda *a, **kw: Spec())
    monkeypatch.setattr(SW, 'scope_separation', lambda *a, **kw: {'calls': 0, 'witness': None})
    monkeypatch.setattr(concurrent.futures, 'ProcessPoolExecutor', Pool)
    SW.BUDGET_HIT.clear()
    out = SW.compare(S, 'one', 'two', fn, context=True, bit_timeout=300)
    assert {x['relation'] for x in out.values()} == {'UNKNOWN'} and SW.BUDGET_HIT == [said]
    assert out['R-RET-1']['scope_check']['witness_a_not_b']['bit'] == 'unknown'


# ---------------------------------------------------------------- a requirement a reading leaves without a rule
LEFT_OUT = ['R-ERR-1', 'R-MEM-1', 'R-COUP-1', 'R-MONO-1', 'R-STACK-1', 'R-ROUND-1', 'R-SHIP-1']


def test_a_requirement_no_reading_states_is_asked_about_and_not_settled(small):
    """Before any code a requirement was settled when the readings did not
    disagree on it, no conflict held it and nothing was flagged.  Readings
    that hold no rule for it meet all three.  It is now a question."""
    out = RV.check(small, None, ['one', 'two'], log=quiet)
    asked = {q['reqs'][0]: q for q in out['queue'] if q['kind'] == 'unformalized'}
    assert sorted(asked) == sorted(LEFT_OUT)
    assert all(q['readings'] == ['one', 'two'] and q['calls'] == [] for q in asked.values())
    assert asked['R-MEM-1']['question'] == 'no reading states this requirement as a rule, so nothing here was ' \
        'checked against it: should it constrain the answer?'
    assert out['certified'] == ['R-RET-1']                  # R-EX-1: the readings differ on it
    text = RV.report(Session(small, sets=['one', 'two']), out)
    assert '**unformalized** (R-MEM-1): no reading states this requirement as a rule' in text
    assert 'Settled: 1 requirements.' in text


def test_a_requirement_one_reading_leaves_out_is_asked_about_with_its_reason(tmp_path, small):
    """One reader's rule for a requirement is no agreement of two readers."""
    more = textwrap.dedent(READING.format(s='more')).replace(
        'scenarios:', "  - {id: T-E, req: R-ERR-1, pattern: implies, args: {trigger: 'subtotal < 6', "
        "cond: 'outcome == 1'}}\nscenarios:")
    with open(os.path.join(small, 'formal', 'more.yaml'), 'w') as f:
        f.write(more)
    with open(os.path.join(small, 'formal', 'one.yaml'), 'a') as f:
        f.write('unformalized:\n  - {req: R-ERR-1, reason: "the request names   no\\n    error"}\n')
    assert 'R-ERR-1' in {it.req for it in Session(small, sets=['more']).mon('more').items.values()}
    out = RV.check(small, None, ['one', 'more'], log=quiet)
    q = next(q for q in out['queue'] if q['kind'] == 'unformalized' and q['reqs'] == ['R-ERR-1'])
    assert q['readings'] == ['one']
    assert q['question'] == 'one does not state this requirement as a rule (one: "the request names no error"), ' \
        'so the readings were not compared on it: should it constrain the answer?'
    assert 'R-ERR-1' not in out['certified'] and 'R-RET-1' in out['certified']
    both = RV.check(small, None, ['more'], log=quiet)       # stated by every reading that is given: no question
    assert 'R-ERR-1' in both['certified']
    assert sorted(q['reqs'][0] for q in both['queue'] if q['kind'] == 'unformalized') == sorted(set(LEFT_OUT) - {'R-ERR-1'})


def test_code_is_not_certified_on_a_requirement_a_reading_leaves_out(small, monkeypatch):
    """With code such a requirement was never certified, and never asked
    about either: it was in neither list of the report."""
    code = os.path.join(B, 'impl', 'ref.py')
    passed = {'T-P': {'req': 'R-RET-1', 'status': 'PASS'}, 'T-Q': {'req': 'R-RET-1', 'status': 'PASS'},
              'S-OK': {'req': 'R-EX-1', 'status': 'COVERED'}}
    monkeypatch.setattr(SW, 'calls_for', lambda S, fn, codes: [])
    monkeypatch.setattr(SW, 'run', lambda fn, code, calls: [])
    monkeypatch.setattr(SW, 'trace', lambda fn, calls, res: {})
    monkeypatch.setattr(SW, 'outcome_summary', lambda fn, res: {'counts': {}})
    monkeypatch.setattr(SW, 'verify', lambda S, s, fn, code, calls, res, cols: dict(passed))
    monkeypatch.setattr('fcp.prove.prove', lambda S, s, fn, code, calls, res: {'status': 'ok', 'requirements': {}})
    out = RV.check(small, code, ['one'], log=quiet)
    assert out['failed'] == [] and set(out['certified']) == {'R-RET-1', 'R-EX-1'}
    assert sorted(q['reqs'][0] for q in out['queue'] if q['kind'] == 'unformalized') == sorted(LEFT_OUT)
    listed = set(out['certified']) | {r for q in out['queue'] for r in q['reqs']}
    S = Session(small, sets=['one'])
    assert listed >= {r.id for r in S.b.requirements.values() if r.kind in ('guarantee', 'scenario') and r.doc != 'FRAME'}


# ---------------------------------------------------------------- requirements of the other kinds
def other_kinds(bundle: str):
    """What a decomposer writes besides guarantees and examples: a phrase
    flagged on a definition, one on an assumption, the phrase of R-SHIP-1
    flagged on a definition as well, and a requirement that is not about
    calls."""
    path = os.path.join(bundle, 'requirements.yaml')
    with open(path) as f:
        doc = yaml.safe_load(f)
    by = {r['id']: r for r in doc['requirements']}
    by['R-IN-2']['ambiguity'] = [{'phrase': 'coupon', 'readings': ['a percentage', 'a code']}]
    by['R-IN-3'].update(kind='assumption', ambiguity=[{'phrase': 'member', 'readings': ['0 or 1', 'any number']}])
    by['R-IN-1']['ambiguity'] = [dict(by['R-SHIP-1']['ambiguity'][0])]
    doc['requirements'].append({'id': 'R-NF-1', 'doc': 'SPEC', 'quote': 'It must be fast.', 'kind': 'non_functional',
                                'text': 'The function is fast.', 'lines': [1],
                                'ambiguity': [{'phrase': 'fast', 'readings': ['under a second', 'linear time']}]})
    with open(path, 'w') as f:
        yaml.safe_dump(doc, f, sort_keys=False)


def test_a_phrase_flagged_on_a_requirement_of_another_kind_is_asked_about(small):
    """The queue asked about the phrases flagged on guarantees and examples
    only.  A phrase flagged on a definition or an assumption decides how the
    guarantees are read, and it was in no list of the report: asked about,
    such phrases are 251 more questions in 66 of the 72 stored reviews of
    the pilot."""
    before = RV.check(small, None, ['one', 'two'], log=quiet)
    other_kinds(small)
    out = RV.check(small, None, ['one', 'two'], log=quiet)
    flagged = [q for q in out['queue'] if q['kind'] == 'ambiguity']
    # the judged requirements first; then the others in the order of the request; one phrase, one question
    assert [q['reqs'] for q in flagged] == [['R-STACK-1'], ['R-ROUND-1'], ['R-SHIP-1', 'R-IN-1'], ['R-IN-2'],
                                            ['R-IN-3'], ['R-NF-1']]
    rest = lambda o: [q for q in o['queue'] if q['kind'] != 'ambiguity']
    assert rest(out) == rest(before) and out['certified'] == before['certified'] == ['R-RET-1']
    assert {q['reqs'][0] for q in out['queue'] if q['kind'] == 'unformalized'} == set(LEFT_OUT)     # no rule: no fault
    text = RV.report(Session(small, sets=['one', 'two']), out)
    assert '**ambiguity** (R-IN-2): "coupon" can mean: a percentage / a code. Which is meant?' in text
    assert '## Outside this review' in text and '- R-NF-1: The function is fast.' in text
    assert 'They are not settled, and nothing is said about them except where the report above names one:' in text
    assert '## Outside this review' not in RV.report(Session(B, sets=['gold']), before)       # nothing of that kind
    bare = RV.unchecked(small, ['one', 'two'], 'it did not start')          # the same questions without a check
    assert [q['reqs'] for q in bare['queue']] == [q['reqs'] for q in flagged]


def coded(monkeypatch, verify: dict, proofs: dict):
    """A check with code whose runs are these: verify[reading] and proofs[reading]."""
    monkeypatch.setattr(SW, 'calls_for', lambda S, fn, codes: [])
    monkeypatch.setattr(SW, 'run', lambda fn, code, calls: [])
    monkeypatch.setattr(SW, 'trace', lambda fn, calls, res: {})
    monkeypatch.setattr(SW, 'outcome_summary', lambda fn, res: {'counts': {}})
    monkeypatch.setattr(SW, 'verify', lambda S, s, fn, code, calls, res, cols: json.loads(json.dumps(verify[s])))
    monkeypatch.setattr('fcp.prove.prove', lambda S, s, fn, code, calls, res:
                        {'status': 'ok', 'requirements': json.loads(json.dumps(proofs.get(s, {})))})


PASSED = {'T-P': {'req': 'R-RET-1', 'status': 'PASS'}, 'T-Q': {'req': 'R-RET-1', 'status': 'PASS'},
          'S-OK': {'req': 'R-EX-1', 'status': 'COVERED'}}


def test_a_rule_stated_for_a_definition_that_the_code_breaks_is_a_question(small, monkeypatch):
    """Readers state rules for definitions too (five such items in the stored
    reviews).  The verdicts looked at guarantees and examples only, so a rule
    of this kind that the code broke would have been in no list."""
    broken = dict(PASSED, **{'T-D': {'req': 'R-IN-1', 'status': 'FAIL',
                                     'calls_shown': [{'call': 'checkout(5, 0, 0)', 'got': 'returned (5, 499)'}]}})
    coded(monkeypatch, {'one': broken}, {})
    out = RV.check(small, os.path.join(B, 'impl', 'ref.py'), ['one'], log=quiet)
    asked = [q for q in out['queue'] if q['kind'] == 'code']
    assert [(q['reqs'], q['calls']) for q in asked] == [(['R-IN-1'], ['checkout(5, 0, 0) -> returned (5, 499)'])]
    assert set(out['certified']) == {'R-RET-1', 'R-EX-1'}                   # a definition is never certified
    assert '**code** (R-IN-1): the code breaks this requirement here' in RV.report(Session(small, sets=['one']), out)


def test_a_call_outside_the_scope_is_shown_where_another_reading_leaves_the_requirement_out(small, monkeypatch):
    """A proof found calls outside the scope that break a requirement under
    one reading.  Where the other reading held no rule for it, the calls
    were not shown: only the question about the missing rule was asked."""
    more = textwrap.dedent(READING.format(s='more')).replace(
        'scenarios:', "  - {id: T-E, req: R-ERR-1, pattern: implies, args: {trigger: 'subtotal < 6', "
        "cond: 'outcome == 1'}}\nscenarios:")
    with open(os.path.join(small, 'formal', 'more.yaml'), 'w') as f:
        f.write(more)
    there = {'R-ERR-1': {'status': 'FAILS', 'call': 'checkout(-1, 0, 0)', 'conversation': ['returned (0, 499)'],
                         'confirmed': True}}
    coded(monkeypatch, {'one': PASSED, 'more': dict(PASSED, **{'T-E': {'req': 'R-ERR-1', 'status': 'PASS'}})},
          {'more': there})
    out = RV.check(small, os.path.join(B, 'impl', 'ref.py'), ['one', 'more'], log=quiet)
    asked = {q['kind']: q for q in out['queue'] if q['reqs'] == ['R-ERR-1']}
    assert set(asked) == {'code', 'unformalized'} and asked['unformalized']['readings'] == ['one']
    assert asked['code']['reading'] == 'more' and asked['code']['calls'] == ['checkout(-1, 0, 0): returned (0, 499)']
    assert asked['code']['question'].startswith('the code passes this requirement on the scope, but these calls '
                                                'outside it break it (replayed)')
    assert 'R-ERR-1' not in out['certified']


# ---------------------------------------------------------------- a question behind which no comparison ended
SHARED = 'both readers gave the same answer to every ambiguity listed under "Shared answers"; '
CALL = ['checkout(7, 0, 0) -> 7, 0']


def test_a_question_says_what_a_comparison_showed_and_no_more(small):
    """A comparison that did not end and showed no call says nothing about a
    requirement.  The question about its two readings is then of the kind
    `undecided`, and the question about the answers the readers shared names
    the requirements that were shown to differ apart from the others."""
    S = Session(small, sets=['one', 'two'])

    def asked(readings=None, depends=None):
        out = {'sets': ['one', 'two'], 'readings': readings or {}, 'depends': depends or {},
               'prompt': {s: {'conflicts': {'conflicts': []}, 'open': {'open': {}}} for s in ('one', 'two')}}
        settled, queue = RV.verdicts(S, out)
        assert not (set(out['readings']) | set(out['depends'])) & set(settled)      # asked about: not settled
        return [q for q in queue if q['kind'] in ('readings', 'depends', 'undecided')]

    def two(relation, witness=None):
        return {'R-RET-1': {'plain': relation, 'context': relation, 'witness': witness}}

    def third(**found):
        return {r.replace('_', '-'): {'relation': rel, 'peers': ['one', 'two'], 'witness': w}
                for r, (rel, w) in found.items()}

    # the two readings of one requirement
    q, = asked(two('UNKNOWN'))
    assert (q['kind'], q['relation'], q['calls']) == ('undecided', 'UNKNOWN', [])
    assert q['question'] == ('the two readings of this requirement were not shown to agree, and no call that '
                             'separates them was found: do they mean the same?')
    q, = asked(two('NO-CONTEXT'))              # (a bounded comparison) nothing meets the rest under both readings
    assert q['kind'] == 'undecided' and q['question'].startswith(
        'the two readings of this requirement were not shown to agree: no behavior meets the other requirements')
    q, = asked(two('UNKNOWN', CALL))           # one direction is undecided, the other has a call: a difference
    assert (q['kind'], q['calls']) == ('readings', CALL)
    q, = asked(two('A-WEAKER'))                # a comparison that ended (of an object: it prints no call)
    assert q['kind'] == 'readings' and q['question'].startswith('the two readings of this requirement disagree (')

    # the answers the readers shared
    q, = asked(depends=third(R_RET_1=('INCOMPARABLE', CALL), R_EX_1=('A-STRONGER', None)))
    assert (q['kind'], q['reqs'], q['calls']) == ('depends', ['R-EX-1', 'R-RET-1'], CALL) and 'undecided' not in q
    assert q['question'] == SHARED + ('read the other way, these requirements mean something else: '
                                      'are those answers meant?')
    q, = asked(depends=third(R_RET_1=('UNKNOWN', CALL), R_EX_1=('UNKNOWN', None)))
    assert (q['kind'], q['reqs'], q['calls'], q['undecided']) == ('depends', ['R-EX-1', 'R-RET-1'], CALL, ['R-EX-1'])
    assert q['question'] == SHARED + ('read the other way, R-RET-1 means something else; whether R-EX-1 does was '
                                      'not shown either way: are those answers meant?')
    q, = asked(depends=third(R_RET_1=('UNKNOWN', None), R_EX_1=('UNKNOWN', None)))
    assert (q['kind'], q['reqs'], q['calls']) == ('undecided', ['R-EX-1', 'R-RET-1'], []) and 'undecided' not in q
    assert q['question'] == SHARED + ('whether these requirements mean something else when read the other way was '
                                      'not shown either way: are those answers meant?')


def test_with_code_a_requirement_waits_for_the_shared_answers_only_where_the_other_reading_may_reject(small):
    """A third reader takes the other reading of what both readers shared.
    Before any code every requirement it reads another way waits for those
    answers.  With code the question is whether the certificate stands under
    the other answer.  It does where the other reading accepts every run
    that each reader accepts on the requirement, whatever the run does on
    the other requirements: that direction is closed without context and in
    context, and the requirement then does not wait.  Closed in context
    only, the direction says nothing about a run that breaks another rule of
    the other reading, and the requirement waits.  It waits as well where a
    call was found, the search of that direction did not end, there was
    nothing to compare on, a step the rule rests on failed, or the review
    was written before both closures were kept per reader.  A requirement
    that the review does not certify stays in the question."""
    S = Session(small, sets=['one', 'two'])
    a_b, b_a = 'witness_a_not_b', 'witness_b_not_a'
    answers = [{'req': 'R-STACK-1', 'phrase': 'Discounts stack', 'taken': 1}]

    def drawn(depends, code=True, verify=PASSED, failed=()):
        out = {'sets': ['one', 'two'], 'readings': {}, 'depends': depends, 'variant_answers': answers,
               'prompt': {s: {'conflicts': {'conflicts': []}, 'open': {'open': {}}} for s in ('one', 'two')},
               'code': {'calls': 0, 'verify': {s: json.loads(json.dumps(verify)) for s in ('one', 'two')}} if code else None,
               'failed': [dict(f) for f in failed]}
        out['certified'], out['queue'] = RV.verdicts(S, out)
        asked = [(q['kind'], q['reqs'], q['calls']) for q in out['queue'] if q['kind'] in ('depends', 'undecided')]
        return sorted(out['certified']), asked, RV.report(S, out)

    def third(w=None, **by):
        """Per reader: (relation in context, closed in context[, closed without context[, bound]])."""
        def one(rel, closed, alone=None, bound=None):
            return {'relation': rel, 'closed': list(closed), 'closed_alone': list(closed if alone is None else alone),
                    **({'bound': bound} if bound else {})}
        return {'relation': next(iter(by.values()))[0], 'peers': list(by), 'witness': w,
                'by': {p: one(*found) for p, found in by.items()}}

    loose = ('the other reading accepts every run that both readers accept, whatever the run does on the other '
             'requirements')
    all_wait = 'the requirements on which its reading differs depend on these answers:'
    assert drawn({})[:2] == (['R-EX-1', 'R-RET-1'], [])
    # the other reading only accepts more, under both readers, with and without context: the certificate stands
    more = {'R-RET-1': third(CALL, one=('A-STRONGER', [a_b]), two=('A-STRONGER', [a_b]))}
    certified, asked, text = drawn(more)
    assert certified == ['R-EX-1', 'R-RET-1'] and asked == []
    assert f'On R-RET-1 {loose}: what is certified of this requirement stands under either answer, and it does ' \
        'not wait for these answers.' in text and '## Shared answers' in text
    assert 'no requirement on which its reading differs waits for these answers:' in text and all_wait not in text
    # before any code the same finding leaves the meaning of the requirement open
    settled, asked, text = drawn(more, code=False)
    assert settled == ['R-EX-1'] and asked == [('depends', ['R-RET-1'], CALL)] and loose not in text
    assert all_wait in text
    # closed in context only: a run may meet the readers and break another rule of the other reading
    for alone in ([], [b_a]):
        found = third(CALL, one=('A-STRONGER', [a_b], alone), two=('A-STRONGER', [a_b]))
        certified, asked, text = drawn({'R-RET-1': found})
        assert certified == ['R-EX-1'] and asked == [('depends', ['R-RET-1'], CALL)], alone
        assert loose not in text and all_wait in text
    # closed without context only: the comparison in context did not show it (it did not end, or had no context)
    certified, asked, text = drawn({'R-RET-1': third(CALL, one=('UNKNOWN', [], [a_b]))})
    assert certified == ['R-EX-1'] and asked == [('depends', ['R-RET-1'], CALL)] and loose not in text
    # one reader is enough to hold it: the other reading rejects a run that reader accepts
    for found in (third(CALL, one=('A-STRONGER', [a_b]), two=('A-WEAKER', [b_a])),
                  third(CALL, one=('INCOMPARABLE', [])),
                  third(CALL, two=('UNKNOWN', [b_a]))):         # that direction did not end
        certified, asked, text = drawn({'R-RET-1': found})
        assert certified == ['R-EX-1'] and asked == [('depends', ['R-RET-1'], CALL)], found
        assert loose not in text
    # nothing was shown either way: the search did not end, or there was nothing to compare on
    for found in (third(None, one=('UNKNOWN', [])), third(None, one=('NO-CONTEXT', []))):
        certified, asked, _ = drawn({'R-RET-1': found})
        assert certified == ['R-EX-1'] and asked == [('undecided', ['R-RET-1'], [])], found
    certified, asked, _ = drawn({'R-RET-1': third(None, one=('NO-CONTEXT', []), two=('A-WEAKER', [b_a]))})
    assert certified == ['R-EX-1'] and asked == [('depends', ['R-RET-1'], [])]      # one reader shows a difference
    # an undecided comparison whose open direction is the other one does not hold it: the call the other
    # reading alone accepts was not shown, or was not found in time, and no run of a reader is rejected
    certified, asked, text = drawn({'R-RET-1': third(None, one=('UNKNOWN', [a_b]), two=('A-STRONGER', [a_b]))})
    assert certified == ['R-EX-1', 'R-RET-1'] and asked == [] and f'On R-RET-1 {loose}' in text
    # each requirement by what was found for it: the question names those that wait, and shows a call of theirs
    certified, asked, text = drawn({'R-RET-1': third(CALL, one=('A-STRONGER', [a_b])),
                                    'R-EX-1': third(None, one=('A-WEAKER', [b_a]), two=('A-WEAKER', [b_a]))})
    assert certified == ['R-RET-1'] and asked == [('depends', ['R-EX-1'], [])]
    assert f'On R-RET-1 {loose}' in text and 'R-EX-1 the other' not in text
    assert 'of the requirements on which its reading differs, R-EX-1 depends on these answers:' in text
    certified, asked, text = drawn({'R-RET-1': third(CALL, one=('A-STRONGER', [a_b])),
                                    'R-EX-1': third(None, two=('A-STRONGER', [a_b]))})
    assert certified == ['R-EX-1', 'R-RET-1'] and asked == []
    assert f'On R-EX-1, R-RET-1 {loose}: what is certified of these requirements stands under either answer, ' \
        'and they do not wait for these answers.' in text
    # a search that covered less than every run is named with its bound
    bounded = third(CALL, one=('A-STRONGER', [a_b], None, 'the first 6 cycles of a bounded check of 8'),
                    two=('A-STRONGER', [a_b], None, 'runs of 2 calls'))
    certified, asked, text = drawn({'R-RET-1': bounded})
    assert certified == ['R-EX-1', 'R-RET-1'] and asked == []
    assert f'On R-RET-1 {loose} (searched within runs of 2 calls and the first 6 cycles of a bounded check of 8): ' \
        'what is certified of this requirement stands' in text
    # a bounded check shows a disagreement `lookahead` cycles after it happens, and is named before a horizon
    assert RV._bound({'engine': 'bmc', 'depth': 8, 'lookahead': 2}, None) == 'the first 6 cycles of a bounded check of 8'
    assert RV._bound({'exact': False, 'k': 2}, {'engine': 'bmc', 'depth': 10, 'lookahead': 6}) == \
        'the first 4 cycles of a bounded check of 10'
    assert RV._bound({'engine': 'bmc', 'depth': 8}) == 'a bounded check of 8 cycles'
    assert RV._bound({'exact': True, 'k': 3}, {'exact': False, 'k': 2}) == 'runs of 2 calls'
    assert RV._bound({'exact': False, 'k': 1}) == 'runs of 1 call'
    assert RV._bound({'exact': True, 'k': 3}, None, {}) is None
    # the rule protects a certificate: a requirement the code breaks stays in the question, and is not named
    broken = {**PASSED, 'T-P': {'req': 'R-RET-1', 'status': 'FAIL'}}
    certified, asked, text = drawn(more, verify=broken)
    assert certified == ['R-EX-1'] and asked == [('depends', ['R-RET-1'], CALL)]
    assert loose not in text and all_wait in text
    # a step the rule rests on did not end: every requirement waits
    for step, rests in (('the code on the scope', 'all'), ('the comparison of one and variant, in context', 'all'),
                        ('the comparison of two and variant, in context', 'all')):
        lost = [{'step': step, 'why': 'stopped', 'rests': rests, 'reading': None}]
        certified, asked, text = drawn(more, failed=lost)
        assert certified == [] and asked == [('depends', ['R-RET-1'], CALL)] and loose not in text, step
        assert RV.waiting({'code': {}, 'sets': ['one', 'two'], 'depends': more, 'failed': lost}) == (['R-RET-1'], [])
    # a review written before both closures were kept per reader: every requirement waits, as it did
    old = {'R-RET-1': {'relation': 'A-STRONGER', 'peers': ['one', 'two'], 'witness': CALL}}
    half = {'R-RET-1': {**old['R-RET-1'], 'by': {'one': {'relation': 'A-STRONGER', 'closed': [a_b]}}}}
    none = {'R-RET-1': {**old['R-RET-1'], 'by': {}}}           # and one that names no reader
    for stored in (old, half, none):
        certified, asked, text = drawn(stored)
        assert certified == ['R-EX-1'] and asked == [('depends', ['R-RET-1'], CALL)] and loose not in text
        assert RV.waiting({'code': {}, 'depends': stored}) == (['R-RET-1'], [])
    assert RV.waiting({'code': {}, 'depends': more}) == ([], ['R-RET-1'])
    assert RV.waiting({'code': None, 'depends': more}) == (['R-RET-1'], []) and RV.waiting({'code': {}}) == ([], [])
    # what is released is drawn from the certificates of the same review
    assert RV.released({'code': {}, 'depends': more, 'certified': ['R-RET-1']}) == ['R-RET-1']
    assert RV.released({'code': {}, 'depends': more, 'certified': ['R-RET-1']}, certified=[]) == []
    assert RV.released({'code': {}, 'depends': more, 'certified': []}) == []


# ---------------------------------------------------------------- the watched check of a bundle, with its review
def test_a_bundle_with_readings_is_checked_and_its_review_written(tmp_path, monkeypatch):
    """What `fcp review` does after its agents, for a bundle that has its
    readings already: the studies call it for bundles checked again."""
    b = copy(tmp_path, 'agent_a', 'agent_b')
    out = tmp_path / 'out'
    out.mkdir()
    monkeypatch.setattr(RV, 'WORKER', STUBBED)
    monkeypatch.setenv('FCP_TEST_MODE', 'ok')
    res = RV.checked(b, None, ['agent_a', 'agent_b'], str(out), quiet, jobs=2, step_seconds=60)
    assert res['failed'] == [] and 'unchecked' not in res and 'R-RET-1' in res['certified']
    assert sorted(os.listdir(out)) == ['review.json', 'review.md']
    with open(out / 'review.json') as f:
        assert json.load(f)['certified'] == res['certified']
    assert (out / 'review.md').read_text() == RV.report(Session(b, sets=['agent_a', 'agent_b']), res)
    monkeypatch.setenv('FCP_TEST_MODE', 'raise')
    res = RV.checked(b, None, ['agent_a', 'agent_b'], str(out), quiet, jobs=2, step_seconds=60)
    assert [x['step'] for x in res['failed']] == ['the comparison of agent_a and agent_b, in context']
    assert res['trace'] == 'check_errors.txt' and 'ValueError' in (out / 'check_errors.txt').read_text()
    assert sorted(os.listdir(out)) == ['check_errors.txt', 'review.json', 'review.md']
