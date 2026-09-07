# BanguninAja

**Sistem Pendukung Keputusan Penentuan Lokasi Berbasis GIS**

Menentukan lokasi paling ideal untuk mendirikan bangunan — hunian, rumah sakit, mall, atau tempat hiburan — berdasarkan kondisi geografis, demografis, dan risiko wilayah.

> Proyek AOL — **COMP6100001 Software Engineering**, Semester Ganjil 2026/2027
> Universitas Bina Nusantara

---

## Masalah

Developer properti menentukan lokasi berdasarkan **intuisi dan harga tanah murah**. Akibatnya: mall sepi, perumahan kebanjiran, rumah sakit menumpuk di satu area sementara wilayah lain tidak terlayani.

Data untuk memutuskan dengan benar sebenarnya **sudah tersedia dan terbuka** — hanya tersebar di banyak portal dan tidak pernah disatukan.

## Solusi

Satu mesin skoring, beberapa profil bangunan. Kriteria dan bobotnya berbeda per profil, mesinnya sama.

| Profil | Kriteria utama |
|--------|----------------|
| Hunian | Harga tanah, akses transport, sekolah, rawan banjir, keamanan |
| Rumah sakit | Kepadatan penduduk, faskes eksisting, akses jalan, luas lahan |
| Mall / retail | Daya beli, lalu lintas pejalan, kompetitor, parkir |
| Hiburan / F&B | Demografi usia, kompetitor, zonasi, akses malam |

> Pendekatan ini adalah **product-line software** — arsitektur dan komponen inti sama untuk beberapa varian produk.

---

## Fitur Utama

| # | Fitur | Ringkas |
|---|-------|---------|
| 1 | Manajemen data spasial | Import & validasi data peta, dengan versioning |
| 2 | Profil & bobot kriteria | User pilih jenis bangunan, atur bobot sendiri |
| 3 | Analisis & ranking lokasi | Skor tiap kandidat **beserta alasannya** |
| 4 | Cek zonasi & perizinan | Lokasi bagus tapi zonanya terlarang = percuma |
| 5 | Analisis kompetitor | Radius, kanibalisasi, celah pasar |
| 6 | Simulasi what-if | Bandingkan beberapa kandidat berdampingan |
| 7 | Laporan investasi | Estimasi biaya, proyeksi permintaan, ekspor PDF |

## Aktor

Developer/investor · Analis lokasi · Konsultan properti · Admin data · Pemda (validasi zonasi)

## SDG

- **SDG 11** — Sustainable Cities and Communities *(utama)*
- **SDG 8** — Decent Work and Economic Growth *(pendukung)*

---

## Ruang Lingkup

**Termasuk:** input & pengelolaan data spasial, analisis multi-kriteria, perankingan lokasi, pengecekan zonasi, visualisasi peta, laporan rekomendasi.

**Tidak termasuk:** proses jual-beli lahan, perizinan resmi (IMB/PBG), konstruksi, dan operasional bangunan.

---

## Struktur Folder

```
sitescope/
├── PANDUAN_DOWNLOAD.md  ← cara ambil datanya, langkah demi langkah
├── DATASETS.md          ← katalog sumber data + link & lisensi
├── data/
│   ├── raw/             hasil download mentah (tidak di-commit)
│   ├── processed/       hasil olahan
│   └── external/        input manual
├── docs/
│   ├── requirements/    SRS, user stories, use case
│   ├── uml/             use case, class, activity, sequence
│   └── architecture/    diagram & keputusan arsitektur
├── queries/             query Overpass siap pakai
├── scripts/             skrip pengambilan & pengolahan data
├── notebooks/           eksplorasi & analisis
└── reports/             laporan & bahan presentasi
```

---

## Mulai dari Mana

👉 **Ikuti [`PANDUAN_DOWNLOAD.md`](PANDUAN_DOWNLOAD.md)** — panduan langkah demi langkah beserta checklist tim.

Ringkasnya:
1. Pasang **QGIS** — [qgis.org/download](https://qgis.org/download/), pilih versi **LTR**
2. Ambil POI lewat [overpass-turbo.eu](https://overpass-turbo.eu/) — paling cepat, 5 menit
3. Lanjut ke WorldPop, InaRISK, dan API Key BPS

Daftar lengkap sumber data & lisensinya ada di [`DATASETS.md`](DATASETS.md).

---

## Cara Kerja Tim

### Aturan commit

```bash
git checkout -b nama/fitur      # kerja di branch sendiri
git add .
git commit -m "docs: tambah use case diagram"
git push -u origin nama/fitur   # lalu buka Pull Request
```

Jangan push langsung ke `main`.

### Format pesan commit

| Prefix | Untuk |
|--------|-------|
| `docs:` | dokumen, diagram, laporan |
| `data:` | skrip atau katalog data |
| `feat:` | fitur baru |
| `fix:` | perbaikan |
| `chore:` | rapi-rapi, konfigurasi |

### Aturan data

⚠️ **Jangan commit file di folder `data/`.** File geospasial ukurannya besar dan bikin repo berat.

Kalau perlu berbagi, upload ke Google Drive lalu catat linknya di tabel *"Data bersama tim"* di [`DATASETS.md`](DATASETS.md).

---

## Tim

| Nama | Peran | GitHub |
|------|-------|--------|
| Jonathan Andrew Saleh | | |
| | | |
| | | |
| | | |

*(lengkapi bersama tim)*

---

## Atribusi Data

Proyek ini menggunakan data terbuka dari OpenStreetMap (ODbL), WorldPop (CC BY 4.0), BNPB InaRISK, PetaBencana.id (CC BY 4.0), NOAA VIIRS (public domain), dan BPS. Rincian lengkap ada di [`DATASETS.md`](DATASETS.md).
