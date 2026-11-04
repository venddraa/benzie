# E6 — review pasangan native pertama

2026-11-04. Direktori laporan pengguna:
data/paired-20261104T150250609690Z. summary.complete=true, exit_code=0.
Kedua model menghasilkan 10/10 kasus tanpa error. Ringkasan dan metrik
dihitung ulang dari file individual; kontrol/hash cocok.

## Kondisi sesi

Urutan A=0.6B kemudian B=1.7B. Hash runtime, suite, system prompt dan parameter
sama. Python 3.12.16 dan kernel 7.2.13 sama pada kedua run. Context 2048,
threads 4, output max 256, temperature 0, thinking off.

| Snapshot sebelum run | 0.6B | 1.7B |
| --- | --- | --- |
| Available RAM | 9,53 GiB | 9,70 GiB |
| Swap sistem terpakai | 0 GiB | 0 GiB |

Kondisi lebih sebanding daripada E4, tetapi snapshot bukan pencatatan paging/
termal selama generation. Tidak ada counterbalancing atau tiga pengulangan;
satu pasangan belum membuktikan stabilitas statistik atau isolasi semua beban.

## Hasil pengukuran

| Metrik | 0.6B Q8_0 | 1.7B Q8_0 |
| --- | --- | --- |
| Median model-ready/load | 0,610 s | 0,714 s |
| Median TTFT client | 0,346 s | 1,071 s |
| Median decode runtime | 59,39 tok/s | 24,31 tok/s |
| Peak RSS child | 909,37 MiB | 2.055,78 MiB |
| Review manual kualitas | 9/20 | 11/20 |

Untuk 1.7B, E4 mencatat TTFT 3,829 s dan decode 15,58 tok/s; pada pasangan ini
TTFT lebih rendah dan decode lebih tinggi. Perubahan sejalan dengan perbedaan
kondisi sesi, tetapi belum eksperimen isolasi penyebab: jangan mengklaim swap
sebagai satu-satunya penyebab. Hashing membaca weights, OS cache tidak dibuang;
load bukan cold start. RSS hanya child runtime, bukan total aplikasi.

## Kualitas dan rekomendasi

Jawaban setiap case ID identik dengan respons model yang sama pada E3/E4
(20 perbandingan cocok). Rubrik lama tetap: 0.6B 9/20 dan 1.7B 11/20; tidak
ada respons possibly_token_limited. 1.7B membaik pada JSON/kejujuran akses file,
tetapi tetap salah berhitung, membenarkan premis RAG salah, dan mengarang jumlah
anggota klub. Belum memilih model utama atau mengubah konfigurasi desktop.

Skor hanya berlaku untuk suite kecil dan konfigurasi ini. Benchmark sengaja
memakai temperature 0 untuk pembanding terkendali, bukan klaim sampling optimal.
Card resmi Qwen3-1.7B merekomendasikan non-thinking temperature 0.7, top_p 0.8,
top_k 20, min_p 0. [Sumber resmi, Best Practices](https://huggingface.co/Qwen/Qwen3-1.7B#best-practices),
diperiksa 2026-11-04. Peringatan eksplisit greedy pada card terkait thinking;
model kita diuji dengan thinking off, jadi jangan menyebut peringatan itu
sebagai diagnosis kegagalan non-thinking.

Usulan berikutnya: uji konfigurasi rekomendasi tersebut secara terpisah dengan
seed tercatat dan pengulangan; pertahankan suite/system prompt/budget/context
agar perubahan sampling terukur. Ini hipotesis eksperimen, belum bukti jawaban
akan membaik. Hasilnya tidak digabung dengan baseline greedy seolah konfigurasi
sama. Jangan mengubah sampling desktop, memperbesar context, atau mengunduh
model berikutnya sebelum checkpoint eksperimen disepakati.

Checkpoint E6 hanya review dokumentasi. Tidak ada kode/dependency baru.
Tes kode terakhir 192 PASS; tidak diulang untuk perubahan dokumen saja.
Diff diperiksa. Laporan raw dan model tetap diabaikan Git.
