import hashlib
import os
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/setup_qwen17_candidate.sh"
SHA = "061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a"
FIXTURE = b"GGUFsynthetic fixture, not weights"


@pytest.fixture
def setup(tmp_path):
    # Salinan script dengan checksum fixture kecil; pin produksi tidak berubah.
    script = tmp_path / "setup.sh"
    script.write_text(SCRIPT.read_text().replace(SHA, hashlib.sha256(FIXTURE).hexdigest()))
    tools = tmp_path / "tools"
    tools.mkdir()
    curl = tools / "curl"
    curl.write_text("#!/usr/bin/env bash\nset -euo pipefail\n"
                    "if [[ ${TEST_CURL_FAIL:-0} == 1 ]]; then exit 7; fi\n"
                    "while (( $# )); do\n"
                    " if [[ $1 == --output ]]; then cp -- \"$TEST_PAYLOAD\" \"$2\"; exit 0; fi\n"
                    " shift\ndone\nexit 1\n")
    curl.chmod(0o700)
    payload = tmp_path / "payload"
    payload.write_bytes(FIXTURE)
    model_dir = tmp_path / "models with spaces"
    env = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"], TEST_PAYLOAD=str(payload))
    return script, model_dir, env, payload


def run(setup):
    script, directory, env, _ = setup
    return subprocess.run(["bash", str(script), str(directory)], env=env,
                          capture_output=True, text=True, timeout=10)


def test_verified_download_publishes_and_reuses_without_network(setup):
    _, directory, env, _ = setup
    result = run(setup)
    assert result.returncode == 0, result.stderr
    target = directory / "Qwen3-1.7B-Q8_0.gguf"
    assert target.read_bytes() == FIXTURE
    assert not target.with_suffix(".gguf.part").exists()
    env["TEST_CURL_FAIL"] = "1"
    assert run(setup).returncode == 0


def test_wrong_download_hash_does_not_publish_model(setup):
    _, directory, _, payload = setup
    payload.write_bytes(b"invalid or incomplete download")
    result = run(setup)
    assert result.returncode != 0
    assert "Checksum gagal" in result.stderr
    assert not (directory / "Qwen3-1.7B-Q8_0.gguf").exists()
    assert (directory / "Qwen3-1.7B-Q8_0.gguf.part").read_bytes() == payload.read_bytes()


def test_existing_mismatch_is_preserved(setup):
    _, directory, _, _ = setup
    directory.mkdir()
    target = directory / "Qwen3-1.7B-Q8_0.gguf"
    target.write_bytes(b"keep existing file")
    assert run(setup).returncode != 0
    assert target.read_bytes() == b"keep existing file"
    assert not (directory / "Qwen3-1.7B-Q8_0.gguf.part").exists()


def test_failed_network_keeps_existing_partial(setup):
    _, directory, env, _ = setup
    directory.mkdir()
    partial = directory / "Qwen3-1.7B-Q8_0.gguf.part"
    partial.write_bytes(b"partial")
    env["TEST_CURL_FAIL"] = "1"
    assert run(setup).returncode != 0
    assert partial.read_bytes() == b"partial"


def test_symlink_target_rejected_without_writing_destination(setup):
    _, directory, _, payload = setup
    directory.mkdir()
    (directory / "Qwen3-1.7B-Q8_0.gguf.part").symlink_to(payload)
    assert run(setup).returncode != 0
    assert payload.read_bytes() == FIXTURE


def test_production_pin_and_https_remain_fixed():
    source = SCRIPT.read_text()
    assert SHA in source
    assert "90862c4b9d2787eaed51d12237eafdfe7c5f6077" in source
    assert "--proto '=https' --proto-redir '=https'" in source
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
