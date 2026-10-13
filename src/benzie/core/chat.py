"""Satu pesan teks lewat engine lokal, tanpa Qt atau persistence percakapan."""

from collections.abc import Callable, Generator
from contextlib import closing
from dataclasses import dataclass
from typing import Literal

from benzie.core.prompts import SYSTEM_PROMPT
from benzie.inference.engine import InferenceEngine


@dataclass(frozen=True)
class ChatEvent:
    kind: Literal["loading", "generating", "text"]
    text: str = ""


class ChatService:
    def __init__(self, engine_factory: Callable[[], InferenceEngine]) -> None:
        self._engine_factory = engine_factory

    def reply(self, prompt: str) -> Generator[ChatEvent, None, None]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Pesan tidak boleh kosong.")
        engine = self._engine_factory()
        try:
            yield ChatEvent("loading")
            engine.start(timeout=30)
            yield ChatEvent("generating")
            with closing(engine.generate_stream(
                prompt, system_prompt=SYSTEM_PROMPT, max_tokens=256, timeout=30,
            )) as events:
                for event in events:
                    if event.text:
                        yield ChatEvent("text", event.text)
        finally:
            engine.close()
