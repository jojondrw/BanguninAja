"""
BanguninAja — Pengambil data bahaya bencana InaRISK (BNPB)

Mengambil langsung dari layanan REST publik BNPB, tanpa perlu akun
maupun mengunduh lewat portal.

CARA PAKAI (dari folder utama proyek):

    python scripts/ambil_inarisk.py            # ambil semua layer
    python scripts/ambil_inarisk.py banjir     # satu layer saja
    python scripts/ambil_inarisk.py --daftar   # lihat semua layer tersedia

Hasilnya disimpan ke data/raw/ dengan ukuran piksel yang sama persis
dengan potongan WorldPop, sehingga kedua raster langsung bisa ditumpuk.
"""

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wilayah as w

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw"

REST = "https://gis.bnpb.go.id/server/rest/services/inarisk"

LAYER = {
    "banjir": "layer_bahaya_banjir",
    "gempa": "layer_bahaya_gempabumi",
    "longsor": "layer_bahaya_tanah_longsor",
    "multi": "layer_bahaya_multi",
    "kebakaran": "layer_bahaya_kebakaran_hutan_dan_lahan",
    "tsunami": "layer_bahaya_tsunami",
}


def daftar_layer() -> None:
    """Tampilkan seluruh layer yang disediakan BNPB."""
    r = requests.get(f"{REST}?f=json", timeout=60)
    r.raise_for_status()
    svc = r.json().get("services", [])

    print(f"{len(svc)} layer tersedia di InaRISK:\n")
    for s in sorted(svc, key=lambda x: x["name"]):
        print(f"  {s['type']:<12} {s['name'].split('/')[-1]}")


def ambil(nama: str, service: str) -> bool:
    """Unduh satu layer bahaya sebagai GeoTIFF."""
    url = f"{REST}/{service}/ImageServer/exportImage"
    param = {
        "bbox": w.bbox(),
        "bboxSR": "4326",
        "imageSR": "4326",
        "size": w.ukuran(),
        "format": "tiff",
        "pixelType": "F32",
        "f": "image",
    }

    try:
        r = requests.get(url, params=param, timeout=180)
    except requests.RequestException as e:
        print(f"❌ {nama:<10} gagal: {e}")
        return False

    if not r.headers.get("Content-Type", "").startswith("image"):
        print(f"❌ {nama:<10} bukan gambar — layer mungkin sudah pindah")
        return False

    # Layer yang tidak punya data di wilayah ini mengembalikan berkas
    # sangat kecil. Contoh: longsor di Jakarta yang datarannya rata,
    # sehingga memang tidak ada indeks bahayanya.
    if len(r.content) < 5000:
        print(f"⏭️  {nama:<10} kosong di wilayah ini — dilewati")
        return False

    OUT.mkdir(parents=True, exist_ok=True)
    berkas = OUT / f"inarisk_bahaya_{nama}_{w.KODE}.tif"
    berkas.write_bytes(r.content)
    print(f"✅ {nama:<10} {len(r.content)/1024:>7.0f} KB  →  {berkas.name}")
    return True


def main() -> None:
    arg = sys.argv[1:]

    if arg and arg[0] in ("--daftar", "-d"):
        daftar_layer()
        return

    pilihan = arg or list(LAYER)
    tidak_dikenal = [p for p in pilihan if p not in LAYER]
    if tidak_dikenal:
        sys.exit(
            f"❌ Layer tidak dikenal: {', '.join(tidak_dikenal)}\n"
            f"   Pilihan: {', '.join(LAYER)}"
        )

    print(f"Mengambil dari BNPB — {w.NAMA} ({w.bbox()})\n")
    berhasil = sum(ambil(n, LAYER[n]) for n in pilihan)
    print(f"\n{berhasil} dari {len(pilihan)} layer tersimpan di data/raw/")


if __name__ == "__main__":
    main()
