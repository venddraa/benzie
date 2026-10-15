# Penerimaan V0.1 — M5.3

Status: **PASS, V0.1 selesai secara fungsional** pada 2026-10-15.
172 tests PASS; pengujian desktop tanpa internet dikonfirmasi pengguna.

## Hasil yang sudah diketahui

- Launcher Applications: dipasang/dibuka pengguna pada M5.2 (commit c83a3c6).
- Pilihan runtime/GGUF dan restart: dikonfirmasi aman pengguna pada M5.1.
- History new/open/continue dan konteks: dikonfirmasi aman pada M4.
- Baseline pipeline CPU Qwen3-0.6B Q8_0 tersedia di benchmark.md; kualitas model
  masih terbatas dan tidak dinilai dari throughput atau smoke test ini.
- M5.3: 172 tests PASS, lockfile check dan uv pip check PASS. Source Python
  memakai HTTPConnection ke 127.0.0.1; subprocess terbatas pada runtime lokal.
  Pemeriksaan source bukan bukti packet capture atau pengujian offline native.
- Smoke penerimaan native dicoba dari sesi asisten tetapi belum mencapai
  inference: konfigurasi model tidak ditemukan pada profil default sesi ini.
  Tidak ada konfigurasi utama yang dibuat atau diubah oleh script.
- Pengguna kemudian menjalankan script native di terminal Fedora: seluruh
  pemeriksaan PASS (generation/storage, reopen/continue, cancel/partial/isolation)
  dan data sementara dibersihkan. Pengguna kemudian mengonfirmasi internet
  dimatikan dan alur launcher/chat/history aman. Penerimaan offline terpenuhi
  berdasarkan pengujian pengguna; tidak ada packet capture yang diklaim.

## Uji penerimaan utama di Fedora

1. Buka Benzie dari Applications. Pastikan Model lokal sudah dipilih/disimpan
   pada profil utama ini (bukan hanya profil /tmp smoke sebelumnya). Tutup Benzie.
2. Matikan koneksi internet dari pengaturan desktop secara manual. Loopback
   lokal tetap diperlukan; jangan mematikan interface lo.
3. Buka Benzie dari Applications. Buat percakapan baru, kirim pesan sintetis,
   dan pastikan jawaban muncul.
4. Tutup/buka lagi, pilih percakapan yang sama dan lanjutkan. Pesan sebelumnya
   harus masih ada. Respons model yang keliru dicatat terpisah dari fungsi
   persistence/inference; Qwen3-0.6B tetap smoke model.
5. Coba Batal pada jawaban panjang, lalu kirim pesan baru. Tutup saat generation
   aktif dan buka ulang. Pastikan tidak hang dan jawaban parsial memiliki status.
6. Setelah selesai, hidupkan internet kembali sesuai kebutuhan. Laporkan hasil
   langkah yang gagal; tidak perlu mengirim isi percakapan pribadi atau database.

## Smoke core tambahan (data sementara)

Tutup semua window Benzie dahulu agar port runtime tidak dipakai. Dengan
internet masih dimatikan, dari root proyek:

```bash
.venv/bin/python scripts/acceptance_local_chat.py
```

Script hanya membaca konfigurasi runtime/model pilihan dan memakai database
sintetis di direktori sementara, kemudian menghapus data tes itu. Model/config/
history utama tidak diubah. Model tidak diunduh dan koneksi sistem tidak diubah.
Script menguji generation, reopen/continue, cancel setelah chunk pertama, status
parsial, isolasi percakapan, dan cleanup. Kualitas jawaban tidak dinilai.
Status internet tidak dideteksi otomatis: PASS alur lokal saja belum membuktikan
bahwa pengguna sudah mematikan internet atau menguji launcher.

Jika memakai profil khusus, berikan konfigurasi profil tersebut:

```bash
.venv/bin/python scripts/acceptance_local_chat.py \
  --settings /tmp/benzie-model-smoke/model-settings.json
```

## Batas V0.1 dan setelahnya

History bukan personal memory. Context penuh menghasilkan pesan penolakan,
bukan pemotongan otomatis. Runtime masih dimuat/ditutup per request. Jawaban
aktif hanya disimpan saat hasil request diketahui; crash/power loss dapat
meninggalkan pesan user tanpa jawaban. Launcher development bergantung pada
checkout/.venv yang tetap tersedia. Tidak ada multi-instance coordination.

Setelah offline acceptance dikonfirmasi, catat V0.1 selesai dan berhenti untuk
evaluasi bersama pengguna. Jangan otomatis mulai memory, RAG, tools, voice,
atau pengunduhan model berikutnya. Benchmark kualitas kandidat adalah keputusan
terpisah dengan RAM, latency, bahasa, instruksi, dan stabilitas yang terukur.
