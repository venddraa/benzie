"""Presentasi chat teks; SQL dan runtime ditangani di luar widget."""

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from benzie.core.chat import ChatService
from benzie.core.startup import StartupState
from benzie.ui.chat_worker import ChatWorker
from benzie.inference.server import RuntimeStartError


class MainWindow(QMainWindow):
    def __init__(self, state: StartupState, *, chat_service: ChatService | None = None,
                 model_name: str | None = None) -> None:
        super().__init__()
        self._service = chat_service
        self._worker: ChatWorker | None = None
        self._close_pending = False
        self._cancelling = False
        self.setWindowTitle("Benzie")
        self.resize(720, 480)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Benzie")
        font = title.font()
        font.setPointSize(20)
        title.setFont(font)
        layout.addWidget(title)

        description = QLabel("Setiap pesan dijawab terpisah. Riwayat belum tersimpan.")
        description.setWordWrap(True)
        layout.addWidget(description)
        model = QLabel(f"Model: {model_name}" if model_name else "Belum ada model dipilih.")
        model.setTextFormat(Qt.TextFormat.PlainText)
        model.setWordWrap(True)
        layout.addWidget(model)

        self.chat_history = QPlainTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history, 1)

        row = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Tulis pesan…")
        self.send_button = QPushButton("Kirim")
        self.cancel_button = QPushButton("Batal")
        self.cancel_button.setEnabled(False)
        row.addWidget(self.message_input, 1)
        row.addWidget(self.send_button)
        row.addWidget(self.cancel_button)
        layout.addLayout(row)
        self.send_button.clicked.connect(self._send)
        self.cancel_button.clicked.connect(self._cancel)
        self.message_input.returnPressed.connect(self._send)
        self.message_input.textChanged.connect(self._update_send)
        self.message_input.setEnabled(self._service is not None)
        self._update_send()

        self.setCentralWidget(content)
        self.statusBar().showMessage(f"SQLite siap · versi skema {state.schema_version}")

    @Slot()
    def _update_send(self) -> None:
        self.send_button.setEnabled(
            self._service is not None and self._worker is None
            and bool(self.message_input.text().strip()) and not self._close_pending
        )

    @Slot()
    def _send(self) -> None:
        prompt = self.message_input.text().strip()
        if self._service is None or self._worker is not None or not prompt or self._close_pending:
            return
        self.chat_history.appendPlainText(f"Anda\n{prompt}\n\nBenzie\n")
        self.message_input.clear()
        self.message_input.setEnabled(False)
        worker = ChatWorker(self._service, prompt, self)
        self._worker = worker
        worker.phase.connect(self._phase)
        worker.chunk.connect(self._chunk)
        worker.failed.connect(self._error)
        worker.cancelled.connect(self._cancelled)
        worker.finished.connect(self._finished)
        self._update_send()
        self.cancel_button.setEnabled(True)
        worker.start()

    @Slot()
    def _cancel(self) -> None:
        if self._worker is None or self._cancelling:
            return
        self._cancelling = True
        self.cancel_button.setEnabled(False)
        self.statusBar().showMessage("Membatalkan…")
        try:
            self._worker.cancel()
        except RuntimeStartError as error:
            self._error(str(error))
            self._cancelling = False
            self.cancel_button.setEnabled(not self._close_pending)

    @Slot()
    def _cancelled(self) -> None:
        self.chat_history.appendPlainText("[Dibatalkan]")

    @Slot(str)
    def _phase(self, phase: str) -> None:
        if not self._close_pending and not self._cancelling:
            self.statusBar().showMessage("Memuat model…" if phase == "loading" else "Menyusun jawaban…")

    @Slot(str)
    def _chunk(self, text: str) -> None:
        if self._cancelling:
            return
        self.chat_history.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_history.insertPlainText(text)
        self.chat_history.ensureCursorVisible()

    @Slot(str)
    def _error(self, message: str) -> None:
        self.chat_history.appendPlainText(f"[Kesalahan: {message}]")

    @Slot()
    def _finished(self) -> None:
        worker = self._worker
        self._worker = None
        if worker is not None:
            # run sudah selesai; pastikan native thread benar-benar berhenti.
            worker.wait()
            worker.deleteLater()
        self.chat_history.appendPlainText("")
        self._cancelling = False
        self.cancel_button.setEnabled(False)
        if self._close_pending:
            self.close()
            return
        self.statusBar().showMessage("Siap")
        self.message_input.setEnabled(self._service is not None)
        self._update_send()
        self.message_input.setFocus()

    def closeEvent(self, event) -> None:
        if self._worker is not None:
            self._close_pending = True
            self._cancel()
            self.statusBar().showMessage("Membatalkan proses sebelum menutup…")
            self._update_send()
            event.ignore()
            return
        super().closeEvent(event)
