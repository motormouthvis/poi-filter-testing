# Filter: Cafes / Coffee & Tea

> **Status: v1 (final) — evidence-based proposal from the raw category pull.**
> Built from `data/coffee_tea_raw/` (18,483 unique POIs, 52 = 50 states + DC, 142 pins).
> Generic USA — no one-off local business names.

**Goal:** surface real **coffee & tea shops** people sit at or drive through — coffee
shops, cafes, tea rooms, roasteries, boba/bubble-tea, drive-thru coffee — while
removing nutrition/kava clubs, gas-station & convenience coffee counters, and
in-store concessions. Chains (Starbucks, Dunkin', Peet's, Blue Bottle, **Panera**,
Paris Baguette) and drive-thru brands (**7 Brew, Dutch Bros, Ellianos**) are **kept**.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings.

---

## 0. Admin panel parameters (paste-ready, v1)

Enter these in the PoiDetail filter builder. The compound quality gate is
**deferred** (needs dev) — see the note at the bottom of this section.

| Control | Value |
|---|---|
| Saved filter (Save as) | `Cafe` |
| Latitude, Longitude | *(your test point)* |
| Distance (miles) | `10` (use `1`–`3` in dense urban cores) |
| Max results | `250` |
| Min confidence | *(leave blank)* — `0.77` is a sentinel default; a floor deletes real chains |
| Website | `Any` |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

**Basic category — include:**

```
coffee_shop
tea_room
```

**Category primary — include:**

```
coffee_shop
tea_room
coffee_roastery
```

**Category alternate — exclude:** *(leave empty — see §3, every candidate over-deletes real cafes)*

**Business name primary — exclude:**

```
aplus
sunoco
wild bean
wfm coffee
proudly serve
mcdonald
krispy kreme
duck donut
royal cup
clean eatz
food mart
chevron
wawa
nutrition
herbalife
kava
kratom
7-eleven
ampm
buc-ee
circle k
conoco
cumberland
exxon
getgo
kum & go
kum and go
quiktrip
racetrac
royal farms
sheetz
sinclair
texaco
thorntons
valero
```

**Query builder:**

```
(basic_category_include or category_primary_include) and name_primary_exclude
```

All other include/exclude boxes: **empty**. `or` on the includes is required — tea
rooms populate `category_primary = tea_room` while their `basic_category` is
`non_alcoholic_beverage_venue` (there is **no** `tea_room` value in `basic_category`).

> **Deferred (requires dev):** the precise quality gate `confidence < 0.7 AND no
> website` (~907 rows) cannot be expressed in the current admin builder, which only
> offers a single numeric `min_confidence` and a separate `has_website` toggle. Do
> **not** set `min_confidence` as a substitute — it would delete the 4,718
> sentinel-`0.77` cafes (Starbucks pickups, APlus, many tea rooms). Leave the gate
> out until a compound rule is supported.

**Expected effect:** of 18,483 raw rows, the name-exclude list removes **166**
(~0.9%) → **≈ 18,317 kept (99.1%)**. (`aplus` and `sunoco` are the *same* 23
"APlus at Sunoco" rows; the 166 is the de-duplicated union.)

---

## 1. Dataset summary (raw pull)

`python scripts/analyze_coffee_tea.py` on `data/coffee_tea_raw/coffee_tea_master.csv`:

| Metric | Value |
|---|---|
| Total unique POIs | **18,483** |
| States covered | **52** (50 + DC) |
| Has website | 15,658 (84%) |
| No website | 2,825 (15%) |

**Top states:** CA 1,590 · TX 1,418 · FL 942 · OH 662 · CO 635 · NY 629 · NC 606 ·
WA 599 · OR 589 · MI 559.

**`basic_category` breakdown (complete — only 2 values):**

| basic_category | count |
|---|---|
| `coffee_shop` | 17,520 |
| `non_alcoholic_beverage_venue` | 963 |

> There is **no `tea_room` in `basic_category`** — tea rooms surface as
> `basic_category = non_alcoholic_beverage_venue` with `category_primary = tea_room`.
> This is why the include query must be `basic_category_include **or**
> category_primary_include`.

**`category_primary` breakdown (complete — only 4 values):**

| category_primary | count |
|---|---|
| `coffee_shop` | 17,470 |
| `tea_room` | 963 |
| `coffee_roastery` | 32 |
| *(empty)* | 18 |

**Confidence distribution:**

| Bucket | count | % |
|---|---|---|
| `<0.5` | 1,558 | 8% |
| `0.5–0.7` | 734 | 4% |
| `0.7–0.9` | 5,837 | 32% |
| `>=0.9` | 10,354 | 56% |

> **`0.77` is a sentinel default, not a real score.** **4,718 rows (25%)** have
> `confidence` **exactly `0.77`** — including obvious real venues (Starbucks @ Target,
> many tea rooms, "APlus at Sunoco"). Any confidence gate must treat `0.77` as
> "unknown", not "low quality", or it will delete thousands of legitimate cafes.

---

## 2. Include tokens used (raw pull)

These are the tokens entered in `scripts/scrape_poi_admin.py`. Matching is
**contains/substring**, so the short tokens absorb the longer Overture values.

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

**Query builder:**

```
(basic_category_include or category_primary_include)
```

`min_confidence = 0`, `operating_status = open`, all exclude boxes empty. (Note:
`tea_room` as a `basic_category` token is a harmless no-op — no row carries it — but
it is kept for symmetry with the `category_primary` include.)

---

## 3. Observed noise / edge cases (evidence from the data)

The `category_primary` set is extremely clean (only 4 values). Noise therefore
enters almost entirely through **names**, not categories — which is why the
category-alternate exclude list is **empty** (every candidate kills real cafes).

### 3a. Category-alternate exclude candidates — all rejected

| Candidate `category_alternate` exclude | Rows hit | Real cafes among them | Verdict |
|---|---|---|---|
| `smoothie_juice_bar` | **847** | Kaladi Brothers, A Whole Latte Love, Downtown Grind, Common Grounds Espresso… (virtually all real coffee shops) | ❌ **reject** — would delete ~840 real cafes to remove a handful of nutrition clubs (caught by name instead) |
| `convenience_store` | **15** | Easy Luck Coffee & Bodega (0.99), The Red Hook (0.98), Liquid Highway (0.98), 2× Starbucks, Salto, Yellow Dog, Boss Tom's Roasters | ❌ **reject** — ~10 of 15 are real; only Chevron/Food Mart/Wawa/Stone House are noise (handled by name) |
| `gas_station` | **1** | — (`Stone House Coffee Shots`) | ❌ **reject** — single row, not worth a category rule |

**Conclusion:** no `category_alternate` excludes. The donuts/`fast_food_restaurant`
alts (which would kill every Dunkin') and `bubble_tea` (which would kill kept boba)
were already ruled out in prior work and remain out.

### 3b. Name-based noise (what the exclude list targets)

| Noise type | Rows | Real examples from the data | Token(s) | Collateral check |
|---|---|---|---|---|
| **Gas-station coffee counter** | 23 | `APlus at Sunoco` (×23, conf `0.77`, no alt) | `aplus`, `sunoco` | `aplus` (no space) avoids `Java Plus`; `a plus` / `a-plus` would hit it |
| **In-store / fuel concession** | 5 | `Wild Bean Cafe` (BP in-store) | `wild bean` | clean |
| **Grocery counter** | 42 | `WFM Coffee Bar` (Whole Foods) | `wfm coffee` | `wfm coffee` is safer than bare `wfm`; both clean here |
| **"We Proudly Serve …" licensed counter** | 0 now | (pattern from other pins, e.g. hotels) | `proudly serve` | forward guard, 0 collateral |
| **Fast food / donut chains** | 27 | `McDonald's` (22), `Krispy Kreme` (4), `Duck Donuts` (1) | `mcdonald`, `krispy kreme`, `duck donut` | clean |
| **Coffee supplier / wholesale brand** | 6 | `Royal Cup Coffee and Tea`, `Royal Cup Inc` | `royal cup` | wholesaler, not a sit-down cafe |
| **C-store / misc** | 4 | `Manchester Food Mart 204`, `Northport Chevron`, `Wawa`, `Clean Eatz` (×2) | `food mart`, `chevron`, `wawa`, `clean eatz` | clean |
| **Nutrition clubs (Herbalife-style)** | 23 | `Powerful Nutrition`, `No Limit Nutrition`, `49 Nutrition`, `Flex'd Up Nutrition (Herbalife)`, `Surf's Up Nutrition (Herbalife)`, `StrongPour: Nutrition Bar` | `nutrition`, `herbalife` | **verified zero legit "… Nutrition & Coffee" sit-down cafes** — all 23 are supplement/shake clubs (mostly `smoothie_juice_bar` alt, low conf or no website) |
| **Kava / kratom lounges** | 32 | `Ohana Kava Bar`, `Kava Collective`, `Kavasutra Kava Bar`, `Grassroots Kava House`, `Miami Kava & Coffee`, `Heights Kava Lounge` | `kava`, `kratom` | see collateral note below |

> **Kava collateral (accepted):** a bare-contains `kava` also removes **2 real
> coffeehouses** whose *names* contain the substring — `Kavarna Coffeehouse` and
> `The Kavanaugh`. This is the locked product decision (exclude kava/kratom); the
> 2-row collateral is acceptable and could be restored later via a name allowlist or
> an `is_kava_bar` enrichment flag. `kratom` matches 0 rows today (the canonical
> "Good Vibez Coffee Kava Kratom" example is caught by `kava` anyway) and is kept as
> a forward guard.

### 3c. Tokens explicitly **rejected** as unsafe (they hit real cafes)

Verified against the data — each of these would delete a genuine coffee/tea shop:

| Rejected token | Real cafe it would kill |
|---|---|
| `pilot` | `Pilot's Coffee House` |
| `casey` | `Casey's Coffee` |
| `stripes` | `Stars and Stripes Coffee House` |
| `murphy` | `Jughead and Murphys Coffee House` |
| `speedway` | `Desert Drifter (Speedway & Main)` (address, not a c-store) |
| `flying j` | `Flying Java Coffee` (`flying j`ava) |
| `kum` (bare) | `Kumquat Coffee DTLA` → use anchored `kum & go` / `kum and go` |
| `loves` (bare) | too generic (Love/Lovespresso names) — dropped |
| `a plus` / `a-plus` | `Java Plus` → use `aplus` (no space) |
| `@` | half the `@` rows are real (`For Five Coffee @ M Street`, `Dope Coffee @ Azalea`, `Coffeentalk @Hillcrest`, `Zeke's Coffee @ …`) — **do not** name-exclude `@`; defer to `is_in_store_concession` |
| `citgo`, `shell`, `mobil` | appear inside co-located Dunkin' names |

### 3d. Known phantom / low-quality rows

`Wave 31` (conf `0.58`, no website) is a representative ghost listing. It is **not**
name-filterable without local strings; it falls to the deferred compound gate
(`confidence < 0.7 AND no website`, see §5) — not to `min_confidence`.

---

## 4. Proposed filter (v1)

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Cafe` |
| Distance | `10.0` miles (`1`–`3` urban, `10` rural) |
| Max results | `250` |
| Min confidence | *(empty)* — `0.77` sentinel makes a numeric gate unsafe |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

### Include

```
basic_category:    coffee_shop, tea_room
category_primary:  coffee_shop, tea_room, coffee_roastery
```

### Exclude — Category alternate

*(empty — see §3a; convenience_store/gas_station/smoothie_juice_bar all over-delete real cafes)*

### Exclude — Business name primary

The curated, **nationally-safe** list from §3b/§3c (substring match unless noted):

```
aplus          sunoco         wild bean      wfm coffee     proudly serve
mcdonald       krispy kreme   duck donut     royal cup      clean eatz
food mart      chevron        wawa           nutrition      herbalife
kava           kratom
7-eleven       ampm           buc-ee         circle k       conoco
cumberland     exxon          getgo          kum & go       kum and go
quiktrip       racetrac       royal farms    sheetz         sinclair
texaco         thorntons      valero
```

*(The trailing block — `7-eleven` … `valero` — are proper-noun gas/c-store brands
with ~0 collateral today; kept as forward guards for other geographies.)*

**Explicitly NOT excluded (kept in):** `7 brew`, `dutch bros`, `ellianos`, `panera`,
`bubble tea` / `boba`, `mudslingers`, and all `smoothie_juice_bar`-tagged cafes.

### Query builder

```
(basic_category_include or category_primary_include) and name_primary_exclude
```

### Quality gate (widget-side, not a numeric admin floor)

Because `0.77` is a sentinel, use a **compound** gate instead of `min_confidence`:

> **Drop a row when `confidence < 0.7` AND it has no website.** (~907 rows, ~5%.)

This targets the unverifiable long tail (`Wave 31`, vanity nutrition pages, ghost
listings) while protecting the 4,718 sentinel-`0.77` records and every websited
cafe. A naive `min_confidence = 0.7` floor would instead delete ~32% of the dataset
(all `0.77` rows + below), including real Starbucks/tea rooms — so it is rejected.

---

## 5. Why no numeric `min_confidence`

| Option | Effect | Verdict |
|---|---|---|
| `min_confidence = 0.7` | Deletes all 4,718 `0.77`-sentinel rows + everything below (~7,000+ rows) | ❌ reject |
| `min_confidence = 0.5` | `0.77 > 0.5` survives, but band `0.5–0.7` (734) goes regardless of website | ⚠️ blunt |
| **`confidence < 0.7` AND no website** | Drops ~907 unverifiable rows; keeps every sentinel + websited cafe | ✅ proposed (deferred to dev) |

---

## 6. Product decisions (locked)

These are intentional — document them so future tuning does not "fix" them away.

| Decision | Rationale |
|---|---|
| **Keep drive-thru coffee chains** (7 Brew, Dutch Bros, Ellianos) | Legitimate coffee brands; sit-down vs drive-thru is a **UI split**, not a filter delete (see §7). |
| **Keep Panera** | Tagged `coffee_shop`; users treat it as a cafe with seating. |
| **Keep bubble/boba tea** (Cha Cha Matcha, heytea, LELECHA, Nana's Green Tea…) | Overture tags them `tea_room`; category excludes would drop real tea/coffee hybrids. |
| **Keep Mudslingers** | Local/regional coffee brand; not on the national noise list. |
| **Exclude nutrition clubs** (`*nutrition*`, `*herbalife*`) | Herbalife-style shake/supplement clubs — verified zero legit "Nutrition & Coffee" sit-down cafes in the data. |
| **Exclude kava/kratom** (`*kava*`, `*kratom*`) | Kava/kratom lounges are not coffee/tea cafes. Accept 2-row collateral (`Kavarna Coffeehouse`, `The Kavanaugh`). |
| **Exclude gas-station / convenience coffee** (`aplus`, `sunoco`, `wawa`, `chevron`, `food mart`, fuel brands) | Not destination cafes. Anchored tokens only — bare gas brands that are English words (`pilot`, `casey`, `stripes`, `murphy`, `speedway`) are rejected (§3c). |
| **Exclude in-store concessions** (`wfm coffee`, `wild bean`, `royal cup`, `proudly serve`, `mcdonald`) | Whole Foods / BP / licensed counters, not standalone cafes. |
| **No `category_alternate` excludes** | Every candidate (`convenience_store`, `gas_station`, `smoothie_juice_bar`) over-deletes real cafes (§3a). |
| **No `@` name exclude** | Half the `@` rows are real cafes (§3c); defer to `is_in_store_concession`. |
| **No `min_confidence` floor** | `0.77` sentinel + many real Starbucks/tea rooms at `0.77` (§5). |
| **No one-off local name excludes** | Not USA-safe. |

---

## 7. Sit-down vs drive-through in the UI

**Not today.** The admin `PoiDetail` list has no service-mode field (no
`is_drive_through`, `dining_type`, etc.) — only Overture categories and names.

**Recommended path:**

1. Add **`is_drive_through_only`** (bool) at ingest/enrichment — brand list
   (7 Brew, Dutch Bros, Ellianos…) + optional Google Places / manual override.
2. Optionally add **`is_sit_down_cafe`** (bool) for the default widget view.
3. Widget toggle: **"Sit-down cafes"** (default) vs **"Include drive-through"** —
   filter on those columns, not by deleting brands from the saved admin filter.

The admin cafe filter stays **inclusive** (drive-thru chains remain in the dataset);
the widget applies the sit-down/drive-thru split.

---

## 8. Residual noise (needs data enrichment)

Cannot be removed reliably with more name tokens:

| Problem | Examples | Needed column |
|---|---|---|
| In-store / pickup counters | `Starbucks @ Target`, `Market @ Hyatt Regency`, Amazon Go pickup | `is_in_store_concession` |
| Hotel / venue counters | `Market Place Coffee Shop @ Hilton Atlanta`, Margaritaville | `is_in_store_concession` / venue flag |
| Bad / test / ghost listings | `Wave 31` (0.58, no web), `The Lee Internet Partners` (0.09) | compound `confidence<0.7 AND no website` gate |
| Same brand, many addresses | Starbucks × many | dedup composite key |
| Kava coffeehouses mis-removed | `Kavarna Coffeehouse`, `The Kavanaugh` | name allowlist / `is_kava_bar` flag |

---

## Appendix A — reproduce

```bash
pip install requests
python scripts/scrape_poi_admin.py --pins data/coffee_tea_raw/pins.csv   # full pull (only if CSV missing)
python scripts/analyze_coffee_tea.py                                      # summary stats
```

Raw dataset + column docs: [`../../data/coffee_tea_raw/README.md`](../../data/coffee_tea_raw/README.md).
