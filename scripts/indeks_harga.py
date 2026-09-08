"""
BanguninAja — Indeks harga tanah per kecamatan

Nilai NJOP resmi tidak tersedia dalam bentuk yang bisa diunduh massal:
peta Zona Nilai Tanah di Bhumi ATR/BPN hanya bisa dicek satu titik pada
satu waktu, dan NJOP DKI diterbitkan lewat Peraturan Gubernur berformat
PDF. Skrip ini menyusun indeks pengganti dari data yang sudah ada.

Tiga penyusunnya:

  Kedekatan ke pusat kota  50%   makin dekat Bundaran HI, makin mahal
  Kepadatan niaga premium  30%   bank, mall, dan hotel per km persegi
  Kepadatan penduduk       20%   permintaan terhadap ruang

Keluarannya dua berkas:

  data/processed/indeks_harga_kecamatan.csv
      indeks 0-100 untuk seluruh kecamatan, siap dipakai mesin skoring

  data/processed/njop_isian.csv
      lembar isian berisi titik tengah tiap kecamatan. Buka Bhumi
      (bhumi.atrbpn.go.id), klik koordinat yang tertera, lalu catat
      angkanya. Setelah terisi, indeks di atas bisa dikalibrasi ke
      rupiah sungguhan.

CARA PAKAI (dari folder utama proyek):

    python scripts/indeks_harga.py
"""

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wilayah as w

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

# Bundaran Hotel Indonesia, titik acuan pusat kegiatan ekonomi Jakarta.
CBD = (106.8230, -6.1944)

# Jenis tempat yang keberadaannya menandakan harga tanah tinggi.
PENANDA_MAHAL = {"bank", "mall", "hotel", "supermarket"}

BOBOT = {"kedekatan": 0.5, "niaga": 0.3, "penduduk": 0.2}


def cari_gdal() -> Path:
    for k in sorted(Path("C:/Program Files").glob("QGIS*"), reverse=True):
        if (k / "bin" / "ogr2ogr.exe").exists():
            return k / "bin"
    from shutil import which
    if which("ogr2ogr"):
        return Path(which("ogr2ogr")).parent
    sys.exit("❌ GDAL tidak ketemu. Pasang QGIS dulu.")


BIN = cari_gdal()


def baca_kecamatan() -> list[dict]:
    """Ambil nama, titik tengah, dan luas tiap kecamatan."""
    gpkg = OUT / f"{w.KODE}_kecamatan_bersih.gpkg"
    if not gpkg.exists():
        sys.exit(f"❌ {gpkg.name} belum ada. Jalankan siapkan_data.py dulu.")

    tmp = OUT / "_kec.geojson"
    tmp.unlink(missing_ok=True)

    subprocess.run(
        [str(BIN / "ogr2ogr"), "-f", "GeoJSON", str(tmp), str(gpkg),
         "-dialect", "SQLITE", "-sql",
         "SELECT kecamatan, ST_X(ST_Centroid(geom)) AS lon, "
         "ST_Y(ST_Centroid(geom)) AS lat, ST_Area(geom) * 12365 AS luas_km2, "
         "geom FROM kecamatan"],
        capture_output=True,
    )
    if not tmp.exists():
        sys.exit("❌ Gagal membaca batas kecamatan.")

    data = json.loads(tmp.read_text(encoding="utf-8"))
    tmp.unlink(missing_ok=True)

    hasil = []
    for f in data["features"]:
        p = f["properties"]
        batas = []
        g = f.get("geometry") or {}
        bagian = g.get("coordinates") or []
        if g.get("type") == "Polygon":
            bagian = [bagian]
        for poly in bagian:
            if poly and poly[0]:
                batas.append(poly[0])

        hasil.append({
            "kecamatan": p["kecamatan"],
            "lon": p["lon"],
            "lat": p["lat"],
            "luas_km2": p["luas_km2"],
            "batas": batas,
        })
    return hasil


def di_dalam(titik: tuple[float, float], cincin: list) -> bool:
    """Uji titik-dalam-poligon dengan metode ray casting."""
    x, y = titik
    masuk = False
    n = len(cincin)
    for i in range(n):
        x1, y1 = cincin[i][0], cincin[i][1]
        x2, y2 = cincin[(i + 1) % n][0], cincin[(i + 1) % n][1]
        if (y1 > y) != (y2 > y):
            potong = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < potong:
                masuk = not masuk
    return masuk


def hitung_niaga(kec: list[dict]) -> None:
    """Hitung jumlah tempat penanda harga tinggi di tiap kecamatan."""
    berkas = RAW / f"osm_kompetitor_{w.KODE}.geojson"
    if not berkas.exists():
        sys.exit(f"❌ {berkas.name} belum ada. Jalankan ambil_poi.py dulu.")

    data = json.loads(berkas.read_text(encoding="utf-8"))
    for k in kec:
        k["niaga"] = 0

    for f in data["features"]:
        p = f["properties"]
        jenis = p.get("amenity") or p.get("shop") or p.get("tourism")
        if jenis not in PENANDA_MAHAL:
            continue

        titik = tuple(f["geometry"]["coordinates"])
        for k in kec:
            if any(di_dalam(titik, c) for c in k["batas"]):
                k["niaga"] += 1
                break


def hitung_penduduk(kec: list[dict]) -> None:
    """
    Perkirakan kepadatan penduduk tiap kecamatan.

    Dipakai kepadatan titik POI sebagai pendekatan sementara. Untuk angka
    yang lebih tepat, WorldPop bisa dijumlahkan per kecamatan — tapi itu
    perlu pustaka raster tambahan, sedangkan hasilnya di sini hanya
    dipakai sebagai satu dari tiga penyusun indeks.
    """
    berkas = RAW / f"osm_terlarang_{w.KODE}.geojson"
    if not berkas.exists():
        for k in kec:
            k["penduduk"] = 0
        return

    data = json.loads(berkas.read_text(encoding="utf-8"))
    for k in kec:
        k["penduduk"] = 0

    for f in data["features"]:
        # Permukiman dan sekolah menandakan wilayah berpenghuni padat.
        p = f["properties"]
        if p.get("landuse") != "residential" and p.get("amenity") != "school":
            continue

        titik = tuple(f["geometry"]["coordinates"])
        for k in kec:
            if any(di_dalam(titik, c) for c in k["batas"]):
                k["penduduk"] += 1
                break


def jarak_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Jarak dua koordinat dalam kilometer."""
    dx = (a[0] - b[0]) * 110.6 * math.cos(math.radians(a[1]))
    dy = (a[1] - b[1]) * 110.6
    return math.hypot(dx, dy)


def normalkan(nilai: list[float]) -> list[float]:
    """Ubah sederet angka jadi rentang 0-1."""
    rendah, tinggi = min(nilai), max(nilai)
    if tinggi == rendah:
        return [0.5] * len(nilai)
    return [(v - rendah) / (tinggi - rendah) for v in nilai]


def main() -> None:
    kec = baca_kecamatan()
    print(f"{len(kec)} kecamatan dibaca.\n")

    print("Menghitung kepadatan niaga...")
    hitung_niaga(kec)
    print("Menghitung kepadatan permukiman...")
    hitung_penduduk(kec)

    for k in kec:
        k["jarak_cbd_km"] = jarak_km((k["lon"], k["lat"]), CBD)
        luas = max(k["luas_km2"], 0.1)
        k["niaga_per_km2"] = k["niaga"] / luas
        k["huni_per_km2"] = k["penduduk"] / luas

    # Kedekatan dibalik dari jarak: makin dekat pusat, makin tinggi nilainya.
    dekat = normalkan([-k["jarak_cbd_km"] for k in kec])
    niaga = normalkan([k["niaga_per_km2"] for k in kec])
    huni = normalkan([k["huni_per_km2"] for k in kec])

    for i, k in enumerate(kec):
        k["indeks"] = round(100 * (
            BOBOT["kedekatan"] * dekat[i]
            + BOBOT["niaga"] * niaga[i]
            + BOBOT["penduduk"] * huni[i]
        ), 1)

    kec.sort(key=lambda k: -k["indeks"])

    OUT.mkdir(parents=True, exist_ok=True)

    berkas_indeks = OUT / "indeks_harga_kecamatan.csv"
    with berkas_indeks.open("w", newline="", encoding="utf-8-sig") as f:
        tulis = csv.writer(f)
        tulis.writerow(["kecamatan", "indeks_harga", "jarak_cbd_km",
                        "niaga_per_km2", "luas_km2", "lon", "lat"])
        for k in kec:
            tulis.writerow([k["kecamatan"], k["indeks"],
                            round(k["jarak_cbd_km"], 2),
                            round(k["niaga_per_km2"], 1),
                            round(k["luas_km2"], 2),
                            round(k["lon"], 5), round(k["lat"], 5)])

    berkas_isian = OUT / "njop_isian.csv"
    with berkas_isian.open("w", newline="", encoding="utf-8-sig") as f:
        tulis = csv.writer(f)
        tulis.writerow(["no", "kecamatan", "lat_lon_untuk_dicek",
                        "indeks_harga", "njop_rp_per_m2", "diisi_oleh"])
        for i, k in enumerate(kec, 1):
            tulis.writerow([i, k["kecamatan"],
                            f"{k['lat']:.5f}, {k['lon']:.5f}",
                            k["indeks"], "", ""])

    print(f"\n✅ {berkas_indeks.relative_to(ROOT)}")
    print(f"✅ {berkas_isian.relative_to(ROOT)}")

    print("\n5 kecamatan termahal menurut indeks:")
    for k in kec[:5]:
        print(f"  {k['indeks']:>5.1f}  {k['kecamatan']:<20} "
              f"{k['jarak_cbd_km']:>5.1f} km dari HI")
    print("\n5 terendah:")
    for k in kec[-5:]:
        print(f"  {k['indeks']:>5.1f}  {k['kecamatan']:<20} "
              f"{k['jarak_cbd_km']:>5.1f} km dari HI")


if __name__ == "__main__":
    main()
