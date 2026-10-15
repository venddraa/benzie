"""Dialog kecil pemilihan file lokal, tanpa model downloader."""

from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
                              QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox)

from benzie.core.model_settings import ModelSettings, SettingsError, save_settings


class ModelDialog(QDialog):
    def __init__(self, settings_path: Path, settings: ModelSettings | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Benzie — model lokal")
        self.resize(600, 200)
        self._path = settings_path
        self.selected_settings = None
        layout = QFormLayout(self)
        self.runtime_input = QLineEdit(str(settings.runtime) if settings else "")
        self.model_input = QLineEdit(str(settings.model) if settings else "")
        for label, field, file_filter in [("llama-server", self.runtime_input, "Semua file (*)"),
                                           ("Model GGUF", self.model_input, "Model GGUF (*.gguf);;Semua file (*)")]:
            row = QHBoxLayout()
            row.addWidget(field)
            button = QPushButton("Pilih…")
            button.clicked.connect(lambda checked=False, f=field, title=label, filters=file_filter:
                                   self._browse(f, title, filters))
            row.addWidget(button)
            layout.addRow(label, row)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(settings.port if settings else 8081)
        layout.addRow("Port lokal", self.port_input)
        layout.addRow(QLabel("Model dimuat saat pesan dikirim. Pilih binary llama-server tepercaya."))
        self.error_label = QLabel()
        self.error_label.setTextFormat(Qt.TextFormat.PlainText)
        self.error_label.setWordWrap(True)
        layout.addRow(self.error_label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _browse(self, field, title, filters):
        filename, _ = QFileDialog.getOpenFileName(self, title, field.text(), filters)
        if filename:
            field.setText(filename)

    @Slot()
    def _save(self):
        if not self.runtime_input.text().strip() or not self.model_input.text().strip():
            self.error_label.setText("Pilih binary llama-server dan file model GGUF.")
            return
        try:
            self.selected_settings = save_settings(self._path, ModelSettings(
                Path(self.runtime_input.text().strip()), Path(self.model_input.text().strip()),
                self.port_input.value(),
            ))
        except SettingsError as error:
            self.error_label.setText(str(error))
            return
        self.accept()
