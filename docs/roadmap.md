# Roadmap

Milestone implementasi berbeda dari nomor versi produk.

| Milestone | Scope | Status |
| --- | --- | --- |
| 0 | Audit tanpa perubahan sistem | Selesai; fondasi disetujui |
| 1 | Python, window Widgets, inisialisasi SQLite, basic tests, docs | Selesai; sudah di-commit/push pengguna |
| 2 | llama-server + satu model kecil, prompt/response, benchmark | Selesai; di-commit/push pengguna |
| 3 | Hubungkan inference ke UI; streaming/cancel dan error handling | Di-commit 1be56d3; pengguna menyatakan fitur aman |
| 4 | New/open/continue conversation; persistence pesan | Selesai, commit 0c46f90; manual dikonfirmasi aman |
| 5 | Launcher Fedora, pemilihan model, polish dan acceptance offline | M5.2 launcher dikonfirmasi berfungsi pengguna; offline acceptance berikutnya |

V0.1 berhasil bila aplikasi dibuka dari desktop Fedora, model lokal dapat
dipilih/dimuat, chat bekerja, dan history bertahan setelah restart, termasuk
ketika internet tidak tersedia. Setelah itu berhenti untuk evaluasi.

M2 dibagi menjadi langkah kecil: lifecycle proses → setup runtime/model yang
dipatok → health check dan prompt/response → benchmark. Masing-masing langkah
diuji, dilaporkan, lalu pengguna dapat commit/push sebelum melanjutkan.

Semua milestone membutuhkan test relevan dan review pengguna. Commit/push
menunggu persetujuan; jangan otomatis melanjutkan milestone berikutnya.

M4 dipecah: store/migrasi → new/open/save history di desktop → konteks percakapan
ke inference dengan batas context. M4.1 belum menyimpan percakapan dari UI.

Arah setelah V0.1 (belum disepakati sebagai pekerjaan aktif): penyempurnaan
conversation management, memory, semantic retrieval, Recall/file search, RAG,
permission-based tools, desktop integration, STT, TTS, wake word, vision,
advanced memory, fine-tuning perilaku, avatar terpisah. Urutan dapat berubah.

Tidak ada implementasi kemampuan tersebut pada Milestone 1. Training eksternal
tidak menjadi dependency runtime dan tidak mengizinkan upload data pribadi
secara otomatis.
