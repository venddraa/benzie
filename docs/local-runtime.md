# Setup runtime lokal — M2.2

Setup development dijalankan manual, tidak dipanggil oleh aplikasi. Langkah ini
mengunduh source publik dan model publik, tanpa mengunggah data Benzie. Internet
diperlukan untuk setup pertama; runtime menggunakan artefak lokal sesudahnya.

## Artefak yang dipatok

- llama.cpp [v0.6.0](https://github.com/ggml-org/llama.cpp/releases/tag/v0.6.0),
  commit `d81235049384534c167caea52b85a694f6103d14`.
- Model resmi [Qwen/Qwen3-0.6B-GGUF](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF),
  revisi `23749fefcc72300e3a2ad315e1317431b06b590a`.
- File `Qwen3-0.6B-Q8_0.gguf`, sekitar 639 MB, lisensi Apache-2.0.
- SHA256 model:
  `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
  Nilai diperiksa pada [metadata file penerbit](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/blob/23749fefcc72300e3a2ad315e1317431b06b590a/Qwen3-0.6B-Q8_0.gguf).

Model ini hanya smoke test pipeline; belum dipilih sebagai model utama Benzie.
Pematokan versi menjamin sumber pengujian tercatat, bukan mengunci runtime/model
selamanya. Periksa lisensi source/model sebelum mendistribusikan binary/weights.

## Menjalankan setup

Dari root proyek, pada terminal dengan internet:

```bash
bash scripts/setup_local_runtime.sh
```

Tool yang diperlukan sudah ditemukan pada audit: Git, CMake, Ninja, GCC/G++,
curl, dan sha256sum. Script tidak memasang package sistem atau meminta sudo.
Source/build berada di `.tools/llama.cpp-v0.6.0`, yang diabaikan Git. Model
berada di `$XDG_DATA_HOME/benzie/models`, fallback `~/.local/share/benzie/models`.
Jangan memasukkan folder source/build/model tersebut ke commit.

Build Release CPU memakai 4 job agar tekanan RAM tidak terlalu besar. Tidak
membutuhkan CUDA, Vulkan SDK, OpenSSL development, Node, atau build UI web.
Opsi mengikuti [CMake pada versi terpilih](https://github.com/ggml-org/llama.cpp/blob/v0.6.0/CMakeLists.txt).
Binary tetap mempunyai library pendamping di folder build; jangan pindahkan
hanya file executable ke lokasi lain.

Script memeriksa commit source, menolak perubahan tracked pada source, memeriksa
checksum sebelum menerima model, membangun llama-server/llama-bench, lalu
memeriksa --version dan opsi CLI yang dipakai adapter Benzie. Download terputus
dapat dilanjutkan dari file `.part` dengan menjalankan script yang sama.
Jika source/artefak berbeda atau checksum gagal, setup berhenti tanpa menghapus
file tersebut. Kirim error untuk ditinjau; jangan mengabaikan checksum.

## Batas verifikasi

Kelulusan script berarti artefak dan CLI tersedia; belum membuktikan pemuatan
model, health check, prompt/response, penggunaan RAM, TTFT, atau tokens/detik.
Hal tersebut masuk langkah M2 berikutnya. Raw output saat setup hanya version/
help/build, tidak berisi conversation. Belum ada unduhan otomatis saat runtime.

Hasil 2026-10-12: pengguna berhasil menjalankan setup. Asisten memeriksa langsung
commit source, binary 0.6.0 (d812350), SHA256 dan header model, serta semua opsi
CLI yang dipakai ServerConfig: PASS. M2.2 selesai untuk setup artefak.
Build/download dilakukan melalui terminal pengguna karena DNS sesi asisten
terbatas. Model belum dimuat; benchmark belum dilakukan.
