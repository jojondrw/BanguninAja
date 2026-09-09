"""
BanguninAja — Pengaturan wilayah studi

Satu-satunya tempat wilayah studi ditentukan. Semua skrip lain membaca
dari sini, supaya seluruh data terpotong pada batas yang sama persis dan
setiap raster bertumpuk tepat piksel per piksel.

Untuk pindah wilayah, ubah berkas ini saja.
"""

# Nama kota/kabupaten sesuai penulisan GADM (kolom NAME_2).
KOTA = [
    "Jakarta Pusat",
    "Jakarta Utara",
    "Jakarta Barat",
    "Jakarta Selatan",
    "Jakarta Timur",
]

# Kepulauan Seribu sengaja tidak diikutkan. Wilayahnya membentang jauh
# ke utara sehingga akan melebarkan kotak pencarian sampai ~100 km,
# padahal isinya laut. Menyertakannya membuat seluruh raster jadi
# 10 kali lebih besar tanpa menambah lokasi yang bisa dibangun.

NAMA = "DKI Jakarta"
KODE = "dki"

# Kotak wilayah studi: bujur & lintang, ditambah penyangga ~2 km.
# Diambil dari batas GADM kelima kota di atas.
BARAT, TIMUR = 106.667, 106.992
SELATAN, UTARA = -6.390, -6.070

# Ukuran raster. Dihitung dari kotak di atas pada resolusi ~100 m
# (0,000833 derajat per piksel), disamakan dengan resolusi asli WorldPop.
LEBAR, TINGGI = 390, 384

# Kode wilayah BPS untuk kelima kota.
DOMAIN_BPS = {
    "3171": "Jakarta Selatan",
    "3172": "Jakarta Timur",
    "3173": "Jakarta Pusat",
    "3174": "Jakarta Barat",
    "3175": "Jakarta Utara",
}

# GADM menuliskan sebagian kecamatan dengan dua ejaan berbeda, sehingga
# satu kecamatan terbaca sebagai dua poligon. Pemetaan ini menyeragamkan
# ejaannya sekaligus menyamakannya dengan penulisan BPS, supaya data dari
# kedua sumber bisa digabungkan.
EJAAN = {
    "Kabayoran Lama": "KEBAYORAN LAMA",
    "Kebayoran Lama": "KEBAYORAN LAMA",
    "Setia Budi": "SETIA BUDI",
    "Setiabudi": "SETIA BUDI",
}


def bbox() -> str:
    """Kotak wilayah untuk layanan REST: barat,selatan,timur,utara."""
    return f"{BARAT},{SELATAN},{TIMUR},{UTARA}"


def bbox_overpass() -> str:
    """Kotak wilayah untuk Overpass: selatan,barat,utara,timur."""
    return f"{SELATAN},{BARAT},{UTARA},{TIMUR}"


def projwin() -> list[str]:
    """Kotak wilayah untuk gdal_translate: kiri, atas, kanan, bawah."""
    return [str(BARAT), str(UTARA), str(TIMUR), str(SELATAN)]


def extent() -> tuple[float, float, float, float]:
    """Kotak wilayah untuk matplotlib: kiri, kanan, bawah, atas."""
    return (BARAT, TIMUR, SELATAN, UTARA)


def ukuran() -> str:
    """Ukuran raster untuk layanan REST."""
    return f"{LEBAR},{TINGGI}"


def where_kota(kolom: str = "NAME_2") -> str:
    """Klausa SQL untuk menyaring kota-kota wilayah studi."""
    daftar = ", ".join(f"'{k}'" for k in KOTA)
    return f"{kolom} IN ({daftar})"
