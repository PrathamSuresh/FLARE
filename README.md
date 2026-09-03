# FLARE

**Flood Level Assessment & Rapid Early-warning**

A ward-level flash flood prediction and early-warning system for hilly regions.

| | |
|---|---|
| **Problem Statement** | SIH26192 — Flash Flood Prediction System For Hilly Regions Using Multi-Source Data |
| **Theme** | Disaster Management |
| **Category** | Software |
| **Ministry** | Ministry of Home Affairs (NDRF, DM Division) |
| **Team ID** | BMS/SIH2026/138 |
| **Event** | Smart India Hackathon 2026 |

---

## The problem

Flash floods in hilly regions develop over hours, driven by rainfall, river conditions, soil saturation and terrain interacting on short timescales. Existing warnings are issued at district level — they tell authorities that flooding is likely somewhere in the district, but not **which villages or wards will actually be affected**. That gap turns a warning into a guess about where to send resources.

## The approach

FLARE predicts risk at two levels.

**Level 1 — District risk.** Rainfall, soil moisture, terrain and river discharge feed an ML model that assesses overall flash-flood risk for the study region.

**Level 2 — Ward risk.** Each ward gets its own independent probability, computed from current conditions plus that ward's fixed geography — elevation, slope, drainage, distance from river. This is not a district score divided among wards; every ward is predicted separately.

The ward-level labels behind Level 2 are built from history. Sentinel-1 SAR imagery for past floods gives the actual inundation footprint, overlaid on ward GIS boundaries to determine which wards flooded and by how much. Sentinel-1 does double duty — it generates the historical training labels, and after deployment validates live predictions against observed flood extent.

**Case study:** Chamoli district, Uttarakhand. The pipeline is parameterised by bounding box, so it extends to other hilly districts.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React.js, Leaflet.js |
| Backend | FastAPI (Python) |
| ML | scikit-learn, XGBoost, GeoPandas, Rasterio |
| Database | PostgreSQL + PostGIS |
| Tooling | conda, Docker, Git |

---

## Repository

```
backend/    FastAPI service      → see backend/README.md
frontend/   React + Leaflet      → see frontend/README.md
ml/         Fetch scripts, models
data/       Processed datasets   → see data/README.md
docs/       Design notes, methodology, pitch material
```

Setup instructions live in each component's own README. Dataset provenance and citations are in [`data/README.md`](data/README.md).

---

## Status

Environment configured, API endpoints scaffolded, and the rainfall, soil moisture, terrain and flood-event datasets acquired for Chamoli. Sentinel-1 flood extent processing and ward GIS boundaries are the current critical path.

---

## Team

Six members: Data/GIS, ML, Backend/API, two Frontend, and Integration/Presentation. Workstreams coordinate through a shared API contract agreed before implementation.
