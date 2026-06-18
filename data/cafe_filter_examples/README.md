# Cafe filter validation — master POI list

**1617 unique POI records** extracted from 19 admin HTML exports
in the cafe-filter design conversation.

## Files

| File | Description |
|---|---|
| `master_list.csv` | One row per unique Overture POI (`id` deduped) |
| `master_list.json` | Same data as JSON array |
| `noise_annotations.csv` | Curated noise/keep labels from filter tuning |

## Records by source batch (inferred from search pin + radius)

| Batch hint | Unique POIs |
|---|---|
| `batch_1_fort_pierce_fl_10mi` | 22 |
| `batch_1_fort_pierce_fl_50mi` | 226 |
| `batch_2_savannah_ga_50mi` | 210 |
| `batch_2_warren_oh_10mi` | 290 |
| `batch_3_alexander_city_al_75mi` | 469 |
| `batch_4_nyc_penn_station_20mi` | 200 |
| `batch_5_la_dtla_5mi` | 200 |

## Columns

See `master_list.csv` header. Key fields for filter tuning:

- `business_name`, `category_primary`, `category_alternate` — include/exclude decisions
- `confidence`, `websites` — widget quality-gate candidates
- `search_latlog`, `search_distance_miles` — which validation run surfaced the row

## Regenerate

```bash
python scripts/extract_cafe_examples.py
```
