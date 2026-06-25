# Filter: Urgent Care (subcategory under Hospital)

> **Status: v1 — live on saved filter `Urgent Care` (id 463).**
> Built from `data/hospitals_raw/` (21,720 unique POIs, 51 states). Generic USA.

**Goal:** surface **urgent care / walk-in clinics** as a subcategory under the
**Hospital** main category — and **exclude real hospitals, ERs, and trauma centers**
(those stay in the Hospital filter).

---

## Why this is name-driven (the key finding)

In Overture's hospital universe, **`category_primary = urgent_care_clinic` appears 0
times**. Urgent cares that live in the hospital data are **mislabeled**:

| What urgent cares are tagged as | count (of 848 UC-named rows) |
|---|---|
| `medical_center` | 597 |
| `hospital` | 184 |
| `emergency_room` | 63 |

So category alone cannot separate urgent care from hospitals. **The business name is
the only reliable signal.** The filter therefore includes by urgent-care name tokens +
UC-specific brands, and a real hospital is excluded structurally — it never carries an
urgent-care token in its name.

> **Do NOT include bare hospital-system names** (Cleveland Clinic, Kaiser Permanente,
> Ascension, Atrium, Banner, Baptist, Memorial Hermann, etc.). Those match the parent
> *hospital*, not the urgent care. System-branded urgent cares are caught by the generic
> `urgent care` / `immediate care` / `convenient care` tokens instead (e.g. "Ascension
> St. Vincent's Urgent Care", "Memorial Hermann GoHealth Urgent Care").

We keep `category_primary = urgent_care_clinic` in the include too — it is **absent in
the hospital pull but present in the live POI table** (e.g. "Concentra Urgent Care",
"Banner Urgent Care" come back tagged `urgent_care_clinic` live).

---

## 0. Admin panel parameters (paste-ready, v1)

| Control | Value |
|---|---|
| Saved filter | `Urgent Care` (id 463) |
| Distance (miles) | `20` (use `5` in metros) |
| Max results | `100` |
| Min confidence | *(blank — UC rows cluster at the 0.77 sentinel / low conf; no floor)* |
| Operating status | `open` |
| Deduplicate addresses | checkbox **unchecked** = dedupe on |

**Category primary — include:**

```
urgent_care_clinic
```

**Business name primary — include** (also paste into **Business name common — include**
and the **keyword** include):

```
urgent care
immediate care
express care
walk-in clinic
walk in clinic
walk-in care
walk in care
minute clinic
minuteclinic
convenient care
convenientmd
quick care
quickcare
nowcare
after hours care
centra care
instacare
zoom care
zoomcare
redicare
redimed
velocity care
walk-in center
walk in center
concentra
medexpress
fastmed
carenow
nextcare
citymd
gohealth
wellnow
carbon health
patient first
md now
fast pace
american family care
afc urgent
doctors care
pm pediatrics
carespot
medpost
carewell
wellstreet
physicianone
the little clinic
next level urgent
exer urgent
total access urgent
```

**Category primary — exclude:**

```
animal_hospital
emergency_pet_hospital
hospitalist
hospital_equipment_and_supplies
oil_change_station
automotive
hospice
funeral
lawyer
attorney
```

**Category alternate — exclude:**

```
veterinarian
pets
pet_services
```

**Business name primary — exclude** (also **Business name common — exclude** + keyword):

```
emergency department
emergency room
freestanding emergency
trauma center
veterinary
veterinarian
animal hospital
pet hospital
animal urgent
valvoline
oil change
jiffy lube
```

**Query builder:**

```
(category_primary_include or name_primary_include or name_common_include)
  and category_primary_exclude
  and category_alternate_exclude
  and name_primary_exclude
  and name_common_exclude
```

---

## Validation

Local simulation over `hospitals_raw`: **870 / 21,720 kept**, **0 leaks**, **0 real
hospitals** (rows with "hospital" in the name and no UC token = 0). The 9,564 real
hospitals + 9,949 medical centers are correctly cut.

Live multi-metro test (filter 463), `total / hospital-leaks`:

| Metro | total | hospital leaks |
|---|---|---|
| Fort Pierce, FL (20mi) | 38 | 0 |
| Chicago (5mi) | 57 | 0 |
| Houston (5mi) | 38 | 0 |
| Phoenix (5mi) | 19 | 0 |
| Atlanta (5mi) | 49 | 0 |
| Denver (5mi) | 43 | 0 |

Reproduce: `python scripts/_populate_uc.py` then `python scripts/_validate_uc.py`.

---

## Open items

- **`category_key` link:** filter 463 currently has `category_key` **blank** — it is not
  linked to the `hospitals` main category (or the `urgent_care` subcategory) at the model
  level. Set this in the PoiFilter model admin if the widget routes subcategories via
  `category_key`. (The change-list save/update path does not set it.)
- **Dedupe on saved filters** is not honored on apply (same caveat as Hospitals) — flag
  for widget/dev plumbing.
- Deferred quality gate (`confidence < x AND no website`) still pending dev, same as the
  other filters.
