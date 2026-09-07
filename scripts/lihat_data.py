"""
BanguninAja — Menggambar data jadi peta yang bisa dilihat

File .tif berisi grid angka, bukan gambar. Kalau dibuka dengan penampil
gambar biasa hasilnya tampak gelap dan tidak terbaca. Skrip ini
mengubahnya jadi peta berwarna supaya isinya kelihatan.

CARA PAKAI (dari folder utama proyek):

    python scripts/lihat_data.py

Hasilnya: reports/tampilan_data.png
"""

import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon as MplPolygon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wilayah as w

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "reports"

BATAS = w.extent()  # kiri, kanan, bawah, atas


def cari_gdal() -> Path:
    for k in sorted(Path("C:/Program Files").glob("QGIS*"), reverse=True):
        if (k / "bin" / "gdal_translate.exe").exists():
            return k / "bin"
    from shutil import which
    if which("gdal_translate"):
        return Path(which("gdal_translate")).parent
    sys.exit("❌ GDAL tidak ketemu. Pasang QGIS dulu.")


BIN = cari_gdal()


def baca_raster(tif: Path) -> np.ndarray | None:
    """Ubah GeoTIFF jadi array angka lewat perantara PNG."""
    if not tif.exists():
        return None

    png = OUT / f"_{tif.stem}.png"
    subprocess.run(
        [str(BIN / "gdal_translate"), "-q", "-of", "PNG", "-ot", "Byte",
         "-scale", str(tif), str(png)],
        capture_output=True,
    )
    if not png.exists():
        return None

    arr = plt.imread(png).astype(float)
    if arr.ndim == 3:
        arr = arr[:, :, 0]

    for sisa in OUT.glob(f"_{tif.stem}.*"):
        sisa.unlink(missing_ok=True)
    return arr


def baca_batas() -> list:
    """Ambil poligon kecamatan sebagai daftar koordinat."""
    gpkg = PROC / f"{w.KODE}_kecamatan_bersih.gpkg"
    if not gpkg.exists():
        return []

    tmp = OUT / "_batas.geojson"
    tmp.unlink(missing_ok=True)
    subprocess.run(
        [str(BIN / "ogr2ogr"), "-f", "GeoJSON", str(tmp), str(gpkg)],
        capture_output=True,
    )
    if not tmp.exists():
        return []

    data = json.loads(tmp.read_text(encoding="utf-8"))
    tmp.unlink(missing_ok=True)

    bentuk = []
    for f in data.get("features", []):
        g = f.get("geometry") or {}
        koord = g.get("coordinates") or []
        bagian = koord if g.get("type") == "MultiPolygon" else [koord]
        for poly in bagian:
            if poly and poly[0]:
                bentuk.append(np.array(poly[0]))
    return bentuk


def baca_poi() -> dict:
    """Kelompokkan POI berdasarkan jenisnya."""
    f = RAW / f"osm_kompetitor_{w.KODE}.geojson"
    if not f.exists():
        return {}

    data = json.loads(f.read_text(encoding="utf-8"))
    kelompok: dict[str, list] = {}
    for fitur in data.get("features", []):
        g = fitur.get("geometry") or {}
        if g.get("type") != "Point":
            continue
        p = fitur.get("properties", {})
        jenis = p.get("amenity") or p.get("shop") or p.get("tourism") or "lain"
        kelompok.setdefault(jenis, []).append(g["coordinates"])
    return kelompok


def gambar_batas(ax, bentuk, warna="white", tebal=0.8) -> None:
    for b in bentuk:
        ax.add_patch(MplPolygon(b, closed=True, fill=False,
                                edgecolor=warna, linewidth=tebal))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    batas = baca_batas()
    poi = baca_poi()

    fig, axes = plt.subplots(2, 2, figsize=(14, 13))
    fig.suptitle(f"BanguninAja — Bentuk Data yang Dipakai\n{w.NAMA}",
                 fontsize=16, fontweight="bold")

    # 1. Kepadatan penduduk
    ax = axes[0][0]
    pop = baca_raster(PROC / f"worldpop_{w.KODE}_2020.tif")
    if pop is not None:
        ax.imshow(pop, extent=BATAS, cmap="YlOrRd", origin="upper")
    gambar_batas(ax, batas, "black", 0.7)
    ax.set_title("1. WorldPop — Kepadatan Penduduk\n"
                 "makin merah = makin padat", fontsize=11, fontweight="bold")

    # 2. Bahaya banjir
    ax = axes[0][1]
    banjir = baca_raster(RAW / f"inarisk_bahaya_banjir_{w.KODE}.tif")
    if banjir is not None:
        ax.imshow(banjir, extent=BATAS, cmap="Blues", origin="upper")
    gambar_batas(ax, batas, "black", 0.7)
    ax.set_title("2. InaRISK — Bahaya Banjir\n"
                 "makin biru = makin rawan", fontsize=11, fontweight="bold")

    # 3. Titik POI
    ax = axes[1][0]
    ax.set_facecolor("#f5f5f5")
    gambar_batas(ax, batas, "#888", 0.9)
    warna = {"restaurant": "#e41a1c", "cafe": "#ff7f00", "bank": "#377eb8",
             "convenience": "#4daf4a", "mall": "#984ea3", "hotel": "#a65628"}
    for jenis, titik in sorted(poi.items(), key=lambda x: -len(x[1]))[:6]:
        t = np.array(titik)
        ax.scatter(t[:, 0], t[:, 1], s=4, alpha=0.6,
                   c=warna.get(jenis, "#999"), label=f"{jenis} ({len(titik)})")
    ax.legend(fontsize=7, markerscale=2, loc="lower left")
    ax.set_title(f"3. OpenStreetMap — POI Kompetitor\n"
                 f"{sum(len(v) for v in poi.values())} titik",
                 fontsize=11, fontweight="bold")

    # 4. Gabungan
    ax = axes[1][1]
    if pop is not None:
        ax.imshow(pop, extent=BATAS, cmap="YlOrRd", origin="upper", alpha=0.85)
    if banjir is not None:
        ax.imshow(np.ma.masked_where(banjir < 60, banjir), extent=BATAS,
                  cmap="Blues", origin="upper", alpha=0.45)
    for jenis in ("restaurant", "mall"):
        if jenis in poi:
            t = np.array(poi[jenis])
            ax.scatter(t[:, 0], t[:, 1], s=3, alpha=0.5,
                       c="black" if jenis == "restaurant" else "lime",
                       label=jenis)
    gambar_batas(ax, batas, "black", 0.9)
    ax.legend(fontsize=8, markerscale=3, loc="lower left")
    ax.set_title("4. Ditumpuk Jadi Satu\n"
                 "inilah bahan mesin skoring", fontsize=11, fontweight="bold")

    for baris in axes:
        for a in baris:
            a.set_xlim(BATAS[0], BATAS[1])
            a.set_ylim(BATAS[2], BATAS[3])
            a.set_xlabel("Bujur", fontsize=8)
            a.set_ylabel("Lintang", fontsize=8)
            a.tick_params(labelsize=7)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    hasil = OUT / f"tampilan_data_{w.KODE}.png"
    plt.savefig(hasil, dpi=110, bbox_inches="tight")
    print(f"✅ {hasil.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
