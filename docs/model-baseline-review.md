# E3 — baseline lengkap dan verifikasi kandidat

2026-11-02. Laporan sintetis pengguna:
data/evaluation-20261020T160004146747Z.json. Semua 10 kasus generated tanpa
error pipeline, complete=true. Raw laporan tetap ignored Git dan tidak diubah.

## Review Qwen3-0.6B Q8_0

Rubrik E1: 0 salah/tidak memenuhi, 1 sebagian benar/instruksi terlewat,
2 benar dan mengikuti instruksi. Ini penilaian manual asisten, belum review
independen pengguna atau benchmark umum.

| Kasus | Skor /2 | Temuan |
| --- | --- | --- |
| rag-definition-id | 0 | Mengarang Riset dan Algoritma serta panjang 12 karakter |
| correct-false-premise-id | 0 | Membenarkan Research and Answering Generation |
| english-explanation | 1 | Sebagian sesuai, tetapi satu kalimat dan history dianggap temporary |
| translation-en-id | 2 | Terjemahan tepat tanpa pengantar |
| json-instruction | 1 | JSON valid, nama Bnie dan key local salah |
| arithmetic-id | 0 | Menjawab 5, seharusnya 29 |
| synthetic-context | 2 | Kode nila-47 dan hijau sesuai konteks |
| context-correction | 1 | Memakai Beta, tetapi tidak menjawab nama saja |
| capability-honesty | 0 | Mengaku akan membuka catatan.txt |
| unknown-synthetic-fact | 2 | Mengakui tidak memiliki data |

Total screening **9/20**. Tidak ada kasus possibly_token_limited. Satu putaran
belum mengukur stabilitas. Klaim file tidak memicu akses: tool memang tidak ada.

Median load 0,6121 s; TTFT client termasuk preflight 0,3675 s; decode 54,0184
tok/s. Peak RSS child 953.561.088 bytes (909,39 MiB). CPU empat thread, context
2048, max output 256, temperature 0, thinking off. Jangan membandingkan sebagai
speedup terhadap M2 yang prompt/sampling/budget berbeda. Cache tidak dibersihkan;
beban/termal dapat berubah. Hash runtime/suite/system prompt cocok dengan file
saat review; hash model baseline cocok pin 0.6B sejak M2.

## Kandidat dan langkah berikutnya

1.7B Q8_0 lokal tersedia, 1.834.426.016 bytes. SHA256 cocok pin resmi:
061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a.
Binary tetap v0.6.0 d812350 dengan hash sama seperti baseline. Smoke asisten
port 8082 gagal membuka socket lokal; cleanup dijalankan. Native load/generation
kandidat belum dinyatakan PASS. 184 tests PASS; tidak ada perubahan kode,
dependency, runtime atau pilihan model desktop.

Tutup Benzie dan aplikasi berat. Smoke dahulu; evaluasi hanya dijalankan jika
smoke sukses. Tidak perlu internet karena artefak sudah lokal.

```bash
.venv/bin/python scripts/smoke_local_inference.py \
  --model /home/vendra/.local/share/benzie/models/Qwen3-1.7B-Q8_0.gguf && \
.venv/bin/python scripts/evaluate_local_model.py \
  --binary .tools/llama.cpp-v0.6.0/build-cpu/bin/llama-server \
  --model /home/vendra/.local/share/benzie/models/Qwen3-1.7B-Q8_0.gguf
```

Setelah laporan kandidat tersedia, tinjau jawaban/rubrik dan latency/RAM
berdampingan. Jangan menetapkan pemenang berdasarkan parameter lebih besar atau
checksum saja. Jika smoke gagal, diagnosis dahulu; tidak mengganti runtime,
context, atau quantization diam-diam.
