# Filter: Restaurants (sit-down / full-service)

> **Status: v1 (draft) — evidence-based proposal from the raw category pull.**
> Built from `data/restaurants_raw/` (28,019 unique POIs, 50 states + DC, 142 pins).
> Generic USA — no one-off local business names.

**Goal:** surface real **sit-down / full-service restaurants** — every cuisine
type plus bar-and-grills. Excluded: fast food, food trucks / street vendors,
coffee shops / cafes / bakeries (their own filters), bars / nightclubs /
breweries / wineries (nightlife), caterers, food courts, and non-food businesses
mislabeled as `restaurant` (gas stations, convenience stores, markets).

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings.

---

## 0. Admin panel parameters (paste-ready, v1)

Enter these in the PoiDetail filter builder. The compound quality gate is
**deferred** (needs dev) — see note at the bottom.

| Control | Value |
|---|---|
| Saved filter (Save as) | `Restaurants` |
| Latitude, Longitude | *(your test point)* |
| Distance (miles) | `10` (use `1`–`3` in dense urban cores) |
| Max results | `200` |
| Min confidence | `0.7` (kept — see §5; safely below the `0.77` sentinel) |
| Website | `Any` |
| Operating status | `open` |
| Deduplicate addresses | **ON** (collapses ~26% redundant rows — see §5) |

**Basic category — include:**

```
restaurant
```

**Category primary — exclude:**

```
fast_food_restaurant
food_truck
street_vendor
coffee_shop
cafe
bakery
nightclub
brewery
distillery
winery
caterer
food_court
cafeteria
```

**Category alternate — exclude:**

```
fast_food_restaurant
food_truck
street_vendor
coffee_shop
cafe
bakery
nightclub
brewery
distillery
winery
caterer
food_court
gas_station
convenience_store
grocery_store
supermarket
```

**Business name primary — exclude:**

```
*catering*
*food truck*
*taco truck*
chevron
shell
exxon
mobil
marathon
circle k
7-eleven
```

**Query builder:**

```
basic_category_include
  and category_primary_exclude
  and category_alternate_exclude
  and name_primary_exclude
```

All other include/exclude boxes: **empty**.

> **Do NOT add a bare `bar` token to any category exclude box.** Substring
> matching means `bar` also hits `bar_and_grill_restaurant` (900 rows),
> `barbecue_restaurant` (678) and `salad_bar` (221) — deleting ~1,799 real
> sit-down places. Nightlife is removed with the specific `nightclub` / `brewery`
> / `distillery` / `winery` tokens instead. (In this dataset those primaries don't
> even appear — they're defensive no-ops, see §3.)

> **Deferred (requires dev):** a precise quality gate like `confidence < 0.5 AND
> no website` (drops the unverifiable long tail without touching the `0.77`
> sentinel band) cannot be expressed in the current admin builder, which offers
> only a single numeric `min_confidence` plus a separate `has_website`. Until a
> compound rule is supported, `min_confidence = 0.7` is the pragmatic choice
> (see §5).

---

## 1. Dataset summary (raw pull)

`python scripts/analyze_restaurants.py` on `data/restaurants_raw/restaurants_master.csv`:

| Metric | Value |
|---|---|
| Total unique POIs | **28,019** |
| States covered | **50 + DC** (+ a few dirty values, see note) |
| Has website | 24,923 (88%) |
| No website | 3,096 (11%) |

**Top states:** TX 2,000 · CA 1,796 · FL 1,401 · NY 801 · OH 801 · CO 800 ·
NC 800 · OR 800 · TN 800 · MI 799. (Most pins saturate the 200-row cap, so this
is a broad geographic sample, not a full census.)

> **Data hygiene note:** the `state` column also contains a handful of
> non-standard values — `Calif`, `Mi`, and a few blanks — alongside the 50 USPS
> codes + `DC`. The widget should normalize state strings; the underlying data is
> not perfectly clean.

**`basic_category` breakdown (complete):**

| basic_category | count |
|---|---|
| `restaurant` | 25,822 |
| `fast_food_restaurant` | 2,197 |

> Note: we pulled `basic_category (include) = restaurant`, and substring matching
> means **`fast_food_restaurant` is also pulled in** (it contains `restaurant`).
> That's why 2,197 fast-food rows appear in the raw base — and exactly why the
> production filter must exclude `fast_food_restaurant`.

**`category_primary` breakdown (top 20):**

| category_primary | count |
|---|---|
| `restaurant` (generic) | 3,669 |
| `pizza_restaurant` | 2,426 |
| `american_restaurant` | 2,401 |
| `mexican_restaurant` | 2,303 |
| `fast_food_restaurant` | 2,196 |
| `italian_restaurant` | 1,007 |
| `burger_restaurant` | 995 |
| `bar_and_grill_restaurant` | 900 |
| `seafood_restaurant` | 761 |
| `sushi_restaurant` | 694 |
| `chinese_restaurant` | 691 |
| `barbecue_restaurant` | 678 |
| `breakfast_and_brunch_restaurant` | 620 |
| `steakhouse` | 592 |
| `japanese_restaurant` | 571 |
| `chicken_restaurant` | 500 |
| `thai_restaurant` | 484 |
| `taco_restaurant` | 395 |
| `asian_restaurant` | 391 |
| `salad_bar` | 221 |

**Confidence distribution:**

| Bucket | count | % |
|---|---|---|
| `<0.5` | 2,050 | 7% |
| `0.5–0.7` | 1,160 | 4% |
| `0.7–0.9` | 10,280 | 36% |
| `>=0.9` | 14,529 | 51% |

> **`0.77` is a sentinel default, not a real score.** 8,612 rows (**30%** of the
> dataset) have `confidence` **exactly `0.77`** — including Chipotle, Denny's and
> McDonald's. Any confidence floor set **at or above 0.78** would delete these
> real chains. A `0.7` floor sits safely *below* the sentinel, so it keeps every
> `0.77` record while trimming the genuinely low-confidence tail (see §5).

---

## 2. Include tokens used (raw pull)

These are the tokens entered in `scripts/scrape_restaurants.py` (`CATEGORY_PARAMS`).
The raw pull is intentionally wide — **includes only, no excludes, no confidence
floor** — so the analysis sees everything `basic_category = restaurant` drags in.

**Basic category (include):**

```
restaurant
```

**Query builder:**

```
(basic_category_include)
```

`min_confidence = 0`, `operating_status = open`, `max_results = 200`, all other
boxes empty.

---

## 3. Observed noise / edge cases (evidence from the data)

| Noise type | ~Count | Real examples from the data | Signal | Caught by |
|---|---|---|---|---|
| **Fast food** | 2,196 | `McDonald's`, `Chick-fil-A`, `Jack in the Box` | `category_primary = fast_food_restaurant` | `category_primary_exclude: fast_food_restaurant` |
| **Caterers** (primary is a real `*_restaurant`, so a *primary* exclude misses them) | 120 by alt / 108 by name | `Parkers Soulfood and Catering` (cp=`restaurant`, alt=`caterer`), `Wing Out Events & Catering`, `Bridge Seafood Restaurant & Catering` | `caterer` in `category_alternate`; `catering` in name | `category_alternate_exclude: caterer` **+** `name_primary_exclude: *catering*` |
| **Food trucks / street vendors** | ~57 by name, 1,622 with `fast_food` alt | `Bayou Bros Food Truck and Catering`, `Shindigs Catering Foodtruck`, `taco truck` | `food_truck`/`street_vendor` in alt; `*food truck*` in name | `category_alternate_exclude: food_truck, street_vendor` + name excludes |
| **Gas stations / convenience stores** mislabeled `restaurant` | 10 by alt | `Casa Latina` (cp=`mexican_restaurant`, alt=`…,convenience_store`), `Paavo's Pizza` (alt=`…,convenience_store`) | `gas_station`/`convenience_store` in alt; gas-brand in name | `category_alternate_exclude: gas_station, convenience_store` + name brand excludes (`chevron`, `shell`, …) |
| **Markets / grocery hybrids** | 92 by alt / 223 by name | `Anita Street Market` (cp=`mexican_restaurant`, alt=`…,grocery_store`), `Sharks fish&chiken+rooseveltsuperstore` (alt=`grocery_store,…`) | `grocery_store`/`supermarket` in alt; `market` in name | `category_alternate_exclude: grocery_store, supermarket` |
| **Cafeterias** (institutional dining) | ~70 | `Children's Hospital Cafeteria`, `Lakeside Dining Hall`, `Cal/EPA Cafeteria` | `category_primary = cafeteria` | `category_primary_exclude: cafeteria` (also caught by `cafe` substring) |
| **Coffee / cafe / bakery** | small | covered by the dedicated cafe/coffee filter | `coffee_shop`/`cafe`/`bakery`/`tea_room` primary | category excludes |
| **Permanently-closed but still tagged `open`** | unknown — **invisible here** | (Norris's Ribs-style stale rows) | none in the data — `operating_status` is stale | **NOT filterable — enrichment needed (see below)** |

### Two important sharp edges

- **`cafe` substring also matches `cafeteria`.** Excluding `cafe` removes both
  cafes (own filter) and institutional cafeterias — which is what we want here,
  so it's a happy accident. `cafeteria` is also listed explicitly for clarity.
- **Bare `bar` is forbidden** (see §0): it would substring-match
  `bar_and_grill_restaurant`, `barbecue_restaurant` and `salad_bar` — 1,799 real
  restaurants. Nightlife is excluded with `nightclub`/`brewery`/`distillery`/
  `winery` only.

### Defensive no-ops

In the `basic_category = restaurant` universe there are **zero** `nightclub`,
`brewery`, `distillery` or `winery` `category_primary` values — those venues live
under other basic categories. The nightlife excludes are kept anyway as
**harmless guards** so the filter stays correct if Overture re-tags a venue.

### Stale `operating_status` (the "Norris's Ribs" problem)

We pulled with `operating_status = open`, so every row claims to be open and
**no closed venues are visible to filter against**. Permanently-closed
restaurants that Overture still tags `open` (the user's "Norris's Ribs" example,
`confidence 0.77`, which clears the `0.7` gate) therefore **cannot be removed by
any admin filter** — this is a **data-freshness / enrichment** problem, not a
filter problem. Recommend a periodic enrichment pass (Google/Places re-check)
to refresh `operating_status`; flag as **enrichment-needed**.

---

## 4. Proposed filter (v1)

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Restaurants` |
| Distance | `10.0` miles (`1`–`3` urban, `10` rural) |
| Max results | `200` |
| Min confidence | `0.7` (below the `0.77` sentinel; see §5) |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

### Include — Basic category (include)

```
restaurant
```

### Exclude — Category primary (exclude)

```
fast_food_restaurant
food_truck
street_vendor
coffee_shop
cafe
bakery
nightclub
brewery
distillery
winery
caterer
food_court
cafeteria
```

### Exclude — Category alternate (exclude)

Removes venues whose *secondary* category reveals a non-restaurant purpose — this
is where the gas-station / convenience / market / caterer leaks (whose
`category_primary` is a real `*_restaurant`) are actually caught:

```
fast_food_restaurant
food_truck
street_vendor
coffee_shop
cafe
bakery
nightclub
brewery
distillery
winery
caterer
food_court
gas_station
convenience_store
grocery_store
supermarket
```

### Exclude — Business name primary (exclude)

Catches caterers/trucks/gas-brands that carry a clean `*_restaurant` category:

```
*catering*
*food truck*
*taco truck*
chevron
shell
exxon
mobil
marathon
circle k
7-eleven
```

> Bare `market` is **deliberately NOT** a name exclude: it would drop legit
> places like `Anita Street Market` only if you also want to lose `… Market &
> Grill` style restaurants. The `grocery_store`/`supermarket` **alt** excludes
> already remove the true store hybrids without risking restaurant names.

### Query builder

```
basic_category_include
  and category_primary_exclude
  and category_alternate_exclude
  and name_primary_exclude
```

### Quality gate (future — widget-side)

> **Ideal:** drop a row when `confidence < 0.5` AND it has no website. This targets
> the unverifiable long tail (ghost listings, abandoned pages) while protecting
> the 8,612 sentinel-`0.77` records and every websited restaurant. **Deferred
> (requires dev)** — the admin can't express a compound rule, so `min_confidence
> = 0.7` is the interim stand-in.

---

## 5. Min-confidence & dedupe decisions

### Why `min_confidence = 0.7` (kept from the user's filter)

| Option | Effect | Verdict |
|---|---|---|
| `min_confidence = 0.78` | Deletes all 8,612 `0.77`-sentinel rows (Chipotle, Denny's, McDonald's included) | ❌ reject |
| **`min_confidence = 0.7`** | `0.77 > 0.7`, so every sentinel survives; drops the 3,210 rows below `0.7` (11%) — overwhelmingly the low-signal caterer/food-truck/ghost leaks (many at conf 0.2–0.5) | ✅ keep |
| `min_confidence = 0` (none) | Keeps everything, including obvious junk | ⚠️ too loose |

The `0.7` floor is safe **only because it sits below the `0.77` sentinel**. The
key teaching from the gym/cafe work still holds: never set a floor *at or above*
`0.77`. It does **not** catch the stale-closed "Norris's Ribs" case (conf `0.77`
> `0.7`, so it survives) — that's the enrichment problem in §3, not a gate
problem.

### Why **Deduplicate addresses = ON**

The raw pull is full of the same venue listed multiple times:

- **Exact same name + address:** 409 groups, **417 redundant rows** (e.g.
  `Chick-fil-A`, `Marco's Pizza`, `Johnny Rockets`, `O-Ku` each appear 3×).
- **Same address (any name), which `show_duplicates` collapses by keeping the
  highest-confidence record:** ~4,611 address groups, **~7,179 redundant rows
  (~26% of the dataset)**. This also matches the user's reported dups across
  *different* addresses for the same brand (e.g. three `A Touch of Brooklyn`
  rows, `Goodfella's Pizza`, `Big Worm's BBQ`) — those collapse once duplicates
  per address are removed.

Turning **Deduplicate addresses ON** is the single biggest cleanliness win and is
strongly recommended.

---

## 6. How this improves on the user's current `Restaurants` filter

| Issue in the user's saved filter | What happens today | This v1 fix |
|---|---|---|
| **Gas-station leak** ("Chevron of Vero Beach": cp=`restaurant`, alt=`gas_station,convenience_store`) | survives — no gas/convenience exclude | `category_alternate_exclude: gas_station, convenience_store` + name brands (`chevron`, `shell`, …) |
| **Caterer leak** ("DiMichelli's Catering": cp=`restaurant`, so the *category-primary* `caterer` exclude misses it) | survives | adds `category_alternate_exclude: caterer` **and** `name_primary_exclude: *catering*` (the primary exclude alone can't catch a `*_restaurant`-tagged caterer) |
| **Duplicate rows** ("A Touch of Brooklyn", "Goodfella's Pizza", "Big Worm's BBQ" appear multiple times) | all shown — `show_duplicates` is OFF | **Deduplicate addresses ON** → collapses ~26% redundant rows |
| **Stale permanently-closed** ("Norris's Ribs", conf `0.77`) | survives both `operating_status=open` and the `0.7` gate | **cannot be fixed by any filter** — documented as enrichment-needed (§3) |
| **Markets / grocery hybrids** | partially caught by name excludes only | adds `category_alternate_exclude: grocery_store, supermarket` for the alt-tagged hybrids |
| **Cafeterias** | not excluded | adds `category_primary_exclude: cafeteria` |
| **Risk: bare `bar` token** | n/a (user filter doesn't use it) | explicitly rejected — would nuke `bar_and_grill`, `barbecue`, `salad_bar` (1,799 rows) |

The user's existing excludes (`fast_food_restaurant`, `food_truck`,
`street_vendor`, `coffee_shop`, `cafe`, `bakery`, `nightclub`, `brewery`,
`distillery`, `winery`, `caterer`, `food_court`) are all **retained** — this v1
extends them with the alt-list and name handling needed to plug the documented
leaks, and turns on address dedupe.

---

## Appendix A — reproduce

```bash
pip install requests
python scripts/scrape_restaurants.py --pins data/coffee_tea_raw/pins.csv   # full pull (~6-8 min)
python scripts/analyze_restaurants.py                                       # summary stats
```

Raw dataset + column docs: [`../../data/restaurants_raw/README.md`](../../data/restaurants_raw/README.md).
