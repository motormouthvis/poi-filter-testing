"""Review admin state for the urgent-care task (read-only).

Dumps:
  - PoiFilter list (all saved filters + ids)
  - PoiCategory list (main categories + any subcategory linkage)
  - The change-form field values for the Hospital + urgent care filters
"""
from __future__ import annotations

import html
import re

import requests

from scrape_poi_admin import load_env, login

FILTER_LIST = "/admin/poi_data/poifilter/"
CAT_LIST = "/admin/poi_data/poicategory/"

ROW_LINK = re.compile(r'<th class="field-[^"]*"><a href="([^"]+)">([^<]+)</a>')
ANY_CHANGE_LINK = re.compile(r'href="(/admin/poi_data/poifilter/(\d+)/change/)"[^>]*>([^<]*)</a>')
CAT_CHANGE_LINK = re.compile(r'href="(/admin/poi_data/poicategory/(\d+)/change/)"[^>]*>([^<]*)</a>')


def strip(t: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()


def dump_change_form(session, base, url):
    r = session.get(base + url, timeout=60)
    r.encoding = "utf-8"
    txt = r.text
    print(f"\n----- {url} -----")
    # text inputs
    for m in re.finditer(r'<input[^>]*\bname="([^"]+)"[^>]*\bvalue="([^"]*)"[^>]*>', txt):
        name, val = m.group(1), m.group(2)
        if name in ("csrfmiddlewaretoken",) or name.startswith("_"):
            continue
        if val.strip():
            print(f"  {name} = {html.unescape(val)}")
    # selects (selected option)
    for sm in re.finditer(r'<select[^>]*\bname="([^"]+)"[^>]*>(.*?)</select>', txt, re.S):
        name, body = sm.group(1), sm.group(2)
        sel = re.search(r'<option value="([^"]*)"[^>]*selected[^>]*>([^<]*)</option>', body)
        if sel:
            print(f"  {name} = {sel.group(1)} ({strip(sel.group(2))})")
    # textareas
    for tm in re.finditer(r'<textarea[^>]*\bname="([^"]+)"[^>]*>(.*?)</textarea>', txt, re.S):
        name, body = tm.group(1), html.unescape(body).strip()
        if body:
            print(f"  {name} = {body!r}")
    # checkboxes
    for cm in re.finditer(r'<input[^>]*type="checkbox"[^>]*\bname="([^"]+)"[^>]*?>', txt):
        checked = "checked" in cm.group(0)
        print(f"  [checkbox] {cm.group(1)} = {checked}")


def main() -> int:
    env = load_env()
    base = env["POI_ADMIN_BASE_URL"].rstrip("/")
    s = requests.Session()
    login(s, base, env["POI_ADMIN_USERNAME"], env["POI_ADMIN_PASSWORD"])

    # --- categories ---
    r = s.get(base + CAT_LIST, timeout=60)
    r.encoding = "utf-8"
    print("=" * 70)
    print("POI CATEGORIES")
    print("=" * 70)
    cats = CAT_CHANGE_LINK.findall(r.text)
    for url, cid, label in cats:
        print(f"  [{cid}] {strip(label)}  -> {url}")

    # --- filters ---
    r = s.get(base + FILTER_LIST, timeout=60)
    r.encoding = "utf-8"
    print("\n" + "=" * 70)
    print("POI FILTERS")
    print("=" * 70)
    seen = {}
    for url, fid, label in ANY_CHANGE_LINK.findall(r.text):
        if fid not in seen:
            seen[fid] = (url, strip(label))
            print(f"  [{fid}] {strip(label)}  -> {url}")

    # --- dump Hospital(67) + hospital-cursor(434) + urgent care(463) ---
    print("\n" + "=" * 70)
    print("CHANGE-FORM DUMPS")
    print("=" * 70)
    for fid in ("67", "434", "463"):
        print(f"\n### filter [{fid}]")
        dump_change_form(s, base, f"/admin/poi_data/poifilter/{fid}/change/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
