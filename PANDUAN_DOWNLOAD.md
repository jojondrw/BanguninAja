# Panduan Download Dataset

Ikuti urut dari atas. Setelah selesai, isi folder `data/` kamu akan **sama persis** dengan anggota tim lain.

Total waktu: ~30 menit (sebagian besar cuma nunggu download).

---

## Checklist

- [ ] 0. Pasang QGIS
- [ ] 1. Siapkan Python
- [ ] 2. Kepadatan penduduk — WorldPop *(manual)*
- [ ] 3. Batas wilayah — GADM *(manual)*
- [ ] 4. POI, lahan, bangunan — OSM *(skrip)*
- [ ] 5. Bahaya bencana — InaRISK *(skrip)*
- [ ] 6. Statistik — BPS *(skrip)*
- [ ] 7. Olah jadi siap pakai *(skrip)*
- [ ] 8. Cek hasilnya cocok

Cuma 2 langkah manual (2 dan 3) karena situsnya butuh klik. Sisanya dijalankan skrip.

**Wilayah studi: DKI Jakarta** (5 kota, 43 kecamatan). Diatur di `scripts/wilayah.py` — kalau mau pindah wilayah, cukup ubah berkas itu.

---

## 0. Pasang QGIS

Wajib. Dipakai skrip untuk memotong data, dan dipakai kamu untuk melihat petanya.

1. [qgis.org/download](https://qgis.org/download/)
2. Pilih **Long Term Version (LTR)**
3. Install biasa (±583 MB, agak lama)

---

## 1. Siapkan Python

Dari folder utama proyek:

```bash
pip install requests pandas lxml html5lib beautifulsoup4 matplotlib
```

---

## 2. Kepadatan Penduduk — WorldPop *(manual, ~10 menit)*

1. Buka [hub.worldpop.org/geodata/summary?id=6376](https://hub.worldpop.org/geodata/summary?id=6376)
2. Scroll ke bawah → tombol **Download**
3. File `idn_ppp_2020.tif` terunduh (**±1 GB**, sabar)
4. Pindahkan ke `data/raw/`, ganti namanya jadi `worldpop_idn_2020.tif`

## 3. Batas Wilayah — GADM *(manual, ~5 menit)*

1. Buka [gadm.org/download_country.html](https://gadm.org/download_country.html)
2. Dropdown → pilih **Indonesia**
3. Klik **Shapefile** (`gadm41_IDN_shp.zip`, ±234 MB)
4. **Unzip** ke folder `data/raw/gadm/`

Hasilnya 25 berkas (`gadm41_IDN_0` sampai `_4`, masing-masing 5 berkas). Yang dipakai cuma level 3 (kecamatan), tapi biarkan semuanya.

> ⚠️ Harus di-unzip. Shapefile bukan satu berkas — `.shp` tidak bisa dibaca tanpa `.dbf`, `.shx`, dan `.prj` di folder yang sama.

---

## 4. POI, Lahan & Bangunan — OpenStreetMap *(skrip, ~5 menit)*

Dulu langkah ini manual lewat overpass-turbo.eu. Sekarang otomatis.

```bash
python scripts/ambil_poi.py
```

Empat kelompok yang diambil:

| Kelompok | Isi | Untuk apa |
|----------|-----|-----------|
| `kompetitor` | Restoran, kafe, mall, bank, hotel, minimarket | Menghitung persaingan |
| `lahan` | Lahan yang tipe penggunaannya layak dibangun | Kandidat lokasi (mode bangun baru) |
| `terlarang` | Taman, makam, air, hutan, permukiman | **Dikecualikan mutlak** |
| `komersial` | Bangunan niaga & ruko | Kandidat lokasi (mode sewa/beli unit) |

Kelompok `terlarang` yang mencegah sistem menyarankan taman kota atau halaman rumah orang.

> Kalau muncul "cermin sibuk", tunggu sebentar lalu ulangi. Server Overpass gratis dan kadang antre.

---

## 5. Bahaya Bencana — InaRISK *(skrip, ~1 menit)*

**Tidak perlu daftar akun.** Portal unduh InaRISK memang minta pendaftaran, tapi layanan REST BNPB terbuka penuh — skrip mengambil dari situ.

```bash
python scripts/ambil_inarisk.py
```

Hasil yang benar:

```
✅ banjir         769 KB  maks 1.00  →  inarisk_bahaya_banjir_dki.tif
✅ gempa          769 KB  maks 0.73  →  inarisk_bahaya_gempa_dki.tif
⏭️  longsor    kosong di wilayah ini — dilewati
✅ multi          769 KB  maks 1.00  →  inarisk_bahaya_multi_dki.tif
⏭️  kebakaran  kosong di wilayah ini — dilewati
⏭️  tsunami    nilainya nyaris nol (maks 0.050) — dilewati

3 dari 6 layer tersimpan di data/raw/
```

**3 layer terpakai, 3 dilewati.** Itu bukan kegagalan:

- **Longsor** dan **kebakaran hutan** — DKI datar dan tidak berhutan, servernya membalas berkas kosong.
- **Tsunami** — berkasnya terkirim penuh, tapi seluruh nilainya nyaris nol (maksimum 0,05 dari skala 0–1). Jakarta Utara memang berbatasan dengan laut, namun indeks bahaya tsunaminya dapat diabaikan. Skrip mengeceknya lewat isi raster, bukan ukuran berkas.

Lihat seluruh 158 layer yang disediakan BNPB:

```bash
python scripts/ambil_inarisk.py --daftar
```

---

## 6. Statistik — BPS *(skrip, ~5 menit)*

### Ambil API Key

1. Daftar di [webapi.bps.go.id/developer](https://webapi.bps.go.id/developer/) pakai email
2. Cek email → klik link aktivasi
3. **Profile → Applications → Add Application**
4. Salin API Key-nya

### Simpan key

Salin `.env.example` jadi `.env`, isi key-nya:

```
BPS_API_KEY=key_kamu_disini
```

⚠️ **Jangan commit `.env`.** Sudah diblokir `.gitignore`.

### Ambil 4 tabel ini

```bash
python scripts/bps.py ambil 3171 18
python scripts/bps.py ambil 3171 24
python scripts/bps.py ambil 3171 66
python scripts/bps.py ambil 3171 3
```

| ID | Isi |
|----|-----|
| **18** | Jumlah penduduk per kecamatan 2021 ⭐ paling penting |
| 24 | Penduduk per kecamatan menurut agama |
| 66 | PDRB triwulanan 2022–2024 |
| 3 | Penduduk miskin 2002–2012 |

Cari tabel lain:

```bash
python scripts/bps.py wilayah jakarta       # daftar kode wilayah
python scripts/bps.py cari 3171 penduduk    # cari tabel
```

---

## 7. Olah Jadi Siap Pakai *(skrip, ~2 menit)*

```bash
python scripts/siapkan_data.py
```

Yang dikerjakan:

| Dari | Jadi |
|------|------|
| GADM nasional (6.695 kecamatan) | **43 kecamatan** se-DKI Jakarta |
| WorldPop nasional (1.015 MB) | Potongan DKI (**0,5 MB**) |

Skrip juga membetulkan masalah di GADM: sebagian kecamatan tertulis dengan dua ejaan (*Kabayoran/Kebayoran Lama*, *Setia Budi/Setiabudi*), sehingga satu kecamatan terbaca sebagai dua poligon. Ejaannya diseragamkan sekalian disamakan dengan penulisan BPS supaya kedua sumber bisa digabung.

---

## 8. Cek Hasilnya Cocok

```bash
python scripts/lihat_data.py
```

Buka `reports/tampilan_data_dki.png`. Kalau muncul 4 panel peta, semuanya beres.

### Isi folder yang benar

**`data/raw/`**

| Berkas | Ukuran |
|--------|--------|
| `osm_kompetitor_dki.geojson` | ±2,7 MB — **8.026 titik** |
| `osm_terlarang_dki.geojson` | ±7,5 MB — 21.844 objek |
| `osm_komersial_dki.geojson` | ±1,4 MB — 6.206 objek |
| `osm_lahan_dki.geojson` | ±580 KB — 3.068 objek |
| `worldpop_idn_2020.tif` | ±1.015 MB |
| `inarisk_bahaya_banjir_dki.tif` | ±772 KB |
| `inarisk_bahaya_gempa_dki.tif` | ±772 KB |
| `inarisk_bahaya_multi_dki.tif` | ±772 KB |
| `bps_*.csv` | beberapa KB |
| `gadm/` | 25 berkas, ±410 MB |

**`data/processed/`**

| Berkas | Ukuran |
|--------|--------|
| `dki_kecamatan_bersih.gpkg` | ±524 KB — **harus 43 kecamatan** |
| `worldpop_dki_2020.tif` | ±464 KB — **harus 390 × 384 piksel** |

Semua raster berukuran **390 × 384 piksel** (±92 m per piksel) pada extent yang sama, jadi bisa ditumpuk piksel per piksel tanpa penyesuaian.

---

## Kalau Nyangkut

| Masalah | Solusi |
|---------|--------|
| `ambil_poi.py` bilang cermin sibuk | Server Overpass gratis sedang antre. Tunggu 1–2 menit, jalankan lagi |
| `ambil_poi.py` balas 406 | Versi skrip lama. Tarik pembaruan: `git pull` |
| `.tif` gelap semua di Photos | Wajar — itu grid angka. Buka pakai QGIS atau jalankan `lihat_data.py` |
| Skrip bilang GDAL tidak ketemu | QGIS belum terpasang, atau set `GDAL_BIN` ke folder bin QGIS |
| `bps.py` bilang API Key belum ada | Berkas `.env` belum dibuat atau salah isi |
| `siapkan_data.py` melewati langkah | Berkas sumbernya belum ada — cek nama berkasnya sudah persis |
| Shapefile tidak terbaca | Belum di-unzip, atau `.dbf`/`.shx` terpisah dari `.shp` |

---

## ⚠️ Aturan Data

**Jangan commit isi folder `data/` ke GitHub.** Berkas geospasial terlalu besar — sudah diblokir `.gitignore`.

Setiap orang mengunduh sendiri mengikuti panduan ini. Itu sebabnya penamaan berkas harus persis: supaya skrip berjalan sama di semua komputer.

Kalau perlu berbagi hasil olahan, upload ke Google Drive lalu catat tautannya di tabel **"Data bersama tim"** pada [`DATASETS.md`](DATASETS.md).
