"""Smoke test ringan; tidak menggantikan review window pada desktop nyata."""

import pytest

pytest.importorskip("PySide6", reason="PySide6 diperlukan untuk smoke test window")

from PySide6.QtWidgets import QApplication

from benzie.core.startup import initialize_application
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
