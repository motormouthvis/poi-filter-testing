"""Build noise_annotations.csv by matching curated labels to master_list rows."""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MASTER = REPO / "data" / "cafe_filter_examples" / "master_list.csv"
OUT = REPO / "data" / "cafe_filter_examples" / "noise_annotations.csv"

# (substring match on business_name lower, verdict, reason, tier_a_token or enrichment)
LABELS: list[tuple[str, str, str, str]] = [
    ("mcdonald", "exclude", "Fast food, not sit-down cafe", "*mcdonald*"),
    ("wfm coffee", "exclude", "Whole Foods in-store counter", "*wfm coffee*"),
    ("7-eleven", "exclude", "Convenience store co-location", "*7-eleven*"),
    ("proudly serve", "exclude", "Licensed hotel/c-store counter", "*proudly serve*"),
    ("wild bean", "exclude", "BP gas-station cafe brand", "*wild bean*"),
    ("clean eatz", "exclude", "Meal-prep, not cafe", "*clean eatz*"),
    ("nutrition", "exclude", "Herbalife-style nutrition club", "*nutrition*"),
    ("protein harbor", "exclude", "Nutrition/smoothie club miscategorized", "is_nutrition_club"),
    ("wave 31", "exclude", "Phantom listing; low conf, no website", "widget_quality_gate"),
    ("kava bar", "exclude", "Kava lounge, not coffee shop", "*kava bar*"),
    ("kava lounge", "exclude", "Kava lounge, not coffee shop", "*kava lounge*"),
    ("tax expresso", "exclude", "Tax prep junk name", "*tax expresso*"),
    ("tax service", "exclude", "Tax prep junk name", "*tax service*"),
    ("lee internet partners", "exclude", "Bad/test listing", "widget_quality_gate"),
    ("qa cafe flatiron", "exclude", "Test/office listing", "widget_quality_gate"),
    ("amazon go", "exclude", "Pickup counter, not sit-down", "is_in_store_concession"),
    ("7 brew", "keep", "Drive-through chain — product decision", ""),
    ("dutch bros", "keep", "Drive-through chain — product decision", ""),
    ("ellianos", "keep", "Drive-through chain — product decision", ""),
    ("panera", "keep", "Bakery-cafe — product decision", ""),
    ("cha cha matcha", "keep", "Bubble tea — product decision", ""),
    ("heytea", "keep", "Bubble tea — product decision", ""),
    ("lelecha", "keep", "Bubble tea — product decision", ""),
    ("mudslingers", "keep", "Regional brand — product decision", ""),
    ("bohemio", "keep", "Real local cafe despite low confidence", ""),
    ("good vibez coffee kava kratom", "exclude", "Kava/kratom shop", "enrichment"),
]


def main() -> None:
    rows = list(csv.DictReader(MASTER.open(encoding="utf-8")))
    annotations: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for row in rows:
        name = (row.get("business_name") or "").lower()
        for needle, verdict, reason, mechanism in LABELS:
            if needle in name:
                poi_id = row["id"]
                if poi_id in seen_ids:
                    break
                seen_ids.add(poi_id)
                annotations.append(
                    {
                        "id": poi_id,
                        "business_name": row["business_name"],
                        "city": row.get("city", ""),
                        "state": row.get("state", ""),
                        "verdict": verdict,
                        "reason": reason,
                        "mechanism": mechanism,
                        "confidence": row.get("confidence", ""),
                        "websites": row.get("websites", ""),
                        "source_batch_hint": row.get("source_batch_hint", ""),
                    }
                )
                break

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "business_name",
                "city",
                "state",
                "verdict",
                "reason",
                "mechanism",
                "confidence",
                "websites",
                "source_batch_hint",
            ],
        )
        writer.writeheader()
        writer.writerows(sorted(annotations, key=lambda r: (r["verdict"], r["business_name"])))

    print(f"Wrote {len(annotations)} annotations to {OUT}")


if __name__ == "__main__":
    main()
