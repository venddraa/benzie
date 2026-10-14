import os
import builtins
from pathlib import Path
import subprocess
import sys

import pytest

from benzie.core.startup import initialize_application
from benzie.persistence.database import DatabaseError, SCHEMA_VERSION


def test_core_initializes_database_in_selected_directory(tmp_path):
    state = initialize_application(tmp_path / "local data")

    assert state.database_path == tmp_path / "local data" / "benzie.sqlite3"
    assert state.database_path.is_file()
    assert state.schema_version == SCHEMA_VERSION
    assert initialize_application(tmp_path / "local data") == state


def test_relative_directory_is_resolved(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    state = initialize_application(Path("data"))

    assert state.database_path == tmp_path / "data" / "benzie.sqlite3"


def test_core_propagates_storage_error(tmp_path):
    path = tmp_path / "blocked"
    path.write_text("keep", encoding="utf-8")

    with pytest.raises(DatabaseError):
        initialize_application(path)


def test_core_import_does_not_load_ui_or_create_data(tmp_path):
    environment = dict(os.environ, XDG_DATA_HOME=str(tmp_path))
    result = subprocess.run(
        [sys.executable, "-c", (
            "import sys; import benzie.core.startup; "
            "assert not any(n.startswith('PySide6') for n in sys.modules)"
        )],
        env=environment, capture_output=True, text=True, timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert not list(tmp_path.iterdir())


def test_module_help_does_not_start_ui_or_create_data(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "benzie", "--help"],
        env=dict(os.environ, XDG_DATA_HOME=str(tmp_path)),
        capture_output=True, text=True, timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert "--data-dir" in result.stdout
    assert not list(tmp_path.iterdir())


def test_missing_qt_has_readable_error_without_creating_data(monkeypatch, tmp_path, caplog):
    from benzie.app import main

    original_import = builtins.__import__

    def without_qt(name, *args, **kwargs):
        if name.startswith("PySide6"):
            raise ModuleNotFoundError("PySide6 is not available")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_qt)

    assert main(["--data-dir", str(tmp_path)]) == 1
    assert "PySide6 tidak tersedia atau gagal dimuat" in caplog.text
    assert not list(tmp_path.iterdir())
