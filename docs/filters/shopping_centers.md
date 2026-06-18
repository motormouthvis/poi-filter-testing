# Filter: Shopping centers / malls

> **Status: v1 (draft from raw analysis).** Evidence base: raw category-only pull
> of **6,360 unique POIs** across 142 pins (50 states + DC). See
> [`../../data/shopping_centers_raw/README.md`](../../data/shopping_centers_raw/README.md).

**Goal:** surface real **shopping centers, malls, plazas, and outlet/strip centers**
— the multi-tenant retail destinations a shopper would drive to — while dropping
individual stores, food courts, parking operators, office/business "plazas", and
unverified stub listings.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings.

---

## 0. Admin panel parameters (paste-ready, v1)

Enter these in the PoiDetail filter builder. Compound quality gate is **deferred**
(needs dev) — see note at the bottom.

| Control | Value |
|---|---|
| Saved filter (Save as) | `Shopping` |
| Latitude, Longitude | *(your test point)* |
| Distance (miles) | `10` (use `1`–`3` in dense urban cores) |
| Max results | `250` |
| Min confidence | *(leave blank)* |
| Website | `Any` |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

**Basic category — include:**

```
shopping_center
shopping_mall
```

**Category primary — include:**

```
shopping_center
shopping_mall
outlet_mall
strip_mall
```

**Business name primary — exclude:**

```
*food court*
*parking*
*self storage*
*business park*
*business plaza*
*office park*
*medical center*
*medical plaza*
*professional plaza*
*professional building*
*industrial park*
```

**Query builder:**

```
(basic_category_include or category_primary_include) and name_primary_exclude
```

All other include/exclude boxes: **empty**. No `category_alternate` excludes (they
over-delete real centers).

> **Deferred (requires dev):** the precise quality gate `confidence < 0.5 AND no
> website` (~342 stub rows) needs a compound rule the admin doesn't support. A
> numeric `min_confidence = 0.5` is the closest single-control approximation but
> also drops ~226 real centers that lack a website and score 0.5–0.7, so prefer to
> leave it blank until the compound gate exists.

---

## 1. Dataset stats (raw pull)

| Metric | Value |
|---|---|
| Unique POIs | **6,360** |
| States covered | **51** (50 + DC) |
| `operating_status` | `open` (filtered at pull time) |
| Has website | 4,472 (70%) |
| No website | 1,888 (29%) |
| Confidence ≥ 0.9 | 2,396 |
| Confidence 0.7–0.9 | 2,490 |
| Confidence 0.5–0.7 | 906 |
| Confidence < 0.5 | 568 |

Top states: CA 724, TX 574, FL 435, NY 255, NC 228, MD 214, PA 208, OH 203,
NV 201, GA 193. (NYC, Brooklyn, and LA each hit the 200/pin cap, so dense-metro
counts are truncated by design.)

**Category structure is extremely consistent:** every record has
`basic_category = shopping_mall`, and 6,356 / 6,360 have
`category_primary = shopping_center` (4 have an empty primary). Overture funnels
the whole shopping-center universe through this single pair — there is no separate
`outlet_mall` / `strip_mall` category value in the data, so those tokens only
matter as defensive "contains" matches.

---

## 2. Include tokens used (raw pull)

**Basic category (include):**

```
shopping_center
shopping_mall
```

**Category primary (include):**

```
shopping_center
shopping_mall
outlet_mall
strip_mall
```

**Query builder:**

```
(basic_category_include or category_primary_include)
```

**Settled include logic:** the two tokens that actually do the work are
`basic_category = shopping_mall` and `category_primary = shopping_center`. Keeping
`outlet_mall` / `strip_mall` in the primary list is harmless (no distinct rows, no
pollution) and future-proofs against Overture adding those values. Unlike the
coffee/tea pull, **the `or` across includes is essentially redundant here** because
both fields are populated on virtually every row — but we keep it so the 4
empty-primary rows still come in via `basic_category`.

---

## 3. Observed noise / edge cases (evidence-based)

The headline finding: **this category is unusually clean.** Name-level noise is
tiny (only ~26 rows match any junk-name token across the whole 6,360). The real
edge cases surface through `category_alternate` and low confidence, not names.

| # | Noise class | How to spot it | Approx. count | Examples |
|---|---|---|---|---|
| 1 | **Food courts inside a mall** | name = `Food Court` / `Food Court Plaza`; often empty `category_primary` | a handful | `Food Court`, `Food Court Plaza - 818 Wilshire` |
| 2 | **Individual stores / single tenants** mislabeled as a center | retail name + `category_alternate` of `clothing_store` / `jewelry_store` / `department_store` and **no** "shopping/plaza/center/mall" cue in the name | low | `Parties Plus` (alt `event_planning`), `Godsey's Local` (alt `community_center`) |
| 3 | **Office / business "plazas" & parks** | name contains `business park` / `business plaza` / `office`; alt `office` | ~9 office, 1 business park | `Midpoint Business Plaza` (office, no web) |
| 4 | **Civic / landmark / historic mislabels** | alt `landmark_and_historical_building`, `public_plaza` (civic square), `community_center`, `central_government_office` | ~145 carry these alts (mostly still real centers) | `The Emporium (San Francisco)`, `Maryvale Mall` (alt `central_government_office`) |
| 5 | **Entertainment venues** (theaters / concert halls) reading as centers | alt `cinema` / `topic_concert_venue` / `event_planning` with no retail name cue | ~90 cinema, ~30 concert | `The Brickyard` (alt `cinema`), `Pavilion in the Park` (alt `concert_venue`) |
| 6 | **Parking operators** | name = `*parking*`; website points to a tenant | 1 | (rare in this pull; common in coffee/tea) |
| 7 | **Unverified / stub listings** | `confidence < 0.5` **and** no website; sometimes mis-geocoded or vacant | 342 | `Montlimar Plaza` (0.19), `Greenlaw Shopping Center` (0.30) |
| 8 | **Empty `category_primary`** | ingest gap — only `basic_category` populated | 4 | `Shoppes At University`, `The Emporium` |

**Important nuance on alternates:** most rows carrying `public_plaza`, `landmark`,
`cinema`, or `event_planning` in `category_alternate` are **genuine shopping
centers** that happen to host a plaza/theater/event space (`Roebuck Shopping
Center`, `Summit Shopping Center`, `Springdale Mall`). So a blanket
`category_alternate` exclude would over-delete. These alternates are **signals to
combine with a weak name + low confidence**, not standalone delete rules.

Car dealers, self-storage, and industrial "centers" — explicitly checked for and
**not found** in this category (0 `dealer`, 0 `automotive`, 0 `storage`, 0
`industrial`). That noise lives in other Overture buckets, not `shopping_center`.

---

## 4. Proposed filter (v1 draft)

Because the include side is already high-precision, the proposed filter leans on a
**light name exclude + a quality gate**, and deliberately avoids category-alternate
excludes (they over-delete real centers).

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Shopping` (new) |
| Distance | `10.0` miles (`1`–`3` urban, `10` rural) |
| Max results | `250` |
| Min confidence | *(empty — gate in query instead)* |
| Operating status | `open` |
| Deduplicate addresses | **ON** (keeps highest-confidence record per address) |

### Include — categories

**Basic category (include):**

```
shopping_center
shopping_mall
```

**Category primary (include):**

```
shopping_center
shopping_mall
outlet_mall
strip_mall
```

### Exclude — Business name primary (exclude)

Small, national-safe junk list (substring match). These remove non-retail
"centers" without touching real malls/plazas:

```
*food court*
*parking*
*self storage*
*business park*
*business plaza*
*office park*
*medical center*
*medical plaza*
*professional plaza*
*professional building*
*industrial park*
```

> Do **not** add generic retail words (`market`, `square`, `village`, `commons`,
> `crossing`, `town center`) — those are the names of real shopping centers
> (1,000+ rows each) and excluding them would gut the dataset.

### Quality gate (in the query builder)

There is no `category_alternate` exclude. Instead drop only the clearly
low-trust stubs: **confidence below 0.5 AND no website.** This removes 342 rows
(mostly vacant/mis-geocoded), keeping low-confidence rows that have a website
(those are usually real, just under-scored).

### Query builder

```
(basic_category_include or category_primary_include)
  and name_primary_exclude
```

> The confidence/website quality gate is expressed via the **Min confidence**
> control + `has_website`, or — preferably — as an enrichment-time quality flag,
> since the admin query builder combines category/name token groups but does not
> express `confidence < x AND website is null` directly. If applied as
> `min_confidence = 0.5`, expect to also lose ~226 real centers that lack a
> website but score 0.5–0.7; the **confidence-AND-no-website** rule is the more
> precise gate and is the recommended enrichment-side implementation.

### Expected impact

| Step | Rows removed | Rows remaining |
|---|---|---|
| Raw pull | — | 6,360 |
| Name excludes (food court / parking / office / business park / medical / industrial) | ~26 | ~6,334 |
| Quality gate (confidence < 0.5 **and** no website) | ~342 | ~5,993 |
| Empty `category_primary` (optional ingest QA drop) | 4 | ~5,989 |

Net: a proposed **~5,990 high-confidence shopping centers** (94% of raw), with the
deleted ~370 being food courts, office/business plazas, parking, and unverified
stubs.

---

## 5. Residual noise (needs data enrichment)

Cannot be removed reliably with name tokens or categories alone:

| Problem | Examples | Needed signal |
|---|---|---|
| Individual anchor store tagged as the center | `Parties Plus`, single-tenant rows with `clothing_store`/`jewelry_store` alt | `is_multi_tenant` / tenant count |
| Theater / concert venue reading as a center | `The Brickyard`, `Pavilion in the Park` | venue flag (combine alt `cinema`/`concert_venue` + venue name) |
| Civic plaza vs retail plaza | `public_plaza`-only civic squares | land-use / tenant enrichment |
| Mis-geocoded / vacant stubs | very low confidence, no web, no phone | freshness + min-quality policy in widget |
| Ingest gaps (empty `category_primary`) | `Shoppes At University` | ingest QA |

---

## Appendix A — config history

- **v1 (current):** category-only include
  `(basic_category_include or category_primary_include)` on
  `{shopping_center, shopping_mall, outlet_mall, strip_mall}`; light national
  `name_primary_exclude` (food court / parking / office / business park / medical
  / industrial); recommended quality gate `confidence < 0.5 AND no website`; no
  `category_alternate` excludes (they over-delete real centers).
