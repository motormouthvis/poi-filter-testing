# Filter: Cafes

> **Status: SHIPPABLE (v2) — validated across 4 US metros, no name hacks.**
> Tested at Fort Pierce FL (22), Warren OH (35), San Jose CA (250+), Ely NV / Park
> City UT (5). The filter is a pure **category gate with no excludes** — that is the
> correct production design for a nationwide product.

**Goal:** surface real **coffee & tea shops** a mom would sit at (meet a friend, sit
with kids) — coffee shops, cafes, tea rooms, roasteries. Chains (Starbucks, Dunkin',
Peet's, Blue Bottle, Panera, Paris Baguette) are **kept in** — a sit-down chain is
exactly what many users want.

This is a **generic USA solution — no hardcoded business names, ever.**

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings.

---

## 1. The production filter — copy/paste into the admin

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Cafe` |
| Distance | `10.0` miles (`1`–`3` urban, `10` rural) |
| Max results | `250` |
| Min confidence | *(empty)* |
| Operating status | `open` |
| Deduplicate addresses | **ON** (collapse same-address dupes like the Starbucks/Daily Grind double-rows) |

### Include

**Basic category (include):**

```
coffee_shop
tea_room
```

**Category primary (include):**

```
coffee_shop
tea_room
coffee_roastery
```

(`coffee_roastery` matters: in Ely NV, **Headframe Coffee** has
`category_primary = coffee_roastery`. Without it you drop real roaster-cafes.)

### Exclude

**Leave every exclude box empty.** See section 3 for why.

### Query builder

```
basic_category_include or category_primary_include
```

`or` is required — some rows only populate `category_primary` (e.g. tea rooms whose
`basic_category` is `non_alcoholic_beverage_venue`), so an `and` would drop them.

---

## 2. Why name excludes are banned

This is a USA-wide product. A name token that looks safe in one town silently deletes
real cafes in another. Proof from the actual samples:

| Tempting name token | Who it was meant to drop | Who it ALSO kills (real cafes) |
|---|---|---|
| `*market*` | "Streetside Market" (FL) | **Corner Market Kitchen** (SJ), any "Market St Coffee" nationwide |
| `Sunoco` / `Citgo` / `APlus` | gas-station coffee (FL) | nothing locally, but it's an infinite, unwinnable list of gas brands |
| `nutrition` | "Powerful Nutrition" club (SJ) | any "Nutrition Cafe" |

There is no finite name list for a 50-state dataset. Names are out.

---

## 3. Why category excludes are ALSO out (the key finding)

The obvious next move is excluding `category_alternate` junk like `bubble_tea` or
`smoothie_juice_bar`. **Your San Jose data proves this backfires** — those alternates
ride on legitimate, popular coffee shops:

| Alternate you'd exclude | Junk it removes | Real cafés it would WRONGLY delete |
|---|---|---|
| `bubble_tea` | boba counters | **Nirvana Soul Coffee** (0.99), **Dr.ink** (0.98), **Cafe Boba**, **Chun Yang Tea** |
| `smoothie_juice_bar` | Protein Harbor, Powerful Nutrition | **Voyager Craft Coffee HQ**, **Cowboy Coffee**, **Jack Cafe** |
| `donuts` / `fast_food_restaurant` | — | **every Dunkin'** (all carry these) |
| `restaurant` | — | Starbucks, Peet's, Cool Beans, half the list |

Every category-based exclude removes more signal than noise. So we don't use them.

---

## 4. The one real, name-free knob you can choose

The only defensible lever is **whether to include `tea_room` at all**:

- **Option A — Coffee + Tea (current):** keep `tea_room`. You also pull in bubble-tea /
  boba counters, because Overture tags boba shops as `tea_room` with no sub-distinction.
- **Option B — Coffee-only:** drop `tea_room` from both include boxes. Removes ~all boba
  counters wholesale (clean, nationwide), but also drops genuine tea rooms (Exhale Tea
  in OH, Olas African Coffee & Tea) and a few roasteries tagged tea.

This is a product call, not a data-quality fix. Pick one. Default is **A** (broad).

---

## 5. Residual noise this filter can't fix (needs data enrichment)

These leak in every metro and **cannot** be removed by any category/name boolean —
they need enrichment flags, exactly like the Restaurants P-series:

| Problem | Examples in your samples | Needed flag |
|---|---|---|
| In-store coffee counters | WFM Coffee Bar (Whole Foods), Nordstrom Ebar, Nespresso @ Macy's, Teavana (SJ) | `is_in_store_concession` |
| Gas-station coffee | APlus at Sunoco (FL) | `is_fuel_station` |
| Drive-through-only | 7 Brew (FL) | `is_drive_through_only` |
| Nutrition/herbalife clubs | Powerful Nutrition, Protein Harbor | `is_nutrition_club` |
| Same brand, many addresses | Starbucks dupes, Daily Grind ×2 | dedup by (name+address) — P4 |

See the [Dev team section in restaurants.md](restaurants.md#dev-team-what-to-improve-next).
Until those flags exist, the category gate above is the correct, honest ceiling.

---

## Appendix A — config history

- **v0 (broken):** `basic_category = cafe` + heavy excludes + conf `0.7`. **0 results** —
  wrong `basic_category` (data uses `coffee_shop`).
- **v1 (discovery):** broad primary includes, no gate.
- **v2 (name-exclude attempt — rejected):** added `*market*` / gas-brand name tokens and
  `smoothie_juice_bar` / `donuts` category excludes. Rejected: name tokens aren't
  USA-safe, and category excludes delete real cafes (Nirvana Soul, every Dunkin').
- **v2 (current, shippable):** `coffee_shop` + `tea_room` + `coffee_roastery` includes,
  query `basic_category_include or category_primary_include`, **no excludes**, dedup ON.
  Validated across FL/OH/CA/NV-UT. Residual cleanup deferred to enrichment flags.
