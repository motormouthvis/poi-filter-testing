# Production finalization checklist

Tracking which POI filters are finalized for production, one category at a time.
Legend: ✅ finalized · 🔄 in review · ⬜ not started

| Category | Production filter | Status | Notes |
|---|---|---|---|
| **Hospitals** | `hospital-cursor` (id 434) | 🔄 chosen, pending sign-off | Beat `Hospital` (id 67) decisively — see below |
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
