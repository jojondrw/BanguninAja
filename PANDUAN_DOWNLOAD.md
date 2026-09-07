# Panduan Download Dataset

Panduan langkah demi langkah untuk anggota tim. Kerjakan berurutan — makin ke bawah makin ribet.

**Simpan semua hasil download ke folder `data/raw/`.**

Aturan penamaan file:
```
<sumber>_<wilayah>_<tahun>.<ext>

contoh:  osm_jaksel_2026.geojson
```

---

## Checklist Tim

Centang kalau sudah selesai, lalu commit perubahannya.

- [ ] 1. POI kompetitor (Overpass)
- [ ] 2. Kepadatan penduduk (WorldPop)
- [ ] 3. Risiko bencana (InaRISK)
- [ ] 4. API Key BPS
- [ ] 5. Batas wilayah (GADM)
- [ ] 6. QGIS terpasang

---

## 0. Pasang QGIS dulu

Tanpa ini, file `.tif` dan `.shp` tidak bisa dibuka.

1. Buka [qgis.org/download](https://qgis.org/download/)
2. Pilih **Long Term Version (LTR)** — lebih stabil
3. Install seperti biasa, next-next-finish

---

## 1. POI Kompetitor — Overpass Turbo

⏱️ ~5 menit · 🟢 Paling gampang

1. Buka [overpass-turbo.eu](https://overpass-turbo.eu/)
2. **Geser & zoom peta** ke wilayah studi kasus (contoh: Jakarta Selatan)
   > ⚠️ Zoom secukupnya. Kalau areanya kelewat luas, query-nya timeout.
3. Hapus isi kotak kiri
4. Buka file [`queries/poi_kompetitor.overpassql`](queries/poi_kompetitor.overpassql), copy semua isinya, paste ke kotak kiri
5. Klik tombol **Run** (▶)
6. Tunggu sampai titik-titik muncul di peta
7. Klik **Export** → **download as GeoJSON**
8. Simpan ke `data/raw/` dengan nama `osm_<wilayah>_2026.geojson`

### Cara ganti kategori

Pola tiap baris:
```
node["amenity"="restaurant"]({{bbox}});
       ↑kunci      ↑nilai
```

Yang diganti cuma isi dalam kutip:

| Mau cari | Tulis begini |
|----------|--------------|
| Klub malam | `node["amenity"="nightclub"]({{bbox}});` |
| Bar | `node["amenity"="bar"]({{bbox}});` |
| Hotel | `node["tourism"="hotel"]({{bbox}});` |
| Minimarket | `node["shop"="convenience"]({{bbox}});` |
| Mall | `node["shop"="mall"]({{bbox}});` |
| Rumah sakit | `node["amenity"="hospital"]({{bbox}});` |

> **Perhatikan kuncinya bisa beda.** Mall pakai `shop`, bukan `amenity`.

### Kenapa ada `node` dan `way`?

- `node` = titik (kafe kecil)
- `way` = area/bangunan (mall, rumah sakit)

Bangunan besar sering terdaftar sebagai `way`. Kalau cuma ambil `node`, banyak yang kelewat. Baris `out center;` di akhir yang membuat `way` ikut keluar sebagai titik tengah.

Daftar tag lengkap: [OSM Map Features](https://wiki.openstreetmap.org/wiki/Map_features)

---

## 2. Kepadatan Penduduk — WorldPop

⏱️ ~10 menit (filenya besar) · 🟢

1. Buka [hub.worldpop.org/geodata/summary?id=6376](https://hub.worldpop.org/geodata/summary?id=6376)
2. Scroll ke bawah, cari tombol **Download**
3. File `.tif` (GeoTIFF) akan terunduh — sabar, ukurannya lumayan
4. Simpan ke `data/raw/` dengan nama `worldpop_idn_2020.tif`

**Cara buka:** drag file `.tif` langsung ke jendela QGIS.

Isinya: jumlah orang per petak 100×100 meter.

---

## 3. Risiko Bencana — InaRISK

⏱️ ~10 menit · 🟢

1. Buka [inarisk2.bnpb.go.id/portal](https://inarisk2.bnpb.go.id/portal/)
2. Di menu atas, klik **"Unduh Data Peta"**
3. Pilih jenis bahaya. Untuk proyek ini yang paling terpakai:
   - **Banjir** ← ambil ini dulu, paling berpengaruh ke keputusan lokasi
   - Gempa Bumi
   - Longsor
4. Pilih wilayah studi kasus
5. Download
6. Simpan ke `data/raw/` dengan nama `inarisk_banjir_<wilayah>_2026.geojson`

### Alternatif: langsung dari QGIS

Kalau portalnya ribet, tarik layernya langsung:

**QGIS → menu Layer → Add Layer → Add ArcGIS REST Server Layer**

Lalu masukkan URL REST service InaRISK. Cara ini lebih cepat kalau cuma mau lihat-lihat.

---

## 4. API Key BPS

⏱️ ~5 menit · 🔑 Perlu daftar

1. Buka [webapi.bps.go.id/developer](https://webapi.bps.go.id/developer/)
2. Daftar pakai email
3. Cek email → klik link aktivasi
4. Masuk ke menu **Profile → Applications → Add Application**
5. Salin **API Key** yang muncul

### Simpan key-nya

⚠️ **JANGAN commit API Key ke GitHub.**

Salin `.env.example` jadi `.env` di folder utama proyek, lalu isi key-nya:

```
BPS_API_KEY=key_kamu_disini
```

File `.env` sudah diblokir lewat `.gitignore`, jadi aman.

### Ambil datanya

Sudah ada skrip siap pakai di [`scripts/bps.py`](scripts/bps.py). Jalankan dari folder utama proyek.

**Langkah 1 — cari kode wilayah:**

```bash
python scripts/bps.py wilayah jakarta
```

Keluar daftar kode wilayah. Catat kode kota yang jadi studi kasus.

**Langkah 2 — cari tabel yang dibutuhkan:**

```bash
python scripts/bps.py cari 3171 penduduk
```

Ganti `3171` dengan kode wilayahmu. Kata kunci yang berguna untuk proyek ini:

| Kata kunci | Dapat apa |
|-----------|-----------|
| `penduduk` | Jumlah & kepadatan penduduk |
| `pengeluaran` | Pengeluaran per kapita (proxy daya beli) |
| `pdrb` | Produk domestik regional bruto |
| `kemiskinan` | Persentase penduduk miskin |
| `kesehatan` | Jumlah faskes |
| `pendidikan` | Jumlah sekolah |

**Langkah 3 — ambil tabelnya:**

```bash
python scripts/bps.py ambil 3171 123
```

Angka terakhir adalah `table_id` dari hasil langkah 2. Hasilnya otomatis tersimpan sebagai CSV di `data/raw/`.

Dokumentasi API: [webapi.bps.go.id/documentation](https://webapi.bps.go.id/documentation/)

---

## 5. Batas Wilayah — GADM

⏱️ ~3 menit · 🟢

1. Buka [gadm.org/download_country.html](https://gadm.org/download_country.html)
2. Pilih **Indonesia** dari dropdown
3. Download format **Shapefile** atau **GeoPackage**
4. Simpan ke `data/raw/`

Isinya batas provinsi, kabupaten/kota, kecamatan. Dipakai untuk memotong data agar fokus ke satu wilayah saja.

> **Catatan lisensi:** GADM hanya untuk penggunaan non-komersial. Aman untuk tugas kuliah.

---

## 6. Opsional — kalau sudah selesai semua

| Data | Link | Untuk apa |
|------|------|-----------|
| Peta RBI resmi | [Ina-Geoportal](https://tanahair.indonesia.go.id/portal-web/unduh) | Batas wilayah versi resmi BIG (perlu daftar) |
| Banjir real-time | [PetaBencana API](https://docs.petabencana.id/routes) | Data banjir terkini |
| Nightlight | [VIIRS di GEE](https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_MONTHLY_V1_VCMSLCFG) | Proxy keramaian malam |
| Jalan lengkap | [Geofabrik](https://download.geofabrik.de/asia/indonesia.html) | 1,6 GB — hanya kalau butuh jaringan jalan penuh |

---

## Setelah Semua Terkumpul

Buka QGIS, lalu tumpuk layer berurutan dari bawah ke atas:

```
1. Batas wilayah (GADM)        ← paling bawah
2. Kepadatan penduduk (WorldPop)
3. Risiko banjir (InaRISK)
4. POI kompetitor (OSM)        ← paling atas
```

Dari tumpukan ini polanya mulai kelihatan: mana daerah padat tapi minim fasilitas, mana yang ramai tapi rawan banjir.

Itu bahan mentah untuk mesin skoring.

---

## Kalau Nyangkut

| Masalah | Penyebab & solusi |
|---------|-------------------|
| Overpass timeout | Area kelewat luas — zoom lebih dekat, atau kurangi jumlah kategori |
| File `.tif` gak bisa dibuka | Belum pasang QGIS. Jangan dibuka pakai Photos/Paint |
| Download WorldPop lama | Wajar, filenya besar. Tunggu saja |
| Hasil Overpass kosong | Salah tag, atau memang tidak ada objeknya di area itu. Coba tag lain |
| Layer QGIS tidak sejajar | Beda sistem koordinat. Set project CRS ke **EPSG:4326 (WGS 84)** |

---

## ⚠️ Aturan Penting

**Jangan commit file di folder `data/` ke GitHub.** File geospasial ukurannya besar dan bikin repo berat — sudah diblokir lewat `.gitignore`.

Kalau perlu berbagi hasil download ke tim:
1. Upload ke Google Drive
2. Catat linknya di tabel **"Data bersama tim"** di [`DATASETS.md`](DATASETS.md)
3. Commit perubahan `DATASETS.md`-nya saja
