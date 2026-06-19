# Hospitals raw analysis database

Raw **category-only** pull from the Overture `PoiDetail` data — every record where:

- `basic_category` contains `hospital`, **or**
- `category_primary` ∈ {`hospital`, `emergency_room`, `medical_center`}

**No name excludes, no confidence floor.** This is the unfiltered base we analyze
to design the hospital (24/7 ER) filter. Because matching is *contains/substring*,
the `medical_center` token also pulls the entire `outpatient_care_facility`
universe (urgent care, clinics, doctor offices), and the `hospital` token also
grabs `animal_hospital`, `emergency_pet_hospital`, `hospital_equipment_and_supplies`,
and `hospitalist`. That noise is intentional here — we keep it so the analysis can
measure and design excludes against it.

## Files

| File | Description |
|---|---|
| `hospitals_master.csv` | One row per unique Overture POI (`id` deduped) |
| `hospitals_master.json` | Same data as JSON |

(The search pins are reused from `data/coffee_tea_raw/pins.csv`.)

## How it is built

`scripts/scrape_hospitals.py` logs into the staging Django admin filter builder
(credentials in `.env`, gitignored), runs the raw hospital category pull across
every pin in `pins.csv` (with pagination + retry/backoff), and merges results into
`hospitals_master.csv`, deduped by Overture `id`. Each POI records which pin(s) it
appeared in (`source_examples`). Per-pin `max_results` is capped (default 200) so
dense metros don't swamp the geographic sample.

```bash
pip install requests
python scripts/scrape_hospitals.py --pins data/coffee_tea_raw/pins.csv   # full pull
python scripts/scrape_hospitals.py --pin "27.4945,-80.3382" --label test # single pin
python scripts/analyze_hospitals.py                                       # summary stats
```

Current snapshot: **21,720 unique POIs** across 142 pins (50 states + DC).

## Columns

`id`, `business_name`, `business_address`, `city`, `state`, `zipcode`,
`zipcode_full`, `basic_category`, `category_primary`, `category_alternate`,
`taxonomy_primary`, `confidence`, `operating_status`, `name_common`,
`brand_name_primary`, `websites`, `emails`, `socials`, `phone_num`,
`latitude`, `longitude`, `search_latlog`, `search_distance_miles`,
`source_examples`.
