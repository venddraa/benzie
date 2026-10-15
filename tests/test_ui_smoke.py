"""Smoke test ringan; tidak menggantikan review window pada desktop nyata."""

import pytest
import threading
import time

pytest.importorskip("PySide6", reason="PySide6 diperlukan untuk smoke test window")

from PySide6.QtWidgets import QApplication

from benzie.core.startup import initialize_application
from benzie.core.chat import ChatService
from benzie.inference.engine import InferenceError
from benzie.inference.stream import GenerationEvent
from benzie.ui.main_window import MainWindow


def test_window_opens_and_closes(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(["benzie-test"])
    state = initialize_application(tmp_path)
    window = MainWindow(state)
    try:
        window.show()
        app.processEvents()
        assert window.isVisible()
        assert window.windowTitle() == "Benzie"
        assert "SQLite siap" in window.statusBar().currentMessage()
    finally:
        window.close()
        app.processEvents()
    assert not window.isVisible()


def wait_for(app, condition):
    deadline = time.monotonic() + 3
    while not condition() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.005)
    app.processEvents()
    assert condition()


def test_chat_streams_literal_text_and_accepts_next_message(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(["benzie-test"])

    class FakeEngine:
        def start(self, **options): pass
        def close(self): pass
        def generate_stream(self, prompt, **options):
            yield GenerationEvent("<b>Ha")
            yield GenerationEvent("lo</b>")

    window = MainWindow(initialize_application(tmp_path), chat_service=ChatService(FakeEngine), model_name="test.gguf")
    window.show()
    try:
        assert not window.send_button.isEnabled()
        window.message_input.setText("Halo <i>literal</i>")
        assert window.send_button.isEnabled()
        window.send_button.click()
        assert not window.message_input.isEnabled()
        assert not window.model_button.isEnabled()
        wait_for(app, lambda: window._worker is None)
        assert "<b>Halo</b>" in window.chat_history.toPlainText()
        assert "Halo <i>literal</i>" in window.chat_history.toPlainText()
        assert window.message_input.isEnabled()
        assert window.model_button.isEnabled()
        window.message_input.setText("Pesan kedua")
        window.send_button.click()
        wait_for(app, lambda: window._worker is None)
        assert "Pesan kedua" in window.chat_history.toPlainText()
    finally:
        window.close()


def test_error_restores_input(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(["benzie-test"])

    class FailingEngine:
        def start(self, **options): raise InferenceError("Model lokal gagal dimuat.")
        def close(self): pass

    window = MainWindow(initialize_application(tmp_path), chat_service=ChatService(FailingEngine))
    window.show()
    try:
        window.message_input.setText("Halo")
        window.send_button.click()
        wait_for(app, lambda: window._worker is None)
        assert "Model lokal gagal dimuat." in window.chat_history.toPlainText()
        assert window.message_input.isEnabled()
        assert window._history.messages(window._conversation_id)[-1].status == "failed"
    finally:
        window.close()


def test_close_cancels_worker_before_destroying_window(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(["benzie-test"])
    release = threading.Event()
    started = threading.Event()

    class SlowEngine:
        def start(self, **options):
            started.set()
            release.wait(timeout=2)
        def cancel(self): release.set()
        def close(self): pass
        def generate_stream(self, prompt, **options): yield GenerationEvent("Selesai")

    window = MainWindow(initialize_application(tmp_path), chat_service=ChatService(SlowEngine))
    window.show()
    try:
        window.message_input.setText("Halo")
        window.send_button.click()
        wait_for(app, started.is_set)
        window.close()
        assert window._close_pending
        wait_for(app, lambda: not window.isVisible())
        assert release.is_set()
        assert window._worker is None
        assert window._history.messages(window._conversation_id)[-1].status == "cancelled"
    finally:
        release.set()
        wait_for(app, lambda: window._worker is None)
        window.close()


def test_cancel_preserves_partial_text_and_allows_next_request(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(["benzie-test"])
    release = threading.Event()
    blocked = threading.Event()
    engines = []

    class Engine:
        def __init__(self):
            self.closed = False
            engines.append(self)
        def start(self, **options): pass
        def generate_stream(self, prompt, **options):
            yield GenerationEvent("Awal")
            if len(engines) == 1:
                blocked.set()
                release.wait(timeout=2)
                yield GenerationEvent("Teks terlambat")
            else:
                yield GenerationEvent(" pesan kedua")
        def cancel(self): release.set()
        def close(self): self.closed = True

    window = MainWindow(initialize_application(tmp_path), chat_service=ChatService(Engine))
    window.show()
    try:
        window.message_input.setText("Pertama")
        window.send_button.click()
        wait_for(app, lambda: blocked.is_set() and "Awal" in window.chat_history.toPlainText())
        assert window.cancel_button.isEnabled()
        window.cancel_button.click()
        assert not window.cancel_button.isEnabled()
        wait_for(app, lambda: window._worker is None)
        assert "[Dibatalkan]" in window.chat_history.toPlainText()
        assert "Teks terlambat" not in window.chat_history.toPlainText()
        assert engines[0].closed
        saved = window._history.messages(window._conversation_id)[-1]
        assert saved.status == "cancelled"
        assert saved.content == "Awal"
        window.message_input.setText("Kedua")
        window.send_button.click()
        wait_for(app, lambda: window._worker is None)
        assert "pesan kedua" in window.chat_history.toPlainText()
        assert engines[1].closed
    finally:
        release.set()
        wait_for(app, lambda: window._worker is None)
        window.close()


def test_history_reopens_switches_and_continues_without_model_context(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(["benzie-test"])
    class Engine:
        def start(self, **kwargs): pass
        def close(self): pass
        def generate_stream(self, prompt, **kwargs): yield GenerationEvent("Jawaban " + prompt)
    state = initialize_application(tmp_path)
    window = MainWindow(state, chat_service=ChatService(Engine))
    try:
        window.message_input.setText("pertama")
        window.send_button.click()
        assert not window.new_button.isEnabled()
        assert not window.conversation_picker.isEnabled()
        wait_for(app, lambda: window._worker is None)
        first = window._conversation_id
        assert window.new_button.isEnabled()
        window.new_button.click()
        assert not window.chat_history.toPlainText()
        window.message_input.setText("kedua")
        window.send_button.click()
        wait_for(app, lambda: window._worker is None)
        window.conversation_picker.setCurrentIndex(window.conversation_picker.findData(first))
        assert "Jawaban pertama" in window.chat_history.toPlainText()
        assert "kedua" not in window.chat_history.toPlainText()
        window.message_input.setText("lanjutan")
        window.send_button.click()
        wait_for(app, lambda: window._worker is None)
    finally:
        window.close()
    reopened = MainWindow(state)
    try:
        assert "Jawaban lanjutan" in reopened.chat_history.toPlainText()
        assert "Jawaban pertama" in reopened.chat_history.toPlainText()
        assert not reopened.message_input.isEnabled()
    finally:
        reopened.close()


def test_storage_failure_preserves_visible_text_and_blocks_sending(monkeypatch, tmp_path):
    from benzie.persistence.database import DatabaseError
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(["benzie-test"])
    class Engine:
        def start(self, **kwargs): pass
        def close(self): pass
        def generate_stream(self, prompt, **kwargs): yield GenerationEvent("Jawaban penting")
    window = MainWindow(initialize_application(tmp_path), chat_service=ChatService(Engine))
    append = window._history.store.append_message
    def fail(cid, role, *args, **kwargs):
        if role == "assistant": raise DatabaseError("disk error")
        return append(cid, role, *args, **kwargs)
    monkeypatch.setattr(window._history.store, "append_message", fail)
    try:
        window.message_input.setText("Halo")
        window.send_button.click()
        wait_for(app, lambda: window._worker is None)
        assert "Jawaban penting" in window.chat_history.toPlainText()
        assert "History gagal" in window.chat_history.toPlainText()
        assert not window.send_button.isEnabled()
        assert not window.new_button.isEnabled()
    finally:
        window.close()
