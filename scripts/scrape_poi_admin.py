"""Authenticated scraper for the POI admin change-list.

Logs into the Django admin using credentials from a local .env, runs the
coffee/tea category pull across one or more lat/long pins (with full
pagination), and merges results into data/coffee_tea_raw/coffee_tea_master.csv
(deduped by Overture id).

Security:
- Credentials are read from .env (gitignored). Never hard-code or print them.
- Run locally via the shell; the admin sits behind login on your network.

Usage:
  pip install requests python-dotenv
  python scripts/scrape_poi_admin.py --pins pins.csv
  python scripts/scrape_poi_admin.py --pin "27.4945,-80.3383" --distance 10

`pins.csv` columns: label,latlog,distance_miles  (distance optional)
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Missing dependency: pip install requests python-dotenv", file=sys.stderr)
    raise

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data" / "coffee_tea_raw"
CHANGELIST_PATH = "/admin/poi_data/poidetail/"
LOGIN_PATH = "/accounts/login/"

ROW_RE = re.compile(r"<tr><td class=\"action-checkbox\".*?</tr>", re.DOTALL)
LINK_NAME_RE = re.compile(r'class="field-business_name"><a[^>]*>([^<]+)</a>')
FIELD_RE = re.compile(r'class="field-([^"]+)">([^<]*(?:<a[^>]*>[^<]*</a>)?[^<]*)</t[dh]>')
UUID_RE = re.compile(r'value="([0-9a-f-]{36})"')
CSRF_RE = re.compile(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"')

CSV_COLUMNS = [
    "id", "business_name", "business_address", "city", "state", "zipcode",
    "zipcode_full", "basic_category", "category_primary", "category_alternate",
    "taxonomy_primary", "confidence", "operating_status", "name_common",
    "brand_name_primary", "websites", "emails", "socials", "phone_num",
    "latitude", "longitude", "search_latlog", "search_distance_miles",
    "source_examples",
]

# Full form param set matching the staging PoiDetail filter builder. Empty
# fields are sent intentionally so the custom change-list parses the request
# (otherwise Django bounces it with ?e=1). This pulls the RAW coffee/tea
# universe: basic_category in {coffee_shop, tea_room} OR category_primary in
# {coffee_shop, tea_room, coffee_roastery}, no excludes, no confidence gate.
CATEGORY_PARAMS = {
    "apply_saved_filter": "",
    "update_saved_filter": "",
    "apply_filter": "1",
    "saved_filter_id": "",
    "max_results": "200",
    "min_confidence": "0",
    "address_line": "",
    "city": "",
    "state": "",
    "zipcode": "",
    "has_website": "",
    "operating_status": "open",
    "name_primary_include_values": "",
    "name_common_include_values": "",
    "basic_category_include_values": "coffee_shop\r\ntea_room\r\n",
    "category_primary_include_values": "coffee_shop\r\ntea_room\r\ncoffee_roastery\r\n",
    "category_alternate_include_values": "",
    "taxonomy_primary_include_values": "",
    "taxonomy_alternates_include_values": "",
    "name_primary_exclude_values": "",
    "name_common_exclude_values": "",
    "basic_category_exclude_values": "",
    "category_primary_exclude_values": "",
    "category_alternate_exclude_values": "",
    "taxonomy_primary_exclude_values": "",
    "taxonomy_alternates_exclude_values": "",
    "query_builder": "(basic_category_include or category_primary_include)\r\n",
}


def load_env() -> dict[str, str]:
    env_path = REPO_ROOT / ".env"
    values: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    for k in ("POI_ADMIN_BASE_URL", "POI_ADMIN_USERNAME", "POI_ADMIN_PASSWORD"):
        values.setdefault(k, os.environ.get(k, ""))
    missing = [k for k in ("POI_ADMIN_BASE_URL", "POI_ADMIN_USERNAME", "POI_ADMIN_PASSWORD") if not values.get(k)]
    if missing:
        print(f"Missing in .env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    return values


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value.strip())
    return "" if value == "-" else value


def login(session: requests.Session, base: str, user: str, pw: str) -> None:
    """Authenticate via django-allauth (/accounts/login/).

    The form posts to the same URL with fields: csrfmiddlewaretoken, login,
    password, remember-me.
    """
    r = session.get(base + LOGIN_PATH, timeout=30)
    r.raise_for_status()
    m = CSRF_RE.search(r.text)
    token = m.group(1) if m else session.cookies.get("csrftoken", "")
    r = session.post(
        base + LOGIN_PATH,
        data={
            "csrfmiddlewaretoken": token,
            "login": user,
            "password": pw,
            "remember-me": "on",
            "next": CHANGELIST_PATH,
        },
        headers={"Referer": base + LOGIN_PATH},
        timeout=30,
    )
    r.raise_for_status()
    # Confirm the session can actually reach the admin change-list.
    check = session.get(base + CHANGELIST_PATH, timeout=30)
    if "/login" in check.url or 'id="result_list"' not in check.text and "Select poi detail" not in check.text:
        print("Login failed — check credentials in .env", file=sys.stderr)
        sys.exit(1)


def parse_rows(page_html: str, latlog: str, distance: str, label: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row_html in ROW_RE.findall(page_html):
        rec = {"search_latlog": latlog, "search_distance_miles": distance, "source_examples": label}
        name_m = LINK_NAME_RE.search(row_html)
        if name_m:
            rec["business_name"] = html.unescape(name_m.group(1))
        id_m = UUID_RE.search(row_html)
        if id_m:
            rec["id"] = id_m.group(1)
        for fm in FIELD_RE.finditer(row_html):
            key, val = fm.group(1), clean(fm.group(2))
            if key == "business_name" and "business_name" in rec:
                continue
            rec[key] = val
        if rec.get("id"):
            rows.append(rec)
    return rows


def get_with_retry(
    session: requests.Session, url: str, params: dict[str, str],
    env: dict[str, str], base: str, attempts: int = 4,
) -> requests.Response:
    """GET with retry/backoff on transient errors; re-login on auth bounce."""
    delay = 2.0
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            r = session.get(url, params=params, timeout=90)
            if r.status_code in (500, 502, 503, 504):
                raise requests.exceptions.HTTPError(f"{r.status_code} transient")
            if "/login" in r.url:  # session expired -> re-auth and retry
                login(session, base, env["POI_ADMIN_USERNAME"], env["POI_ADMIN_PASSWORD"])
                raise requests.exceptions.HTTPError("re-login")
            r.raise_for_status()
            r.encoding = "utf-8"
            return r
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            if attempt < attempts:
                time.sleep(delay)
                delay *= 2
    raise last_exc if last_exc else RuntimeError("request failed")


def fetch_pin(
    session: requests.Session, base: str, latlog: str, distance: str, label: str,
    env: dict[str, str], pause: float = 0.4,
) -> list[dict[str, str]]:
    params = dict(CATEGORY_PARAMS)
    params["latlog"] = latlog
    params["distance_miles"] = distance
    collected: list[dict[str, str]] = []
    page = 1
    while True:
        page_params = dict(params)
        if page > 1:
            page_params["p"] = str(page)
        r = get_with_retry(session, base + CHANGELIST_PATH, page_params, env, base)
        rows = parse_rows(r.text, latlog, distance, label)
        if not rows:
            break
        collected.extend(rows)
        if 'class="end"' not in r.text or f"?p={page + 1}" not in r.text:
            break
        page += 1
        time.sleep(pause)
    return collected


def load_existing() -> dict[str, dict[str, str]]:
    csv_path = OUT_DIR / "coffee_tea_master.csv"
    records: dict[str, dict[str, str]] = {}
    if csv_path.exists():
        for row in csv.DictReader(csv_path.open(encoding="utf-8")):
            records[row["id"]] = row
    return records


def write_master(records: dict[str, dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = sorted(records.values(), key=lambda r: (r.get("state", ""), r.get("city", ""), r.get("business_name", "")))
    with (OUT_DIR / "coffee_tea_master.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    (OUT_DIR / "coffee_tea_master.json").write_text(
        json.dumps(all_rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def read_pins(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    pins: list[tuple[str, str, str]] = []
    if args.pins:
        for row in csv.DictReader(Path(args.pins).open(encoding="utf-8")):
            pins.append((row.get("label", row["latlog"]), row["latlog"], row.get("distance_miles") or args.distance))
    if args.pin:
        pins.append((args.label or args.pin, args.pin, args.distance))
    return pins


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pins", help="CSV file: label,latlog,distance_miles")
    ap.add_argument("--pin", help='Single pin "lat,lon"')
    ap.add_argument("--label", help="Label for single pin")
    ap.add_argument("--distance", default="10", help="Default radius miles")
    args = ap.parse_args()

    pins = read_pins(args)
    if not pins:
        print("Provide --pins file or --pin 'lat,lon'", file=sys.stderr)
        return 1

    env = load_env()
    base = env["POI_ADMIN_BASE_URL"].rstrip("/")
    session = requests.Session()
    login(session, base, env["POI_ADMIN_USERNAME"], env["POI_ADMIN_PASSWORD"])

    records = load_existing()
    before = len(records)
    failed: list[str] = []
    for idx, (label, latlog, distance) in enumerate(pins, 1):
        try:
            rows = fetch_pin(session, base, latlog.strip(), str(distance).strip(), label, env)
        except Exception as exc:  # noqa: BLE001 - keep going past a bad pin
            failed.append(label)
            print(f"[{idx}/{len(pins)}] {label}: FAILED ({exc}); skipping")
            continue
        new = 0
        for rec in rows:
            if rec["id"] not in records:
                records[rec["id"]] = rec
                new += 1
            else:
                prior = records[rec["id"]].get("source_examples", "")
                labels = {x for x in prior.split(";") if x} | {label}
                records[rec["id"]]["source_examples"] = ";".join(sorted(labels))
        print(f"[{idx}/{len(pins)}] {label}: fetched {len(rows)} rows, +{new} new (total {len(records)})")
        write_master(records)  # incremental save so a later crash never loses progress

    write_master(records)
    print(f"Master total: {len(records)} unique POIs (was {before})")
    if failed:
        print(f"Failed pins ({len(failed)}): {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
