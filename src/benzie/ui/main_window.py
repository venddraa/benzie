"""Presentasi chat teks; SQL dan runtime ditangani di luar widget."""

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                              QMainWindow, QPushButton, QSplitter, QStackedWidget,
                              QVBoxLayout, QWidget)

from benzie.core.chat import ChatService
from benzie.core.startup import StartupState
from benzie.ui.chat_worker import ChatWorker
from benzie.inference.server import RuntimeStartError
from benzie.core.history import HistoryService
from benzie.persistence.database import DatabaseError
from benzie.ui.model_dialog import ModelDialog
from benzie.ui.chat_widgets import ChatTranscript, MessageInput
from benzie.ui.theme import SUNSET


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
        self.resize(1080, 740)
        self.setMinimumSize(740, 540)
        self.setStyleSheet(SUNSET)
        content = QSplitter(Qt.Orientation.Horizontal)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(190)
        sidebar.setMaximumWidth(300)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 28, 20, 20)
        side.setSpacing(14)
        brand = QLabel("Benzie")
        brand.setObjectName("brand")
        side.addWidget(brand)
        tagline = QLabel("Asisten pribadi lokal")
        tagline.setObjectName("muted")
        side.addWidget(tagline)
        side.addSpacing(16)
        self.new_button = QPushButton("+  Percakapan baru")
        self.new_button.setObjectName("newConversation")
        side.addWidget(self.new_button)
        section = QLabel("PERCAKAPAN")
        section.setObjectName("sectionLabel")
        side.addSpacing(8)
        side.addWidget(section)
        self.conversation_list = QListWidget()
        self.conversation_list.setAccessibleName("Riwayat percakapan")
        self.conversation_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.conversation_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side.addWidget(self.conversation_list, 1)
        privacy = QLabel("Riwayat tersimpan\ndi perangkat ini.")
        privacy.setObjectName("muted")
        side.addWidget(privacy)
        content.addWidget(sidebar)

        main = QWidget()
        main.setObjectName("mainPanel")
        layout = QVBoxLayout(main)
        layout.setContentsMargins(28, 24, 28, 16)
        layout.setSpacing(16)
        header = QHBoxLayout()
        headings = QVBoxLayout()
        headings.setSpacing(6)
        self.conversation_title = QLabel("Percakapan baru")
        self.conversation_title.setObjectName("conversationTitle")
        self.conversation_title.setTextFormat(Qt.TextFormat.PlainText)
        self.conversation_title.setWordWrap(True)
        headings.addWidget(self.conversation_title)
        self.model_label = QLabel(f"Model dipilih: {model_name}" if model_name else "Belum ada model dipilih.")
        self.model_label.setObjectName("modelName")
        self.model_label.setTextFormat(Qt.TextFormat.PlainText)
        self.model_label.setWordWrap(True)
        headings.addWidget(self.model_label)
        header.addLayout(headings, 1)
        local = QLabel("Lokal")
        local.setObjectName("localBadge")
        local.setFixedHeight(28)
        header.addWidget(local)
        self.model_button = QPushButton("Model lokal…")
        self.model_button.clicked.connect(self._choose_model)
        header.addWidget(self.model_button)
        layout.addLayout(header)
        self.settings_label = QLabel(settings_error or "")
        self.settings_label.setObjectName("settingsError")
        self.settings_label.setTextFormat(Qt.TextFormat.PlainText)
        self.settings_label.setWordWrap(True)
        self.settings_label.setVisible(bool(settings_error))
        layout.addWidget(self.settings_label)
        self.new_button.clicked.connect(self._new_conversation)
        self.conversation_list.currentRowChanged.connect(self._open_conversation)

        area = QFrame()
        area.setObjectName("conversationArea")
        area_layout = QVBoxLayout(area)
        area_layout.setContentsMargins(4, 4, 4, 4)
        self.chat_pages = QStackedWidget()
        welcome = QWidget()
        welcome.setObjectName("welcome")
        greeting = QVBoxLayout(welcome)
        greeting.setContentsMargins(24, 24, 24, 24)
        greeting.addStretch()
        hello = QLabel("Mau bahas apa\nhari ini?")
        hello.setObjectName("welcomeTitle")
        hello.setAlignment(Qt.AlignmentFlag.AlignCenter)
        greeting.addWidget(hello)
        self.welcome_detail = QLabel()
        self.welcome_detail.setObjectName("welcomeDetail")
        self.welcome_detail.setWordWrap(True)
        self.welcome_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        greeting.addWidget(self.welcome_detail)
        greeting.addStretch()
        self.chat_pages.addWidget(welcome)
        self.chat_history = ChatTranscript()
        self.chat_history.setObjectName("transcript")
        self.chat_history.setAccessibleName("Isi percakapan")
        self.chat_pages.addWidget(self.chat_history)
        area_layout.addWidget(self.chat_pages)
        layout.addWidget(area, 1)

        composer = QFrame()
        composer.setObjectName("composer")
        compose = QVBoxLayout(composer)
        compose.setContentsMargins(14, 12, 14, 12)
        self.message_input = MessageInput()
        self.message_input.setObjectName("messageInput")
        self.message_input.setAccessibleName("Tulis pesan")
        self.message_input.setPlaceholderText("Tulis pesan untuk Benzie…")
        self.message_input.setFixedHeight(72)
        self.message_input.setTabChangesFocus(True)
        compose.addWidget(self.message_input)
        row = QHBoxLayout()
        hint = QLabel("Enter untuk kirim · Shift+Enter untuk baris baru")
        hint.setObjectName("inputHint")
        hint.setWordWrap(True)
        row.addWidget(hint, 1)
        self.send_button = QPushButton("Kirim")
        self.send_button.setObjectName("sendButton")
        self.cancel_button = QPushButton("Batal")
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()
        row.addWidget(self.cancel_button)
        row.addWidget(self.send_button)
        compose.addLayout(row)
        layout.addWidget(composer)
        self.send_button.clicked.connect(self._send)
        self.cancel_button.clicked.connect(self._cancel)
        self.message_input.submitted.connect(self._send)
        self.message_input.textChanged.connect(self._update_send)
        self.message_input.setEnabled(self._service is not None)
        self._update_send()

        content.addWidget(main)
        content.setStretchFactor(1, 1)
        content.setSizes([230, 850])
        self.setCentralWidget(content)
        self.statusBar().showMessage("Siap" if self._service is not None else "Pilih model lokal untuk mulai")
        self._update_conversation_view()
        try:
            self._refresh_conversations()
            if self.conversation_list.count():
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
                self.settings_label.hide()
                self._update_conversation_view()
                self.message_input.setEnabled(True)
                self._update_send()
                self.statusBar().showMessage("Pilihan tersimpan. Model dimuat saat pesan dikirim.")
        finally:
            dialog.deleteLater()

    def _refresh_conversations(self):
        conversations = self._history.conversations()
        self.conversation_list.blockSignals(True)
        try:
            self.conversation_list.clear()
            selected = 0
            for conversation in conversations:
                title = conversation.title if conversation.title != "Percakapan baru" else f"Percakapan {conversation.id}"
                item = QListWidgetItem(f"{title}\n{conversation.updated_at[:10]}")
                item.setData(Qt.ItemDataRole.UserRole, conversation.id)
                item.setData(Qt.ItemDataRole.UserRole + 1, title)
                item.setToolTip(title)
                self.conversation_list.addItem(item)
                if conversation.id == self._conversation_id:
                    selected = self.conversation_list.count() - 1
            self.conversation_list.setCurrentRow(selected if conversations else -1)
        finally:
            self.conversation_list.blockSignals(False)

    def _update_conversation_view(self):
        item = self.conversation_list.currentItem()
        title = item.data(Qt.ItemDataRole.UserRole + 1) if item is not None else "Percakapan baru"
        self.conversation_title.setText(title)
        self.chat_pages.setCurrentIndex(0 if self.chat_history.document().isEmpty() else 1)
        self.welcome_detail.setText("Mulai percakapan dengan model lokal pilihanmu." if self._service is not None
                                    else "Pilih model lokal untuk mulai mengobrol.")

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
            self._update_conversation_view()
            self.message_input.setFocus()
        except DatabaseError as error:
            self._storage_error(str(error))

    @Slot()
    def _open_conversation(self):
        if self._worker is not None or self._storage_failed:
            return
        item = self.conversation_list.currentItem()
        if item is None:
            return
        selected = item.data(Qt.ItemDataRole.UserRole)
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
            self.chat_history.append_message(label, message.content)
            if marker:
                self.chat_history.append_notice(marker.strip())
        self._update_conversation_view()

    @Slot(str)
    def _storage_error(self, message):
        self._storage_failed = True
        self.model_button.setEnabled(False)
        self._close_pending = False
        self._error("History gagal disimpan/dibaca. " + message)
        self.statusBar().showMessage("History bermasalah; salin teks yang diperlukan sebelum menutup aplikasi.")
        self.message_input.setEnabled(False)
        self.new_button.setEnabled(False)
        self.conversation_list.setEnabled(False)
        self._update_send()

    @Slot()
    def _update_send(self) -> None:
        self.send_button.setEnabled(
            self._service is not None and self._worker is None
            and bool(self.message_input.toPlainText().strip()) and not self._close_pending
            and not self._storage_failed
        )

    @Slot()
    def _send(self) -> None:
        prompt = self.message_input.toPlainText().strip()
        if self._service is None or self._worker is not None or not prompt or self._close_pending or self._storage_failed:
            return
        if self._conversation_id is None:
            self._new_conversation()
            if self._storage_failed:
                return
        self.chat_history.append_message("Anda", prompt)
        self.chat_history.append_message("Benzie")
        self._update_conversation_view()
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
        self.cancel_button.show()
        self.model_button.setEnabled(False)
        self.new_button.setEnabled(False)
        self.conversation_list.setEnabled(False)
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
        self.chat_history.append_notice("[Dibatalkan]")

    @Slot(str)
    def _phase(self, phase: str) -> None:
        if not self._close_pending and not self._cancelling:
            self.statusBar().showMessage("Memuat model…" if phase == "loading" else "Menyusun jawaban…")

    @Slot(str)
    def _chunk(self, text: str) -> None:
        if self._cancelling:
            return
        self.chat_history.append_chunk(text)

    @Slot(str)
    def _error(self, message: str) -> None:
        self.chat_history.append_notice(f"[Kesalahan: {message}]")
        self._update_conversation_view()

    @Slot()
    def _finished(self) -> None:
        worker = self._worker
        self._worker = None
        if worker is not None:
            # run sudah selesai; pastikan native thread benar-benar berhenti.
            worker.wait()
            worker.deleteLater()
        self._cancelling = False
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()
        if self._storage_failed:
            return
        try:
            self._refresh_conversations()
        except DatabaseError as error:
            self._storage_error(str(error))
            return
        self.new_button.setEnabled(True)
        self.model_button.setEnabled(True)
        self.conversation_list.setEnabled(True)
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
