# Benchmark awal — M2.4

Tujuan: mengukur pipeline lokal pada satu model smoke test, bukan memilih model
utama atau mengevaluasi kualitas percakapan. Model/path dapat diganti melalui
argumen tanpa mengubah core. Tidak ada dependency Python baru.

## Menjalankan

Setelah setup runtime dan smoke test berhasil, dari root proyek:

```bash
.venv/bin/python scripts/benchmark_local_inference.py
```

Default: tiga pengulangan; setiap pengulangan membuat proses baru, context
2.048, empat thread CPU, maksimal 128 token output, temperature 0,7. Prompt
sintetis Bahasa Indonesia tetap (walking-benefits-id-v1), thinking dimatikan.
Tidak ada data pribadi yang dimasukkan atau respons yang disimpan ke laporan.

Untuk perbandingan thread kelak, gunakan --threads 8/12 pada eksekusi terpisah.
--model, --binary, --runs (1–10), --port, dan --output juga tersedia. Jangan
menjalankan benchmark bersamaan atau pada port yang dipakai aplikasi lain.
Biarkan kondisi daya dan aplikasi latar konsisten; catat perubahan kondisi.

Laporan JSON hanya metrik/configuration/hardware, tersimpan di data/ yang
diabaikan Git. File default memiliki timestamp, dan output yang sudah ada tidak
ditimpa. Laporan benchmark tidak dikirim ke internet.

## Definisi metrik

- Model bytes: ukuran file, terpisah dari penggunaan RAM proses.
- Load seconds: sejak start proses sampai health/model terautentikasi siap;
  termasuk warmup runtime dan overhead pemeriksaan HTTP.
- TTFT: dari mulai iterasi request sampai potongan teks non-kosong pertama
  diterima. Ini latensi teks pertama yang dialami client; event role atau usage
  kosong tidak dihitung. Satu potongan streaming belum tentu satu token.
- Decode tokens/sec: predicted_per_second dari statistik runtime. Jumlah token
  berasal dari usage.completion_tokens, tidak dihitung dari jumlah chunk.
- Generation seconds: durasi client dari request sampai SSE DONE.
- RSS dan peak RSS: VmRSS/VmHWM proses llama-server dari /proc. Peak mencakup
  masa hidup proses termasuk load/generation dan halaman model yang resident;
  bukan RAM total sistem, memori Python, atau penggunaan memori unik/PSS.
- CPU seconds: user+system runtime dari /proc. average_cpu_percent dihitung
  terhadap wall time load+generation yang diamati. 100% berarti satu core,
  sehingga proses multi-thread dapat melampaui 100%.
- RAM tersedia dan swap sebelum tiap run dicatat untuk konteks resource.

Semua hasil tiap run disimpan; summary memakai median load/TTFT/decode serta
peak RSS terbesar. OS page cache tidak dibersihkan. Run pertama tidak otomatis
merupakan cold start. Tidak ada klaim benchmark internet atau kualitas model.

## Streaming dan cleanup

Adapter menambah generate_stream, dengan event teks/usage/timing. Parser SSE
mendukung komentar, CRLF, data multi-baris, batas respons, dan DONE. Stream
terputus, JSON invalid, atau error/timeout I/O menghentikan runtime. Pemanggil
yang berhenti dini wajib close iterator; benchmark memakai contextlib.closing.
Respons sukses dapat diikuti request berikutnya. Semua operasi tetap berurutan
dari satu pemanggil; belum ada UI worker. Ctrl+C benchmark melakukan cleanup.

Kontrak timing mengacu pada [dokumentasi llama-server v0.6.0](https://github.com/ggml-org/llama.cpp/blob/v0.6.0/tools/server/README.md),
dan usage streaming diperiksa terhadap server-task.cpp versi lokal terpatok.

## Status verifikasi

80 automated tests PASS, build/syntax/diff check PASS. Pengukuran server dari
sesi asisten terhambat izin socket; pengguna berhasil menjalankan benchmark
di terminal desktop. JSON lokal diperiksa: tiga run sukses, 128 token setiap
run, dan summary sesuai perhitungan ulang.

## Hasil pipeline, 2026-10-12

Qwen3-0.6B Q8_0, llama.cpp 0.6.0 (d812350), i5-13500H, CPU empat thread,
context 2.048. Tidak membersihkan OS cache.

| Run | Load (s) | TTFT (s) | Decode (tok/s) | Peak RSS (MiB) |
| --- | --- | --- | --- | --- |
| 1 | 1,0201 | 0,6970 | 43,2883 | 904,9 |
| 2 | 1,0355 | 0,4954 | 42,7854 | 904,9 |
| 3 | 1,0399 | 0,4769 | 43,1655 | 904,9 |

Median load **1,0355 s**, TTFT **0,4954 s**, decode **43,1655 tok/s**.
Peak RSS terbesar **948.899.840 bytes / 904,94 MiB**. CPU rata-rata tiap run
291,78–297,79% selama load+generation, kira-kira tiga core; seluruh laptop
mempunyai 16 logical CPU. MemAvailable sebelum run sekitar 5,28 GiB.

Laporan lokal: data/benchmark-20261012T061828308289Z.json, tidak masuk Git.
Tidak menyimpan prompt/jawaban. Tiga sampel membuktikan baseline pipeline
ini, belum menguji sesi panjang, context besar, baterai/thermal berkelanjutan,
offline acceptance desktop V0.1, atau kualitas percakapan. Belum cukup untuk
memilih model utama atau jumlah thread optimal. Thread lain/model lain perlu
benchmark terpisah bila nanti dipilih untuk evaluasi.

## Baseline native

Baseline native yang benar-benar dijalankan asisten pada 2026-10-12:

```bash
.tools/llama.cpp-v0.6.0/build-cpu/bin/llama-bench --model /home/vendra/.local/share/benzie/models/Qwen3-0.6B-Q8_0.gguf --offline -p 128 -n 128 -r 3 -t 4 -ngl 0 -dev none -o json
```

llama.cpp d812350, Qwen3 0.6B Q8_0, i5-13500H, CPU empat thread, warmup default:

- Prompt processing pp128: **197,94 ± 19,36 token/detik**, tiga sampel.
- Generation tg128: **47,31 ± 0,65 token/detik**, tiga sampel.

Ini rata-rata/stddev microbenchmark native dengan token sintetis dan tanpa HTTP,
berbeda dari median benchmark pipeline. tg128 memakai kedalaman prompt nol;
tidak menggantikan pengukuran dengan chat template/prompt nyata. TTFT, load time,
dan RSS pipeline belum diukur pada baseline native ini. Ukuran file GGUF yang
diverifikasi sebelumnya adalah 639.446.688 bytes.
