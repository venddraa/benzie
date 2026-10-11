# Visi Benzie

Benzie adalah personal AI assistant milik pengguna, dikembangkan bertahap tanpa
deadline. Nama berasal dari kucing jantan pertama yang diadopsi pengguna.

Runtime harus local-first: setelah model dan dependency tersedia, percakapan
harus tetap berfungsi tanpa internet dan tanpa cloud AI API. Data pribadi tetap
lokal; tidak ada telemetry atau analytics.

Visi jangka panjang meliputi percakapan, memory yang dapat dilihat/dikoreksi/
dihapus/ditelusuri, pencarian pengetahuan lokal, tools dengan permission, integrasi
desktop, voice, vision, dan mungkin avatar terpisah dari core. Semuanya di luar
scope fondasi saat ini.

V0.1 hanya desktop text chat lokal, model yang dapat diganti, error handling,
serta history yang bisa dibuka kembali. History bukan personal memory.

Compute eksternal boleh menjadi workshop untuk eksperimen/training berat;
artefaknya kembali ke runtime lokal. Percakapan, file pribadi, database,
credential, atau data sensitif tidak boleh diunggah tanpa diskusi dan persetujuan
eksplisit pengguna. Pretraining foundation model dari nol bukan target.

Stack boleh berubah berdasarkan kebutuhan dan bukti. Perubahan fondasi besar
memerlukan penjelasan masalah, alternatif, trade-off, biaya migrasi,
rekomendasi, dan keputusan pengguna.

Prioritas: clarity, maintainability, modularity, testability, observability.
Tidak ada agent framework, microservices, atau dependency untuk kebutuhan
hipotetis. Setiap milestone berhenti untuk review; commit/push menunggu izin.
