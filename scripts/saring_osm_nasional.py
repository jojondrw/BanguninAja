"""
BanguninAja — Penyaring lahan dari file OSM Indonesia

Menghasilkan tiga lapisan nasional yang jadi dasar pemilihan kandidat:

  terlarang  wilayah yang HARUS dicoret (taman, sekolah, air, permukiman)
  layak      lahan yang tipe penggunaannya memang boleh dibangun
  komersial  bangunan niaga, untuk mode "sewa/beli unit"

Daftar tipenya disalin persis dari scripts/ambil_poi.py supaya definisi
versi nasional ini sama dengan versi DKI yang sudah ada.

SUMBER
  data/raw/osm_indonesia_2026.osm.pbf (Geofabrik, ~1,6 GB, terbuka)
  Diunduh dari https://download.geofabrik.de/asia/indonesia-latest.osm.pbf

CATATAN
  Sebuah objek bisa cocok di lebih dari satu kelompok. Urutannya:
  terlarang menang duluan. Lebih baik salah mencoret lahan bagus
  daripada salah menawarkan taman kota sebagai kandidat.

CARA PAKAI (jalankan dari folder utama proyek):

  python scripts/saring_osm_nasional.py
"""
import os
import subprocess
import sys
from pathlib import Path
from shutil import which

ROOT = Path(__file__).resolve().parent.parent
PBF = ROOT / "data" / "raw" / "osm_indonesia_2026.osm.pbf"
KELUAR = ROOT / "data" / "raw" / "lahan_indonesia.gpkg"

# Disalin dari KELOMPOK di scripts/ambil_poi.py
TERLARANG_LEISURE = ["park", "garden", "pitch"]
TERLARANG_LANDUSE = ["cemetery", "forest", "grass", "military", "residential"]
TERLARANG_AMENITY = ["school", "hospital", "place_of_worship"]
LAYAK_LANDUSE = ["brownfield", "greenfield", "construction", "commercial",
                 "retail", "industrial", "farmland", "meadow"]
KOMERSIAL_BUILDING = ["retail", "commercial", "office", "industrial", "warehouse"]


def daftar(nilai):
    return ", ".join(f"'{v}'" for v in nilai)


def cari_gdal_data() -> str | None:
    """
    Cari folder data GDAL (berisi osmconf.ini).

    Tanpa GDAL_DATA, driver OSM gagal dengan pesan
    "Could not parse configuration file for OSM import" — pesan yang
    menyesatkan, karena masalahnya bukan berkas OSM-nya melainkan
    konfigurasi GDAL yang tidak ketemu.
    """
    if os.environ.get("GDAL_DATA"):
        return os.environ["GDAL_DATA"]
    for kandidat in sorted(Path("C:/Program Files").glob("QGIS*"), reverse=True):
        for sub in ("apps/gdal/share/gdal", "share/gdal"):
            p = kandidat / sub
            if (p / "osmconf.ini").exists():
                return str(p)
    return None


def cari_ogr2ogr() -> str:
    if os.environ.get("GDAL_BIN"):
        p = Path(os.environ["GDAL_BIN"]) / "ogr2ogr.exe"
        if p.exists():
            return str(p)
    for kandidat in sorted(Path("C:/Program Files").glob("QGIS*"), reverse=True):
        p = kandidat / "bin" / "ogr2ogr.exe"
        if p.exists():
            return str(p)
    if which("ogr2ogr"):
        return which("ogr2ogr")
    sys.exit("GDAL tidak ketemu. Pasang QGIS dulu, atau set GDAL_BIN.")


# Satu kali baca berkas untuk ketiga kelompok sekaligus. Membaca ulang
# berkas 1,6 GB tiga kali jelas mubazir.
#
# Dialek SQL bawaan OGR tidak mengenal CASE WHEN, jadi di sini hanya
# menyaring barisnya. Kolom `kategori` diisi menyusul lewat SQLite biasa
# pada berkas GPKG hasilnya - lebih cepat dan tidak rewel.
SQL = f"""
SELECT osm_id, osm_way_id, name, landuse, leisure, "natural", amenity, building
FROM multipolygons
WHERE leisure IN ({daftar(TERLARANG_LEISURE)})
   OR landuse IN ({daftar(TERLARANG_LANDUSE + LAYAK_LANDUSE)})
   OR "natural" = 'water'
   OR amenity IN ({daftar(TERLARANG_AMENITY)})
   OR building IN ({daftar(KOMERSIAL_BUILDING)})
"""

# Urutan penting: terlarang menang duluan. Lebih baik salah mencoret lahan
# bagus daripada salah menawarkan taman kota sebagai kandidat.
ISI_KATEGORI = f"""
UPDATE lahan SET kategori =
  CASE
    WHEN leisure IN ({daftar(TERLARANG_LEISURE)})
      OR landuse IN ({daftar(TERLARANG_LANDUSE)})
      OR "natural" = 'water'
      OR amenity IN ({daftar(TERLARANG_AMENITY)})
    THEN 'terlarang'
    WHEN landuse IN ({daftar(LAYAK_LANDUSE)}) THEN 'layak'
    WHEN building IN ({daftar(KOMERSIAL_BUILDING)}) THEN 'komersial'
  END
"""


def main() -> None:
    if not PBF.exists():
        sys.exit(f"Berkas OSM belum ada: {PBF}")

    gb = PBF.stat().st_size / 1024 ** 3
    print(f"Sumber  : {PBF.relative_to(ROOT)}  ({gb:.2f} GB)")
    print(f"Keluaran: {KELUAR.relative_to(ROOT)}")
    print("Ini memakan waktu lama (berkasnya besar). Sabar.\n")

    ogr = cari_ogr2ogr()
    KELUAR.unlink(missing_ok=True)

    lingkungan = dict(os.environ)
    # Driver OSM butuh pembacaan berselang-seling, dan cache besar supaya
    # tidak bolak-balik ke disk.
    lingkungan["OGR_INTERLEAVED_READING"] = "YES"
    lingkungan["GDAL_CACHEMAX"] = "1024"
    lingkungan["OSM_MAX_TMPFILE_SIZE"] = "2048"

    gdal_data = cari_gdal_data()
    if not gdal_data:
        sys.exit("Folder data GDAL (osmconf.ini) tidak ketemu. Set GDAL_DATA manual.")
    lingkungan["GDAL_DATA"] = gdal_data
    print(f"GDAL_DATA: {gdal_data}")

    perintah = [
        ogr, "-f", "GPKG", str(KELUAR), str(PBF),
        "-sql", SQL.strip(),
        "-nln", "lahan",
        "-lco", "SPATIAL_INDEX=YES",
        "-progress",
    ]

    hasil = subprocess.run(perintah, env=lingkungan)
    if hasil.returncode != 0:
        sys.exit(f"\nogr2ogr gagal (kode {hasil.returncode}).")

    import sqlite3
    db = sqlite3.connect(KELUAR)
    # GPKG punya pemicu bawaan yang memanggil ST_IsEmpty, dan sqlite3
    # bawaan Python tidak mengenal fungsi itu. Jadi penulisannya lewat
    # ogrinfo, yang jalan di atas GDAL dan sudah punya fungsi spasialnya.
    print("Mengisi kolom kategori...")
    ogrinfo = ogr.replace("ogr2ogr", "ogrinfo")
    for perintah_sql in ("ALTER TABLE lahan ADD COLUMN kategori TEXT",
                         " ".join(ISI_KATEGORI.split()),
                         "CREATE INDEX idx_lahan_kategori ON lahan(kategori)"):
        r = subprocess.run([ogrinfo, str(KELUAR), "-sql", perintah_sql],
                           capture_output=True, text=True, env=lingkungan)
        if r.returncode != 0:
            sys.exit(f"gagal mengisi kategori: {(r.stderr or r.stdout)[:200]}")
    print("\n=== HASIL ===")
    total = 0
    for kategori, jumlah in db.execute(
            "SELECT kategori, COUNT(*) FROM lahan GROUP BY kategori ORDER BY 2 DESC"):
        print(f"  {kategori or '(tanpa kategori)':<12} {jumlah:>10,} objek")
        total += jumlah
    print(f"  {'TOTAL':<12} {total:>10,} objek")
    db.close()
    print(f"\nBerkas: {KELUAR.relative_to(ROOT)} "
          f"({KELUAR.stat().st_size / 1024**2:.0f} MB)")


if __name__ == "__main__":
    main()
