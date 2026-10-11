# Status sekarang

Terakhir diperbarui: 2026-10-11.

Milestone terakhir: **1 — fondasi aplikasi desktop, selesai dan menunggu review**.
Implementasi dan seluruh automated tests lulus. Window desktop berhasil dibuka,
dikonfirmasi screenshot pengguna. Pengguna juga mengonfirmasi resize serta
tutup–buka ulang berjalan tanpa error. Konfirmasi manual test bukan izin commit.

## Sudah ditulis

- Package Python 3.12, pyproject.toml, Hatchling, entry point benzie.
- Window PySide6 Widgets sederhana, terpisah dari core.
- Resolusi data XDG/--data-dir, SQLite user_version=1, error startup.
- Basic tests untuk lokasi data, startup, SQLite, serta smoke test UI ringan.
- Dokumentasi visi, arsitektur aktual, keputusan, roadmap; .gitignore.

## Environment dan kendala

- uv 0.12.3 ditemukan sebagai wheel dalam cache lokal dan dipasang ke .tools/uv.
- .venv menggunakan /usr/bin/python3.12 (3.12.14).
- Pengguna berhasil membuat lockfile dan menjalankan uv sync melalui terminalnya
  setelah unduhan PyPI dari sesi ini terhambat DNS.
- PySide6/Qt 6.12.0 tersedia; environment sekarang memenuhi dependency proyek.
- uv.lock sudah dibuat oleh uv dan konsisten dengan pyproject.toml.
- PySide6 menarik Addons, Essentials, PDF, WebEngine, dan Shiboken sebagai
  dependency transitif. Aplikasi hanya mengimpor QtCore/QtGui melalui Widgets
  dan QtWidgets; tidak mengaktifkan fitur browser atau PDF.
- Hatchling tidak diperlukan dalam environment runtime. Build memakai isolated
  environment dari cache, tanpa menambahkannya sebagai dependency aplikasi.
- Akses desktop dari sesi ini ditolak: Wayland melaporkan Operation not permitted
  dan X11 tidak dapat dihubungi. Ini membatasi verifikasi desktop, bukan bukti
  bahwa instalasi Qt pada sesi desktop pengguna rusak.
- .git tidak dikenali sebagai repository valid dan direktori tersebut tidak
  dapat ditulis oleh sesi ini. Remote lokal belum dikonfigurasi oleh asisten.
- Pengguna sudah membuat repository https://github.com/venddraa/benzie.git.
  Pengguna menjalankan push sendiri; asisten hanya memberikan perintah siap salin.
- README disederhanakan menjadi `benzie` sesuai permintaan pengguna. Panduan
  setup, menjalankan aplikasi, dan testing dipindahkan ke docs/development.md.

## Hasil verifikasi

- Python 3.12.14, uv 0.12.3, pytest 9.1.1, PySide6/Qt 6.12.0.
- pytest: **18 PASS, tanpa SKIP**, termasuk window open/close melalui offscreen.
- Editable package dan entry point --help: PASS.
- Build sdist dan wheel dengan Hatchling dalam isolated build, offline: PASS.
- Isi paket diperiksa: source distribution memuat uv.lock dan docs; tidak
  menyertakan .venv, cache/tooling lokal, database, model, atau data pribadi.
- Pemeriksaan syntax Python: PASS.
- uv pip check: PASS.
- uv lock --check --offline: PASS.
- Window desktop: PASS untuk launch/tampilan berdasarkan screenshot pengguna.
  Terlihat judul Benzie, status SQLite siap (skema 1), dan database development
  /tmp/benzie-manual-smoke/benzie.sqlite3. Layout terlihat utuh.
- Resize dan tutup–buka ulang pada desktop nyata: PASS berdasarkan konfirmasi
  eksplisit pengguna setelah screenshot.
- Jalur kegagalan database diuji otomatis pada core. Tampilan dialog error
  pada desktop nyata belum diuji manual; tidak diklaim PASS.
- Startup tanpa PySide6 memberikan pesan error dan exit code 1.

Target Milestone 1 tercapai: package berjalan, window desktop terbuka, SQLite
diinisialisasi, UI/core terpisah, basic tests lulus. Penggunaan RAM/CPU pada sesi
desktop nyata belum diukur; tidak ada model atau inference.

## Menjalankan hasil Milestone 1

Di terminal desktop Fedora, dari root proyek:

```bash
.venv/bin/benzie --data-dir /tmp/benzie-manual-smoke
```

Window, resize, dan restart sudah dikonfirmasi pengguna. Tidak perlu mengunduh
ulang dependency untuk menjalankan aplikasi.
Perintah Git init, konfigurasi remote, commit, dan push diserahkan untuk
dijalankan dari terminal pengguna. Remote: https://github.com/venddraa/benzie.git.

## Belum diimplementasikan

LLM/model, llama-server, chat, history, model settings, launcher Applications,
memory, RAG, file search, tools, shell, voice, vision, avatar, fine-tuning.

Qwen3-0.6B hanya disetujui sebagai smoke test Milestone 2, bukan model utama.

## Gerbang review

Tidak commit/push sebelum pengguna review dan menyetujui.
Usulan pesan commit: `menyiapkan fondasi aplikasi Benzie`.
Pengguna meminta perintah siap salin untuk commit/push dan menjalankan push
sendiri. Asisten belum menjalankan commit/push. Jangan mulai Milestone 2 otomatis.
