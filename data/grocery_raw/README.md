# Grocery raw analysis database

Raw **category-only** pull from the Overture `PoiDetail` data — every record where:

- `basic_category` ∈ {`food_and_beverage_store`}, **or**
- `category_primary` ∈ {`supermarket`, `grocery_store`, `specialty_grocery_store`, `wholesale_grocer`}

**No name excludes, no brand whitelist, no confidence floor.** This is the
unfiltered base we analyze to design the next grocery filter.

## Files

| File | Description |
|---|---|
| `grocery_master.csv` | One row per unique Overture POI (`id` deduped) |
| `grocery_master.json` | Same data as JSON |
| `pins.csv` | The search pins used: `label,latlog,distance_miles` (reused from `coffee_tea_raw`) |

## How it is built

`scripts/scrape_grocery.py` logs into the staging Django admin filter builder
(credentials in `.env`, gitignored), runs the raw grocery category pull across
every pin in `pins.csv` (with pagination + retry/backoff), and merges results into
`grocery_master.csv`, deduped by Overture `id`. Each POI records which pin(s) it
appeared in (`source_examples`). Per-pin `max_results` is capped (default 200) so
dense metros don't swamp the geographic sample.

```bash
pip install requests
python scripts/scrape_grocery.py --pins data/coffee_tea_raw/pins.csv   # full pull
python scripts/scrape_grocery.py --pin "27.4945,-80.3382" --label test # single pin
python scripts/analyze_grocery.py                                       # summary stats
```

Current snapshot: **23,664 unique POIs** across 142 pins (50 states + DC).

## Columns

`id`, `business_name`, `business_address`, `city`, `state`, `zipcode`,
`zipcode_full`, `basic_category`, `category_primary`, `category_alternate`,
`taxonomy_primary`, `confidence`, `operating_status`, `name_common`,
`brand_name_primary`, `websites`, `emails`, `socials`, `phone_num`,
`latitude`, `longitude`, `search_latlog`, `search_distance_miles`,
`source_examples`.
