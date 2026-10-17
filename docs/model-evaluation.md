# Evaluasi model — E1

2026-10-18. V0.1 sudah berfungsi offline; langkah ini mengukur kualitas sebelum
memilih model berikutnya. Tidak mengubah model desktop atau menambah memory/RAG.

## Alat dan baseline

Tutup Benzie dahulu agar port tersedia. Jalankan dari root repository:

```bash
.venv/bin/python scripts/evaluate_local_model.py --limit 3
```

Konfigurasi runtime/model dibaca dari profil default. Gunakan --settings untuk
profil khusus. Override model/runtime tanpa mengubah konfigurasi desktop:

```bash
.venv/bin/python scripts/evaluate_local_model.py \
  --binary .tools/llama.cpp-v0.6.0/build-cpu/bin/llama-server \
  --model /home/vendra/.local/share/benzie/models/Qwen3-0.6B-Q8_0.gguf
```

Tanpa --limit, semua 10 kasus dijalankan. --limit 3 adalah pemeriksaan awal
runner, bukan hasil suite lengkap. Bandingkan model hanya pada case ID/suite
hash dan pengaturan yang sama. Tidak ada downloader atau cloud judge.

File laporan `data/evaluation-<timestamp>.json` diabaikan Git dan tidak ditimpa.
Laporan sengaja berisi prompt/jawaban **sintetis evaluasi**, bukan log percakapan
pengguna. Script tidak membaca database/history pribadi. Ctrl+C menutup runtime
dan menyimpan progres dengan complete=false jika file laporan sudah dibuka.
Kegagalan kasus ditandai error, tidak diberi skor kualitas. Cleanup gagal dapat
menghentikan seluruh evaluasi supaya tidak menjalankan engine baru pada port sama.

Suite tetap: scripts/evaluation_cases.json. Rubrik/expected criteria tidak
dikirim ke model. History fixture sintetis sama pada setiap model, bukan respons
generation sebelumnya, agar tes koreksi/konteks dapat dibandingkan.

## Protokol dan interpretasi

- CPU empat thread, context 2048, max output 256, thinking off, temperature 0.
  Default sampling lain mengikuti binary yang hash-nya dicatat. Ini kondisi
  pembanding terkendali; bukan rekomendasi sampling optimal setiap model.
- Restart runtime tiap kasus, menyerupai lifecycle desktop. OS cache tidak
  dibersihkan. Load bukan klaim cold boot; hash file dibaca sebelum benchmark
  sehingga bisa menghangatkan page cache. TTFT dihitung setelah startup hingga
  teks pertama dan termasuk preflight template/tokenisasi/HTTP.
- Decode tok/s berasal dari runtime. RSS/HWM hanya child runtime, bukan total
  aplikasi/OS. System memory sebelum tes dicatat. Jangan membandingkan hasil
  saat laptop sibuk/thermal throttling dengan hasil saat idle tanpa catatan.
- Token count >=256 ditandai possibly_token_limited, bukan bukti pasti stop
  reason. Jawaban terpotong perlu diulang dengan budget terkontrol jika relevan.
- Hash model/binary/suite/system prompt membedakan artefak. Temperature 0 tidak
  menjamin identik lintas hardware/runtime. Lakukan tiga pengulangan untuk
  kandidat final; satu putaran hanya screening, bukan klaim stabilitas.

Penilaian manual per kasus: **0** salah/tidak memenuhi, **1** sebagian benar
atau instruksi terlewat, **2** benar dan mengikuti instruksi. Isi manual_score
dan tambahkan catatan pada salinan laporan lokal; null berarti belum dinilai.
Jangan mengubah prompt/system prompt di tengah perbandingan. Tinjau fakta,
bahasa alami, relevansi, serta klaim kemampuan; jangan hanya cocokkan keyword.
Sepuluh kasus ini regression screen Benzie, bukan benchmark kecerdasan umum.

## Kondisi hardware yang diperiksa

i5-13500H, 16 logical CPU, AVX2, RAM sekitar 16 GB, Intel Iris Xe terintegrasi,
ruang disk sekitar 310 GiB. Saat audit RAM tersedia sekitar 6,1 GiB dan swap
terpakai sekitar 4,1 GiB. Ini snapshot beban, bukan kapasitas model maksimum.
Tutup aplikasi berat sebelum membandingkan. CPU empat thread tetap baseline;
thread tuning/akselerasi GPU belum diubah. Estimasi 1,7B–4B quantized layak diuji
adalah hipotesis engineering, belum hasil RAM/latency model kandidat.

## Shortlist riset (bukan keputusan model utama)

1. **Qwen3-1.7B**, mulai GGUF Q4_K_M bila artefaknya tersedia/terverifikasi.
   Prioritas eksperimen berikutnya: langkah ukuran kecil dari smoke model.
   [Repository GGUF resmi Qwen](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF)
   tersedia. Revision, file, checksum, dan native load belum dipatok/diuji.
2. **Qwen3-4B-Instruct-2507**, target pembanding kualitas Q4_K_M. Model card
   resmi menyebut mode non-thinking saja; ini cocok dengan alur text chat.
   [Model card resmi](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507).
   GGUF publisher/revision/checksum belum dipilih, RAM/latency lokal belum diukur.
3. **Qwen3.5-2B**, kandidat generasi lebih baru. Card resmi mencatat arsitektur
   hybrid dan default non-thinking, serta penggunaan prototyping sesuai skala.
   [Model card resmi](https://huggingface.co/Qwen/Qwen3.5-2B). Hanya text path yang
   dipertimbangkan. Source llama.cpp terpasang mempunyai arsitektur qwen35,
   tetapi keberadaan enum bukan bukti GGUF tertentu kompatibel. Publisher/file/
   checksum dan uji native wajib diverifikasi sebelum dipakai.

Rekomendasi: ukur baseline 0.6B dulu, lalu 1.7B sebagai langkah unduhan berikutnya;
bandingkan 4B/2B setelah artefak diverifikasi. Semua shortlist masih satu keluarga
dan bukan pencarian ekosistem lengkap; pembanding keluarga lain bisa ditambah
setelah hasil awal. Benchmark penerbit tidak membuktikan Bahasa Indonesia atau
latency laptop ini. Tidak mengunduh apa pun pada E1.

178 tests PASS (runner diuji dengan fake engine); hasil model asli belum ada.
Tiga kasus native dicoba dari sesi asisten dan gagal sebelum generation;
diagnosis langsung menunjukkan socket lokal ditolak. Laporan kasus error bukan
baseline kualitas dan harus dipisahkan dari hasil pengguna yang benar-benar jalan.
Build/lockfile diperiksa terpisah. Jalankan baseline di terminal desktop;
sesi asisten sebelumnya terbatas untuk socket/native UI. Hasil nyata perlu
dibaca dan dinilai sebelum rekomendasi akhir model.

## Screening native pertama — 3/10 kasus

Pengguna menjalankan Qwen3-0.6B Q8_0 dan ketiga kasus generated tanpa error.
Laporan lokal: data/evaluation-20261017T173115809532Z.json (tetap ignored Git).
Review berdasarkan isi jawaban, bukan status runner:

- rag-definition-id: salah, mengartikan RAG sebagai Riset dan Algoritma serta
  menambahkan klaim panjang 12 karakter. Penilaian awal 0/2.
- correct-false-premise-id: membenarkan Research and Answering Generation dan
  tidak mengikuti satu kalimat. Penilaian awal 0/2.
- english-explanation: membedakan konsep secara parsial tetapi menyebut history
  temporary dan hanya satu kalimat, bukan dua. Penilaian awal 1/2.

Ini review asisten atas tiga kasus, belum suite lengkap atau evaluasi berulang.
Tidak menyimpulkan kualitas kandidat lain. Checkpoint runner dapat disimpan
meskipun model baseline gagal rubrik. Selanjutnya jalankan semua 10 kasus sebelum
membandingkan kandidat dengan suite dan pengaturan sama.
