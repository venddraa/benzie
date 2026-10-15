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
    parser.add_argument("--port", type=int, help="port HTTP loopback runtime (default 8081 atau konfigurasi tersimpan)")
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
    application.setDesktopFileName("benzie")
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

    from benzie.core.model_settings import ModelSettings, SettingsError, load_settings

    chat_service = None
    settings = None
    settings_error = None
    if args.model is not None:
        settings = ModelSettings(args.runtime.expanduser().resolve(), args.model.expanduser().resolve(),
                                 args.port if args.port is not None else 8081)
    else:
        try:
            settings = load_settings(state.database_path.parent / "model-settings.json")
            if settings is not None and args.port is not None:
                settings = ModelSettings(settings.runtime, settings.model, args.port)
        except SettingsError as error:
            settings_error = str(error)
    if settings is not None:
        try:
            settings.validate()
            chat_service = settings.chat_service()
        except SettingsError as error:
            settings_error = str(error)
    window = MainWindow(state, chat_service=chat_service,
                        model_name=settings.model.name if settings is not None else None,
                        model_settings=settings, settings_error=settings_error)
    window.show()
    result = application.exec()
    logger.info("Aplikasi ditutup")
    return result
