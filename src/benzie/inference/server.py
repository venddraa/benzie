"""Lifecycle child process llama-server. Proses hidup belum berarti model siap."""

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import subprocess

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

    Belum melakukan health check atau request inference. Pemanggil wajib stop
    saat selesai; kelas ini belum dihubungkan ke lifecycle aplikasi desktop.
    """

    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self._process: subprocess.Popen | None = None

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
        try:
            self._process = subprocess.Popen(
                command, shell=False, env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except OSError as error:
            raise RuntimeStartError("Proses llama-server gagal dijalankan.") from error
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
        logger.info("Proses runtime dihentikan")
