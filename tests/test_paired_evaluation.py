import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def pair_runner(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts/evaluate_model_pair.py"
    monkeypatch.syspath_prepend(str(script.parent))
    spec = importlib.util.spec_from_file_location("evaluate_model_pair", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.ServerConfig, "command", lambda self: [])
    return module, tmp_path / "new experiment"


def fake_evaluator(module, calls):
    def evaluate(args):
        model = Path(args[args.index("--model") + 1])
        output = Path(args[args.index("--output") + 1])
        calls.append(model.name)
        ids = [case["id"] for case in json.loads(module.SUITE.read_text())["cases"][:2]]
        report = {key: "fixed" for key in module.CONTROLS}
        report.update(complete=True, selected_cases=2, model_sha256=model.name, model_file=model.name,
                      system_memory_before={"MemAvailable": 100, "SwapFree": 50},
                      cases=[{"id": id, "status": "generated", "load_seconds": 1,
                              "ttft_seconds": 0.5, "decode_tokens_per_second": 20,
                              "peak_rss_bytes": 1000} for id in ids])
        output.write_text(json.dumps(report))
        return 0
    return evaluate


def test_sequential_order_alternates_and_preserves_per_run_memory(pair_runner):
    module, output = pair_runner
    calls = []
    assert module.run_pair(Path("server"), [Path("a"), Path("b")], output,
                           pairs=3, limit=2, evaluator=fake_evaluator(module, calls)) == 0
    assert calls == ["a", "b", "b", "a", "a", "b"]
    summary = json.loads((output / "summary.json").read_text())
    assert summary["complete"] and len(summary["runs"]) == 6
    assert summary["quality_status"] == "manual_review_required"
    assert all(row["system_memory_before"]["MemAvailable"] == 100 for row in summary["runs"])


@pytest.mark.parametrize("exit_code", [1, 130])
def test_failure_stops_without_starting_second_model(pair_runner, exit_code):
    module, output = pair_runner
    calls = []
    def fail(args):
        calls.append(args)
        return exit_code
    assert module.run_pair(Path("server"), [Path("a"), Path("b")], output,
                           limit=2, evaluator=fail) == exit_code
    assert len(calls) == 1
    summary = json.loads((output / "summary.json").read_text())
    assert not summary["complete"] and summary["exit_code"] == exit_code


def test_changed_controls_do_not_produce_complete_comparison(pair_runner):
    module, output = pair_runner
    calls = []
    base = fake_evaluator(module, calls)
    def changed(args):
        base(args)
        if len(calls) == 2:
            path = Path(args[args.index("--output") + 1])
            data = json.loads(path.read_text())
            data["runtime_sha256"] = "different"
            path.write_text(json.dumps(data))
        return 0
    with pytest.raises(ValueError, match="berubah"):
        module.run_pair(Path("server"), [Path("a"), Path("b")], output, limit=2, evaluator=changed)
    assert not json.loads((output / "summary.json").read_text())["complete"]


def test_existing_experiment_is_never_overwritten(pair_runner):
    module, output = pair_runner
    output.mkdir()
    sentinel = output / "summary.json"
    sentinel.write_text("keep")
    with pytest.raises(FileExistsError):
        module.run_pair(Path("server"), [Path("a"), Path("b")], output, evaluator=lambda args: 0)
    assert sentinel.read_text() == "keep"


def test_same_model_is_rejected_before_creating_output(pair_runner):
    module, output = pair_runner
    with pytest.raises(ValueError, match="berbeda"):
        module.run_pair(Path("server"), [Path("a"), Path("a")], output)
    assert not output.exists()


def test_interruption_marks_summary_incomplete(pair_runner):
    module, output = pair_runner
    def interrupt(args): raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        module.run_pair(Path("server"), [Path("a"), Path("b")], output, evaluator=interrupt)
    report = json.loads((output / "summary.json").read_text())
    assert not report["complete"] and report["exit_code"] == 130


def test_missing_cases_rejected_even_if_child_returns_success(pair_runner):
    module, output = pair_runner
    calls = []
    base = fake_evaluator(module, calls)
    def incomplete(args):
        base(args)
        path = Path(args[args.index("--output") + 1])
        data = json.loads(path.read_text())
        data["cases"].pop()
        path.write_text(json.dumps(data))
        return 0
    with pytest.raises(ValueError, match="tidak lengkap"):
        module.run_pair(Path("server"), [Path("a"), Path("b")], output, limit=2, evaluator=incomplete)
    assert not json.loads((output / "summary.json").read_text())["complete"]
