import io
import json

import pytest

from benzie.inference.stream import StreamError, iter_events, parse_event


def wire(*events):
    return io.BytesIO("".join(f"data: {json.dumps(event)}\n\n" for event in events).encode() + b"data: [DONE]\n\n")


def test_text_metadata_and_done_do_not_count_chunks_as_tokens():
    events = list(iter_events(wire(
        {"choices": [{"delta": {"role": "assistant"}}]},
        {"choices": [{"delta": {"content": "Halo"}}]},
        {"choices": [{"delta": {"content": " dunia"}}]},
        {"choices": [], "usage": {"completion_tokens": 3}, "timings": {"predicted_per_second": 15.5}},
    )))
    assert "".join(event.text for event in events) == "Halo dunia"
    assert events[-1].completion_tokens == 3
    assert events[-1].decode_tokens_per_second == 15.5


def test_multiline_data_crlf_and_comments():
    response = io.BytesIO(b': keepalive\r\ndata: {"choices":\r\ndata: [{"delta":{"content":"Hi"}}]}\r\n\r\ndata: [DONE]\r\n\r\n')
    assert list(iter_events(response))[0].text == "Hi"


@pytest.mark.parametrize("raw", [
    b'data: {"choices": [{"delta": {"content":"Hi"}}]}\n\n',
    b"data: [DONE]\n\n", b"data: invalid-json\n\n",
    b"data: \xff\n\n", b"data: " + b"x" * 65536 + b"\n\n",
])
def test_truncated_empty_malformed_or_oversized_stream_is_rejected(raw):
    with pytest.raises(StreamError):
        list(iter_events(io.BytesIO(raw)))


@pytest.mark.parametrize("data", [
    {"error": {"message": "private content"}},
    {"choices": [{"delta": {"content": 123}}]},
    {"usage": {"completion_tokens": True}},
    {"timings": {"predicted_per_second": float("nan")}},
])
def test_invalid_event_has_generic_error(data):
    with pytest.raises(StreamError) as error:
        parse_event(data)
    assert "private content" not in str(error.value)
