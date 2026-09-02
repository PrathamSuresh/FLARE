# FLARE — Data Sources

**Project:** FLARE (Flood Level Assessment & Rapid Early-warning)
**Problem Statement:** SIH26192 — Flash Flood Prediction System for Hilly Regions using Multi-Source Data
**Sponsoring Ministry:** Ministry of Home Affairs (NDRF, DM Division)

**Study area:** Chamoli district, Uttarakhand
**Bounding box:** 30.2–31.0 °N, 79.0–80.0 °E

**Configuration:** All spatial and temporal parameters are defined in `ml/config.py`. Changing the region requires editing that file and re-running the fetch scripts — no code changes. Note that the SRTM DEM must be downloaded manually for a new region.

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

## chamoli_soil_moisture.csv

**Source:** Copernicus ERA5-Land hourly reanalysis
**Access:** `cdsapi` Python package (`pip install cdsapi netcdf4`), free CDS account required
**URL:** https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
**Resolution:** ~9 km native, aggregated to 0.25° grid to match IMD rainfall
**Period:** 2010–2021, sampled at 00:00 and 12:00 UTC, averaged to daily
**Rows:** 87,660
**Columns:** date, lat, lon, soil_moisture_l1 (0–7 cm), soil_moisture_l2 (7–28 cm)
**Script:** `ml/fetch_soil_moisture.py`
**Citation:** Muñoz Sabater, J. (2019): ERA5-Land hourly data from 1950 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). https://doi.org/10.24381/cds.e2161bac. Accessed 2026-09-03
**Licence:** CC-BY
**Notes:** Requests are issued one year at a time — CDS rejects multi-year requests for this area as exceeding cost limits. Already-downloaded years are skipped on re-run. Raw `.nc` files excluded from repo via `.gitignore`.

**Why ERA5-Land and not NASA SMAP:** SMAP only became operational in 2015, which excludes the 2013 Kedarnath disaster — one of our two anchor labelling events. SMAP is also gridded at 36 km, coarser than our 25 km rainfall grid, which works against the hyper-local requirement. ERA5-Land covers 1950–present at ~9 km. It is a reanalysis product (model output constrained by observations) rather than a direct satellite measurement, which we note as a limitation.

---

## [pending] flood event labels

**Source:** NDMA / Uttarakhand SDMA reports, Bhuvan landslide inventory (NRSC), CWC discharge records
**URL:** https://bhuvan.nrsc.gov.in
**Purpose:** Target variable (`flood_occurred`) for supervised training. Anchor events include the 2013 Kedarnath disaster and the 2021 Chamoli disaster.
**Status:** Not yet acquired — this is the critical path for model training