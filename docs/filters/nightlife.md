# Filter: Nightlife (bars / clubs / lounges)

> **Status: v1 (draft from raw analysis).** Built from a category-only RAW pull of
> 22,686 POIs across 142 pins (50 states + DC). No name excludes / no confidence
> floor in the raw pull — this doc proposes the first real filter on top of it.

**Goal:** surface real **nightlife venues** — bars, pubs, cocktail/wine/sports
bars, breweries (taprooms), lounges, night clubs, karaoke. Food-forward bars that
are genuinely drinking venues (gastropub, tapas bar, hotel bar) are **kept in**;
food/dessert venues that only match on a `*bar` substring (juice bars, salad bars,
ice-cream "milk bars") are **noise to remove**.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings.

---

## 0. Admin panel parameters (paste-ready, v1)

Enter these in the PoiDetail filter builder. Compound quality gate is **deferred**
(needs dev) — see note at the bottom.

| Control | Value |
|---|---|
| Saved filter (Save as) | `Nightlife` |
| Latitude, Longitude | *(your test point)* |
| Distance (miles) | `10` (use `1`–`3` in dense urban cores) |
| Max results | `250` |
| Min confidence | *(leave blank)* — `0.77` sentinel; floor drops real bars |
| Website | `Any` |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

**Basic category — include:**

```
bar
nightlife
```

**Category primary — include:** ⚠️ ends-with anchors (`*bar`/`*pub`) do **NOT**
work — the admin strips a leading `*` on save, collapsing `*pub` → `pub`
(contains), which then matches `public_*` (gov/schools/publishers). Use `"pub"`
**exact** + explicit `gastropub`/`brewpub`; `bar` stays contains and the
over-reach is cleaned with excludes below:

```
bar
night_club
nightclub
"pub"
gastropub
brewpub
lounge
brewery
karaoke
```

**Category primary — exclude** (food/dessert `bar` noise + `bar`/`pub`
contains over-reach):

```
smoothie_juice_bar
salad_bar
milk_bar
juice_bar
sushi_bar
oyster_bar
raw_bar
snack_bar
candy_bar
restaurant
barber
bartender
```

> `restaurant` removes `bar_and_grill_restaurant` / `barbecue_restaurant` that
> bare `bar` (contains) drags in; `barber` removes barber shops; `bartender`
> removes the bartending-service category. Verified live: without these, a Denver
> test pulled 109 `public_and_government_association` rows (City Hall, DMV,
> schools) plus barber/BBQ venues.

**Query builder:**

```
(basic_category_include or category_primary_include) and category_primary_exclude
```

All other include/exclude boxes: **empty**. No name excludes needed (noise here is
a clean category signal). Optional product call: add `hookah_bar` and
`airport_lounge` to the category-primary exclude list to drop hookah/vape and
airside lounges. (`irish_pub`, `dive_bar`, `wine_bar`, etc. are still kept — they
arrive via `basic_category = bar`.)

> **Deferred (requires dev):** the precise quality gate `confidence < 0.7 AND no
> website` (~1,234 rows) needs a compound rule the admin doesn't support. Don't set
> a numeric `min_confidence` as a substitute — it would drop real bars at the
> `0.77` sentinel.

---

## 1. Dataset stats (raw pull)

`data/nightlife_raw/` — `nightlife_master.csv` / `.json`.

| Metric | Value |
|---|---|
| Total unique POIs | **22,686** |
| States covered | **50 + DC** (53 distinct `state` codes incl. 4 blank + 1 `Mo` casing dupe — see §4 data quality) |
| Pins | 142 (`data/coffee_tea_raw/pins.csv`) |
| Has website | 18,922 (83%) |
| No website | 3,764 (16%) |
| Confidence ≥0.9 | 11,736 · 0.7–0.9: 8,231 · 0.5–0.7: 1,200 · <0.5: 1,519 |

**Top states:** TX 1,846 · CA 1,581 · FL 1,322 · OH 796 · TN 796 · CO 774 ·
NC 760 · OR 721 · GA 681 · MI 681.

### Include tokens used (raw pull)

Matching in the admin builder is **"contains" (substring)**, so bare tokens
pollute heavily. We use **ends-with anchors** to keep the venue tokens while
dropping pure-substring junk.

**Basic category (include):**

```
bar
nightlife
```

**Category primary (include):**

```
*bar
night_club
nightclub
*pub
lounge
brewery
karaoke
```

**Query builder:**

```
(basic_category_include or category_primary_include)
```

**Why anchored — proven on a single test pin (Fort Pierce FL, 10 mi):** bare
tokens hit the 200-row cap with garbage; anchored tokens returned 77 clean rows.

| Bare token | Junk it pulled (test pin) | Fix |
|---|---|---|
| `bar` (contains) | `barber` ×35, `barbecue_restaurant` ×24, `bar_and_grill_restaurant` ×10 | `*bar` (ends-with) — `barber`/`barbecue`/`bar_and_grill` don't END in "bar" |
| `pub` (contains) | `public_and_government_association` ×33, `public_service_and_government` ×17, `notary_public` ×6, `public_school`, `public_adjuster`, `topic_publisher` | `*pub` (ends-with) — keeps `pub`/`irish_pub`/`gastropub` only |

`*bar` subsumes every `*_bar` subtype (`wine_bar`, `sports_bar`, `cocktail_bar`,
`dive_bar`, …) so the individual tokens in the original brief are redundant.

---

## 2. Category breakdown (full dataset)

`category_primary` distribution (all 22,686 rows):

| category_primary | count | verdict |
|---|---:|---|
| `bar` | 6,796 | keep |
| `cocktail_bar` | 2,286 | keep |
| `brewery` | 2,038 | keep (taprooms) |
| `lounge` | 2,031 | keep |
| **`smoothie_juice_bar`** | **1,798** | **NOISE — juice/smoothie shops** |
| `pub` | 1,546 | keep |
| `sports_bar` | 1,499 | keep |
| `wine_bar` | 817 | keep |
| `gastropub` | 656 | keep (drinking-forward) |
| `beer_bar` | 507 | keep |
| **`salad_bar`** | **419** | **NOISE — Olive Garden buffets** |
| `dive_bar` | 354 | keep |
| `gay_bar` | 309 | keep |
| `irish_pub` | 283 | keep |
| `tapas_bar` | 273 | keep (bar-forward) |
| `hookah_bar` | 233 | edge — hookah/vape (see §3) |
| `hotel_bar` | 211 | keep |
| `karaoke` | 211 | keep |
| `speakeasy` | 138 | keep |
| `whiskey_bar` | 80 | keep |
| `tiki_bar` | 75 | keep |
| **`milk_bar`** | **63** | **NOISE — ice cream shops** |
| `piano_bar` | 19 | keep |
| `airport_lounge` | 15 | edge — airside, not a neighborhood venue |
| `sake_bar` | 10 | edge — some are restaurants |
| `drive_thru_bar` | 6 | keep |
| `champagne_bar` | 5 | keep |
| `beach_bar` | 3 · `cigar_bar` 2 · `bar_crawl` 1 · *(blank)* 2 | keep / minor |

`basic_category`: `bar` 15,180 · `lounge` 2,046 · `brewery` 2,038 ·
`smoothie_juice_bar` 1,799 · `casual_eatery` 929 (gastropub+tapas_bar) ·
`restaurant` 419 (all `salad_bar`) · `music_venue` 211 (karaoke/clubs) ·
`non_alcoholic_beverage_venue` 63 (milk_bar) · `nightlife_venue` 1.

---

## 3. Observed NOISE & edge cases (with evidence)

### Substring pollution removed by anchoring (would otherwise be huge)

- `bar` → **`barber`** (hair salons), **`barbecue_restaurant`** (BBQ joints),
  **`bar_and_grill_restaurant`**. All dropped by `*bar`.
- `pub` → **`public_and_government_association`**, **`notary_public`**,
  **`public_school`**, **`publisher`**. All dropped by `*pub`.

### Food/beverage venues still pulled by the `*bar` anchor (10% of dataset)

These END in "bar" but are **not nightlife** — recommend category excludes:

| category_primary | n | Examples (from data) | Why noise |
|---|---:|---|---|
| `smoothie_juice_bar` | 1,798 | Market Juice, Pure & Pressed Juice Company, Fruitland Fresh, Brewed Intentions | Juice/smoothie shops, daytime, non-alcoholic |
| `salad_bar` | 419 | **Olive Garden** (×many), Salad Box, Urban Greens | Restaurant salad-bar buffets, `basic_category=restaurant` |
| `milk_bar` | 63 | **Cold Stone Creamery**, TCBY, Handel's Homemade Ice Cream, Rita's | Ice-cream shops, `basic_category=non_alcoholic_beverage_venue` |

Total clear food/beverage noise: **2,280 rows (~10%)**.

### Edge cases (judgment calls — flagged, not auto-excluded)

| Type | n | Examples | Note |
|---|---:|---|---|
| `hookah_bar` | 233 | 1st Ave Hookah and Vape Shop, Avondale Vape and Hookah Lounge, Belo Hookah Studio | Hookah/vape lounges. Many nightlife filters exclude vape; some treat hookah lounges as nightlife. **Optional exclude.** |
| `airport_lounge` | 15 | (airside lounges) | Not a walk-in neighborhood venue; exclude if widget is neighborhood-scoped. |
| `sake_bar` | 10 | Koji Sake Lounge, The Void Sake Co., **Koji Restaurant New Haven** | Some are restaurants; small volume, low risk. Keep. |
| `gastropub` / `tapas_bar` | 929 | (`basic_category=casual_eatery`) | Food-forward but genuinely drinking venues. **Keep.** |
| `hotel_bar` | 211 | W XYZ Bar, Ptarmigan Lounge, Mallard's Bar | Real bars inside hotels. Keep (mirrors cafe "keep hotel counters" debate — here they're full bars). |
| Restaurants-with-a-bar | — | `bar_and_grill_restaurant` (dropped by anchor) | Not in dataset because it ends in "restaurant"; would need a name/alternate signal to recover if desired. |

### Not observed (but defensively excluded in proposal)

`sushi_bar`, `oyster_bar`, `raw_bar`, `snack_bar`, `candy_bar`, `juice_bar`,
`coffee` — food `*bar` types that didn't appear in this geographic sample but
could appear elsewhere. Adding them to the category-primary exclude list is cheap
insurance.

---

## 4. Data quality notes

- **4 rows have a blank `state`** and **1 row has `Mo`** (lowercase) instead of
  `MO` — ingest-side casing/normalization bug, not a filter issue. Real geographic
  coverage is all **50 states + DC**.
- ~16% of rows have **no website**; combined with low confidence this is the basis
  for the quality gate in §5.

---

## 5. PROPOSED filter (v1)

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Nightlife` |
| Distance | `10.0` miles (`1`–`3` urban, `10` rural) |
| Max results | `250` |
| Min confidence | *(empty — gate in query, see below)* |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

### Include — Basic category

```
bar
nightlife
```

### Include — Category primary (anchored)

```
*bar
night_club
nightclub
*pub
lounge
brewery
karaoke
```

### Exclude — Category primary (food/dessert `*bar` noise)

```
smoothie_juice_bar
salad_bar
milk_bar
juice_bar
sushi_bar
oyster_bar
raw_bar
snack_bar
candy_bar
```

> **Optional, product call:** add `hookah_bar` and `airport_lounge` to the
> category-primary exclude list if the widget should exclude hookah/vape lounges
> and airside lounges. Left **in** by default (they are arguably nightlife).

### Query builder

```
(basic_category_include or category_primary_include) and category_primary_exclude
```

`or` on includes is required — e.g. karaoke venues land in `basic_category =
music_venue` with `category_primary = karaoke`, and some lounges only populate one
field. `and category_primary_exclude` strips the juice/salad/milk-bar food noise.

> **Why exclude by category, not by name:** the noise here is a clean *category*
> signal (`salad_bar` = Olive Garden, `milk_bar` = ice cream), unlike the cafe
> filter where noise was brand names. No name excludes needed for v1.

### Quality gate (widget-side, recommended)

Mirror the cafe/restaurant pattern: drop **confidence < 0.7 AND no website**
(low-trust ghost listings). In this dataset that removes **1,234 rows (~5%)**
without touching high-confidence or websited venues. Keep as a widget min-quality
gate rather than a hard `min_confidence` (which would drop real bars at 0.77).

### Expected effect

| Stage | Approx. rows |
|---|---:|
| Raw pull | 22,686 |
| − category excludes (juice/salad/milk + defensive) | −~2,280 → **~20,400** |
| − quality gate (conf<0.7 & no website) | −~1,234 → **~19,200** |

---

## 6. Appendix — config history

- **raw (this pull):** anchored category includes (`*bar`, `*pub`, `night_club`,
  `nightclub`, `lounge`, `brewery`, `karaoke`) + basic (`bar`, `nightlife`), no
  excludes, no confidence gate — the analysis base in `data/nightlife_raw/`.
- **v1 (proposed, §5):** same includes + category-primary excludes for food
  `*bar` types + widget quality gate. Not yet validated against per-metro batches
  (next step: spot-check NYC / LA / a rural pin like the cafe filter's batches).
