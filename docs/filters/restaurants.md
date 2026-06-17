# Filter: Restaurants

> **Status: Improved (v2).** v2 below is the recommended config. It fixes the main
> problem with v1: non-restaurant businesses (grocery/convenience stores, an RV
> park, a freight terminal, a social-service org, a cake shop, restaurant-supply
> wholesale, etc.) were appearing in the results.

**Goal:** surface real sit-down / casual *restaurants* for the mom-centric widget,
while excluding fast food, drinking-focused venues (bars, breweries), cafes,
bakeries, food trucks, stores, and services.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for what each field
and the query tokens mean — including the important note that matching is
**"contains" (substring), not exact**.

---

## Root cause of the leak (why non-restaurants showed up)

Two things combined to let non-restaurants in:

1. **Matching is substring-based.** `category_primary (include) = restaurant`
   matches `mexican_restaurant`, `chinese_restaurant`, … (good) — but it also
   matches `restaurant_wholesale` (a wholesaler — bad).
2. **`restaurant` was in `category_alternate (include)`.** Overture stores a list
   of *alternate* categories per place. Lots of non-restaurants list `restaurant`
   (or `*_restaurant`) as an alternate: grocery stores, convenience stores, an RV
   park, a freight terminal, a fishing club, a social-service org, a cake shop.
   Because the query OR'd the alternate include in, any of those qualified.

### The 12 non-restaurants v1 returned (and why)

| Business | basic_category | category_primary | leaked via |
|---|---|---|---|
| Haris market | food_and_beverage_store | grocery_store | alt `restaurant` |
| Indian River Terminal | b2b_transportation_and_storage_service | freight_and_cargo_service | alt `indian_restaurant` |
| 12A Buoy | sport_or_recreation_club | fishing_club | alt `restaurant` |
| Express Food Mart | convenience_store | convenience_store | alt `restaurant` |
| A1 Super Market | convenience_store | convenience_store | alt `restaurant` |
| Citgo Food Mart | convenience_store | convenience_store | alt `restaurant` |
| Esthers House | social_or_community_service | social_service_organizations | alt `filipino_restaurant` |
| 5 Brothers Ice Cream | casual_eatery | ice_cream_shop | alt `restaurant` |
| The Cake Lady Custom Cakes | food_and_beverage_store | custom_cakes_shop | alt `restaurant` |
| St.Lucie Restaurant Supplies | wholesaler | restaurant_wholesale | primary contains `restaurant` |
| Bunnell RV Park | rv_park | rv_park | alt `restaurant` |
| The Medical Training Center | convenience_store | convenience_store | alt `health_food_restaurant` |

**The fix:** in this dataset every one of the ~53 genuine restaurants has
`basic_category = restaurant`, and **all 12** junk rows have a *different*
`basic_category`. So gate inclusion on `basic_category` and stop letting the
primary/alternate `restaurant` substring qualify a record.

---

## Recommended filter (v2) — copy/paste into the admin

### Top controls

| Setting | Value |
|---|---|
| Distance | `5.0` miles |
| Max results | `250` |
| Min confidence | `0.0` (leave low — see notes; real restaurants here go as low as 0.08) |
| Operating status | `open` |
| Deduplicate addresses | **ON** (several real dupes share an address, e.g. `211 Avenue A`, `224 Orange Ave`) |

### Include

**Basic category (include):**

```
restaurant
```

**Leave `category_primary (include)` and `category_alternate (include)` EMPTY.**
(This is the core change — those were the leak. The basic-category gate does the
inclusion now.)

### Exclude

Keep your mom-centric exclusions. With the basic-category gate, pure bars / cafes /
bakeries are already gone (their `basic_category` isn't `restaurant`), so these
excludes are now mostly a safety net for any sub-type still tagged
`basic_category = restaurant`.

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

> Note: the bare `bar` token was **removed** from v1's primary-exclude list. Because
> matching is substring-based, `bar` also matches `barbecue_restaurant`, which would
> wrongly drop BBQ places. Pure bars are already excluded by the basic-category gate.

**Category alternate (exclude):**

```
fast_food_restaurant
food_truck
coffee_shop
cafe
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

> `bar` likewise removed here for the same `barbecue` substring reason.

### Query builder

```
basic_category_include and category_primary_exclude and category_alternate_exclude and name_primary_exclude
```

Plain-English: **must** be a `basic_category = restaurant`, **and** not match any
primary-category exclude, **and** not match any alternate-category exclude, **and**
its primary name isn't in the name-exclude list.

### Expected effect

- Removes **all 12** non-restaurants listed above.
- Keeps the ~53 genuine restaurants (Airport Tiki, China Wok, Casa Pasta, The Fort
  Steakhouse, Denny's, Thai Pepper, Puerto Vallarta, etc.).

---

## Optional polish (after v2 looks good)

These are data-quality oddities that are *tagged* `basic_category = restaurant` but
may not be what a mom wants. They can't be removed by category (the data calls them
restaurants), so only use careful, narrow name excludes — and watch for collateral
damage:

- `Kari Berry Bakery & Bagel Cafe` — tagged `restaurant` (bakery/cafe by name).
- `5 Brothers Ice Cream` — already removed by v2 (basic = casual_eatery).
- `La Michoacana` — tagged `restaurant`, but the website suggests a meat market.
- `Quixotic Develop` / `Brown store` — odd names, low/medium confidence.

⚠️ Do **not** add broad name excludes like `market` — it would wrongly drop
`Country Market Restaurant And Buffett`, a real restaurant. If you want to try name
excludes, keep them specific (e.g. `creamery`, `ice cream`) and re-test.

### Cuisine policy is separate from the non-restaurant problem

Your exclude lists drop some cuisines (e.g. `latin_american_restaurant`,
`caribbean_restaurant`) but, because of substring matching, they only catch places
whose category *contains that exact token*. Mexican (`mexican_restaurant`),
Peruvian (`peruvian_restaurant`), and name-only "Caribbean" places (primary =
generic `restaurant`) still pass. That's a *selection-policy* decision, not the
non-restaurant bug — adjust those lists if you want a stricter cuisine policy.

### Confidence floor

`min_confidence` is `0.0`. Raising it removes noise but also drops genuine
restaurants — in this sample real restaurants include `Festival Italiano` (0.08),
`ZENSHI` (0.27), `Kame` (0.30), `Boston House` (0.30). Recommend leaving it low and
relying on the category gate rather than confidence.

---

## Appendix: previous filter (v1, for history)

v1 inclusion used broad category includes, which caused the leak:

- `category_primary (include)`: `restaurant`, `casual_eatery`, `fine_dining`
- `category_alternate (include)`: `restaurant`, `casual_eatery`, `fine_dining`  ← main leak
- `basic_category (include)`: *(empty)*
- Query:
  `(basic_category_include or category_primary_include or category_alternate_include) and category_primary_exclude and category_alternate_exclude and name_primary_exclude`

Note: `casual_eatery` / `fine_dining` as *category_primary/alternate* include values
were largely no-ops — observed records use values like `american_restaurant`,
`italian_restaurant`, etc. `casual_eatery` / `fine_dining` are actually
**basic_category** values, not primary/alternate ones.
