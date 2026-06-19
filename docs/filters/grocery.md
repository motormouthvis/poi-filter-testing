# Filter: Grocery / Supermarkets

> **Status: v1 (draft) — evidence-based proposal from the raw category pull.**
> Built from `data/grocery_raw/` (23,664 unique POIs, 51 states + DC, 142 pins).
> Generic USA — no one-off local business names.

**Goal:** surface real **places people buy weekly groceries** — full-line
supermarkets, neighborhood grocery stores, warehouse clubs (Costco, BJ's, Sam's),
and legitimate **independent / ethnic markets** (international, Asian, Mexican,
Indian, Korean grocers). Major chains (Publix, Kroger, ALDI, Walmart Supercenter,
H-E-B, Wegmans, Whole Foods, Trader Joe's, Wegmans) are **kept in**. Convenience
stores, gas marts, dollar stores, pharmacies, liquor/beer-wine, tobacco/vape
shops, vitamin shops, standalone bakeries/butchers/fishmongers, and
wholesale/distribution depots & online-only pickup points are **excluded**.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings.

---

## 0. Admin panel parameters (paste-ready, v1)

Enter these in the PoiDetail filter builder. Compound quality gate is **deferred**
(needs dev) — see note at the bottom.

| Control | Value |
|---|---|
| Saved filter (Save as) | `Grocery` |
| Latitude, Longitude | *(your test point)* |
| Distance (miles) | `10` (use `1`–`3` in dense urban cores) |
| Max results | `250` |
| Min confidence | *(leave blank)* — `0.77` is a sentinel default; a floor deletes real chains |
| Website | `Any` |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

**Category primary — include:**

```
supermarket
grocery_store
specialty_grocery_store
wholesale_grocer
```

> These four tokens (substring match) absorb every real grocery sub-type:
> `grocery_store` → `international_grocery_store`, `asian_grocery_store`,
> `mexican_grocery_store`, `indian_grocery_store`, `korean_grocery_store`,
> `organic_grocery_store`; `wholesale_grocer` → Costco / BJ's / Sam's.
> Optionally add `health_food_store` if you want more natural-foods markets (see §3).

**Category primary — exclude:**

```
convenience_store
gas_station
dollar_store
discount_store
pharmacy
drugstore
liquor_store
beer_wine_and_spirits
tobacco_shop
e_cigarette_store
vitamins_and_supplements
bakery
caterer
fast_food_restaurant
bank
```

> **Do NOT** add a bare `wholesale` / `warehouse` token here — it would
> substring-match `wholesale_grocer` and delete **Costco, BJ's, Sam's Club**.
> Distribution depots are removed by name instead (below).

**Business name primary — exclude:**

```
*Distribution Center*
*Grocery Pickup*
*Pickup & Delivery*
*Pickup and Delivery*
```

**Query builder:**

```
category_primary_include and category_primary_exclude and name_primary_exclude
```

All other include/exclude boxes: **empty**.

> **Whitelist note:** the brand name whitelist (Publix*, ALDI*, Kroger*, …) is
> **intentionally NOT used** as a hard `and name_primary_include` gate — see §5.
> Keep it only as an optional *ranking booster*, never a filter requirement, or
> you delete ~78% of real independent groceries.

> **Deferred (requires dev):** the precise quality gate `confidence < 0.5 AND no
> website` (~1,297 rows, 5%) cannot be expressed in the current admin builder,
> which only offers a single `min_confidence` and a separate `has_website`. Do
> **not** set `min_confidence` as a substitute — it would delete the 4,191
> sentinel-`0.77` rows (real chains included). Leave the gate out until a
> compound rule is supported.

---

## 1. Dataset summary (raw pull)

`python scripts/analyze_grocery.py` on `data/grocery_raw/grocery_master.csv`:

| Metric | Value |
|---|---|
| Total unique POIs | **23,664** |
| States covered | **51** (50 + DC; plus a few blank / `Ca`-typo rows) |
| Has website | 17,858 (75%) |
| No website | 5,806 (24%) |

**Top states:** TX 1,851 · CA 1,749 · FL 1,192 · TN 785 · CO 772 · NC 766 ·
OH 716 · GA 712 · MI 705 · NY 671.

**`basic_category` breakdown (only 2 distinct values):**

| basic_category | count |
|---|---|
| `food_and_beverage_store` | 23,547 |
| `wholesaler` | 117 |

> The raw pull's breadth comes almost entirely from `food_and_beverage_store`,
> which is a **catch-all retail-food bucket** — it includes liquor, tobacco,
> vitamins, bakeries, butchers, etc. as well as actual groceries. This is the
> root cause of nearly all the noise (see §3).

**`category_primary` breakdown (top of ~30 distinct values):**

| category_primary | count | grocery? |
|---|---|---|
| `grocery_store` | 6,857 | ✅ keep |
| `liquor_store` | 4,319 | ❌ noise |
| `tobacco_shop` | 2,584 | ❌ noise |
| `supermarket` | 2,468 | ✅ keep |
| `vitamins_and_supplements` | 1,437 | ❌ noise |
| `health_food_store` | 979 | ⚠️ borderline |
| `butcher_shop` | 962 | ⚠️ specialty |
| `specialty_grocery_store` | 883 | ✅ keep |
| `food` | 729 | ❌ vague/distribution |
| `fruits_and_vegetables` | 450 | ⚠️ produce stand |
| `beer_wine_and_spirits` | 290 | ❌ noise |
| `pizza_delivery_service` | 285 | ❌ noise |
| `fishmonger` | 240 | ⚠️ specialty |
| `international_grocery_store` | 159 | ✅ keep |
| `organic_grocery_store` | 146 | ✅ keep |
| `wholesale_grocer` | 117 | ✅ keep (Costco/BJ's/Sam's) |
| `cheese_shop` / `seafood_market` / `herbal_shop` / `herb_and_spice_shop` … | <130 each | ⚠️ specialty |

**Confidence distribution:**

| Bucket | count | % |
|---|---|---|
| `<0.5` | 3,010 | 12% |
| `0.5–0.7` | 1,817 | 7% |
| `0.7–0.9` | 6,766 | 28% |
| `>=0.9` | 12,071 | 51% |

> **`0.77` is a sentinel default, not a real score.** 4,191 rows (17% of the
> dataset) have `confidence` **exactly `0.77`** — including real chains. Any
> confidence gate must treat `0.77` as "unknown", not "low quality".

---

## 2. Include tokens used (raw pull)

These are the tokens entered in `scripts/scrape_grocery.py` (`CATEGORY_PARAMS`).
Matching is **contains/substring**, so a short token absorbs the longer Overture
values (e.g. `grocery_store` → `international_grocery_store`, `asian_grocery_store`).

**Basic category (include):**

```
food_and_beverage_store
```

**Category primary (include):**

```
supermarket
grocery_store
specialty_grocery_store
wholesale_grocer
```

**Query builder:**

```
(basic_category_include or category_primary_include)
```

`min_confidence = 0`, `operating_status = open`, `max_results = 200`, all exclude
boxes empty, **no brand whitelist**. This is deliberately broad so we can *see*
the noise the `food_and_beverage_store` bucket carries and design the production
excludes from evidence.

---

## 3. Observed noise / edge cases (evidence from the data)

The `category_primary` grocery values (`supermarket`, `grocery_store`,
`specialty_grocery_store`, `wholesale_grocer` + `*_grocery_store` variants) are
**clean** — they total **10,708 rows** and are almost all real groceries. Nearly
all noise enters through the **`basic_category = food_and_beverage_store` OR
branch**, which drags in ~13,000 non-grocery food retailers.

| Noise type | Count | category_primary signal | Real examples |
|---|---|---|---|
| **Liquor / beer-wine** | 4,319 + 290 | `liquor_store`, `beer_wine_and_spirits` | `Down South Liquor Store`, `Fort Pierce Discount Liquor` |
| **Tobacco / vape** | 2,584 | `tobacco_shop`, `e_cigarette_store` | `Brass Pipe Cigar & Tobacco`, `Lucky 7 Cigarettes` |
| **Vitamin / supplement shops** | 1,437 | `vitamins_and_supplements` | `Downtown Sports Nutrition` |
| **Standalone bakeries / cake shops** | ~110 | `bakery`, `patisserie_cake_shop`, `custom_cakes_shop` | various |
| **Pizza / prepared food delivery** | 285 | `pizza_delivery_service` | various |
| **Vague "food" / food distribution** | 729 | `food` + alt `food_beverage_service_distribution` | `Espinoza Brothers Food Distribution`, `Egan Packing` |
| **Specialty single-line food** (butcher, fishmonger, cheese, produce, herb) | ~1,900 | `butcher_shop`, `fishmonger`, `cheese_shop`, `fruits_and_vegetables`, `herbal_shop` | `Best Choice Meats`, `Day Boat Seafood` |

### Noise that survives **inside** the grocery `category_primary` set

These are mislabeled records — they carry a real grocery `category_primary` but
are not weekly-grocery destinations. They cannot be removed by category and need
**name excludes** (or the deferred quality gate):

| Noise | Count in grocery set | Why it's there | Fix |
|---|---|---|---|
| **Online pickup / delivery depots** | **258** (`Walmart Grocery Pickup` ×139, `… Pickup and Delivery` ×104, `… Pickup & Delivery` ×15) | tagged `grocery_store` but are order-fulfillment points, not stores | name exclude `*Grocery Pickup*`, `*Pickup and Delivery*`, `*Pickup & Delivery*` |
| **Distribution centers** | 2+ (`Whole Foods … Distribution Center`) | tagged `grocery_store`/`health_food_store` | name exclude `*Distribution Center*` |
| **Mislabeled non-stores** (e.g. an arcade tagged `grocery_store`) | rare | bad Overture label | residual; caught by compound quality gate |

### Borderline — keep or drop?

- **`wholesale_grocer` (117 — Costco, BJ's, Sam's Club):** **KEEP.** People buy
  weekly groceries there. ⚠️ This is why we must *not* exclude a `wholesale`
  category token — it would substring-match `wholesale_grocer` and delete them.
  Walmart *Distribution Centers* are filtered by **name**, not category.
- **`health_food_store` (979):** mixed — real natural-foods markets *and*
  GNC-style supplement shops. Whole Foods sometimes lands here. **Optional
  include**: add it for recall, accept some supplement-shop noise; leave it out
  for precision. Recommended: leave **out** of v1 (Whole Foods is also tagged
  `supermarket`/`organic_grocery_store`, which we already keep).
- **Specialty single-line (`butcher_shop`, `fishmonger`, `cheese_shop`,
  `fruits_and_vegetables`):** not weekly-grocery destinations → **DROP** (they're
  excluded automatically by using a category_primary include instead of the broad
  basic_category include).
- **Ethnic / international grocers (`*_grocery_store`, 237 total):** **KEEP** —
  these are exactly the independents the brand whitelist would wrongly drop.

---

## 4. Proposed filter (v1)

### Design change vs the raw pull

Switch the include from the broad **`basic_category` OR** to a
**`category_primary`-only include**. This single change removes essentially all
of the liquor / tobacco / vitamin / bakery / butcher noise *for free*, because
those records' `category_primary` is not a grocery token. The category excludes
below are then a thin belt-and-suspenders layer for stragglers in `category_alternate`.

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Grocery` |
| Distance | `10.0` miles (`1`–`3` urban, `10` rural) |
| Max results | `250` |
| Min confidence | *(empty)* — `0.77` sentinel makes a numeric gate unsafe |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

### Include — Category primary (include)

```
supermarket
grocery_store
specialty_grocery_store
wholesale_grocer
```

> Add `health_food_store` only if natural-foods recall matters more than the
> supplement-shop noise it admits.

### Exclude — Category primary (exclude)

Removes the rare grocery-tagged stragglers and anything pulled via a grocery
substring in `category_alternate`. Safe because none of these tokens appear
inside a real grocery `category_primary` (and crucially, **`wholesale` is absent**
so Costco/BJ's survive):

```
convenience_store
gas_station
dollar_store
discount_store
pharmacy
drugstore
liquor_store
beer_wine_and_spirits
tobacco_shop
e_cigarette_store
vitamins_and_supplements
bakery
caterer
fast_food_restaurant
bank
```

### Exclude — Business name primary (exclude)

Online-only depots and distribution points that are mislabeled `grocery_store`
(substring/anchored match):

```
*Distribution Center*
*Grocery Pickup*
*Pickup & Delivery*
*Pickup and Delivery*
```

### Query builder

```
category_primary_include
  and category_primary_exclude
  and name_primary_exclude
```

### Quality gate (widget-side, not a numeric admin floor)

Because `0.77` is a sentinel, use a **compound** gate instead of `min_confidence`:

> **Drop a row when `confidence < 0.5` AND it has no website.**

This targets the genuinely unverifiable long tail (1,297 rows, ~5%) — ghost
listings, vanity pages, mislabeled stalls (the "arcade tagged grocery_store"
case) — while protecting the 4,191 sentinel-`0.77` records and every websited
store. A naive `confidence < 0.7` floor would instead delete ~36% of the dataset
(all the `0.77` rows), including brand-name chains, so it is explicitly rejected.

---

## 5. How this improves on the current saved `Grocery` filter

The user's current `Grocery` filter has two structural problems this v1 fixes,
plus a couple of category-coverage gaps.

### A. The brand-whitelist `AND` drops real independents (biggest issue)

The current query **requires** `name_primary_include` (the Publix/ALDI/Kroger/…
brand whitelist) AND-ed into every result:

```
… and name_primary_include and …
```

In the raw data, **78% of real grocery/supermarket POIs (8,446 of 10,708) have no
`brand_name_primary`** — they are independent and ethnic markets
(`Alaska Commercial Company`, `H Mart`, `Bravo Supermarkets`, `D L Supermarket`,
countless `… Supermarket` / `… Mercado` / `Mini Super` shops). A hard whitelist
`AND` silently deletes ~4 of every 5 genuine groceries.

> **Fix:** drop `name_primary_include` from the query entirely. Keep the brand
> list only as an optional *ranking booster* (sort whitelisted chains first), never
> as a filter gate. v1 query is include-by-category, not include-by-brand.

### B. Tobacco & vitamin shops leak through the current category excludes

The current `category_primary` exclude list (banks, fast_food, pharmacy, caterer,
liquor_store, beer_wine_and_spirits, bakery, convenience_store, discount_store,
gas_station, dollar_store, …) **does not list `tobacco_shop` or
`vitamins_and_supplements`**. In the raw pull those are **2,584 + 1,437 = 4,021
rows** sitting in the `food_and_beverage_store` bucket. Today they are only held
back by the brand-whitelist `AND` (they aren't whitelisted brands) — so the moment
you relax the whitelist to keep independents (issue A), they would flood in.

> **Fix:** add `tobacco_shop`, `e_cigarette_store`, and `vitamins_and_supplements`
> to the category excludes. (Better still, the v1 `category_primary`-only include
> never admits them in the first place.)

### C. Distribution / pickup-only noise needs **name** excludes, not category

The reported leaks — **`Walmart Grocery Pickup & Delivery`** (order-fulfillment
point) and **`Walmart Distribution Center`** (warehouse) — both carry a grocery or
warehouse `category_primary`, so no category rule removes them. The data confirms
**258 pickup/delivery depot rows and 2+ distribution centers** sitting inside the
grocery `category_primary` set.

> **Fix:** name excludes `*Grocery Pickup*`, `*Pickup and Delivery*`,
> `*Pickup & Delivery*`, `*Distribution Center*`. The mislabeled
> `Lucky 7 …` arcade/grocery case is residual category-mislabel noise — handled by
> the deferred `confidence < 0.5 AND no website` quality gate.

### D. Don't blanket-exclude "wholesale"

The current filter (and any instinct to exclude wholesale/distribution by
category) risks deleting **Costco, BJ's, and Sam's Club**, which are tagged
`wholesale_grocer` and *are* weekly-grocery destinations. v1 keeps
`wholesale_grocer` in the include and removes only Walmart-style depots **by name**.

### Side-by-side

| Concern | Current `Grocery` filter | v1 proposal |
|---|---|---|
| Independent / ethnic grocers | ❌ dropped by brand-whitelist `AND` (~78% of real groceries) | ✅ kept (include by category, not brand) |
| Tobacco / vape shops | ⚠️ leak if whitelist relaxed (not in excludes) | ✅ excluded by category |
| Vitamin / supplement shops | ⚠️ leak if whitelist relaxed (not in excludes) | ✅ excluded by category |
| `Walmart Grocery Pickup & Delivery` | ❌ passes (grocery_store) | ✅ name-excluded |
| `Walmart Distribution Center` | ❌ passes (warehouse) | ✅ name-excluded |
| Costco / BJ's / Sam's | ✅ (whitelisted) | ✅ kept via `wholesale_grocer` |
| `Lucky 7` arcade mislabel | ❌ passes | ⚠️ deferred quality gate |
| Confidence handling | risk of numeric floor deleting `0.77` chains | compound gate, deferred |

---

## 6. Why no numeric `min_confidence`

| Option | Effect | Verdict |
|---|---|---|
| `min_confidence = 0.7` | Deletes all 4,191 `0.77`-sentinel rows (real chains) + everything below (~36% of data) | ❌ reject |
| `min_confidence = 0.5` | Keeps `0.77` (>0.5) but blindly drops the `0.5–0.7` band (1,817) regardless of website | ⚠️ blunt |
| **`confidence < 0.5` AND no website** | Drops 1,297 unverifiable rows; keeps every sentinel + websited store | ✅ proposed (deferred) |

---

## Appendix A — reproduce

```bash
pip install requests
python scripts/scrape_grocery.py --pins data/coffee_tea_raw/pins.csv   # full pull
python scripts/analyze_grocery.py                                       # summary stats
```

Raw dataset + column docs: [`../../data/grocery_raw/README.md`](../../data/grocery_raw/README.md).
