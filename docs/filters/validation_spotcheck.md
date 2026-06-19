# Filter validation — per-metro spot-checks (v1)

Full proposed filters (includes + excludes + query) run against staging.
Metros: houston_tx, denver_co, key_west_fl, ann_arbor_mi.

> Reproduce: `python scripts/validate_filters.py`

## Verdict

**Automated leak scan: 0 leaks in all 4 categories × 4 metros.** The category/name
excludes are applied correctly server-side — no juice/salad/milk bars survive in
nightlife, no parking lots/garden centers in parks, no food courts in shopping.

**Manual eyeball of kept samples — a few residual false positives remain** (all
match the "residual noise — needs data enrichment" sections already in each doc;
none are fixable with category/name tokens alone):

| Category | Residual FP seen | Why it survives |
|---|---|---|
| Parks | `Hot Wells Shooting Range`, `Key West Concierge`, some `Civic Center/Centre` plazas | genuinely tagged `category_primary = park`; not a park by use |
| Shopping | `GNC` (single store, Ann Arbor), `Houston Tunnels` | individual tenant / pedestrian retail tagged `shopping_center` |
| Nightlife | `Wolverine Sushi Bar`, `Victors Restaurant & Bar` | basic_category `bar` on a food-forward venue; name not a clean signal |
| Gyms | none material (e.g. `Denver Public Safety Yoga` is a real class) | — |

These are **single-digit per metro** and require enrichment flags (`is_multi_tenant`,
`is_paid_admission`, tenant counts, venue-type) to remove — documented per filter.
Recommendation: ship v1 as-is; revisit residuals when enrichment fields exist.

## gyms  (distance 5 mi)

| Metro | Kept | Leaks | Sample kept |
|---|---:|---:|---|
| houston_tx | 250 | 0 | Houston Heights Neighbor, NirvanaFlex Restorative , H-Fitness, Fit700, 711 Fit, Health Club at Travis Pl |
| denver_co | 250 | 0 | Denver Public Safety  Yo, YMCA, 1884 Group Fitness - Den, Lagreeluxe, Pilates Downtown, Fitness in the City |
| key_west_fl | 42 | 0 | FFAKW, Pilates Key West, Webefit Personal Trainin, Gligorovic Martial Arts, Paradise Fitness, Shane Wood - Key West Fl |
| ann_arbor_mi | 202 | 0 | Red Yoga, Ann Arbor Bjj, Pure Barre, openfloor, Erin Cantrell Fitness, Tiny Buddha Yoga |

## parks  (distance 3 mi)

| Metro | Kept | Leaks | Sample kept |
|---|---:|---:|---|
| houston_tx | 166 | 0 | Hot Wells Shoting Range, Barbara Bush Literacy Pl, Tranquillity Park, Tranquility Park, Sam Houston Park, Little Tranquility Park |
| denver_co | 207 | 0 | D-Town, Civic Center Park - Inde, Civic Centre, Civic Center Park, Liberty Park, Lincoln Veterans Memoria |
| key_west_fl | 75 | 0 | Key West Community Cente, Glass Beach Key West, The Key West Nature Pres, Key West Concierge, Sonny Mccoy Indigenous P, C B Harvey Rest Beach Pa |
| ann_arbor_mi | 116 | 0 | B2B Trail - Walks, Liberty Plaza, Nicholas Arboretum, Michigan Square, Leslie Science & Nature , Broadway Dog Park |

## shopping_centers  (distance 5 mi)

| Metro | Kept | Leaks | Sample kept |
|---|---:|---:|---|
| houston_tx | 42 | 0 | Houston Tunnels, The Shops at Houston Cen, The Shops at Houston Cen, Sharpstown Center, The Shops at Sawyer Yard, ONLi by tadaima |
| denver_co | 41 | 0 | Denver Pavilions, 16th Street Mall, Denver-16th Street Mall, 16th Street, California Mall on 16th, 16th Street Mall |
| key_west_fl | 5 | 0 | Overseas Market, Key Plaza Shopping Cente, Searstown Plaza, Searstown Shopping Cente, Key West Cyber Mall |
| ann_arbor_mi | 16 | 0 | The Courtyard, Westgate Shopping Center, Maple Village, Georgetown Mall, GNC, Traver Village Shopping  |

## nightlife  (distance 5 mi)

| Metro | Kept | Leaks | Sample kept |
|---|---:|---:|---|
| houston_tx | 250 | 0 | The Concert Pub - Galler, Time Out Sports Bar #4, Downtown Club At Met, Blue by Massa's, 40 Below At Revention, The Wine Cellar Wine & M |
| denver_co | 250 | 0 | Willkommen - Bier im Par, The Greedy Hamster, Pints Pub, Pints Pub, Cap City Tavern, MÁS MARGS Denver Margari |
| key_west_fl | 177 | 0 | Shanna Key Irish Pub and, Bier Boutique, Brady's Pub, Mac's Place, Espiritu Tequila Bar, Drifter’s Cove |
| ann_arbor_mi | 118 | 0 | 1824 Cocktails & Coffee, Wolverine Sushi Bar, Allen Rumsey Cocktail Lo, Victors Restaurant & Bar, Allen Rumsey Cocktail Lo, Bar Louie |

