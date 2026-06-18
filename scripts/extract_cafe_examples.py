"""Extract POI rows from cafe-filter validation HTML pasted in agent transcripts."""

from __future__ import annotations

import csv
import html
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT = (
    Path.home()
    / ".cursor/projects/c-Users-bill-Dropbox-Programming-Cursor-poi-filter-testing"
    / "agent-transcripts/67095113-8e44-47dc-9750-53676984347f"
    / "67095113-8e44-47dc-9750-53676984347f.jsonl"
)

ROW_RE = re.compile(r"<tr><td class=\"action-checkbox\".*?</tr>", re.DOTALL)
LINK_NAME_RE = re.compile(r'class="field-business_name"><a[^>]*>([^<]+)</a>')
FIELD_RE = re.compile(
    r'class="field-([^"]+)">([^<]*(?:<a[^>]*>[^<]*</a>)?[^<]*)</t[dh]>'
)
UUID_RE = re.compile(r'value="([0-9a-f-]{36})"')

CSV_COLUMNS = [
    "id",
    "business_name",
    "business_address",
    "city",
    "state",
    "zipcode",
    "basic_category",
    "category_primary",
    "category_alternate",
    "taxonomy_primary",
    "confidence",
    "operating_status",
    "brand_name_primary",
    "websites",
    "latitude",
    "longitude",
    "search_latlog",
    "search_distance_miles",
    "source_batch_hint",
]


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value.strip())
    return "" if value == "-" else value


# Search pins observed in validation HTML exports (lat, lon prefix → batch label).
BATCH_BY_PIN: list[tuple[str, str, str]] = [
    ("27.425393", "50", "batch_1_fort_pierce_fl_50mi"),
    ("27.462447", "10", "batch_1_fort_pierce_fl_10mi"),
    ("27.494997", "10", "batch_1_fort_pierce_fl_10mi_rerun"),
    ("27.4945", "10", "batch_1_fort_pierce_fl_10mi_rerun"),
    ("32.0809", "50", "batch_2_savannah_ga_50mi"),
    ("32.081", "50", "batch_2_savannah_ga_50mi"),
    ("32.061246", "50", "batch_2_savannah_ga_50mi"),
    ("41.239", "50", "batch_2_warren_oh_50mi"),
    ("41.24", "50", "batch_2_warren_oh_50mi"),
    ("41.237964", "10", "batch_2_warren_oh_10mi"),
    ("32.934516", "75", "batch_3_alexander_city_al_75mi"),
    ("40.748578", "20", "batch_4_nyc_penn_station_20mi"),
    ("40.748", "20", "batch_4_nyc_penn_station_20mi"),
    ("34.045806", "5", "batch_5_la_dtla_5mi"),
    ("34.045", "5", "batch_5_la_dtla_5mi"),
]


def infer_batch_hint(latlog: str, distance: str, row_count: int) -> str:
    latlog_clean = latlog.replace(" ", "")
    dist = distance.rstrip("0").rstrip(".") if "." in distance else distance
    for lat_prefix, dist_prefix, label in BATCH_BY_PIN:
        if lat_prefix in latlog_clean and dist.startswith(dist_prefix):
            return label
    return f"unknown_{latlog_clean}_{distance}mi_{row_count}rows"


def parse_html_chunk(chunk: str) -> list[dict[str, str]]:
    latlog_m = re.search(r'name="latlog"[^>]*\n\n  value="([^"]+)"', chunk)
    if not latlog_m:
        latlog_m = re.search(r'name="latlog"[^>]*value="([^"]+)"', chunk)
    latlog = latlog_m.group(1).strip() if latlog_m else ""

    dist_m = re.search(r'name="distance_miles"[^>]*\n\n  value="([^"]+)"', chunk)
    if not dist_m:
        dist_m = re.search(r'name="distance_miles"[^>]*value="([^"]+)"', chunk)
    distance = dist_m.group(1).strip() if dist_m else ""

    rows: list[dict[str, str]] = []
    for row_html in ROW_RE.findall(chunk):
        rec: dict[str, str] = {
            "search_latlog": latlog,
            "search_distance_miles": distance,
        }
        name_m = LINK_NAME_RE.search(row_html)
        if name_m:
            rec["business_name"] = html.unescape(name_m.group(1))

        id_m = UUID_RE.search(row_html)
        if id_m:
            rec["id"] = id_m.group(1)

        for fm in FIELD_RE.finditer(row_html):
            key, val = fm.group(1), clean(fm.group(2))
            if key == "business_name" and "business_name" in rec:
                continue
            rec[key] = val

        if rec.get("id"):
            rows.append(rec)

    hint = infer_batch_hint(latlog, distance, len(rows))
    for rec in rows:
        rec["source_batch_hint"] = hint
    return rows


def load_html_chunks(transcript_path: Path) -> list[str]:
    chunks: list[str] = []
    for line in transcript_path.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("role") != "user":
            continue
        for part in obj.get("message", {}).get("content", []):
            text = part.get("text", "")
            if "field-business_name" in text and "result_list" in text:
                chunks.append(text)
    return chunks


def main() -> int:
    transcript_path = Path(sys.argv[1]) if len(sys.argv) > 1 else TRANSCRIPT
    if not transcript_path.exists():
        print(f"Transcript not found: {transcript_path}", file=sys.stderr)
        return 1

    chunks = load_html_chunks(transcript_path)
    print(f"Found {len(chunks)} HTML result pages")

    all_rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for chunk in chunks:
        for rec in parse_html_chunk(chunk):
            poi_id = rec["id"]
            if poi_id not in seen_ids:
                seen_ids.add(poi_id)
                all_rows.append(rec)

    out_dir = REPO_ROOT / "data" / "cafe_filter_examples"
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "master_list.csv"
    json_path = out_dir / "master_list.json"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for rec in sorted(all_rows, key=lambda r: (r.get("state", ""), r.get("city", ""), r.get("business_name", ""))):
            writer.writerow(rec)

    json_path.write_text(
        json.dumps(all_rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Summary by batch hint
    by_batch: dict[str, int] = {}
    for rec in all_rows:
        hint = rec.get("source_batch_hint", "unknown")
        by_batch[hint] = by_batch.get(hint, 0) + 1

    summary_path = out_dir / "README.md"
    lines = [
        "# Cafe filter validation — master POI list",
        "",
        f"**{len(all_rows)} unique POI records** extracted from {len(chunks)} admin HTML exports",
        "in the cafe-filter design conversation.",
        "",
        "## Files",
        "",
        "| File | Description |",
        "|---|---|",
        "| `master_list.csv` | One row per unique Overture POI (`id` deduped) |",
        "| `master_list.json` | Same data as JSON array |",
        "| `noise_annotations.csv` | Curated noise/keep labels from filter tuning |",
        "",
        "## Records by source batch (inferred from search pin + radius)",
        "",
        "| Batch hint | Unique POIs |",
        "|---|---|",
    ]
    for hint, count in sorted(by_batch.items()):
        lines.append(f"| `{hint}` | {count} |")
    lines.extend(
        [
            "",
            "## Columns",
            "",
            "See `master_list.csv` header. Key fields for filter tuning:",
            "",
            "- `business_name`, `category_primary`, `category_alternate` — include/exclude decisions",
            "- `confidence`, `websites` — widget quality-gate candidates",
            "- `search_latlog`, `search_distance_miles` — which validation run surfaced the row",
            "",
            "## Regenerate",
            "",
            "```bash",
            "python scripts/extract_cafe_examples.py",
            "```",
            "",
        ]
    )
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {len(all_rows)} rows to {csv_path}")
    print("By batch:")
    for hint, count in sorted(by_batch.items()):
        print(f"  {hint}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
