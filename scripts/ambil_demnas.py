"""
BanguninAja — Pengambil DEMNAS (peta ketinggian 8 m, BIG)

DEMNAS adalah model ketinggian resmi Indonesia beresolusi ~8 m, jauh lebih
halus daripada Copernicus 30 m. Bedanya: DEMNAS hanya bisa diunduh setelah
login, dan tokennya cuma berlaku sekitar satu jam.

TOKEN
  Disimpan di .env sebagai DEMNAS_TOKEN, tidak pernah ditampilkan ke layar
  dan tidak ikut ke GitHub. Cara mengambilnya ada di PANDUAN_DOWNLOAD.md.

PENOMORAN LEMBAR (hasil pembongkaran sendiri, 2026-09-10)
  Nama berkas: DEMNAS_{AABB}-{ab}_v1.0.tif

  Tiap berkas berisi satu petak 0,25 derajat x 0,25 derajat, 3333 x 3333
  piksel (~8,3 m per piksel).

  AABB = nomor lembar 1:250.000, yang luasnya 1,5 derajat bujur x 1 derajat
  lintang. Dua digit pertama menentukan bujur, dua digit terakhir lintang:

      bujur_barat_lembar  = 1,5 * AA + 88,5
      lintang_selatan_lembar = BB - 16

  ab = posisi petak di dalam lembar itu. Digit a (1-6) memilih blok
  0,5 x 0,5 derajat, digit b (1-4) memilih seperempatnya:

      a: blok, disusun 3 kolom x 2 baris, mulai dari barat daya
      b: kuadran, disusun 2 kolom x 2 baris, mulai dari barat daya

  Rumus ini sudah dicocokkan dengan 8 berkas contoh yang diunduh langsung
  (1109-11, 1209-11/12/13/21/41, 1210-11, 1309-11) dan semuanya tepat.

  Contoh: DKI Jakarta jatuh di lembar 1209, petak 41, 42, 43, dan 44.

CARA PAKAI (jalankan dari folder utama proyek):

  python scripts/ambil_demnas.py                  # wilayah studi (wilayah.py)
  python scripts/ambil_demnas.py --bbox 112.5 -7.4 112.8 -7.2 --nama surabaya
  python scripts/ambil_demnas.py --hanya-daftar   # lihat dulu, tanpa unduh

Berhenti di tengah jalan tidak masalah: berkas yang sudah ada dilewati.
Kalau tokennya kedaluwarsa, ambil token baru lalu jalankan lagi.
"""
import argparse
import math
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import wilayah

PANGKAL = "https://tanahair.indonesia.go.id"
UNDUH = f"{PANGKAL}/api-inageo/unduh/demnas"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"

SISI_PETAK = 0.25       # derajat, ukuran satu berkas DEMNAS
SISI_LEMBAR_X = 1.5     # derajat bujur per lembar 1:250.000
SISI_LEMBAR_Y = 1.0     # derajat lintang per lembar
PERCOBAAN = 3


def ambil_token() -> str:
    """Baca DEMNAS_TOKEN dari environment atau .env. Tidak pernah dicetak."""
    token = os.environ.get("DEMNAS_TOKEN")
    if not token:
        env = ROOT / ".env"
        if env.exists():
            for baris in env.read_text(encoding="utf-8").splitlines():
                baris = baris.strip()
                if baris.startswith("DEMNAS_TOKEN"):
                    token = baris.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not token or token.startswith("tempel_"):
        sys.exit(
            "DEMNAS_TOKEN belum diisi.\n\n"
            f"   Buka {ROOT / '.env'} lalu tambahkan satu baris:\n"
            "   DEMNAS_TOKEN=eyJ...\n\n"
            "   Cara mengambilnya ada di PANDUAN_DOWNLOAD.md.\n"
        )
    return token


def kode_petak(lon_barat: float, lat_selatan: float) -> str:
    """Ubah pojok barat-daya sebuah petak 0,25 derajat jadi kode DEMNAS."""
    lembar_lon = math.floor(lon_barat / SISI_LEMBAR_X) * SISI_LEMBAR_X
    lembar_lat = math.floor(lat_selatan / SISI_LEMBAR_Y) * SISI_LEMBAR_Y

    aa = round(lembar_lon / SISI_LEMBAR_X) - 59
    bb = round(lembar_lat) + 16

    dx = round((lon_barat - lembar_lon) / SISI_PETAK)   # 0..5
    dy = round((lat_selatan - lembar_lat) / SISI_PETAK)  # 0..3

    a = (dy // 2) * 3 + (dx // 2) + 1   # blok 0,5 derajat, 1..6
    b = (dy % 2) * 2 + (dx % 2) + 1     # kuadran 0,25 derajat, 1..4

    return f"{aa:02d}{bb:02d}-{a}{b}"


def petak_di_kotak(barat, selatan, timur, utara) -> list[tuple[str, float, float]]:
    """Daftar petak DEMNAS yang menyentuh sebuah kotak wilayah."""
    x0 = math.floor(barat / SISI_PETAK) * SISI_PETAK
    y0 = math.floor(selatan / SISI_PETAK) * SISI_PETAK

    hasil, y = [], y0
    while y < utara:
        x = x0
        while x < timur:
            hasil.append((kode_petak(x, y), round(x, 4), round(y, 4)))
            x += SISI_PETAK
        y += SISI_PETAK
    return hasil


def ada(sesi: requests.Session, token: str, nama: str) -> bool:
    """Cek keberadaan berkas tanpa mengunduhnya (HEAD, jadi murah)."""
    try:
        r = sesi.head(UNDUH, params={"token": token, "filename": nama}, timeout=60)
        return r.status_code == 200
    except requests.RequestException:
        return False


def unduh(sesi: requests.Session, token: str, nama: str, tujuan: Path) -> int:
    """Unduh satu berkas DEMNAS, kembalikan ukurannya dalam byte."""
    for percobaan in range(1, PERCOBAAN + 1):
        try:
            r = sesi.get(UNDUH, params={"token": token, "filename": nama},
                         timeout=600, stream=True)
            if r.status_code == 403:
                sys.exit(
                    "\nToken ditolak (403). Kemungkinan besar sudah kedaluwarsa —\n"
                    "   masa berlakunya cuma sekitar 1 jam.\n"
                    "   Ambil token baru, perbarui .env, lalu jalankan lagi.\n"
                    "   Berkas yang sudah terunduh tidak akan diulang.\n"
                )
            r.raise_for_status()
            sementara = tujuan.with_suffix(".sedang-diunduh")
            ukuran = 0
            with sementara.open("wb") as f:
                for bagian in r.iter_content(chunk_size=1 << 20):
                    f.write(bagian)
                    ukuran += len(bagian)
            # Baru dianggap selesai setelah utuh, supaya unduhan yang putus
            # tidak tertinggal sebagai berkas rusak yang dikira sudah beres.
            sementara.replace(tujuan)
            return ukuran
        except requests.RequestException as e:
            if percobaan == PERCOBAAN:
                raise
            time.sleep(percobaan * 5)
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Tarik DEMNAS 8 m dari BIG")
    p.add_argument("--bbox", nargs=4, type=float,
                   metavar=("BARAT", "SELATAN", "TIMUR", "UTARA"))
    p.add_argument("--nama", default=None, help="nama folder keluaran")
    p.add_argument("--hanya-daftar", action="store_true",
                   help="tampilkan daftar petak saja, tanpa mengunduh")
    args = p.parse_args()

    if args.bbox:
        kotak, nama = tuple(args.bbox), args.nama or "pilihan"
    else:
        kotak = (wilayah.BARAT, wilayah.SELATAN, wilayah.TIMUR, wilayah.UTARA)
        nama = args.nama or wilayah.KODE

    petak = petak_di_kotak(*kotak)
    tujuan = ROOT / "data" / "raw" / "demnas" / nama

    print(f"Wilayah : {nama}  {kotak}")
    print(f"Petak   : {len(petak)} x 0,25 derajat (~44 MB per petak, "
          f"~{len(petak) * 44 / 1024:.1f} GB total)")
    print(f"Tujuan  : {tujuan.relative_to(ROOT)}\n")

    for kode, x, y in petak:
        print(f"  DEMNAS_{kode}  ->  {x} s/d {round(x + SISI_PETAK, 2)} BT, "
              f"{y} s/d {round(y + SISI_PETAK, 2)} LS")

    if args.hanya_daftar:
        print("\n(hanya daftar, tidak ada yang diunduh)")
        return

    token = ambil_token()
    sesi = requests.Session()
    sesi.headers.update({"User-Agent": UA})
    tujuan.mkdir(parents=True, exist_ok=True)

    print()
    berhasil, dilewati, kosong, total_byte = 0, 0, 0, 0

    for i, (kode, _, _) in enumerate(petak, 1):
        berkas = f"DEMNAS_{kode}_v1.0.tif"
        keluar = tujuan / berkas

        if keluar.exists():
            print(f"[{i}/{len(petak)}] {berkas} -- sudah ada, dilewati")
            dilewati += 1
            total_byte += keluar.stat().st_size
            continue

        if not ada(sesi, token, berkas):
            # Petak yang seluruhnya laut memang tidak diterbitkan BIG.
            print(f"[{i}/{len(petak)}] {berkas} -- tidak tersedia (kemungkinan laut)")
            kosong += 1
            continue

        ukuran = unduh(sesi, token, berkas, keluar)
        total_byte += ukuran
        berhasil += 1
        print(f"[{i}/{len(petak)}] {berkas} -- {ukuran / 1024 / 1024:.1f} MB")

    print("\n=== SELESAI ===")
    print(f"Terunduh  : {berhasil}")
    print(f"Sudah ada : {dilewati}")
    print(f"Tak tersedia: {kosong}")
    print(f"Total      : {total_byte / 1024 / 1024:.0f} MB di "
          f"{tujuan.relative_to(ROOT)}")
    if berhasil or dilewati:
        print("\nGabung jadi satu berkas (opsional):")
        print(f"  gdalbuildvrt gabungan.vrt {tujuan.relative_to(ROOT)}/*.tif")


if __name__ == "__main__":
    main()
