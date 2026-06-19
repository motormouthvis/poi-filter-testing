# Filter: Gyms / Fitness

> **Status: v1 (draft) — evidence-based proposal from the raw category pull.**
> Built from `data/gyms_raw/` (23,788 unique POIs, 51 states, 142 pins).
> Generic USA — no one-off local business names.

**Goal:** surface real **places people go to work out** — full-service gyms,
boutique fitness studios (yoga, pilates, barre, spin), CrossFit boxes, martial
arts dojos, boxing gyms, climbing gyms. Big chains (Planet Fitness, Anytime
Fitness, LA Fitness, Crunch, Orangetheory, F45) are **kept in**.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings.

---

## 0. Admin panel parameters (paste-ready, v1)

Enter these in the PoiDetail filter builder. Compound quality gate is **deferred**
(needs dev) — see note at the bottom.

| Control | Value |
|---|---|
| Saved filter (Save as) | `Gym` |
| Latitude, Longitude | *(your test point)* |
| Distance (miles) | `10` (use `1`–`3` in dense urban cores) |
| Max results | `250` |
| Min confidence | *(leave blank)* — `0.77` is a sentinel default; a floor deletes real chains |
| Website | `Any` |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

**Basic category — include:**

```
gym
fitness_center
```

**Category primary — include:**

```
gym
fitness_center
yoga_studio
pilates_studio
martial_arts
boxing_gym
climbing_gym
crossfit
gymnastics_center
aerial_fitness_center
```

**Category alternate — exclude:**

```
day_spa
swimming_pool
golf_course
golf_instructor
dance_school
```

**Business name primary — exclude** (plain = contains; a leading `*` is stripped on save — see admin-filter-builder.md):

```
physical therapy
chiropract
country club
golf academy
swim academy
swim school
```

**Query builder:**

```
(basic_category_include or category_primary_include) and category_alternate_exclude and name_primary_exclude
```

All other include/exclude boxes: **empty**.

> **Deferred (requires dev):** the precise quality gate `confidence < 0.5 AND no
> website` (~637 rows) cannot be expressed in the current admin builder, which only
> offers a single `min_confidence` and a separate `has_website`. Do **not** set
> `min_confidence` as a substitute — it would delete the 5,820 sentinel-`0.77`
> gyms. Leave the gate out until a compound rule is supported.

---

## 1. Dataset summary (raw pull)

`python scripts/analyze_gyms.py` on `data/gyms_raw/gyms_master.csv`:

| Metric | Value |
|---|---|
| Total unique POIs | **23,788** |
| States covered | **51** (50 + DC) |
| Has website | 21,159 (88%) |
| No website | 2,629 (11%) |

**Top states:** CA 1,800 · TX 1,794 · FL 1,202 · CO 800 · NC 800 · TN 742 ·
OH 730 · GA 694 · NY 678 · MI 676.

**`basic_category` breakdown:**

| basic_category | count |
|---|---|
| `gym` | 14,391 |
| `fitness_studio` | 4,288 |
| `sport_or_recreation_club` | 3,704 |
| `sport_or_fitness_facility` | 1,405 |

**`category_primary` breakdown (complete — only 11 distinct values):**

| category_primary | count |
|---|---|
| `gym` | 14,390 |
| `martial_arts_club` | 3,691 |
| `yoga_studio` | 3,004 |
| `pilates_studio` | 1,277 |
| `sports_and_fitness_instruction` | 860 |
| `gymnastics_center` | 458 |
| `boxing_gym` | 61 |
| `rock_climbing_gym` | 26 |
| `chinese_martial_arts_club` | 13 |
| `aerial_fitness_center` | 7 |
| *(empty)* | 1 |

**Confidence distribution:**

| Bucket | count | % |
|---|---|---|
| `<0.5` | 2,919 | 12% |
| `0.5–0.7` | 2,096 | 8% |
| `0.7–0.9` | 8,609 | 36% |
| `>=0.9` | 10,164 | 42% |

> **`0.77` is a sentinel default, not a real score.** 5,820 rows (24% of the
> dataset) have `confidence` **exactly `0.77`** — including obvious real gyms
> (Anytime Fitness, Planet Fitness, YMCA). Any confidence gate must treat `0.77`
> as "unknown", not "low quality", or it will delete thousands of legitimate gyms.

---

## 2. Include tokens used (raw pull)

These are the tokens entered in `scripts/scrape_gyms.py` (`CATEGORY_PARAMS`).
Matching is **contains/substring**, so the short tokens absorb the longer Overture
values (e.g. `martial_arts` → `martial_arts_club`, `chinese_martial_arts_club`;
`climbing_gym` → `rock_climbing_gym`).

**Basic category (include):**

```
gym
fitness_center
```

**Category primary (include):**

```
gym
fitness_center
yoga_studio
pilates_studio
martial_arts
boxing_gym
climbing_gym
crossfit
sports_and_fitness_instruction
```

**Query builder:**

```
(basic_category_include or category_primary_include)
```

`min_confidence = 0`, `operating_status = open`, `max_results = 200`, all exclude
boxes empty. (Note: Overture has no standalone `fitness_center` / `crossfit`
`category_primary` — CrossFit boxes and most chains are tagged `gym`; the tokens
are harmless no-ops kept for completeness.)

---

## 3. Observed noise / edge cases (evidence from the data)

The `category_primary` set is clean, so most noise enters two ways:
(a) the `gym` bucket is a **catch-all** that swallows non-workout venues, and
(b) `category_primary = sports_and_fitness_instruction` (860 rows) is a grab-bag
of coaches/academies, many of which are not gyms.

| Noise type | ~Count* | Real examples from the data | Signal |
|---|---|---|---|
| **Coaching / sport academies** (golf, hockey, "athletics") | ~300 of the 860 `sports_and_fitness_instruction` | `Blake Smith Golf Academy`, `GO Golf Academy`, `Alaska Goaltending Academy`, `Tuscaloosa Junior Golf Academy` | `cp=sports_and_fitness_instruction` + `golf`/`academy` in name |
| **Swim clubs / aquatics** | ~35 by name | `Swim America Of Gainesville`, `Bone Island Swim Club`, `Delaware Swim & Fitness Center` | `swim` in name; `swimming_pool` in `category_alternate` |
| **Golf / country clubs** | ~50 by name | `Flagstaff Athletic Club – N Country Club`, `Alabama Golf` | `golf`/`country club` in name; `golf_course` alt |
| **Dance schools** | ~95 by name | `McCafferty's School Of Irish Dance`, `Dance Starz`, `Williams Dance & Gymnastics` | `dance` in name; `dance_school` alt |
| **Nutrition / supplement clubs** (Herbalife-style) | ~86 by name | `Tumamoc Nutrition Club & Fitness`, `Fit Bar Nutrition`, `Push fitness & Nutrition` | `nutrition`/`supplement`/`smoothie`/`juice` in name; often low conf, no website |
| **Physical therapy / chiropractic** | ~14 by name | `Total Balance Physical Therapy`, `Spring Forward Physical Therapy`, `Brickell Family Chiropractic` | `physical_therapy`/`chiropractor` in `category_alternate` |
| **Day spas / tanning / salon** | ~5 tanning, several spa | `Soluna Yoga + Spa` (alt `day_spa,spas`), `Club Rumba spa` | `day_spa`/`spas`/`tanning_salon` alt; `spa`/`tanning` in name |
| **YMCA / community & rec centers** | ~484 by name | `YMCA`, `Anchorage Community YMCA`, rec/community centers | `community_center`/`community_services_non_profits` alt — **borderline, see below** |

\* Counts are heuristic name/category scans, not exact filter output. The
combined `analyze_gyms.py` noise heuristic flags **~890 rows (3–4%)** as
likely-non-gym; treating `sports_and_fitness_instruction` coaching/academies and
the aquatic/dance/nutrition leaks together puts the practical noise ceiling closer
to **~6–8%**.

### Borderline — keep or drop?

- **YMCA / community / rec centers (~484):** these *do* have gyms and group
  fitness. Recommend **KEEP** for a "where can I work out" widget; only drop if
  the product specifically wants commercial studios.
- **Gym + tanning / gym + spa combos** (`GFG Fitness and Tanning`,
  `Alameda Fitness & Spa`): these are real gyms that *also* tan/spa — **KEEP**.
  Only *pure* tanning salons / day spas are noise, and those are rare here.
- **Martial arts / dance hybrids** (`The Annex Yoga & Dance Fitness`): real
  studios — **KEEP**. Pure dance *schools* (kids' recital studios) are noise.

---

## 4. Proposed filter (v1)

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Gym` |
| Distance | `10.0` miles (`1`–`3` urban, `10` rural) |
| Max results | `250` |
| Min confidence | *(empty)* — `0.77` sentinel makes a numeric gate unsafe |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

### Include

**Basic category (include):**

```
gym
fitness_center
```

**Category primary (include):**

```
gym
fitness_center
yoga_studio
pilates_studio
martial_arts
boxing_gym
climbing_gym
crossfit
gymnastics_center
aerial_fitness_center
```

> Deliberately **drop `sports_and_fitness_instruction` from the include** in the
> production filter — it is the single noisiest primary (golf/hockey/swim coaches,
> academies). The genuine gyms it covers (e.g. `Alaska Athletics`) almost always
> also carry `gym` in `category_alternate`, so add `category_alternate (include) = gym`
> if recall drops too far. Keep it in the *raw* pull (above) for analysis only.

### Exclude — Category alternate (exclude)

Removes venues whose secondary category reveals a non-workout primary purpose
(substring match; safe because these tokens don't appear inside real gym alts):

```
day_spa
swimming_pool
golf_course
golf_instructor
dance_school
```

### Exclude — Business name primary (exclude)

National / generic noise only (substring match):

```
*physical therapy*
*chiropract*
*country club*
*golf academy*
*swim academy*
*swim school*
```

> **Do NOT** add bare `*nutrition*` here as aggressively as the cafe filter:
> several legit gyms are named `... Fitness & Nutrition`. Instead, rely on the
> quality gate below to drop the low-signal Herbalife-style clubs, which are
> overwhelmingly low-confidence and websiteless.

### Query builder

```
(basic_category_include or category_primary_include)
  and category_alternate_exclude
  and name_primary_exclude
```

### Quality gate (widget-side, not a numeric admin floor)

Because `0.77` is a sentinel, use a **compound** gate instead of `min_confidence`:

> **Drop a row when `confidence < 0.5` AND it has no website.**

This targets the genuinely unverifiable long tail (637 rows, ~3%) — abandoned
listings, vanity "nutrition club" pages, ghost studios — while protecting the
5,820 sentinel-`0.77` records and every websited gym. A naive `confidence < 0.7`
floor would instead delete ~24% of the dataset (all the `0.77` rows), including
brand-name gyms, so it is explicitly rejected.

---

## 5. Why no numeric `min_confidence`

| Option | Effect | Verdict |
|---|---|---|
| `min_confidence = 0.7` | Deletes all 5,820 `0.77`-sentinel rows (Anytime/Planet/YMCA included) + everything below | ❌ reject |
| `min_confidence = 0.5` | Still deletes the `0.77` band? No — `0.77 > 0.5` survives, but band `0.5–0.7` (2,096) goes regardless of website | ⚠️ blunt |
| **`confidence < 0.5` AND no website** | Drops 637 unverifiable rows; keeps every sentinel + websited gym | ✅ proposed |

---

## Appendix A — reproduce

```bash
pip install requests
python scripts/scrape_gyms.py --pins data/coffee_tea_raw/pins.csv   # full pull
python scripts/analyze_gyms.py                                       # summary stats
```

Raw dataset + column docs: [`../../data/gyms_raw/README.md`](../../data/gyms_raw/README.md).
