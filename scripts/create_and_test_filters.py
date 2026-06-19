"""Create the 8 `-cursor` saved filters in the PoiDetail admin, then live-test
each one across multiple US locations.

Creation reproduces the change-list "Save as New Filter" action (a GET to the
change-list with `save_filter_name` set and all filter fields populated).
Testing applies each saved filter (`apply_saved_filter=1` + `saved_filter_id`)
at several pins, counts results, and scans for leaks (kept rows that still match
an exclude token).

Usage:
  python scripts/create_and_test_filters.py              # create + test
  python scripts/create_and_test_filters.py --test-only  # skip creation
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from collections import Counter

import requests

from scrape_poi_admin import (
    CHANGELIST_PATH, load_env, login, parse_rows, get_with_retry,
)
from filter_configs import FILTERS, FIELD_PARAM, FIELD_COLUMN
from simulate_filters import group_matches, EXCLUDE_GROUPS

OPTION_RE = re.compile(r'<option value="(\d+)">([^<]+)</option>')

# Diverse live-test pins: dense urban, mid metro, suburb, rural, the home pin.
TEST_PINS = [
    ("NYC-Midtown", "40.7580,-73.9855", "2"),
    ("Chicago-Loop", "41.8781,-87.6298", "3"),
    ("Denver", "39.7392,-104.9903", "5"),
    ("FortPierce-FL", "27.494378561621637,-80.33815750178654", "10"),
    ("Bozeman-MT", "45.6770,-111.0429", "10"),
]

BLANK_FORM = {k: "" for k in [
    "apply_saved_filter", "update_saved_filter", "apply_filter", "saved_filter_id",
    "max_results", "min_confidence", "address_line", "city", "state", "zipcode",
    "has_website", "operating_status", "latlog", "distance_miles",
    "name_primary_include_values", "name_common_include_values",
    "basic_category_include_values", "category_primary_include_values",
    "category_alternate_include_values", "taxonomy_primary_include_values",
    "taxonomy_alternates_include_values", "name_primary_exclude_values",
    "name_common_exclude_values", "basic_category_exclude_values",
    "category_primary_exclude_values", "category_alternate_exclude_values",
    "taxonomy_primary_exclude_values", "taxonomy_alternates_exclude_values",
    "query_builder",
]}


def joined(values: list[str]) -> str:
    return "".join(f"{v}\r\n" for v in values)


def field_params(cfg: dict) -> dict[str, str]:
    """The shared filter-field portion of the change-list form for a config."""
    p = dict(BLANK_FORM)
    p["max_results"] = cfg.get("max_results", "200")
    p["min_confidence"] = cfg.get("min_confidence", "")
    p["operating_status"] = cfg.get("operating_status", "open")
    p["has_website"] = cfg.get("has_website", "")
    p["query_builder"] = cfg.get("query_builder", "") + "\r\n"
    if cfg.get("show_duplicates"):
        p["show_duplicates"] = "on"
    for key, param in FIELD_PARAM.items():
        if cfg.get(key):
            p[param] = joined(cfg[key])
    return p


def save_params(name: str, cfg: dict) -> dict[str, str]:
    p = field_params(cfg)
    p["save_filter_name"] = name
    return p


def update_params(fid: str, cfg: dict) -> dict[str, str]:
    p = field_params(cfg)
    p["update_saved_filter"] = "1"
    p["saved_filter_id"] = fid
    return p


def saved_filters(session: requests.Session, base: str) -> dict[str, str]:
    r = session.get(base + CHANGELIST_PATH, timeout=60)
    r.encoding = "utf-8"
    # restrict to the saved-filter <select> block
    block = r.text.split('name="saved_filter_id"', 1)[-1].split("</select>", 1)[0]
    return {name.strip(): fid for fid, name in OPTION_RE.findall(block)}


def create_filters(session: requests.Session, base: str, env: dict) -> dict[str, str]:
    """Create each -cursor filter; if it already exists, UPDATE it in place."""
    existing = saved_filters(session, base)
    print("Existing saved filters:", ", ".join(sorted(existing)) or "(none)")
    for name, cfg in FILTERS.items():
        if name in existing:
            params = update_params(existing[name], cfg)
            r = get_with_retry(session, base + CHANGELIST_PATH, params, env, base)
            ok = r.status_code == 200 and "?e=1" not in r.url
            print(f"  ~ {name}: UPDATE (id {existing[name]}) {'OK' if ok else 'FAILED'} ({r.status_code})")
        else:
            params = save_params(name, cfg)
            r = get_with_retry(session, base + CHANGELIST_PATH, params, env, base)
            ok = r.status_code == 200 and "?e=1" not in r.url
            print(f"  + {name}: CREATE {'OK' if ok else 'FAILED'} ({r.status_code})")
        time.sleep(0.5)
    after = saved_filters(session, base)
    print("\nSaved-filter IDs now:")
    for name in FILTERS:
        print(f"  {name}: {after.get(name, 'NOT FOUND')}")
    return after


def scan_leaks(cfg: dict, rows: list[dict[str, str]]) -> list[str]:
    leaks = []
    for row in rows:
        for g in EXCLUDE_GROUPS:
            if cfg.get(g) and group_matches(cfg[g], FIELD_COLUMN[g], row):
                leaks.append(f"{row.get('business_name','?')} [{g}={row.get(FIELD_COLUMN[g],'')}]")
                break
    return leaks


def apply_saved(session, base, fid, latlog, distance, env) -> list[dict[str, str]]:
    p = dict(BLANK_FORM)
    p["apply_saved_filter"] = "1"
    p["saved_filter_id"] = fid
    p["latlog"] = latlog
    p["distance_miles"] = distance
    r = get_with_retry(session, base + CHANGELIST_PATH, p, env, base)
    return parse_rows(r.text, latlog, distance, "test")


def test_filters(session, base, env, ids: dict[str, str]) -> None:
    print("\n" + "=" * 78)
    print("LIVE MULTI-LOCATION TEST (applying each saved filter)")
    print("=" * 78)
    header = f"{'filter':18} " + " ".join(f"{lbl.split('-')[0][:6]:>7}" for lbl, _, _ in TEST_PINS) + f" {'leaks':>6}"
    print(header)
    for name, cfg in FILTERS.items():
        fid = ids.get(name)
        if not fid:
            print(f"{name:18} (no saved id - skipped)")
            continue
        counts, total_leaks, leak_samples = [], 0, []
        cats: Counter = Counter()
        for _, latlog, distance in TEST_PINS:
            try:
                rows = apply_saved(session, base, fid, latlog, distance, env)
            except Exception as exc:  # noqa: BLE001
                counts.append("ERR")
                continue
            counts.append(str(len(rows)))
            cats.update(r.get("category_primary", "") for r in rows)
            leaks = scan_leaks(cfg, rows)
            total_leaks += len(leaks)
            leak_samples.extend(leaks[:2])
            time.sleep(0.3)
        row_str = " ".join(f"{c:>7}" for c in counts)
        print(f"{name:18} {row_str} {total_leaks:>6}")
        print("      cats: " + ", ".join(f"{c or '(blank)'}:{n}" for c, n in cats.most_common(12)))
        if leak_samples:
            for s in leak_samples[:3]:
                print(f"      leak: {s}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-only", action="store_true")
    args = ap.parse_args()

    env = load_env()
    base = env["POI_ADMIN_BASE_URL"].rstrip("/")
    session = requests.Session()
    login(session, base, env["POI_ADMIN_USERNAME"], env["POI_ADMIN_PASSWORD"])

    if args.test_only:
        ids = saved_filters(session, base)
    else:
        ids = create_filters(session, base, env)
    test_filters(session, base, env, ids)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
