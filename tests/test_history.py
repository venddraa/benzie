import pytest

from benzie.core.chat import ChatService
from benzie.core.history import HistoryService
from benzie.inference.engine import InferenceCancelled, InferenceError
from benzie.inference.stream import GenerationEvent
from benzie.persistence.database import DatabaseError, initialize_database


class Engine:
    closed = False
    def start(self, **kwargs): pass
    def close(self): self.closed = True
    def cancel(self): pass
    def generate_stream(self, prompt, **kwargs):
        yield GenerationEvent("Halo")


def history(tmp_path, engine):
    path = tmp_path / "history.sqlite3"
    initialize_database(path)
    service = HistoryService(path, ChatService(lambda: engine))
    return service, service.new_conversation().id


def test_request_saved_after_cleanup(tmp_path):
    engine = Engine()
    service, cid = history(tmp_path, engine)
    list(service.new_request("Hai", cid).events())
    assert engine.closed
    assert [(m.role, m.content, m.status) for m in service.messages(cid)] == [
        ("user", "Hai", "completed"), ("assistant", "Halo", "completed")]


def test_cancel_keeps_partial_response(tmp_path):
    service, cid = history(tmp_path, Engine())
    request = service.new_request("Hai", cid)
    events = request.events()
    for event in events:
        if event.kind == "text":
            request.cancel()
            break
    with pytest.raises(InferenceCancelled):
        next(events)
    assert service.messages(cid)[-1].status == "cancelled"
    assert service.messages(cid)[-1].content == "Halo"


def test_cancel_before_start_is_persisted(tmp_path):
    service, cid = history(tmp_path, Engine())
    request = service.new_request("Hai", cid)
    request.cancel()
    with pytest.raises(InferenceCancelled):
        list(request.events())
    assert service.messages(cid)[-1].status == "cancelled"


def test_inference_failure_saved_without_raw_exception(tmp_path):
    class Broken(Engine):
        def start(self, **kwargs): raise InferenceError("private detail")
    service, cid = history(tmp_path, Broken())
    with pytest.raises(InferenceError):
        list(service.new_request("Hai", cid).events())
    message = service.messages(cid)[-1]
    assert message.status == "failed"
    assert message.content == ""


def test_input_save_failure_prevents_inference(tmp_path, monkeypatch):
    engine = Engine()
    service, cid = history(tmp_path, engine)
    def fail(*args, **kwargs): raise DatabaseError("disk error")
    monkeypatch.setattr(service.store, "append_message", fail)
    with pytest.raises(DatabaseError):
        list(service.new_request("Hai", cid).events())
    assert not engine.closed


def test_output_save_failure_reported_after_engine_cleanup(tmp_path, monkeypatch):
    engine = Engine()
    service, cid = history(tmp_path, engine)
    append = service.store.append_message
    def fail(cid, role, *args, **kwargs):
        if role == "assistant": raise DatabaseError("disk error")
        return append(cid, role, *args, **kwargs)
    monkeypatch.setattr(service.store, "append_message", fail)
    with pytest.raises(DatabaseError):
        list(service.new_request("Hai", cid).events())
    assert engine.closed
    assert len(service.messages(cid)) == 1
