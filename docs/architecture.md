# Arsitektur saat ini

Implementasi Milestone 1; bukan deskripsi fitur yang belum dibangun.

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

Belum ada InferenceEngine, worker inference, HTTP client, model loader, atau
abstraksi tools. Strategi llama-server telah disetujui untuk tahap berikutnya,
tetapi belum diimplementasikan.
