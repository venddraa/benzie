# Status sekarang

Terakhir diperbarui: 2026-10-12.

Milestone aktif: **2 — integrasi inference lokal**, dikerjakan per langkah kecil.
Milestone 1 selesai dan sudah di-commit (`6d9c5c9`); pengguna mengonfirmasi push.
Window desktop, resize, dan tutup–buka ulang telah dikonfirmasi pengguna.

## Langkah M2.1 — lifecycle proses, sudah di-commit

Commit lokal: `c93982f`. Worktree bersih saat memulai langkah M2.2.

- ServerConfig memvalidasi executable, keberadaan model/header GGUF, port,
  context size, dan threads. Header GGUF bukan validasi model lengkap.
- LocalServerProcess mengelola satu child process tanpa shell, dengan start,
  status proses hidup, stop, timeout shutdown, dan kill bila diperlukan.
- Argumen eksplisit: loopback 127.0.0.1, offline, CPU, satu slot, tanpa web UI,
  agent, atau multimodal projector. Environment LLAMA_* dan token HF disaring.
- Baseline M2.1 memakai mock subprocess. is_running hanya berarti proses hidup,
  bukan model siap. Diagnosis dan health check ditambahkan pada M2.3.
- Full suite: **34 PASS** (18 sebelumnya + 16 tes runtime); diff check PASS.

## Langkah M2.2 — setup artefak selesai, sudah di-commit

Commit lokal: `6d45061`. Worktree bersih saat memulai M2.3.

- scripts/setup_local_runtime.sh menyiapkan source llama.cpp v0.6.0 yang dipatok,
  build Release CPU, dan GGUF resmi Qwen3-0.6B Q8_0 dengan revision/SHA256 tetap.
- Setup manual terpisah dari runtime aplikasi; tidak ada dependency Python baru.
- Panduan/source/checksum tercatat di docs/local-runtime.md.
- Script memeriksa commit, checksum, dan kompatibilitas opsi CLI setelah build.
- Pengguna berhasil menjalankan script setup; source/build/model tersedia lokal.
- Pemeriksaan langsung asisten: source commit
  d81235049384534c167caea52b85a694f6103d14, binary 0.6.0 (d812350), SHA256 model
  sesuai pin, header GGUF dan semua opsi CLI adapter: PASS.
- Syntax Bash, build package, lockfile, dan diff check: PASS; tes aplikasi tetap
  34 PASS. Tidak ada dependency Python baru.
- Model belum dimuat. Belum ada hasil inference atau benchmark yang diklaim.
- Health check, adapter prompt/response, dan benchmark masuk langkah berikutnya.

## Langkah M2.3 — adapter teks selesai, siap review/push

- Protocol InferenceEngine dan LlamaServerEngine: start, generate sinkron, close;
  tanpa Qt atau dependency baru. System prompt dasar berasal dari core.
- HTTP standard library ke 127.0.0.1 tanpa proxy/redirect. API key acak per engine
  melalui environment child dan header HTTP; tidak disimpan ke config/log.
- /health menunggu status ok; /v1/models terautentikasi memverifikasi server
  milik engine. ID model berasal dari runtime. Thinking dinonaktifkan pada
  request smoke test; respons belum streaming.
- Deadline startup, timeout I/O generation, serta cleanup ketika error/timeout.
  Smoke script menangani Ctrl+C. API digunakan berurutan, belum thread-safe.
- stderr native dibaca thread daemon; hanya hint generik port/model/memori/
  argumen dipertahankan. Prompt, jawaban, API key, dan baris mentah tidak dilog.
- scripts/smoke_local_inference.py memakai prompt sintetis tanpa persistence.
- **62 tests PASS**, termasuk mock HTTP/process, timeout, metadata invalid,
  redirect, dan diagnosis. diff check PASS.
- Smoke test asli di sesi asisten gagal sebelum memuat model: socket ditolak
  (`PermissionError: Operation not permitted`). Cleanup dijalankan.
- Pengguna menjalankan script di terminal desktop: **smoke test PASS**. Model
  siap dalam 1,02 detik, respons teks Bahasa Indonesia diterima, dan proses
  runtime ditutup. Durasi satu startup ini bukan benchmark lengkap atau TTFT.
- Inference asli terverifikasi untuk satu prompt sintetis. Kualitas jawaban
  belum dievaluasi; Qwen3-0.6B tetap hanya model smoke test. UI belum berubah.
- Benchmark RAM/load time/TTFT/tokens per second tetap langkah berikutnya.

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
- Repository lokal sekarang valid; worktree bersih sebelum pekerjaan M2.1.
  origin mengarah ke https://github.com/venddraa/benzie.git. Metadata Git tetap
  read-only pada sesi asisten; commit/push diserahkan kepada pengguna.
- Pengguna sudah membuat repository https://github.com/venddraa/benzie.git.
  Pengguna menjalankan push sendiri; asisten hanya memberikan perintah siap salin.
- README disederhanakan menjadi `benzie` sesuai permintaan pengguna. Panduan
  setup, menjalankan aplikasi, dan testing dipindahkan ke docs/development.md.

## Hasil verifikasi Milestone 1 (baseline)

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

Streaming, benchmark lengkap, chat UI, history, model settings, launcher Applications,
memory, RAG, file search, tools, shell, voice, vision, avatar, fine-tuning.

Qwen3-0.6B hanya disetujui sebagai smoke test Milestone 2, bukan model utama.

## Gerbang review

Tidak commit/push sebelum pengguna review dan menyetujui.
Usulan pesan commit M2.3: `menambah inference teks lokal`.
Pengguna meminta perintah siap salin untuk commit/push dan menjalankan push
sendiri. Asisten belum menjalankan commit/push M2.3. Berhenti setelah langkah
kecil yang telah lolos tes; tunggu pengguna sebelum langkah berikutnya.
