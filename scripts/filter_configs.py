"""Shared definitions of all 8 POI filters (the `-cursor` saved-filter set).

Each config mirrors the paste-ready §0 section of the matching docs/filters/*.md
file. These are consumed by:
  - simulate_filters.py  (local checks/leak detection over the raw datasets)
  - create_and_test_filters.py  (create the saved filters + live multi-location test)

Field names match the PoiDetail change-list filter form (the `*_values` GET
params). Token syntax follows the admin builder's match operators:
  contains (default) | "exact" | prefix* | *suffix | *contains*
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = REPO_ROOT / "data"

# name -> config. `name` becomes the saved_filter_name (the "-cursor" tag set).
FILTERS: dict[str, dict] = {
    "gym-cursor": {
        "raw_csv": DATA / "gyms_raw" / "gyms_master.csv",
        "max_results": "250",
        "min_confidence": "",
        "operating_status": "open",
        "has_website": "",
        "show_duplicates": True,
        "basic_category_include": ["gym", "fitness_center"],
        "category_primary_include": [
            "gym", "fitness_center", "yoga_studio", "pilates_studio",
            "martial_arts", "boxing_gym", "climbing_gym", "crossfit",
            "gymnastics_center", "aerial_fitness_center",
        ],
        "category_alternate_exclude": [
            "day_spa", "swimming_pool", "golf_course", "golf_instructor",
            "dance_school",
        ],
        "name_primary_exclude": [
            "physical therapy", "chiropract", "country club",
            "golf academy", "swim academy", "swim school",
        ],
        "query_builder": "(basic_category_include or category_primary_include) and category_alternate_exclude and name_primary_exclude",
    },
    "park-cursor": {
        "raw_csv": DATA / "parks_raw" / "parks_master.csv",
        "max_results": "200",
        "min_confidence": "",
        "operating_status": "open",
        "has_website": "",
        "show_duplicates": True,
        "basic_category_include": ['"park"', '"garden"', '"playground"', '"dog_park"', '"national_park"'],
        "category_primary_include": [
            '"park"', '"state_park"', '"national_park"', '"nature_preserve"',
            '"botanical_garden"', '"community_gardens"', '"dog_park"',
            '"playground"', '"skate_park"', '"water_park"',
        ],
        "category_primary_exclude": [
            "parking", "mobile_home_park", "rv_park", "amusement_park",
            "gardener", "nursery_and_gardening", "home_and_garden",
            "beer_garden", "trampoline_park", "atv_recreation_park",
            "hydroponic_gardening", "park_and_rides",
        ],
        "name_primary_exclude": [
            "parking", "garage", "mobile home", "trailer park", "business park",
            "office park", "industrial park", "rv park", "self storage",
        ],
        "query_builder": "(basic_category_include or category_primary_include) and category_primary_exclude and name_primary_exclude",
    },
    "shopping-cursor": {
        "raw_csv": DATA / "shopping_centers_raw" / "shopping_centers_master.csv",
        "max_results": "250",
        "min_confidence": "",
        "operating_status": "open",
        "has_website": "",
        "show_duplicates": True,
        "basic_category_include": ["shopping_center", "shopping_mall"],
        "category_primary_include": ["shopping_center", "shopping_mall", "outlet_mall", "strip_mall"],
        "name_primary_exclude": [
            "food court", "parking", "self storage", "business park",
            "business plaza", "office park", "medical center",
            "medical plaza", "professional plaza", "professional building",
            "industrial park",
        ],
        "query_builder": "(basic_category_include or category_primary_include) and name_primary_exclude",
    },
    "nightlife-cursor": {
        "raw_csv": DATA / "nightlife_raw" / "nightlife_master.csv",
        "max_results": "250",
        "min_confidence": "",
        "operating_status": "open",
        "has_website": "",
        "show_duplicates": True,
        "basic_category_include": ["bar", "nightlife"],
        # NOTE: the admin strips a leading '*', so ends-with anchors (*bar/*pub)
        # collapse to plain "contains". Two consequences handled here:
        #  - bare "pub" (contains) matches public_* gov/school/publisher cats, so we
        #    use exact "pub" + explicit gastropub/brewpub instead.
        #  - "bar" (contains) pulls barber/bartender/barbecue/bar_and_grill, removed
        #    via excludes ("restaurant" kills *_restaurant; barber; bartender).
        "category_primary_include": [
            "bar", "night_club", "nightclub", '"pub"', "gastropub", "brewpub",
            "lounge", "brewery", "karaoke",
        ],
        "category_primary_exclude": [
            "smoothie_juice_bar", "salad_bar", "milk_bar", "juice_bar",
            "sushi_bar", "oyster_bar", "raw_bar", "snack_bar", "candy_bar",
            "restaurant", "barber", "bartender",
        ],
        "query_builder": "(basic_category_include or category_primary_include) and category_primary_exclude",
    },
    "hospital-cursor": {
        "raw_csv": DATA / "hospitals_raw" / "hospitals_master.csv",
        "max_results": "200",
        "min_confidence": "0.7",
        "operating_status": "open",
        "has_website": "",
        "show_duplicates": True,
        "basic_category_include": ["hospital"],
        "category_primary_include": ["hospital", "emergency_room"],
        "category_primary_exclude": ["animal", "pet", "hospitalist", "equipment"],
        "category_alternate_exclude": ["veterinarian", "pets"],
        "name_primary_exclude": [
            "urgent care", "walk-in", "walk in", "immediate care", "express care",
            "dental", "dentist", "orthodont", "veterinar", "animal hospital",
            "rehab", "recovery", "behavioral", "mental health", "psychiat",
            "detox", "hospice", "nursing home", "skilled nursing", "assisted living",
            "dialysis", "imaging", "radiology", "pharmacy", "med spa", "medspa",
            "chiropract", "physical therapy", "occupational therapy",
            "surgery center", "surgical center", "endoscopy", "eye clinic",
            "vision center", "std clinic", "free clinic", "wellness center",
        ],
        # name_common_exclude mirrors name_primary_exclude per the doc
        "name_common_exclude": [
            "urgent care", "walk-in", "walk in", "immediate care", "express care",
            "dental", "dentist", "orthodont", "veterinar", "animal hospital",
            "rehab", "recovery", "behavioral", "mental health", "psychiat",
            "detox", "hospice", "nursing home", "skilled nursing", "assisted living",
            "dialysis", "imaging", "radiology", "pharmacy", "med spa", "medspa",
            "chiropract", "physical therapy", "occupational therapy",
            "surgery center", "surgical center", "endoscopy", "eye clinic",
            "vision center", "std clinic", "free clinic", "wellness center",
        ],
        "query_builder": "(basic_category_include or category_primary_include) and category_primary_exclude and category_alternate_exclude and name_primary_exclude and name_common_exclude",
    },
    "cafe-cursor": {
        "raw_csv": DATA / "coffee_tea_raw" / "coffee_tea_master.csv",
        "max_results": "250",
        "min_confidence": "",
        "operating_status": "open",
        "has_website": "",
        "show_duplicates": True,
        "basic_category_include": ["coffee_shop", "tea_room"],
        "category_primary_include": ["coffee_shop", "tea_room", "coffee_roastery"],
        "name_primary_exclude": [
            "aplus", "sunoco", "wild bean", "wfm coffee", "proudly serve",
            "mcdonald", "krispy kreme", "duck donut", "royal cup", "clean eatz",
            "food mart", "chevron", "wawa", "nutrition", "herbalife", "kava",
            "kratom", "7-eleven", "ampm", "buc-ee", "circle k", "conoco",
            "cumberland", "exxon", "getgo", "kum & go", "kum and go", "quiktrip",
            "racetrac", "royal farms", "sheetz", "sinclair", "texaco",
            "thorntons", "valero",
        ],
        "query_builder": "(basic_category_include or category_primary_include) and name_primary_exclude",
    },
    "grocery-cursor": {
        "raw_csv": DATA / "grocery_raw" / "grocery_master.csv",
        "max_results": "250",
        "min_confidence": "",
        "operating_status": "open",
        "has_website": "",
        "show_duplicates": True,
        "category_primary_include": ["supermarket", "grocery_store", "specialty_grocery_store", "wholesale_grocer"],
        "category_primary_exclude": [
            "convenience_store", "gas_station", "dollar_store", "discount_store",
            "pharmacy", "drugstore", "liquor_store", "beer_wine_and_spirits",
            "tobacco_shop", "e_cigarette_store", "vitamins_and_supplements",
            "bakery", "caterer", "fast_food_restaurant", "bank",
        ],
        "name_primary_exclude": [
            "Distribution Center", "Grocery Pickup", "Pickup & Delivery",
            "Pickup and Delivery",
        ],
        "query_builder": "category_primary_include and category_primary_exclude and name_primary_exclude",
    },
    "restaurant-cursor": {
        "raw_csv": DATA / "restaurants_raw" / "restaurants_master.csv",
        "max_results": "200",
        "min_confidence": "0.7",
        "operating_status": "open",
        "has_website": "",
        "show_duplicates": True,
        "basic_category_include": ["restaurant"],
        "category_primary_exclude": [
            "fast_food_restaurant", "food_truck", "street_vendor", "coffee_shop",
            "cafe", "bakery", "nightclub", "brewery", "distillery", "winery",
            "caterer", "food_court", "cafeteria",
        ],
        "category_alternate_exclude": [
            "fast_food_restaurant", "food_truck", "street_vendor", "coffee_shop",
            "cafe", "bakery", "nightclub", "brewery", "distillery", "winery",
            "caterer", "food_court", "gas_station", "convenience_store",
            "grocery_store", "supermarket",
        ],
        "name_primary_exclude": [
            "catering", "food truck", "taco truck", "chevron", "shell",
            "exxon", "mobil", "marathon", "circle k", "7-eleven",
        ],
        "query_builder": "basic_category_include and category_primary_exclude and category_alternate_exclude and name_primary_exclude",
    },
}

# Map filter-config keys to the change-list GET form field names.
FIELD_PARAM = {
    "basic_category_include": "basic_category_include_values",
    "category_primary_include": "category_primary_include_values",
    "category_alternate_include": "category_alternate_include_values",
    "name_primary_include": "name_primary_include_values",
    "name_common_include": "name_common_include_values",
    "taxonomy_primary_include": "taxonomy_primary_include_values",
    "taxonomy_alternates_include": "taxonomy_alternates_include_values",
    "basic_category_exclude": "basic_category_exclude_values",
    "category_primary_exclude": "category_primary_exclude_values",
    "category_alternate_exclude": "category_alternate_exclude_values",
    "name_primary_exclude": "name_primary_exclude_values",
    "name_common_exclude": "name_common_exclude_values",
    "taxonomy_primary_exclude": "taxonomy_primary_exclude_values",
    "taxonomy_alternates_exclude": "taxonomy_alternates_exclude_values",
}

# Which raw-CSV column each filter field tests against (for local simulation).
FIELD_COLUMN = {
    "basic_category_include": "basic_category",
    "category_primary_include": "category_primary",
    "category_alternate_include": "category_alternate",
    "name_primary_include": "business_name",
    "name_common_include": "name_common",
    "basic_category_exclude": "basic_category",
    "category_primary_exclude": "category_primary",
    "category_alternate_exclude": "category_alternate",
    "name_primary_exclude": "business_name",
    "name_common_exclude": "name_common",
}
