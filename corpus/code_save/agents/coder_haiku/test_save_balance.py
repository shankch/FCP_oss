import builtins
import os

import pytest

from save_balance import save_balance


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_writes_digits_and_returns_true(workdir):
    assert save_balance(1250) is True
    assert (workdir / "balance.txt").read_text(encoding="ascii") == "1250"


def test_no_tmp_file_left_after_success(workdir):
    save_balance(1250)
    assert not (workdir / "balance.txt.tmp").exists()


def test_zero_is_stored_as_0(workdir):
    assert save_balance(0) is True
    assert (workdir / "balance.txt").read_text(encoding="ascii") == "0"


def test_maximum_is_accepted(workdir):
    assert save_balance(100_000_000) is True
    assert (workdir / "balance.txt").read_text(encoding="ascii") == "100000000"


def test_overwrites_previous_balance(workdir):
    save_balance(1)
    assert save_balance(2) is True
    assert (workdir / "balance.txt").read_text(encoding="ascii") == "2"


@pytest.mark.parametrize("bad", [-1, -1250, 100_000_001])
def test_out_of_range_raises_and_touches_no_file(workdir, bad):
    (workdir / "balance.txt").write_text("999", encoding="ascii")
    with pytest.raises(ValueError):
        save_balance(bad)
    assert sorted(p.name for p in workdir.iterdir()) == ["balance.txt"]
    assert (workdir / "balance.txt").read_text(encoding="ascii") == "999"


def test_out_of_range_creates_nothing_in_empty_dir(workdir):
    with pytest.raises(ValueError):
        save_balance(-5)
    assert list(workdir.iterdir()) == []


@pytest.mark.parametrize("bad", [12.5, "1250", None, True])
def test_non_int_raises_type_error(workdir, bad):
    with pytest.raises(TypeError):
        save_balance(bad)
    assert list(workdir.iterdir()) == []


def test_fsync_runs_on_open_tmp_file_before_replace_and_file_is_closed(workdir, monkeypatch):
    events = []
    real_fsync = os.fsync
    real_replace = os.replace

    def spy_fsync(fd):
        events.append(("fsync", fd))
        assert os.path.exists(workdir / "balance.txt.tmp")
        return real_fsync(fd)

    def spy_replace(src, dst):
        events.append(("replace", src, dst))
        fsync_fds = [e[1] for e in events if e[0] == "fsync"]
        assert fsync_fds, "replace called before fsync"
        for fd in fsync_fds:
            with pytest.raises(OSError):
                os.fstat(fd)  # file must already be closed
        return real_replace(src, dst)

    monkeypatch.setattr(os, "fsync", spy_fsync)
    monkeypatch.setattr(os, "replace", spy_replace)

    assert save_balance(1250) is True
    assert [e[0] for e in events] == ["fsync", "replace"]
    assert events[1][1:] == ("balance.txt.tmp", "balance.txt")


def test_balance_txt_is_never_opened_directly(workdir, monkeypatch):
    opened = []
    real_open = builtins.open

    def spy_open(file, *args, **kwargs):
        opened.append(os.fspath(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy_open)
    save_balance(1250)
    assert "balance.txt" not in opened
    assert "balance.txt.tmp" in opened


def test_replace_failure_keeps_tmp_and_returns_false(workdir, monkeypatch):
    (workdir / "balance.txt").write_text("999", encoding="ascii")

    def failing_replace(src, dst):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", failing_replace)
    assert save_balance(1250) is False
    assert (workdir / "balance.txt.tmp").read_text(encoding="ascii") == "1250"
    assert (workdir / "balance.txt").read_text(encoding="ascii") == "999"


def test_fsync_failure_removes_tmp_and_returns_false(workdir, monkeypatch):
    (workdir / "balance.txt").write_text("999", encoding="ascii")

    def failing_fsync(fd):
        raise OSError("simulated fsync failure")

    monkeypatch.setattr(os, "fsync", failing_fsync)
    assert save_balance(1250) is False
    assert not (workdir / "balance.txt.tmp").exists()
    assert (workdir / "balance.txt").read_text(encoding="ascii") == "999"


def test_open_failure_returns_false(workdir, monkeypatch):
    def failing_open(file, *args, **kwargs):
        raise OSError("simulated open failure")

    monkeypatch.setattr(builtins, "open", failing_open)
    assert save_balance(1250) is False
    assert list(workdir.iterdir()) == []
