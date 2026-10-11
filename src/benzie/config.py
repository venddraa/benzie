"""Lokasi data aplikasi; tidak membuat direktori saat diimpor."""

import os
from pathlib import Path


def default_data_directory() -> Path:
    """Hormati XDG_DATA_HOME absolut; abaikan nilai relatif sesuai XDG."""
    value = os.environ.get("XDG_DATA_HOME", "")
    if value and Path(value).is_absolute():
        return Path(value) / "benzie"
    return Path.home() / ".local" / "share" / "benzie"
