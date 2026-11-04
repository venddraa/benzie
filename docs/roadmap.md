# Roadmap

Milestone implementasi berbeda dari nomor versi produk.

| Milestone | Scope | Status |
| --- | --- | --- |
| 0 | Audit tanpa perubahan sistem | Selesai; fondasi disetujui |
| 1 | Python, window Widgets, inisialisasi SQLite, basic tests, docs | Selesai; sudah di-commit/push pengguna |
| 2 | llama-server + satu model kecil, prompt/response, benchmark | Selesai; di-commit/push pengguna |
| 3 | Hubungkan inference ke UI; streaming/cancel dan error handling | Di-commit 1be56d3; pengguna menyatakan fitur aman |
| 4 | New/open/continue conversation; persistence pesan | Selesai, commit 0c46f90; manual dikonfirmasi aman |
| 5 | Launcher Fedora, pemilihan model, polish dan acceptance offline | Selesai: 172 tests PASS dan desktop offline dikonfirmasi pengguna |

V0.1 berhasil bila aplikasi dibuka dari desktop Fedora, model lokal dapat
dipilih/dimuat, chat bekerja, dan history bertahan setelah restart, termasuk
ketika internet tidak tersedia. Setelah itu berhenti untuk evaluasi.

2026-10-15: definisi sukses V0.1 dikonfirmasi terpenuhi pengguna dengan internet
dimatikan. Berhenti untuk evaluasi. Kualitas model masih perlu benchmark
kandidat terpisah; belum mengunduh atau memilih model utama berikutnya.

2026-10-18: pengguna meminta lanjut. E1 menyiapkan suite/runner evaluasi model
lokal (178 tests PASS); baseline kualitas model asli belum dijalankan. Ini
evaluasi pasca-V0.1, bukan implementasi memory atau fitur V0.2 otomatis.
Panduan dan shortlist: model-evaluation.md. Setiap unduhan kandidat dipisahkan
agar file/revision/checksum dan kompatibilitas dapat diperiksa terlebih dahulu.

2026-10-20: E1 di-commit. E2 menyiapkan script artefak resmi Qwen3-1.7B Q8_0
berpin (184 tests PASS). Baseline full suite, unduhan dan load kandidat pending;
tidak mengubah model utama. Panduan: qwen17-experiment.md.

2026-11-02: E2 di-commit. E3 memverifikasi weights kandidat dan mereview baseline
10 kasus (penilaian manual asisten 9/20). Native load/evaluasi 1.7B menunggu
terminal pengguna karena socket sesi asisten ditolak. Tidak ada perubahan fitur.

2026-11-02 E4: smoke/evaluasi 1.7B native pengguna PASS; review manual 11/20
vs baseline 9/20. Performance diukur pada kondisi RAM/swap berbeda. Hasil
didokumentasikan, tidak memilih model utama atau mengunduh kandidat berikutnya.

2026-11-02 E5: runner pengukuran ulang berpasangan siap (192 tests PASS),
native pending. Satu pasangan awal sebelum pengulangan lebih banyak. Tidak
memilih model utama atau mengubah runtime/prompt/model desktop.

2026-11-04 E6: pasangan native lengkap direview. RAM/swap sebelum kedua run
lebih sebanding; 1.7B TTFT 1,071 s, decode 24,31 tok/s. Jawaban identik dengan
sebelumnya, skor manual tetap 9/20 vs 11/20. Usulan eksperimen sampling resmi
Qwen terpisah, belum diimplementasikan. Tidak menetapkan model utama.

2026-11-04 UI1: atas permintaan pengguna, eksperimen sampling ditunda untuk
perapian UI sunset (sidebar/chat/composer multiline). 196 tests PASS dan
preview offscreen diperiksa; commit disetujui pengguna, manual Fedora pending. Tetap
PySide6 Widgets, tanpa fitur memory/RAG atau perubahan model.

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
