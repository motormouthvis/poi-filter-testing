# DN-POI-DATASET: Building Production-Grade POI Filters for the Dream Neighborhood Widget (Overture-First)

## Project Description

This project focuses on developing and maintaining high-quality, production-ready
POI filters for the **Dream Neighborhood widget** on
[www.dreamneighborhood.com](https://www.dreamneighborhood.com). The widget
currently surfaces mom-centric neighborhood data including grocery stores,
restaurants, cafes, nightlife, gyms, parks, and major hospitals with ERs.

Rather than building a complex multi-source data fusion system at this stage, the
project is currently **Overture-first**. Overture Maps Places data serves as the
single primary data source. Future sources (OSM, Foursquare OS Places, or
proprietary datasets) may be evaluated later, but only if they can be cleanly
integrated without complicating the production pipeline. The current priority is
building robust, maintainable filters that work reliably on Overture data.

A key architectural goal is to manage POI selection through **configurable filters
in the admin panel** rather than hard-coded logic. This allows the team to adjust
what appears in the widget (include/exclude rules, category logic, name patterns,
etc.) without requiring code changes or deployments — even once the system is in
production.

## Current Phase

We are in the **Filter Development Phase**. The focus is on creating, testing, and
refining category-specific filters (Groceries, Restaurants, Hospitals, etc.) using
the custom filter builder in the Django admin. These filters combine business name
patterns, basic categories, primary/alternate categories, and query logic to
produce clean, relevant POI results.

## Core Objectives

- Build accurate, production-grade filters for each widget category using Overture
  data.
- Enable filter changes through the admin panel without code modifications.
- Maintain a clean separation between **data** (Overture) and **selection logic**
  (filters).
- Create filters that are easy to understand, test, and iterate on.
- Prepare a foundation that can later support additional data sources if needed,
  without major rework.

## Why This Matters

Real estate agents need trustworthy neighborhood data that keeps users on their
site. By investing in high-quality, easily adjustable filters on top of Overture
data, we can deliver strong results quickly while keeping the system maintainable
and low-cost. This approach reduces reliance on expensive third-party APIs and
gives the team direct control over the user experience.

## Current Scope

- **Primary Data Source:** Overture Maps Places (GeoParquet)
- **Focus:** Developing and refining filters for core widget categories
  (Groceries, Restaurants, Hospitals, etc.)
- **Filter Management:** All category rules are controlled through the admin panel
  filter builder (name includes/excludes, category includes/excludes, query
  builder logic).
- **Future Consideration:** Additional sources (OSM, Foursquare, etc.) may be
  evaluated later, but only if integration remains clean and low-risk.

## Key Deliverables (Current Phase)

- Well-tested, production-ready filters for each major category.
- Clear documentation of filter logic and rationale for each category.
- Ability to modify POI selection behavior in production via the admin panel
  without code changes.
- A repeatable testing process for validating filter changes.

## Success Criteria (Current Phase)

- Filters produce clean, relevant results that match mom-centric expectations.
- Filter changes can be made and deployed to production without code changes.
- High consistency and low noise across test locations.
- Filters are easy for the team to understand and maintain over time.

## Project Approach

- Work category by category (Groceries → Restaurants → Hospitals → etc.).
- Start with category-based rules first, then layer in name-based rules only where
  needed.
- Use the admin panel's query builder and include/exclude fields as the primary
  control surface.
- Iterate quickly based on real test results from the widget/admin.
- Keep the system simple and maintainable by staying Overture-first for now.

This project serves as the working space to design, test, and document the filter
system that will power the Dream Neighborhood widget.
