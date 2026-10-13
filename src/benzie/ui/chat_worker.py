"""Jembatan thread Qt ke core; engine dibuat dan dipakai di thread worker."""

from contextlib import closing
import logging

from PySide6.QtCore import QThread, Signal

from benzie.core.chat import ChatService
from benzie.inference.engine import InferenceError
from benzie.inference.server import RuntimeStartError

logger = logging.getLogger(__name__)


class ChatWorker(QThread):
    phase = Signal(str)
    chunk = Signal(str)
    failed = Signal(str)

    def __init__(self, service: ChatService, prompt: str, parent=None) -> None:
        super().__init__(parent)
        self._service = service
        self._prompt = prompt

    def run(self) -> None:
        try:
            with closing(self._service.reply(self._prompt)) as events:
                for event in events:
                    if event.kind == "text":
                        self.chunk.emit(event.text)
                    else:
                        self.phase.emit(event.kind)
        except (InferenceError, RuntimeStartError, ValueError) as error:
            self.failed.emit(str(error))
        except Exception as error:
            logger.error("Chat gagal (%s)", type(error).__name__)
            self.failed.emit("Terjadi kesalahan saat memproses pesan. Silakan coba kembali.")
