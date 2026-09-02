# FLARE — Data Sources

**Project:** FLARE (Flood Level Assessment & Rapid Early-warning)
**Problem Statement:** SIH26192 — Flash Flood Prediction System for Hilly Regions using Multi-Source Data
**Sponsoring Ministry:** Ministry of Home Affairs (NDRF, DM Division)

**Study area:** Chamoli district, Uttarakhand
**Bounding box:** 30.2–31.0 °N, 79.0–80.0 °E

All datasets are clipped to this bounding box. The pipeline is parameterised by bounding box, so re-running the scripts with different coordinates extends FLARE to any other hilly district.

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
**Citation:** India Meteorological Department (IMD), Pune. Gridded daily rainfall data (0.25° × 0.25°). Accessed 2026-09-02 via `imdlib`.
**Notes:** Raw `.grd` files excluded from repo via `.gitignore`. Values below -100 removed as no-data sentinels.

---

## chamoli_terrain.csv

**Source:** SRTM 30m Digital Elevation Model (SRTM_GL1)
**Access:** OpenTopography portal (manual download, GeoTIFF)
**URL:** https://portal.opentopography.org/raster?opentopoID=OTSRTM.082015.4326.1
**Resolution:** 30m native, aggregated to 0.25° grid to match IMD rainfall
**Grid cells:** 20 (aggregated from 10,368,000 SRTM pixels)
**Columns:** lat, lon, elevation (m), slope (deg), slope_max (deg), aspect (deg)
**Script:** `ml/fetch_terrain.py`
**Citation:** NASA Shuttle Radar Topography Mission (SRTM) (2013). Shuttle Radar Topography Mission (SRTM) Global. Distributed by OpenTopography. https://doi.org/10.5069/G9445JDF. Accessed 2026-09-02
**Notes:** Slope and aspect are derived from elevation, not downloaded. `slope_max` retained alongside mean slope because the steepest point in a cell is more relevant to flash flood risk than the average. Raw GeoTIFF excluded from repo via `.gitignore`.

---

## [pending] soil moisture

**Source:** NASA SMAP (Soil Moisture Active Passive)
**URL:** https://nsidc.org/data/smap
**Purpose:** Satellite-derived substitute for the physical soil moisture sensors named in the problem statement. Saturated soil is a primary driver of flash flooding on steep terrain.
**Status:** Not yet acquired

---

## [pending] flood event labels

**Source:** NDMA / Uttarakhand SDMA reports, Bhuvan landslide inventory (NRSC), CWC discharge records
**URL:** https://bhuvan.nrsc.gov.in
**Purpose:** Target variable (`flood_occurred`) for supervised training. Anchor events include the 2013 Kedarnath disaster and the 2021 Chamoli disaster.
**Status:** Not yet acquired — this is the critical path for model training