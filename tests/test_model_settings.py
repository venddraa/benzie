from unittest.mock import Mock

import pytest

from benzie.core.model_settings import ModelSettings, SettingsError, load_settings, save_settings


@pytest.fixture
def settings(tmp_path):
    runtime = tmp_path / "runtime with spaces"
    runtime.write_bytes(b"not executed by validation")
    runtime.chmod(0o700)
    model = tmp_path / "smoke.gguf"
    model.write_bytes(b"GGUFtest")
    return ModelSettings(runtime, model)


def test_round_trip_is_private_and_does_not_load_model(tmp_path, settings, monkeypatch):
    start = Mock(side_effect=AssertionError("must not start model"))
    monkeypatch.setattr("benzie.inference.server.LocalServerProcess.start", start)
    path = tmp_path / "profile" / "model-settings.json"
    assert load_settings(path) is None
    assert save_settings(path, settings) == settings
    assert load_settings(path) == settings
    assert path.stat().st_mode & 0o777 == 0o600
    assert not list(path.parent.glob(".model-settings-*"))
    settings.chat_service()
    start.assert_not_called()


@pytest.mark.parametrize("text", ["not json", "[]", '{"version":99}',
                                       '{"version":1,"runtime":"relative","model":"/model","port":8081}',
                                       "x" * 16385])
def test_corrupt_settings_preserved_for_recovery(tmp_path, text):
    path = tmp_path / "model-settings.json"
    path.write_text(text)
    with pytest.raises(SettingsError):
        load_settings(path)
    assert path.read_text() == text


def test_missing_model_does_not_discard_existing_configuration(tmp_path, settings):
    path = tmp_path / "model-settings.json"
    save_settings(path, settings)
    original = path.read_bytes()
    settings.model.unlink()
    with pytest.raises(SettingsError, match="model lokal tidak ditemukan"):
        load_settings(path)
    assert path.read_bytes() == original


@pytest.mark.parametrize("port", [0, 65536, True, "8081"])
def test_invalid_settings_do_not_replace_saved_file(tmp_path, settings, port):
    path = tmp_path / "model-settings.json"
    save_settings(path, settings)
    original = path.read_bytes()
    with pytest.raises(SettingsError):
        save_settings(path, ModelSettings(settings.runtime, settings.model, port))
    assert path.read_bytes() == original


def test_failed_atomic_replace_preserves_previous_config(tmp_path, settings, monkeypatch):
    path = tmp_path / "model-settings.json"
    save_settings(path, settings)
    original = path.read_bytes()
    def fail(*args): raise OSError("private detail")
    monkeypatch.setattr("benzie.core.model_settings.os.replace", fail)
    with pytest.raises(SettingsError) as error:
        save_settings(path, ModelSettings(settings.runtime, settings.model, 8082))
    assert "private detail" not in str(error.value)
    assert path.read_bytes() == original
    assert not list(tmp_path.glob(".model-settings-*"))


def test_cli_override_does_not_replace_saved_settings(tmp_path, settings, monkeypatch):
    from benzie.app import main
    path = tmp_path / "model-settings.json"
    save_settings(path, settings)
    original = path.read_bytes()
    application = Mock()
    application.exec.return_value = 0
    window = Mock()
    monkeypatch.setattr("PySide6.QtWidgets.QApplication", Mock(return_value=application))
    constructor = Mock(return_value=window)
    monkeypatch.setattr("benzie.ui.main_window.MainWindow", constructor)
    assert main(["--data-dir", str(tmp_path), "--runtime", str(settings.runtime),
                 "--model", str(settings.model), "--port", "8082"]) == 0
    assert constructor.call_args.kwargs["model_settings"].port == 8082
    assert path.read_bytes() == original


def test_app_uses_saved_settings_without_cli_model(tmp_path, settings, monkeypatch):
    from benzie.app import main
    save_settings(tmp_path / "model-settings.json", settings)
    application = Mock()
    application.exec.return_value = 0
    monkeypatch.setattr("PySide6.QtWidgets.QApplication", Mock(return_value=application))
    constructor = Mock()
    monkeypatch.setattr("benzie.ui.main_window.MainWindow", constructor)
    assert main(["--data-dir", str(tmp_path)]) == 0
    assert constructor.call_args.kwargs["model_settings"] == settings
    assert constructor.call_args.kwargs["chat_service"] is not None


def test_app_recovers_from_invalid_config_without_overwriting(tmp_path, monkeypatch):
    from benzie.app import main
    path = tmp_path / "model-settings.json"
    path.write_text("broken")
    application = Mock()
    application.exec.return_value = 0
    monkeypatch.setattr("PySide6.QtWidgets.QApplication", Mock(return_value=application))
    constructor = Mock()
    monkeypatch.setattr("benzie.ui.main_window.MainWindow", constructor)
    assert main(["--data-dir", str(tmp_path)]) == 0
    assert constructor.call_args.kwargs["settings_error"]
    assert constructor.call_args.kwargs["chat_service"] is None
    assert path.read_text() == "broken"
