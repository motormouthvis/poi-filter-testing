# Parks raw analysis database

Raw **category-only** pull from the Overture `PoiDetail` data — every record where:

- `basic_category` contains `park`, **or**
- `category_primary` contains any of {`park`, `state_park`, `national_park`,
  `dog_park`, `playground`, `garden`, `nature_preserve`, `botanical_garden`}

**No name excludes, no confidence floor.** This is the unfiltered base we analyze
to design the next parks filter. Because the admin matches by *substring*, this
intentionally pulls noise (`mobile_home_park`, `rv_park`, `parking`,
`amusement_park`, `skate_park`, `nursery_and_gardening`, ...) so we can see and
exclude it when designing the filter.

## Files

| File | Description |
|---|---|
| `parks_master.csv` | One row per unique Overture POI (`id` deduped) |
| `parks_master.json` | Same data as JSON |
| `pins.csv` | The search pins used: `label,latlog,distance_miles` (reused from `data/coffee_tea_raw/pins.csv`) |

## How it is built

`scripts/scrape_parks.py` logs into the staging Django admin filter builder
(credentials in `.env`, gitignored), runs the raw parks category pull across
every pin in `pins.csv` (with pagination + retry/backoff), and merges results into
`parks_master.csv`, deduped by Overture `id`. Each POI records which pin(s) it
appeared in (`source_examples`). Per-pin `max_results` is capped (default 200) so
dense metros don't swamp the geographic sample.

```bash
pip install requests
python scripts/scrape_parks.py --pins data/coffee_tea_raw/pins.csv   # full pull
python scripts/scrape_parks.py --pin "27.4945,-80.3382" --label test # single pin
python scripts/analyze_parks.py                                      # summary stats
```

Current snapshot: **25,187 unique POIs** across all 142 pins (51 states + DC; the 4 dense metros were backfilled at 1 mi).
The 4 densest metros (`new_york_ny`, `brooklyn_ny`, `los_angeles_ca`, `chicago_il`)
returned a server-side **503** on the 10-mile parks query (the spatial scan exceeds
the staging gateway's ~30s timeout for very dense areas) and were skipped; all 51
states/DC are still represented from the surrounding pins. See `docs/filters/parks.md`.

## Columns

`id`, `business_name`, `business_address`, `city`, `state`, `zipcode`,
`zipcode_full`, `basic_category`, `category_primary`, `category_alternate`,
`taxonomy_primary`, `confidence`, `operating_status`, `name_common`,
`brand_name_primary`, `websites`, `emails`, `socials`, `phone_num`,
`latitude`, `longitude`, `search_latlog`, `search_distance_miles`,
`source_examples`.
