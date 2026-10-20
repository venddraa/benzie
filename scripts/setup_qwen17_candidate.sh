#!/usr/bin/env bash
# Unduhan eksperimen manual; tidak pernah dipanggil dari runtime Benzie.
set -euo pipefail

if (( $# > 1 )); then
    printf 'Pemakaian: bash scripts/setup_qwen17_candidate.sh [direktori-model]\n' >&2
    exit 1
fi
data_dir=${XDG_DATA_HOME:-"$HOME/.local/share"}
if [[ "$data_dir" != /* ]]; then
    data_dir="$HOME/.local/share"
fi
model_dir=${1:-"$data_dir/benzie/models"}
model_revision=90862c4b9d2787eaed51d12237eafdfe7c5f6077
model_sha=061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a
model_file="$model_dir/Qwen3-1.7B-Q8_0.gguf"
partial_file="$model_file.part"

for tool in curl sha256sum ln rm; do
    command -v "$tool" >/dev/null || { printf 'Tool belum tersedia: %s\n' "$tool" >&2; exit 1; }
done
mkdir -p -- "$model_dir"
if [[ -L "$model_file" || -L "$partial_file" ]]; then
    printf 'Target atau file parsial berupa symlink; tidak diubah.\n' >&2
    exit 1
fi
if [[ -e "$model_file" ]]; then
    # Jika file lama berbeda, jangan overwrite atau unduh lagi diam-diam.
    printf '%s  %s\n' "$model_sha" "$model_file" | sha256sum --check
else
    printf 'Mengunduh kandidat resmi Qwen3-1.7B Q8_0, sekitar 1,83 GB.\n'
    printf 'Hanya model baru; pilihan desktop, model lama, dan runtime tidak diubah.\n'
    curl --fail --location --retry 2 --connect-timeout 15 \
        --proto '=https' --proto-redir '=https' --continue-at - \
        --output "$partial_file" \
        "https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/resolve/$model_revision/Qwen3-1.7B-Q8_0.gguf"
    if ! printf '%s  %s\n' "$model_sha" "$partial_file" | sha256sum --check; then
        printf 'Checksum gagal. File .part dipertahankan untuk pemeriksaan; belum dipublikasikan sebagai model.\n' >&2
        exit 1
    fi
    # Hard link atomik gagal jika nama final sudah ada, tanpa overwrite.
    ln -- "$partial_file" "$model_file"
    rm -- "$partial_file"
fi
printf '\nArtefak kandidat terverifikasi: %s\n' "$model_file"
printf 'Model belum dimuat/diukur dan belum dipilih sebagai model utama Benzie.\n'
