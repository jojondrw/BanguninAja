"""
BanguninAja — Menyiapkan data mentah jadi siap pakai

Mengubah data nasional yang besar jadi potongan wilayah studi:

  data/raw/gadm/gadm41_IDN_3.shp  →  data/processed/<kode>_kecamatan_bersih.gpkg
  data/raw/worldpop_idn_2020.tif  →  data/processed/worldpop_<kode>_2020.tif

Wilayah studinya diatur di wilayah.py.

CARA PAKAI (dari folder utama proyek):

    python scripts/siapkan_data.py

Butuh QGIS terpasang (dipakai GDAL-nya). Kalau QGIS ada di lokasi lain,
set dulu:  set GDAL_BIN=D:\\QGIS\\bin
"""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wilayah as w

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"


def cari_gdal() -> Path:
    """Temukan folder bin GDAL, biasanya bawaan QGIS."""
    if os.environ.get("GDAL_BIN"):
        p = Path(os.environ["GDAL_BIN"])
        if (p / "ogr2ogr.exe").exists() or (p / "ogr2ogr").exists():
            return p

    for pola in ("C:/Program Files/QGIS *", "C:/Program Files/QGIS*/bin"):
        for kandidat in sorted(Path("C:/Program Files").glob("QGIS*"), reverse=True):
            b = kandidat / "bin"
            if (b / "ogr2ogr.exe").exists():
                return b

    # Linux/Mac: andalkan PATH
    from shutil import which
    if which("ogr2ogr"):
        return Path(which("ogr2ogr")).parent

    sys.exit(
        "❌ GDAL tidak ketemu.\n"
        "   Pasang QGIS dulu, atau set GDAL_BIN ke folder bin-nya."
    )


BIN = cari_gdal()


def jalankan(exe: str, *args: str) -> None:
    """Jalankan perintah GDAL, sembunyikan peringatan yang tidak penting."""
    path = BIN / exe
    if not path.exists():
        path = BIN / f"{exe}.exe"

    hasil = subprocess.run(
        [str(path), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if hasil.returncode != 0:
        print(hasil.stdout)
        print(hasil.stderr)
        sys.exit(f"❌ {exe} gagal.")


def sql_ejaan() -> str:
    """Bangun ekspresi CASE untuk menyeragamkan ejaan nama kecamatan."""
    baris = "\n".join(
        f"    WHEN NAME_3 = '{asli}' THEN '{benar}'" for asli, benar in w.EJAAN.items()
    )
    return f"CASE\n{baris}\n    ELSE UPPER(NAME_3) END"


def olah_batas() -> None:
    sumber = RAW / "gadm" / "gadm41_IDN_3.shp"
    if not sumber.exists():
        print(f"⏭️  Lewati batas wilayah — {sumber.relative_to(ROOT)} belum ada.")
        return

    antara = OUT / "_batas_sementara.gpkg"
    hasil = OUT / f"{w.KODE}_kecamatan_bersih.gpkg"

    for f in (antara, hasil):
        f.unlink(missing_ok=True)

    # Tahap 1: ambil kecamatan di kota yang dipilih saja.
    jalankan(
        "ogr2ogr", "-f", "GPKG", str(antara), str(sumber),
        "-where", w.where_kota(),
        "-nln", "kecamatan", "-nlt", "MULTIPOLYGON",
    )

    # Tahap 2: seragamkan ejaan, lalu gabungkan poligon bernama sama.
    jalankan(
        "ogr2ogr", "-f", "GPKG", str(hasil), str(antara),
        "-dialect", "SQLITE", "-nln", "kecamatan", "-nlt", "MULTIPOLYGON",
        "-sql",
        f"SELECT {sql_ejaan()} AS kecamatan, ST_Union(geom) AS geom "
        f"FROM kecamatan GROUP BY 1",
    )

    antara.unlink(missing_ok=True)
    print(f"✅ {hasil.relative_to(ROOT)}")


def olah_penduduk() -> None:
    sumber = RAW / "worldpop_idn_2020.tif"
    if not sumber.exists():
        print(f"⏭️  Lewati penduduk — {sumber.relative_to(ROOT)} belum ada.")
        return

    hasil = OUT / f"worldpop_{w.KODE}_2020.tif"
    hasil.unlink(missing_ok=True)

    jalankan(
        "gdal_translate",
        "-projwin", *w.projwin(),
        "-co", "COMPRESS=DEFLATE",
        str(sumber), str(hasil),
    )

    kecil = hasil.stat().st_size / 1048576
    besar = sumber.stat().st_size / 1048576
    print(f"✅ {hasil.relative_to(ROOT)}  ({besar:.0f} MB → {kecil:.1f} MB)")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"GDAL: {BIN}")
    print(f"Wilayah studi: {w.NAMA} ({len(w.KOTA)} kota)\n")

    olah_batas()
    olah_penduduk()

    print("\nSelesai. Hasilnya ada di data/processed/")


if __name__ == "__main__":
    main()
