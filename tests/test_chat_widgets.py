import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from benzie.core.startup import initialize_application
from benzie.persistence.conversations import ConversationStore
from benzie.ui.chat_widgets import ChatTranscript, MessageInput
from benzie.ui.main_window import MainWindow

_application = None


@pytest.fixture
def app(monkeypatch):
    global _application
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _application = QApplication.instance() or QApplication(["benzie-test"])
    return _application


def test_enter_submits_shift_enter_keeps_newline(app):
    field = MessageInput()
    spy = QSignalSpy(field.submitted)
    try:
        field.show()
        field.setFocus()
        QTest.keyClicks(field, "Baris pertama")
        QTest.keyClick(field, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
        QTest.keyClicks(field, "Baris kedua")
        assert spy.count() == 0
        assert field.toPlainText() == "Baris pertama\nBaris kedua"
        QTest.keyClick(field, Qt.Key.Key_Return)
        assert spy.count() == 1
        assert field.toPlainText() == "Baris pertama\nBaris kedua"
    finally:
        field.close()


def test_formatted_roles_do_not_interpret_user_or_model_html(app):
    view = ChatTranscript()
    try:
        view.append_message("Anda", '<b>literal</b><img src="file:///private.png">')
        view.append_message("Benzie")
        view.append_chunk('<a href="https://example.test">teks</a>')
        assert '<img src="file:///private.png">' in view.toPlainText()
        assert '<a href="https://example.test">teks</a>' in view.toPlainText()
        cursor = view.document().find("teks")
        assert not cursor.charFormat().isAnchor()
        assert not view.textInteractionFlags() & Qt.TextInteractionFlag.LinksAccessibleByMouse
    finally:
        view.close()


def test_stream_does_not_pull_reader_away_from_older_messages(app):
    view = ChatTranscript()
    view.resize(400, 200)
    try:
        view.show()
        view.append_message("Benzie", "\n".join(f"Baris {i}" for i in range(100)))
        app.processEvents()
        bar = view.verticalScrollBar()
        assert bar.maximum() > 0
        bar.setValue(0)
        view.append_chunk("\nTambahan di akhir")
        app.processEvents()
        assert bar.value() == 0
        bar.setValue(bar.maximum())
        view.append_chunk("\nLanjut mengikuti jawaban")
        app.processEvents()
        assert bar.maximum() - bar.value() <= 2
    finally:
        view.close()


def test_sidebar_keyboard_navigation_and_empty_state(app, tmp_path):
    state = initialize_application(tmp_path)
    store = ConversationStore(state.database_path)
    first = store.create_conversation("Pertama <literal>")
    store.append_message(first.id, "user", "Pesan pertama")
    second = store.create_conversation("Kedua")
    store.append_message(second.id, "user", "Pesan kedua")
    window = MainWindow(state)
    try:
        window.show()
        app.processEvents()
        assert window.conversation_title.text() == "Kedua"
        assert window.chat_pages.currentIndex() == 1
        window.conversation_list.setFocus()
        QTest.keyClick(window.conversation_list, Qt.Key.Key_Down)
        assert window._conversation_id == first.id
        assert window.conversation_title.text() == "Pertama <literal>"
        assert "Pesan pertama" in window.chat_history.toPlainText()
        window.new_button.click()
        assert window.chat_pages.currentIndex() == 0
        assert "Pilih model" in window.welcome_detail.text()
        assert not window.message_input.isEnabled()
        assert window.cancel_button.isHidden()
    finally:
        window.close()
