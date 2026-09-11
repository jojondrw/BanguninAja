"""
BanguninAja — Pengambil Zona Nilai Tanah (ZNT) ATR/BPN

ZNT adalah peta harga tanah resmi pemerintah: tiap poligon punya kolom
NILAI berisi rupiah per meter persegi. Ini pengganti sebenarnya untuk
indeks harga buatan sendiri di scripts/indeks_harga.py.

Sumber: GeoServer WFS publik ATR/BPN, layer petabpn:ZONANILAITANAH
(2.892.896 poligon, cakupan nasional).

Catatan teknis yang ditemukan saat mencoba:
  - CQL_FILTER pada kolom geometri BATAS selalu balas IOException
    (bug di sisi server). Penyaringan wilayah HARUS lewat parameter
    `bbox` bawaan WFS, bukan CQL.
  - Satu permintaan dibatasi 1000 fitur, jadi tiap petak di-paging
    dengan startIndex.
  - Skala nasional tidak muat di memori: DKI saja 120 ribu poligon =
    433 MB GeoJSON. Jadi tiap petak langsung ditulis ke GPKG lalu
    berkas sementaranya dibuang, bukan ditumpuk dulu di RAM.
  - Menyederhanakan bentuk poligon (toleransi ~6 m) memangkas ukuran
    55% tanpa mengurangi jumlah zona. Aman karena petak analisis kita
    92 m, jauh lebih kasar dari pergeseran 6 m itu.

CARA PAKAI (jalankan dari folder utama proyek):

  python scripts/ambil_znt.py                    # wilayah studi (wilayah.py)
  python scripts/ambil_znt.py --nasional         # seluruh Indonesia
  python scripts/ambil_znt.py --bbox 112.5 -7.4 112.8 -7.2 --nama surabaya

Berhenti di tengah jalan tidak masalah: jalankan lagi, petak yang sudah
selesai dilewati (dicatat di berkas _petak_selesai.txt).
"""
import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from shutil import which

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import wilayah

WFS = "https://atlas.atrbpn.go.id/geoserver/ows"
LAYER = "petabpn:ZONANILAITANAH"
UA = "Mozilla/5.0 (kuliah COMP6100001 BanguninAja)"

PER_HALAMAN = 1000       # batas server per permintaan
SISI_PETAK = 0.5         # derajat (~55 km)
SEDERHANAKAN = 0.00005   # ~6 m; pergeseran batas yang masih aman
PERCOBAAN = 4
JEDA = 0.2

NASIONAL = (94.9, -11.1, 141.1, 6.1)


def cari_ogr2ogr() -> str:
    """Temukan ogr2ogr, biasanya bawaan QGIS (sama seperti siapkan_data.py)."""
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
    sys.exit("GDAL tidak ketemu. Pasang QGIS dulu, atau set GDAL_BIN ke folder bin-nya.")


def petak_petak(barat, selatan, timur, utara, sisi):
    """Pecah satu kotak besar jadi daftar kotak kecil."""
    hasil, y = [], selatan
    while y < utara:
        x, y2 = barat, min(y + sisi, utara)
        while x < timur:
            x2 = min(x + sisi, timur)
            hasil.append((round(x, 4), round(y, 4), round(x2, 4), round(y2, 4)))
            x = x2
        y = y2
    return hasil


def minta(params: dict) -> dict:
    """Panggil WFS, ulangi kalau jaringannya yang bermasalah."""
    for percobaan in range(1, PERCOBAAN + 1):
        try:
            r = requests.get(WFS, params=params, headers={"User-Agent": UA}, timeout=180)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            if percobaan == PERCOBAAN:
                raise RuntimeError(f"gagal setelah {PERCOBAAN} percobaan: {e}") from e
            time.sleep(percobaan * 4)
    return {}


def ambil_petak(kotak):
    """
    Ambil zona di dalam satu petak, halaman demi halaman.

    Dikembalikan sebagai generator per halaman (bukan satu daftar penuh)
    supaya petak yang sangat padat tidak menumpuk di memori. Versi lama
    yang mengumpulkan sepetak sekaligus sempat memakai 3,3 GB RAM pada
    petak padat di Jawa Tengah.
    """
    barat, selatan, timur, utara = kotak
    # WFS 2.0 dengan CRS urn memakai urutan lintang,bujur.
    bbox = f"{selatan},{barat},{utara},{timur},urn:ogc:def:crs:EPSG::4326"
    mulai = 0
    while True:
        data = minta({
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": LAYER,
            "outputFormat": "application/json",
            "count": PER_HALAMAN,
            "startIndex": mulai,
            "bbox": bbox,
        })
        halaman = data.get("features", [])
        if halaman:
            yield halaman
        if len(halaman) < PER_HALAMAN:
            return
        mulai += PER_HALAMAN
        time.sleep(JEDA)


def tulis_ke_gpkg(ogr: str, fitur: list, gpkg: Path, sementara: Path, tol: float) -> None:
    """Tuang satu petak ke GPKG, lalu buang berkas sementaranya."""
    sementara.write_text(json.dumps({
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
        "features": fitur,
    }), encoding="utf-8")

    perintah = [ogr, "-f", "GPKG", str(gpkg), str(sementara), "-nln", "znt"]
    if gpkg.exists():
        perintah += ["-append"]
    else:
        perintah += ["-lco", "SPATIAL_INDEX=YES"]
    if tol > 0:
        perintah += ["-simplify", str(tol)]

    hasil = subprocess.run(perintah, capture_output=True, text=True)
    sementara.unlink(missing_ok=True)
    if hasil.returncode != 0:
        raise RuntimeError(f"ogr2ogr gagal: {hasil.stderr.strip()[:200]}")


def buang_kembar(gpkg: Path) -> tuple[int, int]:
    """Petak bersebelahan bisa mengembalikan zona yang sama. Sisakan satu."""
    db = sqlite3.connect(gpkg)
    sebelum = db.execute("SELECT COUNT(*) FROM znt").fetchone()[0]
    db.execute(
        "DELETE FROM znt WHERE rowid NOT IN "
        "(SELECT MIN(rowid) FROM znt GROUP BY ZONANILAITANAHID)"
    )
    db.commit()
    sesudah = db.execute("SELECT COUNT(*) FROM znt").fetchone()[0]
    db.close()
    return sebelum, sesudah


def ringkas(gpkg: Path) -> None:
    """Tampilkan sebaran harga supaya kewajarannya langsung kelihatan."""
    db = sqlite3.connect(gpkg)
    n = db.execute("SELECT COUNT(*) FROM znt WHERE NILAI > 0").fetchone()[0]
    if not n:
        db.close()
        return
    titik = {}
    for label, q in (("p25", 0.25), ("tengah", 0.5), ("p75", 0.75)):
        titik[label] = db.execute(
            "SELECT NILAI FROM znt WHERE NILAI > 0 ORDER BY NILAI LIMIT 1 OFFSET ?",
            (int(q * n),),
        ).fetchone()[0]
    lo, hi = db.execute("SELECT MIN(NILAI), MAX(NILAI) FROM znt WHERE NILAI > 0").fetchone()
    db.close()
    print(f"Rp/m2     : min {lo:,} | p25 {titik['p25']:,} | "
          f"tengah {titik['tengah']:,} | p75 {titik['p75']:,} | maks {hi:,}")


def main() -> None:
    p = argparse.ArgumentParser(description="Tarik Zona Nilai Tanah ATR/BPN")
    p.add_argument("--bbox", nargs=4, type=float,
                   metavar=("BARAT", "SELATAN", "TIMUR", "UTARA"))
    p.add_argument("--nasional", action="store_true", help="seluruh Indonesia")
    p.add_argument("--nama", default=None, help="nama untuk berkas keluaran")
    p.add_argument("--sisi", type=float, default=SISI_PETAK, help="sisi petak (derajat)")
    p.add_argument("--sederhanakan", type=float, default=SEDERHANAKAN,
                   help="toleransi penyederhanaan bentuk, 0 = matikan")
    args = p.parse_args()

    if args.nasional:
        kotak_besar, nama = NASIONAL, args.nama or "indonesia"
    elif args.bbox:
        kotak_besar, nama = tuple(args.bbox), args.nama or "pilihan"
    else:
        kotak_besar = (wilayah.BARAT, wilayah.SELATAN, wilayah.TIMUR, wilayah.UTARA)
        nama = args.nama or wilayah.KODE

    ogr = cari_ogr2ogr()
    petak = petak_petak(*kotak_besar, sisi=args.sisi)
    gpkg = ROOT / "data" / "raw" / f"znt_atrbpn_{nama}.gpkg"
    kerja = ROOT / "data" / "raw" / f"_znt_{nama}_kerja"
    kerja.mkdir(parents=True, exist_ok=True)
    catatan = kerja / "_petak_selesai.txt"

    selesai = set()
    if catatan.exists():
        selesai = set(catatan.read_text(encoding="utf-8").split())

    print(f"Wilayah : {nama}  {kotak_besar}")
    print(f"Petak   : {len(petak)} (sisi {args.sisi} derajat), {len(selesai)} sudah selesai")
    print(f"Keluaran: {gpkg.relative_to(ROOT)}")
    print(f"Sederhanakan: {args.sederhanakan} (~{round(args.sederhanakan * 111320)} m)\n")

    total, kosong, gagal = 0, 0, []
    mulai = time.time()

    for i, kotak in enumerate(petak, 1):
        kunci = f"{kotak[0]}_{kotak[1]}"
        if kunci in selesai:
            continue

        # Tiap halaman langsung dituang ke GPKG, jadi yang ditahan di memori
        # paling banyak 1000 poligon, bukan sepetak penuh.
        di_petak = 0
        try:
            for n, halaman in enumerate(ambil_petak(kotak)):
                tulis_ke_gpkg(ogr, halaman, gpkg,
                              kerja / f"{kunci}_h{n}.json", args.sederhanakan)
                di_petak += len(halaman)
        except Exception as e:
            print(f"[{i}/{len(petak)}] {kotak} GAGAL: {e}", flush=True)
            gagal.append((kotak, str(e)))
            continue

        if di_petak:
            total += di_petak
            lewat = time.time() - mulai
            print(f"[{i}/{len(petak)}] {kotak} -- {di_petak:,} zona "
                  f"(total {total:,}, {lewat/60:.0f} mnt)", flush=True)
        else:
            kosong += 1

        with catatan.open("a", encoding="utf-8") as f:
            f.write(kunci + "\n")

    print("\n=== SELESAI ===")
    print(f"Petak berisi data : {len(petak) - kosong - len(gagal)}")
    print(f"Petak kosong (laut/hutan): {kosong}")
    if gagal:
        print(f"Petak gagal       : {len(gagal)} -- jalankan ulang untuk mencoba lagi")

    if gpkg.exists():
        sebelum, sesudah = buang_kembar(gpkg)
        gb = gpkg.stat().st_size / 1024 ** 3
        print(f"Zona (sebelum saring kembar): {sebelum:,}")
        print(f"Zona unik         : {sesudah:,}")
        print(f"Berkas            : {gpkg.relative_to(ROOT)}  ({gb:.2f} GB)")
        ringkas(gpkg)


if __name__ == "__main__":
    main()
