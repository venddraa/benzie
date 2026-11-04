# UI2 — judul percakapan dari pesan pertama

2026-11-04. Perapian UX setelah tema sunset: history percakapan baru lebih mudah
dikenali melalui judul pendek dari pesan pengguna pertama.

## Perilaku

- Core mengambil baris pertama yang tidak kosong, merapikan spasi/tab, lalu
  membatasi judul maksimal 60 karakter dengan elipsis jika perlu. Pesan asli
  tetap utuh, termasuk newline dan whitespace internal. Tidak memakai LLM.
- Store mengganti judul default hanya ketika menyimpan pesan user pertama.
  Title, updated_at, dan insert pesan berada dalam transaksi yang sama.
  Jika insert gagal, judul/aktivitas juga rollback. SQLite tetap skema 2.
- Pesan lanjutan tidak mengganti judul. Judul nondefault dipertahankan, demikian
  pula history lama yang sudah memiliki pesan meski judulnya masih default.
  Tidak ada backfill otomatis atau perubahan database pribadi dari sesi asisten.
- Judul dipakai pada sidebar/header setelah worker selesai dan saat membuka
  history kembali. Selama generation, sidebar masih dikunci dan refresh judul
  menunggu cleanup selesai. Teks tetap literal, termasuk tanda HTML/kutip.
- Cancel/error model tidak menghilangkan judul jika pesan user sudah disimpan.
  Ini label history lokal, bukan personal memory atau ekstraksi informasi.

## Verifikasi

203 tests PASS: normalisasi/panjang/Unicode, reopen, pesan kedua, judul khusus,
history lama, judul persis sama dengan string default, rollback insert, cancel,
dan sidebar/header setelah streaming. Tidak ada dependency, migration, atau
perubahan model/runtime. File utama: core/history.py, persistence/conversations.py,
ui/main_window.py beserta tes.

Manual: tutup window lama, buka Benzie, buat percakapan baru lalu kirim pesan
multiline. Sidebar/header harus memakai baris pertama, bukan detail baris kedua.
Kirim pesan lain lalu restart: judul awal tetap. History lama bisa tetap bernomor
karena tidak diubah otomatis. Manual desktop checkpoint ini masih pending.

Pembaruan UI4: history yang sudah memiliki pesan dapat diubah judulnya secara
manual melalui sidebar/F2, tanpa ditimpa pesan berikutnya.
[Perilaku dan validasi](ui-rename-conversation.md).
