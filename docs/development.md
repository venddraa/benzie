# Panduan development Benzie

Personal AI assistant lokal milik pengguna. Nama Benzie berasal dari kucing
jantan pertama yang diadopsi pengguna; tidak mempunyai filosofi branding tambahan.

Saat ini: **M5.3, acceptance V0.1**. Panduan: [penerimaan offline](acceptance-v0.1.md), [chat UI](chat-ui.md)
dan [launcher desktop](desktop-launcher.md). Chat/history/model settings tersedia;
memory, tools, dan voice belum diimplementasikan.
Status verifikasi terbaru ada di [current-state](current-state.md).

## Kebutuhan

- Fedora desktop dengan Python 3.12.
- `uv` untuk menyiapkan environment, mengunci dependency, dan build.
- PySide6 Widgets sebagai satu-satunya dependency runtime langsung.
- SQLite melalui standard library Python; server/CLI SQLite tidak diperlukan.

Dependency development: pytest. Build backend: Hatchling.
Pengunduhan dependency membutuhkan internet saat setup awal; aplikasi tidak
menjalankan download atau telemetry saat runtime; HTTP inference hanya loopback.
uv dikonfigurasi untuk tidak mengunduh interpreter Python otomatis.

## Setup

Dari root repository, setelah `uv` tersedia:

```bash
uv sync --locked --python /usr/bin/python3.12
```

`uv.lock` sudah tersedia. `uv lock` hanya diperlukan saat dependency sengaja
diperbarui. Review perubahan lockfile sebelum commit. Cache saja belum tentu cukup untuk
setup offline; semua wheel dan metadata yang diperlukan harus sudah tersedia.

Pada sesi development awal, uv tersedia secara lokal di `.tools/uv/bin/uv`.
Folder tersebut diabaikan Git. Gunakan path itu sebagai pengganti perintah `uv`
jika uv belum tersedia pada PATH. Tidak ada package Python sistem yang diubah.

## Menjalankan

```bash
.venv/bin/benzie
```

Alternatif: `.venv/bin/python -m benzie`.
Launcher ini menjalankan aplikasi langsung, tanpa menyinkronkan environment.
Shortcut di Applications Fedora dipasang lewat panduan launcher M5.2.

Default database adalah `$XDG_DATA_HOME/benzie/benzie.sqlite3`, atau
`~/.local/share/benzie/benzie.sqlite3` bila XDG_DATA_HOME kosong/tidak absolut.
Untuk data development terpisah:

```bash
.venv/bin/benzie --data-dir /tmp/benzie-manual-smoke
```

Folder dibuat ketika aplikasi dimulai. Pilih runtime/model melalui Model lokal;
file model-settings.json tersimpan pada direktori data yang sama. CLI
--runtime/--model/--port tetap tersedia sebagai override sementara.

## Verifikasi

```bash
.venv/bin/python -m pytest
uv build
```

Tes core tidak memerlukan display. Satu smoke test UI memakai Qt offscreen;
jika PySide6 belum tersedia, tes tersebut SKIP dan milestone belum lulus penuh.

Manual smoke test pada desktop Fedora:

1. Jalankan aplikasi dengan direktori data development di atas.
2. Pastikan window Benzie terlihat, dapat diubah ukurannya, dan menampilkan
   status SQLite siap, pilihan model, dan history.
3. Tutup window, buka lagi dengan lokasi data yang sama, lalu tutup kembali.
4. Coba lokasi data yang tidak dapat ditulis; dialog kesalahan harus menjelaskan
   kegagalan tanpa mengganti/menghapus database.

Semua tes manual menggunakan data terpisah; jangan mengubah database pribadi
untuk membuat kondisi error. Qt offscreen bukan pengganti verifikasi desktop.

## Struktur

- `app.py`: entry point dan perakitan core dengan UI.
- `config.py`: resolusi lokasi data XDG.
- `core/`: startup, orchestration chat/history, model settings; tanpa Qt.
- `persistence/`: SQLite skema 2, migrasi, dan conversation store.
- `ui/`: presentasi PySide6 Widgets.
- `tests/`: core, lokasi data, database, dan smoke test window ringan.
- `docs/`: visi, arsitektur aktual, keputusan, roadmap, dan status.

Lapisan inference mengelola llama-server dan HTTP loopback lokal.

## Workflow

Satu milestone → implementasi → test → laporan → review dan persetujuan pengguna
→ commit → push oleh pengguna. Jangan lanjut milestone berikutnya otomatis.
Asisten menyiapkan perintah siap salin; pengguna menjalankan push sendiri.
Commit memakai Bahasa Indonesia sederhana. Tidak ada force push atau perubahan
history tanpa izin. Jangan commit model, database, konfigurasi personal,
credential, log, atau training artifacts.
