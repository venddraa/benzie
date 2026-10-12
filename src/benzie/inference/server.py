"""Lifecycle child process llama-server. Proses hidup belum berarti model siap."""

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import subprocess
import threading

logger = logging.getLogger(__name__)


class RuntimeStartError(Exception):
    """Runtime lokal tidak dapat disiapkan atau dijalankan."""


@dataclass(frozen=True)
class ServerConfig:
    executable: Path
    model: Path
    port: int = 8081
    context_size: int = 2048
    threads: int = 4

    def command(self) -> list[str]:
        for name, value, maximum in (
            ("port", self.port, 65535),
            ("context_size", self.context_size, None),
            ("threads", self.threads, None),
        ):
            if type(value) is not int or value < 1 or (maximum and value > maximum):
                raise RuntimeStartError(f"Nilai {name} tidak valid.")
        try:
            executable = self.executable.expanduser().resolve()
            model = self.model.expanduser().resolve()
            if not executable.is_file() or not os.access(executable, os.X_OK):
                raise RuntimeStartError("Binary llama-server tidak ditemukan atau tidak executable.")
            if not model.is_file():
                raise RuntimeStartError("File model lokal tidak ditemukan.")
            with model.open("rb") as stream:
                if stream.read(4) != b"GGUF":
                    raise RuntimeStartError("File model tidak memiliki header GGUF.")
        except (OSError, RuntimeError) as error:
            raise RuntimeStartError("Binary atau model lokal tidak dapat diakses.") from error

        # Header hanya pemeriksaan awal, bukan validasi weights/arsitektur model.
        return [
            str(executable), "--model", str(model),
            "--host", "127.0.0.1", "--port", str(self.port),
            "--ctx-size", str(self.context_size), "--threads", str(self.threads),
            "--parallel", "1", "--device", "none", "--n-gpu-layers", "0",
            "--offline", "--no-webui", "--no-agent", "--no-mmproj",
        ]


class LocalServerProcess:
    """Satu pemilik proses; panggil start/stop dari thread pemilik yang sama.

    Health check/request berada di adapter engine. Pemanggil wajib stop saat
    selesai; kelas ini belum dihubungkan ke lifecycle aplikasi desktop.
    """

    def __init__(self, config: ServerConfig, *, api_key: str | None = None) -> None:
        self.config = config
        self._api_key = api_key
        self._process: subprocess.Popen | None = None
        self._reader: threading.Thread | None = None
        self.failure_hint: str | None = None

    def _read_diagnostics(self, stream) -> None:
        # Baca pipe agar native process tidak macet. Jangan simpan/log baris mentah.
        hints = (
            (("address already in use", "failed to bind", "couldn't bind"), "Socket lokal tidak dapat dibuka; periksa port atau izin jaringan sesi."),
            (("out of memory", "bad_alloc", "cannot allocate memory"), "Memori tidak cukup untuk runtime/model."),
            (("failed to load model", "error loading model", "invalid magic"), "Runtime gagal memuat model lokal."),
            (("unknown argument", "invalid argument"), "Opsi runtime tidak cocok dengan binary."),
        )
        try:
            for line in stream:
                text = line.decode("utf-8", errors="replace").lower()
                for patterns, hint in hints:
                    if any(pattern in text for pattern in patterns):
                        if self.failure_hint is None or "Memori tidak cukup" in hint:
                            self.failure_hint = hint
                        break
        finally:
            stream.close()

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self) -> None:
        if self.is_running:
            raise RuntimeStartError("Proses llama-server sudah berjalan.")
        command = self.config.command()
        # Jangan warisi konfigurasi llama yang dapat mengaktifkan download,
        # tools, RPC, log file, atau preset di luar konfigurasi Benzie.
        environment = {
            key: value for key, value in os.environ.items()
            if not key.startswith("LLAMA_")
            and key not in {"HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"}
        }
        if self._api_key is not None:
            environment["LLAMA_API_KEY"] = self._api_key
        self.failure_hint = None
        try:
            self._process = subprocess.Popen(
                command, shell=False, env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
        except OSError as error:
            raise RuntimeStartError("Proses llama-server gagal dijalankan.") from error
        if self._process.stderr is not None:
            self._reader = threading.Thread(
                target=self._read_diagnostics, args=(self._process.stderr,), daemon=True,
            )
            self._reader.start()
        logger.info("Proses runtime dimulai; kesiapan model belum diperiksa")

    def stop(self) -> None:
        process = self._process
        if process is None:
            return
        try:
            if process.poll() is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass  # Proses selesai di antara poll dan terminate.
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            else:
                process.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired) as error:
            # Pertahankan handle agar pemanggil dapat mencoba cleanup kembali.
            raise RuntimeStartError("Proses llama-server belum berhasil dihentikan.") from error
        self._process = None
        if self._reader is not None:
            self._reader.join(timeout=1)
            self._reader = None
        logger.info("Proses runtime dihentikan")
