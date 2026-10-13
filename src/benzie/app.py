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
    parser.add_argument("--runtime", type=Path, help="path binary llama-server lokal")
    parser.add_argument("--model", type=Path, help="path model GGUF lokal")
    parser.add_argument("--port", type=int, default=8081, help="port HTTP loopback runtime")
    args = parser.parse_args(argv)
    if (args.runtime is None) != (args.model is None):
        parser.error("--runtime dan --model harus diberikan bersama")
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

    chat_service = None
    if args.model is not None:
        from benzie.core.chat import ChatService
        from benzie.inference.engine import LlamaServerEngine
        from benzie.inference.server import ServerConfig

        config = ServerConfig(args.runtime, args.model, port=args.port)
        chat_service = ChatService(lambda: LlamaServerEngine(config))
    window = MainWindow(state, chat_service=chat_service,
                        model_name=args.model.name if args.model is not None else None)
    window.show()
    result = application.exec()
    logger.info("Aplikasi ditutup")
    return result
