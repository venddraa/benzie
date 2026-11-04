# UI1 — sunset Widgets

2026-11-04. Pengguna meminta perbaikan UI/UX dengan arah oren/sunset/kuning;
eksperimen sampling model ditunda. Fondasi Python/PySide6/core tidak diganti.

## Yang berubah

- Latar cream, sidebar peach, aksen oren matang dan kuning lembut. Tombol Kirim
  memakai oren lebih gelap agar teks putih lebih terbaca. Tema lokal tanpa
  font eksternal, aset unduhan, animasi, atau dependency baru.
- Sidebar daftar percakapan menggantikan dropdown. Pilihan aktif, nama yang
  sudah tersimpan, dan tanggal terlihat; judul default tetap nomor percakapan.
  Belum ada auto-title, rename/delete/search pada checkpoint ini.
- Header judul percakapan/model pilihan dan tombol Model lokal. Badge Lokal
  menjelaskan jenis runtime, bukan klaim model sedang dimuat. Status proses
  tetap di bawah. Error konfigurasi terlihat ketika ada.
- Area chat memisahkan label Anda/Benzie dengan warna dan jarak. QTextEdit
  hanya merender format label milik aplikasi; semua isi pengguna/model/status
  masuk melalui QTextCursor.insertText. HTML/URL/image dari pesan tidak dieksekusi,
  diload, atau menjadi link interaktif. Markdown tetap teks literal.
- Composer multiline: Enter mengirim, Shift+Enter baris baru; Tab berpindah
  fokus. Batal terlihat selama request aktif. Model/new/open dikunci saat
  generation seperti sebelumnya. Saat membaca pesan lama, chunk baru tidak
  menarik scroll ke bawah; bila di bawah, stream tetap diikuti.
- Empty state memberi petunjuk memilih model atau memulai chat. Status awal
  memakai bahasa pengguna, tidak menampilkan versi skema SQLite.

Ukuran awal 1080x740, minimum 740x540, sidebar dapat diubah lebarnya dengan
splitter. Masih light theme tunggal; preferensi tema belum disimpan. Dialog
model mengikuti warna window dan tombol Simpan/Batal berbahasa Indonesia.

## Verifikasi

196 tests PASS: tes lama history/model/cancel/error/close tetap lulus. Tambahan
keyboard Enter/Shift+Enter, preservasi input multiline di database, literal
HTML, navigasi sidebar, empty state, dan scroll selama streaming.
Preview Qt offscreen dengan data sintetis diperiksa pada ukuran 1080x740 dan
740x540, keadaan chat dan kosong. Preview bukan hasil generation native atau
konfirmasi Wayland desktop. Tidak membaca history pribadi untuk screenshot.

Manual pengguna: tutup window lama, buka Benzie lagi lewat Applications atau
`.venv/bin/benzie`. Cek tampilan normal/kecil, pilih percakapan, buat baru,
Shift+Enter lalu Enter, streaming/Batal, model dialog, dan history setelah
restart. Launcher yang sudah terpasang tidak perlu dipasang ulang karena
entry point/checkout sama. Tidak mengubah model atau konfigurasinya.

File utama: ui/main_window.py (layout), ui/chat_widgets.py (composer/transcript),
ui/theme.py (stylesheet kecil), ui/model_dialog.py (label tombol).
Preview development berada di /tmp, tidak masuk Git. README tetap benzie.
