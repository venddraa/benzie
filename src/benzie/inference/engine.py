"""Adapter teks sinkron melalui HTTP loopback; tanpa proxy, redirect, atau cloud."""

import http.client
from collections.abc import Generator
import json
import logging
import math
import secrets
import time
import threading
from typing import Protocol

from benzie.inference.server import LocalServerProcess, ServerConfig
from benzie.inference.stream import GenerationEvent, StreamError, iter_events

logger = logging.getLogger(__name__)


class InferenceError(Exception):
    """Kegagalan pemuatan/generation yang bisa ditampilkan pemanggil."""


class InferenceCancelled(InferenceError):
    """Request dibatalkan pengguna, bukan kegagalan model."""


class InferenceEngine(Protocol):
    def start(self, *, timeout: float = 120) -> None: ...
    def generate(self, prompt: str, *, system_prompt: str, max_tokens: int = 128,
                 temperature: float = 0.7, timeout: float = 120) -> str: ...
    def generate_stream(self, prompt: str, *, system_prompt: str, max_tokens: int = 128,
                        temperature: float = 0.7, timeout: float = 120,
                        history: list[dict[str, str]] | None = None) -> Generator[GenerationEvent, None, None]: ...
    def close(self) -> None: ...
    def cancel(self) -> None: ...


def _valid_timeout(timeout: float) -> None:
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Timeout harus berupa angka positif dan terbatas.")


class LlamaServerEngine:
    def __init__(self, config: ServerConfig) -> None:
        self._config = config
        self._key = secrets.token_urlsafe(32)
        self._server = LocalServerProcess(config, api_key=self._key)
        self._model_id: str | None = None
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        """Boleh dipanggil lintas thread; hanya flag dan sinyal ke child."""
        self._cancelled.set()
        logger.info("Pembatalan runtime diminta")
        self._server.request_stop()

    def _check_cancelled(self) -> None:
        if self._cancelled.is_set():
            raise InferenceCancelled("Request dibatalkan.")

    @property
    def process_id(self) -> int | None:
        return self._server.process_id

    def _request(self, method: str, path: str, *, timeout: float, payload=None):
        # HTTPConnection tidak memakai proxy environment atau mengikuti redirect.
        connection = http.client.HTTPConnection("127.0.0.1", self._config.port, timeout=timeout)
        try:
            body = None if payload is None else json.dumps(payload).encode("utf-8")
            connection.request(method, path, body=body, headers={
                "Content-Type": "application/json", "Authorization": f"Bearer {self._key}",
            })
            response = connection.getresponse()
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise InferenceError("Respons runtime terlalu besar.")
            # Jangan tampilkan body error native karena dapat memuat isi prompt.
            if response.status != 200:
                return response.status, None
            return response.status, json.loads(raw)
        except (TimeoutError, OSError, http.client.HTTPException) as error:
            raise InferenceError("Koneksi runtime gagal atau melewati timeout.") from error
        except (ValueError, UnicodeError) as error:
            raise InferenceError("Respons JSON runtime tidak valid.") from error
        finally:
            connection.close()

    def start(self, *, timeout: float = 120) -> None:
        _valid_timeout(timeout)
        self._check_cancelled()
        self._server.start()
        self._model_id = None
        deadline = time.monotonic() + timeout
        try:
            while time.monotonic() < deadline:
                self._check_cancelled()
                if not self._server.is_running:
                    self._server.stop()  # Tunggu reader diagnosis selesai.
                    raise InferenceError(self._server.failure_hint or "Runtime berhenti saat memuat model.")
                request_timeout = min(1.0, max(0.001, deadline - time.monotonic()))
                try:
                    status, health = self._request("GET", "/health", timeout=request_timeout)
                except InferenceError:
                    self._check_cancelled()
                    time.sleep(min(0.1, max(0, deadline - time.monotonic())))
                    continue
                self._check_cancelled()
                if status not in (200, 503):
                    raise InferenceError(f"Health check ditolak runtime (HTTP {status}).")
                if status == 200:
                    if not isinstance(health, dict) or health.get("status") != "ok":
                        raise InferenceError("Status kesiapan runtime tidak valid.")
                    status, models = self._request("GET", "/v1/models", timeout=request_timeout)
                    self._check_cancelled()
                    if status != 200:
                        raise InferenceError("Identitas runtime lokal tidak dapat diverifikasi.")
                    try:
                        model_id = models["data"][0]["id"]
                        if not isinstance(model_id, str) or not model_id:
                            raise ValueError()
                    except (KeyError, IndexError, TypeError, ValueError) as error:
                        raise InferenceError("Metadata model runtime tidak valid.") from error
                    if not self._server.is_running:
                        raise InferenceError("Runtime berhenti setelah health check.")
                    self._model_id = model_id
                    logger.info("Model lokal siap")
                    return
                time.sleep(min(0.1, max(0, deadline - time.monotonic())))
            raise InferenceError("Pemuatan model melewati timeout.")
        except BaseException:
            self.close()
            self._check_cancelled()
            raise

    def _generation_payload(self, prompt: str, system_prompt: str, max_tokens: int,
                            temperature: float, timeout: float) -> dict:
        _valid_timeout(timeout)
        self._check_cancelled()
        if not isinstance(prompt, str) or not prompt.strip() or not isinstance(system_prompt, str):
            raise ValueError("Prompt harus berupa teks dan tidak boleh kosong.")
        if type(max_tokens) is not int or not 1 <= max_tokens < self._config.context_size:
            raise ValueError("Max tokens harus positif dan lebih kecil dari context size.")
        if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise ValueError("Temperature harus berada pada rentang 0–2.")
        if self._model_id is None or not self._server.is_running:
            raise InferenceError("Model lokal belum siap.")
        return {
            "model": self._model_id,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": temperature, "stream": False,
            "chat_template_kwargs": {"enable_thinking": False},
        }

    def generate(self, prompt: str, *, system_prompt: str, max_tokens: int = 128,
                 temperature: float = 0.7, timeout: float = 120) -> str:
        payload = self._generation_payload(prompt, system_prompt, max_tokens, temperature, timeout)
        logger.info("Generation dimulai")
        try:
            status, data = self._request("POST", "/v1/chat/completions", timeout=timeout, payload=payload)
            self._check_cancelled()
            if status != 200:
                raise InferenceError(f"Generation ditolak runtime (HTTP {status}).")
            try:
                content = data["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise ValueError()
            except (KeyError, IndexError, TypeError, ValueError) as error:
                raise InferenceError("Respons teks runtime tidak valid atau kosong.") from error
        except InferenceError:
            # Tutup proses supaya generation gagal/timeout tidak terus berjalan.
            self.close()
            self._check_cancelled()
            raise
        logger.info("Generation selesai")
        return content

    def _conversation_payload(self, payload: dict, history: list[dict[str, str]], timeout: float) -> dict:
        if not isinstance(history, list) or len(history) % 2:
            raise ValueError("Konteks harus berisi pasangan pesan selesai.")
        messages = []
        for index, message in enumerate(history):
            role = "user" if index % 2 == 0 else "assistant"
            if (not isinstance(message, dict) or message.get("role") != role
                    or not isinstance(message.get("content"), str) or not message["content"].strip()):
                raise ValueError("Pesan konteks tidak valid.")
            messages.append({"role": role, "content": message["content"]})
        payload["messages"] = [payload["messages"][0], *messages, payload["messages"][-1]]
        if len(json.dumps(payload).encode("utf-8")) > 1024 * 1024:
            raise InferenceError("Percakapan terlalu panjang. Buat percakapan baru atau pendekkan pesan.")
        # Gunakan formatter dan tokenizer runtime yang sama dengan generation.
        self._check_cancelled()
        status, template = self._request("POST", "/apply-template", timeout=timeout, payload=payload)
        self._check_cancelled()
        if status != 200 or not isinstance(template, dict) or not isinstance(template.get("prompt"), str):
            raise InferenceError("Format konteks runtime tidak dapat diverifikasi.")
        status, result = self._request("POST", "/tokenize", timeout=timeout, payload={
            "content": template["prompt"], "add_special": True, "parse_special": True,
        })
        self._check_cancelled()
        tokens = result.get("tokens") if isinstance(result, dict) else None
        if status != 200 or not isinstance(tokens, list) or not tokens or any(type(t) is not int for t in tokens):
            raise InferenceError("Jumlah token konteks runtime tidak dapat diverifikasi.")
        # Cadangan kecil untuk token khusus; jangan mengandalkan context shifting.
        if len(tokens) + payload["max_tokens"] + 32 > self._config.context_size:
            raise InferenceError("Konteks percakapan penuh. Buat percakapan baru atau pendekkan pesan.")
        return payload

    def generate_stream(self, prompt: str, *, system_prompt: str, max_tokens: int = 128,
                        temperature: float = 0.7, timeout: float = 120,
                        history: list[dict[str, str]] | None = None) -> Generator[GenerationEvent, None, None]:
        """Iterator GenerationEvent; pemanggil harus close iterator bila berhenti dini.

        Early close/error menghentikan runtime. Iterasi sukses membiarkan model
        siap untuk request berikutnya. Timeout berlaku per operasi I/O.
        """
        payload = self._generation_payload(prompt, system_prompt, max_tokens, temperature, timeout)
        if history is not None:
            try:
                payload = self._conversation_payload(payload, history, timeout)
            except Exception:
                self.close()
                self._check_cancelled()
                raise
        payload.update(stream=True, stream_options={"include_usage": True})
        connection = http.client.HTTPConnection("127.0.0.1", self._config.port, timeout=timeout)
        completed = False
        logger.info("Generation streaming dimulai")
        try:
            connection.request("POST", "/v1/chat/completions", body=json.dumps(payload).encode("utf-8"), headers={
                "Content-Type": "application/json", "Authorization": f"Bearer {self._key}",
            })
            response = connection.getresponse()
            self._check_cancelled()
            if response.status != 200:
                raise InferenceError(f"Streaming ditolak runtime (HTTP {response.status}).")
            for event in iter_events(response):
                self._check_cancelled()
                yield event
            self._check_cancelled()
            completed = True
            logger.info("Generation streaming selesai")
        except (OSError, http.client.HTTPException, StreamError) as error:
            self._check_cancelled()
            raise InferenceError("Streaming runtime gagal, terputus, atau melewati timeout.") from error
        finally:
            connection.close()
            if not completed:
                self.close()

    def close(self) -> None:
        self._model_id = None
        self._server.stop()
