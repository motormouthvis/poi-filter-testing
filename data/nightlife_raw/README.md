# Nightlife raw analysis database

Raw **category-only** pull from the Overture `PoiDetail` data — every record where:

- `basic_category` contains {`bar`, `nightlife`}, **or**
- `category_primary` matches one of the anchored nightlife tokens:
  `*bar` (ends-with), `night_club`, `nightclub`, `*pub` (ends-with), `lounge`,
  `brewery`, `karaoke`.

**No name excludes, no confidence floor.** This is the unfiltered base we analyze
to design the nightlife (bars / clubs / lounges) filter.

> **Why anchored tokens?** Matching in the admin builder is "contains"
> (substring). A bare `bar` token pulls `barber`, `barbecue_restaurant`,
> `bar_and_grill_restaurant`; a bare `pub` token pulls
> `public_and_government_association`, `notary_public`, `publisher`. The
> ends-with anchors `*bar` / `*pub` keep `bar`, `wine_bar`, `sports_bar`,
> `irish_pub`, `gastropub` while dropping that pure-substring junk. See
> `docs/filters/nightlife.md` for the full noise analysis.

## Files

| File | Description |
|---|---|
| `nightlife_master.csv` | One row per unique Overture POI (`id` deduped) |
| `nightlife_master.json` | Same data as JSON |

The search pins are reused from `data/coffee_tea_raw/pins.csv`
(`label,latlog,distance_miles`) — 142 diverse pins covering all 50 states + DC.

## How it is built

`scripts/scrape_nightlife.py` logs into the staging Django admin filter builder
(credentials in `.env`, gitignored), runs the raw nightlife category pull across
every pin in `pins.csv` (with pagination + retry/backoff), and merges results into
`nightlife_master.csv`, deduped by Overture `id`. Each POI records which pin(s) it
appeared in (`source_examples`). Per-pin `max_results` is capped (default 200) so
dense metros don't swamp the geographic sample.

```bash
pip install requests
python scripts/scrape_nightlife.py --pins data/coffee_tea_raw/pins.csv      # full pull
python scripts/scrape_nightlife.py --pin "27.4945,-80.3382" --label test    # single pin
python scripts/analyze_nightlife.py                                         # summary stats
```

Current snapshot: **22,686 unique POIs** across 142 pins (50 states + DC).

## Columns

`id`, `business_name`, `business_address`, `city`, `state`, `zipcode`,
`zipcode_full`, `basic_category`, `category_primary`, `category_alternate`,
`taxonomy_primary`, `confidence`, `operating_status`, `name_common`,
`brand_name_primary`, `websites`, `emails`, `socials`, `phone_num`,
`latitude`, `longitude`, `search_latlog`, `search_distance_miles`,
`source_examples`.
