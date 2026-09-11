"""
BanguninAja — Pengintai API DEMNAS (sekali pakai, buat cari jalan)

DEMNAS (peta ketinggian 8 m dari BIG) hanya bisa diunduh setelah login.
Berkas ini BUKAN pengunduh, melainkan pengintai: tugasnya mencari alamat
mana yang mengembalikan DAFTAR TILE untuk sebuah wilayah, karena alamat
itu belum diketahui.

Token dibaca dari .env (DEMNAS_TOKEN) dan TIDAK PERNAH ditampilkan ke
layar. Token DEMNAS hanya berlaku sekitar satu jam.

CARA PAKAI (jalankan dari folder utama proyek):

  python scripts/intip_demnas.py
"""
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PANGKAL = "https://tanahair.indonesia.go.id"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"

# Kotak kecil di Jakarta Pusat, dipakai sebagai contoh pencarian.
CONTOH = {"barat": 106.80, "selatan": -6.21, "timur": 106.86, "utara": -6.15}


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
            "   Cara mengambil token ada di PANDUAN_DOWNLOAD.md.\n"
        )
    return token


def coba(sesi: requests.Session, jalur: str, params: dict | None = None,
         hanya_kepala: bool = False) -> None:
    """Panggil satu alamat, laporkan bentuk jawabannya secara ringkas."""
    url = f"{PANGKAL}/{jalur.lstrip('/')}"
    try:
        if hanya_kepala:
            r = sesi.head(url, params=params, timeout=45)
        else:
            r = sesi.get(url, params=params, timeout=45)
    except requests.RequestException as e:
        print(f"  [error ] {jalur}  {type(e).__name__}")
        return

    tipe = r.headers.get("content-type", "")[:40] or "(tanpa tipe)"
    print(f"  [{r.status_code:>3}   ] {jalur}  ({len(r.content):,} B, {tipe})")

    # Jawaban besar tanpa tipe JSON berarti berkasnya sendiri, bukan daftar.
    if len(r.content) > 100_000:
        print("           -> ini berkas TIF-nya langsung, bukan daftar tile")
        return

    if r.status_code != 200 or "json" not in tipe:
        if r.status_code != 404:
            # Isinya bisa biner; paksa jadi teks aman supaya tidak crash.
            cuplik = r.content[:150].decode("utf-8", errors="replace")
            print(f"           {cuplik}")
        return

    try:
        data = r.json()
    except json.JSONDecodeError:
        return

    # Tampilkan bentuk datanya saja, bukan isinya, supaya tidak membocorkan
    # apa pun yang bersifat pribadi.
    if isinstance(data, dict):
        print(f"           kunci: {list(data.keys())[:12]}")
        for k, v in data.items():
            if isinstance(v, list) and v:
                print(f"           '{k}' berisi {len(v)} item; "
                      f"contoh kunci: {list(v[0].keys())[:10] if isinstance(v[0], dict) else type(v[0]).__name__}")
    elif isinstance(data, list):
        print(f"           daftar {len(data)} item; "
              f"contoh kunci: {list(data[0].keys())[:10] if data and isinstance(data[0], dict) else '-'}")


def main() -> None:
    token = ambil_token()
    sesi = requests.Session()
    sesi.headers.update({
        "User-Agent": UA,
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    })

    print("Token terbaca (isinya tidak ditampilkan).\n")

    print("== 1. Alamat yang sudah diketahui ==")
    coba(sesi, "api-inageo/unduh/demnas", {"filename": "DEMNAS_1209-11_v1.0.tif"})
    coba(sesi, "api-inageo/unduh/demnas",
         {"token": token, "filename": "DEMNAS_1209-11_v1.0.tif"}, hanya_kepala=True)

    print("\n== 2. Tebakan alamat daftar tile ==")
    tebakan = [
        "api-inageo/demnas",
        "api-inageo/demnas/list",
        "api-inageo/demnas/tile",
        "api-inageo/unduh/demnas/list",
        "api-inageo/unduh/list",
        "api-inageo/unduh/demnas/nlp",
        "api-inageo/nlp",
        "api-inageo/nlp/demnas",
        "api-inageo/wilayah",
        "api-inageo/unduh/wilayah",
    ]
    for jalur in tebakan:
        coba(sesi, jalur)

    print("\n== 3. Tebakan dengan kotak wilayah ==")
    for jalur in ["api-inageo/demnas", "api-inageo/demnas/list", "api-inageo/nlp"]:
        coba(sesi, jalur, CONTOH)
        coba(sesi, jalur, {"bbox": f"{CONTOH['barat']},{CONTOH['selatan']},"
                                   f"{CONTOH['timur']},{CONTOH['utara']}"})

    print("\nSelesai. Cari baris berkode 200 yang isinya daftar tile.")


if __name__ == "__main__":
    main()
