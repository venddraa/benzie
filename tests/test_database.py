from contextlib import closing
import sqlite3

import pytest

from benzie.persistence.database import DatabaseError, SCHEMA_VERSION, initialize_database


def test_initialize_database_persists_schema_version(tmp_path):
    path = tmp_path / "nested" / "benzie.sqlite3"

    assert initialize_database(path) == SCHEMA_VERSION

    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_reopening_database_preserves_existing_data(tmp_path):
    path = tmp_path / "benzie.sqlite3"
    initialize_database(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        # Fixture untuk memastikan startup tidak menghapus data, bukan tabel produk.
        connection.execute("CREATE TABLE sentinel (value TEXT)")
        connection.execute("INSERT INTO sentinel VALUES (?)", ("tetap tersimpan",))

    initialize_database(path)

    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("SELECT value FROM sentinel").fetchone()[0] == "tetap tersimpan"


def test_newer_database_is_rejected_without_changing_it(tmp_path):
    path = tmp_path / "benzie.sqlite3"
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA user_version = 99")
    before = path.read_bytes()

    with pytest.raises(DatabaseError, match="lebih baru"):
        initialize_database(path)

    assert path.read_bytes() == before


def test_invalid_database_is_not_overwritten(tmp_path):
    path = tmp_path / "benzie.sqlite3"
    original = b"This is not a SQLite database." * 10
    path.write_bytes(original)

    with pytest.raises(DatabaseError, match="SQLite valid"):
        initialize_database(path)

    assert path.read_bytes() == original


def test_file_in_place_of_directory_has_a_readable_error(tmp_path):
    parent = tmp_path / "not-a-directory"
    parent.write_text("preserve this", encoding="utf-8")

    with pytest.raises(DatabaseError, match="izin akses"):
        initialize_database(parent / "benzie.sqlite3")

    assert parent.read_text(encoding="utf-8") == "preserve this"


def test_directory_in_place_of_database_has_a_readable_error(tmp_path):
    path = tmp_path / "benzie.sqlite3"
    path.mkdir()

    with pytest.raises(DatabaseError):
        initialize_database(path)


def test_initialization_leaves_no_write_lock(tmp_path):
    path = tmp_path / "benzie.sqlite3"
    initialize_database(path)

    with closing(sqlite3.connect(path, timeout=0)) as connection:
        connection.execute("BEGIN EXCLUSIVE")
        connection.rollback()
