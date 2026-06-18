"""Quick summary stats for data/nightlife_raw/nightlife_master.csv.

Usage: python scripts/analyze_nightlife.py
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "data" / "nightlife_raw" / "nightlife_master.csv"

# category_primary values that are food/beverage venues rather than true
# nightlife — observed substring noise pulled in by the "*bar" anchor.
NOISE_PRIMARY = {
    "smoothie_juice_bar", "juice_bar", "salad_bar", "sushi_bar", "oyster_bar",
    "raw_bar", "snack_bar", "coffee_shop", "candy_bar", "barbecue_restaurant",
    "bar_and_grill_restaurant",
}


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
        print(f"  {cat:26} {c}")

    print("\nCategory primary (top 25):")
    for cat, c in Counter(r["category_primary"] or "?" for r in rows).most_common(25):
        flag = "  <- noise" if cat in NOISE_PRIMARY else ""
        print(f"  {cat:26} {c}{flag}")

    noise = sum(1 for r in rows if r["category_primary"] in NOISE_PRIMARY)
    print(f"\nFood/beverage noise (juice/salad/sushi/etc. *bar): {noise} ({noise * 100 // n}%)")

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
            print(f"  {b:8} {buckets[b]}")

    # Quality-gate preview: confidence < 0.7 AND no website
    gate = sum(1 for r in rows if (to_float(r["confidence"]) or 1) < 0.7 and not r["websites"])
    print(f"\nWould fail (confidence<0.7 AND no website): {gate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
