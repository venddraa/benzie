# Arsitektur saat ini

Implementasi desktop/core/inference, history, dan konfigurasi model M5.1.

M5.2 menambahkan installer shortcut development scripts/desktop_launcher.py.
Desktop entry per-user menunjuk interpreter .venv absolut (tanpa resolve
symlink interpreter agar venv tetap berlaku), argumen -m benzie, Terminal=false,
tanpa shell atau uv sync. Python package tetap berasal dari checkout editable.
Default data XDG diselesaikan oleh aplikasi saat launch; --data-dir opsional
untuk profil terpisah. Nama desktop file benzie sesuai DesktopFileName Qt.

```text
app.py (entry point)
  ├── config.py → lokasi data
  ├── core.startup → persistence.database → SQLite lokal
  └── ui.main_window ← StartupState + ChatService
        └── ChatWorker (QThread) → core.chat → InferenceEngine → llama-server
```

`app.py` membuat QApplication, meminta core menginisialisasi data, kemudian
menampilkan window. Kegagalan startup ditampilkan melalui dialog dan exit code 1.

Core tidak mengimpor PySide6. `StartupState` hanya membawa path database dan
versi skema ke UI. UI tidak membuka koneksi database.

SQLite versi skema 2 memiliki tabel conversations (id/title/created_at/updated_at)
dan messages (id/conversation_id/role/content/status/created_at). Migrasi dari
skema 1 dan penanda user_version berada dalam satu transaksi. Versi lebih baru
ditolak tanpa downgrade. Koneksi ditutup setelah operasi.

ConversationStore di persistence/conversations.py menyediakan CRUD terbatas:
create/get/list conversation dan append/list message, tanpa edit/delete dulu.
Satu koneksi per operasi dengan foreign_keys aktif; insert pesan dan update
aktivitas percakapan atomik. Timestamp UTC, pesan diurutkan ID, percakapan
berdasarkan updated_at DESC lalu ID DESC. Status completed/cancelled/failed
menandai hasil akhir; jawaban gagal/dibatalkan boleh kosong. Store mengharuskan
database sudah diinisialisasi dan tidak membuat file pengganti bila hilang.
Sejak M4.2, core/history.py membungkus request inference dengan penyimpanan input
dan hasil/status di worker. UI memakai HistoryService untuk new/list/open;
tidak menjalankan SQL. Pemilihan percakapan dikunci selama generation. Request
menyimpan ID percakapan tetap. Hasil disimpan setelah cleanup engine. Kegagalan
penyimpanan ditampilkan, transcript dipertahankan, auto-close dibatalkan dan
kontrol history/send dinonaktifkan sampai aplikasi dibuka ulang.

Default data mengikuti XDG_DATA_HOME, dengan fallback `~/.local/share/benzie`.
`--data-dir` memungkinkan lokasi development/test terpisah. Resolusi lokasi
sendiri tidak membuat direktori. core/model_settings.py menyimpan konfigurasi
runtime/model/port versi 1 di <data-dir>/model-settings.json, permission 0600,
temporary file + fsync + atomic replace. Penempatan per data-dir menjaga profil
development dan utama terpisah. Konfigurasi rusak tidak ditimpa otomatis;
history tetap bisa dibaca, pilihan bisa diperbaiki melalui dialog Model lokal.
Validasi hanya file/executable/header; pemuatan weights dilakukan worker saat
pesan dikirim. CLI override bersifat sementara, Save dialog bersifat persisten.
Dialog hanya presentation; service/engine factory tetap dibuat oleh core.

Logging hanya event lifecycle ke stderr, tanpa log file atau isi conversation.
Transcript direkonstruksi dari SQLite ketika membuka percakapan; chunk aktif
berada di widget sampai hasil akhir disimpan. Tidak ada autosave per token.

Chat desktop memanggil core melalui worker. Adapter memakai HTTP loopback, tanpa cloud,
shell, package manager, atau downloader.
PySide6 satu-satunya dependency runtime langsung; SQLite/config/logging memakai
standard library. UI menggunakan Widgets bawaan tanpa design system.

`inference/server.py` menyediakan ServerConfig dan LocalServerProcess,
digunakan engine lewat core/worker. Modul memakai subprocess dengan shell=False untuk
menjalankan binary runtime lokal; tidak memberikan shell/tools kepada model.
Parameter dibatasi pada file lokal, port, context, dan threads. Binding loopback,
offline, CPU, serta penonaktifan web UI/agent/projector ditetapkan eksplisit.
Environment LLAMA_* tidak diwarisi agar konfigurasi eksternal tidak mengaktifkan
fitur lain. API key acak engine ditetapkan melalui environment child. stderr
dibaca thread daemon; hanya hint generik disimpan, tanpa baris mentah. stdout
dibuang. Tidak ada prompt/jawaban/API key yang dicatat ke log.

Start/stop tetap pada thread pemilik; request_stop boleh lintas thread dan hanya
mengirim kill pada child sendiri di bawah lock, tanpa wait. Worker melakukan
reap. Shutdown normal menunggu
3 detik sebelum kill lalu menunggu maksimal 3 detik lagi. Handle dipertahankan
jika cleanup gagal. Proses hidup tidak dianggap model siap.

`inference/engine.py` menyediakan protocol InferenceEngine dan adapter sinkron
LlamaServerEngine. Startup memakai deadline, /health, dan /v1/models dengan API
key untuk verifikasi server. HTTPConnection hanya menuju 127.0.0.1 tanpa proxy
atau redirect. Model ID dibaca dari runtime. generate menerima teks/system
prompt, mengambil message.content, serta menutup proses saat error/timeout I/O.
Start/generate/close dipakai berurutan pada satu thread pemilik. Satu pengecualian
eksplisit: cancel boleh lintas thread untuk flag Event dan sinyal ke child.

System prompt dasar di core/prompts.py tidak mengklaim file/tools/memory.
Smoke script mengirim satu prompt sintetis dan selalu menutup engine.
generate_stream sekarang membaca SSE, menghasilkan GenerationEvent berisi teks
serta statistik token/timing. EOF tanpa DONE ditolak. Error dan early close
menghentikan proses; stream sukses tetap memuat model. Pemanggil harus menutup
iterator jika berhenti dini. History percakapan aktif masuk prompt sejak M4.3:
core memilih pasangan user/assistant selesai, mengecualikan failed/cancelled/
yatim. Adapter memvalidasi role, memakai /apply-template dengan opsi thinking
yang sama, lalu /tokenize (add_special/parse_special true). Cadangan output dan
32 token khusus diperhitungkan terhadap context_size. Jika melebihi kapasitas,
request ditolak tanpa menghapus history; tidak ada pemotongan otomatis.
Payload dibatasi 1 MiB sebelum preflight. Respons endpoint dibatasi 2 MiB
seperti request JSON lain. Gagal preflight tidak meneruskan generation.

`core/chat.py` menyediakan ChatService dan ChatRequest, tanpa Qt. Request dibuat
sebelum worker start, menyimpan flag cancel serta handle engine di bawah lock.
Factory hanya konstruksi tanpa I/O. Engine dibuat/dipakai/close di worker;
core menyampaikan event loading/generating/text dan memastikan cleanup.
Runtime dimuat/ditutup per pesan pada baseline M3.1. `ui/chat_worker.py` hanya
menjalankan core di QThread dan mengirim signal ke window. Widget memodifikasi
transcript dengan plain text agar teks pengguna/model tidak dianggap HTML.
Satu request aktif; kontrol input dinonaktifkan sampai selesai/error.

Tombol Batal meminta cancellation, mengabaikan chunk yang sudah antre setelah
cancel, dan mempertahankan jawaban parsial. Close aktif meminta cancellation,
menunggu finished/cleanup asinkron, lalu menutup; tidak memakai QThread.terminate.
Pembatalan sebelum spawn dicek kembali setelah spawn agar tidak meninggalkan
runtime baru. cancel engine bersifat terminal; request berikutnya engine baru.
app.py menerima pasangan
--runtime/--model serta --port untuk konfigurasi sementara; tidak menetapkan
model tertentu sebagai default identitas desktop. Tanpa keduanya, konfigurasi
tersimpan digunakan; bila belum valid input nonaktif sampai dipilih melalui UI.

inference/benchmark.py membaca metrik Linux proses milik engine, dan script
benchmark mengukur tiga restart dengan prompt sintetis. JSON hanya metrik,
di data/ yang diabaikan Git; bukan conversation persistence. Pengukuran asli
pipeline lulus tiga restart di terminal pengguna. Hasil dan definisi metrik
tercatat di docs/benchmark.md; tidak menyatakan kualitas model dari throughput.

Opsi CLI diperiksa terhadap [dokumentasi resmi llama-server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
pada 2026-10-12 dan diverifikasi terhadap binary v0.6.0 (d812350) pada M2.2.
Kontrak health/models/chat mengikuti dokumentasi versi v0.6.0. Smoke test asli
lulus di terminal pengguna: startup, respons teks, dan cleanup. Socket tetap
ditolak pada sesi asisten, sehingga eksekusi inference dilakukan pengguna.
