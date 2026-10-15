import importlib.util
from pathlib import Path

import pytest

from benzie.core.chat import ChatService
from benzie.inference.engine import InferenceError
from benzie.inference.stream import GenerationEvent

spec = importlib.util.spec_from_file_location(
    "acceptance_local_chat", Path(__file__).resolve().parents[1] / "scripts/acceptance_local_chat.py")
acceptance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acceptance)


def test_acceptance_exercises_history_context_cancellation_and_cleanup(tmp_path):
    engines = []
    contexts = []
    class Engine:
        def __init__(self):
            self.closed = False
            engines.append(self)
        def start(self, **kwargs): pass
        def close(self): self.closed = True
        def cancel(self): pass
        def generate_stream(self, prompt, **kwargs):
            contexts.append(kwargs["history"])
            yield GenerationEvent("Respons sintetis")
    acceptance.run_checks(ChatService(Engine), tmp_path)
    assert len(engines) == 3 and all(engine.closed for engine in engines)
    assert contexts[0] == contexts[2] == []
    assert [m["role"] for m in contexts[1]] == ["user", "assistant"]


def test_acceptance_failure_still_closes_runtime(tmp_path):
    class Engine:
        closed = False
        def start(self, **kwargs): raise InferenceError("Runtime gagal")
        def close(self): self.closed = True
    engine = Engine()
    with pytest.raises(InferenceError):
        acceptance.run_checks(ChatService(lambda: engine), tmp_path)
    assert engine.closed


def test_missing_settings_returns_failure_without_creating_data(tmp_path, capsys):
    assert acceptance.main(["--settings", str(tmp_path / "missing.json")]) == 1
    assert "terlebih dahulu" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())
