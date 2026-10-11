"""Entry point desktop dan perakitan core dengan UI."""

import argparse
import logging
from pathlib import Path

from benzie.config import default_data_directory
from benzie.core.startup import initialize_application
from benzie.persistence.database import DatabaseError

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benzie — aplikasi desktop lokal")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_directory(),
        help="direktori data lokal (default mengikuti XDG_DATA_HOME)",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    # Impor UI setelah parsing: --help dan core tidak membutuhkan Qt.
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication, QMessageBox
    except ImportError:
        logger.error(
            "PySide6 tidak tersedia atau gagal dimuat. "
            "Lengkapi environment dengan uv sync, lalu jalankan Benzie kembali."
        )
        return 1

    from benzie.ui.main_window import MainWindow

    application = QApplication(["benzie"])
    application.setApplicationName("Benzie")
    logger.info("Aplikasi dimulai")
    try:
        state = initialize_application(args.data_dir)
    except (DatabaseError, OSError, RuntimeError) as error:
        # Jangan tulis detail exception mentah atau data pribadi ke log.
        logger.error("Inisialisasi data gagal (%s)", type(error).__name__)
        message = QMessageBox()
        message.setIcon(QMessageBox.Icon.Critical)
        message.setWindowTitle("Benzie — gagal membuka data")
        message.setTextFormat(Qt.TextFormat.PlainText)
        message.setText("Benzie tidak dapat menyiapkan data lokal.")
        message.setInformativeText(
            str(error) if isinstance(error, DatabaseError)
            else "Lokasi data tidak dapat diakses. Periksa path dan izin akses."
        )
        message.exec()
        return 1

    window = MainWindow(state)
    window.show()
    result = application.exec()
    logger.info("Aplikasi ditutup")
    return result
