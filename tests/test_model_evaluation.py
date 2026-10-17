import importlib.util
import json
import os
from pathlib import Path

import pytest

from benzie.inference.engine import InferenceError
from benzie.inference.stream import GenerationEvent

spec = importlib.util.spec_from_file_location(
    "evaluate_local_model", Path(__file__).resolve().parents[1] / "scripts/evaluate_local_model.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class Engine:
    closed = False
    process_id = os.getpid()
    def start(self, **options): pass
    def close(self): self.closed = True
    def generate_stream(self, prompt, **options):
        self.options = options
        yield GenerationEvent("Jawaban sintetis", completion_tokens=5, decode_tokens_per_second=20)


def test_generated_answer_requires_manual_review_and_uses_fixed_context():
    engine = Engine()
    case = {"id": "test", "prompt": "Sintetis", "criteria": "rubrik", "history": []}
    row = evaluation.evaluate_case(case, engine, resource_reader=lambda pid: {"peak_rss_bytes": 100})
    assert row["status"] == "generated" and row["manual_score"] is None
    assert row["answer"] == "Jawaban sintetis"
    assert row["ttft_seconds"] >= 0 and row["completion_tokens"] == 5
    assert row["peak_rss_bytes"] == 100
    assert engine.options["history"] == []
    assert engine.options["temperature"] == 0.0
    assert engine.closed


def test_failed_case_keeps_partial_text_but_is_not_generated():
    class Broken(Engine):
        def generate_stream(self, *args, **options):
            yield GenerationEvent("Parsial")
            raise InferenceError("private raw detail")
    engine = Broken()
    row = evaluation.evaluate_case({"id": "test", "prompt": "x", "criteria": "y"}, engine)
    assert row["status"] == "error"
    assert row["answer"] == "Parsial"
    assert "private raw detail" not in json.dumps(row)
    assert engine.closed


def test_interruption_always_cleans_up():
    class Interrupted(Engine):
        def start(self, **kwargs): raise KeyboardInterrupt()
    engine = Interrupted()
    with pytest.raises(KeyboardInterrupt):
        evaluation.evaluate_case({"id": "test", "prompt": "x", "criteria": "y"}, engine)
    assert engine.closed


def test_suite_has_unique_small_synthetic_cases_and_balanced_history():
    suite = json.loads(evaluation.SUITE.read_text())
    cases = suite["cases"]
    assert len(cases) == 10 and len({case["id"] for case in cases}) == 10
    for case in cases:
        assert case["prompt"] and case["criteria"]
        assert [message["role"] for message in case.get("history", [])] in (
            [], ["user", "assistant"], ["user", "assistant", "user", "assistant"])


@pytest.fixture
def command(tmp_path, monkeypatch):
    binary = tmp_path / "server"
    binary.write_bytes(b"not executed")
    binary.chmod(0o700)
    model = tmp_path / "model.gguf"
    model.write_bytes(b"GGUFtest")
    output = tmp_path / "report.json"
    monkeypatch.setattr(evaluation, "LlamaServerEngine", lambda config: Engine())
    return ["--binary", str(binary), "--model", str(model), "--output", str(output), "--limit", "2"], output


def test_report_has_hashes_and_never_overwrites_previous_output(command):
    args, output = command
    assert evaluation.main(args) == 0
    original = output.read_bytes()
    report = json.loads(original)
    assert report["complete"] and len(report["cases"]) == 2
    assert len(report["model_sha256"]) == 64
    assert report["quality_status"] == "awaiting_manual_review"
    assert str(output.parent) not in original.decode()
    assert evaluation.main(args) == 1
    assert output.read_bytes() == original


def test_interrupted_report_is_marked_incomplete_and_preserves_progress(command, monkeypatch):
    args, output = command
    real = evaluation.evaluate_case
    calls = []
    def interrupt(case, engine):
        if calls:
            raise KeyboardInterrupt()
        calls.append(case["id"])
        return real(case, engine)
    monkeypatch.setattr(evaluation, "evaluate_case", interrupt)
    assert evaluation.main(args) == 130
    report = json.loads(output.read_text())
    assert not report["complete"] and len(report["cases"]) == 1
