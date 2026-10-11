"""Inisialisasi SQLite. Tabel percakapan baru ditambahkan pada Milestone 4."""

from contextlib import closing
from pathlib import Path
import sqlite3

SCHEMA_VERSION = 1


class DatabaseError(Exception):
    """Kesalahan penyimpanan yang dapat ditampilkan kepada pengguna."""


def initialize_database(path: Path) -> int:
    """Buat database atau validasi versi lama tanpa menghapus data.

    Versi 1 hanya menetapkan penanda versi skema, belum mempunyai tabel.
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
                elif version != SCHEMA_VERSION:
                    raise DatabaseError("Versi database tidak didukung.")
        return SCHEMA_VERSION
    except (OSError, sqlite3.Error) as error:
        raise DatabaseError(
            "Database lokal tidak dapat dibuka atau diinisialisasi. "
            "Periksa lokasi data, izin akses, ruang disk, dan apakah file SQLite valid. "
            "Jika aplikasi lain sedang memakai database, tutup lalu coba kembali."
        ) from error
