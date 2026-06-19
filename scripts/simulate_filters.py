"""Local simulation + checks for all 8 `-cursor` filters.

Replays each filter's include/exclude logic (with the admin builder's
substring/anchor match operators) against its raw dataset, with no network
calls. Reports kept/removed counts, an address-dedup preview, the surviving
category mix, what got cut, and a leak sanity-scan (any kept row that still
matches an exclude token — should always be 0 by construction).

Usage:  python scripts/simulate_filters.py
"""
from __future__ import annotations

import csv
from collections import Counter

from filter_configs import FILTERS, FIELD_COLUMN

INCLUDE_GROUPS = [
    "basic_category_include", "category_primary_include",
    "category_alternate_include", "name_primary_include", "name_common_include",
]
EXCLUDE_GROUPS = [
    "basic_category_exclude", "category_primary_exclude",
    "category_alternate_exclude", "name_primary_exclude", "name_common_exclude",
]
LIST_FIELDS = {"category_alternate"}  # comma-separated multi-value columns


def token_matches(token: str, value: str) -> bool:
    """Admin match operators: "exact" | prefix* | *suffix | *contains* | contains."""
    v = value.lower().strip()
    t = token.lower().strip()
    if not t:
        return False
    if t.startswith('"') and t.endswith('"') and len(t) >= 2:
        return v == t[1:-1]
    if t.startswith("*") and t.endswith("*") and len(t) >= 2:
        return t[1:-1] in v
    if t.startswith("*"):
        return v.endswith(t[1:])
    if t.endswith("*"):
        return v.startswith(t[:-1])
    return t in v


def group_matches(tokens: list[str], column: str, row: dict[str, str]) -> bool:
    value = row.get(column, "") or ""
    if column in LIST_FIELDS:
        items = [p.strip() for p in value.split(",") if p.strip()] or [""]
        return any(token_matches(tok, item) for tok in tokens for item in items)
    return any(token_matches(tok, value) for tok in tokens)


def keep_row(cfg: dict, row: dict[str, str]) -> tuple[bool, str]:
    inc_present = [g for g in INCLUDE_GROUPS if cfg.get(g)]
    include_ok = any(group_matches(cfg[g], FIELD_COLUMN[g], row) for g in inc_present)
    if not include_ok:
        return False, "no-include"
    for g in EXCLUDE_GROUPS:
        if cfg.get(g) and group_matches(cfg[g], FIELD_COLUMN[g], row):
            return False, g
    mc = cfg.get("min_confidence", "")
    if mc:
        try:
            if float(row.get("confidence", "") or 0) < float(mc):
                return False, "min_confidence"
        except ValueError:
            return False, "min_confidence"
    return True, "kept"


def leak_scan(cfg: dict, kept: list[dict[str, str]]) -> int:
    """Any kept row that still matches an exclude token (should be 0)."""
    leaks = 0
    for row in kept:
        for g in EXCLUDE_GROUPS:
            if cfg.get(g) and group_matches(cfg[g], FIELD_COLUMN[g], row):
                leaks += 1
                break
    return leaks


def run_one(name: str, cfg: dict) -> dict:
    path = cfg["raw_csv"]
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    kept, removed = [], Counter()
    for row in rows:
        ok, reason = keep_row(cfg, row)
        (kept.append(row) if ok else removed.update([reason]))
    deduped = len({(r.get("business_address", ""), r.get("city", ""), r.get("state", "")) for r in kept}) if cfg.get("show_duplicates") else len(kept)
    kept_cats = Counter(r.get("category_primary", "") for r in kept)
    cut_cats = Counter(
        r.get("category_primary", "") for r in rows if keep_row(cfg, r)[0] is False
    )
    return {
        "name": name, "raw": len(rows), "kept": len(kept), "deduped": deduped,
        "removed": dict(removed), "kept_cats": kept_cats.most_common(12),
        "cut_cats": cut_cats.most_common(8), "leaks": leak_scan(cfg, kept),
        "states": len({r.get("state", "") for r in kept if r.get("state")}),
        "sample": [r.get("business_name", "") for r in kept[:6]],
    }


def main() -> int:
    print("=" * 78)
    print("LOCAL FILTER SIMULATION - all 8 -cursor filters")
    print("=" * 78)
    grand = []
    for name, cfg in FILTERS.items():
        if not cfg["raw_csv"].exists():
            print(f"\n## {name}: MISSING dataset {cfg['raw_csv']}")
            continue
        r = run_one(name, cfg)
        grand.append(r)
        pct = 100 * r["kept"] / r["raw"] if r["raw"] else 0
        print(f"\n## {name}")
        print(f"   raw={r['raw']:,}  kept={r['kept']:,} ({pct:.1f}%)  "
              f"addr-deduped={r['deduped']:,}  states={r['states']}")
        print(f"   removed by group: {r['removed']}")
        print(f"   leak sanity (kept rows still matching an exclude): {r['leaks']}")
        print(f"   surviving category_primary (top): "
              + ", ".join(f"{c or '(blank)'}:{n}" for c, n in r['kept_cats'][:8]))
        print(f"   cut category_primary (top): "
              + ", ".join(f"{c or '(blank)'}:{n}" for c, n in r['cut_cats']))
        print(f"   sample kept: {', '.join(s for s in r['sample'] if s)}")

    print("\n" + "=" * 78)
    print("SUMMARY")
    print(f"{'filter':18} {'raw':>8} {'kept':>8} {'kept%':>7} {'deduped':>9} {'leaks':>6}")
    for r in grand:
        pct = 100 * r["kept"] / r["raw"] if r["raw"] else 0
        print(f"{r['name']:18} {r['raw']:>8,} {r['kept']:>8,} {pct:>6.1f}% {r['deduped']:>9,} {r['leaks']:>6}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
