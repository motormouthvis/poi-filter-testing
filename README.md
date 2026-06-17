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
- [`docs/filters/restaurants.md`](docs/filters/restaurants.md) — a worked example
  filter for the **Restaurants** category (work in progress).

## TL;DR

- **Single data source (for now):** Overture Maps Places (GeoParquet).
- **Filters live in the admin panel**, not in code — so POI selection can change
  in production without a deploy.
- **Current phase:** Filter Development — building/testing category filters
  (Groceries, Restaurants, Hospitals, etc.) with the custom filter builder.
