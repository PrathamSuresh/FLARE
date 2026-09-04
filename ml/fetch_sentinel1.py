"""
fetch_sentinel1.py — FLARE

Step 1 of Sentinel-1 acquisition: find which flood events actually have
usable SAR coverage before downloading anything.

Queries the Copernicus Data Space Ecosystem (CDSE) OData catalogue for
Sentinel-1 GRD scenes intersecting the Chamoli bounding box, within a
search window around each flood event date from the India Flood Inventory.

IMPORTANT — same-track pairing:
Change detection is only valid between scenes acquired from the SAME
relative orbit. Sentinel-1 passes overhead on both ascending (~12:47 UTC
here) and descending (~00:35 UTC) tracks, viewing the terrain from
opposite sides. Differencing across tracks measures viewing geometry, not
flooding — and in steep terrain, layover and radar shadow fall in
completely different places, producing spurious "change" everywhere.
This script therefore groups scenes by relative orbit and only pairs
within a group.

Outputs data/sentinel1_candidates.csv — one row per event, with the best
same-track pre/post pair found.

No download happens here. This is a cheap metadata call that tells you
which events are labelable at all.

Usage:
    python ml/fetch_sentinel1.py

Requires: requests (pip install requests)
No authentication needed for catalogue search — only for download.
"""

import csv
import os
import re
from datetime import datetime, timedelta

import requests

# --- config -----------------------------------------------------------------
# Mirrors ml/config.py. Import from there instead once this is wired in.
BBOX = {
    "lat_min": 30.2,
    "lat_max": 31.0,
    "lon_min": 79.0,
    "lon_max": 80.0,
}

# How far either side of an event date to look for acquisitions.
# Wider than before: the same-track constraint means a 6-12 day effective
# revisit, so a narrow window can miss a valid pair entirely.
SEARCH_WINDOW_DAYS = 30

# A post-event pass beyond this is unlikely to still see standing water.
GOOD_POST_GAP = 3
MARGINAL_POST_GAP = 7

INVENTORY_PATH = os.path.join("data", "India_Flood_Inventory_v3.csv")
OUTPUT_PATH = os.path.join("data", "sentinel1_candidates.csv")

# Sentinel-1A launched 2014-04-03. Nothing before this exists.
SENTINEL1_START = datetime(2014, 4, 3)

CDSE_ODATA = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

# Relative orbit = ((absolute_orbit - offset) mod 175) + 1
# Offset differs per satellite.
ORBIT_OFFSET = {"S1A": 73, "S1B": 27, "S1C": 172, "S1D": 73}

SCENE_RE = re.compile(
    r"^(?P<sat>S1[ABCD])_(?P<mode>\w{2})_(?P<prod>\w{4})_(?P<pol>\w{4})_"
    r"(?P<start>\d{8}T\d{6})_(?P<stop>\d{8}T\d{6})_(?P<orbit>\d{6})_"
)


def parse_scene(name):
    """Extract satellite, polarisation and relative orbit from a scene name."""
    m = SCENE_RE.match(name)
    if not m:
        return None
    sat = m.group("sat")
    abs_orbit = int(m.group("orbit"))
    offset = ORBIT_OFFSET.get(sat)
    if offset is None:
        return None
    rel_orbit = ((abs_orbit - offset) % 175) + 1
    return {"sat": sat, "pol": m.group("pol"), "rel_orbit": rel_orbit}


def load_chamoli_events(path):
    """Pull dated Chamoli events from the India Flood Inventory."""
    events = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            haystack = f"{row.get('Location', '')} {row.get('Districts', '')}".lower()
            if "chamoli" not in haystack:
                continue
            try:
                start = datetime.strptime(row["Start Date"].split(" ")[0], "%d-%m-%Y")
            except (ValueError, KeyError):
                continue
            if start < SENTINEL1_START:
                continue
            cause = (row.get("Main Cause", "") or "").strip()
            events.append(
                {
                    "uei": row.get("UEI", ""),
                    "date": start,
                    "cause": cause,
                    # Landslides with no flood component have no inundation
                    # extent to map — flag them so they can be filtered.
                    "is_flood": any(
                        k in cause.lower()
                        for k in ("flood", "rain", "burst", "glacier")
                    ),
                    "fatalities": (row.get("Human fatality", "") or "").strip(),
                }
            )
    events.sort(key=lambda e: e["date"])
    return events


def bbox_wkt(b):
    """CDSE expects a closed WKT polygon, lon lat order."""
    return (
        "POLYGON(("
        f"{b['lon_min']} {b['lat_min']},"
        f"{b['lon_max']} {b['lat_min']},"
        f"{b['lon_max']} {b['lat_max']},"
        f"{b['lon_min']} {b['lat_max']},"
        f"{b['lon_min']} {b['lat_min']}"
        "))"
    )


def query_acquisitions(start, end, bbox):
    """List Sentinel-1 GRD scenes over the bbox between two dates."""
    flt = (
        "Collection/Name eq 'SENTINEL-1' "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;{bbox_wkt(bbox)}') "
        f"and ContentDate/Start gt {start.strftime('%Y-%m-%dT00:00:00.000Z')} "
        f"and ContentDate/Start lt {end.strftime('%Y-%m-%dT00:00:00.000Z')} "
        "and contains(Name,'GRD')"
    )
    resp = requests.get(
        CDSE_ODATA,
        params={"$filter": flt, "$orderby": "ContentDate/Start asc", "$top": 200},
        timeout=60,
    )
    resp.raise_for_status()

    scenes = []
    for item in resp.json().get("value", []):
        name = item.get("Name", "")
        meta = parse_scene(name)
        if meta is None:
            continue
        raw = item.get("ContentDate", {}).get("Start", "")
        try:
            acquired = datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue
        scenes.append({"id": item.get("Id"), "name": name, "acquired": acquired, **meta})
    return scenes


def best_same_track_pair(scenes, event_date):
    """
    Find the pre/post pair sharing a relative orbit that minimises the
    post-event gap. Returns (pre, post, rel_orbit) or (None, None, None).
    """
    by_orbit = {}
    for s in scenes:
        by_orbit.setdefault(s["rel_orbit"], []).append(s)

    best = None
    for rel_orbit, group in by_orbit.items():
        before = [s for s in group if s["acquired"] < event_date]
        after = [s for s in group if s["acquired"] > event_date]
        if not before or not after:
            continue
        pre = max(before, key=lambda s: s["acquired"])
        post = min(after, key=lambda s: s["acquired"])
        post_gap = (post["acquired"] - event_date).days
        if best is None or post_gap < best[3]:
            best = (pre, post, rel_orbit, post_gap)

    if best is None:
        return None, None, None
    return best[0], best[1], best[2]


def main():
    events = load_chamoli_events(INVENTORY_PATH)
    print(f"{len(events)} Chamoli events in the Sentinel-1 era (2014-04-03 onward)\n")

    results = []
    for ev in events:
        window_start = ev["date"] - timedelta(days=SEARCH_WINDOW_DAYS)
        window_end = ev["date"] + timedelta(days=SEARCH_WINDOW_DAYS)

        try:
            scenes = query_acquisitions(window_start, window_end, BBOX)
        except requests.RequestException as exc:
            print(f"  {ev['date'].date()}  query failed: {exc}")
            continue

        pre, post, rel_orbit = best_same_track_pair(scenes, ev["date"])

        if post is None:
            verdict = "NO SAME-TRACK PAIR"
            pre_gap = post_gap = None
        else:
            pre_gap = (ev["date"] - pre["acquired"]).days
            post_gap = (post["acquired"] - ev["date"]).days
            if post_gap <= GOOD_POST_GAP:
                verdict = "GOOD"
            elif post_gap <= MARGINAL_POST_GAP:
                verdict = "MARGINAL"
            else:
                verdict = "LIKELY TOO LATE"

        # Mixed polarisation between pre and post also degrades comparison.
        pol_note = ""
        if pre and post and pre["pol"] != post["pol"]:
            pol_note = f"  [pol mismatch {pre['pol']}/{post['pol']}]"

        if not ev["is_flood"]:
            verdict += " (non-flood cause)"

        orbit_str = f"orbit={rel_orbit}" if rel_orbit else "orbit=--"
        print(
            f"  {ev['date'].date()}  scenes={len(scenes):3d}  {orbit_str:<10}  "
            f"pre=-{pre_gap if pre_gap is not None else '?'}d  "
            f"post=+{post_gap if post_gap is not None else '?'}d  "
            f"{verdict}{pol_note}   {ev['cause'][:36]}"
        )

        results.append(
            {
                "uei": ev["uei"],
                "event_date": ev["date"].date(),
                "cause": ev["cause"],
                "is_flood": ev["is_flood"],
                "fatalities": ev["fatalities"],
                "scenes_in_window": len(scenes),
                "rel_orbit": rel_orbit if rel_orbit else "",
                "pre_acquired": pre["acquired"].date() if pre else "",
                "pre_gap_days": pre_gap if pre_gap is not None else "",
                "pre_scene": pre["name"] if pre else "",
                "pre_scene_id": pre["id"] if pre else "",
                "post_acquired": post["acquired"].date() if post else "",
                "post_gap_days": post_gap if post_gap is not None else "",
                "post_scene": post["name"] if post else "",
                "post_scene_id": post["id"] if post else "",
                "pol_mismatch": bool(pol_note),
                "verdict": verdict,
            }
        )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    usable = [
        r
        for r in results
        if r["is_flood"] and r["verdict"].startswith(("GOOD", "MARGINAL"))
    ]
    print(f"\nWrote {OUTPUT_PATH}")
    print(f"{len(usable)} events are flood-caused AND have a usable same-track pair")
    print(
        "\nNote: events within one revisit cycle of each other (e.g. 2019-06-08 "
        "and 2019-06-09) share scenes and cannot be separated. Treat them as one "
        "labelling unit."
    )


if __name__ == "__main__":
    main()