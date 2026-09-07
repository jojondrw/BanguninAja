# Katalog Dataset — BanguninAja

Semua sumber data di bawah ini **sudah dicek dan bisa diakses** (per 7 September 2026).

Kolom **Status**:
- 🟢 **Langsung** — klik, download, selesai
- 🔑 **Daftar** — gratis tapi harus bikin akun dulu
- 🟡 **Manual** — datanya ada tapi perlu diolah/input tangan

---

## ⚡ Mulai dari sini (cukup 4 ini dulu)

| No | Data | Sumber | Status |
|----|------|--------|--------|
| 1 | POI kompetitor | [Overpass Turbo](https://overpass-turbo.eu/) | 🟢 |
| 2 | Kepadatan penduduk | [WorldPop Indonesia](https://hub.worldpop.org/geodata/summary?id=6376) | 🟢 |
| 3 | Risiko bencana | [InaRISK BNPB](https://inarisk2.bnpb.go.id/portal/) | 🟢 |
| 4 | Statistik wilayah | [WebAPI BPS](https://webapi.bps.go.id/developer/) | 🔑 |

Empat ini sudah cukup untuk membuat mesin skoring pertama jalan.

---

## 1. Peta Dasar & Batas Wilayah

| Data | Sumber | Format | Lisensi | Status |
|------|--------|--------|---------|--------|
| Jalan, bangunan, POI (OSM) | [Geofabrik Indonesia](https://download.geofabrik.de/asia/indonesia.html) | `.osm.pbf`, `.gpkg` | ODbL | 🟢 |
| Batas administrasi (cepat) | [GADM](https://gadm.org/download_country.html) | SHP, GPKG | Non-komersial | 🟢 |
| Peta RBI & batas desa | [Ina-Geoportal BIG](https://tanahair.indonesia.go.id/portal-web/unduh) | SHP | Terbuka | 🔑 |

**Catatan Geofabrik:** file Indonesia penuh **1,6 GB**. Kalau cuma butuh satu pulau, ambil sub-region (Jawa 854 MB). Untuk POI saja, **pakai Overpass** — jauh lebih ringan.

---

## 2. Penduduk & Demografi

| Data | Sumber | Format | Lisensi | Status |
|------|--------|--------|---------|--------|
| Kepadatan penduduk 100m | [WorldPop Indonesia](https://hub.worldpop.org/geodata/summary?id=6376) | GeoTIFF | CC BY 4.0 | 🟢 |
| Proyeksi penduduk 2027 | [WorldPop STAC](https://stac.worldpop.org/collections/IDN/items/idn_pop_2027_CN_100m_R2025A_v1) | GeoTIFF | CC BY 4.0 | 🟢 |
| Sensus, umur, pendidikan | [WebAPI BPS](https://webapi.bps.go.id/developer/) | JSON | Terbuka | 🔑 |
| Kepadatan resolusi tinggi | [Meta HRSL via HDX](https://data.humdata.org/) | CSV, GeoTIFF | CC BY 4.0 | 🟢 |

---

## 3. Ekonomi & Daya Beli

| Data | Sumber | Format | Status |
|------|--------|--------|--------|
| PDRB & pengeluaran per kapita | [WebAPI BPS](https://webapi.bps.go.id/developer/) | JSON | 🔑 |
| Nightlight (proxy aktivitas ekonomi) | [VIIRS di Google Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_MONTHLY_V1_VCMSLCFG) | Raster 463m | 🟢 |
| Dataset pemerintah umum | [Satu Data Indonesia](https://data.go.id/dataset) | Bervariasi | 🟢 |
| Dataset DKI Jakarta | [Satu Data Jakarta](https://satudata.jakarta.go.id/) | Bervariasi | 🟢 |

**VIIRS**: resolusi 463 m, tersedia **Januari 2014 – Juli 2026**, public domain. Bagus untuk menilai keramaian malam hari (profil hiburan & F&B).

---

## 4. POI & Kompetitor

Sumber utama: **[Overpass Turbo](https://overpass-turbo.eu/)** — query siap pakai ada di folder [`queries/`](queries/).

| Kategori | Tag OSM |
|----------|---------|
| Restoran | `amenity=restaurant` |
| Kafe | `amenity=cafe` |
| Mall | `shop=mall` |
| Klub malam | `amenity=nightclub` |
| Bar | `amenity=bar` |
| Minimarket | `shop=convenience` |
| Supermarket | `shop=supermarket` |
| Rumah sakit | `amenity=hospital` |
| Klinik | `amenity=clinic` |
| Sekolah | `amenity=school` |
| Hotel | `tourism=hotel` |
| Bank / ATM | `amenity=bank` / `amenity=atm` |
| Parkir | `amenity=parking` |

Referensi tag lengkap: [OSM Map Features](https://wiki.openstreetmap.org/wiki/Map_features)

---

## 5. Fasilitas Kesehatan

| Data | Sumber | Status |
|------|--------|--------|
| Daftar RS nasional (3.000+) | [RS Kemenkes](https://rs.kemkes.go.id/hospitals) | 🟡 |
| Dashboard SIRS | [SIRS Kemenkes](https://sirs.kemkes.go.id/fo/home/dashboard_rs) | 🟡 |

Berisi nama, alamat, kelas RS, kepemilikan, jumlah tempat tidur, dokter spesialis, fasilitas ICU.

> Untuk analisis spasial cepat, **Overpass (`amenity=hospital`) lebih praktis** karena koordinatnya langsung tersedia.

---

## 6. Risiko Bencana

| Data | Sumber | Akses | Status |
|------|--------|-------|--------|
| Indeks risiko multi-bahaya | [InaRISK BNPB](https://inarisk.bnpb.go.id/) | Web, REST API, Geoserver | 🟢 |
| Portal unduh peta | [InaRISK Download](https://inarisk2.bnpb.go.id/portal/) | Download layer | 🟢 |
| Banjir real-time | [PetaBencana API](https://docs.petabencana.id/routes) | REST API, CC BY 4.0 | 🟢 |
| Gempa & cuaca | [BMKG](https://www.bmkg.go.id/) | Web, API | 🟢 |

**Bahaya yang tercakup InaRISK:** banjir, banjir bandang, gempa bumi, tsunami, longsor, likuefaksi, letusan gunung api, kekeringan, cuaca ekstrem, gelombang ekstrem & abrasi, kebakaran hutan.

Empat dimensi analisis: **Bahaya · Kerentanan · Kapasitas · Risiko**

**PetaBencana endpoint:** `/floods`, `/floods/timeseries`, `/reports`, `/reports/archive`, `/infrastructure`
Format output: JSON, XML, GeoJSON, TopoJSON, CAP

---

## 7. Aksesibilitas & Rute

| Data | Sumber | Catatan | Status |
|------|--------|---------|--------|
| Rute & matriks waktu tempuh | [OSRM API](http://project-osrm.org/docs/v5.24.0/api/) | Demo server `router.project-osrm.org` | 🟢 |
| Alternatif | [GraphHopper](https://www.graphhopper.com/) | Bisa self-host | 🟢 |
| Distance Matrix | [Google Maps Platform](https://developers.google.com/maps/documentation/distance-matrix) | Ada free tier, lalu berbayar | 🔑 |

**Layanan OSRM:** `route` · `table` (matriks) · `nearest` · `match` · `trip` · `tile`

> ⚠️ Demo server OSRM punya **rate limit** (jeda maksimal 5 detik antar request, 512 request per koneksi). Jangan dipakai untuk batch besar — kalau butuh banyak, self-host pakai Docker.

---

## 8. Citra Satelit (opsional)

| Data | Sumber | Resolusi | Status |
|------|--------|----------|--------|
| Sentinel-2 | [Copernicus Browser](https://browser.dataspace.copernicus.eu/) | 10 m | 🔑 |
| Landsat | [USGS EarthExplorer](https://earthexplorer.usgs.gov/) | 30 m | 🔑 |
| Katalog lengkap | [Google Earth Engine](https://developers.google.com/earth-engine/datasets) | Bervariasi | 🔑 |

---

## 9. Zonasi & Lahan ⚠️ *(paling sulit)*

| Data | Sumber | Kendala |
|------|--------|---------|
| RTRW / peta zonasi | Situs Dinas Tata Ruang tiap kota | Mayoritas **PDF**, bukan data terstruktur |
| Kesesuaian ruang (KKPR) | [OSS](https://oss.go.id/) | Per-permohonan, bukan dataset terbuka |
| Bidang tanah | ATR/BPN — Sentuh Tanahku | Akses terbatas |
| Harga tanah (NJOP) | Bapenda / Pemda setempat | Per kelurahan, format bervariasi |

### Keputusan tim

Data zonasi **tidak tersedia dalam format terbuka yang bisa dibaca mesin**. Ini dicatat sebagai **asumsi & keterbatasan** di dokumen requirement:

> *Data zonasi diinput manual oleh admin sistem karena belum tersedia dalam format terbuka yang dapat diproses secara otomatis.*

**Jangan scraping** situs properti (Rumah123, 99.co, Lamudi) — melanggar Terms of Service. Kalau butuh harga tanah, pakai **NJOP** resmi dari Bapenda.

---

## Metode: Mengukur Daya Beli per Kecamatan

Daya beli adalah kriteria terpenting untuk profil **mall/retail** dan **hiburan/F&B**. Sistem mengukurnya dengan **indeks komposit** dari tiga sumber, bukan dari satu angka tunggal:

| Komponen | Sumber | Bobot | Alasan |
|----------|--------|-------|--------|
| Intensitas cahaya malam | [VIIRS](https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_MONTHLY_V1_VCMSLCFG) | 40% | Terang = aktivitas ekonomi tinggi. Resolusi 463 m, jauh lebih halus dari batas administrasi |
| Kepadatan POI komersial | [OSM](https://overpass-turbo.eu/) | 40% | Banyak bank, kafe, minimarket = daya beli tinggi. Resolusi titik |
| PDRB & indikator ekonomi | [BPS](https://webapi.bps.go.id/) | 20% | Jangkar kalibrasi tingkat kota |

### Kenapa indeks komposit

Angka pengeluaran per kapita BPS diterbitkan pada level kota — cocok sebagai jangkar, tapi terlalu kasar untuk membedakan antar-kecamatan. VIIRS dan kepadatan POI memberi variasi spasial yang dibutuhkan, lalu dikalibrasi ke angka BPS supaya tetap terhubung ke statistik resmi.

Pendekatan ini adalah praktik standar di **location intelligence** — nightlight sudah lama dipakai sebagai proksi aktivitas ekonomi dalam riset pembangunan.

### Cara hitungnya

```
1. Bagi wilayah studi jadi grid 500 × 500 m
2. Tiap sel dapat:
     - rata-rata radiance VIIRS      → normalisasi 0–1
     - jumlah POI komersial (r=500m) → normalisasi 0–1
3. indeks_daya_beli = 0.4·nightlight + 0.4·poi + 0.2·pdrb_kota
4. Kalibrasi: rata-rata indeks per kota harus sejalan dengan
   peringkat PDRB per kapita antar kota dari BPS
```

Hasilnya: peta daya beli beresolusi 500 m, bukan satu angka untuk seluruh kota.

---

## Ringkasan Lisensi

| Sumber | Lisensi | Boleh komersial? | Wajib atribusi? |
|--------|---------|------------------|-----------------|
| OpenStreetMap | ODbL | ✅ | ✅ + share-alike |
| WorldPop | CC BY 4.0 | ✅ | ✅ |
| PetaBencana | CC BY 4.0 | ✅ | ✅ |
| VIIRS / NOAA | Public Domain | ✅ | Tidak wajib |
| GADM | Non-komersial | ❌ | ✅ |
| BPS | Terbuka | ✅ | ✅ |

> **Tulis atribusi di laporan akhir.** Ini bagian dari etika profesi yang dibahas di Sesi 1.

---

## Aturan Menyimpan Data

```
data/
├── raw/         # hasil download mentah — JANGAN diubah
├── processed/   # hasil olahan (sudah dibersihkan)
└── external/    # data dari sumber lain / input manual
```

⚠️ **Isi folder `data/` tidak di-commit ke Git** (lihat `.gitignore`). File geospasial terlalu besar.

Kalau perlu berbagi data olahan ke tim: pakai Google Drive, lalu **catat linknya di tabel bawah** supaya semua orang tahu.

### Data bersama tim

| Data | Link Drive | Diunggah oleh | Tanggal |
|------|-----------|---------------|---------|
| *(isi setelah ada)* | | | |
