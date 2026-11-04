from contextlib import closing
import sqlite3

import pytest

from benzie.persistence.conversations import ConversationStore
from benzie.persistence.database import DatabaseError, initialize_database


@pytest.fixture
def store(tmp_path):
    path = tmp_path / "history.sqlite3"
    initialize_database(path)
    return ConversationStore(path)


def test_round_trip_after_reopening_preserves_literal_content_and_order(store):
    conversation = store.create_conversation("Bahasa Indonesia")
    contents = ["halo 🌟", "<b>Benzie</b>", "'); DROP TABLE messages; --"]
    messages = [store.append_message(conversation.id, role, content)
                for role, content in zip(["user", "assistant", "user"], contents)]

    reopened = ConversationStore(store.path)
    assert reopened.list_messages(conversation.id) == messages
    assert [m.content for m in messages] == contents
    assert reopened.get_conversation(conversation.id).created_at == conversation.created_at
    assert reopened.get_conversation(conversation.id).updated_at == messages[-1].created_at


def test_conversations_are_isolated_and_recent_activity_sorts_first(store, monkeypatch):
    times = iter(["2026-10-14T01:00:00+00:00", "2026-10-14T02:00:00+00:00",
                  "2026-10-14T03:00:00+00:00"])
    monkeypatch.setattr("benzie.persistence.conversations._timestamp", lambda: next(times))
    first = store.create_conversation("Pertama")
    second = store.create_conversation("Kedua")
    assert [c.id for c in store.list_conversations()] == [second.id, first.id]
    message = store.append_message(first.id, "user", "Halo")
    assert [c.id for c in store.list_conversations()] == [first.id, second.id]
    assert store.list_messages(first.id) == [message]
    assert store.list_messages(second.id) == []


def test_equal_timestamps_still_have_deterministic_order(store, monkeypatch):
    monkeypatch.setattr("benzie.persistence.conversations._timestamp", lambda: "2026-10-14T00:00:00+00:00")
    first = store.create_conversation()
    second = store.create_conversation()
    messages = [store.append_message(first.id, "user", str(i)) for i in range(3)]
    assert store.list_messages(first.id) == messages
    assert [c.id for c in store.list_conversations()] == [second.id, first.id]


@pytest.mark.parametrize("status,content", [("cancelled", "Jawaban parsial"), ("cancelled", ""), ("failed", "")])
def test_incomplete_answers_keep_explicit_status(store, status, content):
    conversation = store.create_conversation()
    message = store.append_message(conversation.id, "assistant", content, status=status)
    assert store.list_messages(conversation.id) == [message]
    assert message.status == status


@pytest.mark.parametrize("role,content,status", [
    ("system", "prompt", "completed"), ("user", "halo", "cancelled"),
    ("assistant", "halo", "pending"), ("assistant", "  ", "completed"),
    ("user", None, "completed"),
])
def test_invalid_messages_do_not_change_history(store, role, content, status):
    conversation = store.create_conversation()
    with pytest.raises(ValueError):
        store.append_message(conversation.id, role, content, status=status)
    assert store.get_conversation(conversation.id) == conversation
    assert store.list_messages(conversation.id) == []


def test_blank_title_rejected(store):
    with pytest.raises(ValueError):
        store.create_conversation(" \n ")
    assert store.list_conversations() == []


def test_missing_conversation_has_readable_error(store):
    for operation in [lambda: store.get_conversation(999), lambda: store.list_messages(999),
                      lambda: store.append_message(999, "user", "halo")]:
        with pytest.raises(DatabaseError, match="tidak ditemukan"):
            operation()
    assert store.list_conversations() == []


def test_failed_insert_rolls_back_conversation_update_and_hides_raw_error(store):
    conversation = store.create_conversation()
    with closing(sqlite3.connect(store.path)) as connection:
        connection.execute("""CREATE TRIGGER reject_message BEFORE INSERT ON messages
                              BEGIN SELECT RAISE(ABORT, 'private detail'); END""")
    with pytest.raises(DatabaseError) as caught:
        store.append_message(conversation.id, "user", "private prompt", initial_title="Judul jangan tersimpan")
    assert "private" not in str(caught.value)
    assert store.get_conversation(conversation.id) == conversation
    assert store.list_messages(conversation.id) == []


def test_missing_database_not_silently_created(tmp_path):
    path = tmp_path / "missing.sqlite3"
    with pytest.raises(DatabaseError):
        ConversationStore(path).list_conversations()
    assert not path.exists()


def test_foreign_keys_reject_orphan_messages(store):
    with store._connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO messages(conversation_id, role, content, status, created_at) "
                "VALUES (999, 'user', 'halo', 'completed', 'now')"
            )


def test_store_rejects_newer_schema_without_mutation(store):
    with closing(sqlite3.connect(store.path)) as connection:
        connection.execute("PRAGMA user_version = 99")
    before = store.path.read_bytes()
    with pytest.raises(DatabaseError, match="Versi database"):
        store.create_conversation()
    assert store.path.read_bytes() == before


def test_operations_release_database_lock(store):
    conversation = store.create_conversation()
    store.append_message(conversation.id, "user", "halo")
    store.list_messages(conversation.id)
    with closing(sqlite3.connect(store.path, timeout=0)) as connection:
        connection.execute("BEGIN EXCLUSIVE")
        connection.rollback()


def test_custom_title_and_existing_history_are_not_renamed(store):
    custom = store.create_conversation("Judul pilihan sendiri")
    store.append_message(custom.id, "user", "Pesan pertama", initial_title="Judul otomatis")
    assert store.get_conversation(custom.id).title == "Judul pilihan sendiri"
    old = store.create_conversation()
    store.append_message(old.id, "user", "Riwayat dari versi lama")
    store.append_message(old.id, "user", "Pesan baru", initial_title="Judul otomatis")
    assert store.get_conversation(old.id).title == "Percakapan baru"


def test_default_title_matching_first_message_is_still_only_set_once(store):
    conversation = store.create_conversation()
    store.append_message(conversation.id, "user", "Percakapan baru", initial_title="Percakapan baru")
    store.append_message(conversation.id, "user", "Jangan ganti judul", initial_title="Judul berbeda")
    assert store.get_conversation(conversation.id).title == "Percakapan baru"


def test_rename_preserves_messages_and_survives_reopening(store):
    conversation = store.create_conversation()
    message = store.append_message(conversation.id, "user", "Pesan awal", initial_title="Judul awal")
    store.rename_conversation(conversation.id, "  Belajar\t SQLite  ")
    reopened = ConversationStore(store.path)
    assert reopened.get_conversation(conversation.id).title == "Belajar SQLite"
    assert reopened.list_messages(conversation.id) == [message]
    store.append_message(conversation.id, "user", "Lanjutan", initial_title="Tidak mengganti")
    assert store.get_conversation(conversation.id).title == "Belajar SQLite"


@pytest.mark.parametrize("title", ["", " \n ", "a" * 61, None])
def test_invalid_rename_preserves_title_and_activity(store, title):
    conversation = store.create_conversation("Judul lama")
    store.append_message(conversation.id, "user", "Pesan")
    before = store.get_conversation(conversation.id)
    with pytest.raises(ValueError):
        store.rename_conversation(conversation.id, title)
    assert store.get_conversation(conversation.id) == before


def test_empty_conversation_cannot_be_renamed_until_first_message(store):
    conversation = store.create_conversation()
    with pytest.raises(ValueError, match="pesan pertama"):
        store.rename_conversation(conversation.id, "Nama manual")
    assert store.get_conversation(conversation.id) == conversation
    with pytest.raises(DatabaseError, match="tidak ditemukan"):
        store.rename_conversation(999, "Judul")


def test_failed_rename_rolls_back_title_and_activity(store):
    conversation = store.create_conversation("Judul tetap")
    message = store.append_message(conversation.id, "user", "Pesan tetap")
    before = store.get_conversation(conversation.id)
    with closing(sqlite3.connect(store.path)) as connection:
        connection.execute("""CREATE TRIGGER reject_title BEFORE UPDATE OF title ON conversations
                              BEGIN SELECT RAISE(ABORT, 'private detail'); END""")
    with pytest.raises(DatabaseError) as caught:
        store.rename_conversation(conversation.id, "Tidak tersimpan")
    assert "private detail" not in str(caught.value)
    assert store.get_conversation(conversation.id) == before
    assert store.list_messages(conversation.id) == [message]
