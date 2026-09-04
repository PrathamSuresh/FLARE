"""
download_sentinel1.py — FLARE

Step 2 of Sentinel-1 acquisition: download the GRD scenes identified by
ml/fetch_sentinel1.py.

Reads data/sentinel1_candidates.csv and downloads the pre/post scene pair
for every event that is flood-caused AND has a usable same-track pair.
Scenes shared between events (e.g. 2019-06-08 and 2019-06-09, which fall
in the same revisit cycle) are downloaded once.

Downloads go to data/raw/sentinel1/ as .zip — add that path to .gitignore
alongside the other raw data.

CREDENTIALS
Set these as environment variables. Never put them in this file or commit
them; the repo is private but credentials in git are still a bad habit.

    PowerShell (this session only):
        $env:CDSE_USERNAME = "you@example.com"
        $env:CDSE_PASSWORD = "..."

    PowerShell (persistent):
        setx CDSE_USERNAME "you@example.com"
        setx CDSE_PASSWORD "..."

Register free at https://dataspace.copernicus.eu

SIZE
Roughly 1 GB per scene. Expect ~20 GB total. Check free disk before
starting. The script skips already-downloaded files, so it is safe to
interrupt and re-run.

Usage:
    python ml/download_sentinel1.py            # download everything usable
    python ml/download_sentinel1.py --dry-run  # list what would download
    python ml/download_sentinel1.py --event 2021-02-07   # single event

Requires: requests
"""

import argparse
import csv
import os
import sys
import time

import requests

# --- config -----------------------------------------------------------------
CANDIDATES_PATH = os.path.join("data", "sentinel1_candidates.csv")
OUTPUT_DIR = os.path.join("data", "raw", "sentinel1")

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
    "protocol/openid-connect/token"
)
DOWNLOAD_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products({id})/$value"

# CDSE access tokens are short-lived (~10 min). A 1 GB download can outlast
# one, so refresh before it expires rather than after a 401.
TOKEN_LIFETIME_MARGIN = 60  # seconds before expiry to refresh

CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB


class CDSESession:
    """Holds a CDSE token and refreshes it before expiry."""

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._token = None
        self._expires_at = 0
        self._refresh_token = None

    def _request_token(self, data):
        resp = requests.post(TOKEN_URL, data=data, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(
                f"CDSE auth failed ({resp.status_code}). "
                "Check CDSE_USERNAME / CDSE_PASSWORD.\n"
                f"{resp.text[:300]}"
            )
        payload = resp.json()
        self._token = payload["access_token"]
        self._refresh_token = payload.get("refresh_token")
        self._expires_at = time.time() + payload.get("expires_in", 600)

    def _login(self):
        self._request_token(
            {
                "client_id": "cdse-public",
                "username": self._username,
                "password": self._password,
                "grant_type": "password",
            }
        )

    def token(self):
        if self._token is None:
            self._login()
        elif time.time() > self._expires_at - TOKEN_LIFETIME_MARGIN:
            # Try a cheap refresh; fall back to a full login.
            try:
                self._request_token(
                    {
                        "client_id": "cdse-public",
                        "refresh_token": self._refresh_token,
                        "grant_type": "refresh_token",
                    }
                )
            except (RuntimeError, KeyError):
                self._login()
        return self._token

    def headers(self):
        return {"Authorization": f"Bearer {self.token()}"}


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def collect_scenes(path, event_filter=None):
    """
    Build a deduplicated {scene_id: scene_name} map from the candidates CSV,
    keeping only flood-caused events with a usable pair.
    """
    scenes = {}
    kept_events = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            verdict = row.get("verdict", "")
            is_flood = row.get("is_flood", "").strip().lower() == "true"
            if not is_flood:
                continue
            if not verdict.startswith(("GOOD", "MARGINAL")):
                continue
            if event_filter and row.get("event_date") != event_filter:
                continue

            kept_events.append(row.get("event_date"))
            for id_col, name_col in (
                ("pre_scene_id", "pre_scene"),
                ("post_scene_id", "post_scene"),
            ):
                sid = (row.get(id_col) or "").strip()
                name = (row.get(name_col) or "").strip()
                if sid and name:
                    scenes[sid] = name
    return scenes, kept_events


def download_scene(session, scene_id, scene_name, out_dir):
    """Download one scene, skipping if already present. Returns bytes fetched."""
    dest = os.path.join(out_dir, f"{scene_name}.zip")
    partial = dest + ".part"

    if os.path.exists(dest):
        print(f"  skip (exists)  {scene_name}")
        return 0

    resume_from = os.path.getsize(partial) if os.path.exists(partial) else 0

    headers = dict(session.headers())
    if resume_from:
        headers["Range"] = f"bytes={resume_from}-"
        print(f"  resuming at {human(resume_from)}  {scene_name}")
    else:
        print(f"  downloading    {scene_name}")

    url = DOWNLOAD_URL.format(id=scene_id)

    # CDSE redirects $value to a separate download host. requests strips the
    # Authorization header on cross-host redirects, so follow them by hand and
    # re-attach the token each hop.
    resp = None
    for _ in range(10):
        resp = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=120,
            allow_redirects=False,
        )
        if resp.status_code in (301, 302, 303, 307, 308):
            url = resp.headers["Location"]
            resp.close()
            headers = dict(session.headers())
            if resume_from:
                headers["Range"] = f"bytes={resume_from}-"
            continue
        break

    with resp:
        if resp.status_code in (401, 403):
            raise RuntimeError(
                f"Authorisation rejected ({resp.status_code}). "
                "Verify your CDSE email, then log in once at dataspace.copernicus.eu "
                "to accept the terms."
            )
        if resp.status_code == 416:
            os.replace(partial, dest)
            return 0
        resp.raise_for_status()

        total = resp.headers.get("Content-Length")
        total = int(total) + resume_from if total else None

        mode = "ab" if resume_from else "wb"
        fetched = resume_from
        last_report = time.time()

        with open(partial, mode) as fh:
            for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                fh.write(chunk)
                fetched += len(chunk)
                if time.time() - last_report > 5:
                    pct = f" ({100 * fetched / total:.0f}%)" if total else ""
                    print(f"    {human(fetched)}{pct}", end="\r", flush=True)
                    last_report = time.time()

    os.replace(partial, dest)
    print(f"    done {human(fetched)}                    ")
    return fetched


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="list, do not download")
    parser.add_argument("--event", help="only this event date, e.g. 2021-02-07")
    args = parser.parse_args()

    if not os.path.exists(CANDIDATES_PATH):
        sys.exit(f"{CANDIDATES_PATH} not found. Run ml/fetch_sentinel1.py first.")

    scenes, events = collect_scenes(CANDIDATES_PATH, args.event)
    if not scenes:
        sys.exit("No matching scenes. Check --event or the candidates CSV.")

    print(f"{len(events)} events -> {len(scenes)} unique scenes after dedupe")
    print(f"Estimated ~{len(scenes)} GB (scenes average roughly 1 GB)\n")

    if args.dry_run:
        for name in sorted(scenes.values()):
            print(f"  {name}")
        return

    username = os.environ.get("CDSE_USERNAME")
    password = os.environ.get("CDSE_PASSWORD")
    if not username or not password:
        sys.exit(
            "Set CDSE_USERNAME and CDSE_PASSWORD environment variables.\n"
            "See the docstring at the top of this file."
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    session = CDSESession(username, password)

    total_bytes = 0
    failures = []
    for i, (scene_id, scene_name) in enumerate(sorted(scenes.items(), key=lambda kv: kv[1]), 1):
        print(f"[{i}/{len(scenes)}]")
        try:
            total_bytes += download_scene(session, scene_id, scene_name, OUTPUT_DIR)
        except (requests.RequestException, RuntimeError) as exc:
            print(f"  FAILED {scene_name}: {exc}")
            failures.append(scene_name)

    print(f"\nFetched {human(total_bytes)} into {OUTPUT_DIR}")
    if failures:
        print(f"{len(failures)} failed — re-run to retry (completed scenes are skipped):")
        for name in failures:
            print(f"  {name}")


if __name__ == "__main__":
    main()