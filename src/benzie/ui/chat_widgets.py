"""Presentasi chat; konten pengguna/model selalu dimasukkan sebagai teks literal."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextBlockFormat, QTextCharFormat, QTextCursor, QFont
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit


class MessageInput(QPlainTextEdit):
    submitted = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if not event.isAutoRepeat():
                self.submitted.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class ChatTranscript(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAcceptRichText(False)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse |
                                     Qt.TextInteractionFlag.TextSelectableByKeyboard)

    def _body_format(self):
        format = QTextCharFormat()
        format.setForeground(QColor("#382F29"))
        format.setFontWeight(QFont.Weight.Normal)
        return format

    def append_message(self, role, content=""):
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self.document().isEmpty():
            cursor.insertBlock()
        block = QTextBlockFormat()
        block.setTopMargin(22)
        block.setBottomMargin(8)
        cursor.setBlockFormat(block)
        heading = QTextCharFormat()
        heading.setFontWeight(QFont.Weight.DemiBold)
        heading.setForeground(QColor("#AF471E") if role == "Benzie" else QColor("#776456"))
        cursor.insertText(role, heading)
        cursor.insertBlock()
        body = QTextBlockFormat()
        body.setLineHeight(140, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        cursor.setBlockFormat(body)
        cursor.insertText(content, self._body_format())
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def append_chunk(self, text):
        scrollbar = self.verticalScrollBar()
        follow = scrollbar.maximum() - scrollbar.value() < 24
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, self._body_format())
        if follow:
            scrollbar.setValue(scrollbar.maximum())

    def append_notice(self, text):
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock()
        format = self._body_format()
        format.setForeground(QColor("#96431F"))
        cursor.insertText(text, format)
