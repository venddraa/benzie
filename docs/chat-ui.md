# Uji UI chat — M3.1

Jalankan dari root proyek pada desktop Fedora:

```bash
.venv/bin/benzie --data-dir /tmp/benzie-chat-smoke \
  --runtime .tools/llama.cpp-v0.6.0/build-cpu/bin/llama-server \
  --model /home/vendra/.local/share/benzie/models/Qwen3-0.6B-Q8_0.gguf
```

1. Ketik pesan sintetis seperti `Halo. Jawab dalam Bahasa Indonesia.` lalu Kirim
   atau Enter. Window harus tetap responsif saat status Memuat model/Menyusun
   jawaban; jawaban muncul bertahap.
2. Kirim pesan kedua setelah selesai. Input tersedia kembali dan runtime baru
   memproses pesan tersebut. Setiap pesan saat ini dijawab terpisah.
3. Tutup window setelah selesai. Bila ditutup saat masih bekerja, window
   menunggu worker dan cleanup selesai sebelum menutup; jangan matikan proses
   dari terminal untuk uji penutupan normal.

Tidak ada history DB/context pesan sebelumnya pada langkah ini. Transcript
hanya tampilan sementara dan hilang setelah window ditutup. Runtime dimuat
lalu ditutup per pesan agar lifecycle awal sederhana; overhead load sekitar
satu detik menurut benchmark model smoke test, bukan angka jaminan UI.
Model tetap smoke test dan bukan identitas permanen Benzie.

--runtime dan --model harus diberikan bersama; --port dapat diganti jika port
8081 dipakai. Tanpa argumen model/runtime, window tetap terbuka dengan input
dinonaktifkan. Pemilihan model grafis/config permanen menyusul.
Tidak ada install/download saat menjalankan aplikasi.

Untuk uji error tanpa mengubah artefak, buka aplikasi dengan --model menunjuk
path yang tidak ada dan kirim pesan. Error harus muncul sebagai teks; input
tersedia kembali. Kegagalan unexpected tidak mencatat traceback/pesan pribadi.

## Verifikasi saat ini

89 tests PASS, build package dan diff check PASS. Core diuji tanpa Qt. Fake
service pada test offscreen memverifikasi streaming literal (tidak merender
HTML), input/error, pengiriman ulang, dan close ketika worker sedang berjalan.
ChatWorker hanya jembatan QThread/signal; ChatService mengelola engine di core,
dan factory engine dipanggil di worker. Widget tidak memanggil runtime/SQL.

Pengguna mengirim transcript UI+model asli: beberapa pesan mendapat jawaban,
tetapi respons berulang berupa sapaan Inggris dan tidak menjawab permintaan
bahasa. Jalur kirim/jawab terbukti; streaming/responsivitas/close pada desktop
belum dikonfirmasi. Kode/test memperlihatkan pesan terbaru diteruskan ke engine;
belum ada inspeksi payload pada server asli, sehingga penyebab kualitas belum
dipastikan. Tidak ada konteks pesan sebelumnya pada M3.1.

System prompt dasar diperjelas: jawab permintaan secara langsung, default Bahasa
Indonesia, dan ikuti bahasa yang diminta eksplisit. Pengguna menguji ulang:
pertanyaan bahasa dijawab dalam Bahasa Indonesia dan pertanyaan nama dijawab
dengan identitas Benzie. Manual kirim/jawab beberapa pesan: PASS. Ini dua contoh
berhasil, bukan benchmark kualitas menyeluruh. Permintaan bahasa Inggris,
streaming/responsivitas/close desktop belum dikonfirmasi eksplisit; review manual
masih dapat mengikuti checklist di atas sebelum push.

Belum ada tombol cancel; close tidak membatalkan
generation langsung. Pembatalan responsif menjadi langkah kecil berikutnya.
Core membatasi deadline load 30 detik dan timeout I/O generation 30 detik;
timeout I/O bukan deadline keseluruhan jika server terus mengirim chunk.
