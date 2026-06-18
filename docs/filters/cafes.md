# Filter: Cafes

> **Status: v3 (in validation) — category gate + curated national-brand name excludes.**
> Batches 1–3 (FL/GA/AL) + Round 4 (NYC Penn Station) + Round 5 (LA DTLA, 200 rows).
> Generic USA — no one-off local business names.

**Goal:** surface real **coffee & tea shops** a mom would sit at (meet a friend, sit
with kids) — coffee shops, cafes, tea rooms, roasteries. Chains (Starbucks, Dunkin',
Peet's, Blue Bottle, **Panera**, Paris Baguette) are **kept in**.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings.

---

## Product decisions (locked)

These are intentional — document them so future tuning does not “fix” them away.

| Decision | Rationale |
|---|---|
| **Keep drive-through coffee chains** (7 Brew, Dutch Bros, Ellianos) | They are legitimate coffee brands in many markets; excluding them requires per-brand logic we are not doing in the admin filter. Sit-down vs drive-through is a **UI split**, not a filter delete (see section 6). |
| **Keep Panera** | Tagged `coffee_shop`; users treat it as a cafe with seating. |
| **Keep bubble tea / boba** (Cha Cha Matcha, heytea, LELECHA, etc.) | Overture tags them as `tea_room`; category excludes would drop real tea/coffee hybrids. |
| **Keep Mudslingers** | Local/regional brand; not on the national noise list. |
| **Exclude `*nutrition*`** | Catches Herbalife-style “nutrition clubs” (`Powerful Nutrition`, etc.) with minimal collateral — unlike excluding all `smoothie_juice_bar`. |
| **No `min_confidence`** | Drops real cafes (many Starbucks rows at 0.77). |
| **No local name excludes** | `gadsden nutrition`, `magic always`, etc. are not USA-safe. |
| **No category_alternate excludes** | `donuts` / `fast_food_restaurant` kills every Dunkin'; `bubble_tea` kills kept boba cafes. |

---

## 1. Production filter — copy/paste into the admin

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Cafe` |
| Distance | `10.0` miles (`1`–`3` urban, `10` rural) |
| Max results | `250` |
| Min confidence | *(empty)* |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

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

### Exclude — Business name primary (exclude)

**Tier A — national / generic noise only** (one token per line; substring match):

```
*7-eleven*
*ampm*
*aplus*
*buc-ee*
*casey*
*chevron*
*circle k*
*clean eatz*
*conoco*
*cumberland*
*duck donut*
*exxon*
*flying j*
*getgo*
*kava bar*
*kava lounge*
*krispy kreme*
*kum and go*
*kum & go*
*lickin good donut*
*loves*
*marathon*
*mcdonald*
*murphy*
*nutrition*
*pilot*
*proudly serve*
*quiktrip*
*racetrac*
*royal cup*
*royal farms*
*sheetz*
*sinclair*
*speedway*
*stripes*
*sunoco*
*tax expresso*
*tax service*
*texaco*
*thorntons*
*valero*
*wawa*
*wfm coffee*
*wild bean*
bp 
 bp 
```

**Explicitly NOT on this list:** `*7 brew*`, `*dutch bros*`, `*ellianos*`, `*panera*`,
`*bubble tea*`, `*mudslingers*`.

**Do not add:** `*citgo*`, `*shell*`, `*mobil*` — those strings appear inside
Dunkin' names at co-located gas stations and would drop real Dunkin' rows.

Leave all other exclude boxes empty (no category excludes).

### Query builder

```
(basic_category_include or category_primary_include) and name_primary_exclude
```

`or` on includes is required — some tea rooms only populate `category_primary`
while `basic_category` is `non_alcoholic_beverage_venue`.

---

## 2. Why this is not “name excludes banned”

v2 said no name tokens because `*market*` and gas brands are unsafe nationwide. v3
adds a **small, curated national list** — gas/c-store brands, in-store counters,
nutrition clubs, tax-prep “Tax Espresso” junk — not arbitrary local strings.

| Token class | Example noise removed | Why it is safe |
|---|---|---|
| C-store / fuel | Min Matcha @ **7-Eleven**, APlus @ Sunoco | Brand names, not geography |
| In-store counter | **WFM Coffee Bar**, Proudly Serve | Whole Foods / licensed counter |
| Fast food misc | **McDonald's** (tagged `coffee_shop`) | National brand |
| Nutrition club | **Powerful Nutrition** | User decision: `*nutrition*` |
| Tax / junk | Tax Espresso, Tax Service | Obvious non-cafe |

Still **out of scope** for name tokens: finite local junk (`QA Cafe Flatiron`,
`The Lee Internet Partners`) — needs enrichment or dedup, not more tokens.

---

## 3. Round 4 — NYC Penn Station (20 mi, max 200)

**Center:** `40.748578, -73.990292` · **Prior exclude:** `*sunoco*` only.

**Verdict:** Mostly real cafes (Starbucks, Dunkin', Gregory's, Blue Bottle, tea
rooms). Noise that Tier A catches in this batch:

| Row | Why noise | Tier A token |
|---|---|---|
| McDonald's | Fast food, not a cafe | `*mcdonald*` |
| WFM Coffee Bar | Whole Foods in-store counter | `*wfm coffee*` |
| Min Matcha (address: 7-Eleven…) | Convenience store | `*7-eleven*` |
| Starbucks Pickup with Amazon Go | Pickup counter, not sit-down | *(future `is_in_store_concession`)* |

**Still leaks (enrichment-only):** `The Lee Internet Partners` (conf 0.09),
`QA Cafe Flatiron` (test/office), `Coffee Near Me`, `UE Coffee Bean Cambodia`,
hotel counters (Margaritaville), duplicate Patent Coffee at same address.

**Correctly kept:** Panera (×3), Cha Cha Matcha, heytea, LELECHA, Nana's Green Tea,
Prince Tea House — per product decisions above.

---

## 3b. Round 5 — Los Angeles DTLA (5 mi, max 200)

**Center:** `34.045806, -118.246653` · **Filter loaded:** saved `Cafe` (id 333) but
**exclude textarea showed only `*sunoco*`** and query was
`basic_category_include or category_primary_include` **without**
`and name_primary_exclude` — re-paste full v3 config before treating this as a
production sign-off.

**Verdict:** Dense urban core; overwhelmingly real cafes (Starbucks, G&B, Go Get Em
Tiger, Verve, Alfred, Cognoscenti, tea rooms in Little Tokyo, Dunkin', Philz, etc.).
No gas-station or nutrition-club noise in this batch. Bubble tea kept (I Love Boba,
Joimo Tea, Zenzu Tea @ Smorgasburg).

**Noise Tier A would remove (once full exclude list + query are applied):**

| Row | Why noise | Tier A token |
|---|---|---|
| WFM Coffee Bar | Whole Foods in-store counter | `*wfm coffee*` |

**Still leaks (enrichment-only — same classes as Round 4):**

| Row | Signal | Fix |
|---|---|---|
| Five Star Parking | Name is parking operator; website is starbucks.com | `is_in_store_concession` |
| Hyatt Hotels… / Rendezvous Court / Bluestone Lane @ Moxy | `category_alternate` includes `hotel` or hotel URL | `is_in_store_concession` |
| Cafe Royal | Hotel property (`hotelcaferoyal.com`) | venue / concession flag |
| Coffee Cart Los Angeles | `category_alternate`: `caterer` | catering ≠ neighborhood cafe |
| Old Cty Jail | Mis-geocoded listing at jail address; conf 0.21 | freshness / manual curation |
| Tea Drops / August Uncommon Tea | Very low conf; missing or HQ-style address | widget min-quality gate |
| Olympic & Soto | Walkscore/transit junk; `attractions_and_activities` | not name-filterable |
| Courage Bagels | `farmers_market`; no street address | enrichment |
| Kavahana @ Smorgasburg / Arts District Market | Market/vendor stalls | enrichment |
| Flix Cafe | Studio lot (`lacenterstudios.com`) | venue flag |
| Dulce dos | `category_primary` empty (basic only) | ingest QA |

**Correctly kept:** Paris Baguette, Panera-class bakery-cafes, drive-through Dunkin',
duplicate Starbucks/G&B/GGET locations (dedup is a widget concern, not filter delete).

**New Tier A tokens from Round 5:** none — do not add hotel or `*parking*` strings.

---

## 4. Validation batches (running log)

| Batch | Location | Rows | Notes |
|---|---|---|---|
| 1 | Fort Pierce FL | 247 | Gas brands in Dunkin' names; Wild Bean noise |
| 2 | Savannah GA | 210 | Clean; mostly real cafes |
| 3 | Alexander City AL | 469 | 7 Brew / Ellianos present — **kept** |
| 4 | NYC Penn Station | 200 | Tier A drops McDonald's, WFM, 7-Eleven co-location |
| 5 | LA DTLA | 200 | Cafe-rich; WFM leak with partial config; hotel/market junk → enrichment |

---

## 5. Residual noise (needs data enrichment)

Cannot be removed reliably with more name tokens:

| Problem | Examples | Needed column |
|---|---|---|
| In-store / pickup counters | Amazon Go Starbucks, Nespresso @ Macy's | `is_in_store_concession` |
| Hotel / venue counters | Margaritaville Coffee Shop | `is_in_store_concession` or venue flag |
| Bad / test listings | Lee Internet Partners, QA Cafe Flatiron | freshness + confidence policy in widget |
| Same brand, many addresses | Starbucks × many | dedup composite key (P4 in restaurants.md) |
| Nutrition clubs (edge names) | clubs without “nutrition” in name | `is_nutrition_club` |

See [Dev team section in restaurants.md](restaurants.md#dev-team-what-to-improve-next).

---

## 6. Sit-down vs drive-through in the UI

**Not today.** The admin `PoiDetail` list has no service-mode field (no
`is_drive_through`, `dining_type`, etc.) — only Overture categories and names.

**Recommended path (same pattern as Restaurants P-series):**

1. Add **`is_drive_through_only`** (bool) at ingest/enrichment time — brand list
   (7 Brew, Dutch Bros, Ellianos…) + optional Google Places / manual override.
2. Optionally add **`is_sit_down_cafe`** (bool) for the default widget view.
3. Widget toggle: **“Sit-down cafes”** (default) vs **“Include drive-through”**
   — filter on those columns, not on deleting brands from the saved admin filter.

The admin cafe filter should stay **inclusive** (keep drive-through chains in the
dataset); the widget applies the sit-down/drive-through split.

---

## Appendix A — config history

- **v0:** `basic_category = cafe` + heavy excludes + conf `0.7` → 0 results.
- **v1:** broad primary includes, no gate.
- **v2:** category-only gate, no excludes — shippable ceiling without enrichment.
- **v3 (current):** category gate + Tier A national `name_primary_exclude` +
  `*nutrition*`; keep Panera, boba, Mudslingers, drive-through chains; query
  `(basic_category_include or category_primary_include) and name_primary_exclude`.
