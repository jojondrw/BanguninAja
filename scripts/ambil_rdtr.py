"""
BanguninAja — Pengambil data RDTR (zonasi, KDB/KLB) dari ATR/BPN

Endpoint yang dipakai BUKAN ArcGIS (yang rusak/butuh token), tapi backend
asli portal RDTR Interaktif yang dipakai fitur "klik peta = lihat detail
zona". Ditemukan lewat DevTools Network tab, bukan reverse-engineer JS:

    GET https://gistaru.atrbpn.go.id/rdtrinteraktif/api/interactive/data
        ?id_wilayah={kode_kota}&latitude={lat}&longitude={lon}

Ini point-query (1 request = 1 titik), jadi buat cakupan area kita bikin
grid titik dalam batas kab/kota (dari GADM yang sudah ada), lalu query
satu-satu. Hasilnya per titik: kode/nama zona, KDB, KLB, KDH, GSB, daftar
kegiatan yang diizinkan/bersyarat.

CARA PAKAI (dari folder utama proyek):

    python scripts/ambil_rdtr.py --katalog
        Bangun daftar kota yang punya RDTR aktif (sekali saja, dari 38
        provinsi). Hasilnya data/raw/rdtr_katalog.json.

    python scripts/ambil_rdtr.py --kota "Kab. Aceh Tengah" --spasi 500
        Tarik satu kota, grid 500m. Butuh katalog sudah ada.

    python scripts/ambil_rdtr.py --semua --spasi 500
        Tarik SEMUA kota di katalog. Ini bisa puluhan ribu request —
        jalankan semalaman, bukan buat dicoba iseng.

Perlu GADM (data/raw/gadm41_indonesia.gpkg) untuk batas wilayah tiap kota.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import which

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent


def siapkan_env_gdal() -> dict:
    """GDAL/PROJ butuh GDAL_DATA & PROJ_LIB, tidak selalu ke-set otomatis di Windows."""
    env = os.environ.copy()
    for qgis in sorted(Path("C:/Program Files").glob("QGIS*"), reverse=True):
        gdal_data = qgis / "apps" / "gdal" / "share" / "gdal"
        proj_lib = qgis / "share" / "proj"
        if gdal_data.exists():
            env["GDAL_DATA"] = str(gdal_data)
        if proj_lib.exists():
            env["PROJ_LIB"] = str(proj_lib)
        if gdal_data.exists() or proj_lib.exists():
            break
    return env

OUT_KATALOG = ROOT / "data" / "raw" / "rdtr_katalog.json"
OUT_DIR = ROOT / "data" / "raw" / "rdtr"
GADM = ROOT / "data" / "raw" / "gadm41_indonesia.gpkg"

BASE = "https://gistaru.atrbpn.go.id/rdtrinteraktif/api/interactive"
PEKERJA = 15  # request paralel — bottleneck-nya latensi jaringan (~1 detik/request),
              # bukan CPU, jadi paralel motong waktu total ~15x tanpa nge-hajar server


def cari_gdal() -> Path:
    for k in sorted(Path("C:/Program Files").glob("QGIS*"), reverse=True):
        if (k / "bin" / "ogr2ogr.exe").exists():
            return k / "bin"
    if which("ogr2ogr"):
        return Path(which("ogr2ogr")).parent
    sys.exit("❌ GDAL tidak ketemu. Pasang QGIS dulu.")


# ---------------------------------------------------------------- katalog


def bangun_katalog() -> None:
    """Kumpulkan semua kota yang punya RDTR aktif, dari seluruh provinsi."""
    provinsi = requests.get(f"{BASE}/provinces", timeout=60).json()["data"]
    print(f"{len(provinsi)} provinsi ditemukan.\n")

    katalog = []
    for p in provinsi:
        id_prov = p["id"]
        nama_prov = p["provinsi"]
        try:
            kota_list = requests.get(f"{BASE}/cities/{id_prov}", timeout=60).json()["data"]
        except (requests.RequestException, KeyError, ValueError):
            print(f"⚠️  {nama_prov}: gagal ambil daftar kota, dilewati")
            continue

        for k in kota_list:
            id_kota = k["id"]
            nama_kota = k["kota_atau_kabupaten"] or "?"
            try:
                rdtr = requests.get(f"{BASE}/rdtr/{id_kota}", timeout=30).json()["data"]
            except (requests.RequestException, KeyError, ValueError):
                continue
            time.sleep(0.15)  # katalog cuma dibangun sekali, gak perlu paralel

            for r in rdtr:
                if r.get("status") == 6:  # 6 = RDTR sudah jadi produk hukum
                    katalog.append({
                        "id_wilayah": id_kota,
                        "id_rtr": r["id_rtr"],
                        "provinsi": nama_prov,
                        "kota": nama_kota,
                        "nama_rtr": r.get("rtr", ""),
                    })
        print(f"✅ {nama_prov}: {len(kota_list)} kota dicek")

    OUT_KATALOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_KATALOG.write_text(json.dumps(katalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(katalog)} RDTR aktif ditemukan → {OUT_KATALOG.relative_to(ROOT)}")


def baca_katalog() -> list[dict]:
    if not OUT_KATALOG.exists():
        sys.exit(f"❌ {OUT_KATALOG.name} belum ada. Jalankan --katalog dulu.")
    return json.loads(OUT_KATALOG.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- grid


def normalkan_nama(nama: str) -> str:
    """Seragamkan 'Kab. Aceh Tengah' / 'Kota Bandung' jadi bentuk yang cocok dengan GADM NAME_2."""
    n = nama.upper()
    n = re.sub(r"^KAB\.?\s+", "", n)
    n = re.sub(r"^KOTA\s+", "", n)
    n = n.strip()
    return n


def bbox_kota(nama_kota: str) -> tuple[float, float, float, float] | None:
    """Ambil bounding box kab/kota dari GADM lewat ogr2ogr, kembalikan (barat, selatan, timur, utara)."""
    if not GADM.exists():
        sys.exit(f"❌ {GADM.name} belum ada.")

    bin_gdal = cari_gdal()
    target = normalkan_nama(nama_kota)

    hasil = subprocess.run(
        [str(bin_gdal / "ogrinfo"), "-al", "-dialect", "SQLITE", "-sql",
         f"SELECT ST_MinX(geom), ST_MinY(geom), ST_MaxX(geom), ST_MaxY(geom) "
         f"FROM ADM_ADM_2 WHERE UPPER(NAME_2) LIKE '%{target}%'",
         str(GADM)],
        capture_output=True, text=True, errors="replace", env=siapkan_env_gdal(),
    )

    angka = re.findall(r"=\s*(-?\d+\.\d+)", hasil.stdout)
    if len(angka) < 4:
        return None
    b, s, t, u = (float(x) for x in angka[:4])
    return (b, s, t, u)


def buat_grid(bbox: tuple[float, float, float, float], spasi_m: float) -> list[tuple[float, float]]:
    """Bikin grid titik lat/lon dalam bbox, jarak antar titik kira-kira spasi_m meter."""
    barat, selatan, timur, utara = bbox
    lat_tengah = (selatan + utara) / 2
    derajat_per_m_lat = 1 / 111_320
    derajat_per_m_lon = 1 / (111_320 * max(0.1, abs(__import__("math").cos(__import__("math").radians(lat_tengah)))))

    langkah_lat = spasi_m * derajat_per_m_lat
    langkah_lon = spasi_m * derajat_per_m_lon

    titik = []
    lat = selatan
    while lat <= utara:
        lon = barat
        while lon <= timur:
            titik.append((lat, lon))
            lon += langkah_lon
        lat += langkah_lat
    return titik


# ---------------------------------------------------------------- ambil


def ambil_titik(id_wilayah: str, lat: float, lon: float) -> dict | None:
    try:
        r = requests.get(f"{BASE}/data", params={
            "id_wilayah": id_wilayah, "latitude": lat, "longitude": lon,
        }, timeout=20)
        j = r.json()
    except (requests.RequestException, ValueError):
        return None

    if j.get("status") != 200 or not j.get("data"):
        return None
    return j["data"]


SPASI_SCAN_KASAR_M = 2000  # RDTR cuma nutup "kawasan perkotaan", bukan seluruh kabupaten —
                            # scan kasar dulu biar gak buang request ke area kosong


def cari_area_rdtr(id_wilayah: str, bbox: tuple[float, float, float, float]) -> tuple[float, float, float, float] | None:
    """Scan kasar seluruh bbox kabupaten, kembalikan sub-bbox tempat RDTR beneran ada datanya."""
    titik_kasar = buat_grid(bbox, SPASI_SCAN_KASAR_M)
    lat_kena, lon_kena = [], []

    with ThreadPoolExecutor(max_workers=PEKERJA) as kolam:
        hasil = kolam.map(lambda t: (t, ambil_titik(id_wilayah, *t)), titik_kasar)
        for (lat, lon), data in hasil:
            if data:
                lat_kena.append(lat)
                lon_kena.append(lon)

    if not lat_kena:
        return None

    # kasih penyangga selebar 1 sel grid kasar, biar tepi kawasan gak kepotong
    pad_lat = SPASI_SCAN_KASAR_M / 111_320
    pad_lon = pad_lat
    return (min(lon_kena) - pad_lon, min(lat_kena) - pad_lat,
            max(lon_kena) + pad_lon, max(lat_kena) + pad_lat)


def ambil_kota(entri: dict, spasi_m: float) -> None:
    id_wilayah = entri["id_wilayah"]
    nama_kota = entri["kota"]

    aman = re.sub(r"[^A-Za-z0-9]+", "_", nama_kota).strip("_")
    berkas = OUT_DIR / f"rdtr_{id_wilayah}_{aman}.json"
    if berkas.exists():
        print(f"⏭️  {nama_kota}: sudah pernah ditarik, dilewati (hapus filenya kalau mau tarik ulang)")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    bbox_kab = bbox_kota(nama_kota)
    if bbox_kab is None:
        print(f"⏭️  {nama_kota}: batas wilayah tidak ketemu di GADM, dilewati")
        berkas.write_text("[]", encoding="utf-8")  # tandai sudah dicoba, biar tidak diulang
        return

    print(f"🔍 {nama_kota}: scan kasar dulu (spasi {SPASI_SCAN_KASAR_M}m) buat nemuin kawasan RDTR...")
    bbox = cari_area_rdtr(id_wilayah, bbox_kab)
    if bbox is None:
        print(f"⏭️  {nama_kota}: scan kasar nihil — kawasan RDTR-nya kelewat kecil buat spasi {SPASI_SCAN_KASAR_M}m, atau id_wilayah salah")
        berkas.write_text("[]", encoding="utf-8")
        return

    titik = buat_grid(bbox, spasi_m)
    print(f"▶  {nama_kota} ({id_wilayah}): kawasan RDTR ketemu, {len(titik)} titik grid halus @ {spasi_m}m ({PEKERJA} paralel)")

    hasil = []
    selesai = 0
    with ThreadPoolExecutor(max_workers=PEKERJA) as kolam:
        for (lat, lon), data in kolam.map(lambda t: (t, ambil_titik(id_wilayah, *t)), titik):
            selesai += 1
            if data:
                data["_lat"] = lat
                data["_lon"] = lon
                hasil.append(data)
            if selesai % 100 == 0:
                print(f"   {selesai}/{len(titik)} titik, {len(hasil)} berisi zona")

    if not hasil:
        print(f"⏭️  {nama_kota}: tidak ada titik yang berisi data zona (mungkin grid meleset dari kawasan RDTR)")
        berkas.write_text("[]", encoding="utf-8")
        return

    berkas.write_text(json.dumps(hasil, ensure_ascii=False), encoding="utf-8")
    print(f"✅ {nama_kota}: {len(hasil)}/{len(titik)} titik berisi zona → {berkas.relative_to(ROOT)}")


# ---------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--katalog", action="store_true", help="Bangun daftar kota yang punya RDTR aktif")
    ap.add_argument("--kota", help="Nama kota/kabupaten yang mau ditarik (harus ada di katalog)")
    ap.add_argument("--semua", action="store_true", help="Tarik SEMUA kota di katalog (lama, puluhan ribu request)")
    ap.add_argument("--spasi", type=float, default=200, help="Jarak antar titik grid HALUS dalam meter, setelah kawasan RDTR ketemu lewat scan kasar (default 200)")
    args = ap.parse_args()

    if args.katalog:
        bangun_katalog()
        return

    katalog = baca_katalog()

    if args.kota:
        cocok = [k for k in katalog if args.kota.lower() in k["kota"].lower()]
        if not cocok:
            sys.exit(f"❌ '{args.kota}' tidak ketemu di katalog ({len(katalog)} entri tersedia).")
        for entri in cocok:
            ambil_kota(entri, args.spasi)
        return

    if args.semua:
        print(f"Menarik SEMUA {len(katalog)} kota di katalog, spasi grid {args.spasi}m.")
        print("Ini akan memakan waktu lama — biarkan berjalan, jangan dihentikan di tengah.\n")
        for entri in katalog:
            ambil_kota(entri, args.spasi)
        return

    print(__doc__)


if __name__ == "__main__":
    main()
