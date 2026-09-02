# FLARE — Data Sources

Study area: Chamoli district, Uttarakhand
Bounding box: 30.2–31.0 N, 79.0–80.0 E

---

## chamoli_rainfall_2010_2021.csv

**Source:** India Meteorological Department (IMD), gridded daily rainfall
**Access:** `imdlib` Python package (`pip install imdlib`)
**URL:** https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html
**Resolution:** 0.25° grid, daily
**Period:** 2010–2021
**Rows:** 87,660
**Columns:** time, lat, lon, rain (mm)
**Script:** `ml/fetch_rainfall.py`
**Notes:** Raw `.grd` files excluded from repo via .gitignore. Values below -100 removed as no-data sentinels.

---

## chamoli_terrain.csv

**Source:** SRTM 30m Digital Elevation Model
**Access:** OpenTopography portal (manual download)
**URL:** https://portal.opentopography.org/raster?opentopoID=OTSRTM.082015.4326.1
**Resolution:** 30m, aggregated to 0.25° grid
**Columns:** lat, lon, elevation (m), slope (deg), slope_max (deg), aspect (deg)
**Script:** `ml/fetch_terrain.py`
**Notes:** Slope and aspect derived from elevation, not downloaded. Raw GeoTIFF excluded from repo.

---

## [pending] soil moisture

**Source:** NASA SMAP
**URL:** https://nsidc.org/data/smap

---

## [pending] flood event labels

**Source:** NDMA / Uttarakhand SDMA reports, Bhuvan landslide inventory
**URL:** https://bhuvan.nrsc.gov.in