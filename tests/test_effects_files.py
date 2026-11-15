"""Effects through objects the code makes itself: files from open (with
os.fsync, os.replace, os.remove patched and a run's own view of which files
exist), and a socket from socket.create_connection (corpus/code_save, and a
small socket client built here)."""
import os
import shutil
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'corpus', 'code_save')
sys.path.insert(0, ROOT)

from fcp import effects as FX  # noqa: E402
from fcp import software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402


@pytest.fixture(scope='module')
def save():
    S = Session(B, sets=['gold'])
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    return S, fn, ifc, FX.scope(S, fn, ifc)


def fails(S, fn, ifc, runs, src):
    res = FX.run(fn, ifc, src, runs)
    out = FX.verify(S, 'gold', fn, ifc, src, runs, res)
    return {k: v for k, v in out.items() if v['status'] == 'FAIL'}


def test_reference_and_planted_bugs(save):
    """The reference keeps the temporary file when os.replace fails (rule 7)
    and so breaks rule 6 there, and only there; every planted bug breaks
    something more; the refactoring breaks nothing more."""
    import importlib.util
    S, fn, ifc, runs = save
    spec = importlib.util.spec_from_file_location('save_build', os.path.join(B, 'build.py'))
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    paths = build.materialize()
    ref = fails(S, fn, ifc, runs, os.path.join(B, 'impl', 'ref.py'))
    assert set(ref) == {'G-CLEAN'}
    assert ref['G-CLEAN']['call'] == 'save_balance(0) with answers ["fail"]'
    assert ref['G-CLEAN']['conversation'] == [
        "f1 = open('balance.txt.tmp', 'w')", "f1.write('0')", 'f1.flush()', 'os.fsync(f1.fileno())',
        'f1.close()', "os.replace('balance.txt.tmp', 'balance.txt') -> \"fail\"", 'returns False']
    for b in build.bugs():
        got = fails(S, fn, ifc, runs, paths[b['id']])
        if 'refactoring' in b['desc']:
            assert set(got) == set(ref), b['id']
        else:
            assert set(got) - set(ref), b['id']
    # removing in `finally` after the move: the file is gone, as on a disk
    c5 = fails(S, fn, ifc, runs, paths['C5'])
    assert "os.remove('balance.txt.tmp') -> FileNotFoundError" in c5['G-RET']['conversation']


def test_the_run_sees_its_own_files(save, tmp_path):
    """os.path.exists answers from what the run did; pathlib goes through the
    same stand-ins; a call on a closed file raises, as on a real one."""
    S, fn, ifc, runs = save
    src = tmp_path / 'impl.py'
    src.write_text(textwrap.dedent('''
        import os
        from pathlib import Path

        def save_balance(cents):
            if cents == 7:                      # a write after close
                f = open('balance.txt.tmp', 'w')
                f.close()
                f.write('7')
            Path('balance.txt.tmp').write_text(str(cents))
            try:
                os.replace('balance.txt.tmp', 'balance.txt')
            except OSError:
                pass
            if os.path.exists('balance.txt.tmp'):
                os.remove('balance.txt.tmp')
            return os.path.exists('balance.txt') and not Path('balance.txt.tmp').exists()
    '''))
    calls = [((5,), ()), ((5,), (1,)), ((7,), ())]
    res = FX.run(fn, ifc, str(src), calls)
    text = [FX.conversation(fn, ifc, calls, res, i) for i in range(3)]
    assert text[0] == ["f1 = open('balance.txt.tmp', 'w')", "f1.write('5')", 'f1.close()',
                       "os.replace('balance.txt.tmp', 'balance.txt') -> \"ok\"", 'returns True']
    assert text[1][-2:] == ["os.remove('balance.txt.tmp')", 'returns True']
    # a real closed file raises ValueError too, which this prompt's outcome codes as 1
    assert text[2][2] == "f1.write('7') -> ValueError" and res[2]['code'] == 1
    cols, where = FX.trace(fn, ifc, calls, res)
    assert cols['of'][1:4] == [1, 1, 1] and cols['o_mode'][1] == 2 and cols['w_value'][2] == 5


def test_conflict_before_code(save):
    """No conversation meets the rules when os.replace fails: keeping the
    file breaks rule 6, removing it breaks rule 7, and a retry that succeeds
    must return True under rule 5 and False under rule 7."""
    S, fn, ifc, _ = save
    r = FX.conflicts(S, 'gold', fn, ifc, limit=1)
    assert r['conflicts'], r
    c = r['conflicts'][0]
    assert c['script'] == [1] and {'R-CLEAN-1', 'R-KEEP-1'} <= set(c['reqs'])
    assert all({'G-CLEAN', 'G-KEEP'} <= set(mu) for mu in c['muses'])


def test_design_errors(save, tmp_path):
    d = tmp_path / 'bad'
    shutil.copytree(B, d)
    text = (d / 'design.yaml').read_text()
    (d / 'design.yaml').write_text(text.replace('via: open, args: [{name: s', 'via: fsync, args: [{name: s'))
    with pytest.raises(SW.SoftwareError):
        FX.interface(Session(str(d), sets=['gold']), SW.function(Session(str(d), sets=['gold'])))


PING_DESIGN = '''
fcp: '0.1'
design: ping
docs:
- {id: SPEC, path: spec.md}
interface:
  clock: clk
  reset: {name: rst_n, active_low: true, synchronous: true}
  signals:
  - {name: clk, dir: in, width: 1}
  - {name: rst_n, dir: in, width: 1}
  - {name: tries, dir: in, width: 3}
  - {name: answer, dir: in, width: 2}
  - {name: phase, dir: out, width: 1}
  - {name: op, dir: out, width: 3}
  - {name: sock, dir: out, width: 2}
  - {name: c_addr, dir: out, width: 2}
  - {name: s_msg, dir: out, width: 2}
  - {name: outcome, dir: out, width: 2}
  - {name: result, dir: out, width: 1}
environment: {initial_reset: true, reset_anytime: true, bmc_depth: 8, cover_depth: 8}
frame:
- {id: F-END, req: R-1, expr: 'prev(phase) -> phase && stable(outcome) && stable(result)'}
function:
  name: ping
  args: [{name: tries, signal: tries, type: int}]
  interface:
    position: null
    methods:
    - name: connect
      op: 1
      patch: socket.create_connection
      handle: true
      var: s
      args: [{name: address, signal: c_addr, enum: [[ledger, 7000]]}]
      answers: [ok, refused]
      raises: {refused: ConnectionRefusedError}
    - {name: sendall, op: 2, via: connect, args: [{name: data, signal: s_msg, enum: [PING]}]}
    - {name: recv, op: 3, via: connect, answers: [PONG, ''], bytes: true}
    - {name: close, op: 4, via: connect}
    signals: {phase: phase, op: op, answer: answer, handle: sock}
    max_calls: 8
  returns: {signal: result, type: bool}
  outcome: {signal: outcome, raises: [ValueError]}
  scope:
    script: {length: 3, random: 0}
    tries: {values: [1, 2]}
'''
PING_REQS = '''
fcp: '0.1'
design: ping
origin: {kind: human, id: gold, role: decomposer}
requirements:
- {id: R-1, doc: SPEC, lines: [1], quote: 'ping the ledger', text: t, kind: guarantee}
'''
PING_GOLD = '''
fcp: '0.1'
set: gold
origin: {kind: human, role: formalizer, id: gold}
properties:
- {id: G-1, req: R-1, pattern: implies, args: {trigger: 'phase', cond: 'outcome == 0'}}
'''


def test_socket_objects(tmp_path):
    """A socket the code opens itself: each connection is an object, its
    calls are recorded on it, answers come back as bytes, and leaving the
    `with` block closes it."""
    d = tmp_path / 'ping'
    (d / 'formal').mkdir(parents=True)
    (d / 'design.yaml').write_text(PING_DESIGN)
    (d / 'requirements.yaml').write_text(PING_REQS)
    (d / 'spec.md').write_text('ping the ledger\n')
    (d / 'formal' / 'gold.yaml').write_text(PING_GOLD)
    S = Session(str(d), sets=['gold'])
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    src = tmp_path / 'ping.py'
    src.write_text(textwrap.dedent('''
        import socket

        def ping(tries):
            for _ in range(tries):
                try:
                    with socket.create_connection(('ledger', 7000)) as s:
                        s.sendall(b'PING')
                        if s.recv(16) == b'PONG':
                            return True
                except ConnectionRefusedError:
                    pass
            return False
    '''))
    a = {n: i for i, n in enumerate(ifc.answers)}
    calls = [((2,), (a['refused'], a['ok'], a['PONG'])), ((1,), (a['ok'], a['']))]
    res = FX.run(fn, ifc, str(src), calls)
    assert FX.conversation(fn, ifc, calls, res, 0) == [
        "socket.create_connection(('ledger', 7000)) -> \"refused\"",
        "s1 = socket.create_connection(('ledger', 7000))", "s1.sendall(b'PING')", 's1.recv() -> "PONG"',
        's1.close()', 'returns True']
    assert FX.conversation(fn, ifc, calls, res, 1)[-2:] == ['s1.close()', 'returns False']
    cols, _ = FX.trace(fn, ifc, calls, res)
    assert cols['sock'][1:7] == [0, 1, 1, 1, 1, 0] and cols['c_addr'][1:3] == [1, 1] and cols['s_msg'][3] == 1
