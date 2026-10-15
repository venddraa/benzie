"""Presentasi chat teks; SQL dan runtime ditangani di luar widget."""

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from benzie.core.chat import ChatService
from benzie.core.startup import StartupState
from benzie.ui.chat_worker import ChatWorker
from benzie.inference.server import RuntimeStartError
from benzie.core.history import HistoryService
from benzie.persistence.database import DatabaseError
from benzie.ui.model_dialog import ModelDialog


class MainWindow(QMainWindow):
    def __init__(self, state: StartupState, *, chat_service: ChatService | None = None,
                 model_name: str | None = None, model_settings=None, settings_error: str | None = None) -> None:
        super().__init__()
        self._service = chat_service
        self._model_settings = model_settings
        self._settings_path = state.database_path.parent / "model-settings.json"
        self._history = HistoryService(state.database_path, chat_service)
        self._conversation_id = None
        self._storage_failed = False
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

        description = QLabel("Riwayat tersimpan lokal. Model memakai percakapan aktif; jika konteks penuh, buat percakapan baru.")
        description.setWordWrap(True)
        layout.addWidget(description)
        model_row = QHBoxLayout()
        self.model_label = QLabel(f"Model dipilih: {model_name}" if model_name else "Belum ada model dipilih.")
        self.model_label.setTextFormat(Qt.TextFormat.PlainText)
        self.model_label.setWordWrap(True)
        self.model_button = QPushButton("Model lokal…")
        self.model_button.clicked.connect(self._choose_model)
        model_row.addWidget(self.model_label, 1)
        model_row.addWidget(self.model_button)
        layout.addLayout(model_row)
        self.settings_label = QLabel(settings_error or "")
        self.settings_label.setTextFormat(Qt.TextFormat.PlainText)
        self.settings_label.setWordWrap(True)
        layout.addWidget(self.settings_label)

        history_row = QHBoxLayout()
        self.conversation_picker = QComboBox()
        self.new_button = QPushButton("Percakapan baru")
        history_row.addWidget(self.conversation_picker, 1)
        history_row.addWidget(self.new_button)
        layout.addLayout(history_row)
        self.new_button.clicked.connect(self._new_conversation)
        self.conversation_picker.currentIndexChanged.connect(self._open_conversation)

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
        try:
            self._refresh_conversations()
            if self.conversation_picker.count():
                self._open_conversation()
        except DatabaseError as error:
            self._storage_error(str(error))

    @Slot()
    def _choose_model(self):
        if self._worker is not None or self._close_pending or self._storage_failed:
            return
        dialog = ModelDialog(self._settings_path, self._model_settings, self)
        try:
            if dialog.exec() == ModelDialog.DialogCode.Accepted:
                self._model_settings = dialog.selected_settings
                self._service = self._model_settings.chat_service()
                self._history.chat = self._service
                self.model_label.setText(f"Model dipilih: {self._model_settings.model.name}")
                self.settings_label.clear()
                self.message_input.setEnabled(True)
                self._update_send()
                self.statusBar().showMessage("Pilihan tersimpan. Model dimuat saat pesan dikirim.")
        finally:
            dialog.deleteLater()

    def _refresh_conversations(self):
        conversations = self._history.conversations()
        self.conversation_picker.blockSignals(True)
        try:
            self.conversation_picker.clear()
            for conversation in conversations:
                self.conversation_picker.addItem(
                    f"{conversation.title} · #{conversation.id}", conversation.id,
                )
            if self._conversation_id is not None:
                self.conversation_picker.setCurrentIndex(
                    self.conversation_picker.findData(self._conversation_id)
                )
        finally:
            self.conversation_picker.blockSignals(False)

    @Slot()
    def _new_conversation(self):
        if self._worker is not None or self._storage_failed:
            return
        try:
            conversation = self._history.new_conversation()
            self._conversation_id = conversation.id
            self._refresh_conversations()
            self.chat_history.clear()
            self.message_input.clear()
        except DatabaseError as error:
            self._storage_error(str(error))

    @Slot()
    def _open_conversation(self):
        if self._worker is not None or self._storage_failed:
            return
        selected = self.conversation_picker.currentData()
        if selected is None:
            return
        try:
            messages = self._history.messages(selected)
        except DatabaseError as error:
            self._storage_error(str(error))
            return
        self._conversation_id = selected
        self.message_input.clear()
        self.chat_history.clear()
        for message in messages:
            label = "Anda" if message.role == "user" else "Benzie"
            marker = {"completed": "", "cancelled": "\n[Dibatalkan]", "failed": "\n[Gagal]"}[message.status]
            self.chat_history.appendPlainText(f"{label}\n{message.content}{marker}\n")

    @Slot(str)
    def _storage_error(self, message):
        self._storage_failed = True
        self.model_button.setEnabled(False)
        self._close_pending = False
        self._error("History gagal disimpan/dibaca. " + message)
        self.statusBar().showMessage("History bermasalah; salin teks yang diperlukan sebelum menutup aplikasi.")
        self.message_input.setEnabled(False)
        self.new_button.setEnabled(False)
        self.conversation_picker.setEnabled(False)
        self._update_send()

    @Slot()
    def _update_send(self) -> None:
        self.send_button.setEnabled(
            self._service is not None and self._worker is None
            and bool(self.message_input.text().strip()) and not self._close_pending
            and not self._storage_failed
        )

    @Slot()
    def _send(self) -> None:
        prompt = self.message_input.text().strip()
        if self._service is None or self._worker is not None or not prompt or self._close_pending or self._storage_failed:
            return
        if self._conversation_id is None:
            self._new_conversation()
            if self._storage_failed:
                return
        self.chat_history.appendPlainText(f"Anda\n{prompt}\n\nBenzie\n")
        self.message_input.clear()
        self.message_input.setEnabled(False)
        worker = ChatWorker(self._service, prompt, self, history=self._history,
                            conversation_id=self._conversation_id)
        self._worker = worker
        worker.phase.connect(self._phase)
        worker.chunk.connect(self._chunk)
        worker.failed.connect(self._error)
        worker.storage_failed.connect(self._storage_error)
        worker.cancelled.connect(self._cancelled)
        worker.finished.connect(self._finished)
        self._update_send()
        self.cancel_button.setEnabled(True)
        self.model_button.setEnabled(False)
        self.new_button.setEnabled(False)
        self.conversation_picker.setEnabled(False)
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
        if self._storage_failed:
            return
        try:
            self._refresh_conversations()
        except DatabaseError as error:
            self._storage_error(str(error))
            return
        self.new_button.setEnabled(True)
        self.model_button.setEnabled(True)
        self.conversation_picker.setEnabled(True)
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
