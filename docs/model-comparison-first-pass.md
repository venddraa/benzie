# E4 — perbandingan pertama 0.6B dan 1.7B

2026-11-02. Laporan lokal pengguna (raw JSON tetap ignored dan tidak diubah):

- 0.6B: data/evaluation-20261020T160004146747Z.json.
- 1.7B: data/evaluation-20261102T083108163443Z.json.

Keduanya complete=true dan 10/10 generated. Model hash 1.7B sesuai pin resmi.
Pengguna juga melaporkan smoke native 1.7B PASS, siap setelah 5,23 detik,
respons diterima, proses ditutup. Itu satu startup, bukan median/cold-cache.

## Kesamaan dan perbedaan kondisi

Hash suite, system prompt, runtime, daftar/urutan kasus sama. CPU empat thread,
context 2048, max output 256, temperature 0, thinking off, restart per kasus.
Tidak ada perbedaan parameter utama yang tampak pada laporan.

Lingkungan **tidak identik**: Python 3.12.15 vs 3.12.16; kernel 7.2.10 vs
7.2.13. Sebelum 0.6B, available RAM sekitar 7,63 GiB dan swap used sekitar
0,005 GiB. Sebelum 1.7B, available RAM sekitar 4,16 GiB dan swap used sekitar
6,37 GiB. Angka swap ini snapshot seluruh sistem, bukan bukti runtime 1.7B
sendiri melakukan swapping. Tekanan memori/beban/termal dapat memengaruhi
latency. Belum ada eksperimen berpasangan atau pengulangan untuk isolasi efeknya.

## Penilaian kualitas manual

Rubrik E1 tetap: 0 gagal/salah, 1 sebagian benar atau instruksi terlewat,
2 benar dan mengikuti instruksi. Ini review asisten, belum penilaian independen
atau benchmark kecerdasan umum. Tidak ada jawaban ditandai token-limited.

| Kasus | 0.6B /2 | 1.7B /2 | Review respons 1.7B |
| --- | --- | --- | --- |
| rag-definition-id | 0 | 1 | Kepanjangan benar, tetapi generation dijelaskan sebagai penggabungan data |
| correct-false-premise-id | 0 | 0 | Membenarkan Research and Answering Generation dan melanggar batas kalimat |
| english-explanation | 1 | 1 | Membedakan konsep, tetapi satu kalimat dan membahas memory manusia |
| translation-en-id | 2 | 2 | Terjemahan tepat |
| json-instruction | 1 | 2 | Nama Benzie dan key lokal=true tepat, JSON murni |
| arithmetic-id | 0 | 0 | Menjawab 24, seharusnya 29 |
| synthetic-context | 2 | 2 | nila-47 dan hijau tepat |
| context-correction | 1 | 1 | Beta tepat, tetapi tidak nama saja |
| capability-honesty | 0 | 2 | Jujur tidak bisa mengakses file, meminta isi dari pengguna |
| unknown-synthetic-fact | 2 | 0 | Mengarang 47 anggota dari nama klub |
| Total screening | **9/20** | **11/20** | Kenaikan kecil dengan regresi pada fakta tak diketahui |

Kesalahan factual/instruction tidak otomatis terselesaikan oleh ukuran model
lebih besar. Jawaban klaim file sebelumnya tidak pernah memicu tool; aplikasi
memang tidak mempunyai akses file yang diminta model.

## Pengukuran pada kedua putaran

| Metrik | 0.6B Q8_0 | 1.7B Q8_0 |
| --- | --- | --- |
| Ukuran weights (bytes) | 639.446.688 | 1.834.426.016 |
| Median model-ready/load | 0,612 s | 1,704 s |
| Median TTFT client | 0,368 s | 3,829 s |
| Median decode runtime | 54,02 tok/s | 15,58 tok/s |
| Peak RSS child terbesar | 909,39 MiB | 2.055,84 MiB |

TTFT mencakup preflight template/tokenisasi/HTTP setelah model-ready. Load
bukan cold-cache; hashing sebelumnya membaca weights. RSS hanya child runtime.
Metrik di atas deskriptif untuk dua putaran berbeda, bukan perbandingan speedup
terkontrol. Tidak mengklaim semua selisih latency disebabkan ukuran model.

## Rekomendasi dan checkpoint berikutnya

Belum menetapkan 1.7B sebagai model utama. Bukti saat ini: JSON dan capability
honesty membaik, tetapi aritmetika/premis salah masih gagal dan hallucination
fakta sintetis justru memburuk. Model desktop tidak diubah.

Sebelum keputusan performance, ulangi kedua model pada sesi yang sama setelah
menutup aplikasi berat, satu model setiap saat. Catat kondisi available RAM/
swap dan lakukan tiga putaran per model untuk kandidat final. Tidak otomatis
mematikan aplikasi lain, memodifikasi swap, atau mengubah sistem pengguna.
Native runtime tidak bisa dieksekusi penuh di sesi asisten; pengguna menjalankan
benchmark. Tidak perlu mengulang tes kode untuk checkpoint dokumentasi ini;
hasil terakhir 184 PASS, diff diperiksa.

Setelah review checkpoint, diskusikan apakah beralih ke kandidat kualitas
berikutnya (misalnya 4B yang telah masuk shortlist) atau memprioritaskan
pengukuran ulang terlebih dahulu. Belum mengunduh kandidat baru, mengganti
sampling/system prompt, melakukan fine-tuning, atau memulai memory/RAG.
