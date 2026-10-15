import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QWidget
import shiboken6

from benzie.core.model_settings import ModelSettings, load_settings
from benzie.core.startup import initialize_application
from benzie.ui.main_window import MainWindow
from benzie.ui.model_dialog import ModelDialog

_application = None


@pytest.fixture
def app(monkeypatch):
    global _application
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _application = QApplication.instance() or QApplication(["benzie-test"])
    return _application


def test_dialog_saves_valid_local_files_and_reports_invalid_selection(app, tmp_path):
    path = tmp_path / "model-settings.json"
    parent = QWidget()
    dialog = ModelDialog(path, None, parent)
    dialog._save()
    assert dialog.error_label.text()
    assert not path.exists()
    runtime = tmp_path / "server"
    runtime.write_bytes(b"test")
    runtime.chmod(0o700)
    model = tmp_path / "model.gguf"
    model.write_bytes(b"invalid")
    dialog.runtime_input.setText(str(runtime))
    dialog.model_input.setText(str(model))
    dialog._save()
    assert "GGUF" in dialog.error_label.text()
    assert not path.exists()
    model.write_bytes(b"GGUFtest")
    dialog._save()
    assert dialog.result() == ModelDialog.DialogCode.Accepted
    assert load_settings(path) == ModelSettings(runtime, model)
    shiboken6.delete(parent)


def test_cancel_keeps_existing_settings(app, tmp_path):
    path = tmp_path / "model-settings.json"
    path.write_text("keep")
    dialog = ModelDialog(path, None)
    dialog.reject()
    assert path.read_text() == "keep"
    assert dialog.selected_settings is None
    shiboken6.delete(dialog)


def test_model_selection_enables_chat_without_replacing_history(app, tmp_path, monkeypatch):
    runtime = tmp_path / "server"
    model = tmp_path / "model.gguf"
    chosen = ModelSettings(runtime, model)
    class Dialog:
        DialogCode = ModelDialog.DialogCode
        selected_settings = chosen
        def __init__(self, *args): pass
        def exec(self): return self.DialogCode.Accepted
        def deleteLater(self): pass
    monkeypatch.setattr("benzie.ui.main_window.ModelDialog", Dialog)
    window = MainWindow(initialize_application(tmp_path))
    try:
        window._new_conversation()
        cid = window._conversation_id
        window._history.store.append_message(cid, "user", "ancien message")
        window._open_conversation()
        window.message_input.setText("Halo")
        assert not window.send_button.isEnabled()
        window.model_button.click()
        assert window.send_button.isEnabled()
        assert "model.gguf" in window.model_label.text()
        assert "ancien message" in window.chat_history.toPlainText()
        assert window._conversation_id == cid
        assert window._history.chat is window._service
        window._worker = object()
        window._choose_model()  # Guard even if invoked directly during generation.
        assert window._conversation_id == cid
        window._worker = None
    finally:
        window.close()
