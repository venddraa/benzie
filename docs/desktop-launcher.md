# Launcher Fedora — M5.2

Ini shortcut untuk checkout development yang sudah memiliki .venv dan dependency
terpasang. Tidak menyalin aplikasi, memasang paket, menjalankan uv, atau mengunduh
apa pun. Tidak membutuhkan sudo.

## Memasang

Dari root repository, pada terminal desktop:

```bash
.venv/bin/python scripts/desktop_launcher.py
```

Installer menulis satu `benzie.desktop` ke `$XDG_DATA_HOME/applications`, atau
`~/.local/share/applications` jika XDG_DATA_HOME tidak absolut. Cari **Benzie**
di menu Applications. Exec menunjuk Python .venv dengan `-m benzie`, Terminal=false.
Ikon menggunakan ikon utility sistem; belum ada aset branding khusus.

Default launcher memakai profil data normal mengikuti XDG, bukan direktori
`/tmp` dari smoke test sebelumnya. Pilih runtime/model melalui **Model lokal…**
saat pertama kali dibuka; konfigurasi dan history lalu tersimpan di profil itu.
Tidak menyalin history atau konfigurasi smoke ke profil utama otomatis.

Untuk shortcut yang sengaja memakai profil smoke terpisah:

```bash
.venv/bin/python scripts/desktop_launcher.py --data-dir /tmp/benzie-launcher-smoke
```

Perintah ini mengganti shortcut Benzie milik installer sebelumnya. Pasang ulang
tanpa --data-dir untuk kembali memakai profil default. /tmp tidak untuk data penting.
Installer menolak menimpa symlink atau file bernama sama yang tidak ditandai
sebagai miliknya. Tidak mengubah shortcut aplikasi lain.

## Batas development

Folder repository dan .venv harus tetap tersedia. Jika repository dipindah,
buat ulang environment sesuai panduan development lalu jalankan installer lagi.
Tidak ada dependency pada cwd terminal atau aktivasi venv. Path dengan spasi
dan karakter kutip didukung; persen, karakter kontrol, dan tanda `=` di path
executable ditolak dengan penjelasan. Build paket mandiri/RPM belum dibuat.

## Melepas

```bash
.venv/bin/python scripts/desktop_launcher.py --remove
```

Hanya file shortcut yang dihapus. Model, database, konfigurasi, .venv, dan
repository tetap ada. Shortcut bisa dipulihkan dengan perintah pemasangan.

## Verifikasi

Tes otomatis menggunakan direktori sementara: install/update/remove, kegagalan
atomic replace, proteksi file lain/symlink, quoting path, parser GLib, validator
desktop Fedora, serta import package dari cwd lain. Validator/GLib memakai
utilitas sistem jika tersedia, tidak menambah dependency runtime Benzie.

Manual: pasang, cari Benzie di Applications, buka tanpa terminal, pilih model,
kirim pesan, tutup lalu buka lagi dan lanjutkan history. Pemasangan pada profil
desktop utama dilakukan pengguna karena sesi asisten tidak dapat menulis ke sana.
Acceptance internet-off lengkap menjadi checkpoint terpisah; M5.2 belum
menyatakan seluruh V0.1 selesai.

Format Exec mengikuti [spesifikasi desktop freedesktop](https://specifications.freedesktop.org/desktop-entry/latest/exec-variables.html),
termasuk dua lapis escaping string dan argument. Diperiksa 2026-10-15.
