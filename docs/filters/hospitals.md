# Filter: Hospitals (24/7 Emergency Room)

> **Status: v1 (draft) — evidence-based proposal from the raw category pull.**
> Built from `data/hospitals_raw/` (21,720 unique POIs, 51 states, 142 pins).
> Generic USA — no one-off local business names.

**Goal:** surface **real hospitals with a 24-hour Emergency Room** — the kind you'd
go to for an emergency (general acute-care hospitals, regional medical centers,
children's hospitals, freestanding ERs). **Exclude** veterinary/animal hospitals,
urgent care, walk-in clinics, specialty/outpatient medical centers, doctor offices,
surgery/imaging/dialysis centers, rehab/psych/hospice facilities, nursing homes,
pharmacies, and medical-equipment B2B vendors.

> Overture has **no explicit "24-hour ER" flag**. Only **1,065 / 21,720 (4%)** of
> the raw pull carry an `emergency_room` category signal at all, so *requiring* it
> would delete ~95% of genuine hospitals. Instead we **approximate**: keep the
> hospital category universe + the explicit `emergency_room` signal, and **remove
> the non-ER medical facilities** structurally and by name.

See [`../admin-filter-builder.md`](../admin-filter-builder.md) for field meanings.

---

## 0. Admin panel parameters (paste-ready, v1)

Enter these in the PoiDetail filter builder. The compound quality gate is
**deferred** (needs dev) — see note at the bottom.

| Control | Value |
|---|---|
| Saved filter (Save as) | `Hospital` |
| Latitude, Longitude | *(your test point)* |
| Distance (miles) | `20` (use `1`–`5` in dense urban cores) |
| Max results | `200` |
| Min confidence | `0.7` — safe here; the `0.77` sentinel **survives** a `0.7` floor (see §5) |
| Website | `Any` |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

**Basic category — include:**

```
hospital
```

**Category primary — include:**

```
hospital
emergency_room
```

**Category primary — exclude:**

```
animal
pet
hospitalist
equipment
```

**Category alternate — exclude:**

```
veterinarian
pets
```

**Business name primary — exclude** (also paste into **Business name common — exclude**):

```
urgent care
walk-in
walk in
immediate care
express care
dental
dentist
orthodont
veterinar
animal hospital
rehab
recovery
behavioral
mental health
psychiat
detox
hospice
nursing home
skilled nursing
assisted living
dialysis
imaging
radiology
pharmacy
med spa
medspa
chiropract
physical therapy
occupational therapy
surgery center
surgical center
endoscopy
eye clinic
vision center
std clinic
free clinic
wellness center
```

**Query builder:**

```
(basic_category_include or category_primary_include)
  and category_primary_exclude
  and category_alternate_exclude
  and name_primary_exclude
  and name_common_exclude
```

All other include/exclude boxes: **empty**.

> **Deferred (requires dev):** the precise quality gate `confidence < 0.5 AND no
> website` (551 rows in the raw pull) cannot be expressed in the current admin
> builder, which only offers a single `min_confidence` and a separate
> `has_website`. The recommended `min_confidence = 0.7` is a safe approximation
> here (unlike for gyms) because the `0.77` sentinel sits **above** `0.7`. Do **not**
> raise it to `0.9` — that deletes every `0.77`-sentinel hospital (see §5).

---

## 1. Dataset summary (raw pull)

`python scripts/analyze_hospitals.py` on `data/hospitals_raw/hospitals_master.csv`:

| Metric | Value |
|---|---|
| Total unique POIs | **21,720** |
| States covered | **51** (50 + DC) |
| Has website | 18,588 (85%) |
| No website | 3,132 (14%) |

**Top states:** TX 1,800 · CA 1,659 · FL 1,164 · OH 759 · TN 745 · NC 707 ·
GA 650 · MI 642 · CO 629 · NY 619.

**`basic_category` breakdown:**

| basic_category | count |
|---|---|
| `outpatient_care_facility` | 10,570 |
| `hospital` | 10,123 |
| `emergency_department` | 697 |
| `animal_or_pet_service` | 147 |
| `b2b_service` | 101 |
| `specialty_hospital` | 82 |

**`category_primary` breakdown (complete — only 9 distinct values):**

| category_primary | count | keep? |
|---|---|---|
| `medical_center` | 10,570 | ❌ outpatient swallow (see §3) |
| `hospital` | 9,758 | ✅ core |
| `emergency_room` | 697 | ✅ gold ER signal |
| `hospitalist` | 364 | ❌ individual physicians |
| `hospital_equipment_and_supplies` | 101 | ❌ B2B vendor |
| `animal_hospital` | 95 | ❌ veterinary |
| `childrens_hospital` | 82 | ✅ real (has ER) |
| `emergency_pet_hospital` | 52 | ❌ veterinary |
| *(empty)* | 1 | — |

**Confidence distribution:**

| Bucket | count | % |
|---|---|---|
| `<0.5` | 1,658 | 7% |
| `0.5–0.7` | 2,026 | 9% |
| `0.7–0.9` | 12,210 | 56% |
| `>=0.9` | 5,826 | 26% |

> **`0.77` is a sentinel default, not a real score.** **9,162 rows (42%)** have
> `confidence` **exactly `0.77`** — including obvious real hospitals. Critically,
> `0.77 > 0.7`, so a `min_confidence = 0.7` floor **keeps** the sentinel band; a
> `0.9` floor (the user's current setting) **deletes all of it**.

---

## 2. Include tokens used (raw pull)

These are the tokens entered in `scripts/scrape_hospitals.py` (`CATEGORY_PARAMS`).
Matching is **contains/substring**, so short tokens absorb longer Overture values
(`hospital` → `childrens_hospital`, `animal_hospital`, `hospital_equipment_and_supplies`,
`hospitalist`; `medical_center` → the `outpatient_care_facility` universe).

**Basic category (include):**

```
hospital
```

**Category primary (include):**

```
hospital
emergency_room
medical_center
```

**Query builder:**

```
(basic_category_include or category_primary_include)
```

`min_confidence = 0`, `operating_status = open`, `max_results = 200`, all exclude
boxes empty. (Note: `medical_center` is kept in the *raw* pull only — it is the
dominant noise source and is **dropped** from the production filter, see §3/§4.)

---

## 3. Observed noise / edge cases (evidence from the data)

Two structural facts drive almost all the noise:
(a) the `medical_center` include is a **contains** match for
`outpatient_care_facility` — it drags in **10,570** non-ER outpatient venues, and
(b) the `hospital` substring token also matches `animal_hospital`,
`emergency_pet_hospital`, `hospital_equipment_and_supplies`, and `hospitalist`.

| Noise type | ~Count* | Real examples from the data | Signal |
|---|---|---|---|
| **Outpatient / medical_center** (urgent care, COVID clinics, doctor offices, recovery centers, eye doctors) | **10,570** (`cp=medical_center`); only **36** carry an ER tag | `American Care Medical Center`, `Covid Clinic`, `WellMed at Fort Pierce`, `Just Believe Recovery Center`, `Dr. Lynn Erbe, OD` | `category_primary = medical_center` / `basic_category = outpatient_care_facility` |
| **Urgent care / walk-in** | ~774 by name | `MD Now Urgent Care`, `TCMA Urgent Care`, `Physicians Immediate Care` | `urgent care`/`walk-in`/`immediate care` in name; `urgent_care_clinic` alt |
| **Clinics / doctor offices / specialty depts** | ~3,887 by name | `Pulmonology and Sleep Medicine Clinic`, `UAB Vein Clinic`, `Cardiovascular Consultants` | `clinic`/`associates`/`MD` in name; `doctor`/`family_practice` alt |
| **Rehab / recovery / psych** | ~843 by name | `Breathe Anew Life`, `Just Believe Recovery Center` | `rehab`/`recovery`/`behavioral`/`mental health` in name; `counseling_and_mental_health` alt |
| **Imaging / lab / diagnostic** | ~508 by name | `Windsor Imaging`, radiology centers | `imaging`/`radiology`/`diagnostic` in name; `diagnostic_services`/`laboratory_testing` alt |
| **Cancer / oncology / dialysis** | ~460 by name | `Coastal Cyberknife & Radiation Oncology`, dialysis centers | `oncology`/`radiation`/`dialysis` in name |
| **Surgery / specialty centers** | ~216 by name | `Martin Bariatric and Metabolic Surgery Center` | `surgery center`/`surgical center` in name; `surgical_center` alt |
| **Veterinary / animal** | ~215 (incl. `animal_hospital` 95 + `emergency_pet_hospital` 52) | `Cat Haven Animal Clinic` | `cp=animal_hospital`/`emergency_pet_hospital`; `veterinarian`/`pets` alt |
| **Spa / wellness / cosmetic** | ~336 by name | `Dr Christian Presutti` (→ `waxcenter.com`) | `med spa`/`wax`/`wellness` in name |
| **Hospice / nursing / assisted living** | ~78 by name | `Fort Pierce Health Care` (consulate health) | `hospice`/`nursing`/`assisted living` in name |
| **Hospitalist (individual physicians)** | 364 | hospitalist physician listings | `category_primary = hospitalist` |
| **Medical-equipment B2B** | 101 | `Tick R Tech` (`b2b_medical_support_services`) | `cp=hospital_equipment_and_supplies` / `bc=b2b_service` |

\* Counts are heuristic name/category scans (`analyze_hospitals.py`), not exact
filter output. The combined name-noise scan flags **7,189 rows (33%)** of the raw
pull as likely non-ER, and the `medical_center` swallow alone is **49%** of it.

### Borderline — keep or drop?

- **`medical_center` / outpatient (10,570):** **DROP.** Of all 10,570, only **36**
  carry any `emergency_room` signal. These are urgent cares, clinics, COVID-test
  sites, and doctor offices — none are 24/7 ER hospitals. Dropping the whole
  include removes ~49% of the dataset's noise at the cost of ~36 edge rows.
- **`childrens_hospital` (82):** **KEEP** — children's hospitals run pediatric ERs.
- **`emergency_room` (697) / `emergency_department` basic (697):** **KEEP** — this
  is the strongest ER signal, including freestanding emergency rooms.
- **Brand "Clinic" hospitals (Cleveland Clinic ×26, Mayo ×1):** these *are* real
  hospitals with ERs. A bare `clinic` name-exclude would delete them, so we
  **deliberately do not** exclude bare `clinic` (see §4). The trade-off is that
  ~780 specialty-department rows named `… Clinic` survive — a known residual.

---

## 4. Proposed filter (v1)

### Top controls

| Setting | Value |
|---|---|
| Saved filter | `Hospital` |
| Distance | `20` miles (`1`–`5` urban, `20` rural) |
| Max results | `200` |
| Min confidence | `0.7` — safe; `0.77` sentinel survives, `<0.7` long tail dropped |
| Operating status | `open` |
| Deduplicate addresses | **ON** |

### Include

**Basic category (include):**

```
hospital
```

> `hospital` (contains) matches `hospital` + `specialty_hospital` basic categories
> and **excludes** `outpatient_care_facility`, `emergency_department`,
> `animal_or_pet_service`, and `b2b_service`.

**Category primary (include):**

```
hospital
emergency_room
```

> Deliberately **drop `medical_center` from the include** — it is the single
> noisiest token (10,570 outpatient rows, only 36 with an ER signal). `hospital`
> (contains) keeps `hospital` + `childrens_hospital`; `emergency_room` keeps the
> 697 explicit ER / freestanding-ER rows.

### Exclude — Category primary (exclude)

Removes the substring leaks the `hospital` token drags in:

```
animal
pet
hospitalist
equipment
```

> `animal` → `animal_hospital`; `pet` → `emergency_pet_hospital`; `equipment`
> → `hospital_equipment_and_supplies`; `hospitalist` → individual-physician rows.

### Exclude — Category alternate (exclude)

```
veterinarian
pets
```

> Belt-and-suspenders for veterinary rows whose primary slipped through. Kept
> deliberately short — real ER hospitals carry alternates like `surgical_center`,
> `diagnostic_services`, `physical_therapy`, so excluding those alts would delete
> genuine hospitals. Non-ER specialty venues are removed by **name** instead.

### Exclude — Business name primary (exclude) + Business name common (exclude)

National / generic non-ER medical noise (substring match; paste into **both** name
boxes):

```
urgent care · walk-in · walk in · immediate care · express care
dental · dentist · orthodont
veterinar · animal hospital
rehab · recovery · behavioral · mental health · psychiat · detox
hospice · nursing home · skilled nursing · assisted living
dialysis · imaging · radiology · pharmacy
med spa · medspa · chiropract
physical therapy · occupational therapy
surgery center · surgical center · endoscopy
eye clinic · vision center · std clinic · free clinic · wellness center
```

> **Do NOT** add bare `clinic`, `center`, `surgery`, or `wellness`: each hits real
> ER hospitals (`Cleveland Clinic`, `… Medical Center`, hospital surgery depts).
> The list targets *specific* non-ER phrases only.

### Query builder

```
(basic_category_include or category_primary_include)
  and category_primary_exclude
  and category_alternate_exclude
  and name_primary_exclude
  and name_common_exclude
```

### Quality gate

The numeric `min_confidence = 0.7` **is** the gate here (it is safe — see §5).
The ideal compound gate is deferred:

> **Ideal (deferred, requires dev):** drop a row when `confidence < 0.5` **AND** it
> has no website (551 rows in the raw pull). The admin builder can't express a
> compound rule, so `min_confidence = 0.7` is the practical substitute and is safe
> because the `0.77` sentinel sits above the floor.

### Net effect (simulated against the raw pull)

| Stage | Rows |
|---|---|
| Raw pull | 21,720 |
| Includes (drop `medical_center`): `bc=hospital` ∪ `cp∈{hospital,emergency_room}` | 11,150 |
| − all excludes (category primary/alternate + name) | 9,260 |
| + `min_confidence = 0.7` | **6,643** |
| *(retains)* explicit ER-tagged rows | 868 |
| *(retains)* `0.77` sentinel hospitals | 2,123 |
| *(retains)* `Cleveland Clinic` / `Mayo` brand hospitals | 24 / 1 |

Final `category_primary` mix at the proposed filter: `hospital` 5,979 ·
`emergency_room` 588 · `childrens_hospital` 76 — across all **51** states.

---

## 5. Min-confidence decision (and why `0.9` is wrong)

Unlike gyms, a numeric floor **is** usable here, because the sentinel (`0.77`) is
*above* a `0.7` threshold:

| Option | Effect on the cleaned set (9,260) | Verdict |
|---|---|---|
| `min_confidence = 0.9` *(user's current)* | Drops to **2,406** — deletes **all 2,123** `0.77`-sentinel hospitals + the `0.7–0.9` band | ❌ reject |
| *(no floor)* | 9,260 — keeps the unverifiable `<0.5` long tail (abandoned/ghost listings, no website) | ⚠️ noisy |
| **`min_confidence = 0.7`** | **6,643** — keeps every `0.77` sentinel + websited hospital, drops the genuine `<0.7` tail | ✅ proposed |
| Ideal: `confidence < 0.5` AND no website | Drops 551 truly unverifiable rows; keeps everything else | ⏸ deferred (dev) |

Hospitals skew high-confidence and almost always have websites (85% overall, far
higher among the cleaned set), so a `0.7` floor costs little recall while removing
the bottom 16% of unverifiable listings. The user's `0.9` is the opposite: it is
**catastrophic**, deleting ~64% of the *already cleaned* set including
sentinel-scored real hospitals.

---

## 6. How this improves on the user's current `Hospital` filter

The user's saved filter (`min_confidence 0.9`, includes `hospital`,
`emergency_room`, `medical_center` on primary **and** `emergency_room`,
`medical_center` on alternate, plus large name/category excludes) has two
structural problems this v1 fixes:

| Issue in current filter | Evidence | This filter |
|---|---|---|
| **Includes `medical_center` (primary + alternate)** → pulls the entire 10,570-row outpatient universe (urgent care, clinics, COVID sites, doctor offices); only 36 have an ER | `cp=medical_center` = 10,570; ER-tagged = 36 | **Drops `medical_center`** from includes entirely — removes ~49% of all noise at a cost of ~36 edge rows |
| **`min_confidence = 0.9`** deletes all 9,162 `0.77`-sentinel rows, incl. real hospitals | exact `0.77` = 9,162 (42%); `0.9` floor drops 73% of raw, 64% of cleaned | **`0.7`** keeps the sentinel band, drops only the genuine `<0.7` tail |
| No `hospitalist` / `hospital_equipment_and_supplies` exclude | substring `hospital` leaks 364 hospitalist + 101 B2B rows | adds `hospitalist` + `equipment` to `category_primary` excludes |
| Over-broad name excludes risk dropping brand hospitals; current `walk-in clinic`/`clinic`-style tokens can hit `Cleveland Clinic`/`Mayo` | `Cleveland Clinic` ×26, `Mayo` ×1 in pull | uses **specific** non-ER phrases, deliberately omitting bare `clinic`/`center`/`surgery` |

**Noise the current filter misses but this one removes:** the dominant
`medical_center`/outpatient swallow, `hospitalist` physician listings, and
`hospital_equipment_and_supplies` B2B vendors.

**Noise the current filter over-removes (recall the current one loses):** the
`0.9` floor and any bare-`clinic` name token wipe out sentinel-scored hospitals and
brand "Clinic"/"Medical Center" hospitals — which this filter keeps.

**Residual limitation (both filters):** specialty hospital *departments* named
`… Clinic` (~780) and miscategorized `category_primary = hospital` records (e.g.
sleep/eye departments) survive, because Overture gives no 24/7-ER flag to gate on.
A dev-side compound `confidence < 0.5 AND no website` rule and/or an explicit ER
boost would tighten this further.

---

## Appendix A — reproduce

```bash
pip install requests
python scripts/scrape_hospitals.py --pins data/coffee_tea_raw/pins.csv   # full pull
python scripts/analyze_hospitals.py                                       # summary stats
```

Raw dataset + column docs: [`../../data/hospitals_raw/README.md`](../../data/hospitals_raw/README.md).
