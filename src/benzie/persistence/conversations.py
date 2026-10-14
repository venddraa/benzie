"""Penyimpanan history tanpa Qt, inference, atau ekstraksi memory."""

from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from benzie.persistence.database import DatabaseError, SCHEMA_VERSION


@dataclass(frozen=True)
class Conversation:
    id: int
    title: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Message:
    id: int
    conversation_id: int
    role: str
    content: str
    status: str
    created_at: str


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class ConversationStore:
    """Satu koneksi pendek per operasi; database harus diinisialisasi dahulu.

    Pesan disimpan setelah hasil request diketahui. Status membedakan jawaban
    lengkap, parsial yang dibatalkan, dan gagal; bukan state generation aktif.
    """

    def __init__(self, path: Path):
        self.path = path.resolve()

    @contextmanager
    def _connection(self):
        try:
            # mode=rw mencegah pembuatan database kosong jika file hilang.
            with closing(sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, timeout=5)) as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                if connection.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
                    raise DatabaseError("Versi database tidak sesuai. Buka ulang aplikasi Benzie.")
                with connection:
                    yield connection
        except sqlite3.Error as error:
            raise DatabaseError(
                "Riwayat lokal tidak dapat dibaca atau disimpan. "
                "Periksa izin akses, ruang disk, dan apakah database sedang dipakai aplikasi lain."
            ) from error

    def create_conversation(self, title: str = "Percakapan baru") -> Conversation:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Judul percakapan tidak boleh kosong.")
        now = _timestamp()
        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT INTO conversations(title, created_at, updated_at) VALUES (?, ?, ?)",
                (title.strip(), now, now),
            )
            return Conversation(cursor.lastrowid, title.strip(), now, now)

    def get_conversation(self, conversation_id: int) -> Conversation:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if row is None:
                raise DatabaseError("Percakapan tidak ditemukan.")
            return Conversation(*row)

    def list_conversations(self) -> list[Conversation]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, title, created_at, updated_at FROM conversations "
                "ORDER BY updated_at DESC, id DESC"
            ).fetchall()
            return [Conversation(*row) for row in rows]

    def append_message(
        self, conversation_id: int, role: str, content: str, *, status: str = "completed"
    ) -> Message:
        if role not in ("user", "assistant"):
            raise ValueError("Role pesan tidak didukung.")
        if status not in ("completed", "cancelled", "failed") or (role == "user" and status != "completed"):
            raise ValueError("Status pesan tidak didukung.")
        if not isinstance(content, str) or (status == "completed" and not content.strip()):
            raise ValueError("Pesan selesai tidak boleh kosong.")
        now = _timestamp()
        with self._connection() as connection:
            # UPDATE dan INSERT berada dalam satu transaksi: keduanya berhasil atau rollback.
            cursor = connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id)
            )
            if cursor.rowcount != 1:
                raise DatabaseError("Percakapan tidak ditemukan.")
            cursor = connection.execute(
                "INSERT INTO messages(conversation_id, role, content, status, created_at) "
                "VALUES (?, ?, ?, ?, ?)", (conversation_id, role, content, status, now),
            )
            return Message(cursor.lastrowid, conversation_id, role, content, status, now)

    def list_messages(self, conversation_id: int) -> list[Message]:
        with self._connection() as connection:
            if connection.execute(
                "SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone() is None:
                raise DatabaseError("Percakapan tidak ditemukan.")
            rows = connection.execute(
                "SELECT id, conversation_id, role, content, status, created_at FROM messages "
                "WHERE conversation_id = ? ORDER BY id", (conversation_id,),
            ).fetchall()
            return [Message(*row) for row in rows]
