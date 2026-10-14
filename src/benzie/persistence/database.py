"""Inisialisasi dan migrasi SQLite lokal secara transaksional."""

from contextlib import closing
from pathlib import Path
import sqlite3

SCHEMA_VERSION = 2


class DatabaseError(Exception):
    """Kesalahan penyimpanan yang dapat ditampilkan kepada pengguna."""


def initialize_database(path: Path) -> int:
    """Buat database atau validasi versi lama tanpa menghapus data.

    Versi 1 hanya penanda; versi 2 menambahkan percakapan dan pesan.
    Koneksi selalu ditutup sebelum fungsi kembali.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path, timeout=5)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                version = connection.execute("PRAGMA user_version").fetchone()[0]
                if version > SCHEMA_VERSION:
                    raise DatabaseError(
                        "Database dibuat oleh versi Benzie yang lebih baru. "
                        "Gunakan versi aplikasi yang sesuai; database tidak diubah."
                    )
                if version == 0:
                    connection.execute("PRAGMA user_version = 1")
                    version = 1
                if version == 1:
                    connection.execute("""
                        CREATE TABLE conversations (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL CHECK(length(trim(title)) > 0),
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        )
                    """)
                    connection.execute("""
                        CREATE TABLE messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            conversation_id INTEGER NOT NULL REFERENCES conversations(id),
                            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                            content TEXT NOT NULL,
                            status TEXT NOT NULL CHECK(status IN ('completed', 'cancelled', 'failed')),
                            created_at TEXT NOT NULL,
                            CHECK(role = 'assistant' OR status = 'completed')
                        )
                    """)
                    connection.execute(
                        "CREATE INDEX messages_conversation_order ON messages(conversation_id, id)"
                    )
                    connection.execute("PRAGMA user_version = 2")
        return SCHEMA_VERSION
    except (OSError, sqlite3.Error) as error:
        raise DatabaseError(
            "Database lokal tidak dapat dibuka atau diinisialisasi. "
            "Periksa lokasi data, izin akses, ruang disk, dan apakah file SQLite valid. "
            "Jika aplikasi lain sedang memakai database, tutup lalu coba kembali."
        ) from error
