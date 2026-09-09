"""
BanguninAja — Pengambil data OpenStreetMap lewat Overpass API

Menggantikan langkah manual di overpass-turbo.eu. Wilayahnya dibaca dari
wilayah.py, jadi hasilnya sama untuk semua anggota tim.

CARA PAKAI (dari folder utama proyek):

    python scripts/ambil_poi.py            # ambil semua kelompok
    python scripts/ambil_poi.py kompetitor # satu kelompok saja

Kelompok yang tersedia:
    kompetitor  restoran, kafe, mall, bank, hotel, minimarket
    lahan       lahan yang tipe penggunaannya layak dibangun
    terlarang   taman, makam, air, hutan — wilayah yang harus dikecualikan
    komersial   bangunan niaga, untuk mode sewa/beli unit
"""

import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wilayah as w

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw"

CERMIN = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# Setiap kelompok berisi baris query Overpass. Penulisan node/way/relation
# dipisah karena OSM menyimpan objek kecil sebagai titik (node) dan objek
# besar sebagai area (way/relation) — kalau hanya mengambil node, mall dan
# rumah sakit akan terlewat.
KELOMPOK = {
    "kompetitor": [
        'node["amenity"="restaurant"]', 'way["amenity"="restaurant"]',
        'node["amenity"="cafe"]', 'way["amenity"="cafe"]',
        'node["amenity"="fast_food"]',
        'node["amenity"="bar"]', 'node["amenity"="nightclub"]',
        'node["shop"="mall"]', 'way["shop"="mall"]',
        'node["shop"="supermarket"]', 'way["shop"="supermarket"]',
        'node["shop"="convenience"]',
        'node["amenity"="bank"]',
        'node["tourism"="hotel"]', 'way["tourism"="hotel"]',
    ],
    # Daftar putih: tipe lahan yang memang diperuntukkan untuk dibangun.
    "lahan": [
        'way["landuse"="brownfield"]', 'relation["landuse"="brownfield"]',
        'way["landuse"="greenfield"]', 'relation["landuse"="greenfield"]',
        'way["landuse"="construction"]',
        'way["landuse"="commercial"]', 'relation["landuse"="commercial"]',
        'way["landuse"="retail"]', 'relation["landuse"="retail"]',
        'way["landuse"="industrial"]', 'relation["landuse"="industrial"]',
        'way["landuse"="farmland"]', 'way["landuse"="meadow"]',
    ],
    # Daftar hitam: wilayah yang tidak boleh direkomendasikan, apa pun
    # skornya. Inilah yang mencegah sistem menyarankan taman kota atau
    # halaman rumah orang.
    "terlarang": [
        'way["leisure"="park"]', 'relation["leisure"="park"]',
        'way["leisure"="garden"]', 'way["leisure"="pitch"]',
        'way["landuse"="cemetery"]', 'way["landuse"="forest"]',
        'way["landuse"="grass"]', 'way["landuse"="military"]',
        'way["landuse"="residential"]', 'relation["landuse"="residential"]',
        'way["natural"="water"]', 'relation["natural"="water"]',
        'way["amenity"="school"]', 'way["amenity"="hospital"]',
        'way["amenity"="place_of_worship"]',
    ],
    # Untuk mode "sewa/beli unit": bangunan yang berpotensi berisi
    # ruko atau unit niaga yang bisa ditempati.
    "komersial": [
        'way["building"="retail"]', 'way["building"="commercial"]',
        'way["building"="office"]', 'way["building"="industrial"]',
        'way["building"="warehouse"]',
    ],
}


def susun_query(baris: list[str]) -> str:
    bbox = w.bbox_overpass()
    isi = "\n  ".join(f"{b}({bbox});" for b in baris)
    return f"[out:json][timeout:600];\n(\n  {isi}\n);\nout center;"


# Overpass menolak permintaan tanpa User-Agent yang jelas (balasan 406).
KEPALA = {"User-Agent": "BanguninAja/1.0 (proyek kuliah; github.com/jojondrw/BanguninAja)"}


def minta(query: str) -> dict | None:
    """Kirim query ke Overpass, coba cermin lain kalau yang pertama sibuk."""
    for putaran in range(2):
        for i, url in enumerate(CERMIN):
            try:
                r = requests.post(url, data={"data": query},
                                  headers=KEPALA, timeout=900)
                if r.status_code == 200:
                    return r.json()
                # 429 berarti server sedang sibuk, bukan query yang salah.
                sebab = "sibuk" if r.status_code == 429 else f"balas {r.status_code}"
                print(f"   cermin {i+1} {sebab}")
            except requests.RequestException as e:
                print(f"   cermin {i+1} gagal: {type(e).__name__}")
            time.sleep(5)

        if putaran == 0:
            print("   semua cermin sibuk, tunggu 30 detik lalu coba lagi...")
            time.sleep(30)
    return None


def ke_geojson(data: dict) -> dict:
    """Ubah balasan Overpass jadi GeoJSON titik."""
    fitur = []
    for el in data.get("elements", []):
        if el.get("type") == "node":
            lon, lat = el.get("lon"), el.get("lat")
        else:
            c = el.get("center") or {}
            lon, lat = c.get("lon"), c.get("lat")
        if lon is None or lat is None:
            continue

        fitur.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                **el.get("tags", {}),
                "osm_id": el.get("id"),
                "osm_type": el.get("type"),
            },
        })
    return {"type": "FeatureCollection", "features": fitur}


def ambil(nama: str) -> bool:
    print(f"▶  {nama} — mengirim query ke Overpass...")
    data = minta(susun_query(KELOMPOK[nama]))
    if data is None:
        print(f"❌ {nama} gagal — semua cermin sibuk, coba lagi nanti\n")
        return False

    gj = ke_geojson(data)
    if not gj["features"]:
        print(f"⏭️  {nama} tidak menghasilkan objek\n")
        return False

    OUT.mkdir(parents=True, exist_ok=True)
    berkas = OUT / f"osm_{nama}_{w.KODE}.geojson"
    berkas.write_text(json.dumps(gj), encoding="utf-8")

    ukuran = berkas.stat().st_size / 1048576
    print(f"✅ {nama}: {len(gj['features']):,} objek, {ukuran:.1f} MB → {berkas.name}\n")
    return True


def main() -> None:
    pilihan = sys.argv[1:] or list(KELOMPOK)
    salah = [p for p in pilihan if p not in KELOMPOK]
    if salah:
        sys.exit(f"❌ Kelompok tidak dikenal: {', '.join(salah)}\n"
                 f"   Pilihan: {', '.join(KELOMPOK)}")

    print(f"Wilayah: {w.NAMA}  ({w.bbox_overpass()})\n")
    berhasil = sum(ambil(n) for n in pilihan)
    print(f"{berhasil} dari {len(pilihan)} kelompok tersimpan.")


if __name__ == "__main__":
    main()
