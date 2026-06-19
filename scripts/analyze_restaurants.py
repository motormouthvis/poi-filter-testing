"""Summary stats + noise/duplicate scan for data/restaurants_raw/restaurants_master.csv.

Usage: python scripts/analyze_restaurants.py
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "data" / "restaurants_raw" / "restaurants_master.csv"

# category_primary / category_alternate substrings that signal a venue that is
# NOT a sit-down restaurant (the noise we want the production filter to drop).
NOISE_PRIMARY_TOKENS = [
    "fast_food", "food_truck", "street_vendor", "coffee", "cafe", "tea_room",
    "bakery", "nightclub", "brewery", "distillery", "winery", "caterer",
    "food_court", "gas_station", "convenience_store", "grocery", "supermarket",
    "food_stand", "juice", "smoothie", "ice_cream", "dessert", "donut",
    "bar_and_grill",  # tracked separately — kept, not dropped
]


def to_float(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main() -> int:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    n = len(rows)
    print(f"Total unique POIs (by id): {n}\n")

    states = Counter(r["state"] or "?" for r in rows)
    print(f"States covered: {len([s for s in states if s != '?'])}")
    print("Top 10 states:")
    for st, c in states.most_common(10):
        print(f"  {st:4} {c}")

    print("\nBasic category:")
    for cat, c in Counter(r["basic_category"] or "?" for r in rows).most_common(10):
        print(f"  {cat:28} {c}")

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
            print(f"  {b:8} {buckets[b]} ({buckets[b] * 100 // n}%)")
        sentinel = sum(1 for c in confs if abs(c - 0.77) < 1e-9)
        print(f"  exactly 0.77 (sentinel): {sentinel} ({sentinel * 100 // n}%)")
        # The user's saved Restaurants filter uses min_confidence = 0.7.
        below_07 = sum(1 for c in confs if c < 0.7)
        print(f"  would be dropped by min_confidence=0.7: {below_07} ({below_07 * 100 // n}%)")

    # --- Duplicate estimate: same business_name + business_address ---
    def norm(s: str) -> str:
        return " ".join((s or "").lower().split())

    addr_name = Counter((norm(r["business_name"]), norm(r["business_address"]))
                        for r in rows if r.get("business_address"))
    dup_groups = {k: c for k, c in addr_name.items() if c > 1 and k[0] and k[1]}
    dup_rows = sum(c for c in dup_groups.values())
    dup_extra = sum(c - 1 for c in dup_groups.values())
    print(f"\nDuplicate rows (same business_name + business_address):")
    print(f"  groups with >1 row: {len(dup_groups)}")
    print(f"  total rows in those groups: {dup_rows}")
    print(f"  redundant rows (collapsible): {dup_extra} ({dup_extra * 100 // n}%)")
    print("  examples:")
    for (name, _addr), c in Counter(dup_groups).most_common(8):
        print(f"    {c}x  {name}")

    # --- Noise scan by category ---
    print("\nNoise category scan (category_primary contains token):")
    for tok in ["fast_food", "food_truck", "street_vendor", "coffee", "cafe",
                "bakery", "nightclub", "brewery", "distillery", "winery",
                "caterer", "food_court", "gas_station", "convenience",
                "ice_cream", "donut", "juice", "bar_and_grill"]:
        c = sum(1 for r in rows if tok in (r["category_primary"] or ""))
        if c:
            print(f"  category_primary~{tok:18} {c}")

    print("\nNoise scan via category_alternate (primary=restaurant leaks):")
    for tok in ["gas_station", "convenience_store", "caterer", "grocery",
                "supermarket", "fast_food", "nightclub", "brewery"]:
        c = sum(1 for r in rows if tok in (r["category_alternate"] or ""))
        if c:
            print(f"  category_alternate~{tok:18} {c}")

    # name-based leaks (gas/market/catering) mislabeled category_primary=restaurant
    print("\nName-based leak scan (business_name contains token):")
    for tok in ["chevron", "shell", "exxon", "mobil", "marathon", "circle k",
                "7-eleven", "catering", "market", "food truck", "taco truck"]:
        c = sum(1 for r in rows if tok in (r["business_name"] or "").lower())
        if c:
            print(f"  name~{tok:14} {c}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
