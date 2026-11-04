# UI3 — draf selama sesi

2026-11-04. Memperbaiki hilangnya input ketika pengguna berpindah history atau
membuat percakapan baru. Draf tersimpan dalam dictionary milik window selama
aplikasi terbuka, bukan sebagai pesan di SQLite atau konteks model.

## Perilaku

- Setiap percakapan punya draf sendiri, termasuk newline dan whitespace asli.
  Navigasi sidebar memulihkan draf target dan mempertahankan draf sebelumnya.
- Baris tanggal/sidebar menampilkan Draf serta tooltip saat ada input belum
  dikirim. Header judul tidak diberi marker. Update penanda tidak membaca atau
  menulis database per ketikan.
- Percakapan baru dari percakapan aktif menyimpan draf lama dan membuka input
  kosong. Jika belum ada percakapan aktif sama sekali, tombol itu mengikat
  input awal ke percakapan baru tanpa menghapusnya.
- Mengirim pesan membersihkan draf percakapan itu; draf percakapan lain tetap.
  Mengosongkan input juga menghapus draf/penandanya. Whitespace-only tidak
  dianggap draf dan tombol Kirim tetap tidak aktif.
- Draf tidak dikirim ke model sebelum Kirim, tidak ditulis ke database/log,
  dan tidak dipulihkan setelah aplikasi ditutup. Batas sesi ini terlihat pada
  footer sidebar dan tooltip; tidak ada klaim autosave permanen.

SQLite/core/inference/model settings tidak berubah. Record percakapan kosong
yang dibuat lewat tombol baru tetap mengikuti perilaku sebelumnya; checkpoint
ini tidak menambah pembersihan otomatis atau penyimpanan draft permanen.

## Verifikasi

206 tests PASS: draf multiline pada composer awal, navigasi/new, isolasi draf,
kirim dan penghapusan marker, mengosongkan input, serta restart tanpa menulis
isi draf ke history. Tes lama title, literal text, streaming, cancel, storage
error, dan close tetap lulus. Tidak ada dependency atau migrasi baru.

Manual desktop: buat percakapan, ketik dua baris tanpa Kirim; buat percakapan
lain dan ketik draf berbeda; pindah kembali dan periksa input/marker. Kirim
salah satu, lalu pastikan draf lainnya tetap. Periksa teks footer mengenai
batas sesi. Tutup/buka ulang: pesan terkirim tetap, draf memang tidak dipulihkan.

File utama: ui/main_window.py dan tests/test_ui_smoke.py. Manual Fedora masih
menunggu pengguna; hasil otomatis offscreen tidak dianggap verifikasi desktop.
