/*
  BanguninAja — Query Fasilitas Kesehatan Eksisting
  ------------------------------------------------
  Dipakai untuk profil "Rumah Sakit":
  cari wilayah yang JAUH dari faskes yang sudah ada (underserved area).

  CARA PAKAI: sama seperti poi_kompetitor.overpassql
  1. https://overpass-turbo.eu/  →  zoom ke area
  2. Paste  →  Run  →  Export as GeoJSON
*/

[out:json][timeout:90];
(
  node["amenity"="hospital"]({{bbox}});
  way["amenity"="hospital"]({{bbox}});
  relation["amenity"="hospital"]({{bbox}});

  node["amenity"="clinic"]({{bbox}});
  way["amenity"="clinic"]({{bbox}});

  node["amenity"="doctors"]({{bbox}});
  node["amenity"="pharmacy"]({{bbox}});

  // Puskesmas di Indonesia sering ditandai begini
  node["healthcare"="centre"]({{bbox}});
  way["healthcare"="centre"]({{bbox}});
);
out center;
