# Filter: Parks

> **Status: v1 (proposed) — evidence-based draft from a 24,543-row raw pull.**
> Built from `data/parks_raw/` (138 of 142 national pins; 51 states + DC).
> Generic USA — no one-off local business names.

**Goal:** surface real **public parks & green spaces** a family would visit —
neighborhood/city/state/national parks, playgrounds, dog parks, botanical and
community gardens, skate parks, splash/water parks. Exclude commercial,
residential, retail, and infrastructure "parks" that the Overture substring
matching drags in (parking lots, RV/mobile-home parks, garden centers,
landscapers, beer gardens, amusement/trampoline parks, office/industrial parks).

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings.

---

## 0. Admin panel parameters (paste-ready, v1)

Enter these in the PoiDetail filter builder. Compound quality gate is **deferred**
(needs dev) — see note at the bottom.

| Control | Value |
|---|---|
| Saved filter (Save as) | `Parks` |
| Latitude, Longitude | *(your test point)* |
| Distance (miles) | `10` (use `1`–`2` in NYC/Brooklyn/LA/Chicago — see §5 503 note) |
| Max results | `200` |
| Min confidence | *(leave blank)* — real parks often score low / lack a site |
| Website | `Any` |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

**Basic category — include** (use exact `"…"` so `park` ≠ `parking`):

```
"park"
"garden"
"playground"
"dog_park"
"national_park"
```

**Category primary — include** (exact):

```
"park"
"state_park"
"national_park"
"nature_preserve"
"botanical_garden"
"community_gardens"
"dog_park"
"playground"
"skate_park"
"water_park"
```

**Category primary — exclude:**

```
parking
mobile_home_park
rv_park
amusement_park
gardener
nursery_and_gardening
home_and_garden
beer_garden
trampoline_park
atv_recreation_park
hydroponic_gardening
park_and_rides
```

**Business name primary — exclude:**

```
parking
garage
mobile home
trailer park
business park
office park
industrial park
rv park
self storage
```

**Query builder:**

```
(basic_category_include or category_primary_include) and category_primary_exclude and name_primary_exclude
```

All other include/exclude boxes: **empty**. Validated effect: 24,543 → ~14,139 kept (~58%).

> **Deferred (requires dev):** the precise quality gate `confidence < 0.5 AND no
> website` (~532 rows) needs a compound rule the admin doesn't support. Do **not**
> substitute a numeric `min_confidence` — it over-prunes legitimate websiteless
> neighborhood parks.

---

## 1. Dataset (raw pull)

| Metric | Value |
|---|---|
| Unique POIs | **24,543** |
| Pins | 138 of 142 (4 mega-metros 503'd — see §5) |
| States + DC | **51** |
| Has website | 17,339 (70%) · none 7,204 (29%) |
| Confidence | `<0.5` 2,766 · `0.5–0.7` 3,152 · `0.7–0.9` 9,116 · `≥0.9` 9,509 |

Top `basic_category`: `park` 12,395 · **`parking` 5,861** · `hardware_home_and_garden_store` 1,808 ·
`housing_or_property_service` 674 · `home_service` 647 · `amusement_park` 646 ·
`playground` 581 · `dog_park` 484 · `skate_park` 410 · `rv_park` 324 ·
`alcoholic_beverage_venue` 291 · `garden` 218 · `national_park` 169.

Top `category_primary`: `park` 12,287 · **`parking` 5,861** · `nursery_and_gardening` 1,376 ·
`mobile_home_park` 674 · `gardener` 647 · `amusement_park` 646 · `playground` 581 ·
`dog_park` 484 · `home_and_garden` 421 · `skate_park` 410 · `rv_park` 324 ·
`beer_garden` 291 · `botanical_garden` 216 · `national_park` 169 · `water_park` 78 ·
`state_park` 27.

> Reproduce: `python scripts/scrape_parks.py --pins data/coffee_tea_raw/pins.csv`
> then `python scripts/analyze_parks.py`.

---

## 2. Include tokens used for the RAW pull

Sent to the admin so we could *see and measure* the noise (substring/`contains`
match, no excludes, no confidence gate):

**Basic category (include):**

```
park
```

**Category primary (include):**

```
park
state_park
national_park
dog_park
playground
garden
nature_preserve
botanical_garden
```

**Query builder:** `(basic_category_include or category_primary_include)`

These pull the right park universe **plus** heavy noise, because the admin
matches by substring: `park` matches `parking`, `mobile_home_park`, `rv_park`,
`amusement_park`, `skate_park`, `water_park`; and `garden` matches
`nursery_and_gardening`, `gardener`, `home_and_garden`, `beer_garden`.

---

## 3. Observed NOISE (with evidence)

Substring matching is the root cause. Two tokens (`park`, `garden`) generate
~10k junk rows.

| Noise type | Rows | `category_primary` / signal | Examples | Why noise |
|---|---:|---|---|---|
| **Parking lots/garages** | **5,861** | `parking` (matched by `park`*ing*) | `5th & B Parking Garage`, `899 West 5th Avenue Parking`, `Airport Road Car Storage`, `Alachua County Rest Area` | Infrastructure, not a park. Single biggest source. |
| **Garden centers / nurseries** | 1,376 | `nursery_and_gardening` (basic `hardware_home_and_garden_store`) | `Alaska Mill Feed and Garden Center`, `Arthur Campbell Nursery` | Retail. |
| **Mobile-home / trailer parks** | 674 | `mobile_home_park` (basic `housing_or_property_service`) | `Penland Mobile Home Park`, `Top Hand Trailer Court`, `Kodzoff Acres` | Residential. |
| **Landscapers / lawn care** | 647 | `gardener` (basic `home_service`) | `Southern Turf Landscaping`, `McDaniel Land Designs`, `Interiorscapes` | Service business. |
| **Amusement / trampoline parks** | 646 | `amusement_park` | `Urban Air Trampoline Park`, `Funland Amusement Park`, `The Lagoon` | Commercial attraction, paid admission. |
| **Home & garden stores** | 421 | `home_and_garden` (basic `hardware_home_and_garden_store`) | `Bell's Vacuums`, `Al's 5 & 10` | Retail. |
| **RV parks / campgrounds** | 324 | `rv_park` | `Golden Nugget RV Park`, `Avalon RV Park`, `Rosehip Campground` | Lodging, not public park. (Edge — see §4.) |
| **Beer gardens / bars** | 291 | `beer_garden` (basic `alcoholic_beverage_venue`) | `AK Grizzly Bar`, `Buster Belly's`, `Old Shell Growler Station` | Bar, from `garden`. |
| **Office/business/industrial "parks"** | ~115 | `park` by **name** | `Anchorage Business Park`, `Mountain Brook Office Park`, `Campbell Creek Industrial Park` | Commercial real estate labelled `park`. |
| **Park-and-rides** | 4 | `park_and_rides` | — | Transit lot. |

### Edge cases worth a product call

- **`skate_park` (410)** — Overture frequently **mislabels real state parks** as
  `skate_park`: `Baxter State Park - Mount Katahdin`, `Brandywine Creek State Park`,
  `Edness Kimball Wilkins State Park`, `Clinton Lake`. These are legitimate parks,
  so we **keep** `skate_park` (real skate parks are recreational green space too).
- **`water_park` (78)** — basic_category is `park`; mostly **splash pads / water
  gardens** (`Palmore Park Splash Pad`, `Fort Worth Water Gardens`, `Quincy Douglas
  Pool`). Treated as park amenities → **keep**. A handful of paid attractions
  (`Wild River Country`) leak; acceptable.
- **`botanical_garden` (216)** and **`community_gardens` (2)** — real public green
  space → keep. The bare `garden` token's value is *only* these; everything else it
  matched (`nursery`, `gardener`, `home_and_garden`, `beer_garden`) is noise.
- **`rv_park` / campgrounds** — excluded by default (lodging), but if the widget
  wants "outdoor recreation" they could be re-included as a separate layer.
- **No-website / low-confidence parks** — many *legitimate* neighborhood parks have
  no website and mid confidence (e.g. `Coffrin Park` conf 0.66), so a hard quality
  gate over-prunes (see §4 gate options).

---

## 4. Proposed filter (v1)

Strategy: **anchor the include to clean categories** (so the worst noise is never
pulled), then use **name excludes** to remove the real-estate "parks" that are
genuinely tagged `category_primary = park`. Validated against the 24,543-row raw
set: **24,543 → 14,139 kept (57.6%); 10,404 noise dropped; all 51 states/DC
retained.**

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Parks` |
| Distance | `10.0` miles (`1`–`3` urban, `10` rural) |
| Max results | `200` |
| Min confidence | *(empty)* — see gate options below |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

### Include

**Basic category (include)** — exact, to avoid `park`→`parking` bleed:

```
"park"
"garden"
"playground"
"dog_park"
"national_park"
```

**Category primary (include)** — recovers good types not covered by the clean
basic buckets (incl. state parks mislabeled `skate_park`):

```
"state_park"
"national_park"
"nature_preserve"
"botanical_garden"
"community_gardens"
"dog_park"
"playground"
"skate_park"
"water_park"
"park"
```

> Use **exact** (`"…"`) tokens here so `park` does **not** match `parking`,
> `mobile_home_park`, `rv_park`, `amusement_park`. Note `park*` (starts-with) would
> still catch `parking`, so prefer exact.

### Exclude

**Category primary (exclude)** — belt-and-suspenders (largely redundant given exact
includes, but protects against alternate-category bleed if includes are loosened):

```
parking
mobile_home_park
rv_park
amusement_park
gardener
nursery_and_gardening
home_and_garden
beer_garden
trampoline_park
atv_recreation_park
hydroponic_gardening
park_and_rides
```

**Business name primary (exclude)** — removes ~118 real-estate / parking "parks"
that are genuinely tagged `category_primary = park` (substring match):

```
parking
garage
mobile home
trailer park
business park
office park
industrial park
rv park
self storage
```

> **Do NOT add** a bare `park` or `garden` name token (kills everything), and do
> **not** exclude `state`/`water`/`skate`/`dog`/`ball` — those are legitimate park
> names (`Kimball Recreation Area`, splash pads, dog parks).

### Query builder

```
(basic_category_include or category_primary_include)
  and category_primary_exclude
  and name_primary_exclude
```

`or` on includes is required: state parks land in `basic_category = skate_park`
(excluded by the exact basic include) but `category_primary = skate_park`, so the
primary include is what rescues them.

### Quality gate (optional, widget-side)

Parks legitimately lack websites, so the cafe-style hard gate is too aggressive
here. Measured on the 14,139 kept rows:

| Gate | Rows dropped | Verdict |
|---|---:|---|
| `confidence < 0.7 AND no website` | 1,852 | **Too aggressive** — drops real neighborhood parks. |
| `confidence < 0.5 AND no website` | 532 | **Recommended** — trims the low-signal tail. |
| `confidence < 0.3` (any) | 171 | Safe floor for obvious junk. |

Recommendation: ship **no `min_confidence`** in the admin filter; apply
`confidence < 0.5 AND no website` (or a `confidence ≥ 0.3` floor) as a soft
quality gate in the widget so curators can revisit borderline rows.

---

## 5. Data-collection caveat (staging 503s)

The 4 densest metros — `new_york_ny`, `brooklyn_ny`, `los_angeles_ca`,
`chicago_il` — returned a server-side **503 after ~30s** on the 10-mile parks
query. Diagnosed: it is the **spatial radius**, not the tokens —
NYC returns 200 rows in 5.6s at **1 mi** but 503s at **3 mi** and **10 mi**, even
with a `park`-only query. Parks are far denser in raw Overture than coffee shops,
so the 10-mile scan in those metros exceeds the staging gateway timeout. All
other 138 pins succeeded and **all 51 states + DC are still represented**, so the
analysis above is national. To capture the missing metros, re-run those pins at a
smaller radius (1–2 mi) once, e.g.:

```
python scripts/scrape_parks.py --pin "40.7128,-74.0060" --label new_york_ny --distance 1
```

---

## 6. Residual noise (needs data enrichment)

Cannot be removed reliably with category/name tokens:

| Problem | Examples | Needed signal |
|---|---|---|
| Paid attractions tagged `water_park`/`park` | `Wild River Country` | `is_paid_admission` |
| Real parks mislabeled `skate_park`/`amusement_park` | `Baxter State Park` (skate), `Small Boat Launch` (amusement) | upstream Overture category fix |
| Mis-geocoded / test listings | low-conf rows with HQ-style addresses | freshness + confidence policy |
| Same park, many entrances/addresses | large state/national parks | dedup composite key |

---

## Appendix A — config history

- **raw pull:** `basic park` + broad primary set (`park, state_park, national_park,
  dog_park, playground, garden, nature_preserve, botanical_garden`), no excludes,
  no gate → 24,543 rows (≈42% noise).
- **v1 (proposed):** exact category includes + `category_primary_exclude` +
  `name_primary_exclude`; keep `skate_park`/`water_park`/`botanical_garden`; query
  `(basic_category_include or category_primary_include) and category_primary_exclude
  and name_primary_exclude` → 14,139 kept across 51 states/DC.
