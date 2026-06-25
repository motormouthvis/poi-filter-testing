# Production finalization checklist

Tracking which POI filters are finalized for production, one category at a time.
Legend: ✅ finalized · 🔄 in review · ⬜ not started

| Category | Production filter | Status | Notes |
|---|---|---|---|
| **Hospitals** | `hospital-cursor` (id 434, **v2**) | 🔄 v2 live, pending sign-off | v1 had a precision hole (Overture mislabels doctor offices as `hospital`); v2 fixes it — see below |
| **Urgent Care** (sub of Hospital) | `Urgent Care` (id 463) | 🔄 v1 live, pending sign-off | name-driven (urgent_care_clinic=0 in raw); 0 hospital leaks across 6 metros. See `urgent_care.md`. **Open:** `category_key` not linked |
| Cafes | `cafe-cursor` (id 435) | ⬜ | built + validated, not yet head-to-head vs `Cafe` |
| Grocery | `grocery-cursor` (id 436) | ⬜ | built + validated, not yet head-to-head vs `Grocery` |
| Restaurants | `restaurant-cursor` (id 437) | ⬜ | built + validated, not yet head-to-head vs `Restaurants` |
| Gyms | `gym-cursor` (id 430) | ⬜ | built + validated |
| Parks | `park-cursor` (id 431) | ⬜ | built + validated |
| Shopping centers | `shopping-cursor` (id 432) | ⬜ | built + validated |
| Nightlife | `nightlife-cursor` (id 433) | ⬜ | built + validated |

---

## Hospitals — head-to-head (2026-06-19)

`Hospital` (id 67, user-built) vs `hospital-cursor` (id 434). Tested across 11
areas (NYC errored both — staging Heroku 30s timeout). Format `total/real/noise`;
**noise** = vet/urgent-care/clinic/rehab/nursing/imaging/etc.

| Area (radius) | `Hospital` | `hospital-cursor` |
|---|---|---|
| Ft. Pierce, FL — home (5mi) | 1 / 1 / 0 | 6 / 6 / 0 |
| NYC (1mi) | ERR | ERR |
| Los Angeles (1mi) | 0 / 0 / 0 | 6 / 4 / 0 |
| Chicago (1mi) | 0 / 0 / 0 | 25 / 25 / 0 |
| Houston (2mi) | 1 / 1 / 0 | 18 / 16 / 0 |
| Denver (2mi) | 6 / 6 / 0 | 51 / 48 / 0 |
| Atlanta (2mi) | 4 / 4 / 0 | 36 / 35 / 0 |
| Phoenix (2mi) | 4 / 4 / 0 | 27 / 23 / 0 |
| Seattle (2mi) | 3 / 3 / 0 | 84 / 77 / 0 |
| Bozeman, MT (5mi) | 0 / 0 / 0 | 4 / 4 / 0 |
| Dodge City, KS (5mi) | 1 / 1 / 0 | 8 / 8 / 0 |
| **TOTAL (10 valid areas)** | **20 / 20 / 0** | **265 / 246 / 0** |

**Both filters have ZERO noise** (neither leaks vets/urgent care/clinics).
The deciding factor is **recall**: `hospital-cursor` finds **~13× more real
hospitals** (265 vs 20). Category mix is 100% clean for both:
- `Hospital`: hospital 20
- `hospital-cursor`: hospital 237, emergency_room 27, childrens_hospital 1

**Why `Hospital` misses so many:** it sets `min_confidence = 0.9`, which deletes
every hospital sitting at Overture's `0.77` sentinel confidence — i.e. most real
hospitals (Chicago 0 vs 25, Seattle 3 vs 84). `hospital-cursor` uses
`min_confidence = 0.7` (sentinel survives) + structural excludes
(`medical_center` dropped, vet/hospitalist/equipment removed).

> The ~19-row gap between `hospital-cursor` total (265) and "real" (246) is **not
> noise** — it's brand hospitals whose *name* contains a flagged word (e.g. "Mayo
> Clinic", "Cleveland Clinic" → "clinic"); category is still `hospital`. noise% = 0.

### Verdict
**Adopt `hospital-cursor` for production hospitals.** Same precision (0 noise),
far better coverage. Reproduce: `python scripts/compare_hospital_filters.py`.

**Open item:** re-test NYC once staging is stable (it timed out at 1mi for both).

---

## Hospitals — CORRECTION + v2 (2026-06-19, later)

The "0 noise" verdict above was **measured wrong**: the comparison script classified
a row as a real hospital whenever `category_primary = hospital`. But Overture tags a
huge number of **physician offices, specialty clinics, health departments, and even
unrelated businesses** as `category_primary = hospital`. Re-pulling the FL home pin
(`27.49434…, -80.33809…`, 20mi) on `hospital-cursor` v1 returned **47 results, of which
only ~13 (~28%) were genuine 24-hr ER hospitals** — the rest were doctor offices
("Cardiovascular Consultants", "Vero Gastroenterology"), specialty clinics, health
departments, a call center ("Teleperformance"), and a wax center ("Dr Christian Presutti").

### v2 fix (precision-first, user-chosen)
Root cause: name-excludes can't catch junk named like a business; the real signal is
in **`category_alternate`**. Using `scripts/tune_hospital_v2.py` we measured, per
alternate tag, its co-occurrence with an `emergency_room` signal and excluded only the
~0%-ER tags (`doctor`, `family_practice`, `internal_medicine`, `surgical_center`,
`public_and_government_association`, `laboratory_testing`, etc.) while **preserving**
the ER-correlated tags (`medical_center`, `medical_service_organizations`,
`ambulance_and_ems_services`, `diagnostic_services`). Added specialist name-excludes too.

| Metric | v1 | v2 |
|---|---|---|
| Home pin (20mi) results | 47 | **17** |
| ...genuine ER hospitals | ~13 | **14** |
| ...precision | ~28% | **~82%** |
| National ER-signal recall | — | **74.6%** (dropped = urgent care / surgery centers / vet ERs / hospital sub-depts — all correct) |

Residual leaks at home pin: 3 (`Total Care Medical Centers`, `Cleveland Clinic Pointe
West` walk-in, `Dr Christian Presutti`) — all have empty/generic `category_alternate`
and innocuous names, i.e. no usable signal without the deferred confidence+website gate.

**Dedupe caveat:** the `Deduplicate addresses` checkbox is **not honored when applying
a saved filter** (same-address dups still returned regardless of the toggle). Flag for
dev / widget plumbing.

### Verdict (updated)
**Adopt `hospital-cursor` v2.** Precision at the home pin jumped 28% → 82% with no loss
of real acute-care hospitals. v2 is live on saved filter id 434.
