# Uji UI chat — M3.1/M3.2

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
3. Klik Batal saat loading atau jawaban panjang sedang muncul. Tunggu status
   Siap/input aktif kembali; teks parsial tetap terlihat dengan [Dibatalkan].
4. Kirim pesan lagi setelah cancel; jawaban baru harus berjalan normal.
5. Tutup window saat request aktif. Window meminta cancel dan menutup setelah
   worker/cleanup selesai; tidak menunggu seluruh jawaban. Jangan matikan proses
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

M3.2 menambahkan tombol Batal dan close yang meminta cancellation. Flag cancel
dimiliki per request dan tidak dihapus saat worker baru mulai. Pembatalan
menghentikan child llama-server milik request; worker menutup koneksi dan reap.
Operasi kill tidak menunggu proses dari UI atau menghentikan QThread. Engine
yang telah dibatalkan tidak dipakai ulang; pesan berikutnya memakai engine baru.
Error cleanup tetap ditampilkan, bukan dianggap pembatalan sukses.

103 tests PASS dan build/diff check PASS. Tes OS child nyata tanpa socket
membuktikan kill/reap; fake engine/UI membuktikan cancel/loading/generation,
resend, dan close aktif. Manual model asli menunggu terminal pengguna.
Core membatasi deadline load 30 detik dan timeout I/O generation 30 detik;
timeout I/O bukan deadline keseluruhan jika server terus mengirim chunk.

## Manual test M4.2

Gunakan data-dir yang sama saat restart. Kirim pesan, buat percakapan baru,
kirim pesan berbeda, lalu pindah kembali lewat pilihan percakapan. Tutup dan
buka ulang aplikasi: kedua history harus tersedia. Lanjutkan percakapan lama:
pesan baru harus tersimpan di percakapan tersebut. Model masih menerima hanya
pesan terbaru, belum konteks history. Coba Batal dan tutup saat generation;
hasil parsial/status harus tersedia setelah restart. Jalankan tanpa --runtime
dan --model untuk membaca history tanpa memuat model. Jangan gunakan /tmp
untuk history penting karena bisa dibersihkan sistem.

## Manual test M4.3 (menggantikan batasan konteks M4.2)

1. Buat percakapan baru. Kirim: "Kode uji saya nila-47. Jawab singkat."
2. Kirim: "Apa kode uji yang saya sebut tadi?" Periksa nila-47.
3. Tutup/buka aplikasi dengan data-dir sama, buka history itu, tanyakan lagi.
4. Buat percakapan lain dan tanyakan kode: konteks percakapan pertama tidak
   dikirim (jawaban model bisa mengarang, jadi ini bukan bukti isolasi sendiri;
   isolasi payload juga diuji otomatis).
5. Kirim teks sintetis panjang yang melampaui context 2048 token: error konteks
   penuh harus tampil dan UI tetap bisa membuat percakapan baru. Jangan memakai
   data pribadi untuk smoke test. Coba Batal/kirim ulang seperti sebelumnya.

142 tests PASS; validasi model asli masih melalui terminal pengguna karena
socket sesi asisten ditolak. Kualitas Qwen3-0.6B belum menjadi acceptance model.

## Manual test M5.1

Jalankan `.venv/bin/benzie --data-dir /tmp/benzie-model-smoke` tanpa argumen model.
Klik Model lokal, pilih binary llama-server hasil setup dan GGUF lokal, lalu
Simpan. Kirim pesan untuk menguji pemuatan model. Tutup, jalankan perintah yang
sama: model harus sudah dipilih dan history bisa dilanjutkan. Coba Cancel pada
dialog: pilihan lama tetap. Coba file non-GGUF: error muncul tanpa mengubah
pilihan yang tersimpan. Selama generation, tombol Model lokal nonaktif.
Launcher belum dipasang. /tmp hanya untuk smoke; data utama mengikuti XDG.
