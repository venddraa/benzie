# E5 — pengukuran ulang berpasangan

2026-11-02. Perbandingan pertama 0.6B/1.7B memakai kondisi RAM/swap dan
kernel/Python berbeda. Runner ini mendekatkan kondisi kedua model dengan
menjalankannya berurutan pada sesi sama. Bukan kontrol termal/OS otomatis.

## Memulai satu pasangan

Tutup Benzie dan aplikasi berat, gunakan mode daya/charger yang sama sepanjang
tes, lalu dari root repository:

```bash
.venv/bin/python scripts/evaluate_model_pair.py
```

Default: 0.6B Q8_0 kemudian 1.7B Q8_0, masing-masing 10 kasus. Model dimuat
ulang per kasus seperti benchmark sebelumnya. Tidak berjalan bersamaan. File
weights yang sudah lokal digunakan; tidak ada download atau perubahan pilihan
model desktop. Tidak mematikan aplikasi atau mengubah swap atas nama pengguna.

Simpan output lokasi `data/paired-<timestamp>/summary.json` dan berikan kepada
asisten untuk review. Data berisi respons sintetis, metrik, RAM/swap sebelum
setiap run, hash artefak, dan kondisi pembanding. Semua tetap ignored Git.

Satu pasangan adalah pemeriksaan awal runner, belum estimasi stabilitas.
Jika hasil awal valid dan dipilih untuk pengukuran berulang:

```bash
.venv/bin/python scripts/evaluate_model_pair.py --pairs 3
```

Urutan A/B lalu B/A lalu A/B mengurangi ketergantungan pada satu urutan,
tetapi tiga pasangan belum counterbalancing sempurna. Ini enam run suite,
total 60 generation. Waktu bergantung kondisi laptop; jangan menjalankan
benchmark lain secara bersamaan. --limit 1–10 tersedia untuk debugging, tetapi
hasil subset jangan dicampur dengan full suite.

## Validasi dan batas

Runner memakai evaluator E1 yang sama, dengan parameter tetap. Berhenti jika
run gagal/terinterupsi, kasus tidak lengkap, atau hash suite/system prompt/
runtime/parameter/Python/platform berubah. Hash masing-masing model harus
tetap antar-pasangan. Output eksperimen dibuat di direktori baru dan tidak
menimpa direktori lama. Run individual tetap tersedia saat eksperimen terhenti;
summary.complete=false bukan perbandingan yang lulus.

Ringkasan menyimpan median per run dan peak RSS runtime, bukan total RAM
aplikasi. Memory sebelum run adalah snapshot, bukan sampling tekanan memori
sepanjang generation. Catatan swap terpakai sistem tidak membuktikan model
melakukan paging. Tidak membersihkan OS cache atau melakukan warmup tambahan.
Proses hashing pada evaluator dapat menghangatkan page cache.

Quality tetap dinilai manual dari jawaban, terpisah dari generated/complete.
Runner tidak memilih pemenang dan tidak mengubah prompt/sampling. Jika kondisi
available RAM/swap atau termal tetap berbeda, laporkan sebagai keterbatasan;
jangan menganggap urutan berpasangan otomatis menghasilkan perbandingan adil.

192 tests PASS; unit test menggunakan evaluator fake untuk urutan, penghentian,
kelengkapan, kontrol, dan preservasi output. Uji model native berpasangan masih
menunggu terminal pengguna karena socket sesi asisten ditolak pada percobaan
sebelumnya. Belum ada angka latency/RAM baru yang diklaim.
