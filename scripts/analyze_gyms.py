"""Quick summary stats for data/gyms_raw/gyms_master.csv.

Usage: python scripts/analyze_gyms.py
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "data" / "gyms_raw" / "gyms_master.csv"

# category_primary / category_alternate substrings that are NOT really a
# gym/fitness venue (pulled in by the broad "contains" include tokens or by a
# fitness token sitting in the alternate-category list).
NOISE_CATEGORY_TOKENS = (
    "tanning", "spa", "physical_therapy", "physiotherap", "chiropract",
    "nutrition", "weight_loss", "school", "tennis", "swimming", "volleyball",
    "golf", "stadium", "arena", "sporting_goods", "sportswear", "shopping",
    "store", "retail", "automotive", "boat", "marine", "repair",
    "community_center", "community_services", "non_profit", "park",
    "campground", "hotel", "resort", "country_club", "dance",
    "beauty_salon", "hair", "massage", "medical", "doctor", "clinic",
    "trampoline", "playground", "amusement",
)

# name substrings (lowercased) that commonly flag non-gym noise.
NOISE_NAME_TOKENS = (
    "tanning", "spa", "physical therapy", "chiropract", "nutrition",
    "massage", "salon", "dance", "swim", "tennis", "golf", "volleyball",
    "sporting goods", "supplement", "smoothie", "juice", "academy of",
)


def to_float(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def is_noise(row: dict[str, str]) -> bool:
    cats = (row.get("category_primary", "") + " " + row.get("category_alternate", "")).lower()
    if any(tok in cats for tok in NOISE_CATEGORY_TOKENS):
        # Keep it if the primary category is itself a core gym bucket.
        prim = row.get("category_primary", "").lower()
        core = prim in ("gym", "fitness_center", "yoga_studio", "pilates_studio")
        if not core:
            return True
    name = row.get("business_name", "").lower()
    if any(tok in name for tok in NOISE_NAME_TOKENS):
        prim = row.get("category_primary", "").lower()
        if prim not in ("gym", "fitness_center"):
            return True
    return False


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
        print(f"  {cat:28} {c}")

    print("\nCategory primary (top 20):")
    for cat, c in Counter(r["category_primary"] or "?" for r in rows).most_common(20):
        print(f"  {cat:28} {c}")

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

    # Quality-gate preview: confidence < 0.7 AND no website
    gate = sum(1 for r in rows if (to_float(r["confidence"]) or 1) < 0.7 and not r["websites"])
    print(f"\nWould fail (confidence<0.7 AND no website): {gate} ({gate * 100 // n}%)")

    # Noise estimate: rows whose category/name look non-gym.
    noisy = [r for r in rows if is_noise(r)]
    print(f"\nNoise estimate (non-gym category/name heuristic): {len(noisy)} ({len(noisy) * 100 // n}%)")
    print("Top noise category_primary:")
    for cat, c in Counter(r["category_primary"] or "?" for r in noisy).most_common(15):
        print(f"  {cat:28} {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
