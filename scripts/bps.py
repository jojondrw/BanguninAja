"""
BanguninAja — Pengambil data BPS lewat WebAPI

CARA PAKAI (jalankan dari folder utama proyek):

  1. Cari kode wilayah:
     python scripts/bps.py wilayah jakarta

  2. Cari tabel di wilayah itu:
     python scripts/bps.py cari 3171 penduduk

  3. Ambil tabelnya jadi CSV:
     python scripts/bps.py ambil 3171 <table_id>

API Key dibaca dari file .env di folder utama:
     BPS_API_KEY=key_kamu_disini
"""

import csv
import json
import os
import sys
from pathlib import Path
from html import unescape

import requests

BASE = "https://webapi.bps.go.id/v1/api"
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "raw"


def ambil_key() -> str:
    """Baca BPS_API_KEY dari environment atau file .env."""
    key = os.environ.get("BPS_API_KEY")
    if key:
        return key.strip()

    env = ROOT / ".env"
    if env.exists():
        for baris in env.read_text(encoding="utf-8").splitlines():
            baris = baris.strip()
            if baris.startswith("BPS_API_KEY"):
                return baris.split("=", 1)[1].strip().strip('"').strip("'")

    sys.exit(
        "❌ API Key belum ada.\n\n"
        f"   Bikin file .env di {ROOT}\n"
        "   Isinya satu baris:\n\n"
        "   BPS_API_KEY=key_kamu_disini\n"
    )


def panggil(path: str) -> dict:
    """Panggil endpoint BPS, kembalikan JSON."""
    url = f"{BASE}/{path}/key/{ambil_key()}/"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json()

    status = str(data.get("status", "")).upper()
    if status != "OK":
        pesan = data.get("message") or data.get("data-availability") or data
        sys.exit(f"❌ BPS menolak permintaan: {pesan}\n   URL: {url}")
    return data


def isi_daftar(data: dict) -> list:
    """
    Respons BPS berbentuk {"data": [ {info halaman}, [ ...isi... ] ]}.
    Fungsi ini mengambil bagian isinya saja.
    """
    d = data.get("data")
    if isinstance(d, list) and len(d) >= 2 and isinstance(d[1], list):
        return d[1]
    if isinstance(d, list):
        return [x for x in d if isinstance(x, dict)]
    return []


# ---------------------------------------------------------------- perintah


def cmd_wilayah(kata: str = "") -> None:
    """Tampilkan kode wilayah (domain) yang cocok dengan kata kunci."""
    hasil = isi_daftar(panggil("domain/type/all"))
    kata = kata.lower()

    cocok = [
        d for d in hasil
        if not kata or kata in str(d.get("domain_name", "")).lower()
    ]

    if not cocok:
        print(f"Tidak ada wilayah yang cocok dengan '{kata}'.")
        return

    print(f"\n{len(cocok)} wilayah ditemukan:\n")
    print(f"{'KODE':<8} NAMA WILAYAH")
    print("-" * 50)
    for d in cocok[:60]:
        print(f"{d.get('domain_id',''):<8} {d.get('domain_name','')}")

    if len(cocok) > 60:
        print(f"\n... dan {len(cocok)-60} lainnya. Perjelas kata kuncinya.")
    print("\n👉 Catat KODE-nya, dipakai untuk perintah berikutnya.")


def cmd_cari(domain: str, kata: str = "") -> None:
    """Cari tabel statis di satu wilayah."""
    kata = kata.lower()
    semua, halaman = [], 1

    while True:
        data = panggil(f"list/model/statictable/lang/ind/domain/{domain}/page/{halaman}")
        isi = isi_daftar(data)
        if not isi:
            break
        semua.extend(isi)

        info = data.get("data", [{}])[0] if isinstance(data.get("data"), list) else {}
        total = info.get("pages") or info.get("total_page") or 1
        if halaman >= int(total) or halaman >= 20:
            break
        halaman += 1

    cocok = [
        t for t in semua
        if not kata or kata in str(t.get("title", "")).lower()
    ]

    if not cocok:
        print(f"Tidak ada tabel yang cocok dengan '{kata}' di wilayah {domain}.")
        print(f"(total {len(semua)} tabel tersedia di wilayah ini)")
        return

    print(f"\n{len(cocok)} tabel ditemukan di wilayah {domain}:\n")
    for t in cocok[:40]:
        print(f"  [{t.get('table_id')}]  {t.get('title')}")
        if t.get("updt_date"):
            print(f"       diperbarui: {t.get('updt_date')}")

    if len(cocok) > 40:
        print(f"\n... dan {len(cocok)-40} lainnya.")
    print(f"\n👉 python scripts/bps.py ambil {domain} <table_id>")


def cmd_ambil(domain: str, table_id: str) -> None:
    """Ambil satu tabel statis, simpan sebagai CSV."""
    data = panggil(f"view/model/statictable/lang/ind/domain/{domain}/id/{table_id}")
    d = data.get("data") or {}
    if isinstance(d, list):
        d = d[0] if d else {}

    judul = d.get("title", f"tabel_{table_id}")
    html = d.get("table", "")

    if not html:
        sys.exit("❌ Tabel kosong. Cek lagi table_id-nya.")

    # BPS mengirim tabelnya dalam bentuk ter-escape (&lt;table&gt; dst),
    # jadi harus dikembalikan dulu ke HTML asli sebelum bisa dibaca pandas.
    if "&lt;" in html:
        html = unescape(html)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    aman = "".join(c if c.isalnum() or c in " -_" else "" for c in judul)
    aman = "_".join(aman.split())[:60]
    nama = f"bps_{domain}_{table_id}_{aman}"

    try:
        import pandas as pd
        from io import StringIO

        tabel = pd.read_html(StringIO(html))
        for i, df in enumerate(tabel):
            akhiran = "" if len(tabel) == 1 else f"_bag{i+1}"
            path = OUT_DIR / f"{nama}{akhiran}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            print(f"✅ {path.relative_to(ROOT)}  ({df.shape[0]} baris × {df.shape[1]} kolom)")
    except Exception as e:
        path = OUT_DIR / f"{nama}.html"
        path.write_text(html, encoding="utf-8")
        print(f"⚠️  Gagal jadi CSV ({e}). Disimpan sebagai HTML: {path.relative_to(ROOT)}")
        print("   Buka pakai Excel, atau copy-paste ke spreadsheet.")

    print(f"\n📊 {judul}")


# ---------------------------------------------------------------- main

PERINTAH = {
    "wilayah": (cmd_wilayah, 0),
    "cari": (cmd_cari, 1),
    "ambil": (cmd_ambil, 2),
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in PERINTAH:
        print(__doc__)
        sys.exit(1)

    fungsi, wajib = PERINTAH[sys.argv[1]]
    arg = sys.argv[2:]

    if len(arg) < wajib:
        print(__doc__)
        sys.exit(f"\n❌ Perintah '{sys.argv[1]}' butuh minimal {wajib} argumen.")

    try:
        fungsi(*arg)
    except requests.HTTPError as e:
        sys.exit(f"❌ Gagal menghubungi BPS: {e}")
    except requests.RequestException as e:
        sys.exit(f"❌ Masalah koneksi: {e}")


if __name__ == "__main__":
    main()
