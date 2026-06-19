"""Tune the Hospitals v2 category_alternate exclude list from raw data.

Goal: find category_alternate tokens that indicate a physician office / specialty
clinic / admin (NOT a 24-hr ER hospital), without dropping rows that carry a real
emergency-room signal.

For each alternate token we report:
  total   = rows (category_primary~hospital/ER) whose alternate list contains it
  er      = how many of those ALSO carry an ER signal (primary=emergency_room or
            alternate contains emergency_room)
Tokens with high total and ~0 er are safe excludes.
"""
from __future__ import annotations

import csv
from collections import Counter

from filter_configs import FILTERS

RAW = FILTERS["hospital-cursor"]["raw_csv"]


def er_signal(row: dict) -> bool:
    cp = (row.get("category_primary", "") or "").lower()
    alt = (row.get("category_alternate", "") or "").lower()
    return "emergency_room" in cp or "emergency_room" in alt


def main() -> int:
    rows = list(csv.DictReader(RAW.open(encoding="utf-8")))
    # universe = the include set (category_primary contains hospital or emergency_room)
    uni = [r for r in rows
           if "hospital" in (r.get("category_primary", "") or "").lower()
           or "emergency_room" in (r.get("category_primary", "") or "").lower()]
    total = Counter()
    er = Counter()
    for r in uni:
        alts = {a.strip().lower() for a in (r.get("category_alternate", "") or "").split(",") if a.strip()}
        sig = er_signal(r)
        for a in alts:
            total[a] += 1
            if sig:
                er[a] += 1
    print(f"include universe rows: {len(uni)}  (ER-signal rows: {sum(1 for r in uni if er_signal(r))})")
    print(f"\n{'alternate token':40} {'total':>7} {'er':>6} {'er%':>6}")
    for tok, n in total.most_common(45):
        e = er[tok]
        pct = 100 * e / n if n else 0
        print(f"{tok:40} {n:>7} {e:>6} {pct:>5.1f}%")

    # ---- v2 recall/precision guardrail ----
    from simulate_filters import keep_row
    cfg = FILTERS["hospital-cursor"]
    er_rows = [r for r in rows if er_signal(r)]
    er_kept = sum(1 for r in er_rows if keep_row(cfg, r)[0])
    kept = [r for r in rows if keep_row(cfg, r)[0]]
    print("\n--- hospital-cursor v2 applied to full raw ---")
    print(f"raw={len(rows):,}  kept={len(kept):,} ({100*len(kept)/len(rows):.1f}%)")
    print(f"ER-signal rows: {len(er_rows)}  kept={er_kept} "
          f"({100*er_kept/len(er_rows):.1f}% ER recall)  dropped={len(er_rows)-er_kept}")
    # show what dropped the ER-signal rows we lost
    drop_reasons = Counter()
    for r in er_rows:
        ok, why = keep_row(cfg, r)
        if not ok:
            drop_reasons[why] += 1
    print(f"ER-signal drop reasons: {dict(drop_reasons)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
