"""
Script sekali-pakai: tarik data kriminalitas per provinsi dari BPS.
Cari tabel dengan kata kunci 'kejahatan' atau 'kriminal' di tiap 34 provinsi,
ambil yang paling relevan, simpan sebagai CSV.
"""
import sys
import time
sys.path.insert(0, "scripts")
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

KATA_KUNCI = ["kejahatan", "kriminal", "keamanan"]


def cari_tabel(domain: str) -> dict | None:
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

    for kata in KATA_KUNCI:
        cocok = [t for t in semua if kata in str(t.get("title", "")).lower()]
        if cocok:
            return cocok[0]
    return None


def main():
    berhasil, gagal = [], []
    for kode, nama in PROVINSI.items():
        print(f"\n=== {kode} {nama} ===")
        try:
            tabel = cari_tabel(kode)
            if not tabel:
                print(f"  (tidak ada tabel kriminalitas/kejahatan/keamanan)")
                gagal.append((kode, nama, "tidak ditemukan"))
                continue
            table_id = tabel.get("table_id")
            judul = tabel.get("title")
            print(f"  ditemukan: [{table_id}] {judul}")
            cmd_ambil(kode, str(table_id))
            berhasil.append((kode, nama, table_id, judul))
        except SystemExit as e:
            print(f"  GAGAL: {e}")
            gagal.append((kode, nama, str(e)))
        except Exception as e:
            print(f"  ERROR: {e}")
            gagal.append((kode, nama, str(e)))
        time.sleep(0.5)

    print(f"\n\n=== RINGKASAN ===")
    print(f"Berhasil: {len(berhasil)}/{len(PROVINSI)}")
    print(f"Gagal: {len(gagal)}/{len(PROVINSI)}")
    if gagal:
        print("\nProvinsi yang gagal:")
        for kode, nama, alasan in gagal:
            print(f"  {kode} {nama}: {alasan}")


if __name__ == "__main__":
    main()
