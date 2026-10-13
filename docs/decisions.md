# Keputusan teknis

Tanggal: 2026-10-11. Keputusan fondasi disetujui pengguna setelah Milestone 0.

## 001 — Python 3.12, PySide6 Widgets, SQLite

Python menjadi core/orchestration; PySide6 hanya presentation; SQLite penyimpanan
lokal. Python 3.12 sudah tersedia di Fedora pengguna. Python sistem 3.14 tidak
diubah. Baseline package dibatasi ke Python 3.12 sampai versi lain diuji.
Evaluasi upgrade sebelum dukungan Python 3.12 berakhir pada Oktober 2028.

Alternatif: Python 3.14 tersedia, tetapi tidak diperlukan untuk milestone ini.
UI web dan ORM tidak menjawab kebutuhan awal yang lebih baik dari stack pilihan.

## 002 — uv, pyproject.toml, Hatchling

uv mengelola environment dan lockfile; Hatchling membangun package standar.
PySide6 runtime, pytest development, tanpa dependency tambahan untuk fitur masa
depan. uv tidak boleh mengunduh Python otomatis. Aplikasi berjalan langsung dari
entry point environment, tanpa uv sync saat startup.

Alternatif: venv + pip valid, tetapi penguncian dependency memerlukan pengaturan
tambahan. Binary desktop bundling ditunda; belum perlu Flatpak/RPM/PyInstaller.

## 003 — Pemisahan UI/core dan SQLite sederhana

Core hanya memakai Python standard library. UI menerima hasil startup tanpa
SQL. Gunakan sqlite3, transaksi, dan user_version; tanpa ORM atau framework
migrasi. Skema 1 hanya fondasi versi, bukan history percakapan.

## 004 — Runtime dan model, khusus Milestone 2

Disetujui: llama-server lokal sebagai child process terkelola melalui
127.0.0.1, baseline CPU, GGUF lokal, tanpa cloud API. Binding Python dan CLI
dipertimbangkan; server dipilih untuk pemisahan kegagalan native dan streaming.
Versi runtime akan dipatok setelah validasi, bukan mengikuti master otomatis.

Qwen3-0.6B Q8_0 hanya smoke-test model untuk membuktikan pipeline. Bukan model
utama/identitas Benzie. Setelah pipeline stabil, bandingkan kualitas, RAM,
latency, Bahasa Indonesia/Inggris, instruksi, context, dan stabilitas beberapa
kandidat. Belum ada model yang diunduh pada Milestone 1.

## 005 — Lokasi lokal dan konfigurasi bertahap

Data mengikuti XDG; default database di ~/.local/share/benzie/benzie.sqlite3.
Model kelak di ~/.local/share/benzie/models. Config JSON kelak di
~/.config/benzie/config.json bila ada pengaturan yang perlu disimpan.
Pada Milestone 1 cukup resolusi XDG dan --data-dir; tidak membuat settings UI
atau parameter model yang belum digunakan.

## 006 — Workflow review

Setiap milestone/perubahan bermakna yang lolos test disiapkan sebagai commit
kecil. Pesan Bahasa Indonesia sederhana. Commit dan push hanya setelah review
dan persetujuan pengguna; tidak force push atau mengubah history tanpa izin.
Push dijalankan pengguna sendiri; asisten menyediakan perintah siap salin.
Repository yang diberikan pengguna: https://github.com/venddraa/benzie.git.
README cukup berisi `benzie`; panduan development tetap berada di docs/.
Satu milestone belum boleh disebut selesai jika manual smoke test wajib belum
berhasil. Kendala dependency/display harus dilaporkan, bukan dianggap PASS.

Pembaruan 2026-10-12: pengguna meminta checkpoint lebih kecil agar pekerjaan
tidak menumpuk. M2 dikerjakan per langkah yang diuji dan dapat di-commit/push
terpisah. Lifecycle subprocess memakai standard library; HTTP client baru
ditambahkan saat implementasi request inference membutuhkannya.

Pembaruan M2.3: baseline HTTP sinkron memakai http.client standard library untuk
satu request teks. HTTPX yang sebelumnya diusulkan belum diperlukan; evaluasi
ulang saat streaming/UI. API key sementara membedakan server milik engine dari
proses lain pada port sama. UI belum berubah.

M3.1, 2026-10-13: setelah transcript pengguna menunjukkan sapaan Inggris
berulang, system prompt dasar diperjelas agar menjawab permintaan langsung dan
menggunakan Bahasa Indonesia secara default; permintaan bahasa lain tetap
diikuti. Ini instruksi dasar, bukan personality kompleks. Setelah perubahan,
pengguna mengonfirmasi dua respons terkait bahasa dan nama melalui transcript
UI. Evaluasi kualitas menyeluruh belum dilakukan; Qwen3-0.6B tetap smoke test.
