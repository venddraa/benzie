# Arsitektur saat ini

Implementasi desktop Milestone 1 dan modul lifecycle proses pada langkah M2.1.

```text
app.py (entry point)
  ├── config.py → lokasi data
  ├── core.startup → persistence.database → SQLite lokal
  └── ui.main_window ← StartupState
```

`app.py` membuat QApplication, meminta core menginisialisasi data, kemudian
menampilkan window. Kegagalan startup ditampilkan melalui dialog dan exit code 1.

Core tidak mengimpor PySide6. `StartupState` hanya membawa path database dan
versi skema ke UI. UI tidak membuka koneksi database.

SQLite versi skema 1 hanya memiliki penanda `PRAGMA user_version`; belum ada
tabel produk. Inisialisasi dilakukan dalam transaksi, koneksi ditutup setelah
selesai. Database versi lebih baru ditolak tanpa downgrade. SQLite invalid atau
lokasi yang tidak dapat digunakan menghasilkan error yang bisa dijelaskan UI.
Tabel dan repository percakapan baru diperlukan pada Milestone 4.

Default data mengikuti XDG_DATA_HOME, dengan fallback `~/.local/share/benzie`.
`--data-dir` memungkinkan lokasi development/test terpisah. Resolusi lokasi
sendiri tidak membuat direktori. File config JSON belum diperlukan saat ini.

Logging hanya event lifecycle ke stderr, tanpa log file atau isi conversation.
Aplikasi desktop belum mempunyai chat/inference aktif.

Desktop belum memanggil runtime. Adapter memakai HTTP loopback, tanpa cloud,
shell, package manager, atau downloader.
PySide6 satu-satunya dependency runtime langsung; SQLite/config/logging memakai
standard library. UI menggunakan Widgets bawaan tanpa design system.

`inference/server.py` menyediakan ServerConfig dan LocalServerProcess, belum
dihubungkan ke app/UI. Modul memakai subprocess dengan shell=False untuk
menjalankan binary runtime lokal; tidak memberikan shell/tools kepada model.
Parameter dibatasi pada file lokal, port, context, dan threads. Binding loopback,
offline, CPU, serta penonaktifan web UI/agent/projector ditetapkan eksplisit.
Environment LLAMA_* tidak diwarisi agar konfigurasi eksternal tidak mengaktifkan
fitur lain. API key acak engine ditetapkan melalui environment child. stderr
dibaca thread daemon; hanya hint generik disimpan, tanpa baris mentah. stdout
dibuang. Tidak ada prompt/jawaban/API key yang dicatat ke log.

Pemanggil wajib stop dan memakai thread pemilik yang sama. Shutdown menunggu
3 detik sebelum kill lalu menunggu maksimal 3 detik lagi. Handle dipertahankan
jika cleanup gagal. Proses hidup tidak dianggap model siap.

`inference/engine.py` menyediakan protocol InferenceEngine dan adapter sinkron
LlamaServerEngine. Startup memakai deadline, /health, dan /v1/models dengan API
key untuk verifikasi server. HTTPConnection hanya menuju 127.0.0.1 tanpa proxy
atau redirect. Model ID dibaca dari runtime. generate menerima teks/system
prompt, mengambil message.content, serta menutup proses saat error/timeout I/O.
API dipakai berurutan dari satu pemanggil/thread, belum thread-safe.

System prompt dasar di core/prompts.py tidak mengklaim file/tools/memory.
Smoke script mengirim satu prompt sintetis dan selalu menutup engine.
Belum ada streaming, worker UI, history dalam prompt, atau benchmark lengkap.

Opsi CLI diperiksa terhadap [dokumentasi resmi llama-server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
pada 2026-10-12 dan diverifikasi terhadap binary v0.6.0 (d812350) pada M2.2.
Kontrak health/models/chat mengikuti dokumentasi versi v0.6.0. Smoke test asli
lulus di terminal pengguna: startup, respons teks, dan cleanup. Socket tetap
ditolak pada sesi asisten, sehingga eksekusi inference dilakukan pengguna.
