"""Populate the live 'Urgent Care' saved filter (id 463) with urgent-care-cursor."""
from __future__ import annotations

import requests

from scrape_poi_admin import CHANGELIST_PATH, load_env, login, get_with_retry
from filter_configs import FILTERS
from create_and_test_filters import update_params, saved_filters
from _review_uc import dump_change_form

TARGET_NAME = "Urgent Care"


def main() -> int:
    env = load_env()
    base = env["POI_ADMIN_BASE_URL"].rstrip("/")
    s = requests.Session()
    login(s, base, env["POI_ADMIN_USERNAME"], env["POI_ADMIN_PASSWORD"])

    ids = saved_filters(s, base)
    fid = ids.get(TARGET_NAME)
    print("saved-filter ids:", {k: v for k, v in ids.items() if "urgent" in k.lower() or "hospital" in k.lower()})
    if not fid:
        print(f"Could not find saved filter named {TARGET_NAME!r}")
        return 1

    cfg = FILTERS["urgent-care-cursor"]
    r = get_with_retry(s, base + CHANGELIST_PATH, update_params(fid, cfg), env, base)
    ok = r.status_code == 200 and "?e=1" not in r.url
    print(f"UPDATE {TARGET_NAME} (id {fid}): {'OK' if ok else 'FAILED'} ({r.status_code})")

    print("\nverifying stored fields:")
    dump_change_form(s, base, f"/admin/poi_data/poifilter/{fid}/change/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
