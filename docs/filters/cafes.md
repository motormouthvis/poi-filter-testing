# Filter: Cafes

> **Status: v1 (discovery) — run this, then paste results back.**
> We don't have your cafe data sampled yet, so this v1 is intentionally **wide**
> (low confidence floor, dedup OFF) so we can see everything Overture returns — the
> good, the junk, and the duplicates. Once you run it and paste the admin result
> HTML, we'll tighten it to v2/v3 exactly like we did for Restaurants.

**Goal:** surface real **sit-down coffee & tea shops** a mom would be interested in
(meet a friend, sit with kids) — coffee shops, cafes, and tea rooms/houses. Exclude
grab-and-go-only / non-coffee venues: donut chains, ice-cream & dessert shops,
juice/smoothie bars, internet & hookah cafes, institutional cafeterias, and bars.

This must be a **generic USA solution** — no hardcoded business names.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings and
the match operators (`token` = contains, `"token"` = exact, `token*` = starts-with,
`*token` = ends-with, `*token*` = contains-anywhere).

---

## What I need from you (to calibrate)

Run v1 below and **paste the result HTML** (like you did for Restaurants). I'm
specifically looking at the `basic_category`, `category_primary`, and
`category_alternate` columns so I can:

1. Find the right `basic_category` value to **gate** on (for Restaurants it was
   `restaurant`; for cafes it's likely `cafe` — but I want to confirm from your data
   rather than guess).
2. See what non-cafes leak in, so we can add targeted excludes.

---

## v1 (discovery) — copy/paste into the admin

### Top controls

| Setting | Value | Why |
|---|---|---|
| Distance | `5.0` miles | match Restaurants for comparison |
| Max results | `250` | |
| Min confidence | `0.0` | **see everything first**; we raise it after calibration |
| Operating status | `open` | |
| Deduplicate addresses | **OFF** | see duplicates so we can decide dedup policy |

### Include

Leave **Basic category (include)** EMPTY for now (we'll set the gate once we confirm
the value from your data).

**Category primary (include):**

```
coffee_shop
cafe
tea_room
tea_house
```

> Notes on substring matching:
> - `cafe` (contains) will also pull `cafeteria`, `internet_cafe`, `cat_cafe` — that's
>   intentional for discovery; we exclude the unwanted ones below.
> - I avoided a bare `tea` token on purpose — it would wrongly match `s`**`tea`**`khouse`.
>   If your data uses different tea tokens (e.g. `tea_shop`, `teahouse`, `bubble_tea`),
>   tell me and I'll adjust.

**Category alternate (include):** EMPTY for v1.
(In Restaurants, including the *alternate* list was the main source of leaks. We'll
only add it later if recall is too low.)

### Exclude

**Category primary (exclude):**

```
fast_food_restaurant
donut
doughnut
ice_cream
dessert
frozen_yogurt
juice
smoothie
bubble_tea
internet_cafe
cafeteria
hookah
```

**Category alternate (exclude):**

```
fast_food_restaurant
donut
doughnut
ice_cream
dessert
frozen_yogurt
juice
smoothie
bubble_tea
internet_cafe
cafeteria
hookah
```

**Business name primary (exclude):**

```
food truck
kiosk
drive thru
drive-thru
```

Leave the other exclude boxes empty.

### Query builder

```
category_primary_include and category_primary_exclude and category_alternate_exclude and name_primary_exclude
```

Plain English: primary category must be a coffee/cafe/tea type, **and** it's not in
the primary or alternate exclude lists, **and** its name isn't truck/kiosk/drive-thru.

---

## Open questions we'll resolve from the data

- **Chains (Starbucks, Dunkin, etc.):** kept IN for v1 — a sit-down Starbucks is
  exactly what many moms want. We can add an optional chain toggle later (same
  `brand_wikidata` approach noted in the Restaurants dev plan) if you'd rather show
  only independent cafes.
- **Bakery-cafes (Panera-style):** currently NOT excluded by name, but if they're
  tagged `bakery`/`patisserie` they may not appear. We'll decide include vs. exclude
  once we see how your data tags them.
- **Confidence floor:** starts at `0.0`. After we see the results we'll likely raise
  it (Restaurants landed on `0.7`) — but only once we confirm it isn't dropping real
  cafes.
- **Dedup:** OFF for now; we'll turn it ON (or move to name+address dedup) after
  seeing how many duplicate rows show up.

---

## Next step

Apply v1, then paste the result HTML here. I'll calibrate the `basic_category` gate,
trim the leaks, set the confidence floor, and produce a v2 (and a formatted `.docx`
like the Restaurants one).
