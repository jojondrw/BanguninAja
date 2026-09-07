# Panduan Download Dataset

Ikuti urut dari atas. Setelah selesai, isi folder `data/` kamu akan **sama persis** dengan anggota tim lain.

Total waktu: ~30 menit (sebagian besar cuma nunggu download).

---

## Checklist

- [ ] 0. Pasang QGIS
- [ ] 1. Siapkan Python
- [ ] 2. POI kompetitor — Overpass *(manual)*
- [ ] 3. Kepadatan penduduk — WorldPop *(manual)*
- [ ] 4. Batas wilayah — GADM *(manual)*
- [ ] 5. Bahaya bencana — InaRISK *(skrip)*
- [ ] 6. Statistik — BPS *(skrip)*
- [ ] 7. Olah jadi siap pakai *(skrip)*
- [ ] 8. Cek hasilnya cocok

Tiga langkah manual (2–4) tidak bisa diotomatiskan karena situsnya butuh klik. Sisanya dijalankan skrip.

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

## 2. POI Kompetitor — Overpass Turbo *(manual, ~5 menit)*

1. Buka [overpass-turbo.eu](https://overpass-turbo.eu/)
2. **Zoom peta ke Jakarta Selatan** sampai satu kota kelihatan penuh di layar
3. Hapus isi kotak kiri, paste query ini **persis**:

```
[out:json][timeout:90];
(
  node["amenity"="restaurant"]({{bbox}});
  node["amenity"="cafe"]({{bbox}});
  node["amenity"="fast_food"]({{bbox}});
  node["shop"="mall"]({{bbox}});
  way["shop"="mall"]({{bbox}});
  node["shop"="supermarket"]({{bbox}});
  node["shop"="convenience"]({{bbox}});
  node["amenity"="bank"]({{bbox}});
  node["tourism"="hotel"]({{bbox}});
);
out center;
```

4. Klik **Run** (▶), tunggu titik muncul
5. **Export** → **download as GeoJSON**
6. Pindahkan ke `data/raw/` dan **ganti namanya** jadi:

```
osm_poi_jaksel_2026.geojson
```

> Hasilnya sekitar **3.900–4.000 titik**. Kalau jauh lebih sedikit, zoom-nya kurang lebar. Kalau query timeout, zoom-nya kelebaran.

---

## 3. Kepadatan Penduduk — WorldPop *(manual, ~10 menit)*

1. Buka [hub.worldpop.org/geodata/summary?id=6376](https://hub.worldpop.org/geodata/summary?id=6376)
2. Scroll ke bawah → tombol **Download**
3. File `idn_ppp_2020.tif` terunduh (**±1 GB**, sabar)
4. Pindahkan ke `data/raw/` dan **ganti namanya** jadi:

```
worldpop_idn_2020.tif
```

---

## 4. Batas Wilayah — GADM *(manual, ~5 menit)*

1. Buka [gadm.org/download_country.html](https://gadm.org/download_country.html)
2. Dropdown → pilih **Indonesia**
3. Klik **Shapefile** (`gadm41_IDN_shp.zip`, ±234 MB)
4. **Unzip** ke folder `data/raw/gadm/`

Hasilnya 25 berkas (`gadm41_IDN_0` sampai `_4`, masing-masing 5 berkas). Yang dipakai cuma level 3 (kecamatan), tapi biarkan semuanya.

> ⚠️ Harus di-unzip. Shapefile bukan satu berkas — `.shp` tidak bisa dibaca tanpa `.dbf`, `.shx`, dan `.prj` di folder yang sama.

---

## 5. Bahaya Bencana — InaRISK *(skrip, ~1 menit)*

**Tidak perlu daftar akun.** Portal unduh InaRISK memang minta pendaftaran, tapi layanan REST BNPB terbuka penuh — skrip mengambil dari situ.

```bash
python scripts/ambil_inarisk.py
```

Hasil yang benar:

```
✅ banjir         385 KB  →  inarisk_bahaya_banjir_jaksel.tif
✅ gempa          385 KB  →  inarisk_bahaya_gempa_jaksel.tif
⏭️  longsor    kosong di wilayah ini — dilewati
✅ multi          385 KB  →  inarisk_bahaya_multi_jaksel.tif
⏭️  kebakaran  kosong di wilayah ini — dilewati
⏭️  tsunami    kosong di wilayah ini — dilewati

3 dari 6 layer tersimpan di data/raw/
```

**3 layer terpakai, 3 dilewati.** Longsor, tsunami, dan kebakaran hutan memang kosong di Jakarta Selatan — wilayahnya datar, bukan pesisir, dan tidak berhutan. Itu bukan kegagalan.

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
| GADM nasional (6.695 kecamatan) | 10 kecamatan Jakarta Selatan |
| WorldPop nasional (1.015 MB) | Potongan Jaksel (**0,2 MB**) |

Skrip juga membetulkan masalah di GADM: sebagian kecamatan tertulis dengan dua ejaan (*Kabayoran/Kebayoran Lama*, *Setia Budi/Setiabudi*), sehingga Jakarta Selatan terbaca 12 poligon padahal kecamatannya 10. Ejaannya diseragamkan sekalian disamakan dengan penulisan BPS supaya kedua sumber bisa digabung.

---

## 8. Cek Hasilnya Cocok

```bash
python scripts/lihat_data.py
```

Buka `reports/tampilan_data.png`. Kalau muncul 4 panel peta, semuanya beres.

### Isi folder yang benar

**`data/raw/`**

| Berkas | Ukuran |
|--------|--------|
| `osm_poi_jaksel_2026.geojson` | ±2,0 MB |
| `worldpop_idn_2020.tif` | ±1.015 MB |
| `inarisk_bahaya_banjir_jaksel.tif` | 385 KB |
| `inarisk_bahaya_gempa_jaksel.tif` | 385 KB |
| `inarisk_bahaya_multi_jaksel.tif` | 385 KB |
| `bps_3171_18_*.csv` | ±0,5 KB |
| `bps_3171_24_*.csv` | ±2 KB |
| `bps_3171_66_*.csv` | ±6 KB |
| `bps_3171_3_*.csv` | ±1 KB |
| `gadm/` | 25 berkas, ±410 MB |

**`data/processed/`**

| Berkas | Ukuran |
|--------|--------|
| `jaksel_kecamatan_bersih.gpkg` | ±224 KB — **harus 10 kecamatan** |
| `worldpop_jaksel_2020.tif` | ±207 KB — **harus 229 × 268 piksel** |

Semua raster berukuran **229 × 268 piksel** pada extent yang sama, jadi bisa ditumpuk piksel per piksel tanpa penyesuaian.

---

## Kalau Nyangkut

| Masalah | Solusi |
|---------|--------|
| Overpass timeout | Zoom lebih dekat, atau kurangi kategori |
| Hasil POI cuma ratusan | Zoom kurang lebar, ulangi |
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
