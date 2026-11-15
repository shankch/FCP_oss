"""Tests for the confinement of fcp review's agents: the permissions on the
command line, the launcher that works on its own workspace only, and the
sandbox whose file system holds the workspace and nothing of the home."""
import json
import os
import shutil
import subprocess
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fcp import agents as AG, cli, review as R  # noqa: E402


def _args(cmd, bundle, **kw):
    return types.SimpleNamespace(cmd=cmd, bundle=bundle, **kw)


def _bwrap_works():
    b = R.bwrap()
    if not b:
        return False
    try:
        return subprocess.run([b, '--ro-bind', '/', '/', 'true'], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


needs_bwrap = pytest.mark.skipif(not _bwrap_works(), reason='no working bubblewrap on this machine')


def test_agent_command_names_what_an_agent_may_do():
    c = R.agent_command('PROMPT', 'sonnet')
    assert c[c.index('--tools') + 1] == 'Read,Write,Edit,Bash'
    assert '--strict-mcp-config' in c and c[c.index('--permission-mode') + 1] == 'acceptEdits'
    allowed = c[c.index('--allowedTools') + 1:c.index('--disallowedTools')]
    assert allowed == [f'Bash({AG.FCP}:*)', 'Bash(ls:*)', 'Bash(cat:*)']
    denied = c[c.index('--disallowedTools') + 1:]
    assert {'Bash(ps:*)', 'Bash(xargs:*)', 'Bash(tree:*)'} <= set(denied)


def test_launcher_is_free_outside_a_review(monkeypatch):
    monkeypatch.delenv('FCP_AGENT_WS', raising=False)
    assert cli.agent_refusal(_args('check', '/anywhere')) is None


def test_launcher_works_on_the_agents_workspace_only(monkeypatch, tmp_path):
    ws, other = tmp_path / 'ws_agent_a', tmp_path / 'ws_agent_b'
    ws.mkdir()
    other.mkdir()
    monkeypatch.setenv('FCP_AGENT_WS', str(ws))
    assert cli.agent_refusal(_args('lint', str(ws))) is None
    assert cli.agent_refusal(_args('explain', str(ws / 'formal'))) is None
    assert 'not available to an agent' in cli.agent_refusal(_args('check', str(ws)))
    assert 'not available to an agent' in cli.agent_refusal(_args('review', str(ws)))
    for path in (other, ws / '..' / 'ws_agent_b', tmp_path):
        assert 'outside the workspace' in cli.agent_refusal(_args('lint', str(path)))
    (ws / 'link').symlink_to(other)                      # a link out of the workspace is followed
    assert 'outside the workspace' in cli.agent_refusal(_args('lint', str(ws / 'link')))
    assert 'outside the workspace' in cli.agent_refusal(_args('anchor', str(ws), draft=str(other / 'd.yaml')))
    assert 'outside the workspace' in cli.agent_refusal(_args('explain', str(ws), out=str(tmp_path / 'x.md')))


def test_launcher_refuses_on_the_command_line(tmp_path):
    ws = tmp_path / 'ws_agent_a'
    ws.mkdir()
    p = subprocess.run([AG.FCP, 'lint', str(tmp_path)], capture_output=True, text=True,
                       env=dict(os.environ, FCP_AGENT_WS=str(ws)))
    assert p.returncode == 2 and 'outside the workspace' in p.stderr


def test_sandbox_can_be_switched_off(monkeypatch, tmp_path):
    monkeypatch.setenv('FCP_AGENT_SANDBOX', '0')
    assert R.sandbox(str(tmp_path)) is None


def _home(tmp_path):
    """A home with a Claude directory, a key, and two workspaces of one review."""
    home = tmp_path / 'home'
    conf = home / '.claude'
    for d in ('projects/p1', 'plugins/x', 'skills/s'):
        (conf / d).mkdir(parents=True)
    (conf / 'projects' / 'p1' / 'old.jsonl').write_text('PAST-SESSION')
    (conf / 'plugins' / 'x' / 'plugin.json').write_text('{}')
    (conf / 'history.jsonl').write_text('PAST-PROMPT\n')
    (conf / 'settings.json').write_text('{}')
    (conf / '.credentials.json').write_text('{"login": "fake"}')
    (home / '.claude.json').write_text('{"n": 1}')
    (home / '.ssh').mkdir()
    (home / '.ssh' / 'id').write_text('SECRET-KEY')
    out = tmp_path / 'out'
    ws, other = out / 'ws_agent_a', out / 'ws_agent_b'
    ws.mkdir(parents=True)
    other.mkdir()
    (ws / 'spec.md').write_text('spec')
    (other / 'secret.txt').write_text('OTHER-READER')
    return home, conf, out, ws


@needs_bwrap
def test_sandbox_copies_nothing_into_the_real_claude_directory(monkeypatch, tmp_path):
    home, conf, out, ws = _home(tmp_path)
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.delenv('FCP_AGENT_SANDBOX', raising=False)
    a, fds = R.sandbox(str(ws))
    for fd in fds:
        os.close(fd)
    three = list(zip(a, a[1:], a[2:]))
    assert ('--tmpfs', str(home)) in zip(a, a[1:])
    assert ('--bind', str(conf), str(conf)) in three
    assert ('--bind', str(out / 'sessions' / 'ws_agent_a'), str(conf / 'projects')) in three
    assert ('--dev-bind', '/dev/null', str(conf / 'history.jsonl')) in three
    assert ('--ro-bind', str(conf / 'settings.json'), str(conf / 'settings.json')) in three
    assert a[-2:] == ['--chdir', str(ws)]
    for i, x in enumerate(a):                            # --file writes its destination: never inside ~/.claude
        if x == '--file':
            assert a[i + 2] == str(home / '.claude.json')


SCRIPT = r'''
echo "home: $(ls -A ~ | sort | tr '\n' ' ')"
echo "ssh: $(cat ~/.ssh/id 2>/dev/null || echo absent)"
echo "out: $(ls -A .. | sort | tr '\n' ' ')"
echo "other: $(cat ../ws_agent_b/secret.txt 2>/dev/null || echo absent)"
echo "spec: $(cat spec.md)"
echo "history: $(wc -c < ~/.claude/history.jsonl)"
echo "projects: $(ls -A ~/.claude/projects | wc -l)"
echo "plugins: $(ls -A ~/.claude/plugins | wc -l)"
echo "login: $(cat ~/.claude/.credentials.json)"
echo "config: $(cat ~/.claude.json)"
echo "tmp: $(ls -A /tmp | tr '\n' ' ')"
echo "pids: $(ls /proc | grep -c '^[0-9]')"
(echo x > ~/.claude/settings.json) 2>/dev/null && echo "settings: written" || echo "settings: fixed"
(echo x > /usr/fcp_probe) 2>/dev/null && echo "usr: written" || echo "usr: fixed"
echo '{"n": 2}' > ~/.claude.json
echo note > note.txt
echo session > ~/.claude/projects/s.jsonl
'''


@needs_bwrap
def test_sandbox_holds_the_workspace_and_nothing_of_the_home(monkeypatch, tmp_path):
    home, conf, out, ws = _home(tmp_path)
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.delenv('FCP_AGENT_SANDBOX', raising=False)
    a, fds = R.sandbox(str(ws))
    try:
        p = subprocess.run(a + ['/bin/sh', '-c', SCRIPT], capture_output=True, text=True, pass_fds=fds, timeout=120)
    finally:
        for fd in fds:
            os.close(fd)
    assert p.returncode == 0, p.stderr
    said = dict(line.split(': ', 1) for line in p.stdout.splitlines() if ': ' in line)
    assert said['home'].split() == ['.claude', '.claude.json']
    assert said['ssh'] == 'absent' and said['other'] == 'absent'
    assert said['out'].split() == ['ws_agent_a']
    assert said['spec'] == 'spec'
    assert said['history'] == '0' and said['projects'] == '0' and said['plugins'] == '0'
    mine = os.path.relpath(str(tmp_path), '/tmp').split(os.sep)[0]      # /tmp is private: at most the way to this test
    assert set(said.get('tmp', '').split()) <= {mine}
    assert said['login'] == '{"login": "fake"}' and said['config'] == '{"n": 1}'
    assert int(said['pids']) < 10
    assert said['settings'] == 'fixed' and said['usr'] == 'fixed'
    # outside, afterwards: the workspace and the session records were written, the home was not
    assert (ws / 'note.txt').read_text() == 'note\n'
    assert (out / 'sessions' / 'ws_agent_a' / 's.jsonl').read_text() == 'session\n'
    assert (conf / 'history.jsonl').read_text() == 'PAST-PROMPT\n'
    assert (conf / 'settings.json').read_text() == '{}'
    assert (home / '.claude.json').read_text() == '{"n": 1}'
    assert sorted(os.listdir(conf / 'projects')) == ['p1']


def _broken_bwrap(tmp_path):
    """A bubblewrap that does not start, as a tool suite may put one on the PATH."""
    d = tmp_path / 'suite'
    d.mkdir()
    fake = d / 'bwrap'
    fake.write_text('#!/bin/sh\necho "No permissions to create a new namespace" >&2\nexit 1\n')
    fake.chmod(0o755)
    return fake


def _claude_stub(calls):
    def run(cmd, **kw):
        calls.append(list(cmd))
        return types.SimpleNamespace(returncode=0, stderr='', stdout=json.dumps(
            {'result': 'done', 'total_cost_usd': 0.01, 'num_turns': 1, 'is_error': False}))
    return run


@needs_bwrap
def test_bubblewrap_is_the_systems_not_the_first_on_the_path(monkeypatch, tmp_path):
    if not any(os.access(b, os.X_OK) for b in ('/usr/bin/bwrap', '/bin/bwrap', '/usr/local/bin/bwrap')):
        pytest.skip('bubblewrap is not in a system directory here')
    home, conf, out, ws = _home(tmp_path)
    fake = _broken_bwrap(tmp_path)
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('PATH', f'{fake.parent}{os.pathsep}{os.environ["PATH"]}')
    monkeypatch.delenv('FCP_AGENT_SANDBOX', raising=False)
    monkeypatch.setattr(R, '_FAULT', {})
    assert shutil.which('bwrap') == str(fake)
    assert R.bwrap() != str(fake)
    assert R.sandbox_fault() is None


def test_a_sandbox_that_does_not_start_is_said_and_never_passed_over(monkeypatch, tmp_path):
    home, conf, out, ws = _home(tmp_path)
    fake = _broken_bwrap(tmp_path)
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.delenv('FCP_AGENT_SANDBOX', raising=False)
    monkeypatch.setattr(R, 'bwrap', lambda: str(fake))
    monkeypatch.setattr(R, '_FAULT', {})
    assert 'No permissions' in R.sandbox_fault()             # found once, by starting it
    calls = []
    monkeypatch.setattr(R.subprocess, 'run', _claude_stub(calls))
    monkeypatch.setenv('FCP_AGENT_SANDBOX', '1')             # a sandbox or no run at all
    with pytest.raises(RuntimeError, match='none starts'):
        R.run_agent('PROMPT', str(ws), 'sonnet')
    assert calls == []
    monkeypatch.delenv('FCP_AGENT_SANDBOX')                  # not required: the run says that it was not sandboxed
    r = R.run_agent('PROMPT', str(ws), 'sonnet')
    assert r == 'done' and r.meta['sandbox'] is False and 'No permissions' in r.meta['sandbox_error']
    assert len(calls) == 1 and calls[0][0] == R.CLAUDE
    monkeypatch.setenv('FCP_AGENT_SANDBOX', '0')
    r = R.run_agent('PROMPT', str(ws), 'sonnet')
    assert r.meta['sandbox'] is False and 'switched off' in r.meta['sandbox_error']


@needs_bwrap
def test_an_agent_is_started_inside_the_sandbox(monkeypatch, tmp_path):
    home, conf, out, ws = _home(tmp_path)
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('FCP_AGENT_SANDBOX', '1')
    monkeypatch.setattr(R, '_FAULT', {})
    assert R.sandbox_fault() is None
    calls = []
    monkeypatch.setattr(R.subprocess, 'run', _claude_stub(calls))
    r = R.run_agent('PROMPT', str(ws), 'sonnet')
    assert r == 'done' and r.meta['sandbox'] is True and 'sandbox_error' not in r.meta
    cmd, claude = calls[0], os.path.realpath(R.CLAUDE)
    assert cmd[0] == R.bwrap() and cmd[cmd.index('--chdir') + 1] == str(ws)
    i = len(cmd) - 1 - cmd[::-1].index(claude)               # after the prefix, which also binds the program
    assert cmd[i + 1:i + 3] == ['-p', 'PROMPT']

