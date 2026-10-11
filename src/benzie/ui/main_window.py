"""Window fondasi; belum menyediakan input chat atau model."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from benzie.core.startup import StartupState


class MainWindow(QMainWindow):
    def __init__(self, state: StartupState) -> None:
        super().__init__()
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

        description = QLabel(
            "Fondasi aplikasi siap.\n"
            "Model lokal belum diintegrasikan. Percakapan belum tersedia."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addStretch()

        database = QLabel(f"Database lokal:\n{state.database_path}")
        database.setTextFormat(Qt.TextFormat.PlainText)
        database.setWordWrap(True)
        database.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(database)

        self.setCentralWidget(content)
        self.statusBar().showMessage(f"SQLite siap · versi skema {state.schema_version}")
