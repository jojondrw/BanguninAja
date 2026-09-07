# Folder Data

⚠️ **Isi folder ini TIDAK di-commit ke Git.** File geospasial terlalu besar dan bikin repo berat.

Yang ikut ter-commit hanya file `README.md` dan `.gitkeep` ini.

## Pembagian folder

| Folder | Isinya | Boleh diubah? |
|--------|--------|---------------|
| `raw/` | Hasil download mentah, apa adanya | ❌ **Jangan pernah diedit** |
| `processed/` | Hasil olahan yang sudah dibersihkan | ✅ |
| `external/` | Input manual (misal data zonasi) | ✅ |

**Kenapa `raw/` tidak boleh diubah?** Supaya kalau ada yang salah di hasil olahan, kita bisa selalu balik ke sumber aslinya. Semua pengolahan harus lewat skrip di `scripts/`, bukan diedit tangan.

## Penamaan file

```
<sumber>_<wilayah>_<tahun>.<ext>

contoh:
osm_jaksel_2026.geojson
worldpop_idn_2020.tif
inarisk_banjir_dki_2026.geojson
bps_pdrb_jaksel_2025.csv
```

## Cara dapat datanya

Semua link download ada di [`../DATASETS.md`](../DATASETS.md).

## Berbagi ke tim

Upload ke Google Drive, lalu catat linknya di tabel **"Data bersama tim"** di [`../DATASETS.md`](../DATASETS.md) supaya semua orang tahu ada data apa saja.
