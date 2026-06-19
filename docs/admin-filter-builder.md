# Admin Filter Builder — Reference

The filters that power the Dream Neighborhood widget are built and saved in the
**Django admin** under the `poi_data` app, on the **PoiDetail** change-list page
(`/admin/poi_data/poidetail/`). This document captures how that filter builder is
laid out so filter logic can be designed and reasoned about outside the admin.

> The admin lives in the main Django project (not this repo). This repo is the
> working space for designing, documenting, and testing the filters that get
> entered there.

## Relevant `poi_data` models

- **PoiCategory** — `/admin/poi_data/poicategory/`
- **PoiDetail** — `/admin/poi_data/poidetail/` (the place records; this is where
  filters are applied and tested)
- **PoiFilter** — `/admin/poi_data/poifilter/` (saved filters)

## Saved filters (as observed)

Saved filters appear in a "Saved filter" dropdown and can be applied, saved, or
updated:

`cafe-filter`, `food-filter`, `Grocery`, `Grocery test`, `Hospital`,
`Restaurants`, `sp_or_filter`, `test`, `test-2`

## Top filter controls

These map to query-string params on the change-list (name in parentheses):

| Field | Param | Notes |
|---|---|---|
| Saved filter | `saved_filter_id` | Select a previously saved filter |
| Latitude, Longitude | `latlog` | Test/search center point, e.g. `27.4945, -80.3382` |
| Distance (miles) | `distance_miles` | Radius around `latlog`. Presets: **Urban 1 mi**, **Suburban 3 mi**, **Rural 10 mi** |
| Max results | `max_results` | e.g. `250` |
| Min confidence | `min_confidence` | `0`–`1`, Overture confidence threshold |
| Address | `address_line` | |
| City | `city` | |
| State | `state` | |
| Zipcode | `zipcode` | |
| Website | `has_website` | `Any` / `yes` (has website) / `no` (no website) |
| Operating status | `operating_status` | e.g. `open` |
| Deduplicate addresses | `show_duplicates` (checkbox) | **ON = keep highest-confidence record per address** |

Action buttons: **Apply filters**, **Clear**, **Save** (prompts for a name),
**Update** (overwrites the selected saved filter).

## Include / Exclude fields

There are seven fields, each with an **include** and an **exclude** text box.
Values are entered one-per-line (also accepts comma/semicolon separation).

> **Matching behavior (important): values match by "contains" (substring), not
> exact equality.** Evidence: `category_primary (include) = restaurant` returns
> records whose `category_primary` is `mexican_restaurant`, `chinese_restaurant`,
> etc. This is powerful but has sharp edges:
>
> - `restaurant` (include) also matches `restaurant_wholesale` (a wholesaler).
> - `bar` (exclude) also matches `barbecue_restaurant` — so a bare `bar` token can
>   wrongly drop BBQ places. Prefer specific tokens, or rely on a `basic_category`
>   gate to remove whole venue types.
> - `category_alternate` is a *list* of secondary categories; if `restaurant` (or
>   any `*_restaurant`) appears in that list, an include on `restaurant` will pull
>   the record in even if it's really a store/service.

### Match operators (per term)

Default is **contains**. You can also anchor with `"`/`*`:

| You type | Means | Example match |
|---|---|---|
| `publix` | contains (substring) | `super publix store` |
| `"publix"` | exact match | only `publix` |
| `publix*` | starts with | `publix pharmacy` |
| `*publix` | ends with | `the publix` |
| `*publix*` | contains anywhere | `mypublix1` |

Use **exact** (`"…"`) or anchored forms when a bare token would hit the wrong
substring (e.g. `bar` also matches `barbecue_restaurant`). Note: for **list**
fields like `category_alternate`, prefer plain contains — exact `"…"` can fail to
match a single item inside a comma-separated list.

> ⚠️ **VERIFIED SAVE BEHAVIOR (2026-06-19): a leading `*` is stripped when a
> filter is saved.** Tested by round-tripping saved `PoiFilter` records:
>
> | You enter | Stored as | Effective meaning |
> |---|---|---|
> | `*catering*` | `catering*` | **starts-with** (NOT contains!) |
> | `*bar` | `bar` | **contains** (NOT ends-with!) |
> | `catering` | `catering` | contains ✓ |
> | `catering*` | `catering*` | starts-with ✓ |
> | `"pub"` | `"pub"` | exact ✓ |
>
> **Practical rule for saved filters:** only **plain** (contains), **`x*`**
> (starts-with), and **`"x"`** (exact) survive. **Ends-with (`*x`) and
> leading-`*` contains (`*x*`) are NOT expressible** — they silently degrade.
> Use plain tokens for "contains", and clean any substring over-reach with
> excludes (e.g. nightlife uses `"pub"` exact + excludes `restaurant`/`barber`/
> `bartender` because plain `pub`/`bar` would pull `public_*`/`barber`/etc.).

| Field | Include param | Exclude param |
|---|---|---|
| Business name primary | `name_primary_include_values` | `name_primary_exclude_values` |
| Business name common | `name_common_include_values` | `name_common_exclude_values` |
| Basic category | `basic_category_include_values` | `basic_category_exclude_values` |
| Category primary | `category_primary_include_values` | `category_primary_exclude_values` |
| Category alternate | `category_alternate_include_values` | `category_alternate_exclude_values` |
| Taxonomy primary | `taxonomy_primary_include_values` | `taxonomy_primary_exclude_values` |
| Taxonomy alternates | `taxonomy_alternates_include_values` | `taxonomy_alternates_exclude_values` |

## Query builder

A free-text **Query builder** box (`query_builder`) combines the active
include/exclude groups with boolean logic. A **Generate Query** button auto-builds
an expression from whichever include/exclude boxes have values.

### Query tokens

Each field contributes two tokens (suffix `_include` / `_exclude`). These tokens
must match `QUERY_BUILDER_FIELD_MAP` in the backend `filters.py`:

```
name_primary_include        name_primary_exclude
name_common_include         name_common_exclude
basic_category_include      basic_category_exclude
category_primary_include    category_primary_exclude
category_alternate_include  category_alternate_exclude
taxonomy_primary_include    taxonomy_primary_exclude
taxonomy_alternates_include taxonomy_alternates_exclude
```

Tokens are combined with `and` / `or` and parentheses. Example (the Restaurants
filter):

```
(basic_category_include or category_primary_include or category_alternate_include)
  and category_primary_exclude
  and category_alternate_exclude
  and name_primary_exclude
```

Interpretation: a place qualifies if it matches **any** of the include category
groups, **and** is not in any of the primary/alternate category exclude lists,
**and** its primary name isn't in the name-exclude list.

## PoiDetail data model (result columns)

Columns shown in the change-list / fields available on a `PoiDetail` record:

`business_name`, `business_address`, `distance_mi` (computed from `latlog`),
`city`, `state`, `basic_category`, `category_primary`, `category_alternate`,
`taxonomy_primary`, `taxonomy_hierarchy`, `taxonomy_alternates`, `confidence`,
`operating_status`, `name_common`, `brand_name_primary`, `brand_name_common`,
`brand_wikidata`, `websites`, `latitude`, `longitude`, `country`, `zipcode_full`,
`zipcode`, `id` (UUID), `geom` (`SRID=4326;POINT(lon lat)`), `emails`, `socials`,
`phone_num`, `phone_num_text`, `zipcode_extn`.

### Overture category fields, briefly

- **basic_category** — coarse bucket (e.g. `restaurant`, `convenience_store`,
  `food_and_beverage_store`).
- **category_primary** — the main Overture category (e.g. `mexican_restaurant`,
  `sushi_restaurant`, `grocery_store`).
- **category_alternate** — comma-separated secondary categories.
- **taxonomy_primary** / **taxonomy_hierarchy** / **taxonomy_alternates** — the
  hierarchical Overture taxonomy path, e.g.
  `food_and_drink,restaurant,asian_restaurant,east_asian_restaurant,chinese_restaurant`.
- **confidence** — Overture confidence score `0`–`1`.
