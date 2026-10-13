"""Smoke test ringan; tidak menggantikan review window pada desktop nyata."""

import pytest
import threading
import time

pytest.importorskip("PySide6", reason="PySide6 diperlukan untuk smoke test window")

from PySide6.QtWidgets import QApplication

from benzie.core.startup import initialize_application
from benzie.core.chat import ChatEvent
from benzie.inference.engine import InferenceError
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

    class FakeService:
        def reply(self, prompt):
            yield ChatEvent("loading")
            yield ChatEvent("generating")
            yield ChatEvent("text", "<b>Ha")
            yield ChatEvent("text", "lo</b>")

    window = MainWindow(initialize_application(tmp_path), chat_service=FakeService(), model_name="test.gguf")
    window.show()
    try:
        assert not window.send_button.isEnabled()
        window.message_input.setText("Halo <i>literal</i>")
        assert window.send_button.isEnabled()
        window.send_button.click()
        assert not window.message_input.isEnabled()
        wait_for(app, lambda: window._worker is None)
        assert "<b>Halo</b>" in window.chat_history.toPlainText()
        assert "Halo <i>literal</i>" in window.chat_history.toPlainText()
        assert window.message_input.isEnabled()
        window.message_input.setText("Pesan kedua")
        window.send_button.click()
        wait_for(app, lambda: window._worker is None)
        assert "Pesan kedua" in window.chat_history.toPlainText()
    finally:
        window.close()


def test_error_restores_input(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(["benzie-test"])

    class FailingService:
        def reply(self, prompt):
            raise InferenceError("Model lokal gagal dimuat.")
            yield  # API generator yang gagal sebelum event pertama.

    window = MainWindow(initialize_application(tmp_path), chat_service=FailingService())
    window.show()
    try:
        window.message_input.setText("Halo")
        window.send_button.click()
        wait_for(app, lambda: window._worker is None)
        assert "Model lokal gagal dimuat." in window.chat_history.toPlainText()
        assert window.message_input.isEnabled()
    finally:
        window.close()


def test_close_waits_for_worker_without_destroying_running_thread(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(["benzie-test"])
    release = threading.Event()

    class SlowService:
        def reply(self, prompt):
            yield ChatEvent("loading")
            release.wait(timeout=2)
            yield ChatEvent("text", "Selesai")

    window = MainWindow(initialize_application(tmp_path), chat_service=SlowService())
    window.show()
    try:
        window.message_input.setText("Halo")
        window.send_button.click()
        window.close()
        app.processEvents()
        assert window.isVisible()
        assert window._close_pending
        release.set()
        wait_for(app, lambda: not window.isVisible())
        assert window._worker is None
    finally:
        release.set()
        wait_for(app, lambda: window._worker is None)
        window.close()
