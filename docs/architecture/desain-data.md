# Desain Data BanguninAja

> Peran tiap dataset di dalam aplikasi: mana yang digabungkan, mana yang
> masuk model, dan yang tidak masuk model dipakai untuk apa.
>
> Disusun 2026-09-11, mengacu pada `README.md` (fitur & profil bangunan)
> dan `data/DATASET_TODO.md` (katalog & status dataset).

---

## 1. Tiga keputusan yang harus diambil lebih dulu

Desain di bawah ini menganggap tiga hal berikut sudah diputuskan. Kalau
jawabannya berbeda, sebagian besar desain ini berubah. Rekomendasi
disertakan beserta alasannya, tapi keputusannya ada di tim.

### 1.1 Mesin skoring: MCDM berbobot atau model prediktif?

Ada pertentangan langsung antara dua dokumen yang sama-sama sah:

| `README.md` menjanjikan | `DATASET_TODO.md` memutuskan |
|---|---|
| Fitur #2: user mengatur bobot sendiri | CNN multi-modal yang mempelajari bobotnya sendiri |
| Fitur #3: skor **beserta alasannya** | CNN sulit menjelaskan alasan per kandidat |

Keduanya tidak bisa berjalan bersamaan apa adanya.

**Rekomendasi: MCDM berbobot sebagai mesin utama.** Alasannya:

1. Dua fitur yang sudah dijanjikan di README hanya bisa dipenuhi MCDM.
2. Mata kuliahnya Software Engineering. Yang dinilai proses rekayasanya,
   bukan kebaruan modelnya.
3. Ada empat profil bangunan dengan kriteria berbeda. Model terlatih
   butuh banyak contoh **per profil**, sedangkan rumah sakit dan tempat
   hiburan jumlahnya sedikit.
4. MCDM bisa dijalankan hari ini dengan data yang sudah ada. Model
   terlatih butuh label yang belum ada (lihat 1.2).

Kalau tim tetap ingin ada unsur pembelajaran mesin, tempatkan sebagai
**pendapat kedua** yang ditampilkan berdampingan dengan skor MCDM —
bukan sebagai penentu peringkat.

### 1.2 Label presence-only

Rencana di `DATASET_TODO.md` adalah melatih model dengan label positif =
lokasi bisnis sejenis yang **sudah ada**.

**Rekomendasi: jangan dipakai untuk menjawab "lokasi ini bagus atau
tidak".** Model seperti itu belajar meniru pola sebaran yang sudah ada.
Padahal masalah yang dirumuskan README justru:

> "rumah sakit menumpuk di satu area sementara wilayah lain tidak terlayani"

Model presence-only akan merekomendasikan **lebih banyak penumpukan**,
yaitu kebalikan dari masalah yang hendak diselesaikan.

Kalau tetap ingin melatih sesuatu, latih untuk memprediksi **permintaan
yang belum terlayani** — misalnya jumlah penduduk per fasilitas terdekat.
Itu menjawab pertanyaan yang benar dan labelnya bisa dihitung dari data
yang sudah ada.

### 1.3 Fitur #4 "Cek zonasi & perizinan" tanpa RDTR

RDTR digital tidak tersedia: `gistaru.atrbpn.go.id` membalas 404 dan
daftar layanan ArcGIS-nya kosong. KDB/KLB menyatu di dalamnya, jadi ikut
tidak tersedia.

**Rekomendasi: turunkan cakupan fiturnya, jangan dicoret.** Rumuskan
ulang menjadi:

> Menyaring lahan yang jelas terlarang berdasarkan tipe penggunaan lahan
> resmi (taman, sekolah, badan air, permukiman, kuburan, kawasan hutan,
> kawasan militer). Verifikasi zonasi formal dan KDB/KLB tetap harus
> dilakukan pengguna lewat OSS, karena RDTR digital belum terbuka.

Lapisan lahan terlarang berisi 303.238 objek dan secara praktis sudah
mengerjakan sebagian besar tugas penyaringan itu.

---

## 2. Lima peran data

Tidak semua dataset berperan sama. Membedakan perannya penting, karena
menentukan kapan data dipakai dan apakah ia punya bobot.

```
  [1] PENYARING KERAS  ->  [2] PEMBENTUK KANDIDAT  ->  [3] KRITERIA SKOR
        (boleh/tidak)          (apa yang dinilai)       (seberapa bagus)
                                                              |
                                     [4] KENDALA PENGGUNA ----+
                                                              v
                                                    [5] BAHAN LAPORAN
```

**[1] Penyaring keras.** Menghapus kandidat sepenuhnya. Biner, tidak
punya bobot. Dijalankan paling awal supaya yang berikutnya lebih ringan.

**[2] Pembentuk kandidat.** Menentukan objek apa yang akan dinilai.

**[3] Kriteria skor.** Dinormalkan ke 0–1, lalu digabung memakai bobot
per profil bangunan. Inilah yang menghasilkan peringkat.

**[4] Kendala pengguna.** Input user (budget, luas minimum, toleransi
risiko) yang memotong kandidat setelah skor dihitung.

**[5] Bahan laporan.** Tidak ikut menentukan peringkat sama sekali,
tetapi mengisi fitur "Laporan Investasi" dan konteks peta.

---

## 3. Tabel lengkap: dataset dan perannya

| Dataset | Peran | Masuk skor? | Dipakai untuk apa |
|---|---|---|---|
| **Lahan terlarang** (303.238) | [1] Penyaring | Tidak | Mencoret taman, sekolah, air, permukiman, kuburan, militer |
| **Kawasan hutan** | [1] Penyaring | Tidak | Mencoret kawasan hutan yang ditetapkan secara hukum |
| **Lahan layak bangun** (106.467) | [2] Kandidat | Tidak | Isi kandidat mode "bangun baru" |
| **Bangunan komersial** (48.501) | [2] Kandidat | Tidak | Isi kandidat mode "sewa/beli unit" |
| **GADM / batas kecamatan** | [2] Kandidat | Tidak | Memotong wilayah, kunci gabung antar sumber |
| **InaRISK 12 layer** | [3] Kriteria | **Ya** | Dimensi Risiko Bencana (lihat 4.1) |
| **ZNT harga tanah** (2.891.580) | [3] + [4] | **Ya** | Dimensi Biaya Lahan, sekaligus penyaring budget |
| **WorldPop kepadatan** | [3] Kriteria | **Ya** | Dimensi Permintaan Pasar |
| **BPS PDRB & pengeluaran** | [3] Kriteria | **Ya** | Dimensi Permintaan Pasar (daya beli) |
| **POI kompetitor** (72.328) | [3] Kriteria | **Ya** | Dimensi Kompetisi |
| **Jaringan jalan & transit** | [3] Kriteria | **Ya** | Dimensi Aksesibilitas |
| **Keterjangkauan faskes** | [3] Kriteria | **Ya** | Dimensi Aksesibilitas, khusus profil rumah sakit |
| **Copernicus DEM 30 m** | [3] Kriteria | **Ya** | Dimensi Kelayakan Fisik (kemiringan lahan) |
| **Hidrologi sungai** | [3] Kriteria | **Ya** | Dimensi Kelayakan Fisik (jarak ke badan air) |
| **IKK biaya konstruksi** | [5] Laporan | Tidak | Estimasi biaya bangun per m² di laporan investasi |
| **BI SHPR harga properti** | [5] Laporan | Tidak | Tren pasar & daya serap di laporan investasi |
| **Kriminalitas** (Polda/provinsi) | [5] Laporan | Tidak | Catatan konteks — lihat 5.2 kenapa tidak diberi bobot |
| **SoilGrids** | [5] Laporan | Tidak | Catatan daya dukung tanah — lihat 5.3 |
| **Patahan aktif** | [5] Peta | Tidak | Tampilan peta saja — sudah tercakup layer gempa |
| **Utilitas OSM** | [5] Peta | Tidak | Tampilan peta saja — cakupannya terlalu bolong |
| **DEMNAS 8 m** | [5] Peta | Tidak | Visual detail untuk satu kandidat terpilih |
| **Buku RBI (BNPB)** | Dokumentasi | Tidak | Rujukan metodologi indeks bahaya di dokumen SE |
| **Status hak atas tanah** | — | Tidak | Di luar ruang lingkup (keputusan tim) |
| **Tanah wakaf** | — | Tidak | Cakupan hanya 1 kota, tidak dapat dipakai |

---

## 4. Penggabungan layer

Ini bagian "mana yang digabungin". Dua puluh lebih dataset tidak menjadi
dua puluh kriteria — kalau begitu bobot tiap kriteria menjadi terlalu
encer dan peringkatnya kabur. Semuanya diringkas jadi **enam dimensi**.

### 4.1 Dimensi Risiko Bencana — dari 12 layer InaRISK

Jangan dirata-ratakan datar. Bahaya di Indonesia sangat bergantung
lokasi: karhutla tidak relevan untuk mall di Jakarta, tsunami tidak
relevan untuk lahan di pedalaman Kalimantan.

**Aturannya dua lapis:**

1. **Bahaya inti** — selalu dihitung, relevan hampir di mana saja:
   `banjir`, `gempabumi`, `tanah longsor`
2. **Bahaya bersyarat** — hanya ikut dihitung kalau nilainya di lokasi
   tersebut di atas ambang (misalnya > 0,1): `tsunami`, `likuefaksi`,
   `gunungapi`, `karhutla`, `kekeringan`, `cuaca ekstrem`,
   `gelombang & abrasi`, `banjir bandang`

Layer `multi` **tidak dipakai** dalam perhitungan, karena isinya sudah
merupakan gabungan — memakainya bersama layer individual berarti
menghitung bahaya yang sama dua kali. Simpan untuk tampilan peta ikhtisar.

Skor akhir dimensi ini = 1 − (rata-rata terbobot bahaya yang aktif),
sehingga makin aman makin tinggi skornya.

### 4.2 Dimensi Permintaan Pasar

Gabungan dari: **WorldPop** (berapa banyak orang di sekitar) + **BPS
pengeluaran per kapita** (seberapa besar daya belinya) + **BPS penduduk
& komuter** (arus orang masuk-keluar wilayah).

Catatan kejujuran: WorldPop beresolusi ~100 m sehingga membedakan antar
petak, sedangkan data BPS hanya per provinsi atau kabupaten/kota sehingga
**tidak membedakan kandidat di dalam satu wilayah**. Jadi BPS berperan
sebagai pengali tingkat wilayah, bukan pembeda antar petak.

### 4.3 Dimensi Kompetisi

Dari **POI kompetitor**, dihitung dua angka: jumlah pesaing sejenis dalam
radius tertentu, dan jarak ke pesaing terdekat. Digabung menjadi satu
skor dengan peluruhan jarak.

Arah skor **berbeda per profil**, dan ini penting: untuk mall, pesaing
dekat itu buruk (kanibalisasi). Untuk F&B, pesaing dekat justru bisa baik
(efek kawasan kuliner). Jadi dimensi ini punya tanda yang dapat dibalik.

### 4.4 Dimensi Aksesibilitas

Gabungan **jaringan jalan** (jarak ke jalan utama, kepadatan jaringan),
**titik transit** (jarak ke stasiun/terminal), dan khusus profil rumah
sakit ditambah **keterjangkauan faskes**.

### 4.5 Dimensi Biaya Lahan

Dari **ZNT**, nilai rupiah per m² pada zona tempat kandidat berada.
Skornya dibalik: makin murah makin tinggi.

⚠️ **Wajib disaring dulu:** nilai maksimum di ZNT adalah 2.147.483.647,
yaitu batas bilangan bulat 32-bit — bukan harga sungguhan, melainkan
data rusak di sumber. Buang baris di atas ambang wajar (misalnya
Rp 500 juta/m²) sebelum dipakai. Sekitar 4% zona juga tidak punya nilai
sama sekali; perlakukan sebagai "tidak diketahui", jangan sebagai nol.

### 4.6 Dimensi Kelayakan Fisik

Gabungan **kemiringan lahan** (diturunkan dari Copernicus DEM) dan
**jarak ke badan air** (dari hidrologi). Lahan curam mahal untuk
dibangun; terlalu dekat sungai menambah risiko banjir dan pembatasan
sempadan.

---

## 5. Yang tidak masuk skoring — dan alasannya

Bagian ini menjawab "kalau ga semua layer bisa dipake buat model, sisa
yang ga bisa dipake buat apa".

### 5.1 Dipakai di Laporan Investasi (fitur #7)

| Dataset | Perannya di laporan |
|---|---|
| **IKK** | Mengubah luas bangunan rencana menjadi estimasi biaya konstruksi, disesuaikan tingkat kemahalan kota tersebut |
| **BI SHPR** | Tren harga properti dan daya serap pasar di kota itu, untuk proyeksi pendapatan |
| **ZNT** | Estimasi biaya akuisisi lahan (luas × rupiah per m²) |

Ketiganya menghasilkan angka **setelah** lokasi dipilih. Memasukkannya
sebagai kriteria peringkat akan menghitung biaya dua kali.

### 5.2 Kriminalitas — kenapa tidak diberi bobot

Data terbaik yang tersedia berhenti di level kabupaten/kota, dan untuk 15
provinsi bahkan tidak ada sama sekali. Artinya di dalam satu wilayah
pencarian, **semua kandidat mendapat angka keamanan yang sama persis**.

Kriteria yang bernilai sama untuk semua kandidat tidak mengubah urutan
sedikit pun, berapa pun bobotnya. Memberinya bobot hanya menciptakan
ilusi bahwa keamanan ikut diperhitungkan.

**Keputusan:** tampilkan sebagai catatan konteks pada laporan ("tingkat
kriminalitas provinsi ini berada di peringkat ke-N nasional"), bukan
sebagai komponen skor. Jika suatu saat tersedia data level kecamatan yang
seragam, dimensi ini bisa diaktifkan.

### 5.3 SoilGrids — kenapa ditunda

Resolusinya 250 m dan sifat tanah jarang berbeda tajam antar kandidat di
dalam satu kota. Daya dukung tanah sangat penting untuk desain pondasi,
tetapi itu pekerjaan teknik sipil **setelah** lokasi terpilih — di luar
ruang lingkup sistem ini.

**Keputusan:** tampilkan sebagai catatan pada laporan kandidat terpilih.

### 5.4 Patahan aktif dan utilitas

**Patahan aktif** sudah tercermin di dalam indeks bahaya gempa InaRISK.
Memakainya sebagai kriteria terpisah berarti menghitung faktor yang sama
dua kali. Dipakai untuk tampilan peta saja.

**Utilitas OSM** hanya berisi 5.135 kabel listrik untuk seluruh
Indonesia. Cakupan sejarang itu membuat ketiadaan data tidak dapat
dibedakan dari ketiadaan utilitas. Dipakai untuk tampilan peta saja.

### 5.5 DEMNAS 8 m

Petak analisis sistem ini 92 m, sedangkan Copernicus sudah 30 m — lebih
halus dari petaknya. Detail 8 m akan hilang dirata-ratakan begitu masuk
petak.

**Keputusan:** dipakai pada tampilan detail satu kandidat terpilih,
tempat resolusi tinggi memang terlihat gunanya. Tersedia untuk 10 kota.

---

## 6. Bobot bawaan per profil bangunan

Angka ini titik awal yang dapat diubah pengguna (fitur #2). Disusun
mengikuti "kriteria utama" tiap profil yang sudah tertulis di README.

| Dimensi | Hunian | Rumah Sakit | Mall / Retail | Hiburan / F&B |
|---|---:|---:|---:|---:|
| Biaya Lahan | **30%** | 15% | 20% | 15% |
| Risiko Bencana | **25%** | 20% | 10% | 10% |
| Permintaan Pasar | 15% | **30%** | **25%** | **25%** |
| Aksesibilitas | 15% | **25%** | **25%** | 20% |
| Kompetisi | 5% | 5% | 15% | **25%** |
| Kelayakan Fisik | 10% | 5% | 5% | 5% |

Perbedaan yang disengaja:

- **Hunian** menomorsatukan harga tanah dan risiko banjir, sesuai
  kriteria di README.
- **Rumah sakit** menomorsatukan kepadatan penduduk dan akses jalan —
  keterjangkauan layanan diperlakukan sebagai peluang, bukan kompetisi.
- **Mall** menekankan daya beli dan aksesibilitas; pesaing dekat dinilai
  merugikan.
- **F&B** memberi bobot kompetisi paling besar, dan tandanya dapat
  dibalik karena kedekatan dengan pesaing bisa menguntungkan.

---

## 7. Alur pemrosesan

```
User memilih: jenis bangunan, wilayah, luas minimum, budget, toleransi risiko

  1. Ambil batas wilayah dari GADM                        -> kotak pencarian
  2. Bangun petak 92 m HANYA untuk wilayah itu            -> ~1.800 petak/kecamatan
  3. Coret petak yang menyentuh lahan terlarang & hutan   -> penyaring keras
  4. Kumpulkan kandidat (lahan layak / bangunan komersial)
  5. Untuk tiap kandidat, hitung enam dimensi
  6. Gabungkan memakai bobot profil                       -> skor 0-100
  7. Buang kandidat yang melanggar kendala pengguna
  8. Urutkan, tampilkan dengan rincian per dimensi        -> fitur #3
```

Langkah 2 adalah alasan sistem ini dapat berskala nasional tanpa
menghitung seluruh Indonesia: petak dibuat sesuai permintaan. Seluruh
Indonesia pada petak 92 m berarti 224 juta petak — tidak mungkin. Satu
kecamatan hanya sekitar 1.800 petak.

---

## 8. Batasan yang diketahui

Ditulis terbuka supaya tidak ditemukan sebagai kejutan saat penilaian.

1. **Zonasi resmi tidak tersedia.** RDTR dan KDB/KLB terhalang di sisi
   ATR/BPN. Sistem menyaring lahan terlarang, tetapi tidak dapat
   memastikan kesesuaian zonasi formal.
2. **Kriminalitas terlalu kasar** untuk membedakan antar kandidat di
   dalam satu wilayah.
3. **Statistik BPS berhenti di provinsi atau kabupaten/kota.** Ia
   mengangkat atau menurunkan seluruh wilayah, bukan membedakan petak.
4. **ZNT memuat nilai rusak** yang wajib disaring, dan sekitar 4% zona
   tidak memiliki nilai.
5. **Data bahaya nasional beresolusi 250 m**, sedangkan petak analisis
   92 m. Untuk analisis tingkat petak, tarik ulang wilayah tersebut pada
   resolusi asli 100 m — perlu waktu belasan detik per wilayah.
6. **Sistem merekomendasikan area untuk diselidiki, bukan tanah yang
   bebas dibeli.** Kepemilikan, harga per bidang, dan status sertifikat
   berada di luar ruang lingkup.
