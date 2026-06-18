# poi-filter-testing

Working space for designing, testing, and documenting the **POI filter system**
that powers the **Dream Neighborhood widget** on
[www.dreamneighborhood.com](https://www.dreamneighborhood.com).

The widget surfaces mom-centric neighborhood data (grocery stores, restaurants,
cafes, nightlife, gyms, parks, and major hospitals with ERs). This repo is where
we iterate on the **production-grade, Overture-first POI filters** that decide
which places show up in each category.

## Documentation

- [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md) — full project brief:
  goals, scope, current phase, success criteria, and approach.
- [`docs/admin-filter-builder.md`](docs/admin-filter-builder.md) — reference for
  the Django admin filter builder (fields, query-builder tokens, how
  include/exclude logic works, the `PoiDetail` data model).
- [`docs/filters/restaurants.md`](docs/filters/restaurants.md) — **Restaurants**
  filter (v3, shippable).
- [`docs/filters/cafes.md`](docs/filters/cafes.md) — **Cafes** filter (v3, in validation).
- [`data/cafe_filter_examples/`](data/cafe_filter_examples/) — **1,600+ unique POI rows**
  from USA validation batches (CSV + JSON); regenerate with
  `python scripts/extract_cafe_examples.py`.
- [`docs/POI_FILTER_TESTING_CLEAN.md`](docs/POI_FILTER_TESTING_CLEAN.md) — hospital
  filter preset, dev brief, and benchmark (session notes).

## Keep local and GitHub in sync

From the repo root:

```powershell
.\scripts\sync.ps1
```

That script **pulls** latest from `origin/main`, then **commits and pushes** any local
changes so this folder and
[github.com/motormouthvis/poi-filter-testing](https://github.com/motormouthvis/poi-filter-testing)
stay aligned.

## TL;DR

- **Single data source (for now):** Overture Maps Places (GeoParquet).
- **Filters live in the admin panel**, not in code — so POI selection can change
  in production without a deploy.
- **Current phase:** Filter Development — building/testing category filters
  (Groceries, Restaurants, Hospitals, etc.) with the custom filter builder.
