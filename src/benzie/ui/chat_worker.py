"""Jembatan thread Qt ke core; engine dibuat dan dipakai di thread worker."""

from contextlib import closing
import logging

from PySide6.QtCore import QThread, Signal

from benzie.core.chat import ChatService
from benzie.inference.engine import InferenceCancelled, InferenceError
from benzie.inference.server import RuntimeStartError

logger = logging.getLogger(__name__)


class ChatWorker(QThread):
    phase = Signal(str)
    chunk = Signal(str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, service: ChatService, prompt: str, parent=None) -> None:
        super().__init__(parent)
        self._request = service.new_request(prompt)

    def cancel(self) -> None:
        self._request.cancel()

    def run(self) -> None:
        try:
            with closing(self._request.events()) as events:
                for event in events:
                    if event.kind == "text":
                        self.chunk.emit(event.text)
                    else:
                        self.phase.emit(event.kind)
        except InferenceCancelled:
            self.cancelled.emit()
        except (InferenceError, RuntimeStartError, ValueError) as error:
            self.failed.emit(str(error))
        except Exception as error:
            logger.error("Chat gagal (%s)", type(error).__name__)
            self.failed.emit("Terjadi kesalahan saat memproses pesan. Silakan coba kembali.")
