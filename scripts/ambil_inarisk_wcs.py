"""
BanguninAja — Pengambil indeks bahaya InaRISK lewat WCS GeoServer

LATAR BELAKANG (kenapa berkas ini ada, padahal sudah ada ambil_inarisk.py)

  scripts/ambil_inarisk.py memakai ArcGIS di gis.bnpb.go.id. Server itu
  rusak: exportImage balas 503 bahkan untuk gambar 64x64 piksel, dan
  layer gempa tidak bisa diambil sama sekali. Dicoba berkali-kali oleh
  dua orang, selalu gagal.

  Ternyata portal inarisk.bnpb.go.id sendiri TIDAK memakai server itu.
  Dia memakai GeoServer terpisah di inarisk1.bnpb.go.id. Ketahuan dari
  berkas javascripts/map-ol.js milik portalnya.

  GeoServer itu sehat, dan lewat WCS memberi tiga hal yang tidak bisa
  didapat dari ArcGIS:

    1. Layer gempa bisa diambil (yang tadinya dianggap mati total)
    2. Nilai asli Float32 rentang 0-1, bukan gambar berwarna
    3. Resolusi asli 100 m. Lewat ArcGIS, banjir terpaksa ditarik di
       1.247 m/piksel karena batas ukuran gambar per permintaan.

CATATAN TEKNIS

  Sumbu WCS layanan ini bernama "E" dan "N" dalam EPSG:3395 (World
  Mercator), bukan Long/Lat. Memakai Long/Lat ditolak dengan pesan
  "Invalid axis label provided: Long". Jadi kotak wilayah diubah dulu
  ke 3395 di dalam berkas ini.

CARA PAKAI (jalankan dari folder utama proyek):

  python scripts/ambil_inarisk_wcs.py --daftar
  python scripts/ambil_inarisk_wcs.py gempabumi
  python scripts/ambil_inarisk_wcs.py --semua
  python scripts/ambil_inarisk_wcs.py banjir --nasional --resolusi 500
  python scripts/ambil_inarisk_wcs.py gempabumi --bbox 112.5 -7.4 112.8 -7.2 --nama surabaya
"""
import argparse
import math
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import wilayah

WCS = "https://inarisk1.bnpb.go.id/geoserver/raster/wcs"
UA = "Mozilla/5.0 (kuliah COMP6100001 BanguninAja)"
PERCOBAAN = 3
RESOLUSI_ASLI = 100  # meter per piksel, bawaan InaRISK

NASIONAL = (94.9, -11.1, 141.1, 6.1)

# Nama pendek -> nama coverage di GeoServer. Nama pendek dipakai supaya
# perintahnya enak dibaca dan sama dengan istilah di DATASET_TODO.md.
LAYER = {
    "gempabumi": "INDEKS_BAHAYA_GEMPABUMI1",
    "banjir": "INDEKS_BAHAYA_BANJIR1",
    "banjir_bandang": "INDEKS_BAHAYA_BANJIRBANDANG1",
    "tsunami": "INDEKS_BAHAYA_TSUNAMI1",
    "longsor": "INDEKS_BAHAYA_TANAHLONGSOR1",
    "likuefaksi": "INDEKS_BAHAYA_LIKUEFAKSI1",
    "gunungapi": "INDEKS_BAHAYA_GUNUNGAPI1",
    "karhutla": "INDEKS_BAHAYA_KARHUTLA1",
    "kekeringan": "INDEKS_BAHAYA_KEKERINGAN1",
    "cuaca_ekstrim": "INDEKS_BAHAYA_CUACAEKSTRIM1",
    "gelombang_abrasi": "INDEKS_BAHAYA_GEA1",
    "multi": "INDEKS_BAHAYA_MULTI1",
}

R_BUMI = 6378137.0
E_BUMI = 0.0818191908426


def ke_3395(lon: float, lat: float) -> tuple[float, float]:
    """Ubah bujur/lintang jadi koordinat World Mercator (EPSG:3395)."""
    x = R_BUMI * math.radians(lon)
    lat_r = math.radians(lat)
    sin_lat = math.sin(lat_r)
    y = R_BUMI * math.log(
        math.tan(math.pi / 4 + lat_r / 2)
        * ((1 - E_BUMI * sin_lat) / (1 + E_BUMI * sin_lat)) ** (E_BUMI / 2)
    )
    return x, y


def daftar_coverage() -> list[str]:
    """Ambil daftar seluruh coverage yang tersedia di GeoServer."""
    r = requests.get(WCS, params={
        "service": "WCS", "version": "2.0.1", "request": "GetCapabilities",
    }, headers={"User-Agent": UA}, timeout=180)
    r.raise_for_status()
    return sorted(set(re.findall(r"raster__([A-Za-z0-9_]+)", r.text)))


def ambil(coverage: str, kotak, resolusi_m: float, tujuan: Path) -> tuple[bool, str]:
    """
    Unduh satu coverage untuk sebuah kotak wilayah.

    resolusi_m menentukan ukuran piksel yang diminta. 100 berarti
    resolusi asli; angka lebih besar dipakai untuk wilayah luas supaya
    berkasnya tidak meledak.
    """
    barat, selatan, timur, utara = kotak
    x0, y0 = ke_3395(barat, selatan)
    x1, y1 = ke_3395(timur, utara)

    params = {
        "service": "WCS",
        "version": "2.0.1",
        "request": "GetCoverage",
        "coverageId": f"raster__{coverage}",
        "subset": [f"E({x0:.0f},{x1:.0f})", f"N({y0:.0f},{y1:.0f})"],
        "format": "image/geotiff",
    }
    if resolusi_m and resolusi_m != RESOLUSI_ASLI:
        # Penskalaan HARUS lewat scalefactor. Dua cara lain sudah dicoba
        # dan ditolak server ini:
        #   scalesize=E(n),N(m)          -> "Scale Axis Undefined"
        #   scalesize sebagai dua param  -> ClassCastException
        params["scalefactor"] = f"{RESOLUSI_ASLI / resolusi_m:.6f}"

    for percobaan in range(1, PERCOBAAN + 1):
        try:
            r = requests.get(WCS, params=params, headers={"User-Agent": UA}, timeout=900)
            isi = r.content
            # Kegagalan dibalas sebagai XML, bukan kode HTTP error.
            if isi[:200].lstrip().startswith(b"<") and b"Coverage" not in isi[:200]:
                pesan = re.sub(rb"<[^>]*>", b" ", isi[:600]).decode("utf-8", "replace")
                return False, " ".join(pesan.split())[:160]
            tujuan.parent.mkdir(parents=True, exist_ok=True)
            # Tulis ke nama sementara dulu, baru diganti namanya. Kalau
            # proses mati di tengah penulisan, yang tertinggal berkas
            # sementara -- bukan berkas utuh palsu yang nanti dilewati
            # karena dikira sudah selesai.
            sementara = tujuan.with_suffix(".sedang-ditulis")
            sementara.write_bytes(isi)
            sementara.replace(tujuan)
            return True, f"{len(isi) / 1024 / 1024:.1f} MB"
        except requests.RequestException as e:
            if percobaan == PERCOBAAN:
                return False, f"{type(e).__name__}: {e}"
            time.sleep(percobaan * 5)
    return False, "gagal"


def main() -> None:
    p = argparse.ArgumentParser(description="Tarik indeks bahaya InaRISK lewat WCS")
    p.add_argument("layer", nargs="*", help=f"nama layer: {', '.join(LAYER)}")
    p.add_argument("--semua", action="store_true", help="tarik semua layer")
    p.add_argument("--daftar", action="store_true", help="tampilkan coverage yang tersedia")
    p.add_argument("--bbox", nargs=4, type=float,
                   metavar=("BARAT", "SELATAN", "TIMUR", "UTARA"))
    p.add_argument("--nasional", action="store_true")
    p.add_argument("--nama", default=None)
    p.add_argument("--resolusi", type=float, default=100,
                   help="ukuran piksel dalam meter (100 = resolusi asli)")
    args = p.parse_args()

    if args.daftar:
        semua = daftar_coverage()
        print(f"{len(semua)} coverage tersedia:\n")
        for c in semua:
            pendek = next((k for k, v in LAYER.items() if v == c), "")
            print(f"  {c:<36} {pendek}")
        return

    if args.nasional:
        kotak, nama = NASIONAL, args.nama or "indonesia"
    elif args.bbox:
        kotak, nama = tuple(args.bbox), args.nama or "pilihan"
    else:
        kotak = (wilayah.BARAT, wilayah.SELATAN, wilayah.TIMUR, wilayah.UTARA)
        nama = args.nama or wilayah.KODE

    pilihan = list(LAYER) if args.semua else args.layer
    if not pilihan:
        p.error("sebutkan nama layer, atau pakai --semua / --daftar")
    salah = [x for x in pilihan if x not in LAYER]
    if salah:
        p.error(f"layer tidak dikenal: {', '.join(salah)}\n   Pilihan: {', '.join(LAYER)}")

    tujuan = ROOT / "data" / "raw" / "inarisk_wcs"
    print(f"Wilayah  : {nama}  {kotak}")
    print(f"Resolusi : {args.resolusi:.0f} m")
    print(f"Layer    : {len(pilihan)}")
    print(f"Tujuan   : {tujuan.relative_to(ROOT)}\n")

    berhasil, gagal = 0, []
    for i, nama_pendek in enumerate(pilihan, 1):
        coverage = LAYER[nama_pendek]
        berkas = tujuan / f"inarisk_{nama_pendek}_{nama}.tif"
        if berkas.exists():
            print(f"[{i}/{len(pilihan)}] {nama_pendek:<18} sudah ada, dilewati")
            berhasil += 1
            continue
        mulai = time.time()
        ok, pesan = ambil(coverage, kotak, args.resolusi, berkas)
        lama = time.time() - mulai
        if ok:
            print(f"[{i}/{len(pilihan)}] {nama_pendek:<18} {pesan:>10}  ({lama:.0f} dtk)")
            berhasil += 1
        else:
            print(f"[{i}/{len(pilihan)}] {nama_pendek:<18} GAGAL: {pesan}")
            gagal.append(nama_pendek)

    print(f"\n=== SELESAI ===")
    print(f"Berhasil : {berhasil}/{len(pilihan)}")
    if gagal:
        print(f"Gagal    : {', '.join(gagal)}")


if __name__ == "__main__":
    main()
