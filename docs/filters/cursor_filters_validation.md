# `-cursor` saved filters — creation + validation report

**Date:** 2026-06-19 · **Env:** `https://staging.dreamneighborhood.com`

Eight production-candidate filters were created in the PoiDetail admin (the
`-cursor` set), validated by local simulation over the raw datasets, and live-
tested across five geographically diverse pins. All eight pass with **zero
exclude leaks** and **clean category distributions**.

Reproduce with:

```
python scripts/simulate_filters.py            # local checks over raw data
python scripts/create_and_test_filters.py     # create/update + live test
python scripts/create_and_test_filters.py --test-only
```

Definitions live in `scripts/filter_configs.py` (shared by both scripts) and
mirror the §0 sections of each `docs/filters/<category>.md`.

## Saved filters (live in staging)

| Filter name | saved_filter_id | Source doc |
|---|---|---|
| `gym-cursor` | 430 | `gyms.md` |
| `park-cursor` | 431 | `parks.md` |
| `shopping-cursor` | 432 | `shopping_centers.md` |
| `nightlife-cursor` | 433 | `nightlife.md` |
| `hospital-cursor` | 434 | `hospitals.md` |
| `cafe-cursor` | 435 | `cafes.md` |
| `grocery-cursor` | 436 | `grocery.md` |
| `restaurant-cursor` | 437 | `restaurants.md` |

> Created via the change-list "Save as New Filter" action (a GET with
> `save_filter_name`). Existing `-cursor` filters are **updated in place**
> (`update_saved_filter` + `saved_filter_id`) on re-run, never duplicated. The
> pre-existing capitalized filters (`Gym`, `Cafe`, `Hospital`, …) were left
> untouched.

## Key finding: the admin strips a leading `*` on save

Round-tripping saved records proved that **a leading `*` is dropped when a filter
is saved**, so the reference doc's `*x*` "contains" tokens silently degrade:

| Entered | Stored | Became |
|---|---|---|
| `*catering*` | `catering*` | starts-with (missed "DiMichelli's Catering") |
| `*bar` | `bar` | contains (pulled barber/barbecue/bar_and_grill) |
| `*pub` | `pub` | contains (pulled 109 `public_*` gov/school rows) |
| `catering` | `catering` | contains ✓ |
| `"pub"` | `"pub"` | exact ✓ |

**Fix applied everywhere:** use plain tokens (contains), `x*` (starts-with), or
`"x"` (exact) only — never lead with `*`. Nightlife additionally uses `"pub"`
exact + excludes `restaurant`/`barber`/`bartender` to clean `bar`/`pub` contains
over-reach. Full detail in `admin-filter-builder.md`.

This was caught only because the live test scans **both** exclude leaks **and**
the surviving category distribution (include-side over-reach is invisible to an
exclude-only check).

## Local simulation (over the raw datasets)

`leaks` = kept rows that still match an exclude token (should be 0).

| filter | raw | kept | kept% | addr-deduped | leaks |
|---|---|---|---|---|---|
| gym-cursor | 23,788 | 22,662 | 95.3% | 18,765 | 0 |
| park-cursor | 25,187 | 14,360 | 57.0% | 11,317 | 0 |
| shopping-cursor | 6,360 | 6,331 | 99.5% | 5,498 | 0 |
| nightlife-cursor | 22,686 | 20,406 | 89.9% | 16,615 | 0 |
| hospital-cursor | 21,720 | 6,696 | 30.8% | 4,333 | 0 |
| cafe-cursor | 18,483 | 18,317 | 99.1% | 16,453 | 0 |
| grocery-cursor | 23,664 | 10,567 | 44.7% | 9,599 | 0 |
| restaurant-cursor | 28,019 | 20,657 | 73.7% | 15,666 | 0 |

## Live multi-location test (final, corrected filters)

Result counts per pin (`250`/`200` = hit the max-results cap). All `leaks = 0`.

| filter | NYC | Chicago | Denver | Ft. Pierce | Bozeman | leaks |
|---|---|---|---|---|---|---|
| gym-cursor | 250 | 250 | 250 | 72 | 96 | 0 |
| park-cursor | 200 | 200 | 200 | 116 | 79 | 0 |
| shopping-cursor | 52 | 29 | 41 | 5 | 6 | 0 |
| nightlife-cursor | 250 | 250 | 250 | 64 | 96 | 0 |
| hospital-cursor | 192 | 160 | 86 | 9 | 6 | 0 |
| cafe-cursor | 250 | 250 | 250 | 22 | 75 | 0 |
| grocery-cursor | 250 | 183 | 171 | 51 | 34 | 0 |
| restaurant-cursor | 200 | 200 | 200 | 200 | 185 | 0 |

**Surviving categories were clean for every filter**, e.g.:
- nightlife: bar, cocktail_bar, lounge, pub, brewery, sports_bar, wine_bar,
  irish_pub, gastropub, beer_bar, dive_bar, hotel_bar (no government/school/barber)
- hospital: hospital, emergency_room, childrens_hospital
- grocery: grocery_store, supermarket, specialty/asian/organic/international, wholesale_grocer
- restaurant: pizza/american/mexican/italian/seafood/burger/sushi/steakhouse + bar_and_grill (kept by design)

## Deferred (requires dev)

The compound quality gate (`confidence < 0.5–0.7 AND no website`) still cannot be
expressed in the admin (single `min_confidence` + separate `has_website` only).
`hospital-cursor` and `restaurant-cursor` use `min_confidence = 0.7` (safe — the
`0.77` sentinel survives); the other six leave it blank. See each doc's §0 note.
