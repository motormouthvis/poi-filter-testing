# Filter: Restaurants

> **Status: Work in progress.** This is a captured example of the saved
> `Restaurants` filter from the admin panel. It is not considered final/correct
> yet — it's a baseline to iterate on.

**Goal:** surface real sit-down / casual *restaurants* for the mom-centric widget,
while excluding fast food, drinking-focused venues (bars, breweries), cafes,
bakeries, food trucks, and narrow ethnic/quick-service categories that create
noise.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for what each field
and the query tokens mean.

## Settings (top controls)

| Setting | Value |
|---|---|
| Saved filter name | `Restaurants` |
| Test location (`latlog`) | `27.494521317824088, -80.33815750281246` (Fort Pierce, FL area) |
| Distance | `5.0` miles |
| Max results | `250` |
| Min confidence | `0.0` |
| Operating status | `open` |
| Deduplicate addresses | off (`show_duplicates` unchecked) |

## Include rules

**Category primary (include):**

```
restaurant
casual_eatery
fine_dining
```

**Category alternate (include):**

```
restaurant
casual_eatery
fine_dining
```

(Basic category include is empty.)

## Exclude rules

**Business name primary (exclude):**

```
taco truck
food truck
```

**Category primary (exclude):**

```
fast_food_restaurant
food_truck
street_vendor
coffee_shop
cafe
bakery
bar
nightclub
brewery
distillery
winery
caterer
food_court
pizza_restaurant
burger_restaurant
sandwich_shop
taco_restaurant
texmex_restaurant
diner
chicken_restaurant
chicken_wings_restaurant
seafood_restaurant
latin_american_restaurant
caribbean_restaurant
haitian_restaurant
cuban_restaurant
soul_food
wings_restaurant
```

**Category alternate (exclude):**

```
fast_food_restaurant
food_truck
coffee_shop
cafe
bar
nightclub
bakery
pizza_restaurant
burger_restaurant
sandwich_shop
taco_restaurant
texmex_restaurant
chicken_restaurant
chicken_wings_restaurant
seafood_restaurant
latin_american_restaurant
caribbean_restaurant
soul_food
```

## Query builder expression

```
(basic_category_include or category_primary_include or category_alternate_include) and category_primary_exclude and category_alternate_exclude and name_primary_exclude
```

Plain-English: include a place if it matches any of the include category groups,
**and** it is not in either category-exclude list, **and** its primary name is not
in the name-exclude list.

## Known issues / things to iterate on

These are observations from the sample result set (65 results) this filter
produced — kept here so the rationale for future tweaks is documented.

- **Include lists are very broad.** Including the generic `restaurant` category
  pulls in almost everything tagged as a restaurant, so most of the real work is
  being done by the exclude lists.
- **`fine_dining` / `casual_eatery` as include values** don't appear to match the
  observed `category_primary` values directly (records use things like
  `american_restaurant`, `italian_restaurant`); confirm these tokens exist in the
  Overture taxonomy or they're effectively no-ops.
- **Specific cuisines still leak through** because they're not generic
  `restaurant`. Examples seen in results: `chinese_restaurant`,
  `mexican_restaurant`, `sushi_restaurant`, `japanese_restaurant`,
  `korean_restaurant`, `thai_restaurant`, `vietnamese_restaurant`,
  `italian_restaurant`, `greek_restaurant`, `steakhouse`,
  `peruvian_restaurant`, `southern_restaurant`. Decide which of these are wanted;
  excluding `latin_american_restaurant`/`caribbean_restaurant` etc. only catches
  the parent token, not children like `mexican_restaurant`.
- **Non-restaurants leak in via `category_alternate`.** Several results are really
  stores/services whose *alternate* category includes `restaurant`, e.g.:
  - `Haris market` — `grocery_store` (alt: `restaurant`)
  - `Indian River Terminal` — `freight_and_cargo_service` (alt: `indian_restaurant`)
  - `12A Buoy` — `fishing_club` (alt: `restaurant`)
  - `Express Food Mart` / `A1 Super Market` / `Citgo Food Mart` — `convenience_store` (alt: `restaurant`)
  - `St.Lucie Restaurant Supplies` — `restaurant_wholesale`
  - `Esthers House` — `social_service_organizations` (alt: `filipino_restaurant`)
  - `Bunnell RV Park` — `rv_park` (alt: `restaurant`)
  - `The Medical Training Center` — `convenience_store` (alt: `health_food_restaurant`)
  - `The Cake Lady Custom Cakes` — `custom_cakes_shop`
  - `5 Brothers Ice Cream` — `ice_cream_shop`

  → Consider requiring the **primary** category (basic/primary) to be a restaurant
  rather than letting `category_alternate_include` qualify a record, or add these
  store/service categories to the exclude lists.
- **Very low-confidence records appear** (e.g. `0.07`, `0.26`) because
  `min_confidence` is `0.0`. Consider raising the floor.
- **Deduplicate addresses is off**, so multiple POIs at the same address show up
  (e.g. several restaurants at `211 Avenue A` / `224 Orange Ave`). Turn on if the
  widget should show one per address.

## Ideas to try next

- Drive inclusion off `basic_category` (= `restaurant`) and/or `taxonomy_*`
  instead of broad `category_primary`/`category_alternate` includes.
- Don't let `category_alternate_include` alone qualify a record; require a
  restaurant **primary/basic** category.
- Add the leaking store/service categories above to the exclude lists.
- Raise `min_confidence` and A/B the result quality across several test locations.
