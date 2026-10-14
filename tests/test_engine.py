import io
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from benzie.inference.engine import InferenceCancelled, InferenceError, LlamaServerEngine
from benzie.inference.server import LocalServerProcess, ServerConfig
from benzie.inference.stream import GenerationEvent


@pytest.fixture
def engine(monkeypatch):
    process = Mock(is_running=True, failure_hint=None)
    monkeypatch.setattr("benzie.inference.engine.LocalServerProcess", Mock(return_value=process))
    result = LlamaServerEngine(ServerConfig(Path("server"), Path("model")))
    result._request = Mock(side_effect=[
        (200, {"status": "ok"}), (200, {"data": [{"id": "selected-model"}]}),
    ])
    return result, process


def test_load_then_generate_uses_selected_model_and_plain_text(engine, caplog):
    client, process = engine
    client.start()
    client._request.side_effect = None
    client._request.return_value = (200, {"choices": [{"message": {"content": "Jawaban privat"}}]})
    with caplog.at_level("INFO"):
        assert client.generate("Pesan privat", system_prompt="Perilaku dasar") == "Jawaban privat"
    payload = client._request.call_args.kwargs["payload"]
    assert payload["model"] == "selected-model"
    assert payload["messages"][1] == {"role": "user", "content": "Pesan privat"}
    assert payload["stream"] is False
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert "Pesan privat" not in caplog.text
    assert "Jawaban privat" not in caplog.text
    client.close()
    process.stop.assert_called_once()


def test_generation_requires_loaded_model(engine):
    with pytest.raises(InferenceError, match="belum siap"):
        engine[0].generate("Halo", system_prompt="Benzie")
    engine[0]._request.assert_not_called()


def test_loading_503_then_ready(engine, monkeypatch):
    client, _ = engine
    monkeypatch.setattr("benzie.inference.engine.time.sleep", lambda _: None)
    client._request.side_effect = [
        (503, None), (200, {"status": "ok"}), (200, {"data": [{"id": "model"}]}),
    ]
    client.start()
    assert client._request.call_count == 3


def test_dead_process_uses_sanitized_diagnosis_and_cleans_up(engine):
    client, process = engine
    process.is_running = False
    process.failure_hint = "Runtime gagal memuat model lokal."
    with pytest.raises(InferenceError, match="gagal memuat"):
        client.start()
    process.stop.assert_called()


def test_loading_deadline_stops_child(engine, monkeypatch):
    client, process = engine
    monkeypatch.setattr("benzie.inference.engine.time.monotonic", Mock(side_effect=[0, 121]))
    with pytest.raises(InferenceError, match="Pemuatan model melewati timeout"):
        client.start()
    process.stop.assert_called_once()


def test_other_server_on_port_is_not_used(engine):
    client, process = engine
    client._request.side_effect = [(200, {"status": "ok"}), (401, None)]
    with pytest.raises(InferenceError, match="Identitas"):
        client.start()
    process.stop.assert_called_once()


@pytest.mark.parametrize("metadata", [{}, {"data": []}, {"data": [{"id": None}]}])
def test_invalid_model_metadata_is_rejected(engine, metadata):
    client, process = engine
    client._request.side_effect = [(200, {"status": "ok"}), (200, metadata)]
    with pytest.raises(InferenceError, match="Metadata"):
        client.start()
    process.stop.assert_called_once()


@pytest.mark.parametrize("response", [(400, None), (200, {}), (200, {"choices": [{"message": {"content": ""}}]})])
def test_generation_failure_stops_child(engine, response):
    client, process = engine
    client.start()
    client._request.side_effect = None
    client._request.return_value = response
    with pytest.raises(InferenceError):
        client.generate("Halo", system_prompt="Benzie")
    process.stop.assert_called_once()


def test_generation_io_timeout_stops_child(engine):
    client, process = engine
    client.start()
    client._request.side_effect = InferenceError("timeout")
    with pytest.raises(InferenceError, match="timeout"):
        client.generate("Halo", system_prompt="Benzie")
    process.stop.assert_called_once()


def test_invalid_health_response_cleans_up(engine):
    client, process = engine
    client._request.side_effect = [(200, {"status": "unexpected"})]
    with pytest.raises(InferenceError, match="kesiapan"):
        client.start()
    process.stop.assert_called_once()


def test_empty_prompt_never_reaches_transport(engine):
    with pytest.raises(ValueError, match="kosong"):
        engine[0].generate("  ", system_prompt="Benzie")
    engine[0]._request.assert_not_called()


@pytest.mark.parametrize("options", [
    {"max_tokens": 0}, {"max_tokens": 2048}, {"temperature": float("nan")},
    {"temperature": 3}, {"timeout": 0}, {"timeout": float("inf")},
])
def test_invalid_parameters_never_send_prompt(engine, options):
    client, _ = engine
    with pytest.raises(ValueError):
        client.generate("Halo", system_prompt="Benzie", **options)
    client._request.assert_not_called()


@pytest.mark.parametrize("status,raw,expected", [
    (200, b'{"status":"ok"}', (200, {"status": "ok"})),
    (302, b"private redirect body", (302, None)),
    (500, b"private error body", (500, None)),
])
def test_transport_is_authenticated_loopback_and_does_not_follow_redirects(engine, monkeypatch, status, raw, expected):
    client, _ = engine
    response = Mock(status=status)
    response.read.return_value = raw
    connection = Mock()
    connection.getresponse.return_value = response
    factory = Mock(return_value=connection)
    monkeypatch.setattr("benzie.inference.engine.http.client.HTTPConnection", factory)
    result = LlamaServerEngine._request(client, "GET", "/health", timeout=1)
    assert result == expected
    factory.assert_called_once_with("127.0.0.1", 8081, timeout=1)
    assert connection.request.call_args.kwargs["headers"]["Authorization"] == f"Bearer {client._key}"
    connection.close.assert_called_once()


@pytest.mark.parametrize("raw", [b"invalid json", b"x" * (2 * 1024 * 1024 + 1)])
def test_bad_transport_response_closes_connection(engine, monkeypatch, raw):
    client, _ = engine
    response = Mock(status=200)
    response.read.return_value = raw
    connection = Mock()
    connection.getresponse.return_value = response
    monkeypatch.setattr("benzie.inference.engine.http.client.HTTPConnection", Mock(return_value=connection))
    with pytest.raises(InferenceError):
        LlamaServerEngine._request(client, "GET", "/health", timeout=1)
    connection.close.assert_called_once()


def test_native_diagnostics_keep_only_generic_hint():
    server = LocalServerProcess(ServerConfig(Path("server"), Path("model")))
    stream = io.BytesIO(b"prompt: private\nerror loading model: /private/model\n")
    server._read_diagnostics(stream)
    assert server.failure_hint == "Runtime gagal memuat model lokal."
    assert stream.closed


def test_bind_failure_hint_does_not_expose_native_output():
    server = LocalServerProcess(ServerConfig(Path("server"), Path("model")))
    server._read_diagnostics(io.BytesIO(b"couldn't bind HTTP server socket, port: 8081\n"))
    assert "izin jaringan sesi" in server.failure_hint
    assert "8081" not in server.failure_hint


@pytest.fixture
def streaming_transport(monkeypatch):
    response = io.BytesIO(b'data: {"choices":[{"delta":{"content":"Halo"}}]}\n\ndata: [DONE]\n\n')
    response.status = 200
    connection = Mock()
    connection.getresponse.return_value = response
    monkeypatch.setattr("benzie.inference.engine.http.client.HTTPConnection", Mock(return_value=connection))
    return connection, response


def test_complete_stream_keeps_model_ready(engine, streaming_transport):
    client, process = engine
    connection, _ = streaming_transport
    client.start()
    assert list(client.generate_stream("Halo", system_prompt="Benzie")) == [GenerationEvent("Halo")]
    process.stop.assert_not_called()
    connection.close.assert_called_once()
    payload = json.loads(connection.request.call_args.kwargs["body"])
    assert payload["stream"] is True
    assert payload["stream_options"] == {"include_usage": True}


def test_early_close_stops_generation(engine, streaming_transport):
    client, process = engine
    client.start()
    events = client.generate_stream("Halo", system_prompt="Benzie")
    assert next(events).text == "Halo"
    events.close()
    process.stop.assert_called_once()
    streaming_transport[0].close.assert_called_once()


@pytest.mark.parametrize("failure", ["disconnect", "http_error", "timeout"])
def test_stream_failure_closes_connection_and_runtime(engine, streaming_transport, failure):
    client, process = engine
    connection, response = streaming_transport
    client.start()
    if failure == "disconnect":
        response.seek(0, 2)
    elif failure == "http_error":
        response.status = 500
    else:
        connection.getresponse.side_effect = TimeoutError()
    with pytest.raises(InferenceError):
        list(client.generate_stream("Halo", system_prompt="Benzie"))
    connection.close.assert_called_once()
    process.stop.assert_called_once()


def test_cancel_before_start_never_launches_runtime(engine):
    client, process = engine
    client.cancel()
    with pytest.raises(InferenceCancelled):
        client.start()
    process.start.assert_not_called()
    process.request_stop.assert_called_once()


def test_cancel_during_health_check_closes_runtime(engine):
    client, process = engine

    def health(*args, **kwargs):
        client.cancel()
        return 200, {"status": "ok"}

    client._request.side_effect = health
    with pytest.raises(InferenceCancelled):
        client.start()
    process.stop.assert_called_once()


def test_cancel_during_metadata_io_is_not_reported_as_connection_error(engine):
    client, process = engine

    def request(method, path, **kwargs):
        if path == "/health":
            return 200, {"status": "ok"}
        client.cancel()
        raise InferenceError("socket disconnected")

    client._request.side_effect = request
    with pytest.raises(InferenceCancelled):
        client.start()
    process.stop.assert_called_once()


def test_cancel_during_blocked_stream_is_reported_as_cancel(engine, streaming_transport):
    client, process = engine
    connection, _ = streaming_transport
    client.start()

    def disconnected():
        client.cancel()
        raise OSError("socket closed")

    connection.getresponse.side_effect = disconnected
    with pytest.raises(InferenceCancelled):
        list(client.generate_stream("Halo", system_prompt="Benzie"))
    process.request_stop.assert_called_once()
    process.stop.assert_called_once()
    connection.close.assert_called_once()
