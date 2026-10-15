"""Smoke penerimaan V0.1 dengan data sintetis sementara dan model pilihan lokal.

Jalankan dari terminal desktop dengan internet dimatikan secara manual.
Script tidak mengubah koneksi sistem atau membaca percakapan pribadi.
"""

import argparse
from contextlib import closing
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from benzie.config import default_data_directory
from benzie.core.history import HistoryService
from benzie.core.model_settings import SettingsError, load_settings
from benzie.core.startup import initialize_application
from benzie.inference.engine import InferenceCancelled, InferenceError
from benzie.inference.server import RuntimeStartError
from benzie.persistence.database import DatabaseError


class AcceptanceError(Exception):
    pass


def _check(condition, message):
    if not condition:
        raise AcceptanceError(message)


def run_checks(chat_service, directory: Path) -> None:
    state = initialize_application(directory)
    history = HistoryService(state.database_path, chat_service)
    conversation = history.new_conversation()
    prompt = "Kode uji sintetis saya nila-47. Jawab singkat."
    with closing(history.new_request(prompt, conversation.id).events()) as events:
        text = "".join(event.text for event in events)
    _check(bool(text.strip()), "Respons pertama kosong.")
    print("Chat lokal dan penyimpanan: PASS", flush=True)

    reopened = HistoryService(initialize_application(directory).database_path, chat_service)
    original = reopened.messages(conversation.id)
    _check(len(original) == 2 and original[-1].status == "completed", "History gagal dibuka ulang.")
    with closing(reopened.new_request("Apa kode uji yang saya sebut tadi?", conversation.id).events()) as events:
        text = "".join(event.text for event in events)
    messages = reopened.messages(conversation.id)
    _check(bool(text.strip()) and len(messages) == 4 and messages[:2] == original,
           "Melanjutkan percakapan gagal.")
    _check(all(message.status == "completed" for message in messages), "Status history tidak sesuai.")
    print("Buka ulang dan lanjut percakapan: PASS (kualitas jawaban tidak dinilai)", flush=True)

    other = reopened.new_conversation()
    _check(not reopened.messages(other.id), "Percakapan baru tidak kosong.")
    request = reopened.new_request("Tuliskan penjelasan panjang tentang pelangi.", other.id)
    cancelled = False
    saw_text = False
    try:
        with closing(request.events()) as events:
            for event in events:
                if event.kind == "text" and not saw_text:
                    saw_text = True
                    request.cancel()
    except InferenceCancelled:
        cancelled = True
    _check(saw_text and cancelled, "Pembatalan setelah token pertama tidak terverifikasi.")
    partial = reopened.messages(other.id)
    _check(len(partial) == 2 and partial[-1].status == "cancelled" and bool(partial[-1].content),
           "Jawaban parsial/status pembatalan tidak tersimpan.")
    _check(reopened.messages(conversation.id) == messages, "Percakapan lain berubah.")
    print("Cancel, jawaban parsial, dan isolasi history: PASS", flush=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", type=Path,
                        default=default_data_directory() / "model-settings.json",
                        help="konfigurasi lokal yang telah disimpan lewat Model lokal")
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.settings)
        if settings is None:
            raise AcceptanceError("Pilih dan simpan runtime/model melalui Benzie terlebih dahulu.")
        print("Tutup Benzie sebelum tes agar port tersedia. Data tes bersifat sementara.", flush=True)
        print("Script tidak memverifikasi status internet; matikan internet secara manual.", flush=True)
        with TemporaryDirectory(prefix="benzie-acceptance-") as directory:
            run_checks(settings.chat_service(), Path(directory))
    except (SettingsError, DatabaseError, InferenceError, RuntimeStartError, AcceptanceError, ValueError) as error:
        print(f"Penerimaan lokal FAIL: {error}", file=sys.stderr)
        return 1
    except OSError:
        print("Penerimaan lokal FAIL: data sementara tidak dapat diakses.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Tes dibatalkan; cleanup request dijalankan.", file=sys.stderr)
        return 130
    print("Alur lokal PASS; data tes dihapus. Konfirmasi offline dan launcher tetap perlu tes desktop.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
