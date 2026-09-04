# 1. Add to .gitignore
data/raw/sentinel1/

# 2. Register free at dataspace.copernicus.eu, then:
$env:CDSE_USERNAME = "your@email"
$env:CDSE_PASSWORD = "yourpassword"

# 3. See what it'll pull, no download
python ml/download_sentinel1.py --dry-run

# 4. Test on one event first
python ml/download_sentinel1.py --event 2021-02-07

# 5. Then the rest
python ml/download_sentinel1.py

# Sentinel-1 data — what it is and who needs to download it

**Short version:** Only the Data/GIS lead needs the raw scenes. Everyone else
waits for the processed output, which is a small CSV that will be committed to
the repo like every other dataset.

---

## What Sentinel-1 actually is

Every other dataset in FLARE so far — rainfall, terrain, soil moisture — arrived
as a **table**. Rows and columns, straight into a CSV.

Sentinel-1 is not that. It is a **radar image**, a raster.

One scene is roughly 25,000 × 16,000 pixels, about 400 million values, stored
compressed as roughly 1 GB. Each pixel is not a rainfall figure or an elevation;
it is *how much microwave energy bounced back from that patch of ground*.

Do not try to convert a scene to CSV. At ~30 bytes per row for lat, lon, value,
400 million rows is about 12 GB — ten times larger than the raster it came from.
Raster formats exist precisely so grids of numbers are not stored as text.

## Why radar, and not a normal satellite photo

Radar supplies its own illumination and microwaves pass through cloud, so
Sentinel-1 images through monsoon cloud and at night. Optical satellites would
show us a white cloud top on exactly the days we care about.

The flood signal works like this:

- Rough surfaces (soil, vegetation, buildings) scatter energy back to the
  satellite and appear **bright**
- Calm water is smooth, reflects the pulse away like a mirror, and appears
  **dark**

So flooding shows up as a patch that was bright before the event and dark after.
That is what change detection looks for.

## Why pre/post scenes must share a relative orbit

Radar looks sideways, roughly 30-45° off vertical, not straight down. In steep
Himalayan terrain the slope facing the radar is compressed and bright (layover)
and the slope facing away receives nothing (radar shadow).

Sentinel-1 passes over Chamoli on both ascending (~12:47 UTC) and descending
(~00:35 UTC) tracks, viewing the valley from opposite sides. Difference an
ascending scene against a descending one and every slope flips brightness — with
no flood at all. The result is spurious change across the whole district.

`ml/fetch_sentinel1.py` therefore groups scenes by relative orbit, computed from
the absolute orbit number in the filename, and only pairs within a group. This
is why the usable event count is 11 rather than 14.

## The pipeline

```
pre-event scene (~1 GB raster)
post-event scene (~1 GB raster)
        |
        v
  difference the two, threshold the result
        |
        v
  binary flood mask (still a raster)
        |
        v
  overlay ward/village boundaries (GeoPandas)
        |
        v
  data/chamoli_ward_flood_labels.csv   <- a few KB, committed to the repo
```

The output is a small table, something like:

```
event_date,ward_id,flooded_fraction
2021-02-07,UK-CHM-042,0.37
2021-02-07,UK-CHM-043,0.00
```

Roughly 11 events × ~50 wards, so a few hundred rows. That file is the actual
deliverable. It becomes the target variable for the ward-level model.

## Who needs to download the raw scenes

| Role | Needs raw scenes? | What they need instead |
|---|---|---|
| Data/GIS lead | **Yes** | Runs change detection, produces the labels CSV |
| ML engineer | No | The labels CSV, joined to rainfall/terrain/soil moisture |
| Backend | No | The API contract |
| Frontend ×2 | No | The API contract |
| Integration/presentation | No | The labels CSV and output maps |

One person downloads once. `data/raw/sentinel1/` is in `.gitignore` — 20 GB must
never enter git, and GitHub rejects single files over 100 MB regardless.

Same pattern we already use: the raw `.grd` rainfall files in `rain/` are
ignored, `chamoli_rainfall_2010_2021.csv` is committed.

If somebody genuinely needs the raw scenes later, copy the folder over the local
network or a USB drive rather than re-pulling 20 GB from Europe.

## Running the download

```powershell
# 1. Register free at dataspace.copernicus.eu, verify the email,
#    and log in once through the browser to accept the terms.
#    Each person needs their own account; shared logins get rate-limited.

# 2. Credentials as environment variables — never in a file, never committed
$env:CDSE_USERNAME = "you@example.com"
$env:CDSE_PASSWORD = "..."

# 3. List what would be pulled, no download, no auth needed
python ml/download_sentinel1.py --dry-run

# 4. Test on one event before committing to 20 GB
python ml/download_sentinel1.py --event 2021-02-07

# 5. The rest. Safe to interrupt — completed scenes are skipped on re-run
python ml/download_sentinel1.py
```

Expect roughly 1 GB per scene, ~20 GB total, an hour or two on a home
connection. It is unattended; run it in a separate terminal and carry on.

### Known gotcha, already fixed

CDSE redirects the download endpoint to a separate host. The `requests` library
strips the `Authorization` header on cross-host redirects as a security measure,
so the redirected request arrives with no token and returns 401. The script now
follows redirects manually and re-attaches the token on each hop. If you see
"Authorisation rejected", check the email is verified and that you have logged
in through the browser once.

## Working with rasters

Not pandas. The GIS lead will need:

- `rasterio` — open and read the scenes, the raster equivalent of `read_csv`
- `numpy` — the differencing and thresholding
- `geopandas` — overlay ward boundaries on the flood mask

**Install via conda, not pip.** `rasterio` pulls in GDAL, the same dependency
that forced conda for GeoPandas on Windows. pip will produce a broken install.

## Current status

- 37 dated Chamoli events in the India Flood Inventory, 15 after Sentinel-1
  began in April 2014
- 11 are flood-caused **and** have a valid same-track pre/post pair
- Two pure landslide events are flagged and excluded — a landslide has no
  inundation extent to map
- 2019-06-08 and 2019-06-09 fall inside one revisit cycle, share scenes, and
  cannot be separated. Treat them as **one** labelling unit, so roughly 10
  distinct events
- 2013 Kedarnath predates Sentinel-1 entirely and can never receive a
  SAR-derived label. If it is needed for the pitch, use published analyses of
  the event instead

Candidate scenes and verdicts per event: `data/sentinel1_candidates.csv`