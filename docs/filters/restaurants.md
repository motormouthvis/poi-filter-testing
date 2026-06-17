# Filter: Restaurants

> **Status: WORKING (v3) — "good enough to ship for now."**
> On the latest test (lat/lon `27.4612, -80.3035`, 5 mi) this config returns
> **104 results**, down from **158** under v2. The worst noise is gone: the retail
> seafood market (Pelican) is dropped by the confidence gate, name-based market
> excludes catch grocery/fish/meat markets, and address dedup collapses true
> duplicates. Remaining issues are **data-quality problems Overture can't express in
> a boolean filter** — see [Dev team: what to improve next](#dev-team-what-to-improve-next).

**Goal:** surface real sit-down / casual *restaurants* for the mom-centric
home-shopper widget, while excluding fast food, drinking-focused venues (bars,
breweries), cafes, bakeries, food trucks, retail food markets, and services.

This must be a **generic USA solution** — no hardcoded business names or
locale-specific hacks. Every rule below is a general signal, not a Fort-Pierce patch.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for what each field and
the query tokens mean — including the important notes on **match operators**
(`token` = contains, `"token"` = exact, `token*` = starts-with, `*token` = ends-with,
`*token*` = contains-anywhere).

---

## 1. The current working filter (v3) — copy/paste into the admin

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Restaurants` |
| Distance | `5.0` miles |
| Max results | `250` |
| Min confidence | `0.7` |
| Operating status | `open` |
| Deduplicate addresses | **ON** (keep highest-confidence record per address) |

### Include

**Basic category (include):**

```
restaurant
```

Leave **`Category primary (include)`** and **`Category alternate (include)`** EMPTY.
The `basic_category = restaurant` gate does all the inclusion; the old broad
category includes were the original source of the non-restaurant leak.

### Exclude

**Business name primary (exclude):**

```
taco truck
food truck
*market
*market*
supermarket
grocery
fish market
meat market
seafood market
*tienda*
```

**Category primary (exclude):**

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
```

**Category alternate (exclude):**

```
fast_food_restaurant
food_truck
coffee_shop
cafe
bakery
nightclub
brewery
distillery
winery
caterer
food_court
```

Leave the remaining exclude boxes (name common, basic category, taxonomy
primary/alternates) empty.

### Query builder

```
basic_category_include and category_primary_exclude and category_alternate_exclude and name_primary_exclude
```

Plain English: **must** be `basic_category = restaurant`, **and** not match any
primary-category exclude, **and** not match any alternate-category exclude, **and**
its primary name isn't in the name-exclude list.

---

## 2. What changed from v2 → v3 and why it helped

| Lever | v2 | v3 | Effect |
|---|---|---|---|
| Min confidence | `0.0` | **`0.7`** | Drops the worst-tagged noise, incl. the **Pelican Seafood** retail market (conf 0.53) and ghost/duplicate fragments. |
| Deduplicate addresses | OFF | **ON** | Collapses true duplicate rows (e.g. two `Pot Belli Deli` records, `Goodfella's` fragments at one address). |
| Name excludes | truck only | **+ market/grocery/tienda tokens** | Catches retail markets mislabeled as `*_restaurant` (Lama's Kitchen **& Seafood Market**, McManus Seafood, La Michoacana, etc.). |

**Net:** 158 → 104, and the obvious "that's not a restaurant" rows a homebuyer would
notice are largely gone.

---

## 3. Known trade-offs of v3 (accepted for now)

- **Min confidence `0.7` drops some real restaurants.** Genuine spots tagged low in
  Overture (e.g. `Festival Italiano` 0.08, `ZENSHI` 0.27, `Kame` 0.30) won't appear.
  This was an intentional precision-over-recall choice. Revisit once the data-layer
  freshness check (below) exists, then you can safely lower the floor again.
- **Name-token market excludes are blunt.** `*market*` would also drop a legitimate
  `Market Street Grill`-type name. None existed in the test set, but it's a
  nationwide risk — the durable fix is the `is_retail_food_market` flag below, after
  which these name tokens can be removed.
- **Address dedup can hide a real co-located restaurant.** ON is right for this area,
  but in food-hall / food-court settings it keeps only the highest-confidence tenant.
  The durable fix is dedup by **(address + name)**, not address alone.

---

## 4. Issues v3 does NOT fix (these are why the dev section exists)

Even at 104 results, these slip through because **the filter only reads Overture
fields, and Overture is wrong or stale**:

| Problem | Example still in results | Root cause |
|---|---|---|
| **Permanently closed, tagged `open`** | **Norris's Ribs** (demolished 2017 — confirmed [TCPalm](https://www.floridatoday.com/story/opinion/columnists/anthony-westbury/2017/12/19/out-old-ribs-joint-new-u-s-1-port-st-lucie-anthony-westbury/960696001/)); conf 0.77 so it clears the gate | `operating_status` is stale; no freshness check |
| **National fast-food chains** | **Pizza Hut** (`brand_wikidata Q191615`), **Jack in the Box** | Tagged `pizza_restaurant` / `burger_restaurant`, not `fast_food_restaurant` |
| **Gas-station / counter brands** | **Krispy Krunchy Chicken** (no address) | Tagged `chicken_restaurant` |
| **Same brand, multiple addresses** | `Goodfella's Pizza` ×3, `A Touch of Brooklyn` ×2, `Sonny's BBQ` ×2, `Dale's BBQ South` ×2 | Address dedup can't merge across distinct addresses / spelling variants |
| **Clubs / venues serving food** | `American Legion of Ft. Pierce` (alt `bar`) | Tagged `basic_category = restaurant` |

---

## Dev team: what to improve next

The admin filter is now good enough to ship. The remaining wins are **data-layer**,
not filter-tuning — the same enrichment pattern we used for the Hospital filter. In
priority order:

### P1 — Operating-status freshness (fixes "closed but listed")
- **Problem:** Overture `operating_status` is stale; permanently-closed places (e.g.
  Norris's Ribs, closed 8 years) still read `open`. No boolean filter can catch this.
- **Build:** add `status_verified_at` (timestamp) and `status_source` (text) columns.
  A scheduled job (cron/Celery) re-confirms `operating_status` against a fresher
  source — **Google Places Details** (`business_status`) or OSM — for POIs shown to
  users. Drop / hide anything not confirmed open within *N* months (suggest 12).
- **Filter hook:** add an `Operating status verified within` control, or simply have
  the widget query exclude `status_verified_at < now() - interval`.

### P2 — Retail-food-market flag (fixes markets mislabeled as restaurants)
- **Problem:** retail seafood/meat/grocery markets are tagged `*_restaurant`
  (Pelican Seafood = retail market; McManus Seafood; La Michoacana). Today we catch
  them with blunt `*market*` name tokens, which risks dropping real "Market Grill"
  names nationwide.
- **Build:** add `is_retail_food_market` (bool), populated by enrichment using
  category + name signals (`market`, `grocery`, `butcher`, `fishmonger`, `tienda`,
  `meat market`, `seafood market`) **and** a secondary source (Google `types`
  contains `grocery_or_supermarket` / `food` without `restaurant`).
- **Payoff:** exclude `is_retail_food_market = true` from Restaurants, then **remove
  the `*market*` name tokens** from the admin filter. Also feeds the future Grocery
  filter.

### P3 — Chain / fast-food normalization (fixes Pizza Hut, Jack in the Box, etc.)
- **Problem:** national QSR chains are tagged as cuisine restaurants
  (`pizza_restaurant`, `burger_restaurant`), so category excludes miss them.
- **Build:** maintain a **brand-based** QSR exclude keyed on `brand_wikidata` /
  `brand_name_primary` (Pizza Hut `Q191615`, Jack in the Box, KFC, Domino's, etc.) —
  a small national reference list, not per-city. Add `is_chain_fast_food` (bool).
- **Filter hook:** exclude `is_chain_fast_food = true` (the widget audience wants
  local sit-down places, not chains). Keep it a flag so it's easy to toggle per
  category/product.

### P4 — Smarter dedup (fixes same-brand duplicates & co-located distinct places)
- **Problem:** address-only dedup both (a) misses same-brand duplicates at *different*
  addresses / spelling variants, and (b) can hide a legitimately co-located second
  restaurant (food halls).
- **Build:** dedup on a composite key — normalized `(name + address)` plus a small
  geospatial tolerance (e.g. within ~25 m) — instead of address alone. Prefer the
  highest-confidence, most-complete record; keep distinct names at the same address.

### P5 — Confidence is not freshness (process note)
- Document for the team that Overture `confidence` measures *tagging certainty*, not
  whether a place is open or correctly categorized. Once P1–P3 exist, **lower
  `min_confidence` back toward ~0.3** to recover the real low-confidence restaurants
  the 0.7 gate currently hides.

### Suggested column summary

| Column | Type | Populated by | Used to |
|---|---|---|---|
| `status_verified_at` | timestamp | P1 cron (Google/OSM) | drop stale/closed |
| `status_source` | text | P1 cron | auditing |
| `is_retail_food_market` | bool | P2 enrichment | exclude markets / feed Grocery |
| `is_chain_fast_food` | bool | P3 brand list | exclude national QSR |

Once P1–P3 ship, the admin filter can be simplified back to:
`basic_category_include and category_primary_exclude and category_alternate_exclude`
plus the three new boolean excludes — and the name-token hacks and the high
confidence floor can be retired.

---

## Appendix A — config history

- **v1:** broad category includes (`restaurant`, `casual_eatery`, `fine_dining` in
  primary **and** alternate). Leaked ~12 non-restaurants (grocery/convenience stores,
  an RV park, a freight terminal, a social-service org, a cake shop, restaurant-supply
  wholesale) because many non-restaurants list `*_restaurant` as an *alternate*.
- **v2 / v2.1:** gated on `basic_category = restaurant`, cleared the primary/alternate
  includes, trimmed cuisine tokens out of the excludes. Dedup OFF, confidence 0.0.
  Result ~158 with retail markets and stale/closed places still present.
- **v3 (current):** confidence `0.7`, dedup **ON**, added market/grocery/tienda name
  excludes. Result **104**, shippable; residual issues are data-layer (see Dev team).
