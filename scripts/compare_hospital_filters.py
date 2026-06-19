"""Head-to-head: `Hospital` (user) vs `hospital-cursor` across 11 US areas.

For each saved filter at each pin we count results, split them into real
hospitals vs. non-hospital noise (vet/urgent-care/clinic/rehab/nursing/etc.),
and surface noise examples. "Better" = keeps real hospitals while leaking the
least non-ER noise.
"""
from __future__ import annotations

import time
from collections import Counter
import requests

from scrape_poi_admin import load_env, login
from create_and_test_filters import apply_saved, saved_filters

REAL_HOSPITAL_CATS = {"hospital", "emergency_room", "childrens_hospital"}

# category_primary substrings that are NOT a 24/7-ER hospital
NOISE_CAT = [
    "medical_center", "clinic", "urgent", "doctor", "physician", "hospitalist",
    "animal", "veterinar", "pet", "dental", "dentist", "rehab", "psych",
    "behavioral", "nursing", "hospice", "dialysis", "imaging", "radiology",
    "surgery", "surgical", "pharmacy", "chiropract", "therapy", "equipment",
    "laboratory", "optometr", "dermatolog", "cancer", "fertility", "urology",
]
NOISE_NAME = [
    "urgent care", "walk-in", "walk in", "immediate care", "express care",
    "dental", "dentist", "orthodont", "veterinar", "animal hospital", "rehab",
    "recovery center", "behavioral", "mental health", "psychiat", "detox",
    "hospice", "nursing home", "skilled nursing", "assisted living", "dialysis",
    "imaging", "radiology", "pharmacy", "med spa", "medspa", "chiropract",
    "physical therapy", "occupational therapy", "surgery center",
    "surgical center", "endoscopy", "eye clinic", "vision center", "std clinic",
    "free clinic", "wellness center", "clinic",
]

PINS = [
    ("FtPierce-FL (home)", "27.494302424958242,-80.33807167109693", "5"),
    ("NYC", "40.7580,-73.9855", "1"),
    ("Los Angeles", "34.0522,-118.2437", "1"),
    ("Chicago", "41.8781,-87.6298", "1"),
    ("Houston", "29.7604,-95.3698", "2"),
    ("Denver", "39.7392,-104.9903", "2"),
    ("Atlanta", "33.7490,-84.3880", "2"),
    ("Phoenix", "33.4484,-112.0740", "2"),
    ("Seattle", "47.6062,-122.3321", "2"),
    ("Bozeman-MT", "45.6770,-111.0429", "5"),
    ("DodgeCity-KS", "37.7528,-100.0171", "5"),
]


def classify(rows: list[dict]) -> tuple[int, int, list[str], Counter]:
    real, noise, noise_eg = 0, 0, []
    cats: Counter = Counter()
    for r in rows:
        cat = (r.get("category_primary", "") or "").lower()
        name = (r.get("business_name", "") or "").lower()
        cats[r.get("category_primary", "") or "(blank)"] += 1
        is_noise = (
            cat not in REAL_HOSPITAL_CATS
            and (any(t in cat for t in NOISE_CAT) or any(t in name for t in NOISE_NAME))
        )
        if cat in REAL_HOSPITAL_CATS and not any(t in name for t in NOISE_NAME):
            real += 1
        elif is_noise:
            noise += 1
            if len(noise_eg) < 4:
                noise_eg.append(f"{r.get('business_name','?')} [{r.get('category_primary','')}]")
    return real, noise, noise_eg, cats


def main() -> int:
    env = load_env()
    base = env["POI_ADMIN_BASE_URL"].rstrip("/")
    s = requests.Session()
    login(s, base, env["POI_ADMIN_USERNAME"], env["POI_ADMIN_PASSWORD"])
    ids = saved_filters(s, base)
    targets = {"Hospital": ids.get("Hospital"), "hospital-cursor": ids.get("hospital-cursor")}
    print("Filter IDs:", targets)

    totals = {k: {"n": 0, "real": 0, "noise": 0} for k in targets}
    allcats = {k: Counter() for k in targets}
    print(f"\n{'area':20} " + " ".join(f"{k:>28}" for k in targets))
    print(f"{'':20} " + " ".join(f"{'total/real/noise':>28}" for _ in targets))
    for label, latlog, dist in PINS:
        cells = []
        for fname, fid in targets.items():
            if not fid:
                cells.append("NO ID")
                continue
            try:
                rows = apply_saved(s, base, fid, latlog, dist, env)
            except Exception as exc:  # noqa: BLE001
                cells.append("ERR")
                continue
            real, noise, _, cats = classify(rows)
            totals[fname]["n"] += len(rows)
            totals[fname]["real"] += real
            totals[fname]["noise"] += noise
            allcats[fname].update(cats)
            cells.append(f"{len(rows):>4}/{real:>4}/{noise:>4}")
            time.sleep(1.0)  # be gentle on staging (Heroku 30s timeout)
        print(f"{label:20} " + " ".join(f"{c:>28}" for c in cells))

    print("\n" + "=" * 70)
    print("TOTALS across 11 areas")
    for k, t in totals.items():
        nr = 100 * t["noise"] / t["n"] if t["n"] else 0
        print(f"  {k:18} total={t['n']:>5}  real={t['real']:>5}  noise={t['noise']:>5}  noise%={nr:.1f}")
    for k in targets:
        print(f"\n  {k} top categories:")
        for c, n in allcats[k].most_common(12):
            print(f"     {c}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
