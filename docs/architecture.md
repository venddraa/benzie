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

Logging hanya event startup, kesiapan skema, jenis kegagalan, dan shutdown ke
stderr; tidak membuat log file. Tidak ada conversation atau inference saat ini.

Runtime tidak memanggil jaringan, shell, package manager, atau downloader.
PySide6 satu-satunya dependency runtime langsung; SQLite/config/logging memakai
standard library. UI menggunakan Widgets bawaan tanpa design system.

`inference/server.py` menyediakan ServerConfig dan LocalServerProcess, belum
dihubungkan ke app/UI. Modul memakai subprocess dengan shell=False untuk
menjalankan binary runtime lokal; tidak memberikan shell/tools kepada model.
Parameter dibatasi pada file lokal, port, context, dan threads. Binding loopback,
offline, CPU, serta penonaktifan web UI/agent/projector ditetapkan eksplisit.
Environment LLAMA_* tidak diwarisi agar konfigurasi eksternal tidak mengaktifkan
fitur lain. Output native dibuang sementara; log hanya lifecycle generik.

Pemanggil wajib stop dan memakai thread pemilik yang sama. Shutdown menunggu
3 detik sebelum kill lalu menunggu maksimal 3 detik lagi. Handle dipertahankan
jika cleanup gagal. Proses hidup tidak dianggap model siap. Belum ada health
check, InferenceEngine, HTTP client, generation, atau worker UI.

Opsi CLI diperiksa terhadap [dokumentasi resmi llama-server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
pada 2026-10-12. Belum diverifikasi terhadap binary terpasang; versi runtime
akan dipatok dan kecocokan opsi diperiksa pada langkah berikutnya.
