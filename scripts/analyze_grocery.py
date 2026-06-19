"""Summary stats + noise heuristics for data/grocery_raw/grocery_master.csv.

Usage: python scripts/analyze_grocery.py
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "data" / "grocery_raw" / "grocery_master.csv"

# category_primary values that are NOT weekly-grocery destinations. These ride
# in because the raw pull includes the broad basic_category=food_and_beverage_store
# bucket, which is a catch-all for any retail food/beverage seller.
NOISE_PRIMARY = {
    "convenience_store", "gas_station", "dollar_store", "discount_store",
    "pharmacy", "drugstore", "liquor_store", "beer_wine_and_spirits",
    "wine_shop", "wine_store", "tobacco_shop", "e_cigarette_store",
    "vitamins_and_supplements", "vitamin_and_supplement_store",
    "bakery", "candy_store", "chocolate_shop", "ice_cream_shop",
    "coffee_shop", "tea_room", "restaurant", "fast_food_restaurant",
    "caterer", "bank", "warehouse", "wholesale_store",
    "freight_and_cargo_service", "distribution_center",
    "food_beverage_service_distribution", "agricultural_service",
    "pet_store", "pet_supply_store",
}

# category_primary values that are clearly real grocery/supermarket targets.
CORE_PRIMARY = {
    "supermarket", "grocery_store", "specialty_grocery_store",
    "wholesale_grocer", "international_grocery_store", "health_food_store",
    "asian_grocery_store",
}

# Name-substring tells for pickup-only depots, distribution, and mislabels.
NAME_NOISE = [
    "distribution center", "distribution centre", "pickup & delivery",
    "pickup and delivery", "grocery pickup", "fulfillment", "warehouse",
    "arcade", "dollar general", "family dollar", "dollar tree",
]


def to_float(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main() -> int:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    n = len(rows)
    print(f"Total unique POIs: {n}\n")

    states = Counter(r["state"] or "?" for r in rows)
    print(f"States covered: {len([s for s in states if s != '?'])}")
    print("Top 10 states:")
    for st, c in states.most_common(10):
        print(f"  {st:4} {c}")

    print("\nBasic category:")
    for cat, c in Counter(r["basic_category"] or "?" for r in rows).most_common(15):
        print(f"  {cat:32} {c}")

    print("\nCategory primary (top 30):")
    for cat, c in Counter(r["category_primary"] or "?" for r in rows).most_common(30):
        print(f"  {cat:32} {c}")

    no_web = sum(1 for r in rows if not r["websites"])
    print(f"\nWebsite: has={n - no_web} ({(n - no_web) * 100 // n}%)  none={no_web} ({no_web * 100 // n}%)")

    confs = [to_float(r["confidence"]) for r in rows]
    confs = [c for c in confs if c is not None]
    if confs:
        buckets = Counter()
        for c in confs:
            buckets["<0.5" if c < 0.5 else "0.5-0.7" if c < 0.7 else "0.7-0.9" if c < 0.9 else ">=0.9"] += 1
        print("\nConfidence distribution:")
        for b in ("<0.5", "0.5-0.7", "0.7-0.9", ">=0.9"):
            print(f"  {b:8} {buckets[b]} ({buckets[b] * 100 // len(confs)}%)")

    # Sentinel check: any single confidence value that is suspiciously frequent.
    exact = Counter(round(c, 4) for c in confs)
    print("\nMost frequent exact confidence values:")
    for val, c in exact.most_common(5):
        print(f"  {val:<8} {c} ({c * 100 // len(confs)}%)")

    # --- Noise analysis -----------------------------------------------------
    print("\n=== NOISE ANALYSIS ===")
    core = sum(1 for r in rows if r["category_primary"] in CORE_PRIMARY)
    noise = sum(1 for r in rows if r["category_primary"] in NOISE_PRIMARY)
    other = n - core - noise
    print(f"category_primary in CORE grocery set: {core} ({core * 100 // n}%)")
    print(f"category_primary in NOISE set:        {noise} ({noise * 100 // n}%)")
    print(f"category_primary other/uncategorized: {other} ({other * 100 // n}%)")

    print("\nNoise breakdown by category_primary:")
    noise_counter = Counter(
        r["category_primary"] for r in rows if r["category_primary"] in NOISE_PRIMARY
    )
    for cat, c in noise_counter.most_common():
        print(f"  {cat:36} {c}")

    # Name-substring noise (pickup depots, distribution, arcades, dollar stores)
    print("\nName-substring noise hits:")
    for tell in NAME_NOISE:
        hits = [r for r in rows if tell in (r["business_name"] or "").lower()]
        if hits:
            print(f"  {tell:24} {len(hits)}  e.g. {hits[0]['business_name']!r} -> cp={hits[0]['category_primary']!r}")

    # Specific known-noise items the user's current filter still lets through.
    print("\nKnown problem items (from user report):")
    for needle in ("lucky 7", "walmart grocery pickup", "walmart distribution",
                   "walmart supercenter"):
        hits = [r for r in rows if needle in (r["business_name"] or "").lower()]
        for h in hits[:3]:
            print(f"  {h['business_name']!r}: cp={h['category_primary']!r} alt={h['category_alternate']!r} bc={h['basic_category']!r}")

    # Independent / ethnic grocers that have NO brand_name_primary (i.e. would be
    # dropped by a hard name-whitelist AND).
    grocery_like = [
        r for r in rows
        if r["category_primary"] in {"supermarket", "grocery_store",
                                     "specialty_grocery_store",
                                     "international_grocery_store",
                                     "asian_grocery_store"}
    ]
    no_brand = [r for r in grocery_like if not (r["brand_name_primary"] or "").strip()]
    print(f"\nReal grocery_store/supermarket rows: {len(grocery_like)}")
    print(f"  ...with NO brand_name_primary (independents a name-whitelist AND would drop): "
          f"{len(no_brand)} ({len(no_brand) * 100 // max(len(grocery_like), 1)}%)")
    print("  examples:")
    for r in no_brand[:8]:
        print(f"    {r['business_name']!r} ({r['city']}, {r['state']}) cp={r['category_primary']}")

    # Quality-gate preview: confidence < 0.5 AND no website
    gate = sum(1 for r in rows if (to_float(r["confidence"]) or 1) < 0.5 and not r["websites"])
    print(f"\nWould fail compound gate (confidence<0.5 AND no website): {gate} ({gate * 100 // n}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
