#!/usr/bin/env bash
# Setup development manual. Tidak pernah dipanggil oleh aplikasi Benzie.
set -euo pipefail

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
runtime_commit=d81235049384534c167caea52b85a694f6103d14
runtime_dir="$project_dir/.tools/llama.cpp-v0.6.0"
model_revision=23749fefcc72300e3a2ad315e1317431b06b590a
model_sha=9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031
data_dir=${XDG_DATA_HOME:-"$HOME/.local/share"}
if [[ "$data_dir" != /* ]]; then
    data_dir="$HOME/.local/share"
fi
model_dir="$data_dir/benzie/models"
model_file="$model_dir/Qwen3-0.6B-Q8_0.gguf"

for tool in git cmake ninja gcc g++ curl sha256sum; do
    command -v "$tool" >/dev/null || { printf 'Tool belum tersedia: %s\n' "$tool" >&2; exit 1; }
done

mkdir -p "$project_dir/.tools"
if [[ ! -e "$runtime_dir" ]]; then
    git clone --depth 1 --branch v0.6.0 https://github.com/ggml-org/llama.cpp.git "$runtime_dir"
fi
if [[ "$(git -C "$runtime_dir" rev-parse HEAD)" != "$runtime_commit" ]]; then
    printf 'Source runtime berbeda dari commit yang dipatok; setup dihentikan.\n' >&2
    exit 1
fi
git -C "$runtime_dir" diff --quiet
git -C "$runtime_dir" diff --cached --quiet

mkdir -p "$model_dir"
if [[ ! -e "$model_file" ]]; then
    curl --fail --location --retry 2 --connect-timeout 15 --continue-at - \
        --output "$model_file.part" \
        "https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/$model_revision/Qwen3-0.6B-Q8_0.gguf"
    printf '%s  %s\n' "$model_sha" "$model_file.part" | sha256sum --check
    mv -n -- "$model_file.part" "$model_file"
fi
printf '%s  %s\n' "$model_sha" "$model_file" | sha256sum --check

cmake -S "$runtime_dir" -B "$runtime_dir/build-cpu" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_IS_DEV=OFF \
    -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_APP=OFF \
    -DLLAMA_BUILD_SERVER=ON -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF \
    -DLLAMA_OPENSSL=OFF -DLLAMA_SUBPROCESS=OFF \
    -DGGML_CUDA=OFF -DGGML_VULKAN=OFF -DGGML_SYCL=OFF
cmake --build "$runtime_dir/build-cpu" --target llama-server llama-bench --parallel 4

server="$runtime_dir/build-cpu/bin/llama-server"
"$server" --version
runtime_help=$("$server" --help 2>&1)
for option in --model --host --port --ctx-size --threads --parallel --device --n-gpu-layers --offline --no-webui --no-agent --no-mmproj; do
    if [[ "$runtime_help" != *"$option"* ]]; then
        printf 'Opsi yang dibutuhkan Benzie tidak tersedia: %s\n' "$option" >&2
        exit 1
    fi
done

printf '\nSetup dan pemeriksaan artefak selesai.\nBinary: %s\nModel: %s\n' "$server" "$model_file"
printf 'Model belum dimuat; inference dan benchmark dilakukan pada langkah berikutnya.\n'
