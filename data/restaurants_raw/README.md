# Restaurants raw analysis database

Raw **category-only** pull from the Overture `PoiDetail` data — every record where:

- `basic_category` = `restaurant`

**No name excludes, no category excludes, no confidence floor.** This is the
unfiltered base we analyze to design the production restaurant filter. Because
restaurants are dense, most pins hit the per-pin `max_results` cap (200).

## Files

| File | Description |
|---|---|
| `restaurants_master.csv` | One row per unique Overture POI (`id` deduped) |
| `restaurants_master.json` | Same data as JSON |
| `pins.csv` | The search pins used (reused from `coffee_tea_raw/pins.csv`): `label,latlog,distance_miles` |

## How it is built

`scripts/scrape_restaurants.py` logs into the staging Django admin filter builder
(credentials in `.env`, gitignored), runs the raw restaurant category pull across
every pin in `pins.csv` (with pagination + retry/backoff), and merges results into
`restaurants_master.csv`, deduped by Overture `id`. Each POI records which pin(s) it
appeared in (`source_examples`). Per-pin `max_results` is capped (default 200) so
dense metros don't swamp the geographic sample.

```bash
pip install requests
python scripts/scrape_restaurants.py --pins data/coffee_tea_raw/pins.csv   # full pull
python scripts/scrape_restaurants.py --pin "27.4945,-80.3383" --label test # single pin
python scripts/analyze_restaurants.py                                       # summary stats
```

Current snapshot: **28,019 unique POIs** across 142 pins (50 states + DC). Most
pins saturate the 200-row cap, so this is a broad geographic sample rather than a
full census of US restaurants.

## Columns

`id`, `business_name`, `business_address`, `city`, `state`, `zipcode`,
`zipcode_full`, `basic_category`, `category_primary`, `category_alternate`,
`taxonomy_primary`, `confidence`, `operating_status`, `name_common`,
`brand_name_primary`, `websites`, `emails`, `socials`, `phone_num`,
`latitude`, `longitude`, `search_latlog`, `search_distance_miles`,
`source_examples`.
