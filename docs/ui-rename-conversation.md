# UI4 — ubah judul percakapan

2026-11-04. Tombol Ubah judul pada sidebar, atau F2, membuka dialog judul
percakapan aktif. Aksi tersedia setelah pesan pertama dikirim, termasuk ketika
model tidak dipilih. Dikunci saat generation, close pending, atau error storage.

## Perilaku dan penyimpanan

- Judul manual 1–60 karakter setelah whitespace dirapikan. Judul kosong atau
  terlalu panjang ditolak dengan pesan status; judul lama tetap ada.
- Membatalkan dialog tidak mengubah data. Judul/pesan/draf tidak ditulis ke log.
- HistoryService meneruskan rename ke ConversationStore. Store memvalidasi
  judul dan keberadaan pesan user, lalu memperbarui title/updated_at dalam
  transaksi. Tidak mengubah message content atau ID percakapan. SQLite tetap
  skema 2 tanpa dependency baru. Error SQL tidak menampilkan detail mentah.
- Percakapan tanpa pesan belum bisa diberi judul manual. Judul pertama tetap
  mengikuti alur otomatis UI2; setelah ada pesan, judul manual tidak ditimpa
  oleh pesan lanjutan. Pengaman ini juga berlaku pada layer penyimpanan.
- Sidebar/header diperbarui tanpa membuka ulang transcript atau menghapus draf.
  updated_at berubah sehingga percakapan dapat naik di daftar aktivitas.
- Judul ditampilkan literal, termasuk yang persis Percakapan baru; judul default
  dibedakan dengan ID pada baris tanggal. Tooltip menggunakan template Qt milik
  aplikasi dengan judul di-escape, agar teks markup tidak menjadi image/link.

## Verifikasi

219 tests PASS: persist/reopen, normalisasi, input invalid, pesan lanjutan,
percakapan kosong/tidak ditemukan, rollback SQL, dialog cancel, action shortcut,
header/sidebar, preservasi draf/pesan, serta judul HTML dan string default.
Tes lama streaming/cancel/storage tetap lulus. Preview offscreen 740x540 diperiksa
untuk penempatan tombol; ini bukan konfirmasi desktop native.

Manual: buka history berisi pesan, klik Ubah judul atau F2; simpan judul baru,
lanjut chat, tutup/buka ulang. Judul harus tetap. Coba Batal dan judul kosong;
pastikan draf dan pesan tidak hilang. Model tidak perlu dimuat untuk rename.

File utama: persistence/conversations.py, core/history.py, ui/main_window.py,
ui/theme.py, dan tes terkait. Tidak ada perubahan inference/model/sampling.
Manual Fedora masih menunggu pengguna; belum commit/push.
