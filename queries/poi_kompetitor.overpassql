/*
  BanguninAja — Query POI Kompetitor
  ---------------------------------
  CARA PAKAI:
  1. Buka https://overpass-turbo.eu/
  2. Geser & ZOOM peta ke area yang mau diambil (misal Jakarta Selatan)
  3. Hapus isi kotak kiri, paste query ini
  4. Klik Run (tombol ▶)
  5. Klik Export → download as GeoJSON
  6. Simpan ke data/raw/

  CATATAN: {{bbox}} otomatis mengikuti tampilan peta saat ini.
  Zoom dulu ke area kecil — kalau kelewat luas, query-nya timeout.
*/

[out:json][timeout:90];
(
  // --- F&B ---
  node["amenity"="restaurant"]({{bbox}});
  node["amenity"="cafe"]({{bbox}});
  node["amenity"="fast_food"]({{bbox}});
  node["amenity"="bar"]({{bbox}});

  // --- Retail ---
  node["shop"="mall"]({{bbox}});
  way["shop"="mall"]({{bbox}});
  node["shop"="supermarket"]({{bbox}});
  node["shop"="convenience"]({{bbox}});

  // --- Penarik keramaian (anchor) ---
  node["amenity"="school"]({{bbox}});
  node["amenity"="university"]({{bbox}});
  node["amenity"="hospital"]({{bbox}});
  way["amenity"="hospital"]({{bbox}});
  node["tourism"="hotel"]({{bbox}});

  // --- Pendukung ---
  node["amenity"="parking"]({{bbox}});
  node["amenity"="bank"]({{bbox}});
);
out center;
