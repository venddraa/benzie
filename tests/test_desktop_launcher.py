import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

spec = importlib.util.spec_from_file_location(
    "desktop_launcher", Path(__file__).resolve().parents[1] / "scripts/desktop_launcher.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


@pytest.fixture
def root(tmp_path):
    path = tmp_path / 'project with spaces $cash `literal` "quote" \\slash'
    (path / ".venv/bin").mkdir(parents=True)
    (path / ".venv/bin/python").symlink_to("/usr/bin/python3.12")
    (path / "src/benzie").mkdir(parents=True)
    (path / "src/benzie/app.py").touch()
    return path


def test_install_validate_and_remove_preserves_profile(root, tmp_path):
    profile = tmp_path / "profile"
    profile.mkdir()
    sentinel = profile / "keep.txt"
    sentinel.write_text("keep")
    directory = tmp_path / "applications"
    content = launcher.render_launcher(root, profile)
    target = launcher.install_launcher(directory, content)
    assert ' -m benzie --data-dir ' in content
    assert '.venv/bin/python' in content
    assert "Terminal=false" in content
    assert target.stat().st_mode & 0o777 == 0o644
    if shutil.which("desktop-file-validate"):
        result = subprocess.run(["desktop-file-validate", str(target)], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    assert launcher.install_launcher(directory, content) == target
    assert launcher.remove_launcher(directory)
    assert not launcher.remove_launcher(directory)
    assert sentinel.read_text() == "keep"


def test_exec_quoting_round_trips_through_glib(root, tmp_path):
    # Fedora menyediakan PyGObject pada Python sistem; verifikasi parser desktop asli.
    if not Path("/usr/bin/python3").exists():
        pytest.skip("Python sistem tidak tersedia")
    target = launcher.install_launcher(tmp_path / "applications", launcher.render_launcher(root))
    code = (
        "import sys; from gi.repository import Gio, GLib; "
        "app=Gio.DesktopAppInfo.new_from_filename(sys.argv[1]); "
        "assert app is not None; ok,args=GLib.shell_parse_argv(app.get_commandline()); "
        "assert ok and args == [sys.argv[2], '-m', 'benzie'], args"
    )
    result = subprocess.run(["/usr/bin/python3", "-c", code, str(target), str(root / ".venv/bin/python")],
                            capture_output=True, text=True)
    if "No module named 'gi'" in result.stderr:
        pytest.skip("PyGObject sistem tidak tersedia")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("value", ["path%f", "path\nExec=evil", "path\tbad"])
def test_rejects_field_code_and_control_characters(value):
    with pytest.raises(ValueError):
        launcher.exec_argument(value)


def test_unrelated_launcher_and_symlink_are_not_overwritten(root, tmp_path):
    directory = tmp_path / "applications"
    directory.mkdir()
    target = directory / "benzie.desktop"
    target.write_text("unrelated launcher")
    with pytest.raises(ValueError):
        launcher.install_launcher(directory, launcher.render_launcher(root))
    with pytest.raises(ValueError):
        launcher.remove_launcher(directory)
    assert target.read_text() == "unrelated launcher"
    target.unlink()
    target.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError):
        launcher.install_launcher(directory, launcher.render_launcher(root))


def test_failed_replace_keeps_previous_launcher(root, tmp_path, monkeypatch):
    directory = tmp_path / "applications"
    target = launcher.install_launcher(directory, launcher.render_launcher(root))
    original = target.read_bytes()
    def fail(*args): raise OSError("disk error")
    monkeypatch.setattr(launcher.os, "replace", fail)
    with pytest.raises(OSError):
        launcher.install_launcher(directory, "replacement")
    assert target.read_bytes() == original
    assert list(directory.iterdir()) == [target]


def test_xdg_and_missing_environment_are_handled(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert launcher.applications_directory() == tmp_path / "applications"
    monkeypatch.setenv("XDG_DATA_HOME", "relative")
    assert launcher.applications_directory() == Path.home() / ".local/share/applications"
    with pytest.raises(ValueError, match=".venv"):
        launcher.render_launcher(tmp_path)


def test_install_cli_is_independent_of_working_directory(tmp_path):
    script = Path(launcher.__file__).resolve()
    directory = tmp_path / "staging applications"
    result = subprocess.run([sys.executable, str(script), "--applications-dir", str(directory)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (directory / "benzie.desktop").is_file()
    # Python yang dituju dapat mengimpor package tanpa cwd proyek atau uv sync.
    result = subprocess.run([sys.executable, "-m", "benzie", "--help"], cwd=tmp_path,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "--model" in result.stdout
    result = subprocess.run([sys.executable, str(script), "--applications-dir", str(directory), "--remove"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0
    assert not (directory / "benzie.desktop").exists()
