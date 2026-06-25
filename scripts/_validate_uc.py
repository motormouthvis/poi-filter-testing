"""Live-test the Urgent Care saved filter (463) across locations."""
from __future__ import annotations

import re
import time
import requests

from scrape_poi_admin import load_env, login
from create_and_test_filters import saved_filters, apply_saved

PINS = [
    ("FortPierce-FL (home)", "27.49434049329653,-80.33809312876933", "20"),
    ("Chicago", "41.8781,-87.6298", "5"),
    ("Houston", "29.7604,-95.3698", "5"),
    ("Phoenix", "33.4484,-112.0740", "5"),
    ("Atlanta", "33.7490,-84.3880", "5"),
    ("Denver", "39.7392,-104.9903", "5"),
]

HOSP = re.compile(r"\bhospital\b|emergency department|emergency room|medical center$", re.I)
UC = re.compile(r"urgent|immediate|express care|walk|convenient|minute|quick|"
                r"concentra|medexpress|fastmed|carenow|nextcare|citymd|gohealth|"
                r"wellnow|carbon health|patient first|md now|afc|instacare|zoom|"
                r"centra care|doctors care|carespot|little clinic", re.I)


def main() -> int:
    env = load_env()
    base = env["POI_ADMIN_BASE_URL"].rstrip("/")
    s = requests.Session()
    login(s, base, env["POI_ADMIN_USERNAME"], env["POI_ADMIN_PASSWORD"])
    fid = saved_filters(s, base)["Urgent Care"]
    print(f"Urgent Care filter id={fid}\n")

    for label, latlog, dist in PINS:
        try:
            rows = apply_saved(s, base, fid, latlog, dist, env)
        except Exception as exc:  # noqa: BLE001
            print(f"{label:24} ERROR {exc}")
            continue
        uc = sum(1 for r in rows if UC.search(r.get("business_name", "")))
        hosp = [r for r in rows if HOSP.search(r.get("business_name", ""))
                and not UC.search(r.get("business_name", ""))]
        print(f"{label:24} total={len(rows):>3}  uc-named={uc:>3}  hospital-leak={len(hosp)}")
        for r in rows[:6]:
            print(f"      {r.get('business_name','')[:46]:46} | cp={r.get('category_primary','')}")
        for r in hosp[:4]:
            print(f"      LEAK? {r.get('business_name','')[:48]:48} | cp={r.get('category_primary','')}")
        time.sleep(0.6)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
