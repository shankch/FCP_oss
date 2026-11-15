import os

import pytest

import save_balance as sb
from save_balance import save_balance

BAL = "balance.txt"
TMP = "balance.txt.tmp"


@pytest.fixture(autouse=True)
def in_tmp_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def read(name):
    with open(name) as f:
        return f.read()


class Spy:
    """Records the order of open / fsync / replace calls."""

    def __init__(self, monkeypatch):
        self.events = []
        self.opened = {}  # name -> file object
        real_open, real_fsync, real_replace = open, os.fsync, os.replace

        def spy_open(name, *args, **kwargs):
            self.events.append(("open", name))
            f = real_open(name, *args, **kwargs)
            self.opened[name] = f
            return f

        def spy_fsync(fd):
            tmp = self.opened.get(TMP)
            self.events.append(
                ("fsync", tmp is not None and fd == tmp.fileno(), tmp.closed if tmp else None)
            )
            return real_fsync(fd)

        def spy_replace(src, dst):
            tmp = self.opened.get(TMP)
            self.events.append(("replace", src, dst, tmp.closed if tmp else None))
            return real_replace(src, dst)

        # `open` is not defined in the module, so this shadows the builtin there.
        monkeypatch.setattr(sb, "open", spy_open, raising=False)
        monkeypatch.setattr(os, "fsync", spy_fsync)
        monkeypatch.setattr(os, "replace", spy_replace)


# --- the happy path ---------------------------------------------------------

def test_saves_digits_and_returns_true():
    assert save_balance(1250) is True
    assert read(BAL) == "1250"


def test_leaves_no_temp_file_after_success():
    save_balance(1250)
    assert os.listdir(".") == [BAL]


def test_overwrites_previous_balance():
    save_balance(1250)
    assert save_balance(7) is True
    assert read(BAL) == "7"
    assert os.listdir(".") == [BAL]


@pytest.mark.parametrize("cents", [0, 1, 99, 100, 123456789 // 2, 100_000_000])
def test_accepts_values_in_range(cents):
    assert save_balance(cents) is True
    assert read(BAL) == str(cents)


def test_text_is_only_digits_no_newline():
    save_balance(100_000_000)
    assert read(BAL) == "100000000"
    assert open(BAL, "rb").read() == b"100000000"


def test_overwrites_stale_temp_file_on_success():
    with open(TMP, "w") as f:
        f.write("999999999999")
    assert save_balance(5) is True
    assert read(BAL) == "5"
    assert os.listdir(".") == [BAL]


# --- rule 1: validation -----------------------------------------------------

@pytest.mark.parametrize("cents", [-1, -100, 100_000_001, 10**12])
def test_out_of_range_raises_value_error(cents):
    with pytest.raises(ValueError):
        save_balance(cents)


@pytest.mark.parametrize("cents", [-1, 100_000_001])
def test_out_of_range_touches_no_file(cents, monkeypatch):
    with open(BAL, "w") as f:
        f.write("42")
    before = os.stat(BAL)
    spy = Spy(monkeypatch)
    with pytest.raises(ValueError):
        save_balance(cents)
    assert spy.events == []  # nothing opened, synced or moved
    assert os.listdir(".") == [BAL]
    assert read(BAL) == "42"
    assert os.stat(BAL).st_mtime_ns == before.st_mtime_ns


def test_out_of_range_creates_no_file_when_none_exists():
    with pytest.raises(ValueError):
        save_balance(-5)
    assert os.listdir(".") == []


@pytest.mark.parametrize("bad", [12.5, "1250", None, True, False])
def test_non_int_is_rejected_and_touches_no_file(bad):
    with pytest.raises(TypeError):
        save_balance(bad)
    assert os.listdir(".") == []


# --- rules 3 and 4: the protocol --------------------------------------------

def test_protocol_order_and_never_opens_balance_file(monkeypatch):
    spy = Spy(monkeypatch)
    assert save_balance(1250) is True
    assert spy.events == [
        ("open", TMP),
        ("fsync", True, False),  # fsync of the temp file's own descriptor, still open
        ("replace", TMP, BAL, True),  # temp file already closed when moved
    ]
    assert list(spy.opened) == [TMP]  # balance.txt itself is never opened


def test_open_for_writing_in_text_mode(monkeypatch):
    modes = []
    real_open = open

    def spy_open(name, mode="r", *args, **kwargs):
        modes.append((name, mode))
        return real_open(name, mode, *args, **kwargs)

    monkeypatch.setattr(sb, "open", spy_open, raising=False)
    save_balance(1250)
    assert modes == [(TMP, "w")]


def test_uses_current_directory_at_call_time(tmp_path, monkeypatch):
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)
    assert save_balance(3) is True
    assert (other / BAL).read_text() == "3"
    assert not (tmp_path / BAL).exists()


def test_data_is_complete_when_replace_is_called(monkeypatch):
    seen = []
    real_replace = os.replace

    def replace(src, dst):
        seen.append(read(src))
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", replace)
    save_balance(1250)
    assert seen == ["1250"]


# --- rule 7: os.replace fails -----------------------------------------------

def _failing_replace(*args):
    raise OSError("replace failed")


def test_replace_failure_returns_false_and_keeps_temp_file(monkeypatch):
    monkeypatch.setattr(os, "replace", _failing_replace)
    assert save_balance(1250) is False
    assert read(TMP) == "1250"
    assert os.listdir(".") == [TMP]  # balance.txt was not created


def test_replace_failure_leaves_old_balance_intact(monkeypatch):
    save_balance(100)
    monkeypatch.setattr(os, "replace", _failing_replace)
    assert save_balance(200) is False
    assert read(BAL) == "100"  # never damaged
    assert read(TMP) == "200"  # new balance recoverable


def test_replace_failure_closes_temp_file(monkeypatch):
    spy = Spy(monkeypatch)
    monkeypatch.setattr(os, "replace", _failing_replace)
    save_balance(1250)
    assert spy.opened[TMP].closed


def test_retry_after_replace_failure_succeeds_and_cleans_up(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(os, "replace", _failing_replace)
        assert save_balance(300) is False
    assert save_balance(400) is True
    assert read(BAL) == "400"
    assert os.listdir(".") == [BAL]


# --- rules 5 and 6: other failures ------------------------------------------

def test_fsync_failure_returns_false_and_leaves_no_temp_file(monkeypatch):
    def bad_fsync(fd):
        raise OSError("disk on fire")

    replaced = []
    monkeypatch.setattr(os, "fsync", bad_fsync)
    monkeypatch.setattr(os, "replace", lambda *a: replaced.append(a))
    assert save_balance(1250) is False
    assert replaced == []  # never moved an unsynced file
    assert os.listdir(".") == []


def test_fsync_failure_keeps_old_balance(monkeypatch):
    save_balance(100)

    def bad_fsync(fd):
        raise OSError("disk on fire")

    monkeypatch.setattr(os, "fsync", bad_fsync)
    assert save_balance(200) is False
    assert read(BAL) == "100"
    assert os.listdir(".") == [BAL]


def test_close_failure_returns_false_and_leaves_no_temp_file(monkeypatch):
    class BadClose:
        def __init__(self, f):
            self.f = f

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.f.close()
            raise OSError("close failed")

        def __getattr__(self, name):
            return getattr(self.f, name)

    real_open = open
    monkeypatch.setattr(
        sb, "open", lambda *a, **k: BadClose(real_open(*a, **k)), raising=False
    )
    replaced = []
    monkeypatch.setattr(os, "replace", lambda *a: replaced.append(a))
    assert save_balance(1250) is False
    assert replaced == []
    assert os.listdir(".") == []


def test_unexpected_error_while_writing_removes_temp_file_and_propagates(monkeypatch):
    def bad_fsync(fd):
        raise RuntimeError("boom")

    monkeypatch.setattr(os, "fsync", bad_fsync)
    with pytest.raises(RuntimeError):
        save_balance(1250)
    assert os.listdir(".") == []


def test_cannot_open_temp_file_returns_false_and_touches_nothing():
    save_balance(100)
    os.mkdir(TMP)  # makes opening balance.txt.tmp for writing fail
    assert save_balance(200) is False
    assert read(BAL) == "100"
    assert sorted(os.listdir(".")) == [BAL, TMP]
    assert os.path.isdir(TMP)  # not ours, left alone


def test_cannot_open_temp_file_does_not_delete_recoverable_balance(monkeypatch):
    # A kept temp file from an earlier failed replace must survive when a
    # later save cannot even open it.
    with open(TMP, "w") as f:
        f.write("777")

    def deny(name, *a, **k):
        raise PermissionError("denied")

    monkeypatch.setattr(sb, "open", deny, raising=False)
    assert save_balance(200) is False
    assert read(TMP) == "777"
