# FLARE — Data Sources

**Project:** FLARE (Flood Level Assessment & Rapid Early-warning)
**Problem Statement:** SIH26192 — Flash Flood Prediction System for Hilly Regions using Multi-Source Data
**Sponsoring Ministry:** Ministry of Home Affairs (NDRF, DM Division)

**Study area:** Chamoli district, Uttarakhand
**Bounding box:** 30.2–31.0 °N, 79.0–80.0 °E

**Configuration:** All spatial and temporal parameters are defined in `ml/config.py`. Changing the region requires editing that file and re-running the fetch scripts — no code changes. Note that the SRTM DEM must be downloaded manually for a new region.

All datasets are clipped to this bounding box. The pipeline is parameterised by bounding box, so re-running the scripts with different coordinates extends FLARE to any other hilly district.

**Environment:** one venv, plain pip. `rasterio` and `geopandas` install cleanly from prebuilt Windows wheels — the earlier "GDAL requires conda on Windows" rule is out of date and conda is not needed for this project.

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

**Why ERA5-Land and not NASA SMAP:** SMAP only became operational in 2015, which excludes the 2013 Kedarnath disaster. SMAP is also gridded at 36 km, coarser than our 25 km rainfall grid, which works against the hyper-local requirement. ERA5-Land covers 1950–present at ~9 km. It is a reanalysis product (model output constrained by observations) rather than a direct satellite measurement, which we note as a limitation.

---

## vb_soi_uk.GeoJSON

**Source:** Survey of India (SOI) — Uttarakhand Village Boundary Database

**Access:** Manual download (GeoJSON)

**Coverage:** Uttarakhand

**Format:** GeoJSON

**Native CRS:** **EPSG:7755** (WGS 84 / India NSF Lambert Conformal Conic — projected, in metres)

**Purpose:** Administrative/spatial boundary layer used to define the village-level prediction units for FLARE.

**Current use:** The complete Uttarakhand village-boundary dataset is retained in the repository. Chamoli villages have been extracted programmatically into `data/gis/chamoli_villages.geojson` (see below).

**File location:**
`data/boundaries/uttarakhand_villages/vb_soi_uk_geojson/vb_soi_uk.GeoJSON`

**Notes:** This dataset contains village boundaries for Uttarakhand rather than only Chamoli. Keeping the complete dataset allows FLARE to be extended to other Uttarakhand districts without acquiring a new boundary dataset.

**CRS warning:** the source is EPSG:7755 while every other FLARE dataset (IMD grid, SRTM, Sentinel-1 footprints, the `config.py` bounding box) is EPSG:4326. Reprojection is mandatory — overlaying without it produces silently misaligned geometry rather than an error.

---

## chamoli_villages.geojson

**Derived from:** `vb_soi_uk.GeoJSON`

**Processing:** reprojected EPSG:7755 → **EPSG:4326**, then clipped to the study bounding box (30.2–31.0 °N, 79.0–80.0 °E)

**Village polygons:** **1,158**

**File location:** `data/gis/chamoli_villages.geojson`

**Purpose:** the prediction units. Village-level risk scores are produced per polygon.

**Open issue — resolution mismatch.** Predictors sit on a 0.25° grid, roughly **20 cells for the whole district**, against 1,158 village polygons. Many villages will therefore share identical rainfall and soil-moisture values; terrain (elevation, slope, distance to river) is what differentiates them. Worth testing whether WRIS sub-basins are a better prediction unit than villages, since in steep terrain water follows catchments rather than administrative lines.

---

## river_discharge_tele_hr_cwc_uk_1970_2025.csv

**Source:** Central Water Commission (CWC), Government of India

**Access:** Manual download (CSV)

**Coverage:** CWC telemetry river-discharge observations for Uttarakhand stations

**Rows:** 364,868 total; **139,864 for Chamoli**

**Columns:** Station, Agency, State, District, Tehsil, Block, Village, River, Basin, Tributary, Latitude, Longitude, Data Acquisition Time, Telemetry Hourly River Water Discharge (m3/sec), and related station metadata

**Temporal resolution:** 15-minute observations

**Actual data coverage (verified):** **01-01-2024 to 31-12-2024 for Chamoli.** The filename says 1970–2025, but the Chamoli records span a single calendar year.

**Chamoli coverage:** 2 CWC stations — Karnaprayag (P) and Lambagarh

**Purpose:** **Real-time river discharge input and threshold-calibration baseline.**

**Important — no overlap with historical events.** Coverage begins 2024-01-01; the most recent flood event in the inventory is 2023-08-26. This dataset therefore **cannot be used to reconstruct conditions preceding historical floods**. It is a live input, not a historical training feature.

**Planned use:**

- Live discharge and rate-of-rise as a real-time risk signal. Rate of rise is one of the strongest flash-flood indicators available.
- One year of observations to establish seasonal normals for these two stations, so alert thresholds are grounded in observed behaviour rather than guessed.

**Derived features planned (real-time):**

- Current discharge
- Discharge 1 / 3 / 6 / 12 / 24 hours before
- Discharge change over 1 / 3 / 6 hours
- Maximum discharge over recent time windows

**Notes:** The filename describes the dataset as `tele_hr`, but the downloaded records are observed at 15-minute intervals (e.g. 07:00, 07:15, 07:30, 07:45). The dataset provides river discharge, not river water level; a separate water-level dataset may therefore be required if water-level features are retained in the final model. `District LGD Code` (47 for Chamoli) allows a clean join to the flood inventory's `District_LGD_Codes`.

**File location:**
`data/river_discharge_tele_hr_cwc_uk_1970_2025.csv`

---

---LABELS

## India_Flood_Inventory_v3.csv

**Source:** India Flood Inventory (IFI) v3 — HydroSense Lab, IIT Delhi, in collaboration with IMD
**Access:** Zenodo (open download)
**URL:** https://zenodo.org/records/16994648
**DOI (all versions):** https://doi.org/10.5281/zenodo.4742142
**Coverage:** All-India, 1967–2023
**Rows:** 6,876 events total; 121 mention Uttarakhand, 37 mention Chamoli
**Columns:** UEI, Start Date, End Date, Duration(Days), Main Cause, Location, Districts, State, Latitude, Longitude, Severity, Area Affected, Human fatality, Human injured, Human Displaced, Animal Fatality, Description of Casualties/injured, Extent of damage, Event Source, Event Source ID, District_LGD_Codes, State_Codes
**Purpose:** Event **dates**, used to validate that our risk score would have crossed threshold ahead of known floods. Anchors the pre-event condition reconstruction in the rainfall, terrain, and soil moisture datasets.
**Citation:** Saharia, M., Jain, A., Baishya, R.R., Haobam, S., Sreejith, O.P., Pai, D.S., Rafieeinasab, A. (2021). India flood inventory: creation of a multi-source national geospatial database to facilitate comprehensive flood research. *Natural Hazards* 108, 619–633. https://doi.org/10.1007/s11069-021-04698-6
**Licence:** CC-BY-NC 4.0 — non-commercial only. Fine for SIH; would require permission for any commercial deployment.
**Accessed:** 2026-09-05

**Major events present:**
- 2013 — Kedarnath disaster
- 2021-02-07 — Nandadevi glacier break at Joshimath (70 fatalities)

Note that 2013 Kedarnath predates Sentinel-1A (launched April 2014) and can never receive a SAR-derived spatial label.

### Limitations

**No coordinates anywhere.** Latitude and Longitude are empty for **all 6,876 rows**, not only the Chamoli ones. This dataset gives event *timing*, not spatial extent.

**Cause field is mixed.** `Main Cause` contains landslides, cloudbursts, and glacier events alongside floods (e.g. the 2016-05-08, 2017-05-20 and 2021-07-11 Chamoli entries are landslides). Filter before treating rows as flood events.

**District granularity only.** `Districts` is the finest spatial resolution available; no ward or village breakdown. `District_LGD_Codes` allows a clean join to LGD-coded datasets including the CWC discharge file.

**Sentinel-1 era subset is small.** **15** Chamoli events fall after April 2014, when Sentinel-1 imagery begins. Of those, 11 are flood-caused with valid same-track imagery; merging 2019-06-08 and 2019-06-09 (one revisit cycle apart, sharing scenes) gives ~10 distinct events.

---

## sentinel1_candidates.csv

**Source:** Copernicus Data Space Ecosystem (CDSE) catalogue
**Access:** OData API — no authentication required for catalogue search
**URL:** https://dataspace.copernicus.eu
**Script:** `ml/fetch_sentinel1.py`
**File location:** `data/sentinel1_candidates.csv`
**Columns:** uei, event_date, cause, is_flood, fatalities, scenes_in_window, rel_orbit, pre/post acquisition dates, scene names and IDs, pol_mismatch, verdict

**Purpose:** identifies which Chamoli flood events have usable Sentinel-1 coverage — the nearest same-track pre/post scene pair for each event.

**Result:** of the 15 post-April-2014 Chamoli events, **11 are flood-caused and have a valid same-track pre/post pair**, with post-event passes mostly 0–3 days after the event.

**Same-track constraint — do not remove.** Change detection is only valid between scenes acquired on the same relative orbit. Sentinel-1 passes over Chamoli on both ascending (~12:47 UTC) and descending (~00:35 UTC) tracks, viewing the terrain from opposite sides. Differencing across tracks measures viewing geometry rather than ground change: in steep terrain, layover and radar shadow fall in completely different places and every slope flips brightness. The script derives relative orbit from the absolute orbit number in the scene filename as `((orbit - offset) % 175) + 1` and pairs only within a group. An earlier version ignored this and reported 14 "usable" events, most of which were invalid.

**Raw scenes:** downloaded via `ml/download_sentinel1.py` into `data/raw/sentinel1/` (gitignored, ~1 GB per scene). The 2021-02-07 pair is on disk, 2.7 GB. Requires a free CDSE account with credentials supplied through `CDSE_USERNAME` / `CDSE_PASSWORD` environment variables — never committed. See `docs/NOTESAbtDwndldingSentinel1data.md`.

---

## ward-level spatial flood labels — tested, not achievable

**Attempted source:** Sentinel-1 GRD change detection + village GIS boundaries
**Script:** `ml/gee_change_detection.js` (Google Earth Engine, `COPERNICUS/S1_GRD`)
**Status:** **Tested and unsuccessful in this terrain. Not on the critical path.**

SAR-derived inundation mapping was tested on two events:

- **2021-02-07 (Joshimath):** detections scattered uniformly across the district, including snowfields above 4,000 m. The event was a rock-and-ice avalanche that became a debris flow — material passed through in minutes leaving no standing water to detect. February snow cover also alters backscatter in the same direction as water.
- **2019-08-08 (monsoon):** identical result. Uniform speckle across the change image, no coherent structure along the Rishiganga or Dhauliganga valleys.

Masks applied and still insufficient: permanent water (JRC Global Surface Water), slope < 15°, elevation < 3,000 m, focal-median despeckling, same-track pairing.

**Interpretation.** SAR flood mapping is well established on flat floodplains where water spreads out and persists for days. Chamoli is a steep headwater catchment: floods are narrow, fast, drained within hours, and terrain-induced backscatter variability is large. Recorded as a negative result rather than tuning thresholds until noise happens to fall in the right place.

**Consequence.** FLARE uses **threshold-based risk scoring** — the approach originally chosen precisely because verified flood-extent labels are hard to source. Validation is against event **timing** (did conditions cross threshold ahead of each of the ~10 known events?) rather than against mapped extent.

**Untested:** 2 of 11 events, both under difficult conditions. The 2023 monsoon events sit lower in the valley where flooding may be broader and slower — worth an hour if someone has spare time.

---

## [outstanding] real-time data feed

**Source:** Open-Meteo (weather forecasts + GloFAS river discharge forecasts)
**Access:** free, no signup
**Status:** **Not yet started — this is the actual critical path.**

Every dataset above is historical, ending 2021–2024. An early-warning system needs current conditions. Until this exists, FLARE analyses the past rather than warning about the present.

IMD API whitelisting and expanded CWC access continue in parallel.