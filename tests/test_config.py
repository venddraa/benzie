import pytest

from benzie.config import default_data_directory


@pytest.mark.parametrize("value", [None, "", "relative/path"])
def test_missing_or_invalid_xdg_uses_home(monkeypatch, tmp_path, value):
    monkeypatch.setenv("HOME", str(tmp_path))
    if value is None:
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    else:
        monkeypatch.setenv("XDG_DATA_HOME", value)

    result = default_data_directory()

    assert result == tmp_path / ".local/share/benzie"
    assert not result.exists()


def test_absolute_xdg_directory_is_used_without_creating_it(monkeypatch, tmp_path):
    directory = tmp_path / "data with spaces"
    monkeypatch.setenv("XDG_DATA_HOME", str(directory))

    assert default_data_directory() == directory / "benzie"
    assert not directory.exists()
