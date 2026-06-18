# Shopping centers / malls raw analysis database

Raw **category-only** pull from the Overture `PoiDetail` data — every record where:

- `basic_category` ∈ {`shopping_center`, `shopping_mall`}, **or**
- `category_primary` ∈ {`shopping_center`, `shopping_mall`, `outlet_mall`, `strip_mall`}

**No name excludes, no confidence floor.** This is the unfiltered base we analyze
to design the shopping-center filter. (In practice Overture stores essentially the
whole universe as `basic_category = shopping_mall` + `category_primary =
shopping_center`; the `outlet_mall` / `strip_mall` tokens match via "contains" but
add no distinct category values.)

## Files

| File | Description |
|---|---|
| `shopping_centers_master.csv` | One row per unique Overture POI (`id` deduped) |
| `shopping_centers_master.json` | Same data as JSON |
| `pins.csv` | The search pins used (shared with the coffee/tea pull: `../coffee_tea_raw/pins.csv`) |

## How it is built

`scripts/scrape_shopping.py` logs into the staging Django admin filter builder
(credentials in `.env`, gitignored), runs the raw shopping-center/mall category
pull across every pin in `data/coffee_tea_raw/pins.csv` (with pagination +
retry/backoff), and merges results into `shopping_centers_master.csv`, deduped by
Overture `id`. Each POI records which pin(s) it appeared in (`source_examples`).
Per-pin `max_results` is capped (default 200) so dense metros don't swamp the
geographic sample.

```bash
pip install requests
python scripts/scrape_shopping.py --pins data/coffee_tea_raw/pins.csv   # full pull
python scripts/scrape_shopping.py --pin "27.4945,-80.3382" --label test # single pin
python scripts/analyze_shopping.py                                      # summary stats
```

Current snapshot: **6,360 unique POIs** across 142 pins (50 states + DC). A few
dense metros (NYC, Brooklyn, LA) hit the 200/pin cap, so their counts are
truncated by design. Staging returns transient `503`s on the first few requests
of a cold session; the failed dense pins were re-pulled after a couple of warm-up
requests.

## Columns

`id`, `business_name`, `business_address`, `city`, `state`, `zipcode`,
`zipcode_full`, `basic_category`, `category_primary`, `category_alternate`,
`taxonomy_primary`, `confidence`, `operating_status`, `name_common`,
`brand_name_primary`, `websites`, `emails`, `socials`, `phone_num`,
`latitude`, `longitude`, `search_latlog`, `search_distance_miles`,
`source_examples`.
