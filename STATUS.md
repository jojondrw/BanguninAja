# STATUS — Di Mana Tiap Dataset Berada

> Catatan Jonathan, 2026-09-11. Berkas terpisah supaya tidak mengganggu
> `data/DATASET_TODO.md` yang dipelihara Derick.
>
> `DATASET_TODO.md` mencatat **apakah sebuah dataset sudah ditarik**.
> Berkas ini menjawab pertanyaan berbeda: **berkasnya ada di laptop siapa,
> dan apakah masih perlu dipindahkan.**
>
> Perlu ada berkas terpisah karena folder `data/` di-gitignore. Sebuah
> dataset bisa berstatus "Selesai" di tracker tapi tetap tidak ada di
> laptop orang lain, dan itu tidak terlihat dari tracker.

---

## Ringkasan

| | |
|---|---|
| Ada di laptop Jonathan | **19,2 GB** |
| Masih di laptop Derick saja | ~4 GB |
| Yang benar-benar perlu dipindahkan | **8 dataset, ~3,3 GB** |
| Sudah tidak perlu dipindahkan | 9 dataset — sudah digantikan yang lebih baik |

---

## 1. Ada di laptop Jonathan

Lokasi: `BanguninAja/data/raw/`

| # | Dataset | Status | Ukuran |
|---|---|---|---|
| 26 | **ZNT harga tanah** — 2.891.580 zona, rupiah asli per m² | ✅ Nasional | 7.245 MB |
| 27 | **InaRISK 12 layer bahaya** — nasional 250 m + DKI 100 m | ✅ Nasional | 7.121 MB |
| — | **OSM Indonesia mentah** (`.osm.pbf`) | ✅ Nasional | 1.656 MB |
| 9b | **DEMNAS 8 m** | 🟡 Baru 10 kota | 1.442 MB |
| 2 | WorldPop kepadatan penduduk *(ditarik Derick)* | ✅ Nasional | 1.016 MB |
| 6 | GADM batas wilayah 5 level *(ditarik Derick)* | ✅ Nasional | 404 MB |
| — | **Lahan terlarang / layak bangun / komersial** — 458.211 objek | ✅ Nasional | 295 MB |
| — | **Publikasi** — Buku RBI (BNPB) + Statistik Kriminal (BPS) | ✅ | 38 MB |
| 12 | **Kriminalitas BPS per provinsi** — 34 tabel | 🟡 19 dari 34 provinsi | ~90 MB |
| — | **PDRB & pengeluaran BPS** — 51 tabel | ✅ 27 provinsi | *(sama)* |
| 28 | **Kriminalitas Pusiknas 2026** — 38 Polda + Bareskrim | ✅ 39/39 satuan | 1 MB |

**Catatan DEMNAS.** Tidak akan pernah nasional: butuh ~150 GB sedangkan
disk tersisa ~104 GB, dan tokennya hanya berlaku 1 jam sedangkan
unduhannya ~12 jam. Lagipula petak analisis 92 m sudah lebih kasar
daripada Copernicus 30 m, jadi detail 8 m hilang dirata-ratakan. Dipakai
untuk tampilan detail satu kandidat terpilih.

---

## 2. Masih di laptop Derick — perlu dipindahkan

Tidak bisa lewat GitHub karena `data/` di-gitignore. Harus lewat harddisk
atau Google Drive.

### 2.1 Perlu — minta yang ini saja (~3,3 GB)

| # | Dataset | Dipakai untuk |
|---|---|---|
| 1 | **POI kompetitor** (72.328 titik) | Penilaian Kompetisi |
| 7 | **Jaringan jalan & rel/transit** (5,5 juta ruas) | Penilaian Aksesibilitas |
| 10 | **Hidrologi** sungai & badan air | Penilaian Kelayakan Fisik |
| 21 | **Kawasan hutan** | Penyaring keras |
| 9 | **Copernicus DEM 30 m** | Penilaian Kelayakan Fisik (kemiringan) |
| 13 | **IKK** biaya konstruksi, 514 kab/kota | Laporan Investasi |
| 17 | **BI SHPR** harga properti, 18 kota | Laporan Investasi |
| 23 | **Keterjangkauan faskes** | Penilaian Aksesibilitas, khusus profil rumah sakit |

### 2.2 Opsional — boleh menyusul

| # | Dataset | Alasan opsional |
|---|---|---|
| 15 | SoilGrids 6 properti tanah | Resolusi 250 m, jarang membedakan kandidat dalam satu kota. Untuk catatan laporan |
| 5, 5b | BPS penduduk & komuter | Level provinsi, tidak membedakan antar petak |

### 2.3 Tidak perlu dipindahkan

| # | Dataset | Alasan |
|---|---|---|
| 3, 3c–3k | 10 layer bencana versi ArcGIS | **Digantikan #27.** Milik Derick 1.247 m/piksel, versi baru 250 m — 5x lebih tajam |
| 3b-alt | Kawasan rawan gempa (BIG) | **Digantikan #27.** Poligon berkelas, sedangkan #27 memberi indeks kontinu 0–1 |
| 25 | Patahan aktif | Sudah tercermin di dalam indeks bahaya gempa — memakainya terpisah berarti menghitung dua kali |
| 8 | Utilitas OSM | Hanya 5.135 kabel se-Indonesia; ketiadaan data tak dapat dibedakan dari ketiadaan utilitas |
| 20 | Batas administrasi ATR/BPN | GADM sudah ada dan sudah dipakai sebagai kunci gabung |
| 24 | Kantor pertanahan | Tidak relevan untuk pemilihan lokasi |
| 22 | Tanah wakaf | Hanya 1 kota (Bekasi), dan di luar ruang lingkup |

---

## 3. Tidak ada di mana pun

| # | Dataset | Sebab | Bisa manual? |
|---|---|---|---|
| — | **RDTR + KDB/KLB** | `gistaru.atrbpn.go.id` membalas 404, daftar layanan ArcGIS-nya kosong | Bisa per kota dari PDF Perda, tapi petanya harus di-georeference manual |
| 16 | **Kriminalitas per kecamatan** | Lima jalur diuji tuntas, tidak satu pun bercakupan nasional seragam | Tidak — lihat catatan gap di `DATASET_TODO.md` |
| 14 | **Sertifikat tanah** | Diperiksa 2.173 tabel BPS di 5 kabupaten/kota, nol hasil | Di luar ruang lingkup |
| 18 | **Status hak atas tanah** | Data nasional **ada** (120.138.492 bidang, kueri per wilayah 0,16 detik) tapi tidak ditimbun: tidak muat, dan di luar ruang lingkup | Tersedia kapan saja per wilayah |

---

## 4. Yang perlu dilakukan

1. **Minta 8 dataset di bagian 2.1 dari Derick** (~3,3 GB). Jangan minta
   bagian 2.3 — sudah digantikan atau tidak terpakai menurut
   `docs/architecture/desain-data.md`.
2. **Cadangkan `data/` ke harddisk eksternal.** 19,2 GB ini tidak ada di
   GitHub dan tidak ada salinannya di mana pun. Skripnya bisa menarik
   ulang, tapi butuh berjam-jam dan DEMNAS perlu token baru.
3. **Tiga keputusan desain** menunggu kesepakatan tim — lihat bagian 1
   pada `docs/architecture/desain-data.md`.

---

## 5. Sebelum memakai datanya

Dua hal yang akan menjadi kejutan kalau tidak diketahui lebih dulu:

- **ZNT memuat nilai rusak.** Nilai maksimumnya 2.147.483.647, yaitu batas
  bilangan bulat 32-bit — bukan harga sungguhan. Saring dulu (misalnya
  buang di atas Rp 500 juta/m²). Sekitar 4% zona juga tidak punya nilai;
  perlakukan sebagai "tidak diketahui", bukan nol.
- **Lahan: 5 objek tanpa kategori** dari 458.211. Kemungkinan bertag ganda
  yang saling bertentangan. Abaikan baris yang `kategori IS NULL`.
