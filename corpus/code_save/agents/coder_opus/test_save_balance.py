import builtins
import os
import sys

import pytest

import save_balance as sb
from save_balance import save_balance

BAL = "balance.txt"
TMP = "balance.txt.tmp"


# --- helpers -----------------------------------------------------------------

# Every open of a path, by any means (builtin open, os.open, ...), raises the
# "open" audit event.  The hook cannot be removed, so it only records while a
# test has switched it on.
_opened = None


def _audit(event, args):
    if _opened is not None and event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        _opened.append(os.path.abspath(os.fsdecode(args[0])))


sys.addaudithook(_audit)


@pytest.fixture
def opened_paths():
    global _opened
    _opened = []
    try:
        yield _opened
    finally:
        _opened = None


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def read(path):
    with open(path, "rb") as f:
        return f.read()


def write(path, data):
    with open(path, "wb") as f:
        f.write(data)


class SpyFile:
    """Wraps a file object, records calls, and can fail on demand."""

    def __init__(self, f, events, fail_on=None):
        self._f = f
        self._events = events
        self._fail_on = fail_on

    def _maybe_fail(self, name):
        if self._fail_on == name:
            raise OSError(f"injected {name} failure")

    def write(self, s):
        self._events.append(("write", s))
        self._maybe_fail("write")
        return self._f.write(s)

    def flush(self):
        self._events.append(("flush",))
        return self._f.flush()

    def fileno(self):
        return self._f.fileno()

    def close(self):
        self._events.append(("close",))
        self._f.close()
        self._maybe_fail("close")

    @property
    def closed(self):
        return self._f.closed


def install_spies(monkeypatch, fail_on=None, fsync_check=None, replace_check=None):
    events = []
    files = []
    real_open = builtins.open
    real_fsync = os.fsync
    real_replace = os.replace

    def spy_open(path, mode="r", *args, **kwargs):
        events.append(("open", os.fspath(path), mode))
        if fail_on == "open":
            raise PermissionError("injected open failure")
        spy = SpyFile(real_open(path, mode, *args, **kwargs), events, fail_on)
        files.append(spy)
        return spy

    def spy_fsync(fd):
        events.append(("fsync", fd))
        if fsync_check:
            fsync_check(fd, files)
        if fail_on == "fsync":
            raise OSError("injected fsync failure")
        if fail_on == "fsync-interrupt":
            raise KeyboardInterrupt
        return real_fsync(fd)

    def spy_replace(src, dst, **kwargs):
        events.append(("replace", os.fspath(src), os.fspath(dst)))
        if replace_check:
            replace_check(src, dst, files)
        if fail_on == "replace":
            raise OSError("injected replace failure")
        return real_replace(src, dst, **kwargs)

    monkeypatch.setattr(sb, "open", spy_open, raising=False)
    monkeypatch.setattr(os, "fsync", spy_fsync)
    monkeypatch.setattr(os, "replace", spy_replace)
    return events, files


# --- successful saves ----------------------------------------------------------

def test_saves_digits_and_returns_true(workdir):
    assert save_balance(1250) is True
    assert read(BAL) == b"1250"
    assert sorted(os.listdir(workdir)) == [BAL]


@pytest.mark.parametrize("cents, digits", [(0, b"0"), (1, b"1"), (100_000_000, b"100000000")])
def test_boundaries_are_accepted(workdir, cents, digits):
    assert save_balance(cents) is True
    assert read(BAL) == digits
    assert not os.path.exists(TMP)


def test_overwrites_previous_balance(workdir):
    write(BAL, b"99999")
    assert save_balance(7) is True
    assert read(BAL) == b"7"
    assert not os.path.exists(TMP)


def test_uses_current_directory_at_call_time(tmp_path, monkeypatch):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    monkeypatch.chdir(a)
    assert save_balance(11) is True
    monkeypatch.chdir(b)
    assert save_balance(22) is True
    assert read(a / BAL) == b"11"
    assert read(b / BAL) == b"22"


def test_example_sequence(workdir, monkeypatch):
    """open tmp, write digits, fsync it, close it, os.replace it over balance.txt."""

    def fsync_check(fd, files):
        # fsync is on the temp file, while it is still open, after its data is flushed.
        assert os.path.samestat(os.fstat(fd), os.stat(TMP))
        assert not files[0].closed
        assert read(TMP) == b"1250"

    def replace_check(src, dst, files):
        # the temp file is closed before it is moved.
        assert all(f.closed for f in files)

    events, _ = install_spies(monkeypatch, fsync_check=fsync_check, replace_check=replace_check)
    assert save_balance(1250) is True
    key = [e[0] if e[0] != "write" else e for e in events if e[0] != "flush"]
    assert key == ["open", ("write", "1250"), "fsync", "close", "replace"]
    assert events[0][1] == TMP
    assert set(events[0][2]) & set("wxa")  # opened for writing
    assert events[-1] == ("replace", TMP, BAL)
    assert read(BAL) == b"1250"
    assert not os.path.exists(TMP)


def test_never_opens_balance_txt(workdir, opened_paths):
    write(BAL, b"5")
    opened_paths.clear()  # forget the test's own setup
    assert save_balance(6) is True
    assert save_balance(7) is True
    assert os.path.abspath(BAL) not in opened_paths
    assert os.path.abspath(TMP) in opened_paths
    assert read(BAL) == b"7"


def test_never_opens_balance_txt_when_replace_fails(workdir, monkeypatch, opened_paths):
    write(BAL, b"5")
    opened_paths.clear()  # forget the test's own setup
    install_spies(monkeypatch, fail_on="replace")
    assert save_balance(6) is False
    assert os.path.abspath(BAL) not in opened_paths


# --- invalid amounts -----------------------------------------------------------

@pytest.mark.parametrize("cents", [-1, -100, 100_000_001, 10**12])
def test_out_of_range_raises_and_touches_no_file(workdir, opened_paths, cents):
    write(BAL, b"42")
    write(TMP, b"43")
    before = {name: os.stat(name) for name in (BAL, TMP)}
    opened_paths.clear()

    with pytest.raises(ValueError):
        save_balance(cents)

    assert opened_paths == []
    assert sorted(os.listdir(workdir)) == [BAL, TMP]
    assert read(BAL) == b"42"
    assert read(TMP) == b"43"
    for name, st in before.items():
        assert os.stat(name).st_mtime_ns == st.st_mtime_ns
        assert os.stat(name).st_ino == st.st_ino


@pytest.mark.parametrize("cents", [-1, 100_000_001])
def test_out_of_range_creates_no_file(workdir, cents):
    with pytest.raises(ValueError):
        save_balance(cents)
    assert os.listdir(workdir) == []


@pytest.mark.parametrize("cents", [True, False, 1250.0, "1250", None])
def test_non_int_raises_type_error_and_creates_no_file(workdir, cents):
    with pytest.raises(TypeError):
        save_balance(cents)
    assert os.listdir(workdir) == []


# --- failures before the move: return False, no temp file left ---------------

@pytest.mark.parametrize("fail_on", ["open", "write", "fsync", "close"])
def test_failure_before_replace_returns_false_and_leaves_no_temp(workdir, monkeypatch, fail_on):
    write(BAL, b"300")
    events, _ = install_spies(monkeypatch, fail_on=fail_on)
    assert save_balance(400) is False
    assert read(BAL) == b"300"
    assert not os.path.exists(TMP)
    assert all(e[0] != "replace" for e in events)


def test_failure_before_replace_closes_the_file(workdir, monkeypatch):
    _, files = install_spies(monkeypatch, fail_on="fsync")
    assert save_balance(400) is False
    assert files and all(f.closed for f in files)


def test_interrupt_during_fsync_leaves_no_temp(workdir, monkeypatch):
    write(BAL, b"300")
    install_spies(monkeypatch, fail_on="fsync-interrupt")
    with pytest.raises(KeyboardInterrupt):
        save_balance(400)
    assert read(BAL) == b"300"
    assert not os.path.exists(TMP)


def test_temp_path_is_a_directory(workdir):
    write(BAL, b"300")
    os.mkdir(TMP)
    assert save_balance(400) is False
    assert read(BAL) == b"300"
    assert os.path.isdir(TMP)


# --- failure at the move: return False, keep the temp file ---------------------

def test_replace_failure_keeps_temp_with_balance(workdir, monkeypatch):
    write(BAL, b"300")
    install_spies(monkeypatch, fail_on="replace")
    assert save_balance(400) is False
    assert read(BAL) == b"300"
    assert read(TMP) == b"400"


def test_replace_failure_on_real_filesystem_keeps_temp(workdir):
    os.mkdir(BAL)  # a directory in the way makes os.replace fail
    assert save_balance(400) is False
    assert read(TMP) == b"400"
    assert os.path.isdir(BAL)


def test_save_after_replace_failure_succeeds(workdir, monkeypatch):
    write(BAL, b"300")
    with monkeypatch.context() as m:
        install_spies(m, fail_on="replace")
        assert save_balance(400) is False
    assert read(TMP) == b"400"
    assert save_balance(500) is True
    assert read(BAL) == b"500"
    assert not os.path.exists(TMP)


# --- stale temp files ------------------------------------------------------------

def test_stale_partial_temp_is_replaced(workdir):
    write(BAL, b"300")
    write(TMP, b"12")  # left by a crash mid-write
    assert save_balance(500) is True
    assert read(BAL) == b"500"
    assert not os.path.exists(TMP)


def _link_test(workdir, monkeypatch, make_link):
    write(BAL, b"111")
    try:
        make_link(BAL, TMP)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"links not supported: {exc}")

    def fsync_check(fd, files):
        # Writing the temp file must not have touched balance.txt.
        assert read(BAL) == b"111"
        assert not os.path.samestat(os.fstat(fd), os.stat(BAL))

    install_spies(monkeypatch, fsync_check=fsync_check)
    assert save_balance(222) is True
    assert read(BAL) == b"222"
    assert not os.path.islink(BAL)
    assert not os.path.exists(TMP)


def test_stale_temp_symlink_to_balance_is_not_followed(workdir, monkeypatch):
    _link_test(workdir, monkeypatch, os.symlink)


def test_stale_temp_hardlink_to_balance_is_not_written_through(workdir, monkeypatch):
    _link_test(workdir, monkeypatch, os.link)
