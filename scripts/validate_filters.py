"""Spot-check the v1 proposed filters end-to-end against staging.

For each category it sends the FULL proposed admin parameters (includes + excludes
+ query_builder, exactly as documented in docs/filters/<cat>.md §0) to the staging
PoiDetail filter builder across a few contrasting metros, then scans the returned
rows for leaks (noise the filter should have removed). Writes a markdown report to
docs/filters/validation_spotcheck.md.

Usage: python scripts/validate_filters.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scrape_poi_admin as s  # reuse login/parse/get_with_retry
import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT = REPO_ROOT / "docs" / "filters" / "validation_spotcheck.md"

# Contrasting metros chosen to avoid the parks 10-mi 503 mega-metros.
METROS = [
    ("houston_tx", "29.7604,-95.3698"),       # large sprawl metro
    ("denver_co", "39.7392,-104.9903"),        # mid-size metro
    ("key_west_fl", "24.5551,-81.7800"),       # small tourist town
    ("ann_arbor_mi", "42.2808,-83.7430"),      # college town
]


def base_params() -> dict[str, str]:
    """Full empty form param set (all keys present) to avoid Django ?e=1."""
    p = dict(s.CATEGORY_PARAMS)
    for k in list(p):
        if k.endswith("_values") or k == "query_builder":
            p[k] = ""
    p["max_results"] = "250"
    p["min_confidence"] = "0"
    p["operating_status"] = "open"
    return p


# --- Proposed v1 filters (must mirror docs/filters/<cat>.md §0) ---------------
FILTERS: dict[str, dict] = {
    "gyms": {
        "distance": "5",
        "params": {
            "basic_category_include_values": "gym\r\nfitness_center\r\n",
            "category_primary_include_values": "gym\r\nfitness_center\r\nyoga_studio\r\npilates_studio\r\nmartial_arts\r\nboxing_gym\r\nclimbing_gym\r\ncrossfit\r\ngymnastics_center\r\naerial_fitness_center\r\n",
            "category_alternate_exclude_values": "day_spa\r\nswimming_pool\r\ngolf_course\r\ngolf_instructor\r\ndance_school\r\n",
            "name_primary_exclude_values": "*physical therapy*\r\n*chiropract*\r\n*country club*\r\n*golf academy*\r\n*swim academy*\r\n*swim school*\r\n",
            "query_builder": "(basic_category_include or category_primary_include) and category_alternate_exclude and name_primary_exclude\r\n",
        },
        "leak_primary": {"sports_and_fitness_instruction"},
        "leak_name": [r"physical therapy", r"chiropract", r"country club", r"golf academy", r"swim school", r"swim academy"],
    },
    "parks": {
        "distance": "3",
        "params": {
            "basic_category_include_values": '"park"\r\n"garden"\r\n"playground"\r\n"dog_park"\r\n"national_park"\r\n',
            "category_primary_include_values": '"park"\r\n"state_park"\r\n"national_park"\r\n"nature_preserve"\r\n"botanical_garden"\r\n"community_gardens"\r\n"dog_park"\r\n"playground"\r\n"skate_park"\r\n"water_park"\r\n',
            "category_primary_exclude_values": "parking\r\nmobile_home_park\r\nrv_park\r\namusement_park\r\ngardener\r\nnursery_and_gardening\r\nhome_and_garden\r\nbeer_garden\r\ntrampoline_park\r\natv_recreation_park\r\nhydroponic_gardening\r\npark_and_rides\r\n",
            "name_primary_exclude_values": "parking\r\ngarage\r\nmobile home\r\ntrailer park\r\nbusiness park\r\noffice park\r\nindustrial park\r\nrv park\r\nself storage\r\n",
            "query_builder": "(basic_category_include or category_primary_include) and category_primary_exclude and name_primary_exclude\r\n",
        },
        "leak_primary": {"parking", "mobile_home_park", "rv_park", "amusement_park", "gardener", "nursery_and_gardening", "home_and_garden", "beer_garden"},
        "leak_name": [r"parking", r"garage", r"mobile home", r"trailer park", r"business park", r"office park", r"industrial park", r"self storage"],
    },
    "shopping_centers": {
        "distance": "5",
        "params": {
            "basic_category_include_values": "shopping_center\r\nshopping_mall\r\n",
            "category_primary_include_values": "shopping_center\r\nshopping_mall\r\noutlet_mall\r\nstrip_mall\r\n",
            "name_primary_exclude_values": "*food court*\r\n*parking*\r\n*self storage*\r\n*business park*\r\n*business plaza*\r\n*office park*\r\n*medical center*\r\n*medical plaza*\r\n*professional plaza*\r\n*professional building*\r\n*industrial park*\r\n",
            "query_builder": "(basic_category_include or category_primary_include) and name_primary_exclude\r\n",
        },
        "leak_primary": set(),
        "leak_name": [r"food court", r"parking", r"self storage", r"business park", r"office park", r"medical center", r"industrial park"],
    },
    "nightlife": {
        "distance": "5",
        "params": {
            "basic_category_include_values": "bar\r\nnightlife\r\n",
            "category_primary_include_values": "*bar\r\nnight_club\r\nnightclub\r\n*pub\r\nlounge\r\nbrewery\r\nkaraoke\r\n",
            "category_primary_exclude_values": "smoothie_juice_bar\r\nsalad_bar\r\nmilk_bar\r\njuice_bar\r\nsushi_bar\r\noyster_bar\r\nraw_bar\r\nsnack_bar\r\ncandy_bar\r\n",
            "query_builder": "(basic_category_include or category_primary_include) and category_primary_exclude\r\n",
        },
        "leak_primary": {"smoothie_juice_bar", "salad_bar", "milk_bar", "juice_bar", "barber", "barbecue_restaurant", "bar_and_grill_restaurant", "public_and_government_association", "notary_public"},
        "leak_name": [r"\bjuice\b", r"smoothie", r"\bbarber\b", r"barbecue", r"ice cream"],
    },
}


def fetch(session, base, params, latlog, distance, label):
    p = dict(params)
    p["latlog"] = latlog
    p["distance_miles"] = distance
    rows, page = [], 1
    while True:
        pp = dict(p)
        if page > 1:
            pp["p"] = str(page)
        r = s.get_with_retry(session, base + s.CHANGELIST_PATH, pp, ENV, base)
        batch = s.parse_rows(r.text, latlog, distance, label)
        if not batch:
            break
        rows.extend(batch)
        if 'class="end"' not in r.text or f"?p={page + 1}" not in r.text:
            break
        page += 1
    return rows


def find_leaks(rows, cat_cfg):
    name_res = [re.compile(p, re.I) for p in cat_cfg["leak_name"]]
    leaks = []
    for r in rows:
        cp = (r.get("category_primary") or "").lower()
        bc = (r.get("basic_category") or "").lower()
        nm = r.get("business_name") or ""
        why = None
        if cp in cat_cfg["leak_primary"] or bc in cat_cfg["leak_primary"]:
            why = f"category={cp or bc}"
        else:
            for rx in name_res:
                if rx.search(nm):
                    why = f"name~/{rx.pattern}/"
                    break
        if why:
            leaks.append((nm, cp, why))
    return leaks


def main() -> int:
    global ENV
    ENV = s.load_env()
    base = ENV["POI_ADMIN_BASE_URL"].rstrip("/")
    session = requests.Session()
    s.login(session, base, ENV["POI_ADMIN_USERNAME"], ENV["POI_ADMIN_PASSWORD"])

    out = ["# Filter validation — per-metro spot-checks (v1)", ""]
    out.append("Full proposed filters (includes + excludes + query) run against staging.")
    out.append(f"Metros: {', '.join(m[0] for m in METROS)}.")
    out.append("")

    for cat, cfg in FILTERS.items():
        params = base_params()
        params.update(cfg["params"])
        dist = cfg["distance"]
        print(f"\n=== {cat} (distance {dist} mi) ===")
        out.append(f"## {cat}  (distance {dist} mi)\n")
        out.append("| Metro | Kept | Leaks | Sample kept |")
        out.append("|---|---:|---:|---|")
        for label, latlog in METROS:
            try:
                rows = fetch(session, base, params, latlog, dist, label)
            except Exception as exc:  # noqa: BLE001
                print(f"  {label}: FETCH FAILED {exc}")
                out.append(f"| {label} | ERR | — | {exc} |")
                continue
            leaks = find_leaks(rows, cfg)
            sample = ", ".join((r.get("business_name") or "?")[:24] for r in rows[:6])
            print(f"  {label}: kept={len(rows)} leaks={len(leaks)}")
            for nm, cp, why in leaks[:8]:
                print(f"      LEAK: {nm}  [{why}]")
            out.append(f"| {label} | {len(rows)} | {len(leaks)} | {sample} |")
            if leaks:
                out.append("")
                out.append(f"**{label} leaks ({len(leaks)}):**")
                for nm, cp, why in leaks[:15]:
                    out.append(f"- `{nm}` — {why}")
                out.append("")
        out.append("")

    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"\nReport written: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
