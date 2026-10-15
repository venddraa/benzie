"""Konfigurasi runtime lokal; tidak memuat model atau mengunduh artefak."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile

from benzie.core.chat import ChatService
from benzie.inference.engine import LlamaServerEngine
from benzie.inference.server import RuntimeStartError, ServerConfig


class SettingsError(Exception):
    """Kesalahan konfigurasi yang aman ditampilkan ke UI."""


@dataclass(frozen=True)
class ModelSettings:
    runtime: Path
    model: Path
    port: int = 8081

    def server_config(self) -> ServerConfig:
        return ServerConfig(self.runtime, self.model, port=self.port)

    def validate(self) -> None:
        try:
            self.server_config().command()
        except RuntimeStartError as error:
            raise SettingsError(str(error)) from error

    def chat_service(self) -> ChatService:
        config = self.server_config()
        return ChatService(lambda: LlamaServerEngine(config))


def load_settings(path: Path) -> ModelSettings | None:
    try:
        with path.open("r", encoding="utf-8") as stream:
            text = stream.read(16385)
        if len(text) > 16384:
            raise ValueError()
        data = json.loads(text)
        if (not isinstance(data, dict) or type(data.get("version")) is not int
                or data["version"] != 1 or not isinstance(data.get("runtime"), str)
                or not isinstance(data.get("model"), str)
                or not Path(data["runtime"]).is_absolute() or not Path(data["model"]).is_absolute()
                or type(data.get("port")) is not int):
            raise ValueError()
        settings = ModelSettings(Path(data["runtime"]), Path(data["model"]), data["port"])
        settings.validate()
        return settings
    except FileNotFoundError:
        return None
    except (OSError, ValueError, UnicodeError) as error:
        raise SettingsError("Konfigurasi model tidak dapat dibaca atau formatnya tidak valid. Pilih ulang runtime/model.") from error


def save_settings(path: Path, settings: ModelSettings) -> ModelSettings:
    """Validasi lalu ganti atomik; gagal menulis mempertahankan file lama."""
    temporary = None
    try:
        settings = ModelSettings(settings.runtime.expanduser().resolve(),
                                 settings.model.expanduser().resolve(), settings.port)
        settings.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".model-settings-", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump({"version": 1, "runtime": str(settings.runtime),
                       "model": str(settings.model), "port": settings.port}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        return settings
    except (OSError, RuntimeError) as error:
        raise SettingsError("Konfigurasi model tidak dapat disimpan. Periksa lokasi dan izin akses data.") from error
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
