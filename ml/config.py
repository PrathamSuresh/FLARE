"""
Region configuration for FLARE.

To extend FLARE to a different hilly district, change REGION_NAME and the
bounding box below, then re-run the fetch scripts in ml/. No other code
changes are required.
"""

REGION_NAME = "chamoli"

# Bounding box (WGS84 decimal degrees)
LAT_MIN, LAT_MAX = 30.2, 31.0
LON_MIN, LON_MAX = 79.0, 80.0

# Temporal range for all datasets
YEAR_START, YEAR_END = 2010, 2021

# Master grid resolution (degrees). Matches IMD rainfall native resolution;
# all other sources are aggregated onto this grid.
GRID_RES = 0.25

# ERA5 / CDS expects [North, West, South, East]
CDS_AREA = [LAT_MAX, LON_MIN, LAT_MIN, LON_MAX]


def out_path(name: str) -> str:
    """Standard output path for a processed dataset."""
    return f"data/{REGION_NAME}_{name}.csv"