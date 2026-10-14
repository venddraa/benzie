"""Satu pesan teks lewat engine lokal, tanpa Qt atau persistence percakapan."""

from collections.abc import Callable, Generator
from contextlib import closing
from dataclasses import dataclass
from typing import Literal
import threading

from benzie.core.prompts import SYSTEM_PROMPT
from benzie.inference.engine import InferenceCancelled, InferenceEngine


@dataclass(frozen=True)
class ChatEvent:
    kind: Literal["loading", "generating", "text"]
    text: str = ""


class ChatService:
    def __init__(self, engine_factory: Callable[[], InferenceEngine]) -> None:
        self._engine_factory = engine_factory

    def reply(self, prompt: str) -> Generator[ChatEvent, None, None]:
        yield from self.new_request(prompt).events()

    def new_request(self, prompt: str) -> "ChatRequest":
        return ChatRequest(self._engine_factory, prompt)


class ChatRequest:
    """Handle per request: cancellation sebelum start maupun saat I/O aktif."""

    def __init__(self, engine_factory: Callable[[], InferenceEngine], prompt: str) -> None:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Pesan tidak boleh kosong.")
        self._engine_factory = engine_factory
        self._prompt = prompt
        self._cancelled = threading.Event()
        self._lock = threading.Lock()
        self._engine: InferenceEngine | None = None
        self._history = None

    def set_history(self, messages: list[dict[str, str]]) -> None:
        """Dipanggil worker sebelum events; snapshot konteks percakapan aktif."""
        self._history = [dict(message) for message in messages]

    def cancel(self) -> None:
        self._cancelled.set()
        with self._lock:
            if self._engine is not None:
                self._engine.cancel()

    def _check_cancelled(self) -> None:
        if self._cancelled.is_set():
            raise InferenceCancelled("Request dibatalkan.")

    def events(self) -> Generator[ChatEvent, None, None]:
        self._check_cancelled()
        # Publikasi engine dan cancellation disinkronkan; factory tidak start I/O.
        with self._lock:
            self._check_cancelled()
            engine = self._engine_factory()
            self._engine = engine
        try:
            yield ChatEvent("loading")
            self._check_cancelled()
            engine.start(timeout=30)
            self._check_cancelled()
            yield ChatEvent("generating")
            self._check_cancelled()
            with closing(engine.generate_stream(
                self._prompt, system_prompt=SYSTEM_PROMPT, max_tokens=256, timeout=30,
                **({"history": self._history} if self._history is not None else {}),
            )) as events:
                for event in events:
                    self._check_cancelled()
                    if event.text:
                        yield ChatEvent("text", event.text)
            self._check_cancelled()
        except Exception:
            self._check_cancelled()
            raise
        finally:
            with self._lock:
                self._engine = None
            engine.close()
