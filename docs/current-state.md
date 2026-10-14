# Status sekarang

Terakhir diperbarui: 2026-10-14.

Milestone aktif: **4 — history lokal**, per langkah kecil.

## Checkpoint terbaru — M4.1

- M3.2 sudah di-commit (`1be56d3`). Pengguna menyatakan fitur aman; kualitas
  jawaban masih bermasalah (contoh definisi RAG salah). Qwen3-0.6B tetap smoke
  test; penyebab kualitas belum diisolasi melalui benchmark kandidat.
- Skema SQLite 2: conversations/messages, foreign key, indeks urutan pesan.
  Migrasi dari skema 1 transaksional, tidak menghapus data yang sudah ada.
- ConversationStore tanpa Qt: buat/ambil/daftar percakapan, tambah/daftar pesan.
  Pesan memiliki status completed/cancelled/failed; jawaban parsial dibedakan.
  Urutan pesan memakai ID, bukan timestamp; update aktivitas dan insert atomik.
- **123 tests PASS**, termasuk reopen, isolasi percakapan, teks literal,
  rollback migrasi/insert, foreign key, dan smoke UI offscreen.
- UI belum memakai store: chat saat ini tetap sementara dan tiap pesan
  dijawab terpisah. Belum ada konteks multi-turn atau personal memory.
- Langkah berikutnya setelah review: hubungkan new/open/save history ke UI/core.
- Usulan commit: `menambah penyimpanan riwayat percakapan lokal`.
  Belum di-commit/push oleh asisten. Catatan di bawah adalah riwayat checkpoint.

Milestone 2 selesai dan di-commit (`4d7b2e1`); worktree bersih sebelum M3.1.
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

## Langkah M2.3 — adapter teks selesai, sudah di-commit

Commit lokal: `42f119b`; pengguna mengonfirmasi push. Worktree bersih sebelum M2.4.

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

## Langkah M2.4 — benchmark dan streaming selesai, sudah di-commit

- generate_stream menghasilkan event teks/usage/timing, tanpa dependency baru.
  Parser SSE memvalidasi DONE, respons invalid, batas ukuran, dan metadata.
  Error atau early close menghentikan generation/proses; sukses tetap siap.
- Script benchmark: tiga restart proses, metrik tiap run dan median, model bytes,
  load, TTFT client, decode tokens/sec, RSS/HWM dan CPU runtime melalui /proc.
- Prompt sintetis tetap. JSON di data/ yang diabaikan Git, tanpa prompt, jawaban,
  API key, atau path personal. Laporan yang sudah ada tidak ditimpa.
- **80 tests PASS**, build/syntax/diff check PASS. Socket ditolak pada sesi
  asisten; pengguna menjalankan benchmark asli dari terminal desktop.
- Tiga pengulangan PASS; JSON lokal diperiksa asisten, summary konsisten dengan
  setiap run dan seluruh run menghasilkan 128 token.
- Qwen3-0.6B Q8_0, file 639.446.688 bytes; CPU empat thread, context 2.048.
  Median load 1,0355 s, TTFT client 0,4954 s, decode 43,1655 tok/s.
  Peak RSS terbesar 948.899.840 bytes (904,94 MiB). Average CPU tiap run
  291,78–297,79% (sekitar tiga core); bukan persentase seluruh CPU laptop.
- Hasil di data/benchmark-20261012T061828308289Z.json tetap diabaikan Git.
  Angka ringkas dan batas interpretasi dicatat di docs/benchmark.md.
- Baseline native llama-bench berhasil dijalankan: pp128 197,94 ± 19,36 tok/s,
  tg128 47,31 ± 0,65 tok/s, CPU empat thread, tiga sampel, warmup default.
  Ini microbenchmark tanpa HTTP, bukan hasil TTFT/load/RAM pipeline.
- Definisi metrik/cache/CPU terdapat di docs/benchmark.md. UI belum berubah.

Target Milestone 2 tercapai: runtime/model lokal, prompt/response, streaming,
serta baseline ukuran/load/RAM/TTFT/tokens per second terukur. Kualitas model
belum dievaluasi; Qwen3-0.6B tetap model smoke test.

## Langkah M3.1 — UI chat dasar, sudah di-commit

Commit lokal: `ea1dc7d`; worktree bersih sebelum memulai M3.2.

- ChatService di core mengelola satu pesan, event loading/generating/text, dan
  cleanup engine. Tidak mengimpor Qt dan tidak menyimpan chat ke SQLite.
- ChatWorker memakai QThread dan signal; engine dibuat/dipakai di worker.
- UI: transcript plain text, input, Kirim/Enter, status, streaming, dan error.
  Satu request aktif; input dibuka kembali ketika selesai atau gagal.
- --runtime/--model CLI eksplisit; keduanya opsional tetapi harus diberikan
  bersama untuk mengaktifkan chat. Model tidak di-hardcode ke desktop app.
- Runtime dimuat/ditutup per pesan. Transcript sementara; setiap pesan dijawab
  terpisah tanpa konteks sebelumnya. Close saat aktif menunggu worker selesai;
  tombol cancel/pembatalan responsif belum ditambahkan.
- **89 tests PASS**, build/diff check PASS; tidak ada dependency baru.
- Test UI offscreen memakai fake service: streaming literal, pesan berulang,
  error/input, dan close menunggu worker.
- Pengguna menunjukkan respons model asli melalui UI untuk beberapa pesan;
  respons menjadi sapaan Inggris berulang dan tidak mengikuti permintaan bahasa.
  Streaming/responsivitas/close desktop belum dikonfirmasi. Bahasa default belum
  ditetapkan pada prompt lama; kode/test meneruskan pesan terbaru ke engine.
- Prompt dasar meminta jawaban langsung dan Bahasa Indonesia default dengan
  bahasa lain jika diminta eksplisit. Pengguna menguji ulang model asli lewat
  UI: pertanyaan bahasa dijawab dalam Bahasa Indonesia, dan pertanyaan nama
  dijawab dengan identitas Benzie. Manual kirim/jawab beberapa pesan: PASS.
- Ini dua contoh berhasil, bukan evaluasi kualitas menyeluruh. Bahasa Inggris,
  streaming/responsivitas/close desktop belum dikonfirmasi eksplisit.
- Perintah dan batas perilaku tercatat di docs/chat-ui.md. Langkah berikutnya
  setelah review/push: pembatalan responsif dan penyempurnaan lifecycle M3.

## Langkah M3.2 — cancel/lifecycle, sudah di-commit

- Tombol Batal aktif saat request berlangsung. Jawaban parsial dipertahankan,
  chunk terlambat diabaikan setelah pembatalan, dan transcript menampilkan
  [Dibatalkan]. Input kembali aktif setelah worker/cleanup selesai.
- ChatRequest per pesan memiliki flag dan lock sehingga cancel sebelum worker
  mulai tidak hilang. Engine tetap dibuat/dipakai/dibersihkan di worker.
- cancel engine hanya operasi thread-safe flag/sinyal kill pada child runtime
  sendiri. Koneksi HTTP terputus, lalu worker close/reap. Tidak membunuh thread
  Qt/Python, tidak menunggu proses dari UI, dan tidak memberi shell ke model.
- Close window saat request aktif meminta cancel, menunggu finished/cleanup
  secara asinkron, kemudian menutup. Request berikutnya memakai engine baru.
- **103 tests PASS**, build/diff check PASS. Tes mencakup cancel sebelum start,
  loading/generation/I/O, event terlambat, resend, close, serta kill/reap child
  nyata tanpa network. Test model/UI asli masih perlu terminal pengguna.
- Tidak ada dependency baru, perubahan model, konteks percakapan, atau history.
- Manual test: cancel saat loading, cancel saat jawaban panjang, kirim ulang,
  dan close window saat aktif. Perintah/checklist ada di docs/chat-ui.md.

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

Integrasi history ke UI/core, konteks multi-turn, model settings, launcher Applications,
memory, RAG, file search, tools, shell, voice, vision, avatar, fine-tuning.

Qwen3-0.6B hanya disetujui sebagai smoke test Milestone 2, bukan model utama.

## Gerbang review

Tidak commit/push sebelum pengguna review dan menyetujui.
Usulan pesan commit M4.1: `menambah penyimpanan riwayat percakapan lokal`.
Pengguna meminta perintah siap salin untuk commit/push dan menjalankan push
sendiri. Asisten belum menjalankan commit/push M4.1. Berhenti setelah langkah
kecil yang telah lolos tes; tunggu pengguna sebelum langkah berikutnya.
