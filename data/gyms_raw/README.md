# Gyms / Fitness raw analysis database

Raw **category-only** pull from the Overture `PoiDetail` data — every record where:

- `basic_category` ∈ {`gym`, `fitness_center`}, **or**
- `category_primary` contains any of: `gym`, `fitness_center`, `yoga_studio`,
  `pilates_studio`, `martial_arts`, `boxing_gym`, `climbing_gym`, `crossfit`,
  `sports_and_fitness_instruction`

(Matching is **contains/substring**, so e.g. the `martial_arts` token also pulls
`martial_arts_club` and `chinese_martial_arts_club`, and `climbing_gym` /
`boxing_gym` match `rock_climbing_gym` / `boxing_gym`.)

**No name excludes, no confidence floor.** This is the unfiltered base we analyze
to design the gym/fitness filter.

## Files

| File | Description |
|---|---|
| `gyms_master.csv` | One row per unique Overture POI (`id` deduped) |
| `gyms_master.json` | Same data as JSON |

The search pins are reused from `../coffee_tea_raw/pins.csv` (142 pins,
`label,latlog,distance_miles`).

## How it is built

`scripts/scrape_gyms.py` logs into the staging Django admin filter builder
(credentials in `.env`, gitignored), runs the raw gym/fitness category pull across
every pin in `data/coffee_tea_raw/pins.csv` (with pagination + retry/backoff), and
merges results into `gyms_master.csv`, deduped by Overture `id`. Each POI records
which pin(s) it appeared in (`source_examples`). Per-pin `max_results` is capped
(default 200) so dense metros don't swamp the geographic sample.

```bash
pip install requests
python scripts/scrape_gyms.py --pins data/coffee_tea_raw/pins.csv     # full pull
python scripts/scrape_gyms.py --pin "27.4945,-80.3382" --label test   # single pin
python scripts/analyze_gyms.py                                         # summary stats
```

Current snapshot: **23,788 unique POIs** across 51 states (50 + DC), all 142 pins.

> Note: the 4 densest metro pins (`brooklyn_ny`, `los_angeles_ca`, `chicago_il`,
> `newark_nj`) intermittently return HTTP 503 on the first pass and were
> back-filled by re-running those pins individually (the script dedupes on merge).

## Columns

`id`, `business_name`, `business_address`, `city`, `state`, `zipcode`,
`zipcode_full`, `basic_category`, `category_primary`, `category_alternate`,
`taxonomy_primary`, `confidence`, `operating_status`, `name_common`,
`brand_name_primary`, `websites`, `emails`, `socials`, `phone_num`,
`latitude`, `longitude`, `search_latlog`, `search_distance_miles`,
`source_examples`.
