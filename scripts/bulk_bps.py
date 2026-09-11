"""
BanguninAja — Borongan tabel BPS per provinsi

Muter ke 34 provinsi, cari tabel statis yang judulnya mengandung kata kunci,
lalu simpan yang cocok jadi CSV di data/raw/.

Generalisasi dari scripts/bulk_kriminalitas.py (kata kuncinya dulu dikunci di
dalam kode) supaya satu skrip ini bisa dipakai untuk tema apa pun.

CARA PAKAI (jalankan dari folder utama proyek):

  python scripts/bulk_bps.py sertifikat
  python scripts/bulk_bps.py pdrb pengeluaran --maks 2
  python scripts/bulk_bps.py kejahatan kriminal keamanan --label kriminalitas

Argumen:
  <kata...>   satu atau lebih kata kunci judul tabel (dicek berurutan)
  --maks N    ambil paling banyak N tabel per provinsi (default 1)
  --label X   nama tema untuk ringkasan & berkas log (default: kata pertama)
"""
import argparse
import sys
import time
from pathlib import Path

ROOT_SKRIP = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_SKRIP))

import requests

from bps import panggil, isi_daftar, cmd_ambil, ROOT

PROVINSI = {
    "1100": "Aceh", "1200": "Sumatera Utara", "1300": "Sumatera Barat", "1400": "Riau",
    "1500": "Jambi", "1600": "Sumatera Selatan", "1700": "Bengkulu", "1800": "Lampung",
    "1900": "Kep. Bangka Belitung", "2100": "Kep. Riau", "3100": "Dki Jakarta",
    "3200": "Jawa Barat", "3300": "Jawa Tengah", "3400": "Di Yogyakarta", "3500": "Jawa Timur",
    "3600": "Banten", "5100": "Bali", "5200": "Nusa Tenggara Barat", "5300": "Nusa Tenggara Timur",
    "6100": "Kalimantan Barat", "6200": "Kalimantan Tengah", "6300": "Kalimantan Selatan",
    "6400": "Kalimantan Timur", "6500": "Kalimantan Utara", "7100": "Sulawesi Utara",
    "7200": "Sulawesi Tengah", "7300": "Sulawesi Selatan", "7400": "Sulawesi Tenggara",
    "7500": "Gorontalo", "7600": "Sulawesi Barat", "8100": "Maluku", "8200": "Maluku Utara",
    "9100": "Papua Barat", "9400": "Papua",
}

# BPS sempat mem-blokir IP kalau permintaannya terlalu rapat, jadi tiap
# kegagalan jaringan dicoba ulang beberapa kali dengan jeda yang menaik.
PERCOBAAN = 3
MAKS_HALAMAN = 100  # 100 x 10 tabel = cukup untuk provinsi terbesar
JEDA_ANTAR_PROVINSI = 0.8


def daftar_tabel(domain: str) -> list:
    """Kumpulkan semua tabel statis di satu provinsi (semua halaman)."""
    semua, halaman = [], 1
    while True:
        data = panggil(f"list/model/statictable/lang/ind/domain/{domain}/page/{halaman}")
        isi = isi_daftar(data)
        if not isi:
            break
        semua.extend(isi)
        info = data.get("data", [{}])[0] if isinstance(data.get("data"), list) else {}
        total = info.get("pages") or info.get("total_page") or 1
        # Batas 20 halaman di skrip lama memotong daftar di 200 tabel, padahal
        # satu provinsi bisa punya 485 tabel. Batasnya dinaikkan ke MAKS_HALAMAN
        # supaya seluruh daftar kebaca.
        if halaman >= int(total) or halaman >= MAKS_HALAMAN:
            break
        halaman += 1
    return semua


def cari_tabel(domain: str, kata_kunci: list[str], maks: int) -> list:
    """Ambil sampai `maks` tabel yang judulnya cocok, kata kunci diprioritaskan urut."""
    semua = daftar_tabel(domain)
    terpilih, sudah = [], set()

    for kata in kata_kunci:
        for t in semua:
            if len(terpilih) >= maks:
                return terpilih
            tid = t.get("table_id")
            if tid in sudah:
                continue
            if kata in str(t.get("title", "")).lower():
                terpilih.append(t)
                sudah.add(tid)
    return terpilih


def coba_ulang(fungsi, *args):
    """Jalankan fungsi, ulangi kalau yang gagal jaringannya (bukan datanya)."""
    for percobaan in range(1, PERCOBAAN + 1):
        try:
            return fungsi(*args)
        except requests.RequestException as e:
            if percobaan == PERCOBAAN:
                raise
            jeda = percobaan * 5
            print(f"  jaringan bermasalah ({e}), coba lagi {jeda} detik lagi...")
            time.sleep(jeda)


def main() -> None:
    p = argparse.ArgumentParser(description="Borongan tabel BPS per provinsi")
    p.add_argument("kata", nargs="+", help="kata kunci judul tabel")
    p.add_argument("--maks", type=int, default=1, help="maks tabel per provinsi")
    p.add_argument("--label", default=None, help="nama tema untuk ringkasan")
    args = p.parse_args()

    kata_kunci = [k.lower() for k in args.kata]
    label = args.label or kata_kunci[0]

    print(f"Tema     : {label}")
    print(f"Kata kunci: {', '.join(kata_kunci)}")
    print(f"Maks per provinsi: {args.maks}\n")

    berhasil, kosong, gagal = [], [], []

    for kode, nama in PROVINSI.items():
        print(f"=== {kode} {nama} ===")
        try:
            tabel = coba_ulang(cari_tabel, kode, kata_kunci, args.maks)
        except Exception as e:
            print(f"  ERROR saat mencari: {e}")
            gagal.append((kode, nama, f"cari: {e}"))
            time.sleep(JEDA_ANTAR_PROVINSI)
            continue

        if not tabel:
            print("  (tidak ada tabel yang cocok)")
            kosong.append((kode, nama))
            time.sleep(JEDA_ANTAR_PROVINSI)
            continue

        for t in tabel:
            table_id, judul = t.get("table_id"), t.get("title")
            print(f"  ditemukan: [{table_id}] {judul}")
            try:
                coba_ulang(cmd_ambil, kode, str(table_id))
                berhasil.append((kode, nama, table_id, judul))
            except SystemExit as e:
                print(f"  GAGAL: {e}")
                gagal.append((kode, nama, f"[{table_id}] {e}"))
            except Exception as e:
                print(f"  ERROR: {e}")
                gagal.append((kode, nama, f"[{table_id}] {e}"))
        time.sleep(JEDA_ANTAR_PROVINSI)

    print(f"\n=== RINGKASAN [{label}] ===")
    print(f"Berhasil ditarik : {len(berhasil)} tabel")
    print(f"Provinsi kosong  : {len(kosong)}/{len(PROVINSI)}")
    print(f"Provinsi gagal   : {len(gagal)}")

    if kosong:
        print("\nTidak punya tabel dengan kata kunci ini:")
        print("  " + ", ".join(n for _, n in kosong))
    if gagal:
        print("\nGagal:")
        for kode, nama, alasan in gagal:
            print(f"  {kode} {nama}: {alasan}")

    log = ROOT / "data" / "raw" / f"_log_bulk_{label}.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    baris = [f"tema: {label}", f"kata kunci: {', '.join(kata_kunci)}", ""]
    baris += [f"OK    {k} {n} [{i}] {j}" for k, n, i, j in berhasil]
    baris += [f"KOSONG {k} {n}" for k, n in kosong]
    baris += [f"GAGAL {k} {n}: {a}" for k, n, a in gagal]
    log.write_text("\n".join(baris), encoding="utf-8")
    print(f"\nLog: {log.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
