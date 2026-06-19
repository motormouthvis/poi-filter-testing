"""Quick summary stats for data/hospitals_raw/hospitals_master.csv.

Adds hospital-specific noise heuristics on top of the generic summary used for
the coffee/tea pull: the raw pull leans on `medical_center` (which swallows the
whole `outpatient_care_facility` universe) and a substring `hospital` token
(which also grabs `hospital_equipment_and_supplies`), so we surface the noise
classes that the production filter has to remove.

Usage: python scripts/analyze_hospitals.py
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "data" / "hospitals_raw" / "hospitals_master.csv"

# Name-substring signals for common non-ER medical noise. Lower-cased contains.
NAME_NOISE = {
    "urgent care / walk-in": ["urgent care", "walk-in", "walk in", "immediate care", "express care"],
    "clinic / doctor office": ["clinic", "dr ", "dr.", " md", "m.d.", " od", ", od", "physician", "associates"],
    "dental / dentist": ["dental", "dentist", "orthodont", "oral surg"],
    "veterinary / animal": ["veterinar", "animal hospital", "animal clinic", " vet ", "pet "],
    "rehab / recovery / psych": ["rehab", "recovery", "behavioral", "mental health", "psychiat", "counseling", "detox"],
    "hospice / nursing / assisted": ["hospice", "nursing", "assisted living", "senior living", "skilled nursing"],
    "imaging / lab / diagnostic": ["imaging", "radiology", "mri", "diagnostic", "laboratory", " lab", "x-ray"],
    "surgery / specialty center": ["surgery center", "surgical center", "ambulatory surg", "endoscopy"],
    "dialysis": ["dialysis", "kidney center", "renal"],
    "cancer / oncology": ["cancer center", "oncology", "oncologist", "radiation"],
    "spa / wellness / cosmetic": ["med spa", "medspa", "wellness", "wax", "aesthetic", "plastic surg", "dermatolog"],
    "pharmacy": ["pharmacy", "drugstore"],
    "therapy (PT/OT/chiro)": ["physical therapy", "chiropract", "occupational therapy", "rehab therapy"],
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
    for cat, c in Counter(r["basic_category"] or "?" for r in rows).most_common(12):
        print(f"  {cat:32} {c}")

    print("\nCategory primary (top 15):")
    for cat, c in Counter(r["category_primary"] or "?" for r in rows).most_common(15):
        print(f"  {cat:32} {c}")

    # category_alternate is a comma-separated list; flatten and count tokens.
    alt_counter: Counter[str] = Counter()
    for r in rows:
        for tok in (r.get("category_alternate") or "").split(","):
            tok = tok.strip()
            if tok:
                alt_counter[tok] += 1
    print("\nCategory alternate tokens (top 20):")
    for cat, c in alt_counter.most_common(20):
        print(f"  {cat:36} {c}")

    no_web = sum(1 for r in rows if not r["websites"])
    print(f"\nWebsite: has={n - no_web} ({(n - no_web) * 100 // n}%)  none={no_web} ({no_web * 100 // n}%)")

    confs = [to_float(r["confidence"]) for r in rows]
    confs = [c for c in confs if c is not None]
    if confs:
        buckets: Counter[str] = Counter()
        for c in confs:
            buckets["<0.5" if c < 0.5 else "0.5-0.7" if c < 0.7 else "0.7-0.9" if c < 0.9 else ">=0.9"] += 1
        print("\nConfidence distribution:")
        for b in ("<0.5", "0.5-0.7", "0.7-0.9", ">=0.9"):
            print(f"  {b:8} {buckets[b]} ({buckets[b] * 100 // n}%)")

    # 0.77 sentinel check.
    sentinel = sum(1 for r in rows if (r.get("confidence") or "").startswith("0.77") and to_float(r["confidence"]) == 0.77)
    exact_077 = sum(1 for r in rows if to_float(r["confidence"]) == 0.77)
    print(f"\nExactly confidence == 0.77 (sentinel): {exact_077} ({exact_077 * 100 // n}%)")

    # ER signal: emergency_room appearing in primary or alternate categories.
    er_primary = sum(1 for r in rows if "emergency_room" in (r.get("category_primary") or ""))
    er_alt = sum(1 for r in rows if "emergency_room" in (r.get("category_alternate") or ""))
    er_any = sum(
        1 for r in rows
        if "emergency_room" in (r.get("category_primary") or "")
        or "emergency_room" in (r.get("category_alternate") or "")
    )
    print(f"\nER signal — emergency_room in category_primary: {er_primary}")
    print(f"ER signal — emergency_room in category_alternate: {er_alt}")
    print(f"ER signal — emergency_room anywhere: {er_any} ({er_any * 100 // n}%)")

    # True 'hospital' primary vs medical_center swallow.
    cp_hospital = sum(1 for r in rows if (r.get("category_primary") or "") == "hospital")
    cp_medcenter = sum(1 for r in rows if (r.get("category_primary") or "") == "medical_center")
    cp_er = sum(1 for r in rows if (r.get("category_primary") or "") == "emergency_room")
    bc_outpatient = sum(1 for r in rows if (r.get("basic_category") or "") == "outpatient_care_facility")
    print(f"\ncategory_primary == 'hospital' (exact): {cp_hospital}")
    print(f"category_primary == 'medical_center' (exact): {cp_medcenter}")
    print(f"category_primary == 'emergency_room' (exact): {cp_er}")
    print(f"basic_category == 'outpatient_care_facility' (exact): {bc_outpatient}")

    # b2b / supplies leaks from the substring 'hospital' token.
    supplies = sum(
        1 for r in rows
        if "equipment" in (r.get("category_primary") or "")
        or (r.get("basic_category") or "") == "b2b_service"
    )
    print(f"hospital_equipment / b2b leaks: {supplies}")

    # Name-based noise scan.
    print("\nName-substring noise scan (rows may match multiple classes):")
    noise_hits: Counter[str] = Counter()
    flagged_ids = set()
    for r in rows:
        name = (r.get("business_name") or "").lower()
        for klass, needles in NAME_NOISE.items():
            if any(nd in name for nd in needles):
                noise_hits[klass] += 1
                flagged_ids.add(r["id"])
    for klass, c in noise_hits.most_common():
        print(f"  {klass:28} {c}")
    print(f"  -- unique rows flagged by any name-noise class: {len(flagged_ids)} ({len(flagged_ids) * 100 // n}%)")

    # Quality-gate previews.
    gate_07 = sum(1 for r in rows if (to_float(r["confidence"]) or 1) < 0.7 and not r["websites"])
    gate_05 = sum(1 for r in rows if (to_float(r["confidence"]) or 1) < 0.5 and not r["websites"])
    floor_07 = sum(1 for r in rows if (to_float(r["confidence"]) or 1) < 0.7)
    floor_09 = sum(1 for r in rows if (to_float(r["confidence"]) or 1) < 0.9)
    print(f"\nWould fail (confidence<0.7 AND no website): {gate_07}")
    print(f"Would fail (confidence<0.5 AND no website): {gate_05}")
    print(f"Numeric floor min_confidence=0.7 would drop: {floor_07} ({floor_07 * 100 // n}%)")
    print(f"Numeric floor min_confidence=0.9 would drop: {floor_09} ({floor_09 * 100 // n}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
