from unittest.mock import Mock

import pytest

from benzie.core.chat import ChatService
from benzie.inference.engine import InferenceError
from benzie.inference.stream import GenerationEvent


@pytest.fixture
def engine():
    result = Mock()
    result.generate_stream.return_value = (event for event in [
        GenerationEvent("Ha"), GenerationEvent("lo"), GenerationEvent(completion_tokens=2),
    ])
    return result


def test_reply_orders_phases_text_and_cleanup(engine):
    service = ChatService(lambda: engine)
    events = list(service.reply("Halo"))
    assert [event.kind for event in events] == ["loading", "generating", "text", "text"]
    assert "".join(event.text for event in events) == "Halo"
    assert engine.generate_stream.call_args.args == ("Halo",)
    assert "memory" in engine.generate_stream.call_args.kwargs["system_prompt"]
    engine.close.assert_called_once()


def test_each_reply_owns_a_new_engine(engine):
    factory = Mock(return_value=engine)
    service = ChatService(factory)
    list(service.reply("satu"))
    engine.generate_stream.return_value = (event for event in [GenerationEvent("dua")])
    list(service.reply("dua"))
    assert factory.call_count == 2
    assert engine.close.call_count == 2


@pytest.mark.parametrize("phase", ["load", "generation"])
def test_failure_still_closes_engine(engine, phase):
    if phase == "load":
        engine.start.side_effect = InferenceError("model gagal")
    else:
        engine.generate_stream.side_effect = InferenceError("generation gagal")
    with pytest.raises(InferenceError):
        list(ChatService(lambda: engine).reply("Halo"))
    engine.close.assert_called_once()


def test_closing_reply_early_closes_stream_and_engine(engine):
    stream = Mock()
    stream.__iter__ = Mock(return_value=iter([GenerationEvent("Ha"), GenerationEvent("lo")]))
    engine.generate_stream.return_value = stream
    reply = ChatService(lambda: engine).reply("Halo")
    next(reply)
    next(reply)
    next(reply)
    reply.close()
    stream.close.assert_called_once()
    engine.close.assert_called_once()


def test_empty_message_does_not_create_engine():
    factory = Mock()
    with pytest.raises(ValueError):
        list(ChatService(factory).reply("  "))
    factory.assert_not_called()
