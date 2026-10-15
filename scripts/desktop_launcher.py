"""Pasang/lepas shortcut development per-user tanpa sudo atau network."""

import argparse
import os
from pathlib import Path
import tempfile

MARKER = "X-Benzie-Managed=true"


def applications_directory() -> Path:
    value = os.environ.get("XDG_DATA_HOME", "")
    base = Path(value) if value and Path(value).is_absolute() else Path.home() / ".local/share"
    return base / "applications"


def exec_argument(value: str) -> str:
    # Dua lapis escaping: Exec quoting, lalu string-value desktop entry.
    # Field code (%) dalam quoted argument dihindari sepenuhnya.
    if not value or "%" in value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("Path launcher tidak boleh mengandung persen atau karakter kontrol.")
    quoted = value.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
    return '"' + quoted.replace("\\", "\\\\") + '"'


def render_launcher(root: Path, data_directory: Path | None = None) -> str:
    root = root.expanduser().resolve()
    # Jangan resolve symlink interpreter: path .venv mempertahankan environment.
    interpreter = root / ".venv/bin/python"
    if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
        raise ValueError("Python .venv tidak tersedia. Siapkan environment proyek dahulu.")
    if not (root / "src/benzie/app.py").is_file():
        raise ValueError("Source aplikasi Benzie tidak ditemukan.")
    if "=" in str(interpreter):
        raise ValueError("Path executable launcher tidak boleh mengandung tanda sama dengan.")
    command = exec_argument(str(interpreter)) + " -m benzie"
    if data_directory is not None:
        command += " --data-dir " + exec_argument(str(data_directory.expanduser().resolve()))
    return (
        "[Desktop Entry]\nType=Application\nVersion=1.0\nName=Benzie\n"
        "Comment=Asisten AI pribadi lokal\n"
        f"Exec={command}\n"
        "Icon=applications-utilities\nTerminal=false\nCategories=Utility;\n"
        "StartupNotify=false\n" + MARKER + "\n"
    )


def install_launcher(directory: Path, content: str) -> Path:
    target = directory / "benzie.desktop"
    if target.is_symlink():
        raise ValueError("Target launcher berupa symlink; tidak diubah.")
    if target.exists() and MARKER not in target.read_text(encoding="utf-8").splitlines():
        raise ValueError("benzie.desktop sudah ada dan bukan milik installer ini; tidak diubah.")
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                         prefix=".benzie-desktop-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o644)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return target


def remove_launcher(directory: Path) -> bool:
    target = directory / "benzie.desktop"
    if target.is_symlink():
        raise ValueError("Target launcher berupa symlink; tidak diubah.")
    if not target.exists():
        return False
    if MARKER not in target.read_text(encoding="utf-8").splitlines():
        raise ValueError("Launcher bukan milik installer ini; tidak dihapus.")
    target.unlink()
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--applications-dir", type=Path, default=applications_directory(),
                        help="direktori shortcut (override untuk staging/test)")
    parser.add_argument("--data-dir", type=Path, help="profil data khusus; default mengikuti XDG saat aplikasi dibuka")
    parser.add_argument("--remove", action="store_true", help="hapus hanya shortcut, pertahankan data/model")
    args = parser.parse_args(argv)
    try:
        directory = args.applications_dir.expanduser().resolve()
        if args.remove:
            removed = remove_launcher(directory)
            print("Shortcut dihapus; pasang ulang dengan script ini untuk memulihkannya. Data/model tetap ada."
                  if removed else "Shortcut belum terpasang.")
        else:
            root = Path(__file__).resolve().parents[1]
            target = install_launcher(directory, render_launcher(root, args.data_dir))
            print(f"Shortcut siap: {target}")
            print("Cari Benzie di Applications. Folder proyek dan .venv harus tetap tersedia.")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Launcher gagal: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
