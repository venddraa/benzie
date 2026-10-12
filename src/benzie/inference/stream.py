"""Parser SSE llama-server dan metadata generation; tanpa menyimpan teks."""

from dataclasses import dataclass
import json
import math


class StreamError(Exception):
    pass


@dataclass(frozen=True)
class GenerationEvent:
    text: str = ""
    completion_tokens: int | None = None
    decode_tokens_per_second: float | None = None


def parse_event(data: dict) -> GenerationEvent:
    try:
        if "error" in data:
            raise ValueError()
        choices = data.get("choices", [])
        text = choices[0].get("delta", {}).get("content", "") if choices else ""
        if text is None:
            text = ""
        if not isinstance(text, str):
            raise ValueError()
        tokens = (data.get("usage") or {}).get("completion_tokens")
        speed = (data.get("timings") or {}).get("predicted_per_second")
        if tokens is not None and (type(tokens) is not int or tokens < 0):
            raise ValueError()
        if speed is not None and (isinstance(speed, bool) or not isinstance(speed, (int, float)) or not math.isfinite(speed) or speed < 0):
            raise ValueError()
        return GenerationEvent(text, tokens, speed)
    except (KeyError, IndexError, TypeError, AttributeError, ValueError) as error:
        raise StreamError("Event streaming runtime tidak valid.") from error


def iter_events(response):
    """Baca event lengkap; EOF tanpa DONE bukan generation sukses."""
    parts = []
    total = 0
    saw_text = False
    while True:
        line = response.readline(65537)
        if not line:
            raise StreamError("Streaming terputus sebelum selesai.")
        total += len(line)
        if len(line) > 65536 or total > 2 * 1024 * 1024:
            raise StreamError("Respons streaming terlalu besar.")
        try:
            line = line.decode("utf-8").rstrip("\r\n")
            if line.startswith("data:"):
                parts.append(line[5:].removeprefix(" "))
            elif not line and parts:
                data = "\n".join(parts)
                parts.clear()
                if data == "[DONE]":
                    if not saw_text:
                        raise StreamError("Respons streaming kosong.")
                    return
                event = parse_event(json.loads(data))
                saw_text = saw_text or bool(event.text)
                yield event
        except (UnicodeError, ValueError) as error:
            raise StreamError("JSON streaming runtime tidak valid.") from error
