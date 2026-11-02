# E2 — persiapan kandidat Qwen3-1.7B

2026-10-20. Tujuan: menyiapkan artefak pembanding setelah alat evaluasi E1
terverifikasi. Belum memilih model utama atau mengubah konfigurasi aplikasi.

## Penyesuaian quantization

Rencana awal Q4_K_M belum memiliki artefak resmi terverifikasi. Pada revision
yang diperiksa, repository resmi hanya mencantumkan Q8_0. Eksperimen pertama
memakai Q8_0: publisher resmi, checksum tersedia, quantization sama dengan
baseline 0.6B. Ini eksperimen skala parameter dengan quant yang sama, bukan
perbandingan di batas ukuran file/RAM yang sama. Q4 dapat diuji terpisah nanti.
RAM/latency Q8_0 tetap harus diukur; file weights bukan total RAM runtime.

Sumber: [tree resmi Qwen](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/tree/90862c4b9d2787eaed51d12237eafdfe7c5f6077)
dan [metadata file pada revision tetap](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/blob/90862c4b9d2787eaed51d12237eafdfe7c5f6077/Qwen3-1.7B-Q8_0.gguf).

Artefak:

```text
Repository: Qwen/Qwen3-1.7B-GGUF
Revision: 90862c4b9d2787eaed51d12237eafdfe7c5f6077
File: Qwen3-1.7B-Q8_0.gguf
Ukuran publik: sekitar 1,83 GB
SHA256: 061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a
Lisensi repository: Apache-2.0
```

## Langkah pengguna

Tutup Benzie dan aplikasi berat. Baseline yang tersedia baru 3/10 kasus.
Lengkapi dahulu memakai model 0.6B yang sama:

```bash
.venv/bin/python scripts/evaluate_local_model.py \
  --binary .tools/llama.cpp-v0.6.0/build-cpu/bin/llama-server \
  --model /home/vendra/.local/share/benzie/models/Qwen3-0.6B-Q8_0.gguf
```

Setelah baseline berjalan, siapkan kandidat (internet diperlukan untuk unduhan):

```bash
bash scripts/setup_qwen17_candidate.sh
```

Default file di $XDG_DATA_HOME/benzie/models atau ~/.local/share/benzie/models.
Argumen direktori opsional tersedia untuk staging/test. Source runtime tidak
dibangun ulang. Tidak ada config desktop/history/model lama yang diubah.
Jalankan satu installer saja pada direktori yang sama.

Script memakai HTTPS, download resumable ke .part, verifikasi SHA256, lalu
mempublikasikan lewat hard link atomik tanpa overwrite file final. File yang
sudah valid dipakai ulang tanpa unduh. File final salah checksum ditolak dan
dipertahankan. Checksum download gagal meninggalkan .part untuk diperiksa;
jangan anggap itu model valid atau melanjutkan inference dengannya.
Setelah verified, nama .part dihapus; file weights yang sama tersedia pada
nama final. Tidak menghapus model yang sudah ada.

## Status dan checkpoint berikutnya

184 tests PASS, termasuk fixture download sukses, reuse offline, kegagalan
network/checksum, file lama, symlink, dan syntax Bash. Tes tidak mengunduh
weights dan tidak mengklaim kompatibilitas native. Tidak ada dependency baru.

Unduhan/model load/evaluasi 1.7B belum dijalankan oleh asisten. Sesi ini hanya
bisa menulis workspace dan /tmp; model directory utama disiapkan pengguna.
Baseline full suite juga masih menunggu terminal pengguna karena socket
runtime sesi asisten sebelumnya ditolak.

Checkpoint setelah artefak verified: smoke native 1.7B lalu evaluasi 10 kasus
dengan runtime/suite/parameter yang sama. Bandingkan jawaban/rubrik dan metrik,
bukan ukuran model saja. Jangan mengganti model utama berdasarkan keberhasilan
download. Tidak memulai memory/RAG/voice atau fine-tuning.

Pembaruan 2026-11-02: unduhan sudah tersedia dan checksum cocok. Baseline
lengkap juga tersedia. Native load kandidat belum terverifikasi karena socket
sesi asisten ditolak. Lanjutkan [review baseline E3](model-baseline-review.md).
