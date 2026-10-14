from dataclasses import replace
import subprocess
import sys
from unittest.mock import Mock

import pytest

from benzie.inference.server import LocalServerProcess, RuntimeStartError, ServerConfig


@pytest.fixture
def config(tmp_path):
    executable = tmp_path / "llama server"
    executable.touch()
    executable.chmod(0o700)
    model = tmp_path / "model ; literal.gguf"
    model.write_bytes(b"GGUF")  # Header fixture, bukan model untuk inference.
    return ServerConfig(executable, model)


@pytest.fixture
def spawn(monkeypatch):
    process = Mock()
    process.poll.return_value = None
    process.wait.return_value = 0
    process.stderr = None
    factory = Mock(return_value=process)
    monkeypatch.setattr("benzie.inference.server.subprocess.Popen", factory)
    return factory, process


def test_launch_is_local_cpu_only_and_does_not_inherit_llama_overrides(config, spawn, monkeypatch):
    factory, _ = spawn
    monkeypatch.setenv("LLAMA_ARG_MODEL_URL", "https://example.invalid/model")
    monkeypatch.setenv("LLAMA_ARG_AGENT", "1")
    monkeypatch.setenv("HF_TOKEN", "test-token")
    server = LocalServerProcess(config)
    server.start()
    args, options = factory.call_args
    command = args[0]
    assert command[command.index("--model") + 1] == str(config.model)
    assert command[command.index("--host") + 1] == "127.0.0.1"
    assert command[command.index("--n-gpu-layers") + 1] == "0"
    assert {"--offline", "--no-agent", "--no-webui", "--no-mmproj"} <= set(command)
    assert options["shell"] is False
    assert not any(key.startswith("LLAMA_") for key in options["env"])
    assert "HF_TOKEN" not in options["env"]
    assert options["stderr"] == subprocess.PIPE
    assert server.is_running
    server.stop()


@pytest.mark.parametrize("field,value", [
    ("port", 0), ("port", 65536), ("port", True),
    ("context_size", 0), ("threads", -1), ("threads", 1.5),
])
def test_invalid_parameters_do_not_spawn(config, spawn, field, value):
    with pytest.raises(RuntimeStartError, match="tidak valid"):
        LocalServerProcess(replace(config, **{field: value})).start()
    spawn[0].assert_not_called()


@pytest.mark.parametrize("problem", ["binary_missing", "not_executable", "model_missing", "invalid_gguf"])
def test_invalid_local_files_do_not_spawn(config, spawn, problem):
    if problem == "binary_missing":
        config.executable.unlink()
    elif problem == "not_executable":
        config.executable.chmod(0o600)
    elif problem == "model_missing":
        config.model.unlink()
    else:
        config.model.write_bytes(b"not a model")
    with pytest.raises(RuntimeStartError):
        LocalServerProcess(config).start()
    spawn[0].assert_not_called()


def test_os_spawn_failure_is_readable(config, spawn):
    spawn[0].side_effect = OSError("exec format error")
    with pytest.raises(RuntimeStartError, match="gagal dijalankan"):
        LocalServerProcess(config).start()


def test_duplicate_start_rejected_and_stop_is_idempotent(config, spawn):
    factory, process = spawn
    server = LocalServerProcess(config)
    server.stop()
    server.start()
    with pytest.raises(RuntimeStartError, match="sudah berjalan"):
        server.start()
    factory.assert_called_once()
    server.stop()
    server.stop()
    process.terminate.assert_called_once()
    assert not server.is_running


def test_hung_child_is_killed_then_reaped(config, spawn):
    _, process = spawn
    process.wait.side_effect = [subprocess.TimeoutExpired("llama-server", 3), 0]
    server = LocalServerProcess(config)
    server.start()
    server.stop()
    process.kill.assert_called_once()
    assert process.wait.call_count == 2
    assert not server.is_running


def test_exited_child_is_not_reported_running_and_can_restart(config, spawn):
    factory, process = spawn
    server = LocalServerProcess(config)
    server.start()
    process.poll.return_value = 1
    assert not server.is_running
    server.stop()
    process.terminate.assert_not_called()
    process.poll.return_value = None
    server.start()
    assert factory.call_count == 2
    server.stop()


def test_failed_stop_can_be_retried(config, spawn):
    _, process = spawn
    process.wait.side_effect = subprocess.TimeoutExpired("llama-server", 3)
    server = LocalServerProcess(config)
    server.start()
    with pytest.raises(RuntimeStartError, match="dihentikan"):
        server.stop()
    assert server.is_running
    process.wait.side_effect = None
    server.stop()
    assert not server.is_running


def test_request_stop_signals_owned_process_without_waiting(config, spawn):
    _, process = spawn
    server = LocalServerProcess(config)
    server.request_stop()
    process.kill.assert_not_called()
    server.start()
    server.request_stop()
    process.kill.assert_called_once()
    process.wait.assert_not_called()
    process.poll.return_value = -9
    server.stop()
    process.wait.assert_called_once()


def test_request_stop_handles_process_exit_race(config, spawn):
    _, process = spawn
    server = LocalServerProcess(config)
    server.start()
    process.kill.side_effect = ProcessLookupError()
    server.request_stop()
    process.poll.return_value = 0
    server.stop()


def test_cancel_reaps_real_owned_child_without_network(config, monkeypatch):
    # Child nyata untuk verifikasi OS kill/wait; bukan inference/model palsu.
    monkeypatch.setattr(ServerConfig, "command", lambda self: [sys.executable, "-c", "import time; time.sleep(30)"])
    server = LocalServerProcess(config)
    try:
        server.start()
        process = server._process
        server.request_stop()
        server.stop()
        assert process.poll() is not None
        assert server.process_id is None
    finally:
        server.stop()
